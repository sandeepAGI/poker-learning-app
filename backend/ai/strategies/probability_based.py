from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ai.hand_evaluator import HandEvaluator
from ai.ai_protocol import AIStrategyProtocol

class ProbabilityBasedStrategy:
    """Probability-Based AI: Uses hand strength thresholds for decision-making."""

    def __init__(self):
        self.evaluator = HandEvaluator()

    def evaluate_hand(self, hole_cards: List[str], community_cards: List[str], 
                     deck: List[str]) -> Tuple[float, str]:
        """
        Evaluates the strength of a poker hand.
        
        Args:
            hole_cards: Player's private cards
            community_cards: Shared community cards
            deck: Current deck state
            
        Returns:
            Tuple containing:
            - hand_score: Numerical score of the hand (lower is better)
            - hand_rank_str: String representation of the hand rank
        """
        return self.evaluator.evaluate_hand(hole_cards, community_cards, deck)

    def make_decision(self, hole_cards: List[str], game_state: Dict[str, Any], 
                     deck: List[str], pot_size: int, spr: float) -> str:
        """Makes a decision based on probability and hand strength."""

        hand_score, _ = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if spr == 0:  # All-in scenario
            return "call"

        # Low SPR (More willing to commit)
        if spr < 3:
            if hand_score < 4500:
                return "raise"
            return "call"

        # Medium SPR (Balanced Decision-Making)
        elif 3 <= spr <= 6:
            if hand_score < 5500:
                return "call"
            return "raise"

        # High SPR (Tighter Play, but Still Some Raising)
        else:
            if hand_score < 5000:
                return "fold"
            return "call" if hand_score < 6500 else "raise"
