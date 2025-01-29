import random
from ai.strategies.conservative import ConservativeAI
from ai.strategies.risk_taker import RiskTakerAI
from ai.strategies.probability_based import ProbabilityBasedAI
from ai.strategies.bluffer import BlufferAI

class AIManager:
    AI_CLASSES = [ConservativeAI, RiskTakerAI, ProbabilityBasedAI, BlufferAI]

    def __init__(self):
        # Randomly assign AI personalities at the start
        self.ai_players = {f'AI-{i+1}': random.choice(self.AI_CLASSES)() for i in range(4)}

    def get_ai_move(self, ai_name, game_state):
        """Returns the move of the given AI based on the game state."""
        if ai_name in self.ai_players:
            return self.ai_players[ai_name].decide_move(game_state)
        return None
