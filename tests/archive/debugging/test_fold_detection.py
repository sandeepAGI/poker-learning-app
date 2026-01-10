"""Test to understand why fold doesn't trigger showdown"""
import sys
sys.path.insert(0, '/Users/sandeepmangaraj/myworkspace/Utilities/Games/poker-learning-app/backend')

from game.poker_engine import PokerGame

def test_fold_detection():
    """Test fold detection logic"""
    print("\n" + "="*60)
    print("TESTING FOLD DETECTION")
    print("="*60)

    # Create game
    game = PokerGame("Human", 3)  # 1 human + 3 AI = 4 total players
    game.start_new_hand(process_ai=False)

    print(f"\n✓ Game created with {len(game.players)} players")
    print(f"\nPlayers:")
    for i, p in enumerate(game.players):
        print(f"  {i}: {p.name} - active={p.is_active}, human={p.is_human}")

    # Find human
    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    print(f"\nHuman at index: {human_index}")

    # Check active count BEFORE fold
    active_before = [p for p in game.players if p.is_active]
    print(f"\nActive players BEFORE fold: {len(active_before)}")
    for p in active_before:
        print(f"  - {p.name}")

    # Human folds
    print(f"\n--- Human folds ---")
    result = game.apply_action(human_index, "fold")

    # Check active count AFTER fold
    active_after = [p for p in game.players if p.is_active]
    print(f"\nActive players AFTER fold: {len(active_after)}")
    for p in active_after:
        print(f"  - {p.name}")

    print(f"\ntriggers_showdown: {result.get('triggers_showdown', False)}")
    print(f"Expected: {len(active_after) <= 1}")

    # Check what the code should have done
    if len(active_after) <= 1:
        print(f"\n❌ BUG: Only {len(active_after)} active players but triggers_showdown=False!")
    else:
        print(f"\n✓ {len(active_after)} active players - fold does not trigger showdown")

    print("="*60)


if __name__ == "__main__":
    test_fold_detection()
