import unittest
from ai.strategies.bluffer import BlufferStrategy
from ai.strategies.conservative import ConservativeStrategy
from ai.strategies.probability_based import ProbabilityBasedStrategy
from ai.strategies.risk_taker import RiskTakerStrategy

class TestPokerStrategies(unittest.TestCase):
    def setUp(self):
        self.bluffer_ai = BlufferStrategy()
        self.conservative_ai = ConservativeStrategy()
        self.probability_ai = ProbabilityBasedStrategy()
        self.risk_taker_ai = RiskTakerStrategy()
    
    def test_bluffer_ai_behavior(self):
        """Test if the Bluffer AI bluffs correctly based on SPR."""
        hole_cards = ["2c", "7d"]  # Weak hand
        game_state = {"current_bet": 50, "community_cards": ["Ah", "Kd", "3c"]}
        deck = ["7s", "Jd", "2d", "9h", "Qh"] * 3
        pot_size = 300
        spr_low = 2.0  # Low SPR scenario
        spr_high = 7.0  # High SPR scenario
        spr_zero = 0.0  # All-in scenario
        
        decision_zero_spr = self.bluffer_ai.make_decision(hole_cards, game_state, deck, pot_size, spr_zero)
        print(f"[DEBUG] Bluffer AI - Expected: Call at SPR ({spr_zero}), Actual: {decision_zero_spr}")
        self.assertEqual(decision_zero_spr, "call")
    
    def test_conservative_ai_behavior(self):
        """Test if the Conservative AI plays only strong hands."""
        hole_cards = ["As", "Ks"]  # Strong hand
        game_state = {"current_bet": 100, "community_cards": ["Ah", "Kd", "3c"]}
        deck = ["7s", "Jd", "2d", "9h", "Qh"] * 3
        pot_size = 500
        spr = 5.0
        spr_zero = 0.0  # All-in scenario
        
        decision_zero_spr = self.conservative_ai.make_decision(hole_cards, game_state, deck, pot_size, spr_zero)
        print(f"[DEBUG] Conservative AI - Expected: Call at SPR ({spr_zero}), Actual: {decision_zero_spr}")
        self.assertEqual(decision_zero_spr, "call")
    
    def test_probability_ai_behavior(self):
        """Test if the Probability-Based AI makes optimal decisions based on hand strength."""
        hole_cards = ["9h", "8h"]  # Mid-strength hand
        game_state = {"current_bet": 75, "community_cards": ["Ah", "Kd", "3c"]}
        deck = ["7s", "Jd", "2d", "9h", "Qh"] * 3
        pot_size = 400
        spr = 4.0
        spr_zero = 0.0  # All-in scenario
        
        decision_zero_spr = self.probability_ai.make_decision(hole_cards, game_state, deck, pot_size, spr_zero)
        print(f"[DEBUG] Probability AI - Expected: Call at SPR ({spr_zero}), Actual: {decision_zero_spr}")
        self.assertEqual(decision_zero_spr, "call")
    
    def test_risk_taker_ai_behavior(self):
        """Test if the Risk-Taker AI raises aggressively regardless of hand strength."""
        hole_cards = ["3c", "7d"]  # Weak hand
        game_state = {"current_bet": 50, "community_cards": ["Ah", "Kd", "3c"]}
        deck = ["7s", "Jd", "2d", "9h", "Qh"] * 3
        pot_size = 300
        spr = 2.0  # Low SPR scenario
        spr_zero = 0.0  # All-in scenario
        
        decision_zero_spr = self.risk_taker_ai.make_decision(hole_cards, game_state, deck, pot_size, spr_zero)
        print(f"[DEBUG] Risk-Taker AI - Expected: Call at SPR ({spr_zero}), Actual: {decision_zero_spr}")
        self.assertEqual(decision_zero_spr, "call")

if __name__ == "__main__":
    unittest.main()
