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
from stats.learning_statistics import LearningStatistics
from stats.analyzer.pattern_analyzer import PatternAnalyzer
from stats.analyzer.recommendation_engine import RecommendationEngine
from stats.analyzer.trend_analyzer import TrendAnalyzer

class TestIntegration(unittest.TestCase):
    """Integration tests for the full statistics system."""

    def setUp(self):
        """
        Set up test environment before each test.
        """
        # Mock file operations to avoid disk I/O
        self.io_patcher = patch('stats.statistics_manager.open', create=True)
        self.mock_open = self.io_patcher.start()
        
        self.json_patcher = patch('stats.statistics_manager.json')
        self.mock_json = self.json_patcher.start()
        
        self.os_patcher = patch('stats.statistics_manager.os')
        self.mock_os = self.os_patcher.start()
        self.mock_os.path.exists.return_value = False
        
        # Set up the system components
        self.stats_manager = StatisticsManager()
        self.analyzer = AIDecisionAnalyzer()
        self.analyzer.stats_manager = self.stats_manager
        
        self.pattern_analyzer = PatternAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        
        # Sample decision templates for different strategies
        self.decision_templates = {
            "Conservative": {
                "decision": "fold",
                "hole_cards": ["8h", "3d"],  # Medium-weak hand
                "game_state": "flop",
                "community_cards": ["As", "Kd", "Qc"],
                "pot_size": 100,
                "current_bet": 30,
                "spr": 5.0
            },
            "Risk Taker": {
                "decision": "raise",
                "hole_cards": ["Th", "8d"],  # Medium hand
                "game_state": "flop",
                "community_cards": ["As", "Kd", "7c"],
                "pot_size": 120,
                "current_bet": 40,
                "spr": 3.0
            },
            "Probability-Based": {
                "decision": "call",
                "hole_cards": ["Jh", "Td"],  # Drawing hand
                "game_state": "flop",
                "community_cards": ["9s", "8d", "2c"],
                "pot_size": 150,
                "current_bet": 50,
                "spr": 4.0
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        self.io_patcher.stop()
        self.json_patcher.stop()
        self.os_patcher.stop()

    def _mock_ai_decisions(self, strategy):
        """Set up mock AI decisions based on the strategy."""
        decisions = {
            "Conservative": {
                "Conservative": "fold",
                "Risk Taker": "call", 
                "Probability-Based": "fold",
                "Bluffer": "raise"
            },
            "Risk Taker": {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "raise" 
            },
            "Probability-Based": {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "fold"
            }
        }
        
        # Determine the optimal strategy for this template
        if strategy == "Conservative":
            optimal = "Conservative"
            ev = 0.7
        elif strategy == "Risk Taker":
            optimal = "Risk Taker" 
            ev = 1.2
        else:
            optimal = "Probability-Based"
            ev = 1.1
            
        return decisions[strategy], optimal, ev

    def test_I1_full_integration_conservative_player(self):
        """
        Test I1: Full Integration - Conservative Player
        
        Test the full system with a predominantly Conservative player profile.
        """
        player_id = "test_conservative_player"
        
        # Start a session
        self.stats_manager.start_session(player_id, "test_session")
        
        # Mock the decision maker and optimal strategy finder
        decision_maker_patcher = patch('stats.ai_decision_analyzer.AIDecisionMaker')
        mock_decision_maker = decision_maker_patcher.start()
        
        # Set up to return Conservative as optimal most of the time
        with patch.object(self.analyzer, '_find_matching_strategy', return_value="Conservative"), \
             patch.object(self.analyzer, '_find_optimal_strategy', 
                         return_value=("Conservative", 0.7)):
            
            # Add 20 decisions with Conservative profile (80% Conservative, 20% others)
            for i in range(20):
                if i < 16:  # 80% Conservative
                    template = self.decision_templates["Conservative"]
                elif i < 18:  # 10% Risk Taker
                    template = self.decision_templates["Risk Taker"]
                else:  # 10% Probability-Based
                    template = self.decision_templates["Probability-Based"]
                
                # Record the decision
                strategy = "Conservative" if i < 16 else ("Risk Taker" if i < 18 else "Probability-Based")
                strategy_decisions, optimal, ev = self._mock_ai_decisions(strategy)
                
                mock_decision_maker.make_decision.return_value = strategy_decisions
                
                result = self.analyzer.analyze_decision(
                    player_id=player_id,
                    player_decision=template["decision"],
                    hole_cards=template["hole_cards"],
                    game_state={"game_state": template["game_state"], 
                                "community_cards": template["community_cards"]},
                    deck=["2c", "3d", "4h"],  # Dummy deck
                    pot_size=template["pot_size"],
                    spr=template["spr"]
                )
            
        # End the session
        self.stats_manager.end_session(player_id, "test_session")
        
        # Get player statistics and profile
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        profile = self.analyzer.get_player_strategy_profile(player_id)
        
        # Analyze patterns and generate recommendations
        patterns = self.pattern_analyzer.analyze_patterns(learning_stats)
        trends = self.trend_analyzer.analyze_trends(learning_stats)
        recommendations = self.recommendation_engine.generate_recommendations(learning_stats, patterns)
        
        # Assertions
        self.assertEqual(profile["dominant_strategy"], "Conservative",
                        "Dominant strategy should be Conservative")
        self.assertGreaterEqual(profile["strategy_distribution"]["Conservative"], 70,
                              "Conservative strategy should be at least 70%")
        
        # Clean up
        decision_maker_patcher.stop()

    def test_I2_full_integration_risk_taker_player(self):
        """
        Test I2: Full Integration - Risk Taker Player
        
        Test the full system with a predominantly Risk Taker player profile.
        """
        player_id = "test_risk_taker_player"
        
        # Start a session
        self.stats_manager.start_session(player_id, "test_session")
        
        # Mock the decision maker and optimal strategy finder
        decision_maker_patcher = patch('stats.ai_decision_analyzer.AIDecisionMaker')
        mock_decision_maker = decision_maker_patcher.start()
        
        # Set up to return Risk Taker decisions most of the time
        with patch.object(self.analyzer, '_find_matching_strategy', return_value="Risk Taker"), \
             patch.object(self.analyzer, '_find_optimal_strategy', 
                         return_value=("Risk Taker", 1.2)):
            
            # Add 20 decisions with Risk Taker profile (75% Risk Taker, 25% others)
            for i in range(20):
                if i < 15:  # 75% Risk Taker
                    template = self.decision_templates["Risk Taker"]
                elif i < 18:  # 15% Conservative
                    template = self.decision_templates["Conservative"]
                else:  # 10% Probability-Based
                    template = self.decision_templates["Probability-Based"]
                
                # Record the decision
                strategy = "Risk Taker" if i < 15 else ("Conservative" if i < 18 else "Probability-Based")
                strategy_decisions, optimal, ev = self._mock_ai_decisions(strategy)
                
                mock_decision_maker.make_decision.return_value = strategy_decisions
                
                result = self.analyzer.analyze_decision(
                    player_id=player_id,
                    player_decision=template["decision"],
                    hole_cards=template["hole_cards"],
                    game_state={"game_state": template["game_state"], 
                                "community_cards": template["community_cards"]},
                    deck=["2c", "3d", "4h"],  # Dummy deck
                    pot_size=template["pot_size"],
                    spr=template["spr"]
                )
            
        # End the session
        self.stats_manager.end_session(player_id, "test_session")
        
        # Get player statistics and profile
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        profile = self.analyzer.get_player_strategy_profile(player_id)
        
        # Analyze patterns and generate recommendations
        patterns = self.pattern_analyzer.analyze_patterns(learning_stats)
        trends = self.trend_analyzer.analyze_trends(learning_stats)
        recommendations = self.recommendation_engine.generate_recommendations(learning_stats, patterns)
        
        # Assertions
        self.assertEqual(profile["dominant_strategy"], "Risk Taker",
                        "Dominant strategy should be Risk Taker")
        self.assertGreaterEqual(profile["strategy_distribution"]["Risk Taker"], 70,
                              "Risk Taker strategy should be at least 70%")
        
        # Clean up
        decision_maker_patcher.stop()

    def test_I3_full_integration_learning_progress(self):
        """
        Test I3: Full Integration - Learning Progress
        
        Test the full system with a player showing learning progress over time.
        """
        player_id = "test_learning_player"
        
        # Start a session
        self.stats_manager.start_session(player_id, "early_session")
        
        # Mock the decision maker and optimal strategy finder
        decision_maker_patcher = patch('stats.ai_decision_analyzer.AIDecisionMaker')
        mock_decision_maker = decision_maker_patcher.start()
        
        # First add 10 decisions with poor decision quality (30% optimal)
        for i in range(10):
            template = self.decision_templates["Conservative"]
            strategy_decisions, optimal, ev = self._mock_ai_decisions("Conservative")
            
            mock_decision_maker.make_decision.return_value = strategy_decisions
            
            # For early decisions, patch to make most suboptimal
            with patch.object(self.analyzer, '_find_matching_strategy', 
                             return_value="Conservative"), \
                 patch.object(self.analyzer, '_find_optimal_strategy', 
                             return_value=("Probability-Based", 1.1)):
                
                # Make only 30% optimal
                was_optimal = (i < 3)
                player_decision = "fold" if was_optimal else "call"
                
                result = self.analyzer.analyze_decision(
                    player_id=player_id,
                    player_decision=player_decision,
                    hole_cards=template["hole_cards"],
                    game_state={"game_state": template["game_state"], 
                                "community_cards": template["community_cards"]},
                    deck=["2c", "3d", "4h"],  # Dummy deck
                    pot_size=template["pot_size"],
                    spr=template["spr"]
                )
            
        # End the first session
        self.stats_manager.end_session(player_id, "early_session")
        
        # Start a second session
        self.stats_manager.start_session(player_id, "later_session")
        
        # Add 10 more decisions with better decision quality (80% optimal)
        for i in range(10):
            template = self.decision_templates["Probability-Based"]
            strategy_decisions, optimal, ev = self._mock_ai_decisions("Probability-Based")
            
            mock_decision_maker.make_decision.return_value = strategy_decisions
            
            # For later decisions, patch to make most optimal
            with patch.object(self.analyzer, '_find_matching_strategy', 
                             return_value="Probability-Based"), \
                 patch.object(self.analyzer, '_find_optimal_strategy', 
                             return_value=("Probability-Based", 1.1)):
                
                # Make 80% optimal
                was_optimal = (i < 8)
                player_decision = "call" if was_optimal else "fold"
                
                result = self.analyzer.analyze_decision(
                    player_id=player_id,
                    player_decision=player_decision,
                    hole_cards=template["hole_cards"],
                    game_state={"game_state": template["game_state"], 
                                "community_cards": template["community_cards"]},
                    deck=["2c", "3d", "4h"],  # Dummy deck
                    pot_size=template["pot_size"],
                    spr=template["spr"]
                )
        
        # End the second session
        self.stats_manager.end_session(player_id, "later_session")
        
        # Get player statistics
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        
        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(learning_stats)
        
        # Assertions
        self.assertEqual(learning_stats.total_decisions, 20,
                        "Should have recorded 20 total decisions")
        
        self.assertEqual(trends["trend"], "improving",
                        "Trend should be detected as improving")
        
        self.assertGreater(trends["improvement_rate"], 0,
                          "Improvement rate should be positive")
        
        # Overall decision accuracy should be around 55% (30% + 80% / 2)
        self.assertAlmostEqual(learning_stats.decision_accuracy, 55.0, delta=5.0)
        
        # Clean up
        decision_maker_patcher.stop()

if __name__ == '__main__':
    unittest.main()