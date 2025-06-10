import random
import itertools
from typing import List, Tuple
from treys import Evaluator, Card
from utils.performance import performance_manager, profile_time


class HandEvaluator:
    """
    Utility class for evaluating poker hand strength.
    Provides methods for exact and Monte Carlo hand evaluation.
    """
    
    def __init__(self):
        """Initialize with a treys Evaluator."""
        self.evaluator = Evaluator()
    
    @performance_manager.cache_hand_evaluation
    @profile_time
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

        # Run optimized Monte Carlo simulation (reduced from 100 to 50 for performance)
        simulations = 50
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
        
    def get_best_hand(self, hole_cards: List[str], community_cards: List[str]) -> List[str]:
        """
        Determines the best 5-card poker hand from hole cards and community cards.
        Used only when a showdown occurs between multiple players.
        
        Args:
            hole_cards: Player's private cards (2 cards)
            community_cards: Shared community cards
            
        Returns:
            List of 5 card strings representing the best hand.
            If not enough cards are available, returns the available cards.
        """
        # Handle edge cases: missing hole cards or community cards
        if not hole_cards:
            return []
        
        # Convert cards to treys format
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]
        
        # If there are fewer than 3 community cards (e.g., everyone folded pre-flop),
        # return just the hole cards - the winning condition was based on position not hand strength
        if not community_cards or len(community_cards) < 3:
            return hole_cards
        
        # Convert community cards
        board = [Card.new(card.replace("10", "T")) for card in community_cards]
        
        # Get all cards (hole + community)
        all_cards = hole + board
        
        # If we don't have 5 cards total, return all available cards
        if len(all_cards) < 5:
            result = []
            for card in all_cards:
                card_str = Card.int_to_str(card)
                if card_str[0] == 'T':
                    card_str = '10' + card_str[1]
                result.append(card_str)
            return result
        
        # Find the best 5-card hand among all possible combinations
        best_score = float('inf')  # Lower is better in treys
        best_hand_combo = None
        
        # Try all 5-card combinations from all available cards
        for combo in itertools.combinations(all_cards, 5):
            score = self.evaluator.evaluate([], list(combo))
            if score < best_score:
                best_score = score
                best_hand_combo = combo
        
        # Convert the best hand back to string representation
        if best_hand_combo:
            best_hand = []
            for card in best_hand_combo:
                card_str = Card.int_to_str(card)
                if card_str[0] == 'T':
                    card_str = '10' + card_str[1]
                best_hand.append(card_str)
            return best_hand
        
        # Fallback: if no best hand found, return available cards
        return hole_cards