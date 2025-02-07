import unittest
from ai.strategies.bluffer import BlufferStrategy
from ai.strategies.conservative import ConservativeStrategy
from ai.strategies.probability_based import ProbabilityBasedStrategy
from ai.strategies.risk_taker import RiskTakerStrategy

class TestAIStrategies(unittest.TestCase):
    def setUp(self):
        """Initialize AI strategies before each test."""
        self.bluffer = BlufferStrategy()
        self.conservative = ConservativeStrategy()
        self.probability = ProbabilityBasedStrategy()
        self.risk_taker = RiskTakerStrategy()

    def simulate_ai_decision(self, ai, hand_score, spr, expected_choices):
        """Helper function to simulate AI decision and check if it's valid."""
        game_state = {"community_cards": [], "current_bet": 100}  # Mock game state
        deck = []  # Empty deck since we are testing static decisions
        pot_size = 1000  # Arbitrary pot size
        hole_cards = ["Ah", "Kd"]  # Mock hole cards
        
        decision = ai.make_decision(hole_cards, game_state, deck, pot_size, spr)
        self.assertIn(decision, expected_choices, f"{ai.__class__.__name__} failed for hand score {hand_score}, SPR {spr}")

    def test_bluffer_strategy(self):
        """Test the Bluffer AI's decision-making logic."""
        self.simulate_ai_decision(self.bluffer, hand_score=3000, spr=2, expected_choices=["raise", "call"])
        self.simulate_ai_decision(self.bluffer, hand_score=4500, spr=5, expected_choices=["raise", "call"])
        self.simulate_ai_decision(self.bluffer, hand_score=6000, spr=7, expected_choices=["call", "fold"])

    def test_conservative_strategy(self):
        """Test the Conservative AI's decision-making logic."""
        self.simulate_ai_decision(self.conservative, hand_score=3500, spr=2, expected_choices=["raise", "call"])
        self.simulate_ai_decision(self.conservative, hand_score=5200, spr=5, expected_choices=["call"])
        self.simulate_ai_decision(self.conservative, hand_score=4900, spr=7, expected_choices=["fold"])

    def test_probability_based_strategy(self):
        """Test the Probability-Based AI's decision-making logic."""
        self.simulate_ai_decision(self.probability, hand_score=4000, spr=2, expected_choices=["raise", "call"])
        self.simulate_ai_decision(self.probability, hand_score=5500, spr=5, expected_choices=["raise", "call"])
        self.simulate_ai_decision(self.probability, hand_score=6200, spr=7, expected_choices=["call", "raise"])

    def test_risk_taker_strategy(self):
        """Test the Risk Taker AI's decision-making logic."""
        self.simulate_ai_decision(self.risk_taker, hand_score=3000, spr=2, expected_choices=["raise"])
        self.simulate_ai_decision(self.risk_taker, hand_score=5500, spr=5, expected_choices=["call", "raise"])
        self.simulate_ai_decision(self.risk_taker, hand_score=4900, spr=7, expected_choices=["call"])

if __name__ == "__main__":
    unittest.main()
