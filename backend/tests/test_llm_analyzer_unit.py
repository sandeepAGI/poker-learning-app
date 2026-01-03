"""
Unit tests for LLM Hand Analyzer (Phase 4).

Tests core functionality WITHOUT making expensive API calls.
Uses mocking to test logic in isolation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from game.poker_engine import CompletedHand, BettingRound, ActionRecord, AIDecision
from llm_analyzer import LLMHandAnalyzer


class TestLLMAnalyzerInitialization:
    """Test LLM analyzer initialization and configuration."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_initialization_with_api_key(self):
        """Test successful initialization with API key."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            assert analyzer.haiku_model == "claude-haiku-4-5"
            assert analyzer.sonnet_model == "claude-sonnet-4-5-20250929"

    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch('llm_analyzer.Anthropic'):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                LLMHandAnalyzer()

    @patch.dict('os.environ', {
        'ANTHROPIC_API_KEY': 'sk-ant-api03-test123',
        'LLM_MODEL_QUICK': 'custom-haiku',
        'LLM_MODEL_DEEP': 'custom-sonnet'
    })
    def test_initialization_with_custom_models(self):
        """Test initialization with custom model names from env vars."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            assert analyzer.haiku_model == "custom-haiku"
            assert analyzer.sonnet_model == "custom-sonnet"


class TestHistoryLimiting:
    """Test intelligent history limiting for cost control."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_history_limit_first_5_analyses(self):
        """First 5 analyses get full 50-hand history."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            assert analyzer._get_history_limit(1) == 50
            assert analyzer._get_history_limit(3) == 50
            assert analyzer._get_history_limit(5) == 50

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_history_limit_analyses_6_to_20(self):
        """Analyses 6-20 get 30-hand history."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            assert analyzer._get_history_limit(6) == 30
            assert analyzer._get_history_limit(10) == 30
            assert analyzer._get_history_limit(20) == 30

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_history_limit_analyses_21_plus(self):
        """Analyses 21+ get minimal 20-hand history."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            assert analyzer._get_history_limit(21) == 20
            assert analyzer._get_history_limit(50) == 20
            assert analyzer._get_history_limit(100) == 20


class TestPlayerStatsCalculation:
    """Test player statistics calculation from hand history."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_empty_history(self):
        """Test stats calculation with no history."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            stats = analyzer._calculate_player_stats([])

            assert stats["hands_played"] == 0
            assert stats["win_rate"] == 0.0
            assert stats["vpip"] == 0.0
            assert stats["pfr"] == 0.0
            assert stats["biggest_win"] == 0
            assert stats["biggest_loss"] == 0

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create 5 hands: 3 wins, 2 losses
            hands = []
            for i in range(5):
                hand = Mock(spec=CompletedHand)
                hand.hand_number = i + 1
                hand.winner_ids = ["human"] if i < 3 else ["ai1"]
                hand.human_action = "call"
                hand.pot_size = 100
                hand.betting_rounds = []
                hands.append(hand)

            stats = analyzer._calculate_player_stats(hands)

            assert stats["hands_played"] == 5
            assert stats["win_rate"] == 60.0  # 3/5 = 60%

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_vpip_calculation(self):
        """Test VPIP (Voluntarily Put money In Pot) calculation."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create 10 hands: 7 active (call/raise), 3 folds
            hands = []
            actions = ["call", "raise", "call", "fold", "raise", "call", "fold", "raise", "call", "fold"]
            for i, action in enumerate(actions):
                hand = Mock(spec=CompletedHand)
                hand.hand_number = i + 1
                hand.winner_ids = ["ai1"]
                hand.human_action = action
                hand.pot_size = 100
                hand.betting_rounds = []
                hands.append(hand)

            stats = analyzer._calculate_player_stats(hands)

            assert stats["vpip"] == 70.0  # 7/10 = 70%


class TestBettingRoundFormatting:
    """Test formatting of betting rounds for LLM consumption."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_empty_betting_rounds(self):
        """Test formatting when no betting rounds exist."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            formatted = analyzer._format_betting_rounds([])
            assert formatted == "No betting rounds recorded"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_betting_round_with_actions(self):
        """Test formatting of betting round with actions."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create a pre-flop round
            action1 = ActionRecord(
                player_id="human",
                player_name="Player",
                action="raise",
                amount=20,
                stack_before=1000,
                stack_after=980,
                pot_before=15,
                pot_after=35,
                reasoning=""
            )
            action2 = ActionRecord(
                player_id="ai1",
                player_name="AI Bot",
                action="call",
                amount=20,
                stack_before=1000,
                stack_after=980,
                pot_before=35,
                pot_after=55,
                reasoning="Good pot odds"
            )

            round_obj = BettingRound(
                round_name="pre-flop",
                pot_at_start=15,
                pot_at_end=55,
                actions=[action1, action2],
                community_cards=[]
            )

            formatted = analyzer._format_betting_rounds([round_obj])

            # Check key elements are present
            assert "PRE-FLOP" in formatted
            assert "Pot: $15 → $55" in formatted
            assert "Player: raise $20" in formatted
            assert "AI Bot: call $20 (Good pot odds)" in formatted


class TestShowdownFormatting:
    """Test formatting of showdown data."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_no_showdown(self):
        """Test formatting when no showdown occurred."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            formatted = analyzer._format_showdown({}, {})
            assert "No showdown" in formatted

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_showdown_with_hands(self):
        """Test formatting of showdown with player hands."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            showdown_hands = {
                "human": ["Ah", "Kh"],
                "ai1": ["Qd", "Qc"]
            }
            hand_rankings = {
                "human": "High Card (Ace)",
                "ai1": "Pair of Queens"
            }

            formatted = analyzer._format_showdown(showdown_hands, hand_rankings)

            assert "human: Ah Kh (High Card (Ace))" in formatted
            assert "ai1: Qd Qc (Pair of Queens)" in formatted


class TestAIOpponentsFormatting:
    """Test formatting of AI opponents information."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_no_ai_opponents(self):
        """Test formatting when no AI opponents."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()
            hand = Mock(spec=CompletedHand)
            hand.ai_decisions = {}

            formatted = analyzer._format_ai_opponents(hand)
            assert formatted == "No AI opponents"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_ai_opponents_formatting(self):
        """Test formatting of AI opponent decisions (without personality field)."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create AI decision (matching actual AIDecision dataclass)
            ai_decision = AIDecision(
                action="raise",
                amount=50,
                reasoning="Strong hand with good position",
                hand_strength=0.85,
                pot_odds=0.33,
                confidence=0.92,
                spr=5.0
            )

            hand = Mock(spec=CompletedHand)
            hand.ai_decisions = {"ai1": ai_decision}

            formatted = analyzer._format_ai_opponents(hand)

            # Verify formatting includes all fields (but NOT personality)
            assert "ai1" in formatted
            assert "Final action: raise" in formatted
            assert "Reasoning: Strong hand with good position" in formatted
            assert "Hand strength: 85.0%" in formatted
            assert "Confidence: 92.0%" in formatted
            # Should NOT contain personality reference
            assert "personality" not in formatted.lower()


class TestJSONParsing:
    """Test JSON parsing and cleanup logic."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_parse_direct_json(self):
        """Test parsing direct JSON response."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            response = '{"summary": "Good hand", "player_analysis": {}, "tips_for_improvement": []}'
            parsed = analyzer._parse_response(response)

            assert parsed["summary"] == "Good hand"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_parse_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            response = '''Here is the analysis:
```json
{
  "summary": "Great play",
  "player_analysis": {},
  "tips_for_improvement": []
}
```
'''
            parsed = analyzer._parse_response(response)

            assert parsed["summary"] == "Great play"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_parse_json_with_trailing_commas(self):
        """Test parsing JSON with trailing commas (cleanup)."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Invalid JSON with trailing commas
            response = '{"summary": "Good hand", "player_analysis": {}, "tips_for_improvement": [],}'
            parsed = analyzer._parse_response(response)

            assert parsed["summary"] == "Good hand"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_parse_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises error."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            response = 'This is not JSON at all!'

            with pytest.raises(ValueError, match="Failed to parse LLM response"):
                analyzer._parse_response(response)


class TestAnalysisValidation:
    """Test analysis quality validation."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_valid_analysis(self):
        """Test validation of complete, valid analysis."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            analysis = {
                "summary": "This is a good summary with enough length",
                "player_analysis": {"good_decisions": [], "questionable_decisions": []},
                "tips_for_improvement": [
                    {
                        "category": "Pre-flop",
                        "observation": "You folded too often",
                        "actionable_step": "Study position-based ranges"
                    }
                ]
            }

            assert analyzer._validate_analysis(analysis) is True

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_missing_required_fields(self):
        """Test validation fails with missing fields."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            analysis = {
                "summary": "Good summary",
                # Missing player_analysis and tips_for_improvement
            }

            assert analyzer._validate_analysis(analysis) is False

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_summary_too_short(self):
        """Test validation fails with too-short summary."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            analysis = {
                "summary": "Too short",  # Less than 20 chars
                "player_analysis": {},
                "tips_for_improvement": [{"actionable_step": "Do this"}]
            }

            assert analyzer._validate_analysis(analysis) is False

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_no_tips(self):
        """Test validation fails with no tips."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            analysis = {
                "summary": "This is a good summary with enough length",
                "player_analysis": {},
                "tips_for_improvement": []  # Empty tips list
            }

            assert analyzer._validate_analysis(analysis) is False

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_tips_missing_actionable_step(self):
        """Test validation fails when tips lack actionable_step."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            analysis = {
                "summary": "This is a good summary with enough length",
                "player_analysis": {},
                "tips_for_improvement": [
                    {
                        "category": "Pre-flop",
                        "observation": "You folded too often"
                        # Missing actionable_step
                    }
                ]
            }

            assert analyzer._validate_analysis(analysis) is False


class TestContextBuilding:
    """Test comprehensive context building for LLM."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_context_structure(self):
        """Test that context has all required fields."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create minimal hand
            hand = Mock(spec=CompletedHand)
            hand.hand_number = 5
            hand.timestamp = "2025-01-01T12:00:00"
            hand.session_id = "test-session"
            hand.human_cards = ["Ah", "Kh"]
            hand.human_action = "raise"
            hand.human_final_stack = 1050
            hand.community_cards = ["Qh", "Jh", "10h"]
            hand.pot_size = 150
            hand.winner_ids = ["human"]
            hand.betting_rounds = []
            hand.showdown_hands = {}
            hand.hand_rankings = {}
            hand.ai_decisions = {}

            context = analyzer._build_context(hand, [], 1)

            # Check all required fields exist
            required_fields = [
                "hand_number", "timestamp", "session_id", "total_hands",
                "hands_played", "win_rate", "vpip", "pfr", "biggest_win", "biggest_loss",
                "human_name", "stack_start", "stack_end", "hole_cards", "final_action",
                "result_description", "formatted_betting_rounds", "community_cards",
                "formatted_showdown_data", "formatted_ai_opponents", "history_count"
            ]

            for field in required_fields:
                assert field in context, f"Missing required field: {field}"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-api03-test123'})
    def test_history_limiting_in_context(self):
        """Test that context respects history limits."""
        with patch('llm_analyzer.Anthropic'):
            analyzer = LLMHandAnalyzer()

            # Create 100 mock hands in history
            history = []
            for i in range(100):
                hand = Mock(spec=CompletedHand)
                hand.hand_number = i + 1
                hand.winner_ids = ["ai1"]
                hand.human_action = "fold"
                hand.human_cards = ["2h", "3c"]
                hand.pot_size = 50
                hand.betting_rounds = []
                history.append(hand)

            # Create current hand
            current_hand = Mock(spec=CompletedHand)
            current_hand.hand_number = 101
            current_hand.timestamp = "2025-01-01T12:00:00"
            current_hand.session_id = "test"
            current_hand.human_cards = ["2h", "3h"]
            current_hand.human_action = "fold"
            current_hand.human_final_stack = 1000
            current_hand.community_cards = []
            current_hand.pot_size = 15
            current_hand.winner_ids = ["ai1"]
            current_hand.betting_rounds = []
            current_hand.showdown_hands = {}
            current_hand.hand_rankings = {}
            current_hand.ai_decisions = {}

            # Test different analysis counts
            context1 = analyzer._build_context(current_hand, history, 1)
            assert context1["history_count"] == 50  # First 5 analyses get 50 hands

            context2 = analyzer._build_context(current_hand, history, 10)
            assert context2["history_count"] == 30  # Analyses 6-20 get 30 hands

            context3 = analyzer._build_context(current_hand, history, 25)
            assert context3["history_count"] == 20  # Analyses 21+ get 20 hands


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
