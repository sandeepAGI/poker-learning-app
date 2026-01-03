"""
Test for Issue #4: Session Analysis Parameter Issues

Verifies that:
1. hand_count parameter is respected (slices hand_history before analysis)
2. Rate limiting applies regardless of use_cache flag

TDD Red Phase: These tests should FAIL before the fix is applied.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from game.poker_engine import PokerGame, CompletedHand, BettingRound, ActionRecord
import main
from main import app, games, last_analysis_time, analysis_cache


# Fixture to set up test game with hand history
@pytest.fixture
def game_with_history():
    """Create a game with 10 completed hands."""
    # Use Mock instead of creating real CompletedHand objects
    # This avoids dealing with all the required fields
    mock_game = Mock(spec=PokerGame)
    mock_game.players = [
        Mock(player_id="human", is_human=True, stack=1000)
    ]

    # Create 10 simple mock hands (just need hand_number for testing)
    mock_hands = []
    for i in range(10):
        mock_hand = Mock()
        mock_hand.hand_number = i + 1
        mock_hand.human_cards = ["Ah", "Kh"]
        mock_hand.community_cards = ["Qh", "Jh", "Th"]
        mock_hand.pot_size = 100
        mock_hand.human_final_stack = 1000
        mock_hand.human_action = "call"
        mock_hand.winner_ids = ["human"]
        mock_hand.betting_rounds = []
        mock_hands.append(mock_hand)

    mock_game.hand_history = mock_hands
    return mock_game


@pytest.mark.asyncio
async def test_hand_count_parameter_slices_history(game_with_history):
    """
    Test that hand_count parameter is respected and hand_history is sliced
    BEFORE calling the analyzer, not inside it.

    This test verifies:
    1. Only the requested number of hands is analyzed
    2. The returned hands_analyzed count matches hand_count
    3. The LLM analyzer receives the correctly sliced history

    RED: This should FAIL before fix because main.py passes full hand_history
    """
    game_id = "test_game_hand_count"
    games[game_id] = (game_with_history, time.time())

    # Clear any cached results
    analysis_cache.clear()

    # Mock the LLM analyzer to track what it receives
    with patch('main.llm_analyzer') as mock_analyzer:
        # Configure mock to return success
        mock_analyzer.analyze_session.return_value = {
            "session_summary": "Test summary",
            "hands_analyzed": 5,
            "overall_stats": {}
        }

        # Mock LLM_ENABLED
        with patch('main.LLM_ENABLED', True):
            # Call endpoint directly
            result = await main.get_session_analysis(
                game_id=game_id,
                depth="quick",
                hand_count=5,
                use_cache=False
            )

        # Verify the reported count matches request
        assert result["hands_analyzed"] == 5, \
            "Reported hands_analyzed should match requested hand_count"

        # Verify the analyzer was called with sliced history (not full history)
        mock_analyzer.analyze_session.assert_called_once()
        call_args = mock_analyzer.analyze_session.call_args

        # The hand_history argument should be a slice, not full history
        hand_history_arg = call_args.kwargs['hand_history']

        # CRITICAL: This assertion should FAIL before fix
        # main.py currently passes all 10 hands, not just last 5
        assert len(hand_history_arg) == 5, \
            f"Analyzer should receive only 5 hands, but received {len(hand_history_arg)}"

        # Verify it's the LAST 5 hands (not first 5)
        assert hand_history_arg[0].hand_number == 6, \
            "Should receive last 5 hands (hands 6-10), not first 5"
        assert hand_history_arg[-1].hand_number == 10, \
            "Last hand should be hand #10"


@pytest.mark.asyncio
async def test_rate_limiting_enforced_regardless_of_cache_flag(game_with_history):
    """
    Test that rate limiting is enforced even when use_cache=false.

    Currently, rate limiting only applies when use_cache=true, allowing
    users to spam analyses by always sending use_cache=false.

    RED: This should FAIL before fix because main.py only checks rate limit
    when use_cache is true (line 667)
    """
    game_id = "test_game_rate_limit"
    games[game_id] = (game_with_history, time.time())

    # Clear cache and rate limit tracking
    analysis_cache.clear()
    last_analysis_time.clear()

    # Mock the LLM analyzer to avoid actual API calls
    with patch('main.llm_analyzer') as mock_analyzer, \
         patch('main.LLM_ENABLED', True):
        mock_analyzer.analyze_session.return_value = {
            "session_summary": "Test summary",
            "hands_analyzed": 10,
            "overall_stats": {}
        }

        # First request should succeed
        result1 = await main.get_session_analysis(
            game_id=game_id,
            depth="quick",
            hand_count=None,
            use_cache=False
        )
        assert result1 is not None, "First request should succeed"

        # Immediate second request with use_cache=false should be rate limited
        # CRITICAL: This assertion should FAIL before fix
        # Currently, rate limiting is bypassed when use_cache=false
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await main.get_session_analysis(
                game_id=game_id,
                depth="quick",
                hand_count=None,
                use_cache=False
            )

        assert exc_info.value.status_code == 429, \
            f"Second request should be rate limited (429), but got {exc_info.value.status_code}"

        # Verify error message mentions rate limit
        error_detail = exc_info.value.detail
        assert "Rate limit" in error_detail or "Wait" in error_detail, \
            f"Error should mention rate limit, got: {error_detail}"


@pytest.mark.asyncio
async def test_hands_analyzed_count_matches_actual_sliced_history(game_with_history):
    """
    Test that hands_analyzed in response matches the actual number of hands
    sent to the analyzer.

    This catches the bug where main.py uses hands_to_analyze variable (line 653)
    but sends full hand_history (line 686).

    RED: Should FAIL because hands_analyzed reports 5 but analyzer receives 10
    """
    game_id = "test_game_count_match"
    games[game_id] = (game_with_history, time.time())

    # Clear cache
    analysis_cache.clear()

    # Mock analyzer and track actual call
    with patch('main.llm_analyzer') as mock_analyzer, \
         patch('main.LLM_ENABLED', True):
        # Track the hand_history length that was passed
        actual_history_length = None

        def capture_history_length(**kwargs):
            nonlocal actual_history_length
            actual_history_length = len(kwargs['hand_history'])
            return {
                "session_summary": "Test",
                "hands_analyzed": actual_history_length,
                "overall_stats": {}
            }

        mock_analyzer.analyze_session.side_effect = capture_history_length

        # Request 3 hands
        result = await main.get_session_analysis(
            game_id=game_id,
            depth="quick",
            hand_count=3,
            use_cache=False
        )

        # The reported count should match what was actually sent to analyzer
        # CRITICAL: This fails before fix because:
        # - main.py reports hands_to_analyze = 3 (line 653)
        # - But sends all 10 hands to analyzer (line 686)
        # - So actual_history_length = 10, but reported = 3
        assert result["hands_analyzed"] == actual_history_length, \
            f"Reported count ({result['hands_analyzed']}) should match actual count sent to analyzer ({actual_history_length})"
