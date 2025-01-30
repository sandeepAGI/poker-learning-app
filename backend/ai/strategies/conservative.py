from ai.base_ai import BaseAI

class ConservativeStrategy(BaseAI):
    """Conservative AI: Plays only strong hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck):
        """Decides AI action based on conservative strategy, using deck for Monte Carlo evaluation"""
        hand_score = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if hand_score is None or hand_score > 7000:  # Weak hand = fold
            return "fold"
        elif hand_score > 5000:
            return "call"
        return "raise"
