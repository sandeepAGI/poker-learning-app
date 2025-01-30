from ai.base_ai import BaseAI

class RiskTakerStrategy(BaseAI):
    """Risk Taker AI: Raises aggressively regardless of hand strength."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck):
        """Decides AI action based on risk-taking behavior."""
        hand_score = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if hand_score is None:
            return "raise"
        elif hand_score > 6000:
            return "call"
        return "raise"
