import random
from treys import Evaluator, Card

class BaseAI:
    """Base class for AI players, defining common behavior."""

    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hole_cards, community_cards, deck):
        """Evaluates the hand strength, using Monte Carlo if needed."""
    
        # ✅ Print input data before evaluation
        #print(f"\n--- DEBUG: evaluate_hand() START ---")
        #print(f"🃏 Hole Cards: {hole_cards}")
        #print(f"🂡 Community Cards: {community_cards}")
        #print(f"🃏 Deck Before Monte Carlo: {len(deck)} cards")

        board = [Card.new(card.replace("10", "T")) for card in community_cards]
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]

        # ✅ Check if we have enough cards for evaluation
        total_cards = len(board) + len(hole)
        #print(f"🃏 Total Cards Available: {total_cards}")

        if total_cards >= 5:
         #   print("✅ Evaluating normally without Monte Carlo.")
            return self.evaluator.evaluate(board, hole)

        # ✅ Monte Carlo simulation: complete the board 100 times
        remaining_deck = [Card.new(card.replace("10", "T")) for card in deck if card not in community_cards and card not in hole_cards]
        print(f"🃏 Cards Available for Monte Carlo: {len(remaining_deck)}")

        simulations = 100
        scores = []

        for _ in range(simulations):
            random.shuffle(remaining_deck)

            # ✅ Ensure we always fill the board to 5 cards
            simulated_board = board + remaining_deck[: (5 - len(board))]

            try:
                score = self.evaluator.evaluate(simulated_board, hole)
                scores.append(score)
            except KeyError as e:
                print(f"❌ ERROR: Hand evaluation failed with KeyError: {e}")

        # ✅ Prevent division by zero
        if not scores:
          #  print("❌ ERROR: No valid hands were evaluated, returning worst score.")
            return float("inf")

        #print(f"✅ Hand evaluation complete. Average score: {sum(scores) / len(scores)}")
        return sum(scores) / len(scores)


    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Provides hand strength evaluation but does not apply strategy."""
        community_cards = game_state.get("community_cards", [])
        return self.evaluate_hand(hole_cards, community_cards, deck)
