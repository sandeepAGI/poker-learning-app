import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.ai_decision_analyzer import AIDecisionAnalyzer, get_decision_analyzer


class TestAIDecisionAnalyzer(unittest.TestCase):
    """Tests for the AIDecisionAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the statistics manager to avoid disk operations
        self.mock_stats_manager = MagicMock()
        
        # Create the analyzer with the mock
        self.analyzer = AIDecisionAnalyzer()
        self.analyzer.stats_manager = self.mock_stats_manager
        
        # Sample data for testing
        self.player_id = "test_player_123"
        self.hole_cards = ["Ah", "Kh"]
        self.community_cards = ["7s", "8d", "Qc"]
        self.game_state = {
            "hand_id": "hand_123",
            "game_state": "flop",
            "community_cards": self.community_cards,
            "current_bet": 20
        }
        self.deck = ["2c", "3d", "4h", "5s", "6c", "7h", "8s", "9c", "Tc", "Jd"]
        self.pot_size = 120
        self.spr = 4.5
        
    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_analyze_decision_match_optimal(self, mock_decision_maker):
        """Test analyzing a decision that matches the optimal strategy."""
        # Important: We need to mock make_decision to directly return the specific value each time
        # It's called, rather than setting up multiple return values through side_effect
        mock_decision_maker.make_decision = MagicMock()
        
        # Set up each strategy to return its own specific decision
        def specific_make_decision(strategy, *args, **kwargs):
            # All strategies return "call" to ensure player's "call" matches optimal "call"
            return "call"
            
        mock_decision_maker.make_decision.side_effect = specific_make_decision
        
        # Patch the _find_optimal_strategy method to return a known value
        with patch.object(self.analyzer, '_find_optimal_strategy', 
                          return_value=("Probability-Based", 1.0)):
            
            # Analyze a "call" decision
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="call",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Check result
            self.assertEqual(result["decision"], "call")
            self.assertEqual(result["matching_strategy"], "Probability-Based")
            self.assertEqual(result["optimal_strategy"], "Probability-Based")
            self.assertTrue(result["was_optimal"])  # This should now be True
            
            # Verify the decision was recorded
            self.mock_stats_manager.record_decision.assert_called_once_with(
                self.player_id, result
            )
            
    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_analyze_decision_non_optimal(self, mock_decision_maker):
        """Test analyzing a decision that doesn't match the optimal strategy."""
        # Set up each strategy to return a specific decision 
        # This is crucial for the test
        mock_decision_maker.make_decision = MagicMock()
        
        def specific_make_decision(strategy, *args, **kwargs):
            if strategy == "Conservative":
                return "fold"
            elif strategy == "Risk Taker":
                return "raise"  # This strategy matches player's "raise" decision
            elif strategy == "Probability-Based":  # This is the optimal strategy
                return "call"   # But it recommends "call" not "raise"
            else:  # Bluffer
                return "fold"
                
        mock_decision_maker.make_decision.side_effect = specific_make_decision
        
        # Patch the _find_optimal_strategy method to return Probability-Based
        with patch.object(self.analyzer, '_find_optimal_strategy', 
                          return_value=("Probability-Based", 0.8)):
            
            # Analyze a "raise" decision (should match Risk Taker)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="raise",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Check result
            self.assertEqual(result["decision"], "raise")
            self.assertEqual(result["matching_strategy"], "Risk Taker")
            self.assertEqual(result["optimal_strategy"], "Probability-Based")
            self.assertFalse(result["was_optimal"])
            
    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_find_matching_strategy_exact(self, mock_decision_maker):
        """Test finding the matching strategy with exact match."""
        strategy_decisions = {
            "Conservative": "call",
            "Risk Taker": "raise",
            "Probability-Based": "call",
            "Bluffer": "fold"
        }
        
        # Test exact matches
        self.assertEqual(
            self.analyzer._find_matching_strategy("call", strategy_decisions),
            "Probability-Based"  # Should match Probability-Based due to priority
        )
        
        self.assertEqual(
            self.analyzer._find_matching_strategy("raise", strategy_decisions),
            "Risk Taker"
        )
        
        self.assertEqual(
            self.analyzer._find_matching_strategy("fold", strategy_decisions),
            "Bluffer"
        )
        
    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_find_matching_strategy_no_exact(self, mock_decision_maker):
        """Test finding the closest matching strategy without exact match."""
        # No strategy matches "call"
        strategy_decisions = {
            "Conservative": "fold",
            "Risk Taker": "raise",
            "Probability-Based": "fold",
            "Bluffer": "raise"
        }
        
        # "call" is closest to "fold" in terms of action strength
        self.assertEqual(
            self.analyzer._find_matching_strategy("call", strategy_decisions),
            "Probability-Based"  # First strategy in priority order that matches the closest strength
        )
        
    def test_find_optimal_strategy(self):
        """Test finding the optimal strategy based on game context."""
        strategy_decisions = {
            "Conservative": "call",
            "Risk Taker": "raise",
            "Probability-Based": "call",
            "Bluffer": "fold"
        }
        
        # Low SPR scenario (< 3)
        low_spr_result = self.analyzer._find_optimal_strategy(
            strategy_decisions,
            self.hole_cards,
            {"game_state": "pre_flop", "community_cards": []},
            100,
            2.5
        )
        self.assertEqual(low_spr_result[0], "Risk Taker")
        
        # Medium SPR scenario (3-6)
        medium_spr_result = self.analyzer._find_optimal_strategy(
            strategy_decisions,
            self.hole_cards,
            {"game_state": "flop", "community_cards": self.community_cards},
            100,
            4.5
        )
        self.assertEqual(medium_spr_result[0], "Probability-Based")
        
        # High SPR scenario (> 6)
        high_spr_result = self.analyzer._find_optimal_strategy(
            strategy_decisions,
            self.hole_cards,
            {"game_state": "pre_flop", "community_cards": []},
            100,
            8.0
        )
        self.assertEqual(high_spr_result[0], "Conservative")
        
    def test_generate_feedback(self):
        """Test feedback generation."""
        decision_data = {
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
        
        # This test just verifies that feedback contains key elements
        feedback = self.analyzer.generate_feedback(decision_data)
        
        self.assertIsInstance(feedback, str)
        self.assertIn("Conservative", feedback)
        self.assertIn("Probability-Based", feedback)
        
    def test_get_player_strategy_profile(self):
        """Test retrieving a player's strategy profile."""
        # Setup mock learning statistics
        mock_learning_stats = MagicMock()
        mock_learning_stats.get_strategy_distribution.return_value = {
            "Conservative": 40.0,
            "Risk Taker": 30.0,
            "Probability-Based": 20.0,
            "Bluffer": 10.0
        }
        mock_learning_stats.dominant_strategy = "Conservative"
        mock_learning_stats.recommended_strategy = "Probability-Based"
        mock_learning_stats.decision_accuracy = 75.0
        mock_learning_stats.total_decisions = 100
        mock_learning_stats.positive_ev_decisions = 70
        
        self.mock_stats_manager.get_learning_statistics.return_value = mock_learning_stats
        
        # Get profile
        profile = self.analyzer.get_player_strategy_profile(self.player_id)
        
        # Check profile properties
        self.assertEqual(profile["dominant_strategy"], "Conservative")
        self.assertEqual(profile["recommended_strategy"], "Probability-Based")
        self.assertEqual(profile["decision_accuracy"], 75.0)
        self.assertEqual(profile["ev_ratio"], 70.0)
        self.assertEqual(profile["total_decisions"], 100)
        
    def test_get_decision_analyzer_singleton(self):
        """Test that get_decision_analyzer returns a singleton instance."""
        # Reset the singleton
        import stats.ai_decision_analyzer
        stats.ai_decision_analyzer._decision_analyzer = None
        
        # Get analyzer twice
        analyzer1 = get_decision_analyzer()
        analyzer2 = get_decision_analyzer()
        
        # Should be the same instance
        self.assertIs(analyzer1, analyzer2)


if __name__ == '__main__':
    unittest.main()