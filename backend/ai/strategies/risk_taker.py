from ai.base_ai import BaseAI

class RiskTakerStrategy(BaseAI):
    """Risk Taker AI: Raises aggressively regardless of hand strength."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Decides AI action based on risk-taking behavior."""
        hand_score, hand_rank = super().make_decision(hole_cards, game_state, deck, pot_size, spr)

        if spr == 0:  # All-in scenario
            return "call"

        # Low SPR (Push Hard)
        if spr < 3:
            return "raise"

        # Medium SPR (Raise Often, But Calls Sometimes)
        elif 3 <= spr <= 6:
            if hand_score < 5500:
                return "call"
            return "raise"

        # High SPR (Selective Aggression)
        else:
            if hand_score < 5000:
                return "call"
            return "raise"
