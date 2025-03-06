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

from stats.ai_decision_analyzer import AIDecisionAnalyzer
from stats.statistics_manager import StatisticsManager

class TestFeedbackRelevance(unittest.TestCase):
    """Test cases for feedback relevance functionality."""

    def setUp(self):
        """
        Set up test environment before each test.
        This includes mocking the necessary dependencies.
        """
        # Mock the statistics manager
        self.stats_manager_mock = Mock(spec=StatisticsManager)
        
        # Create a patched AIDecisionAnalyzer with mocked dependencies
        self.patcher = patch('stats.ai_decision_analyzer.get_statistics_manager', 
                            return_value=self.stats_manager_mock)
        self.get_stats_mock = self.patcher.start()
        
        # Create the analyzer instance
        self.analyzer = AIDecisionAnalyzer()
        
        # Basic test decision data
        self.sample_decision = {
            "decision": "call",
            "matching_strategy": "Conservative",
            "optimal_strategy": "Probability-Based",
            "was_optimal": False,
            "spr": 4.5,
            "game_state": "flop",
            "hole_cards": ["Ah", "Kh"],
            "community_cards": ["7s", "8d", "Qc"],
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
        self.patcher.stop()

    def test_F1_basic_feedback_generation(self):
        """
        Test F1: Basic Feedback Generation
        
        Test that feedback is correctly generated for an optimal decision.
        Should include positive reinforcement.
        """
        # Create decision data for an optimal decision
        optimal_decision = self.sample_decision.copy()
        optimal_decision["matching_strategy"] = "Probability-Based"
        optimal_decision["was_optimal"] = True
        
        # Generate feedback
        feedback = self.analyzer.generate_feedback(optimal_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        self.assertIn("Great job", feedback, "Feedback should include positive reinforcement")
        self.assertIn("Probability-Based", feedback, "Feedback should mention the strategy")

    def test_F2_suboptimal_decision_feedback(self):
        """
        Test F2: Suboptimal Decision Feedback
        
        Test that feedback for a suboptimal decision includes explanation
        and alternative strategy advice.
        """
        # The sample decision is already suboptimal
        feedback = self.analyzer.generate_feedback(self.sample_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        self.assertIn("Probability-Based", feedback, 
                     "Feedback should mention the optimal strategy")
        self.assertNotIn("Great job", feedback, 
                        "Feedback should not include positive reinforcement for suboptimal decision")
        # Look for any phrase that indicates explaining why another strategy is better
        has_explanation = any(phrase in feedback.lower() for phrase in [
            "would have decided", "would have been better", "would have chosen", 
            "consider", "instead of", "better choice", "optimal decision"
        ])
        self.assertTrue(has_explanation, 
                     "Feedback should explain why another strategy would be better or what it would have done")

    def test_F3_spr_based_feedback(self):
        """
        Test F3: SPR-Based Feedback
        
        Test that feedback includes SPR-specific advice.
        """
        # Create decision data with low SPR
        low_spr_decision = self.sample_decision.copy()
        low_spr_decision["spr"] = 2.0
        
        # Generate feedback
        feedback = self.analyzer.generate_feedback(low_spr_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        self.assertIn("SPR", feedback, "Feedback should mention SPR")
        # Check for references to low SPR in various forms
        has_low_spr_reference = any(phrase in feedback.lower() for phrase in [
            "low spr", "spr < 3", "spr below 3", "spr of 2", "spr = 2", "spr is 2"
        ])
        self.assertTrue(has_low_spr_reference, "Feedback should reference low SPR")
        # Check for any commitment-related advice
        has_commitment_advice = any(phrase in feedback.lower() for phrase in [
            "commitment", "commit", "committing", "all-in", "stack"
        ])
        self.assertTrue(has_commitment_advice,
                     "Low SPR feedback should discuss commitment decisions")

    def test_F4_game_stage_feedback(self):
        """
        Test F4: Game Stage Feedback
        
        Test that feedback includes game-stage specific advice.
        """
        # Create pre-flop decision data
        preflop_decision = self.sample_decision.copy()
        preflop_decision["game_state"] = "pre_flop"
        preflop_decision["community_cards"] = []
        
        # Generate feedback
        feedback = self.analyzer.generate_feedback(preflop_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        self.assertIn("pre-flop", feedback.lower(), 
                     "Feedback should mention the game stage")
        self.assertIn("starting hand", feedback.lower(), 
                     "Pre-flop feedback should discuss starting hand selection")

    def test_F5_hand_strength_feedback(self):
        """
        Test F5: Hand Strength Feedback
        
        Test that feedback includes hand strength analysis.
        """
        # Create decision data with premium hand
        premium_hand_decision = self.sample_decision.copy()
        premium_hand_decision["hole_cards"] = ["Ah", "As"]  # Premium hand (pocket aces)
        
        # Generate feedback
        feedback = self.analyzer.generate_feedback(premium_hand_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        self.assertIn("strong", feedback.lower(), 
                     "Feedback should acknowledge the strong hand")
        self.assertIn("pair", feedback.lower(), 
                     "Feedback should mention the pair")

    def test_F6_improvement_tip_relevance(self):
        """
        Test F6: Improvement Tip Relevance
        
        Test that feedback includes strategy-specific improvement tips.
        """
        # Create decision data for a conservative player who should be more aggressive
        conservative_decision = self.sample_decision.copy()
        conservative_decision["matching_strategy"] = "Conservative"
        conservative_decision["optimal_strategy"] = "Risk Taker"
        conservative_decision["strategy_decisions"]["Conservative"] = "call"
        conservative_decision["strategy_decisions"]["Risk Taker"] = "raise"
        
        # Generate feedback
        feedback = self.analyzer.generate_feedback(conservative_decision)
        
        # Assertions
        self.assertIsInstance(feedback, str)
        # Check for any aggression-related improvement advice
        has_aggression_advice = any(phrase in feedback.lower() for phrase in [
            "aggression", "more aggressive", "raise more", "pressure", "less passive"
        ])
        self.assertTrue(has_aggression_advice,
                     "Feedback should include advice about being more aggressive")
        self.assertIn("Risk Taker", feedback, 
                     "Feedback should mention the optimal Risk Taker strategy")

if __name__ == '__main__':
    unittest.main()