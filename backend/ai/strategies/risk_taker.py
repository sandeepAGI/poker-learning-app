from typing import List, Dict, Any, Tuple
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ai.hand_evaluator import HandEvaluator
from ai.ai_protocol import AIStrategyProtocol

class RiskTakerStrategy:
    """Risk Taker AI: Raises aggressively regardless of hand strength."""

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
        """Decides AI action based on risk-taking behavior."""
        
        hand_score, _ = self.evaluate_hand(hole_cards, game_state["community_cards"], deck)

        if spr == 0:  # All-in scenario
            return "call"

        # Low SPR (Push Hard)
        if spr < 3:
            return "raise"

        # Medium SPR (Raise Often, But Calls Sometimes)
        elif 3 <= spr <= 6:
            if hand_score < 5500:
                return "call"
            return "raise"

        # High SPR (Selective Aggression)
        else:
            if hand_score < 5000:
                return "call"
            return "raise"
