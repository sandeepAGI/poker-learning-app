from ai.base_ai import BaseAI

class RiskTakerStrategy(BaseAI):
    """Risk Taker AI: Raises aggressively regardless of hand strength."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Decides AI action based on risk-taking behavior and SPR."""
        hand_score = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

        """Makes a decision based on probability and hand strength."""
        if spr == 0:  # All-in scenario
            return "call"


        # Risk Taker AI applies its own SPR-based decision-making
        if spr < 3:  # Low SPR → Commit aggressively, shove or raise often
            return "raise"

        elif 3 <= spr <= 6:  # Medium SPR → Still aggressive, but calls more
            if hand_score < 6000:
                return "call"
            return "raise"

        else:  # High SPR → More selective aggression
            if hand_score < 5000:
                return "call"
            return "raise"
