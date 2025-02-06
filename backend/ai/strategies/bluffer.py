import random
from ai.base_ai import BaseAI

class BlufferStrategy(BaseAI):
    """Bluffer AI: Makes unpredictable bets, often bluffing with weak hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Bluffer AI makes unpredictable bets, using SPR to adjust bluffing frequency."""
        hand_score = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

        """Makes a decision based on probability and hand strength."""
        if spr == 0:  # All-in scenario
            return "call"
        
        # Bluffer AI applies its own SPR-based decision-making
        if spr < 3:  # Low SPR → Go aggressive, try to steal the pot
            if random.random() < 0.7:  # 70% chance to bluff
                return "raise"
            return "call"

        elif 3 <= spr <= 6:  # Medium SPR → Balanced bluffing
            if hand_score < 5000 and random.random() < 0.5:
                return "raise"  # 50% chance to bluff if hand is weak
            return "call"

        else:  # High SPR → Bluff less, play a bit more cautiously
            if hand_score < 4000 and random.random() < 0.3:
                return "raise"  # 30% chance to bluff
            return "call" if game_state["current_bet"] < 150 else "fold"
