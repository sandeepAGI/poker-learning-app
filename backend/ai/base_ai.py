import random
from treys import Evaluator, Card

class BaseAI:
    """Base class for AI players, defining common behavior."""

    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hole_cards, community_cards, deck):
        """Evaluates the hand strength, using Monte Carlo if needed."""
        board = [Card.new(card.replace("10", "T")) for card in community_cards]
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]

        # If we have 5+ cards, evaluate normally
        if len(board) + len(hole) >= 5:
            return self.evaluator.evaluate(board, hole)

        # Monte Carlo simulation: complete the board 100 times
        remaining_deck = [Card.new(card.replace("10", "T")) for card in deck if card not in community_cards and card not in hole_cards]
        simulations = 100
        scores = []

        for _ in range(simulations):
            random.shuffle(remaining_deck)
            simulated_board = board + remaining_deck[: (5 - len(board))]  # Fill up to 5 cards
            score = self.evaluator.evaluate(simulated_board, hole)
            scores.append(score)

        # Return the average hand strength
        return sum(scores) / len(scores)

    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Provides hand strength evaluation but does not apply strategy."""
        community_cards = game_state.get("community_cards", [])
        return self.evaluate_hand(hole_cards, community_cards, deck)
