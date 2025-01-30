from ai.base_ai import BaseAI

class ProbabilityBasedStrategy(BaseAI):
    """Probability-Based AI: Uses hand strength thresholds for decision-making."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck):
        """Makes a decision based on probability and hand strength."""
        hand_score = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if hand_score is None:
            return "fold"
        elif hand_score < 5000:
            return "raise"
        elif hand_score < 7000:
            return "call"
        elif hand_score < 7500:  # ✅ Added safeguard for medium hands
            return "call"
        return "fold"
