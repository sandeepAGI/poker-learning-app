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
from stats.analyzer.trend_analyzer import TrendAnalyzer

class TestLearningProgressTracking(unittest.TestCase):
    """Test cases for learning progress tracking functionality."""

    def setUp(self):
        """
        Set up test environment before each test.
        This includes initializing the LearningStatistics and other components.
        """
        self.player_id = "test_player_123"
        self.learning_stats = LearningStatistics(self.player_id)
        
        # Sample decision data
        self.sample_decision = {
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
        
        # Sample non-optimal decision
        self.non_optimal_decision = self.sample_decision.copy()
        self.non_optimal_decision["matching_strategy"] = "Risk Taker"
        self.non_optimal_decision["was_optimal"] = False
        self.non_optimal_decision["strategy_decisions"]["Risk Taker"] = "raise"
        self.non_optimal_decision["decision"] = "raise"
        self.non_optimal_decision["expected_value"] = -0.5

    def test_L1_basic_decision_recording(self):
        """
        Test L1: Basic Decision Recording
        
        Test that decisions are correctly recorded in learning statistics.
        """
        # Add 5 varied decisions
        decision_strategies = [
            ("Conservative", True),  # (strategy, was_optimal)
            ("Risk Taker", False),
            ("Probability-Based", True),
            ("Bluffer", False),
            ("Conservative", True)
        ]
        
        for i, (strategy, optimal) in enumerate(decision_strategies):
            decision = self.sample_decision.copy()
            decision["matching_strategy"] = strategy
            decision["was_optimal"] = optimal
            decision["hand_id"] = f"hand_{i}"
            
            if not optimal:
                decision["optimal_strategy"] = "Probability-Based"
            else:
                decision["optimal_strategy"] = strategy
                
            self.learning_stats.add_decision(decision)
        
        # Assertions
        self.assertEqual(self.learning_stats.total_decisions, 5,
                        "Total decisions should be 5")
        self.assertEqual(self.learning_stats.correct_decisions, 3,
                        "Correct decisions should be 3")
        self.assertEqual(len(self.learning_stats.decision_history), 5,
                        "Should have 5 decisions in history")
        self.assertEqual(self.learning_stats.decisions_by_strategy["Conservative"], 2,
                        "Should have 2 Conservative decisions")
        self.assertEqual(self.learning_stats.decisions_by_strategy["Risk Taker"], 1,
                        "Should have 1 Risk Taker decision")

    def test_L2_decision_accuracy_tracking(self):
        """
        Test L2: Decision Accuracy Tracking
        
        Test that decision accuracy is correctly calculated.
        """
        # Add 10 decisions, 6 optimal and 4 suboptimal
        for i in range(10):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_{i}"
            
            if i < 6:  # 6 optimal decisions
                decision["was_optimal"] = True
            else:  # 4 suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Assertions
        self.assertEqual(self.learning_stats.total_decisions, 10,
                        "Total decisions should be 10")
        self.assertEqual(self.learning_stats.correct_decisions, 6,
                        "Correct decisions should be 6")
        self.assertEqual(self.learning_stats.decision_accuracy, 60.0,
                        "Decision accuracy should be 60%")

    def test_L3_improvement_trend_detection(self):
        """
        Test L3: Improvement Trend Detection
        
        Test that trend analysis correctly identifies improving performance.
        """
        # First add 10 decisions with 40% optimal
        for i in range(10):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_first_{i}"
            
            if i < 4:  # 4 optimal decisions (40%)
                decision["was_optimal"] = True
            else:  # 6 suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Then add 10 more decisions with 80% optimal
        for i in range(10):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_second_{i}"
            
            if i < 8:  # 8 optimal decisions (80%)
                decision["was_optimal"] = True
            else:  # 2 suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Create a trend analyzer and analyze the learning statistics
        trend_analyzer = TrendAnalyzer()
        trend_results = trend_analyzer.analyze_decision_quality_trend(self.learning_stats)
        
        # Assertions
        self.assertEqual(trend_results["trend"], "improving",
                        "Trend should be detected as improving")
        self.assertGreater(trend_results["improvement_rate"], 0,
                          "Improvement rate should be positive")

    def test_L4_decline_trend_detection(self):
        """
        Test L4: Decline Trend Detection
        
        Test that trend analysis correctly identifies declining performance.
        """
        # First add 10 decisions with 70% optimal
        for i in range(10):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_first_{i}"
            
            if i < 7:  # 7 optimal decisions (70%)
                decision["was_optimal"] = True
            else:  # 3 suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Then add 10 more decisions with 40% optimal
        for i in range(10):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_second_{i}"
            
            if i < 4:  # 4 optimal decisions (40%)
                decision["was_optimal"] = True
            else:  # 6 suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Create a trend analyzer and analyze the learning statistics
        trend_analyzer = TrendAnalyzer()
        trend_results = trend_analyzer.analyze_decision_quality_trend(self.learning_stats)
        
        # Assertions
        self.assertEqual(trend_results["trend"], "declining",
                        "Trend should be detected as declining")
        self.assertLess(trend_results["improvement_rate"], 0,
                       "Improvement rate should be negative")

    def test_L5_recent_improvement_detection(self):
        """
        Test L5: Recent Improvement Detection
        
        Test that trend analysis correctly identifies very recent improvement.
        """
        # First add 15 decisions with mediocre 50% optimal
        for i in range(15):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_first_{i}"
            
            if i % 2 == 0:  # 50% optimal decisions
                decision["was_optimal"] = True
            else:  # 50% suboptimal decisions
                decision["was_optimal"] = False
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Then add 5 more decisions with 100% optimal (recent improvement)
        for i in range(5):
            decision = self.sample_decision.copy()
            decision["hand_id"] = f"hand_recent_{i}"
            decision["was_optimal"] = True
                
            self.learning_stats.add_decision(decision)
        
        # Create a trend analyzer and analyze the learning statistics
        trend_analyzer = TrendAnalyzer()
        trend_results = trend_analyzer.analyze_decision_quality_trend(self.learning_stats)
        
        # Assertions
        self.assertTrue(trend_results.get("recent_improvement", False),
                       "Should detect recent improvement")
        self.assertIn("recent decisions", trend_results.get("description", ""),
                     "Description should mention recent improvement")

if __name__ == '__main__':
    unittest.main()