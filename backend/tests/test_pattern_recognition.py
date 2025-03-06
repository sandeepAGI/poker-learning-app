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
from stats.analyzer.pattern_analyzer import PatternAnalyzer

class TestPatternRecognition(unittest.TestCase):
    """Test cases for pattern recognition functionality."""

    def setUp(self):
        """
        Set up test environment before each test.
        This includes initializing the LearningStatistics and PatternAnalyzer.
        """
        self.player_id = "test_player_123"
        self.learning_stats = LearningStatistics(self.player_id)
        self.pattern_analyzer = PatternAnalyzer()
        
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

    def test_P1_game_state_pattern_analysis(self):
        """
        Test P1: Game State Pattern Analysis
        
        Test identification of game state weaknesses, specifically
        in the turn stage.
        """
        # Add 20 decisions across different game states
        # Make turn decisions mostly suboptimal
        game_states = ["pre_flop", "flop", "turn", "river"]
        
        for i in range(20):
            game_state = game_states[i % 4]
            
            # For turn, make 4/5 decisions suboptimal
            was_optimal = True
            if game_state == "turn" and i % 5 != 0:
                was_optimal = False
                
            decision = self._create_decision(
                game_state=game_state,
                was_optimal=was_optimal,
                optimal_strategy="Probability-Based" if not was_optimal else "Conservative"
            )
            decision["hand_id"] = f"hand_{i}"
            
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis using the actual methods with decision_history
        game_state_patterns_result = self.pattern_analyzer.analyze_game_state_patterns(self.learning_stats.decision_history)
        spr_patterns_result = self.pattern_analyzer.analyze_spr_patterns(self.learning_stats.decision_history)
        dominant_strategy = self.learning_stats.dominant_strategy
        recommended_strategy = self.learning_stats.recommended_strategy
        decision_accuracy = self.learning_stats.decision_accuracy
        
        # Combine results into a patterns dictionary
        patterns = {
            "game_state_patterns": game_state_patterns_result,
            "spr_patterns": spr_patterns_result,
            "improvement_areas": self.pattern_analyzer.identify_improvement_areas(
                self.learning_stats, dominant_strategy, recommended_strategy, 
                decision_accuracy, spr_patterns_result, game_state_patterns_result
            )
        }
        
        # Find game state patterns in the results
        game_state_patterns = next((p for p in patterns["improvement_areas"] 
                                    if p["type"] == "game_state"), None)
        
        # Assertions
        self.assertIsNotNone(game_state_patterns, 
                            "Should identify game state patterns")
        self.assertEqual(game_state_patterns["area"], "turn",
                        "Should identify turn as the problematic game state")
        self.assertIn("turn", game_state_patterns["description"].lower(),
                     "Description should mention the turn")

    def test_P2_spr_pattern_analysis(self):
        """
        Test P2: SPR Pattern Analysis
        
        Test identification of SPR-related patterns, specifically
        issues with high SPR situations.
        """
        # Add 30 decisions with different SPRs
        # Make high SPR decisions mostly suboptimal
        spr_values = [2.5, 5.0, 8.0]  # low, medium, high
        
        for i in range(30):
            spr = spr_values[i % 3]
            
            # For high SPR, make 8/10 decisions suboptimal
            was_optimal = True
            if spr == 8.0 and i % 10 < 8:
                was_optimal = False
                
            decision = self._create_decision(
                spr=spr,
                was_optimal=was_optimal,
                optimal_strategy="Probability-Based" if not was_optimal else "Conservative"
            )
            decision["hand_id"] = f"hand_{i}"
            
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis using the actual methods with decision_history
        game_state_patterns_result = self.pattern_analyzer.analyze_game_state_patterns(self.learning_stats.decision_history)
        spr_patterns_result = self.pattern_analyzer.analyze_spr_patterns(self.learning_stats.decision_history)
        dominant_strategy = self.learning_stats.dominant_strategy
        recommended_strategy = self.learning_stats.recommended_strategy
        decision_accuracy = self.learning_stats.decision_accuracy
        
        # Combine results into a patterns dictionary
        patterns = {
            "game_state_patterns": game_state_patterns_result,
            "spr_patterns": spr_patterns_result,
            "improvement_areas": self.pattern_analyzer.identify_improvement_areas(
                self.learning_stats, dominant_strategy, recommended_strategy, 
                decision_accuracy, spr_patterns_result, game_state_patterns_result
            )
        }
        
        # Find SPR patterns in the results
        spr_patterns = next((p for p in patterns["improvement_areas"] 
                            if p["type"] == "spr"), None)
        
        # Assertions
        self.assertIsNotNone(spr_patterns, 
                            "Should identify SPR patterns")
        self.assertEqual(spr_patterns["area"], "high",
                        "Should identify high SPR as the problematic area")
        self.assertIn("high spr", spr_patterns["description"].lower(),
                     "Description should mention high SPR situations")

    def test_P3_strategy_alignment_analysis(self):
        """
        Test P3: Strategy Alignment Analysis
        
        Test identification of strategy misalignment where player's
        dominant strategy differs from recommended strategy.
        """
        # Create a player with Conservative dominant strategy
        # but Probability-Based as recommended strategy
        
        # Add 15 decisions with Conservative strategy
        for i in range(15):
            decision = self._create_decision(
                matching_strategy="Conservative",
                was_optimal=i < 5  # Only 1/3 of Conservative decisions are optimal
            )
            decision["hand_id"] = f"hand_c_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Add 5 decisions with other strategies
        for i in range(5):
            decision = self._create_decision(
                matching_strategy="Risk Taker",
                was_optimal=False,
                optimal_strategy="Probability-Based"
            )
            decision["hand_id"] = f"hand_r_{i}"
            self.learning_stats.add_decision(decision)
        
        # The dominant strategy should be Conservative but recommended Probability-Based
        self.assertEqual(self.learning_stats.dominant_strategy, "Conservative")
        self.assertEqual(self.learning_stats.recommended_strategy, "Probability-Based")
        
        # Run pattern analysis using the actual methods with decision_history
        game_state_patterns_result = self.pattern_analyzer.analyze_game_state_patterns(self.learning_stats.decision_history)
        spr_patterns_result = self.pattern_analyzer.analyze_spr_patterns(self.learning_stats.decision_history)
        dominant_strategy = self.learning_stats.dominant_strategy
        recommended_strategy = self.learning_stats.recommended_strategy
        decision_accuracy = self.learning_stats.decision_accuracy
        
        # Combine results into a patterns dictionary
        patterns = {
            "game_state_patterns": game_state_patterns_result,
            "spr_patterns": spr_patterns_result,
            "improvement_areas": self.pattern_analyzer.identify_improvement_areas(
                self.learning_stats, dominant_strategy, recommended_strategy, 
                decision_accuracy, spr_patterns_result, game_state_patterns_result
            )
        }
        
        # Find strategy alignment patterns in the results
        strategy_patterns = next((p for p in patterns["improvement_areas"] 
                                 if p["type"] == "strategy_alignment"), None)
        
        # Assertions
        self.assertIsNotNone(strategy_patterns, 
                            "Should identify strategy alignment issues")
        self.assertIn("Conservative", strategy_patterns["description"],
                     "Description should mention current Conservative strategy")
        self.assertIn("Probability-Based", strategy_patterns["description"],
                     "Description should mention recommended Probability-Based strategy")

    def test_P4_multiple_improvement_areas(self):
        """
        Test P4: Multiple Improvement Areas
        
        Test identification and ranking of multiple improvement areas.
        """
        # Create a player with weaknesses in:
        # 1. Pre-flop decisions (70% suboptimal)
        # 2. Turn decisions (60% suboptimal)
        # 3. High SPR situations (80% suboptimal)
        
        # Add pre-flop decisions
        for i in range(10):
            decision = self._create_decision(
                game_state="pre_flop",
                was_optimal=i >= 7  # 70% suboptimal
            )
            decision["hand_id"] = f"hand_preflop_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Add turn decisions
        for i in range(10):
            decision = self._create_decision(
                game_state="turn",
                was_optimal=i >= 6  # 60% suboptimal
            )
            decision["hand_id"] = f"hand_turn_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Add high SPR decisions
        for i in range(10):
            decision = self._create_decision(
                spr=8.0,  # High SPR
                was_optimal=i >= 8  # 80% suboptimal
            )
            decision["hand_id"] = f"hand_spr_{i}"
            
            if not decision["was_optimal"]:
                decision["optimal_strategy"] = "Probability-Based"
                
            self.learning_stats.add_decision(decision)
        
        # Run pattern analysis using the actual methods with decision_history
        game_state_patterns_result = self.pattern_analyzer.analyze_game_state_patterns(self.learning_stats.decision_history)
        spr_patterns_result = self.pattern_analyzer.analyze_spr_patterns(self.learning_stats.decision_history)
        dominant_strategy = self.learning_stats.dominant_strategy
        recommended_strategy = self.learning_stats.recommended_strategy
        decision_accuracy = self.learning_stats.decision_accuracy
        
        # Combine results into a patterns dictionary
        patterns = {
            "game_state_patterns": game_state_patterns_result,
            "spr_patterns": spr_patterns_result,
            "improvement_areas": self.pattern_analyzer.identify_improvement_areas(
                self.learning_stats, dominant_strategy, recommended_strategy, 
                decision_accuracy, spr_patterns_result, game_state_patterns_result
            )
        }
        
        # Assertions
        self.assertGreaterEqual(len(patterns["improvement_areas"]), 3,
                              "Should identify at least 3 improvement areas")
        
        # Get the types of improvement areas
        improvement_areas = [area["type"] for area in patterns["improvement_areas"]]
        
        # Check that all expected areas are identified
        self.assertIn("game_state", improvement_areas, 
                     "Should identify game state issues")
        self.assertIn("spr", improvement_areas, 
                     "Should identify SPR issues")
        
        # Get the first (highest priority) improvement area
        top_area = patterns["improvement_areas"][0]
        
        # The high SPR issue should be highest priority (80% suboptimal)
        self.assertEqual(top_area["type"], "spr", 
                        "High SPR should be the top priority issue")
        self.assertEqual(top_area["area"], "high", 
                        "The specific SPR issue should be with high SPR")

if __name__ == '__main__':
    unittest.main()