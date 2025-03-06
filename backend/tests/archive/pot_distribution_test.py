import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add the parent directory to the path so we can import the game_engine module
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import Player, AIPlayer, PotInfo, PokerGame, GameState
from treys import Evaluator, Card

class MockEvaluator:
    """Mock Evaluator class that returns predetermined scores."""
    
    def __init__(self, hand_scores):
        self.hand_scores = hand_scores
        self.real_evaluator = Evaluator()
    
    def evaluate(self, board, hand):
        """Return a predetermined score based on the player's hole cards."""
        # In our tests, we'll use the player ID as the first element of hand
        player_id_card = hand[0]
        player_id = None
        
        # Try to extract player ID from the card value
        for pid, score in self.hand_scores.items():
            if pid in str(player_id_card):
                player_id = pid
                break
        
        if player_id in self.hand_scores:
            return self.hand_scores[player_id]
        
        # Fallback to real evaluation
        return self.real_evaluator.evaluate(board, hand)
    
    def get_rank_class(self, score):
        return self.real_evaluator.get_rank_class(score)
    
    def class_to_string(self, rank_class):
        return self.real_evaluator.class_to_string(rank_class)


def test_simple_win():
    """Test basic pot distribution to a single winner."""
    print("\n=== TEST: Simple Win ===")
    
    # Create players
    players = [
        Player(player_id="p1", stack=1000),
        Player(player_id="p2", stack=1000),
        Player(player_id="p3", stack=1000)
    ]
    
    # Setup test: player 2 has the best hand
    hand_scores = {
        "p1": 5000,  # High Card (worst)
        "p2": 2000,  # Four of a Kind (best)
        "p3": 4000   # Pair (middle)
    }
    
    # Create game instance
    game = PokerGame(players=players)
    game.reset_deck()
    
    # Modify the evaluator to use our mock
    game.evaluator = MockEvaluator(hand_scores)
    
    # Simulate betting
    for player in players:
        player.bet(100)
        player.total_bet = 100
    
    game.pot = 300
    
    # Set up community cards and hole cards with player IDs encoded
    game.community_cards = ["2h", "3h", "4h", "5h", "6h"]
    
    # Use specially formatted cards that encode player IDs
    # The first card will have the player ID as part of its value for our mock evaluator
    players[0].hole_cards = ["p1-Ah", "Kh"]
    players[1].hole_cards = ["p2-Ah", "Kh"]
    players[2].hole_cards = ["p3-Ah", "Kh"]
    
    # Mock the BaseAI class for this test
    import game_engine
    original_base_ai = game_engine.BaseAI
    
    class MockBaseAI:
        def __init__(self):
            self.evaluator = MockEvaluator(hand_scores)
        
        def evaluate_hand(self, hole_cards, community_cards, deck):
            # Extract player ID from first hole card
            player_id = None
            if hole_cards and hole_cards[0].startswith("p"):
                player_id = hole_cards[0].split("-")[0]
            
            # Use predetermined score if available
            if player_id in hand_scores:
                score = hand_scores[player_id]
                # Create a dummy rank based on score
                if score < 3000:
                    rank_str = "Four of a Kind"
                elif score < 4500:
                    rank_str = "Pair"
                else:
                    rank_str = "High Card"
                return score, rank_str
            
            # Fallback for unknown players
            return 7000, "High Card"
    
    # Replace BaseAI with our mock
    game_engine.BaseAI = MockBaseAI
    
    try:
        # Run the actual pot distribution
        game.distribute_pot(game.deck)
        
        # Verify results
        print(f"Player 1 stack: {players[0].stack} (expected: 1000)")
        print(f"Player 2 stack: {players[1].stack} (expected: 1300)")
        print(f"Player 3 stack: {players[2].stack} (expected: 1000)")
        
        assert players[0].stack == 1000, "Player 1 should not win anything"
        assert players[1].stack == 1300, "Player 2 should win the entire pot"
        assert players[2].stack == 1000, "Player 3 should not win anything"
        assert game.pot == 0, "Pot should be empty after distribution"
        
        print("✅ Test passed!")
    finally:
        # Restore the original BaseAI
        game_engine.BaseAI = original_base_ai


if __name__ == "__main__":
    print("\n🔍 Running poker pot distribution tests...")
    print(f"Using backend path: {backend_path}")
    
    try:
        # Run only the simple win test for now
        test_simple_win()
        print("\n🎉 Test completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        import traceback
        print(f"\n❌ Unexpected error during testing: {e}")
        traceback.print_exc()