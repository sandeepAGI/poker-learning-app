from ai.base_ai import BaseAI

class ProbabilityBasedStrategy(BaseAI):
    """Probability-Based AI: Uses hand strength thresholds for decision-making."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Makes a decision based on probability and hand strength."""
        hand_score = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

        # Probability AI applies its own SPR-based decision-making
        if spr < 3:  # Low SPR → More willing to risk if hand strength is decent
            if hand_score < 5000:
                return "raise"
            return "call"

        elif 3 <= spr <= 6:  # Medium SPR → Balanced optimal play
            if hand_score < 6000:
                return "call"
            return "raise"

        else:  # High SPR → Play cautiously, only take strong hands
            if hand_score < 5000:
                return "fold"
            return "call" if hand_score < 7000 else "raise"

