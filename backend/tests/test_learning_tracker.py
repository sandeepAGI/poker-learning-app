import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.learning_tracker import LearningTracker
from stats.statistics_manager import StatisticsManager
from stats.ai_decision_analyzer import AIDecisionAnalyzer


class TestLearningTracker(unittest.TestCase):
    """Integration tests for the LearningTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_stats_manager = MagicMock(spec=StatisticsManager)
        self.mock_decision_analyzer = MagicMock(spec=AIDecisionAnalyzer)
        self.mock_hooks = MagicMock()
        
        # Sample data for testing
        self.player_id = "test_player_123"
        self.session_id = "test_session_456"
        self.hand_id = "test_hand_789"
        self.hole_cards = ["Ah", "Kh"]
        self.game_state = {
            "community_cards": ["7s", "8d", "Qc"],
            "current_bet": 20,
            "game_state": "flop"
        }
        self.deck = ["2c", "3d", "4h", "5s", "6c"]
        self.pot_size = 120
        self.spr = 4.5
        self.decision = "call"

    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_learning_tracker_initialization(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test that LearningTracker initializes correctly."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        
        # Create tracker
        tracker = LearningTracker()
        
        # Verify initialization
        self.assertTrue(tracker.enabled)
        self.assertEqual(tracker.stats_manager, self.mock_stats_manager)
        self.assertEqual(tracker.decision_analyzer, self.mock_decision_analyzer)
        self.assertEqual(tracker.hooks, self.mock_hooks)
        self.assertIsNone(tracker.session_id)
        self.assertIsNone(tracker.current_hand_id)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_start_session(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test starting a session."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        self.mock_hooks.start_session.return_value = self.session_id
        
        # Create tracker and start session
        tracker = LearningTracker()
        result = tracker.start_session()
        
        # Verify session was started
        self.assertEqual(result, self.session_id)
        self.assertEqual(tracker.session_id, self.session_id)
        self.mock_hooks.start_session.assert_called_once()
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_end_session(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test ending a session."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        
        # Create tracker and set session ID
        tracker = LearningTracker()
        tracker.session_id = self.session_id
        
        # End session
        tracker.end_session()
        
        # Verify session was ended
        self.mock_hooks.end_session.assert_called_once_with(self.session_id)
        self.assertIsNone(tracker.session_id)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_start_hand(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test starting a hand."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        self.mock_hooks.start_hand.return_value = self.hand_id
        
        # Create tracker
        tracker = LearningTracker()
        
        # Start hand
        result = tracker.start_hand()
        
        # Verify hand was started
        self.assertEqual(result, self.hand_id)
        self.assertEqual(tracker.current_hand_id, self.hand_id)
        self.mock_hooks.start_hand.assert_called_once()
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_end_hand(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test ending a hand."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        
        # Create tracker and set hand ID
        tracker = LearningTracker()
        tracker.current_hand_id = self.hand_id
        
        # End hand with winners
        winners = {"player1": 100, "player2": 50}
        tracker.end_hand(winners)
        
        # Verify hand was ended
        self.mock_hooks.end_hand.assert_called_once_with(winners)
        self.assertIsNone(tracker.current_hand_id)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_track_decision(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test tracking a player's decision."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        
        # Create tracker and set hand ID
        tracker = LearningTracker()
        tracker.current_hand_id = self.hand_id
        
        # Track decision
        tracker.track_decision(
            player_id=self.player_id,
            decision=self.decision,
            hole_cards=self.hole_cards,
            game_state=self.game_state,
            deck=self.deck,
            pot_size=self.pot_size,
            spr=self.spr
        )
        
        # Verify decision was tracked
        self.mock_hooks.track_human_decision.assert_called_once()
        
        # Check that hand ID was added to game state
        call_args = self.mock_hooks.track_human_decision.call_args[1]
        tracking_game_state = call_args["game_state"]
        self.assertEqual(tracking_game_state["hand_id"], self.hand_id)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_get_learning_feedback(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test getting learning feedback."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        expected_feedback = ["Some feedback", "More feedback"]
        self.mock_hooks.get_learning_feedback.return_value = expected_feedback
        
        # Create tracker
        tracker = LearningTracker()
        
        # Get feedback
        feedback = tracker.get_learning_feedback(self.player_id, 2)
        
        # Verify feedback was retrieved
        self.assertEqual(feedback, expected_feedback)
        self.mock_hooks.get_learning_feedback.assert_called_once_with(self.player_id, 2)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_get_strategy_profile(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test getting a player's strategy profile."""
        # Setup mocks
        mock_get_stats.return_value = self.mock_stats_manager
        mock_get_analyzer.return_value = self.mock_decision_analyzer
        mock_get_hooks.return_value = self.mock_hooks
        expected_profile = {
            "dominant_strategy": "Conservative",
            "decision_accuracy": 75.0
        }
        self.mock_hooks.get_strategy_profile.return_value = expected_profile
        
        # Create tracker
        tracker = LearningTracker()
        
        # Get profile
        profile = tracker.get_strategy_profile(self.player_id)
        
        # Verify profile was retrieved
        self.assertEqual(profile, expected_profile)
        self.mock_hooks.get_strategy_profile.assert_called_once_with(self.player_id)
        
    @patch('game.learning_tracker.get_statistics_manager')
    @patch('game.learning_tracker.get_decision_analyzer')
    @patch('game.learning_tracker.get_game_engine_hooks')
    def test_graceful_failure_handling(self, mock_get_hooks, mock_get_analyzer, mock_get_stats):
        """Test that errors are handled gracefully."""
        # Setup mocks to raise exceptions
        mock_get_stats.side_effect = ImportError("Stats not available")
        
        # Create tracker
        tracker = LearningTracker()
        
        # Verify tracker is disabled but doesn't crash
        self.assertFalse(tracker.enabled)
        
        # Test methods don't fail when disabled
        self.assertIsNone(tracker.start_session())
        self.assertIsNone(tracker.start_hand())
        tracker.end_session()  # Should not raise errors
        tracker.end_hand({})  # Should not raise errors
        
        # Should return a fallback message
        self.assertEqual(
            tracker.get_learning_feedback(self.player_id),
            ["Learning statistics not enabled"]
        )
        
        # Should return error info
        self.assertEqual(
            tracker.get_strategy_profile(self.player_id),
            {"error": "Learning statistics not enabled"}
        )


if __name__ == '__main__':
    unittest.main()