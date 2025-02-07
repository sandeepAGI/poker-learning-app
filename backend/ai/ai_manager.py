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
        assert len(deck) > 0, "[ERROR] ai_manager.py - Deck is already lost when received!"

        if personality not in AIDecisionMaker.STRATEGY_MAP:
            raise ValueError(f"Unknown personality type: {personality}")

        strategy_class = AIDecisionMaker.STRATEGY_MAP[personality]()

        # ✅ Retrieve `hand_score`, but no need to print separately
        hand_score, _ = strategy_class.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        # ✅ AI makes a decision
        decision = strategy_class.make_decision(hole_cards, game_state, deck, pot_size, spr)

        # ✅ Combine debug logs into a single useful line
        print(f"  [CRITICAL DEBUG] AI Decision: {decision} (Hand Score: {hand_score})")

        # ✅ Catch if the deck was lost
        assert len(deck) > 0, "[ERROR] ai_manager.py - Deck was lost after AI decision!"

        return decision
