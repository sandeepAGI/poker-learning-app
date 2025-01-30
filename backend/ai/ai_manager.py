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
    def make_decision(personality, hole_cards, game_state, deck, pot_size, spr):
        """Delegates decision-making to the appropriate strategy, passing deck for Monte Carlo simulation."""
        if personality not in AIDecisionMaker.STRATEGY_MAP:
            raise ValueError(f"Unknown personality type: {personality}")

        strategy_class = AIDecisionMaker.STRATEGY_MAP[personality]()
        return strategy_class.make_decision(hole_cards, game_state, deck, pot_size, spr)  # ✅ Pass `deck`

