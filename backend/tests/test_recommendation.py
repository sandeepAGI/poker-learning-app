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
from stats.analyzer.recommendation_engine import RecommendationEngine
from stats.analyzer.pattern_analyzer import PatternAnalyzer

class TestRecommendation(unittest.TestCase):
    """Test cases for recommendation generation functionality."""

    def setUp(self):
        """
        Set up test environment before each test.
        This includes initializing the LearningStatistics and RecommendationEngine.
        """
        self.player_id = "test_player_123"
        self.learning_stats = LearningStatistics(self.player_id)
        self.pattern_analyzer = PatternAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        
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

    def _create_decision(self, game_state="flop", spr=4.5, was_optimal=True, 
                        matching_strategy="Conservative", optimal_strategy="Conservative"):
        """Helper to create a decision with specific attributes."""
        decision = self.decision_template.copy()
        decision["game_state"] = game_state
        decision["spr"] = spr
        decision["was_optimal"] = was_optimal
        decision["matching_strategy"] = matching_strategy
        decision["optimal_strategy"] = optimal_strategy
        
        if game_state == "pre_flop":
            decision["community_cards"] = []
        elif game_state == "turn":
            decision["community_cards"] = ["7s", "8d", "Qc", "2h"]
        elif game_state == "river":
            decision["community_cards"] = ["7s", "8d", "Qc", "2h", "As"]
            
        return decision

    def test_R1_basic_recommendation_generation(self):
        """
        Test R1: Basic Recommendation Generation
        
        Test generation of recommendations based on a single identified weakness.
        """
        # Create a player with a weakness in turn decisions
        game_states = ["pre_flop", "flop", "turn", "river"]
        
        for i in range(20):
            game_state = game_states[i % 4]
            
            # For turn, make all decisions suboptimal
            was_optimal = True
            if game_state == "turn":
                was_optimal = False
                
            decision = self._create_decision(
                game_state=game_state,
                was_optimal=was_optimal,
                optimal_strategy="Probability-Based" if not was_optimal else "Conservative"
            )
            decision["hand_id"] = f"hand_{i}"
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis
        patterns = self.pattern_analyzer.analyze_patterns(self.learning_stats)
        
        # Generate recommendations based on patterns
        recommendations = self.recommendation_engine.generate_recommendations(
            self.learning_stats, patterns)
        
        # Assertions
        self.assertGreaterEqual(len(recommendations), 1,
                              "Should generate at least one recommendation")
        
        # Find a recommendation focused on turn play
        turn_recommendation = next((r for r in recommendations 
                                   if "turn" in r["focus"]), None)
        
        self.assertIsNotNone(turn_recommendation,
                            "Should generate a recommendation for turn play")
        self.assertIn("turn", turn_recommendation["title"].lower(),
                     "Recommendation title should mention turn")
        self.assertIn("turn", turn_recommendation["description"].lower(),
                     "Recommendation description should provide turn advice")

    def test_R2_multiple_recommendations(self):
        """
        Test R2: Multiple Recommendations
        
        Test generation of multiple recommendations prioritized by need.
        """
        # Create a player with weaknesses in:
        # 1. Pre-flop decisions (90% suboptimal) - highest priority
        # 2. Turn decisions (70% suboptimal) - medium priority
        # 3. High SPR situations (50% suboptimal) - lower priority
        
        # Add pre-flop decisions (90% suboptimal)
        for i in range(10):
            decision = self._create_decision(
                game_state="pre_flop",
                was_optimal=i >= 9  # 90% suboptimal
            )
            decision["hand_id"] = f"hand_preflop_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Add turn decisions (70% suboptimal)
        for i in range(10):
            decision = self._create_decision(
                game_state="turn",
                was_optimal=i >= 7  # 70% suboptimal
            )
            decision["hand_id"] = f"hand_turn_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Add high SPR decisions (50% suboptimal)
        for i in range(10):
            decision = self._create_decision(
                spr=8.0,  # High SPR
                was_optimal=i >= 5  # 50% suboptimal
            )
            decision["hand_id"] = f"hand_spr_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis
        patterns = self.pattern_analyzer.analyze_patterns(self.learning_stats)
        
        # Generate recommendations based on patterns
        recommendations = self.recommendation_engine.generate_recommendations(
            self.learning_stats, patterns)
        
        # Assertions
        self.assertGreaterEqual(len(recommendations), 3,
                              "Should generate at least three recommendations")
        
        # The first recommendation should be for pre-flop (highest priority)
        self.assertIn("pre-flop", recommendations[0]["focus"].lower(),
                     "First recommendation should focus on pre-flop (highest priority issue)")
        
        # Check if all three improvement areas are covered in recommendations
        recommendation_focuses = [r["focus"].lower() for r in recommendations]
        self.assertTrue(any("pre-flop" in focus for focus in recommendation_focuses),
                       "Should include pre-flop recommendation")
        self.assertTrue(any("turn" in focus for focus in recommendation_focuses),
                       "Should include turn recommendation")
        self.assertTrue(any("spr" in focus for focus in recommendation_focuses),
                       "Should include SPR recommendation")

    def test_R3_beginner_recommendations(self):
        """
        Test R3: Beginner Recommendations
        
        Test recommendations for new players with few decisions.
        """
        # Create a new player with only a few decisions
        for i in range(5):
            decision = self._create_decision(
                was_optimal=i >= 3  # 60% suboptimal
            )
            decision["hand_id"] = f"hand_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis
        patterns = self.pattern_analyzer.analyze_patterns(self.learning_stats)
        
        # Generate recommendations based on patterns
        recommendations = self.recommendation_engine.generate_recommendations(
            self.learning_stats, patterns)
        
        # Assertions
        self.assertGreaterEqual(len(recommendations), 1,
                              "Should generate at least one recommendation")
        
        # Find a fundamental recommendation for beginners
        fundamental_recommendation = next((r for r in recommendations 
                                          if "fundamental" in r["focus"].lower()), None)
        
        self.assertIsNotNone(fundamental_recommendation,
                            "Should generate a fundamentals recommendation for new players")
        self.assertIn("fundamental", fundamental_recommendation["title"].lower(),
                     "Recommendation title should mention fundamentals")
        self.assertIn("basic", fundamental_recommendation["description"].lower(),
                     "Recommendation description should focus on basics")

    def test_R4_strategy_shift_recommendation(self):
        """
        Test R4: Strategy Shift Recommendation
        
        Test recommendations for strategy shift when needed.
        """
        # Create a player with Conservative dominant strategy
        # but Risk Taker as recommended strategy
        
        # Add 15 decisions with Conservative strategy
        for i in range(15):
            decision = self._create_decision(
                matching_strategy="Conservative",
                was_optimal=i < 5  # Only 1/3 of Conservative decisions are optimal
            )
            decision["hand_id"] = f"hand_c_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Risk Taker"
                
            self.learning_stats.add_decision(decision)
        
        # Add 5 decisions with Risk Taker strategy, all optimal
        for i in range(5):
            decision = self._create_decision(
                matching_strategy="Risk Taker",
                optimal_strategy="Risk Taker",
                was_optimal=True
            )
            decision["hand_id"] = f"hand_r_{i}"
            self.learning_stats.add_decision(decision)
        
        # The dominant strategy should be Conservative but recommended Risk Taker
        self.assertEqual(self.learning_stats.dominant_strategy, "Conservative")
        self.assertEqual(self.learning_stats.recommended_strategy, "Risk Taker")
        
        # Run pattern analysis
        patterns = self.pattern_analyzer.analyze_patterns(self.learning_stats)
        
        # Generate recommendations based on patterns
        recommendations = self.recommendation_engine.generate_recommendations(
            self.learning_stats, patterns)
        
        # Assertions
        self.assertGreaterEqual(len(recommendations), 1,
                              "Should generate at least one recommendation")
        
        # Find a strategy shift recommendation
        strategy_recommendation = next((r for r in recommendations 
                                       if "strategy" in r["focus"].lower()), None)
        
        self.assertIsNotNone(strategy_recommendation,
                            "Should generate a strategy shift recommendation")
        self.assertIn("aggressive", strategy_recommendation["description"].lower(),
                     "Recommendation should suggest more aggressive play")
        self.assertIn("Risk Taker", strategy_recommendation["description"],
                     "Recommendation should mention Risk Taker strategy")

if __name__ == '__main__':
    unittest.main()