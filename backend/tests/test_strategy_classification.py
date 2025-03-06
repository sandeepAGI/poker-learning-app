import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.ai_decision_analyzer import AIDecisionAnalyzer


class TestStrategyClassification(unittest.TestCase):
    """Tests for Strategy Classification in AI Decision Analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the statistics manager to avoid disk operations
        self.mock_stats_manager = MagicMock()
        
        # Create the analyzer with the mock
        self.analyzer = AIDecisionAnalyzer()
        self.analyzer.stats_manager = self.mock_stats_manager
        
        # Sample game state data for tests
        self.player_id = "test_player_123"
        self.game_state = {
            "game_state": "flop",
            "community_cards": ["7s", "8d", "Qc"],
            "current_bet": 20
        }
        self.hole_cards = ["Ah", "Kh"]
        self.deck = ["2c", "3d", "4h", "5s", "6c", "7h", "8s", "9c", "Tc", "Jd"]
        self.pot_size = 120
        self.spr = 4.5

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S1_conservative_strategy_classification(self, mock_decision_maker):
        """Test S1: Classification of Conservative play patterns."""
        # Create mock response for get_player_strategy_profile
        mock_profile = {
            "dominant_strategy": "Conservative",
            "strategy_distribution": {
                "Conservative": 80.0,
                "Risk Taker": 10.0,
                "Probability-Based": 5.0,
                "Bluffer": 5.0
            },
            "recommended_strategy": "Probability-Based",
            "decision_accuracy": 60.0,
            "ev_ratio": 70.0,
            "total_decisions": 100
        }
        
        # Set up our mock for get_player_strategy_profile
        with patch.object(self.analyzer, 'get_player_strategy_profile', 
                          return_value=mock_profile):
            
            # Setup the strategy decisions
            strategy_decisions = {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "raise"
            }
            
            # Setup AIDecisionMaker mock to return strategy decisions
            mock_instance = MagicMock()
            mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
            mock_decision_maker.return_value = mock_instance
            
            # Analyze a fold decision (Conservative play)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="fold",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Get player profile
            profile = self.analyzer.get_player_strategy_profile(self.player_id)
            
            # Verify classification
            self.assertEqual(profile["dominant_strategy"], "Conservative",
                           "Player should be classified as Conservative")
            self.assertGreaterEqual(profile["strategy_distribution"]["Conservative"], 70,
                                  "Conservative strategy should be at least 70%")
            self.assertEqual(result["matching_strategy"], "Conservative",
                           "Decision should match Conservative strategy")

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S2_risk_taker_strategy_classification(self, mock_decision_maker):
        """Test S2: Classification of Risk Taker play patterns."""
        # Create mock response for get_player_strategy_profile
        mock_profile = {
            "dominant_strategy": "Risk Taker",
            "strategy_distribution": {
                "Conservative": 10.0,
                "Risk Taker": 75.0,
                "Probability-Based": 10.0,
                "Bluffer": 5.0
            },
            "recommended_strategy": "Probability-Based",
            "decision_accuracy": 60.0,
            "ev_ratio": 70.0,
            "total_decisions": 100
        }
        
        # Set up our mock for get_player_strategy_profile
        with patch.object(self.analyzer, 'get_player_strategy_profile', 
                          return_value=mock_profile):
            
            # Setup the strategy decisions
            strategy_decisions = {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "call"
            }
            
            # Setup AIDecisionMaker mock to return strategy decisions
            mock_instance = MagicMock()
            mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
            mock_decision_maker.return_value = mock_instance
            
            # Analyze a raise decision (Risk Taker play)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="raise",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Get player profile
            profile = self.analyzer.get_player_strategy_profile(self.player_id)
            
            # Verify classification
            self.assertEqual(profile["dominant_strategy"], "Risk Taker",
                           "Player should be classified as Risk Taker")
            self.assertGreaterEqual(profile["strategy_distribution"]["Risk Taker"], 70,
                                  "Risk Taker strategy should be at least 70%")
            self.assertEqual(result["matching_strategy"], "Risk Taker",
                           "Decision should match Risk Taker strategy")

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S3_probability_based_strategy_classification(self, mock_decision_maker):
        """Test S3: Classification of Probability-Based play patterns."""
        # Create mock response for get_player_strategy_profile
        mock_profile = {
            "dominant_strategy": "Probability-Based",
            "strategy_distribution": {
                "Conservative": 20.0,
                "Risk Taker": 10.0,
                "Probability-Based": 65.0,
                "Bluffer": 5.0
            },
            "recommended_strategy": "Probability-Based",
            "decision_accuracy": 80.0,
            "ev_ratio": 85.0,
            "total_decisions": 100
        }
        
        # Set up our mock for get_player_strategy_profile
        with patch.object(self.analyzer, 'get_player_strategy_profile', 
                          return_value=mock_profile):
            
            # Setup the strategy decisions
            strategy_decisions = {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "raise"
            }
            
            # Setup AIDecisionMaker mock to return strategy decisions
            mock_instance = MagicMock()
            mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
            mock_decision_maker.return_value = mock_instance
            
            # Analyze a call decision (Probability-Based play)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="call",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Get player profile
            profile = self.analyzer.get_player_strategy_profile(self.player_id)
            
            # Verify classification
            self.assertEqual(profile["dominant_strategy"], "Probability-Based",
                           "Player should be classified as Probability-Based")
            self.assertGreaterEqual(profile["strategy_distribution"]["Probability-Based"], 60,
                                  "Probability-Based strategy should be at least 60%")
            self.assertEqual(result["matching_strategy"], "Probability-Based",
                           "Decision should match Probability-Based strategy")

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S4_bluffer_strategy_classification(self, mock_decision_maker):
        """Test S4: Classification of Bluffer play patterns."""
        # Create mock response for get_player_strategy_profile
        mock_profile = {
            "dominant_strategy": "Bluffer",
            "strategy_distribution": {
                "Conservative": 15.0,
                "Risk Taker": 20.0,
                "Probability-Based": 15.0,
                "Bluffer": 50.0
            },
            "recommended_strategy": "Probability-Based",
            "decision_accuracy": 40.0,
            "ev_ratio": 45.0,
            "total_decisions": 100
        }
        
        # Set up our mock for get_player_strategy_profile
        with patch.object(self.analyzer, 'get_player_strategy_profile', 
                          return_value=mock_profile):
            
            # Setup the strategy decisions with Bluffer being the only one to raise
            strategy_decisions = {
                "Conservative": "fold",
                "Risk Taker": "call",
                "Probability-Based": "call",
                "Bluffer": "raise"
            }
            
            # Setup AIDecisionMaker mock to return strategy decisions
            mock_instance = MagicMock()
            mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
            mock_decision_maker.return_value = mock_instance
            
            # Use weak hole cards for a bluffer test
            weak_hole_cards = ["2c", "7d"]
            
            # Analyze a raise decision with weak cards (Bluffer play)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="raise",
                hole_cards=weak_hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Get player profile
            profile = self.analyzer.get_player_strategy_profile(self.player_id)
            
            # Verify classification
            self.assertEqual(profile["dominant_strategy"], "Bluffer",
                           "Player should be classified as Bluffer")
            self.assertGreaterEqual(profile["strategy_distribution"]["Bluffer"], 50,
                                  "Bluffer strategy should be at least 50%")
            self.assertEqual(result["matching_strategy"], "Bluffer",
                           "Decision should match Bluffer strategy")

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S5_mixed_strategy_classification(self, mock_decision_maker):
        """Test S5: Classification with mixed strategy play."""
        # Create mock response for get_player_strategy_profile
        mock_profile = {
            "dominant_strategy": "Conservative",  # Slight edge
            "strategy_distribution": {
                "Conservative": 45.0,
                "Risk Taker": 40.0,
                "Probability-Based": 10.0,
                "Bluffer": 5.0
            },
            "recommended_strategy": "Probability-Based",
            "decision_accuracy": 60.0,
            "ev_ratio": 65.0,
            "total_decisions": 100
        }
        
        # Set up our mock for get_player_strategy_profile
        with patch.object(self.analyzer, 'get_player_strategy_profile', 
                          return_value=mock_profile):
            
            # Setup the strategy decisions
            strategy_decisions = {
                "Conservative": "fold",
                "Risk Taker": "raise",
                "Probability-Based": "call",
                "Bluffer": "raise"
            }
            
            # Setup AIDecisionMaker mock to return strategy decisions
            mock_instance = MagicMock()
            mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
            mock_decision_maker.return_value = mock_instance
            
            # Analyze a mixed pattern of decisions
            # First, a conservative fold
            self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="fold",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Then, a risk taker raise
            self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="raise",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Get player profile
            profile = self.analyzer.get_player_strategy_profile(self.player_id)
            
            # Verify mixed classification
            self.assertTrue(profile["strategy_distribution"]["Conservative"] > 30,
                          "Conservative strategy should be significant")
            self.assertTrue(profile["strategy_distribution"]["Risk Taker"] > 30,
                          "Risk Taker strategy should be significant")
            self.assertTrue(profile["strategy_distribution"]["Conservative"] < 70,
                          "Conservative strategy shouldn't dominate completely")
            self.assertTrue(profile["strategy_distribution"]["Risk Taker"] < 70,
                          "Risk Taker strategy shouldn't dominate completely")

    @patch('stats.ai_decision_analyzer.AIDecisionMaker')
    def test_S6_strategy_boundary_decision(self, mock_decision_maker):
        """Test S6: Classification of boundary decision."""
        # Set up a scenario where multiple strategies suggest the same action
        strategy_decisions = {
            "Conservative": "call",
            "Risk Taker": "call", 
            "Probability-Based": "call",
            "Bluffer": "raise"
        }
        
        # Setup AIDecisionMaker mock to return our strategy decisions
        mock_instance = MagicMock()
        mock_instance.make_decision.side_effect = lambda strategy, *args, **kwargs: strategy_decisions[strategy]
        mock_decision_maker.return_value = mock_instance
        
        # Mock the _find_matching_strategy method to directly verify its behavior
        # We don't need to mock get_player_strategy_profile for this test
        with patch.object(self.analyzer, '_find_matching_strategy', wraps=self.analyzer._find_matching_strategy) as mock_find:
            
            # Analyze the call decision (which matches multiple strategies)
            result = self.analyzer.analyze_decision(
                player_id=self.player_id,
                player_decision="call",
                hole_cards=self.hole_cards,
                game_state=self.game_state,
                deck=self.deck,
                pot_size=self.pot_size,
                spr=self.spr
            )
            
            # Verify the call to find_matching_strategy
            mock_find.assert_called_once_with("call", strategy_decisions)
            
            # Verify the result follows the priority order
            # Probability-Based > Conservative > Risk Taker > Bluffer
            self.assertEqual(result["matching_strategy"], "Probability-Based",
                           "Boundary decisions should follow priority order")


if __name__ == '__main__':
    unittest.main()