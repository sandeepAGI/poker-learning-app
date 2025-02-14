import random
from treys import Evaluator, Card

class BaseAI:
    """Base class for AI players, defining evaluation behavior."""

    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hole_cards, community_cards, deck):
        """Evaluates the hand strength and returns both hand score and hand rank."""
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