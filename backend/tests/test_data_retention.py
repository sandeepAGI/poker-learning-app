import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
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
        
        # Track all session IDs created
        session_ids = []
        
        # Create 5 sessions with decisions
        for session_idx in range(5):
            session_id = f"session_{session_idx}"
            session_ids.append(session_id)
            
            # Start a new session
            self.stats_manager.start_session(session_id)
            
            # Add 10 decisions to the session
            for i in range(10):
                decision = self._create_decision(decision_id=f"{session_idx}_{i}")
                # Add session ID to the decision
                decision["session_id"] = session_id
                self.stats_manager.record_decision(self.player_id, decision)
            
            # End the session
            self.stats_manager.end_session(session_id)
        
        # Get learning statistics
        learning_stats = self.stats_manager.get_learning_statistics(self.player_id)
        
        # Assertions
        self.assertEqual(learning_stats.total_decisions, 50,
                        "Should have recorded 50 decisions (5 sessions * 10 decisions)")
        
        # Verify json.dump was called to save data
        self.mock_json.dump.assert_called()
        
        # Verify each session was considered for the learning stats by checking
        # that decisions from all sessions are in the learning statistics
        session_decisions = {}
        for decision in learning_stats.decision_history:
            sid = decision.get("session_id")
            if sid not in session_decisions:
                session_decisions[sid] = 0
            session_decisions[sid] += 1
        
        # Check that we have decisions from all sessions
        for session_id in session_ids:
            self.assertIn(session_id, session_decisions,
                         f"Session {session_id} should have decisions in learning statistics")

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
            
            # Keep track of files "created" by the manager
            session_files = {}
            
            # Mock the listdir to return our tracked files
            def mock_listdir(path):
                if path.endswith("sessions"):
                    return list(session_files.keys())
                return []
            self.mock_os.listdir.side_effect = mock_listdir
            
            # Mock getmtime to return our timestamps
            def mock_getmtime(path):
                filename = os.path.basename(path)
                return session_files.get(filename, 0)
            self.mock_os.path.getmtime.side_effect = mock_getmtime
            
            # Create 5 sessions (2 more than MAX_SESSIONS)
            for session_idx in range(5):
                session_id = f"session_{session_idx}"
                
                # Track the "file" creation
                session_files[f"{session_id}.json"] = session_idx  # Use idx as timestamp
                
                # Start a new session
                self.stats_manager.start_session(session_id)
                
                # Add decisions to the session
                for i in range(5):
                    decision = self._create_decision(decision_id=f"{session_idx}_{i}")
                    decision["session_id"] = session_id
                    self.stats_manager.record_decision(self.player_id, decision)
                
                # End the session
                self.stats_manager.end_session(session_id)
                
                # Manually trigger pruning (in real code this is done during end_session)
                self.stats_manager._prune_old_sessions()
            
            # Get learning statistics
            learning_stats = self.stats_manager.get_learning_statistics(self.player_id)
            
            # Assertions
            self.assertEqual(learning_stats.total_decisions, 25,
                            "Should have recorded 25 decisions (5 sessions * 5 decisions)")
            
            # Check that decisions from newer sessions are retained
            # by ensuring their session IDs are in the decision history
            newer_session_decisions = 0
            older_session_decisions = 0
            
            for decision in learning_stats.decision_history:
                sid = decision.get("session_id")
                if sid in ["session_3", "session_4"]:  # Newest sessions
                    newer_session_decisions += 1
                elif sid in ["session_0", "session_1"]:  # Oldest sessions
                    older_session_decisions += 1
            
            # The pruning should remove detailed decisions from oldest sessions
            # We expect a higher count for newer sessions
            self.assertGreater(newer_session_decisions, older_session_decisions,
                              "Should retain more decisions from newer sessions after pruning")
        
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
            decision["session_id"] = "initial_session"
            
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
        self.stats_manager.end_session("initial_session")
        
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
                decision["session_id"] = "new_session"
                decision["matching_strategy"] = "Conservative"  # All Conservative for simplicity
                self.stats_manager.record_decision(self.player_id, decision)
            
            # End the new session
            self.stats_manager.end_session("new_session")
            
            # Manually trigger pruning
            self.stats_manager._prune_old_sessions()
            
            # Get updated learning statistics
            updated_stats = self.stats_manager.get_learning_statistics(self.player_id)
            
            # Assertions
            self.assertEqual(updated_stats.total_decisions, initial_total + 5,
                            "Total decisions should include initial + new decisions")
            
            self.assertEqual(updated_stats.correct_decisions, initial_correct + 5,
                            "Correct decisions should include initial + new decisions")
            
            # Check that strategy counts are preserved
            for strategy, count in initial_strategies.items():
                expected_count = count
                if strategy == "Conservative":
                    # We added 5 more Conservative decisions
                    expected_count += 5
                    
                self.assertEqual(updated_stats.decisions_by_strategy[strategy], expected_count,
                                f"{strategy} count should be preserved after pruning")
            
        finally:
            # Restore original MAX_SESSIONS
            StatisticsManager.MAX_SESSIONS = original_max

    def test_D4_decision_history_limit(self):
        """
        Test the MAX_DETAILED_DECISIONS limit for decision history.
        This test directly tests the LearningStatistics class without any mocking.
        """
        # Create a fresh LearningStatistics instance
        player_id = "test_player_123"
        learning_stats = LearningStatistics(player_id)
        
        # Get the MAX_DETAILED_DECISIONS value
        max_decisions = LearningStatistics.MAX_DETAILED_DECISIONS
        self.assertGreater(max_decisions, 0, "MAX_DETAILED_DECISIONS should be positive")
        
        # Add more decisions than the limit to force pruning
        extra_decisions = 10
        total_decisions = max_decisions + extra_decisions
        
        # Add decisions
        for i in range(total_decisions):
            decision = {
                "hand_id": f"hand_{i}",
                "decision": "call",
                "matching_strategy": "Conservative",
                "optimal_strategy": "Conservative",
                "was_optimal": True
            }
            learning_stats.add_decision(decision)
        
        # Verify total decision count
        self.assertEqual(learning_stats.total_decisions, total_decisions,
                         f"Should have recorded {total_decisions} total decisions")
        
        # Verify decision history length is limited
        self.assertEqual(len(learning_stats.decision_history), max_decisions,
                         f"Decision history should be limited to {max_decisions} entries")
        
        # Verify the first decision in history is the one after pruning
        first_hand_id = learning_stats.decision_history[0].get("hand_id")
        expected_first_id = f"hand_{extra_decisions}"
        self.assertEqual(first_hand_id, expected_first_id,
                         "First decision should be the one after pruning")
        
        # Verify the last decision is the most recent one
        last_hand_id = learning_stats.decision_history[-1].get("hand_id")
        expected_last_id = f"hand_{total_decisions-1}"
        self.assertEqual(last_hand_id, expected_last_id,
                         "Last decision should be the most recent one")

if __name__ == '__main__':
    unittest.main()