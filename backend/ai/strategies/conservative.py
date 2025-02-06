from ai.base_ai import BaseAI

class ConservativeStrategy(BaseAI):
    """Conservative AI: Plays only strong hands."""

    def __init__(self):
        super().__init__()

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Decides AI action based on conservative strategy, using deck for Monte Carlo evaluation"""
        hand_score = super().make_decision(hole_cards, game_state, deck, pot_size, spr)
        """Makes a decision based on probability and hand strength."""
        if spr == 0:  # All-in scenario
            return "call"
        # Conservative AI applies SPR logic here
        if spr < 3:  # Low SPR → Commit but only if very strong
            if hand_score < 4000:
                return "raise"
            return "call"

        elif 3 <= spr <= 6:  # Medium SPR → Balanced cautious play
            if hand_score < 5000:
                return "fold"
            return "call"

        else:  # High SPR → Only play premium hands
            if hand_score < 3000:
                return "fold"
            return "call"  # Conservative AI rarely raises
