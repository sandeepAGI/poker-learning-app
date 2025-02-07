import unittest
from game_engine import GameEngine  # ✅ Use game engine to manage game state

class TestAIStrategies(unittest.TestCase):
    """Unit tests for AI strategies using game_engine.py to ensure a valid game state."""

    def setUp(self):
        """Initialize game engine before each test."""
        self.engine = GameEngine()  # ✅ Create an instance of the game engine
        self.engine.initialize_players()  # ✅ Initialize AI players
        self.engine.shuffle_deck()  # ✅ Shuffle deck for testing

    def simulate_ai_decision(self, ai_player, spr, expected_choices):
        """Simulates an AI decision using game_engine.py and ensures it is valid."""

        game_state = {"community_cards": self.engine.community_cards, "current_bet": 100}  # ✅ Get game state from engine
        deck = self.engine.deck  # ✅ Use deck from game engine
        pot_size = 1000  # Arbitrary pot size

        print(f"\n[CRITICAL DEBUG] test_ai_strategies.py - Running test for {ai_player.personality}")
        print(f"  Deck Size Before Decision: {len(deck)}")  # ✅ Confirm deck is available

        decision = ai_player.make_decision(game_state, deck, pot_size, spr)

        print(f"  AI Decision: {decision}")
        print(f"  Deck Size After Decision: {len(deck)}")  # ✅ Confirm deck remains intact

        self.assertIn(decision, expected_choices, f"{ai_player.personality} failed for SPR {spr}")

    def test_bluffer_strategy(self):
        """Test the Bluffer AI's decision-making logic using game_engine.py."""
        ai_player = self.engine.players[0]  # ✅ Use an AI player from game engine
        self.simulate_ai_decision(ai_player, spr=2, expected_choices=["raise", "call"])
        self.simulate_ai_decision(ai_player, spr=5, expected_choices=["raise", "call"])
        self.simulate_ai_decision(ai_player, spr=7, expected_choices=["call", "fold"])

    def test_conservative_strategy(self):
        """Test the Conservative AI's decision-making logic using game_engine.py."""
        ai_player = self.engine.players[1]  # ✅ Use an AI player from game engine
        self.simulate_ai_decision(ai_player, spr=2, expected_choices=["call", "fold"])
        self.simulate_ai_decision(ai_player, spr=5, expected_choices=["call", "fold"])
        self.simulate_ai_decision(ai_player, spr=7, expected_choices=["fold"])

    def test_probability_based_strategy(self):
        """Test the Probability-Based AI's decision-making logic using game_engine.py."""
        ai_player = self.engine.players[2]  # ✅ Use an AI player from game engine
        self.simulate_ai_decision(ai_player, spr=2, expected_choices=["raise", "call"])
        self.simulate_ai_decision(ai_player, spr=5, expected_choices=["call"])
        self.simulate_ai_decision(ai_player, spr=7, expected_choices=["fold"])

    def test_risk_taker_strategy(self):
        """Test the Risk Taker AI's decision-making logic using game_engine.py."""
        ai_player = self.engine.players[3]  # ✅ Use an AI player from game engine
        self.simulate_ai_decision(ai_player, spr=2, expected_choices=["raise"])
        self.simulate_ai_decision(ai_player, spr=5, expected_choices=["raise", "call"])
        self.simulate_ai_decision(ai_player, spr=7, expected_choices=["call"])

if __name__ == "__main__":
    unittest.main()
