from ai.base_ai import BaseAI

class ConservativeStrategy(BaseAI):
    """Conservative AI: Plays only strong hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Decides AI action based on conservative strategy."""
        hand_score, hand_rank = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

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
