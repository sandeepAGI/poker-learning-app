import random
from ai.base_ai import BaseAI

class BlufferStrategy(BaseAI):
    """Bluffer AI: Makes unpredictable bets, often bluffing with weak hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Bluffer AI makes unpredictable bets, using SPR to adjust bluffing frequency."""

        # 🔴 NEW DEBUG STATEMENT: Log deck size before evaluation
        print(f"\n[CRITICAL DEBUG] AI Strategy: {self.__class__.__name__}")
        print(f"  Deck Size Before Evaluation: {len(deck)}")  # 🔴 ADD THIS LINE

        if len(deck) == 0:
            print("[CRITICAL ERROR] The deck was lost inside the AI strategy!")  # 🔴 ADD THIS LINE

        hand_score = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

         # 🔴 NEW DEBUG STATEMENT: Log deck size after evaluation
        print(f"  [CRITICAL DEBUG] AI Hand Score: {hand_score}")  # 🔴 ADD THIS LINE
        print(f"  Deck Size After Evaluation: {len(deck)}")  # 🔴 ADD THIS LINE


        if spr == 0:  # All-in scenario
            return "call"
        
        # Low SPR (Push or Fold)
        if spr < 3:
            if hand_score < 3500 and random.random() < 0.8:
                return "raise"  # 80% chance to bluff if hand is weak
            return "call"

        # Medium SPR (More Balanced)
        elif 3 <= spr <= 6:
            if hand_score < 4500 and random.random() < 0.6:
                return "raise"  # 60% bluff chance if weak
            return "call"

        # High SPR (Less Bluffing, More Cautious)
        else:
            if hand_score < 5000 and random.random() < 0.3:
                return "raise"  # 30% chance to bluff
            return "call" if game_state["current_bet"] < 150 else "fold"
