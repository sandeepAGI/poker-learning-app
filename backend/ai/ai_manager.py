import random
from treys import Evaluator, Card

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.strategies.conservative import ConservativeStrategy
from ai.strategies.risk_taker import RiskTakerStrategy
from ai.strategies.probability_based import ProbabilityBasedStrategy
from ai.strategies.bluffer import BlufferStrategy


class AIDecisionMaker:
    """Manages AI decision-making based on assigned personality."""

    STRATEGY_MAP = {
        "Conservative": ConservativeStrategy,
        "Risk Taker": RiskTakerStrategy,
        "Probability-Based": ProbabilityBasedStrategy,
        "Bluffer": BlufferStrategy,
    }

    @staticmethod
    def make_decision(personality, hole_cards, game_state, deck):
        """Delegates decision-making to the appropriate strategy, passing deck for Monte Carlo simulation."""
        if personality not in AIDecisionMaker.STRATEGY_MAP:
            raise ValueError(f"Unknown personality type: {personality}")

        strategy_class = AIDecisionMaker.STRATEGY_MAP[personality]()
        return strategy_class.make_decision(hole_cards, game_state, deck)  # ✅ Pass `deck`

# Test AI Decision-Making
if __name__ == "__main__":
    test_cases = [
    ("Conservative", ["Ah", "Kh"], {"community_cards": ["2d", "5s", "Jc"], "current_bet": 50}),
    ("Risk Taker", ["2c", "3d"], {"community_cards": ["7h", "9d", "Ks"], "current_bet": 100}),
    ("Probability-Based", ["Jh", "10h"], {"community_cards": ["3s", "5c", "Qd"], "current_bet": 30}),
    ("Bluffer", ["7s", "4d"], {"community_cards": ["6h", "8c", "As"], "current_bet": 20}),
    ]

    
    for personality, hole_cards, game_state in test_cases:
        decision = AIDecisionMaker.make_decision(personality, hole_cards, game_state)
        print(f"AI ({personality}) with {hole_cards} decides to {decision}.")

