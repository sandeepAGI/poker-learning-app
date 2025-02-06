from ai.base_ai import BaseAI

class ProbabilityBasedStrategy(BaseAI):
    """Probability-Based AI: Uses hand strength thresholds for decision-making."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Makes a decision based on probability and hand strength."""
        hand_score, hand_rank = super().make_decision(hole_cards, game_state, deck, pot_size, spr)
        print(f"[DEBUG] Probability AI - Computed Hand Score: {hand_score}, SPR: {spr}")

        if spr == 0:  # All-in scenario
            return "call"

        # Low SPR (More willing to commit)
        if spr < 3:
            if hand_score < 4500:
                return "raise"
            return "call"

        # Medium SPR (Balanced Decision-Making)
        elif 3 <= spr <= 6:
            if hand_score < 5500:
                return "call"
            return "raise"

        # High SPR (Tighter Play, but Still Some Raising)
        else:
            if hand_score < 5000:
                return "fold"
            return "call" if hand_score < 6500 else "raise"
