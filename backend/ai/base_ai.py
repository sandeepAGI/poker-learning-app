import random
from treys import Evaluator, Card

class BaseAI:
    """Base class for AI players, defining common behavior."""

    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hole_cards, community_cards, deck):
        """Evaluates the hand strength and returns both hand score and hand rank."""
        board = [Card.new(card.replace("10", "T")) for card in community_cards]
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]

        print(f"\n[DEBUG] evaluate_hand() called with:")
        print(f"  Hole Cards: {hole_cards}")
        print(f"  Community Cards: {community_cards}")
        print(f"  Deck Size Before Monte Carlo: {len(deck)}")

        if len(board) + len(hole) >= 5:
            hand_score = self.evaluator.evaluate(board, hole)
            hand_rank = self.evaluator.get_rank_class(hand_score)
            hand_rank_str = Evaluator.class_to_string(hand_rank)
            return hand_score, hand_rank_str

        # ✅ Check if deck is being emptied before Monte Carlo runs
        remaining_deck = [Card.new(card.replace("10", "T")) for card in deck if card not in community_cards and card not in hole_cards]
        print(f"  [DEBUG] Monte Carlo - Remaining Deck Size: {len(remaining_deck)} BEFORE simulation")

        if len(remaining_deck) < (5 - len(board)):  
            print("[ERROR] Not enough cards in deck for Monte Carlo! CHECK WHERE THE DECK IS BEING MODIFIED.")
            return float("inf"), "Unknown"

        # Run Monte Carlo simulation safely without modifying the actual deck
        simulations = 100
        scores = []
        for _ in range(simulations):
            simulated_deck = remaining_deck[:]  # ✅ Create a fresh copy
            random.shuffle(simulated_deck)
            simulated_board = board + simulated_deck[: (5 - len(board))]
            scores.append(self.evaluator.evaluate(simulated_board, hole))

        avg_score = sum(scores) / len(scores)
        avg_rank = self.evaluator.get_rank_class(int(avg_score))
        avg_rank_str = Evaluator.class_to_string(avg_rank)

        return avg_score, avg_rank_str
    
    def make_decision(self, hole_cards, game_state, deck, pot_size, spr):
        """Ensures the AI actually receives the deck before evaluating hand strength."""
    
        print(f"\n[CRITICAL DEBUG] AI Strategy: {self.__class__.__name__}")
        print(f"  Hole Cards: {hole_cards}")
        print(f"  Community Cards: {game_state.get('community_cards', [])}")
        print(f"  Deck Size Before Evaluation: {len(deck)}")  # 🔴 This will confirm if AI is getting a deck

        # Ensure AI is receiving a deck
        if len(deck) == 0:
            print("[CRITICAL ERROR] The AI did not receive a deck! Investigate test setup.")

        hand_score, hand_rank = self.evaluate_hand(hole_cards, game_state.get("community_cards", []), deck)

        print(f"  [CRITICAL DEBUG] AI Received Hand Score: {hand_score}, Hand Rank: {hand_rank}")
    
        return hand_score  # Decision logic remains unchanged