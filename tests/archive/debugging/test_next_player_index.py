"""Test to see what happens to current_player_index after fold"""
import sys
sys.path.insert(0, '/Users/sandeepmangaraj/myworkspace/Utilities/Games/poker-learning-app/backend')

from game.poker_engine import PokerGame

def test_next_player_index():
    """Test current_player_index after fold"""
    print("\n" + "="*60)
    print("TESTING current_player_index AFTER FOLD")
    print("="*60)

    # Create game
    game = PokerGame("Human", 3)
    game.start_new_hand(process_ai=False)

    print(f"\n✓ Game started")
    print(f"  current_player_index: {game.current_player_index}")

    current = game.get_current_player()
    if current:
        print(f"  Current player: {current.name}")

    # Find human
    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    print(f"\nHuman index: {human_index}")

    # Submit human action using submit_human_action (NOT apply_action)
    # This is what WebSocket calls
    print(f"\n--- Calling submit_human_action('fold', process_ai=False) ---")
    success = game.submit_human_action("fold", process_ai=False)

    print(f"\nResult: {success}")
    print(f"current_player_index: {game.current_player_index}")

    if game.current_player_index is not None:
        next_player = game.get_current_player()
        if next_player:
            print(f"Next player: {next_player.name} (human={next_player.is_human})")
        else:
            print(f"get_current_player() returned None!")
    else:
        print(f"current_player_index is None!")

    # Show all players and their status
    print(f"\nAll players:")
    for i, p in enumerate(game.players):
        print(f"  {i}: {p.name} - active={p.is_active}, has_acted={p.has_acted}")

    print("="*60)


if __name__ == "__main__":
    test_next_player_index()
