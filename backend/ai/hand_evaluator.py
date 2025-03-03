import random
from typing import List, Tuple
from treys import Evaluator, Card


class HandEvaluator:
    """
    Utility class for evaluating poker hand strength.
    Provides methods for exact and Monte Carlo hand evaluation.
    """
    
    def __init__(self):
        """Initialize with a treys Evaluator."""
        self.evaluator = Evaluator()
    
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
        board = [Card.new(card.replace("10", "T")) for card in community_cards]
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]

        if len(board) + len(hole) >= 5:
            hand_score = self.evaluator.evaluate(board, hole)
            hand_rank = self.evaluator.get_rank_class(hand_score)
            hand_rank_str = self.evaluator.class_to_string(hand_rank)
            return hand_score, hand_rank_str

        remaining_deck = [Card.new(card.replace("10", "T")) for card in deck 
                        if card not in community_cards and card not in hole_cards]

        if len(remaining_deck) < (5 - len(board)):
            return float("inf"), "Unknown"

        # Run Monte Carlo simulation
        simulations = 100
        scores = []
        for _ in range(simulations):
            simulated_deck = remaining_deck[:]
            random.shuffle(simulated_deck)
            simulated_board = board + simulated_deck[: (5 - len(board))]
            scores.append(self.evaluator.evaluate(simulated_board, hole))

        avg_score = sum(scores) / len(scores)
        avg_rank = self.evaluator.get_rank_class(int(avg_score))
        avg_rank_str = self.evaluator.class_to_string(avg_rank)

        return avg_score, avg_rank_str