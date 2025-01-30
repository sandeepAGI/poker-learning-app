import random
from ai.base_ai import BaseAI

class BlufferStrategy(BaseAI):
    """Bluffer AI: Makes unpredictable bets, often bluffing with weak hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck):
        """Bluffer makes decisions randomly to simulate bluffing behavior."""
        hand_score = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if hand_score is None:
            return "raise" if random.random() < 0.75 else "call"

        if random.random() < 0.5:  # 50% chance to bluff regardless of hand
            return "raise"
        return "call" if game_state["current_bet"] < 150 else "fold"
