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
        """Ensures the deck is passed correctly to AI strategies."""

        print(f"\n[CRITICAL DEBUG] ai_manager.py - Making decision for {personality}")
        print(f"  Deck Size Before AI Strategy: {len(deck)}")  # 🔴 TRACK IF AI RECEIVES A DECK

        if personality not in AIDecisionMaker.STRATEGY_MAP:
            raise ValueError(f"Unknown personality type: {personality}")

        strategy_class = AIDecisionMaker.STRATEGY_MAP[personality]()

        # ✅ Only retrieve `hand_score`, ignore `hand_rank`
        hand_score, _ = strategy_class.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        print(f"  [CRITICAL DEBUG] AI Manager - Hand Score: {hand_score}")  # 🔴 CONFIRM AI IS WORKING
        print(f"  Deck Size Before Passing to AI Strategy: {len(deck)}")  # 🔴 CONFIRM DECK SIZE

        decision = strategy_class.make_decision(hole_cards, game_state, deck, pot_size, spr)

        print(f"  [CRITICAL DEBUG] AI Decision: {decision}")
        print(f"  Deck Size After AI Decision: {len(deck)}")  # 🔴 CONFIRM IF DECK IS LOST

        return decision
