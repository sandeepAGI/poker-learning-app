import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.learning_statistics import LearningStatistics


class TestLearningStatistics(unittest.TestCase):
    """Tests for the LearningStatistics class."""

    def setUp(self):
        """Set up test fixtures."""
        self.player_id = "test_player_123"
        self.learning_stats = LearningStatistics(self.player_id)
        
        # Sample decision data for testing
        self.sample_decision = {
            "hand_id": "hand_123",
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
        
        # Sample non-optimal decision
        self.non_optimal_decision = self.sample_decision.copy()
        self.non_optimal_decision["matching_strategy"] = "Risk Taker"
        self.non_optimal_decision["was_optimal"] = False
        self.non_optimal_decision["expected_value"] = -0.5
        
    def test_initialization(self):
        """Test that LearningStatistics initializes with correct default values."""
        self.assertEqual(self.learning_stats.player_id, self.player_id)
        self.assertEqual(self.learning_stats.total_decisions, 0)
        self.assertEqual(self.learning_stats.correct_decisions, 0)
        self.assertEqual(self.learning_stats.decisions_by_strategy, {
            "Conservative": 0,
            "Risk Taker": 0, 
            "Probability-Based": 0,
            "Bluffer": 0
        })
        self.assertEqual(len(self.learning_stats.decision_history), 0)
        
    def test_add_decision(self):
        """Test adding a decision updates statistics correctly."""
        self.learning_stats.add_decision(self.sample_decision)
        
        self.assertEqual(self.learning_stats.total_decisions, 1)
        self.assertEqual(self.learning_stats.correct_decisions, 1)
        self.assertEqual(self.learning_stats.decisions_by_strategy["Conservative"], 1)
        self.assertEqual(len(self.learning_stats.decision_history), 1)
        self.assertEqual(self.learning_stats.positive_ev_decisions, 1)
        self.assertEqual(self.learning_stats.negative_ev_decisions, 0)
        
    def test_add_non_optimal_decision(self):
        """Test adding a non-optimal decision."""
        self.learning_stats.add_decision(self.non_optimal_decision)
        
        self.assertEqual(self.learning_stats.total_decisions, 1)
        self.assertEqual(self.learning_stats.correct_decisions, 0)
        self.assertEqual(self.learning_stats.decisions_by_strategy["Risk Taker"], 1)
        self.assertEqual(self.learning_stats.positive_ev_decisions, 0)
        self.assertEqual(self.learning_stats.negative_ev_decisions, 1)
        
    def test_decision_accuracy(self):
        """Test decision accuracy calculation."""
        # Add one optimal and one non-optimal decision
        self.learning_stats.add_decision(self.sample_decision)
        self.learning_stats.add_decision(self.non_optimal_decision)
        
        # Should be 50% accuracy (1 out of 2)
        self.assertEqual(self.learning_stats.decision_accuracy, 50.0)
        
    def test_dominant_strategy(self):
        """Test dominant strategy identification."""
        # Add decisions with different strategies
        conservative_decision = self.sample_decision.copy()
        conservative_decision["matching_strategy"] = "Conservative"
        
        risk_taker_decision = self.sample_decision.copy()
        risk_taker_decision["matching_strategy"] = "Risk Taker"
        
        # Add Conservative strategy twice and Risk Taker once
        self.learning_stats.add_decision(conservative_decision)
        self.learning_stats.add_decision(conservative_decision)
        self.learning_stats.add_decision(risk_taker_decision)
        
        # Conservative should be dominant
        self.assertEqual(self.learning_stats.dominant_strategy, "Conservative")
        
    def test_recommended_strategy(self):
        """Test recommended strategy identification."""
        # Add decisions with different optimal strategies
        decision1 = self.sample_decision.copy()
        decision1["optimal_strategy"] = "Probability-Based"
        
        decision2 = self.sample_decision.copy()
        decision2["optimal_strategy"] = "Probability-Based"
        
        decision3 = self.sample_decision.copy()
        decision3["optimal_strategy"] = "Conservative"
        
        # Add decisions
        self.learning_stats.add_decision(decision1)
        self.learning_stats.add_decision(decision2)
        self.learning_stats.add_decision(decision3)
        
        # Probability-Based should be recommended (2 vs 1)
        self.assertEqual(self.learning_stats.recommended_strategy, "Probability-Based")
        
    def test_history_size_limit(self):
        """Test that decision history size is limited."""
        # Set a small MAX_DETAILED_DECISIONS for testing
        original_max = LearningStatistics.MAX_DETAILED_DECISIONS
        LearningStatistics.MAX_DETAILED_DECISIONS = 3
        
        try:
            stats = LearningStatistics("test")
            
            # Add 5 decisions (2 more than the limit)
            for i in range(5):
                decision = self.sample_decision.copy()
                decision["hand_id"] = f"hand_{i}"
                stats.add_decision(decision)
                
            # Should only have 3 decisions in history
            self.assertEqual(len(stats.decision_history), 3)
            
            # The oldest decisions should be removed
            self.assertEqual(stats.decision_history[0]["hand_id"], "hand_2")
            self.assertEqual(stats.decision_history[1]["hand_id"], "hand_3")
            self.assertEqual(stats.decision_history[2]["hand_id"], "hand_4")
        finally:
            # Restore the original max
            LearningStatistics.MAX_DETAILED_DECISIONS = original_max
            
    def test_get_recent_decisions(self):
        """Test retrieving recent decisions."""
        # Add 3 decisions
        for i in range(3):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_{i}"
            self.learning_stats.add_decision(decision)
            
        # Get 2 most recent decisions
        recent = self.learning_stats.get_recent_decisions(2)
        
        # Should have 2 decisions, most recent first
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["hand_id"], "hand_1")
        self.assertEqual(recent[1]["hand_id"], "hand_2")
        
    def test_strategy_distribution(self):
        """Test strategy distribution calculation."""
        # Add 4 decisions with different strategies
        strategies = ["Conservative", "Risk Taker", "Probability-Based", "Conservative"]
        
        for i, strategy in enumerate(strategies):
            decision = self.sample_decision.copy()
            decision["matching_strategy"] = strategy
            self.learning_stats.add_decision(decision)
            
        # Get distribution
        distribution = self.learning_stats.get_strategy_distribution()
        
        # Check percentages
        self.assertEqual(distribution["Conservative"], 50.0)  # 2 out of 4
        self.assertEqual(distribution["Risk Taker"], 25.0)   # 1 out of 4
        self.assertEqual(distribution["Probability-Based"], 25.0)  # 1 out of 4
        self.assertEqual(distribution["Bluffer"], 0.0)  # 0 out of 4
        
    def test_serialization(self):
        """Test to_dict and from_dict methods."""
        # Add some decisions
        self.learning_stats.add_decision(self.sample_decision)
        self.learning_stats.add_decision(self.non_optimal_decision)
        
        # Convert to dict
        data_dict = self.learning_stats.to_dict()
        
        # Create new instance from dict
        new_stats = LearningStatistics.from_dict(data_dict)
        
        # Check that key attributes match
        self.assertEqual(new_stats.player_id, self.learning_stats.player_id)
        self.assertEqual(new_stats.total_decisions, self.learning_stats.total_decisions)
        self.assertEqual(new_stats.correct_decisions, self.learning_stats.correct_decisions)
        self.assertEqual(new_stats.decisions_by_strategy, self.learning_stats.decisions_by_strategy)
        self.assertEqual(len(new_stats.decision_history), len(self.learning_stats.decision_history))


if __name__ == '__main__':
    unittest.main()