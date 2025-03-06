import unittest
import sys
import os
from unittest.mock import Mock, patch
import json

# Adjust the import paths to properly find modules
# This assumes the test is running from the "tests" directory within the backend folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Should be the backend directory
sys.path.insert(0, parent_dir)

from stats.learning_statistics import LearningStatistics
from stats.statistics_manager import StatisticsManager

class TestDataRetention(unittest.TestCase):
    """Test cases for data retention and lifecycle management."""

    def setUp(self):
        """
        Set up test environment before each test.
        """
        self.player_id = "test_player_123"
        
        # Mock the file operations to avoid actual disk I/O
        self.io_patcher = patch('stats.statistics_manager.open', create=True)
        self.mock_open = self.io_patcher.start()
        
        self.json_patcher = patch('stats.statistics_manager.json')
        self.mock_json = self.json_patcher.start()
        
        self.os_patcher = patch('stats.statistics_manager.os')
        self.mock_os = self.os_patcher.start()
        
        # Setup the statistics manager
        self.stats_manager = StatisticsManager()
        
        # Sample decision template
        self.decision_template = {
            "decision": "call",
            "matching_strategy": "Conservative",
            "optimal_strategy": "Conservative",
            "was_optimal": True,
            "spr": 4.5,
            "game_state": "flop",
            "hole_cards": ["Ah", "Kh"],
            "community_cards": ["7s", "8d", "Qc"],
            "pot_size": 120,
            "current_bet": 20,
            "strategy_decisions": {
                "Conservative": "call",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "fold"
            },
            "expected_value": 0.8
        }

    def tearDown(self):
        """Clean up after each test."""
        self.io_patcher.stop()
        self.json_patcher.stop()
        self.os_patcher.stop()

    def _create_decision(self, decision_id=None):
        """Helper to create a decision with specific attributes."""
        decision = self.decision_template.copy()
        if decision_id:
            decision["hand_id"] = f"hand_{decision_id}"
        return decision

    def test_D1_session_retention(self):
        """
        Test D1: Session Retention
        
        Test retention of recent sessions and their detailed decision data.
        """
        # Set up mock behavior
        self.mock_os.path.exists.return_value = False  # Let's assume no files exist yet
        
        # Create 5 sessions with decisions
        for session_idx in range(5):
            session_id = f"session_{session_idx}"
            
            # Start a new session
            self.stats_manager.start_session(session_id)
            
            # Add 10 decisions to the session
            for i in range(10):
                decision = self._create_decision(decision_id=f"{session_idx}_{i}")
                self.stats_manager.record_decision(self.player_id, decision)
            
            # End the session
            self.stats_manager.end_session(self.player_id, session_id)
        
        # Get learning statistics
        learning_stats = self.stats_manager.get_learning_statistics(self.player_id)
        
        # Assertions
        self.assertEqual(learning_stats.total_decisions, 50,
                        "Should have recorded 50 decisions (5 sessions * 10 decisions)")
        
        # Mock calls to verify data retention
        # 1. Check that temporary storage has been updated
        self.mock_json.dump.assert_called()  # Should have been called to save data
        
        # 2. Set up and check session meta data
        session_meta = self.stats_manager.session_meta.get(self.player_id, {})
        self.assertEqual(len(session_meta), 5,
                        "Should have meta data for 5 sessions")

    def test_D2_data_pruning(self):
        """
        Test D2: Data Pruning
        
        Test pruning of old session data when exceeding MAX_SESSIONS.
        """
        # Override MAX_SESSIONS for testing
        original_max = StatisticsManager.MAX_SESSIONS
        StatisticsManager.MAX_SESSIONS = 3
        
        try:
            # Set up mock behavior
            self.mock_os.path.exists.return_value = False
            
            # Create 5 sessions (2 more than MAX_SESSIONS)
            for session_idx in range(5):
                session_id = f"session_{session_idx}"
                
                # Start a new session
                self.stats_manager.start_session(session_id)
                
                # Add decisions to the session
                for i in range(5):
                    decision = self._create_decision(decision_id=f"{session_idx}_{i}")
                    self.stats_manager.record_decision(self.player_id, decision)
                
                # End the session
                self.stats_manager.end_session(self.player_id, session_id)
            
            # Get learning statistics
            learning_stats = self.stats_manager.get_learning_statistics(self.player_id)
            
            # Assertions
            self.assertEqual(learning_stats.total_decisions, 25,
                            "Should have recorded 25 decisions (5 sessions * 5 decisions)")
            
            # Check session meta data for active sessions
            session_meta = self.stats_manager.session_meta.get(self.player_id, {})
            active_sessions = [s for s in session_meta.values() if s.get("active", False)]
            
            # Should only have MAX_SESSIONS active sessions
            self.assertLessEqual(len(active_sessions), StatisticsManager.MAX_SESSIONS,
                               "Should not exceed MAX_SESSIONS")
            
            # The oldest 2 sessions should be pruned (no longer active)
            for i in range(2):
                session_id = f"session_{i}"
                session_data = next((s for s in session_meta.values() if s.get("session_id") == session_id), None)
                if session_data:
                    self.assertFalse(session_data.get("active", True),
                                   f"Oldest session {session_id} should be pruned (not active)")
        
        finally:
            # Restore original MAX_SESSIONS
            StatisticsManager.MAX_SESSIONS = original_max

    def test_D3_aggregate_data_preservation(self):
        """
        Test D3: Aggregate Data Preservation
        
        Test preservation of aggregate statistics after pruning.
        """
        # Set up mock behavior
        self.mock_os.path.exists.return_value = False
        
        # Create initial session and add decisions
        self.stats_manager.start_session("initial_session")
        
        # Add 10 decisions with various characteristics
        strategy_counts = {"Conservative": 0, "Risk Taker": 0, "Probability-Based": 0, "Bluffer": 0}
        optimal_count = 0
        
        for i in range(10):
            decision = self._create_decision(decision_id=f"initial_{i}")
            
            # Alternate strategies for better distribution
            strategies = ["Conservative", "Risk Taker", "Probability-Based", "Bluffer"]
            strategy = strategies[i % 4]
            
            decision["matching_strategy"] = strategy
            strategy_counts[strategy] += 1
            
            # Make some decisions optimal
            decision["was_optimal"] = (i % 3 == 0)
            if decision["was_optimal"]:
                optimal_count += 1
            
            self.stats_manager.record_decision(self.player_id, decision)
        
        # End initial session
        self.stats_manager.end_session(self.player_id, "initial_session")
        
        # Get learning statistics and store initial values
        initial_stats = self.stats_manager.get_learning_statistics(self.player_id)
        initial_total = initial_stats.total_decisions
        initial_correct = initial_stats.correct_decisions
        initial_strategies = initial_stats.decisions_by_strategy.copy()
        
        # Now create a new session that will trigger pruning of the initial one
        # Override MAX_SESSIONS for testing
        original_max = StatisticsManager.MAX_SESSIONS
        StatisticsManager.MAX_SESSIONS = 1
        
        try:
            # Create a new session
            self.stats_manager.start_session("new_session")
            
            # Add some decisions to the new session
            for i in range(5):
                decision = self._create_decision(decision_id=f"new_{i}")
                self.stats_manager.record_decision(self.player_id, decision)
            
            # End the new session
            self.stats_manager.end_session(self.player_id, "new_session")
            
            # Get updated learning statistics
            updated_stats = self.stats_manager.get_learning_statistics(self.player_id)
            
            # Assertions
            self.assertEqual(updated_stats.total_decisions, initial_total + 5,
                            "Total decisions should include initial + new decisions")
            
            self.assertEqual(updated_stats.correct_decisions, initial_correct + 5,
                            "Correct decisions should include initial + new decisions")
            
            # Check that strategy counts are preserved
            for strategy, count in initial_strategies.items():
                self.assertEqual(updated_stats.decisions_by_strategy[strategy], count + (1 if strategy == "Conservative" else 0),
                                f"{strategy} count should be preserved after pruning")
            
        finally:
            # Restore original MAX_SESSIONS
            StatisticsManager.MAX_SESSIONS = original_max

    def test_D4_decision_history_limit(self):
        """
        Test D4: Decision History Limit
        
        Test the MAX_DETAILED_DECISIONS limit for decision history.
        """
        # Override MAX_DETAILED_DECISIONS for testing
        original_max = LearningStatistics.MAX_DETAILED_DECISIONS
        LearningStatistics.MAX_DETAILED_DECISIONS = 15
        
        try:
            # Set up mock behavior
            self.mock_os.path.exists.return_value = False
            
            # Create a session and add more decisions than the limit
            self.stats_manager.start_session("test_session")
            
            # Add 20 decisions (5 more than the limit)
            for i in range(20):
                decision = self._create_decision(decision_id=f"decision_{i}")
                self.stats_manager.record_decision(self.player_id, decision)
            
            # End the session
            self.stats_manager.end_session(self.player_id, "test_session")
            
            # Get learning statistics
            learning_stats = self.stats_manager.get_learning_statistics(self.player_id)
            
            # Assertions
            self.assertEqual(learning_stats.total_decisions, 20,
                            "Should have recorded 20 total decisions")
            
            self.assertEqual(len(learning_stats.decision_history), LearningStatistics.MAX_DETAILED_DECISIONS,
                            f"Decision history should be limited to {LearningStatistics.MAX_DETAILED_DECISIONS} entries")
            
            # Check that only the most recent decisions are kept
            # The earliest decision in the history should be decision_5 (decisions 0-4 pruned)
            earliest_id = learning_stats.decision_history[0].get("hand_id")
            self.assertEqual(earliest_id, "decision_5",
                            "First decision should be decision_5 (oldest ones pruned)")
            
            # The latest decision should be decision_19
            latest_id = learning_stats.decision_history[-1].get("hand_id")
            self.assertEqual(latest_id, "decision_19",
                            "Last decision should be decision_19 (most recent)")
        
        finally:
            # Restore original MAX_DETAILED_DECISIONS
            LearningStatistics.MAX_DETAILED_DECISIONS = original_max

if __name__ == '__main__':
    unittest.main()