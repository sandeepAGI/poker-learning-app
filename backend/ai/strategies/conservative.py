from ai.base_ai import BaseAI

class ConservativeStrategy(BaseAI):
    """Conservative AI: Plays only strong hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Decides AI action based on conservative strategy."""

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
            if hand_score < 4000:
                return "raise"
            return "call"

        # Medium SPR (Very Tight Play)
        elif 3 <= spr <= 6:
            if hand_score < 5000:
                return "fold"  # Folding more often with weaker hands
            return "call"

        # High SPR (Premium Hands Only)
        else:
            if hand_score < 4500:
                return "fold"
            return "call"
