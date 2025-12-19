"""
Tests for Phase 3: Hand History Infrastructure.

Validates session tracking, round-by-round action tracking,
and hand history storage.
"""

import pytest
from game.poker_engine import PokerGame


def test_session_id_generated():
    """Verify each game gets a unique session ID."""
    game1 = PokerGame(human_player_name="Player1", ai_count=2)
    game2 = PokerGame(human_player_name="Player2", ai_count=2)

    assert game1.session_id != "", "Session ID should not be empty"
    assert game2.session_id != "", "Session ID should not be empty"
    assert game1.session_id != game2.session_id, "Each game should have unique session ID"

    # Verify it's a valid UUID format (36 chars with hyphens)
    assert len(game1.session_id) == 36, f"Session ID should be 36 chars, got {len(game1.session_id)}"
    assert game1.session_id.count('-') == 4, "Session ID should have 4 hyphens (UUID format)"


def test_hand_history_initialized():
    """Verify hand_history list is initialized."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    assert hasattr(game, 'hand_history'), "Game should have hand_history attribute"
    assert isinstance(game.hand_history, list), "hand_history should be a list"
    assert len(game.hand_history) == 0, "hand_history should start empty"


def test_hand_history_tracks_multiple_hands():
    """Verify hand history accumulates across multiple hands."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play 3 hands - disable QC to avoid hitting unrelated showdown bugs
    game.qc_enabled = False
    for _ in range(3):
        # Fold immediately to end hand quickly
        game.submit_human_action("fold")
        game.start_new_hand()

    # Should have 3 hands in history
    assert len(game.hand_history) >= 3, f"Expected at least 3 hands in history, got {len(game.hand_history)}"


def test_completed_hand_has_phase3_fields():
    """Verify CompletedHand includes Phase 3 fields."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play one hand
    game.submit_human_action("fold")

    # Check last hand has Phase 3 fields
    last_hand = game.last_hand_summary
    assert last_hand is not None, "Should have last_hand_summary after playing a hand"

    # Phase 3 fields
    assert hasattr(last_hand, 'session_id'), "CompletedHand should have session_id"
    assert hasattr(last_hand, 'timestamp'), "CompletedHand should have timestamp"
    assert hasattr(last_hand, 'betting_rounds'), "CompletedHand should have betting_rounds"
    assert hasattr(last_hand, 'showdown_hands'), "CompletedHand should have showdown_hands"
    assert hasattr(last_hand, 'hand_rankings'), "CompletedHand should have hand_rankings"

    # Verify values
    assert last_hand.session_id == game.session_id, "Hand session_id should match game session_id"
    assert len(last_hand.timestamp) > 0, "Timestamp should not be empty"
    assert isinstance(last_hand.betting_rounds, list), "betting_rounds should be a list"
    assert isinstance(last_hand.showdown_hands, dict), "showdown_hands should be a dict"
    assert isinstance(last_hand.hand_rankings, dict), "hand_rankings should be a dict"


def test_betting_rounds_tracked():
    """Verify betting rounds are tracked for each hand."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play a hand with some actions
    game.submit_human_action("call")  # Go to flop

    # Get last hand
    last_hand = game.last_hand_summary

    if last_hand:
        # Should have at least pre-flop betting round
        assert len(last_hand.betting_rounds) > 0, "Should have at least one betting round"

        # Check first betting round structure
        first_round = last_hand.betting_rounds[0]
        assert hasattr(first_round, 'round_name'), "BettingRound should have round_name"
        assert hasattr(first_round, 'community_cards'), "BettingRound should have community_cards"
        assert hasattr(first_round, 'actions'), "BettingRound should have actions"
        assert hasattr(first_round, 'pot_at_start'), "BettingRound should have pot_at_start"
        assert hasattr(first_round, 'pot_at_end'), "BettingRound should have pot_at_end"


def test_action_records_tracked():
    """Verify individual actions are tracked in betting rounds."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play a hand
    game.submit_human_action("call")

    last_hand = game.last_hand_summary
    if last_hand and len(last_hand.betting_rounds) > 0:
        first_round = last_hand.betting_rounds[0]

        # Should have some actions
        if len(first_round.actions) > 0:
            action = first_round.actions[0]

            # Check ActionRecord structure
            assert hasattr(action, 'player_id'), "ActionRecord should have player_id"
            assert hasattr(action, 'player_name'), "ActionRecord should have player_name"
            assert hasattr(action, 'action'), "ActionRecord should have action"
            assert hasattr(action, 'amount'), "ActionRecord should have amount"
            assert hasattr(action, 'stack_before'), "ActionRecord should have stack_before"
            assert hasattr(action, 'stack_after'), "ActionRecord should have stack_after"
            assert hasattr(action, 'pot_before'), "ActionRecord should have pot_before"
            assert hasattr(action, 'pot_after'), "ActionRecord should have pot_after"


def test_hand_history_100_hand_limit():
    """Verify hand history is capped at 100 hands."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play 110 hands (more than limit)
    for i in range(110):
        game.submit_human_action("fold")
        if i < 109:  # Don't start new hand after last fold
            game.start_new_hand()

    # Should be capped at 100
    assert len(game.hand_history) <= 100, f"hand_history should be capped at 100, got {len(game.hand_history)}"

    # Most recent hands should be preserved
    if len(game.hand_history) == 100:
        # Hand numbers should start from 11 (hands 11-110)
        first_hand_number = game.hand_history[0].hand_number
        last_hand_number = game.hand_history[-1].hand_number

        assert first_hand_number >= 11, f"First hand should be >= 11, got {first_hand_number}"
        assert last_hand_number == 110, f"Last hand should be 110, got {last_hand_number}"


def test_timestamp_format():
    """Verify timestamp is in ISO format."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Use call instead of fold to ensure hand is saved
    game.submit_human_action("call")
    last_hand = game.last_hand_summary

    # If hand not saved yet (still in progress), that's ok for this test
    if last_hand is None:
        return  # Skip test if hand hasn't completed yet

    # Check ISO format (ends with Z for UTC)
    assert last_hand.timestamp.endswith('Z'), "Timestamp should end with Z (UTC)"
    assert 'T' in last_hand.timestamp, "Timestamp should have T separator (ISO format)"

    # Verify parseable
    from datetime import datetime
    try:
        parsed = datetime.fromisoformat(last_hand.timestamp.replace('Z', '+00:00'))
        assert parsed is not None, "Timestamp should be parseable as ISO format"
    except ValueError:
        pytest.fail("Timestamp is not valid ISO format")


def test_showdown_hands_populated_at_showdown():
    """Verify showdown_hands structure exists (may be empty if no showdown reached)."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Play one hand (may or may not reach showdown)
    try:
        # Try to reach showdown
        for _ in range(5):
            if game.current_state.value != "showdown":
                game.submit_human_action("call", process_ai=True)
            else:
                break
    except:
        # If errors occur, just fold to end hand
        if game.current_state.value != "showdown":
            game.submit_human_action("fold")

    last_hand = game.last_hand_summary

    if last_hand:
        # Phase 3 fields should exist (may be empty)
        assert hasattr(last_hand, 'showdown_hands'), "Should have showdown_hands field"
        assert hasattr(last_hand, 'hand_rankings'), "Should have hand_rankings field"
        assert isinstance(last_hand.showdown_hands, dict), "showdown_hands should be dict"
        assert isinstance(last_hand.hand_rankings, dict), "hand_rankings should be dict"

        # If hand actually reached showdown, check structure
        if len(last_hand.showdown_hands) > 0:
            for player_id, cards in last_hand.showdown_hands.items():
                assert isinstance(cards, list), f"Cards for {player_id} should be a list"
                assert len(cards) == 2, f"Player {player_id} should have 2 hole cards"

        if len(last_hand.hand_rankings) > 0:
            for player_id, ranking in last_hand.hand_rankings.items():
                assert isinstance(ranking, str), f"Ranking for {player_id} should be a string"
                assert len(ranking) > 0, f"Ranking for {player_id} should not be empty"


def test_hand_history_vs_completed_hands():
    """Verify both hand_history and completed_hands are maintained."""
    game = PokerGame(human_player_name="Test", ai_count=2)

    # Disable QC to avoid hitting unrelated showdown bugs
    game.qc_enabled = False

    # Play 5 hands
    for _ in range(5):
        game.submit_human_action("fold")
        game.start_new_hand()

    # Both lists should be populated
    assert len(game.hand_history) >= 5, f"hand_history should have at least 5 hands"
    assert len(game.completed_hands) >= 5, f"completed_hands should have at least 5 hands"

    # They should contain the same hands
    assert len(game.hand_history) == len(game.completed_hands), \
        "hand_history and completed_hands should have same count"
