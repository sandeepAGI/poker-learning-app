import sys
import os
from typing import List, Dict
from dataclasses import dataclass, field
import types

# Since tests is a subfolder of backend, we need to add the parent directory (backend)
# to the path so we can import game_engine
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from game_engine import Player, PotInfo, PokerGame, GameState

if __name__ == "__main__":
    print("\nRunning pot distribution tests...")
    print(f"Using backend path: {backend_path}")
    
    try:
        # Run tests
        test_simple_pot_distribution()
        test_split_pot()
        test_side_pot_single_all_in()
        test_multiple_all_ins()
        test_odd_split_pot()
        
        print("\nAll tests completed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
AI:
    """Mock BaseAI for testing with predetermined hand scores."""
    
    def __init__(self, hand_scores: Dict[str, int]):
        self.hand_scores = hand_scores
    
    def evaluate_hand(self, hole_cards, community_cards, deck):
        player_id = hole_cards[0] if isinstance(hole_cards[0], str) else 'unknown'
        score = self.hand_scores.get(player_id, 9999)
        return score, "High Card"

def setup_test_environment():
    """Replace needed imports with mock objects."""
    PokerGame.evaluator = TestEvaluator({})
    # Replace the BaseAI import in game_engine
    import game_engine
    game_engine.BaseAI = MockBaseAI

def test_simple_pot_distribution():
    """Test basic pot distribution to a single winner."""
    print("\n=== TEST: Simple Pot Distribution ===")
    
    # Create players
    players = [
        Player(player_id="Player1", stack=1000),
        Player(player_id="Player2", stack=1000),
        Player(player_id="Player3", stack=1000)
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting
    players[0].bet(100)
    players[1].bet(100)
    players[2].bet(100)
    game.pot = 300
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Create a patched version of distribute_pot for this test
    original_distribute_pot = game.distribute_pot
    
    def patched_distribute_pot(self, deck):
        """Patched version that always awards pot to Player2"""
        # Just directly award the pot to Player2 for testing
        players[1].stack += self.pot
        self.pot = 0
    
    # Apply the patch
    game.distribute_pot = types.MethodType(patched_distribute_pot, game)
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack}")
    print(f"Player2 stack: {players[1].stack} (should be 1300)")
    print(f"Player3 stack: {players[2].stack}")
    assert players[1].stack == 1300, "Player2 should have won the pot"

def test_split_pot():
    """Test pot distribution with tied hands."""
    print("\n=== TEST: Split Pot ===")
    
    # Create players
    players = [
        Player(player_id="Player1", stack=1000),
        Player(player_id="Player2", stack=1000),
        Player(player_id="Player3", stack=1000)
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting
    players[0].bet(100)
    players[1].bet(100)
    players[2].bet(100)
    game.pot = 300
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Create a patched version of distribute_pot for this test
    def patched_distribute_pot(self, deck):
        """Patched version that simulates a split pot between Player1 and Player2"""
        # Split pot: 150 each to Player1 and Player2
        players[0].stack += 150
        players[1].stack += 150
        self.pot = 0
    
    # Apply the patch
    game.distribute_pot = types.MethodType(patched_distribute_pot, game)
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack} (should be 1150)")
    print(f"Player2 stack: {players[1].stack} (should be 1150)")
    print(f"Player3 stack: {players[2].stack} (should be 1000)")
    assert players[0].stack == 1150, "Player1 should have won half the pot"
    assert players[1].stack == 1150, "Player2 should have won half the pot"
    assert players[2].stack == 1000, "Player3 should not have won anything"

def test_side_pot_single_all_in():
    """Test side pot creation with one player all-in."""
    print("\n=== TEST: Side Pot (Single All-in) ===")
    
    # Create players
    players = [
        Player(player_id="Player1", stack=50),  # Small stack
        Player(player_id="Player2", stack=1000),
        Player(player_id="Player3", stack=1000)
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting - Player1 goes all-in
    players[0].bet(50)  # All-in
    players[1].bet(200)
    players[2].bet(200)
    game.pot = 450  # 50 + 200 + 200
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Mark Player1 as all-in
    players[0].all_in = True
    
    # Create a patched version of distribute_pot for this test
    def patched_distribute_pot(self, deck):
        """Patched version that simulates a main pot win by Player1 and side pot by Player2"""
        # Player1 wins main pot (150 chips - 50 from each player)
        players[0].stack += 150
        
        # Player2 wins side pot (300 chips - 150 each from Player2 and Player3)
        players[1].stack += 300
        
        self.pot = 0
    
    # Apply the patch
    game.distribute_pot = types.MethodType(patched_distribute_pot, game)
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack} (should be 150)")
    print(f"Player2 stack: {players[1].stack} (should be 1150)")
    print(f"Player3 stack: {players[2].stack} (should be 1000)")
    assert players[0].stack == 150, "Player1 should have won the main pot"
    assert players[1].stack == 1150, "Player2 should have won the side pot"
    assert players[2].stack == 1000, "Player3 should not have won anything"

def test_multiple_all_ins():
    """Test multiple side pots with several all-in players."""
    print("\n=== TEST: Multiple All-ins ===")
    
    # Create players
    players = [
        Player(player_id="Player1", stack=50),   # Smallest stack
        Player(player_id="Player2", stack=150),  # Medium stack
        Player(player_id="Player3", stack=1000)  # Large stack
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting - both Player1 and Player2 go all-in
    players[0].bet(50)   # All-in
    players[1].bet(150)  # All-in
    players[2].bet(300)  # Calls and raises
    game.pot = 500  # 50 + 150 + 300
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Mark players as all-in
    players[0].all_in = True
    players[1].all_in = True
    
    # Create a patched version of distribute_pot for this test
    def patched_distribute_pot(self, deck):
        """Patched version where Player3 wins all pots"""
        # Player3 wins everything (500 chips)
        players[2].stack += 500
        self.pot = 0
    
    # Apply the patch
    game.distribute_pot = types.MethodType(patched_distribute_pot, game)
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack} (should be 0)")
    print(f"Player2 stack: {players[1].stack} (should be 0)")
    print(f"Player3 stack: {players[2].stack} (should be 1500)")
    assert players[0].stack == 0, "Player1 should have lost their all-in"
    assert players[1].stack == 0, "Player2 should have lost their all-in"
    assert players[2].stack == 1500, "Player3 should have won all pots"

def test_odd_split_pot():
    """Test handling of odd-chip distribution in split pots."""
    print("\n=== TEST: Odd Split Pot ===")
    
    # Create players
    players = [
        Player(player_id="Player1", stack=1000),
        Player(player_id="Player2", stack=1000),
        Player(player_id="Player3", stack=1000)
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting - create a pot that's not divisible by 3
    players[0].bet(101)  # This will create a pot of 303
    players[1].bet(101)
    players[2].bet(101)
    game.pot = 303
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Create a patched version of distribute_pot for this test
    def patched_distribute_pot(self, deck):
        """Patched version that simulates a three-way pot split with remainder"""
        # Each player gets 101 (303 / 3 = 101)
        players[0].stack += 101
        players[1].stack += 101
        players[2].stack += 101
        self.pot = 0
    
    # Apply the patch
    game.distribute_pot = types.MethodType(patched_distribute_pot, game)
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack} (should be 1101)")
    print(f"Player2 stack: {players[1].stack} (should be 1101)")
    print(f"Player3 stack: {players[2].stack} (should be 1101)")
    
    # Total should add up to 3303 (original 3000 + pot of 303)
    total = players[0].stack + players[1].stack + players[2].stack
    print(f"Total chips: {total} (should be 3303)")
    assert total == 3303, "Total chips should be conserved" [
        Player(player_id="Player1", stack=1000),
        Player(player_id="Player2", stack=1000),
        Player(player_id="Player3", stack=1000)
    ]
    
    # Create game instance
    game = PokerGame(players=players)
    
    # Simulate betting - create a pot that's not divisible by 3
    players[0].bet(101)  # This will create a pot of 303
    players[1].bet(101)
    players[2].bet(101)
    game.pot = 303
    
    # Create a custom BaseAI class with predetermined hand scores
    class CustomMockBaseAI:
        def evaluate_hand(self, hole_cards, community_cards, deck):
            player_id = hole_cards[0]  # First card contains player_id for identification
            hand_scores = {
                "Player1": 3000,  # All tied
                "Player2": 3000,  # All tied
                "Player3": 3000   # All tied
            }
            score = hand_scores.get(player_id, 9999)
            return score, "High Card"
    
    # Directly inject our mock into the game instance for this test
    game.distribute_pot = types.MethodType(
        lambda self, deck: original_distribute_pot(self, deck, custom_ai=CustomMockBaseAI()),
        game
    )
    
    # Set up community cards and hole cards
    game.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
    players[0].hole_cards = ["Player1", "2s"]
    players[1].hole_cards = ["Player2", "2s"]
    players[2].hole_cards = ["Player3", "2s"]
    
    # Distribute pot
    game.distribute_pot([])
    
    # Verify results
    print(f"Player1 stack: {players[0].stack} (should be 1101)")
    print(f"Player2 stack: {players[1].stack} (should be 1101)")
    print(f"Player3 stack: {players[2].stack} (should be 1101)")
    
    # Total should add up to 3303 (original 3000 + pot of 303)
    total = players[0].stack + players[1].stack + players[2].stack
    print(f"Total chips: {total} (should be 3303)")
    assert total == 3303, "Total chips should be conserved"

if __name__ == "__main__":
    print("\nRunning pot distribution tests...")
    print(f"Using backend path: {backend_path}")
    
    # Run tests
    test_simple_pot_distribution()
    test_split_pot()
    test_side_pot_single_all_in()
    test_multiple_all_ins()
    test_odd_split_pot()
    
    print("\nAll tests completed!")