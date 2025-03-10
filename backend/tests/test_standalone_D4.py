import unittest
import sys
import os
from unittest.mock import patch
import json

# Adjust the import paths to properly find modules
# This assumes the test is running from the "tests" directory within the backend folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Should be the backend directory
sys.path.insert(0, parent_dir)

from stats.learning_statistics import LearningStatistics

class TestDecisionHistoryLimit(unittest.TestCase):
    """Test case specifically for decision history limit in LearningStatistics."""

    def test_decision_history_limit(self):
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