import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json
import tempfile
import shutil
import time

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.statistics_manager import StatisticsManager, get_statistics_manager
from stats.learning_statistics import LearningStatistics


class TestStatisticsManager(unittest.TestCase):
    """Tests for the StatisticsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Patch the DATA_DIR to use our temporary directory
        self.data_dir_patcher = patch('stats.statistics_manager.StatisticsManager.DATA_DIR', 
                                   new=self.test_dir)
        self.data_dir_patcher.start()
        
        # Create the manager
        self.manager = StatisticsManager()
        
        # Sample data
        self.player_id = "test_player_123"
        self.session_id = "test_session_456"
        
        # Sample decision data
        self.decision_data = {
            "hand_id": "hand_789",
            "game_state": "flop",
            "decision": "call",
            "hole_cards": ["Ah", "Kh"],
            "community_cards": ["7s", "8d", "Qc"],
            "pot_size": 120,
            "spr": 4.5,
            "current_bet": 20,
            "matching_strategy": "Conservative",
            "optimal_strategy": "Conservative",
            "was_optimal": True,
            "expected_value": 0.8,
            "strategy_decisions": {
                "Conservative": "call",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "fold"
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Stop the DATA_DIR patch
        self.data_dir_patcher.stop()
        
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_start_session(self):
        """Test starting a new session."""
        # Start a session with a specific ID
        session_id = self.manager.start_session(self.session_id)
        
        # Check that the session was created correctly
        self.assertEqual(session_id, self.session_id)
        self.assertEqual(self.manager.current_session_id, self.session_id)
        self.assertIn(self.session_id, self.manager._session_stats)
        
        # Start a session without an ID (should generate one)
        self.manager.current_session_id = None
        new_session_id = self.manager.start_session()
        
        # Check that a new session was created
        self.assertIsNotNone(new_session_id)
        self.assertNotEqual(new_session_id, self.session_id)
        self.assertEqual(self.manager.current_session_id, new_session_id)
        
    def test_end_session(self):
        """Test ending a session."""
        # Start a session
        self.manager.start_session(self.session_id)
        
        # Create required directories for session storage
        os.makedirs(os.path.join(self.test_dir, "sessions"), exist_ok=True)
        
        # Mock _save_session_statistics to avoid actual file operations
        with patch.object(self.manager, '_save_session_statistics') as mock_save:
            # End the session
            self.manager.end_session(self.session_id)
            
            # Check that the session was properly ended
            self.assertIsNone(self.manager.current_session_id)
            self.assertIsNotNone(self.manager._session_stats[self.session_id].end_time)
            
            # Check that the session was saved
            mock_save.assert_called_once_with(self.session_id)
            
    def test_get_learning_statistics_new(self):
        """Test getting learning statistics for a new player."""
        # Create required directories for learning statistics storage
        os.makedirs(os.path.join(self.test_dir, "learning"), exist_ok=True)
        
        # Get learning statistics for a new player
        stats = self.manager.get_learning_statistics(self.player_id)
        
        # Check that new statistics were created
        self.assertIsInstance(stats, LearningStatistics)
        self.assertEqual(stats.player_id, self.player_id)
        self.assertEqual(stats.total_decisions, 0)
        
        # Check that the statistics were cached
        self.assertIn(self.player_id, self.manager._learning_stats)
        
    def test_get_learning_statistics_existing(self):
        """Test getting learning statistics for an existing player."""
        # Create a mock learning statistics object
        mock_stats = LearningStatistics(self.player_id)
        mock_stats.total_decisions = 10  # Add some data to distinguish it
        
        # Add to manager's cache
        self.manager._learning_stats[self.player_id] = mock_stats
        
        # Get the statistics
        stats = self.manager.get_learning_statistics(self.player_id)
        
        # Should return the cached instance
        self.assertIs(stats, mock_stats)
        self.assertEqual(stats.total_decisions, 10)
        
    def test_record_decision(self):
        """Test recording a player's decision."""
        # Start a session
        self.manager.start_session(self.session_id)
        
        # Create required directories
        os.makedirs(os.path.join(self.test_dir, "learning"), exist_ok=True)
        
        # Mock the _save_learning_statistics method
        with patch.object(self.manager, '_save_learning_statistics') as mock_save:
            # Record a decision
            self.manager.record_decision(self.player_id, self.decision_data)
            
            # Check that the decision was added to learning statistics
            self.assertIn(self.player_id, self.manager._learning_stats)
            learning_stats = self.manager._learning_stats[self.player_id]
            self.assertEqual(learning_stats.total_decisions, 1)
            self.assertEqual(learning_stats.decisions_by_strategy["Conservative"], 1)
            
            # Check that timestamp and session_id were added
            recorded_decision = learning_stats.decision_history[0]
            self.assertIn("timestamp", recorded_decision)
            self.assertEqual(recorded_decision["session_id"], self.session_id)
            
            # Check that statistics were saved
            mock_save.assert_called_once_with(self.player_id)
            
    def test_load_learning_statistics(self):
        """Test loading learning statistics from disk."""
        # Create required directories
        learning_dir = os.path.join(self.test_dir, "learning")
        os.makedirs(learning_dir, exist_ok=True)
        
        # Create a sample statistics file
        stats = LearningStatistics(self.player_id)
        stats.total_decisions = 5
        stats.correct_decisions = 3
        stats_dict = stats.to_dict()
        
        file_path = os.path.join(learning_dir, f"{self.player_id}.json")
        with open(file_path, 'w') as f:
            json.dump(stats_dict, f)
            
        # Load the statistics
        self.manager._load_learning_statistics(self.player_id)
        
        # Check that the statistics were loaded correctly
        self.assertIn(self.player_id, self.manager._learning_stats)
        loaded_stats = self.manager._learning_stats[self.player_id]
        self.assertEqual(loaded_stats.player_id, self.player_id)
        self.assertEqual(loaded_stats.total_decisions, 5)
        self.assertEqual(loaded_stats.correct_decisions, 3)
        
    @patch('os.path.getmtime')
    @patch('os.listdir')
    def test_prune_old_sessions(self, mock_listdir, mock_getmtime):
        """Test pruning old session data."""
        # Setup mock session files (more than MAX_SESSIONS)
        session_files = [f"session_{i}.json" for i in range(10)]
        mock_listdir.return_value = session_files
        
        # Setup mock modification times (oldest first)
        # Extract the number from session_N.json to use as the timestamp
        mock_getmtime.side_effect = lambda path: int(os.path.basename(path).split('_')[1].split('.')[0])
        
        # Mock the learning statistics with decision history
        learning_stats = MagicMock()
        learning_stats.decision_history = [
            {"session_id": f"session_{i}"} for i in range(10)
        ]
        self.manager._learning_stats = {"player1": learning_stats}
        
        # Mock _save_learning_statistics to avoid file operations
        with patch.object(self.manager, '_save_learning_statistics') as mock_save:
            # Prune old sessions
            self.manager._prune_old_sessions()
            
            # Check that decision history was filtered
            # Only decisions from sessions 5-9 should remain (5 sessions)
            expected_sessions = {f"session_{i}" for i in range(5, 10)}
            actual_sessions = {d["session_id"] for d in learning_stats.decision_history}
            self.assertEqual(actual_sessions, expected_sessions)
            
            # Check that learning statistics were saved
            mock_save.assert_called_with("player1")
            
    def test_get_statistics_manager_singleton(self):
        """Test that get_statistics_manager returns a singleton instance."""
        # Reset the singleton
        import stats.statistics_manager
        stats.statistics_manager._statistics_manager = None
        
        # Get manager twice
        manager1 = get_statistics_manager()
        manager2 = get_statistics_manager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()