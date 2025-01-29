class ConservativeAI:
    def decide_move(self, game_state):
        """Conservative AI strategy: Only plays strong hands."""
        hand_strength = game_state.get("hand_strength", 0)
        if hand_strength > 0.7:  # Only play if the hand is strong
            return "raise"
        return "fold"
