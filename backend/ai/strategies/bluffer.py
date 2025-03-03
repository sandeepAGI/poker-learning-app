import random
from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ai.hand_evaluator import HandEvaluator
from ai.ai_protocol import AIStrategyProtocol

class BlufferStrategy:
    """Bluffer AI: Makes unpredictable bets, often bluffing with weak hands."""

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
        """Bluffer AI makes unpredictable bets, using SPR to adjust bluffing frequency."""

        hand_score, _ = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if spr == 0:  # All-in scenario
            return "call"
        
        # Low SPR (Push or Fold)
        if spr < 3:
            if hand_score < 3500 and random.random() < 0.8:
                return "raise"  # 80% chance to bluff if hand is weak
            return "call"

        # Medium SPR (More Balanced)
        elif 3 <= spr <= 6:
            if hand_score < 4500 and random.random() < 0.6:
                return "raise"  # 60% bluff chance if weak
            return "call"

        # High SPR (Less Bluffing, More Cautious)
        else:
            if hand_score < 5000 and random.random() < 0.3:
                return "raise"  # 30% chance to bluff
            return "call" if game_state["current_bet"] < 150 else "fold"
