import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import uuid

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hooks.game_engine_hooks import GameEngineHooks, get_game_engine_hooks
from stats.ai_decision_analyzer import AIDecisionAnalyzer
from stats.statistics_manager import StatisticsManager


class TestGameEngineHooks(unittest.TestCase):
    """Integration tests for the GameEngineHooks class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_decision_analyzer = MagicMock(spec=AIDecisionAnalyzer)
        self.mock_stats_manager = MagicMock(spec=StatisticsManager)
        
        # Sample data
        self.player_id = "test_player_123"
        self.session_id = "test_session_456"
        self.hand_id = "test_hand_789"
        self.hole_cards = ["Ah", "Kh"]
        self.community_cards = ["7s", "8d", "Qc"]
        self.game_state = {
            "community_cards": self.community_cards,
            "current_bet": 20,
            "game_state": "flop"
        }
        self.deck = ["2c", "3d", "4h", "5s", "6c"]
        self.pot_size = 120
        self.spr = 4.5
        self.decision = "call"
        self.decision_analysis = {
            "was_optimal": True,
            "matching_strategy": "Conservative"
        }
        self.winners = {"player1": 100, "player2": 50}
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_hooks_initialization(self, mock_get_stats, mock_get_analyzer):
        """Test that GameEngineHooks initializes correctly."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # Verify hooks initialized correctly
        self.assertEqual(hooks.decision_analyzer, self.mock_decision_analyzer)
        self.assertEqual(hooks.stats_manager, self.mock_stats_manager)
        self.assertIsNone(hooks.current_hand_id)
        self.assertEqual(hooks.hand_data, {})
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_start_session(self, mock_get_stats, mock_get_analyzer):
        """Test starting a session."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        self.mock_stats_manager.start_session.return_value = self.session_id
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # Start session without ID
        session_id = hooks.start_session()
        
        # Verify session was started
        self.assertEqual(session_id, self.session_id)
        self.mock_stats_manager.start_session.assert_called_once_with(None)
        
        # Start with a specific ID
        custom_id = "custom_session_id"
        hooks.start_session(custom_id)
        
        # Verify custom ID was used
        self.mock_stats_manager.start_session.assert_called_with(custom_id)
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_end_session(self, mock_get_stats, mock_get_analyzer):
        """Test ending a session."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # End session
        hooks.end_session(self.session_id)
        
        # Verify session was ended
        self.mock_stats_manager.end_session.assert_called_once_with(self.session_id)
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    @patch('uuid.uuid4')
    def test_start_hand(self, mock_uuid, mock_get_stats, mock_get_analyzer):
        """Test starting to track a hand."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        mock_uuid.return_value = self.hand_id
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # Start hand without ID
        hand_id = hooks.start_hand()
        
        # Verify hand was started
        self.assertEqual(hand_id, self.hand_id)
        self.assertEqual(hooks.current_hand_id, self.hand_id)
        self.assertEqual(hooks.hand_data["hand_id"], self.hand_id)
        self.assertEqual(hooks.hand_data["players"], {})
        self.assertEqual(hooks.hand_data["community_cards"], [])
        self.assertEqual(hooks.hand_data["pot_size"], 0)
        self.assertEqual(hooks.hand_data["current_bet"], 0)
        
        # Start with a specific ID
        custom_id = "custom_hand_id"
        hooks.start_hand(custom_id)
        
        # Verify custom ID was used
        self.assertEqual(hooks.current_hand_id, custom_id)
        self.assertEqual(hooks.hand_data["hand_id"], custom_id)
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_end_hand(self, mock_get_stats, mock_get_analyzer):
        """Test ending a hand."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        
        # Create hooks
        hooks = GameEngineHooks()
        hooks.current_hand_id = self.hand_id
        hooks.hand_data = {
            "hand_id": self.hand_id,
            "players": {
                self.player_id: [{"decision": "call"}]
            },
            "community_cards": self.community_cards
        }
        
        # End hand
        hooks.end_hand(self.winners)
        
        # Verify hand was ended
        self.assertIsNone(hooks.current_hand_id)
        self.assertEqual(hooks.hand_data, {})
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_track_human_decision(self, mock_get_stats, mock_get_analyzer):
        """Test tracking a human player's decision."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        self.mock_decision_analyzer.analyze_decision.return_value = self.decision_analysis
        
        # Create hooks
        hooks = GameEngineHooks()
        hooks.current_hand_id = self.hand_id
        hooks.hand_data = {
            "hand_id": self.hand_id,
            "players": {},
            "community_cards": []
        }
        
        # Track decision
        result = hooks.track_human_decision(
            player_id=self.player_id,
            decision=self.decision,
            hole_cards=self.hole_cards,
            game_state=self.game_state,
            deck=self.deck,
            pot_size=self.pot_size,
            spr=self.spr
        )
        
        # Verify decision was analyzed
        self.mock_decision_analyzer.analyze_decision.assert_called_once()
        self.assertEqual(result, self.decision_analysis)
        
        # Verify data was stored in hand_data
        self.assertIn(self.player_id, hooks.hand_data["players"])
        self.assertEqual(len(hooks.hand_data["players"][self.player_id]), 1)
        self.assertEqual(hooks.hand_data["players"][self.player_id][0], self.decision_analysis)
        
        # Check that hand_id was added to game state if missing
        call_args = self.mock_decision_analyzer.analyze_decision.call_args[1]
        self.assertEqual(call_args["game_state"]["hand_id"], self.hand_id)
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_get_learning_feedback(self, mock_get_stats, mock_get_analyzer):
        """Test getting learning feedback."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        
        # Create learning statistics mock
        mock_learning_stats = MagicMock()
        mock_learning_stats.get_recent_decisions.return_value = [
            {"decision": "fold", "was_optimal": False},
            {"decision": "call", "was_optimal": True}
        ]
        
        self.mock_stats_manager.get_learning_statistics.return_value = mock_learning_stats
        self.mock_decision_analyzer.generate_feedback.side_effect = [
            "Feedback 1", "Feedback 2"
        ]
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # Get feedback
        feedback = hooks.get_learning_feedback(self.player_id, 2)
        
        # Verify feedback was generated
        self.assertEqual(len(feedback), 2)
        self.assertEqual(feedback[0], "Feedback 1")
        self.assertEqual(feedback[1], "Feedback 2")
        
        # Check the right statistics were retrieved
        self.mock_stats_manager.get_learning_statistics.assert_called_once_with(self.player_id)
        mock_learning_stats.get_recent_decisions.assert_called_once_with(2)
        
    @patch('hooks.game_engine_hooks.get_decision_analyzer')
    @patch('hooks.game_engine_hooks.get_statistics_manager')
    def test_get_strategy_profile(self, mock_get_stats, mock_get_analyzer):
        """Test getting a player's strategy profile."""
        # Setup mocks
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_stats.return_value = self.mock_stats_manager
        
        expected_profile = {
            "dominant_strategy": "Conservative",
            "decision_accuracy": 75.0
        }
        
        self.mock_decision_analyzer.get_player_strategy_profile.return_value = expected_profile
        
        # Create hooks
        hooks = GameEngineHooks()
        
        # Get profile
        profile = hooks.get_strategy_profile(self.player_id)
        
        # Verify profile was retrieved
        self.assertEqual(profile, expected_profile)
        self.mock_decision_analyzer.get_player_strategy_profile.assert_called_once_with(
            self.player_id
        )
        
    def test_get_game_engine_hooks_singleton(self):
        """Test that get_game_engine_hooks returns a singleton instance."""
        # Reset the singleton
        import hooks.game_engine_hooks
        hooks.game_engine_hooks._game_engine_hooks = None
        
        # Get hooks twice
        hooks1 = get_game_engine_hooks()
        hooks2 = get_game_engine_hooks()
        
        # Should be the same instance
        self.assertIs(hooks1, hooks2)


if __name__ == '__main__':
    unittest.main()