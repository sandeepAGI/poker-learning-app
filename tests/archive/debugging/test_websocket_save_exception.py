"""Test to capture what exception is thrown when saving hands via WebSocket"""
import sys
from io import StringIO
from game.poker_engine import PokerGame

def test_websocket_save_exception():
    """Capture exception from _save_hand_on_early_end"""
    print("\n=== Testing WebSocket Save Exception ===")

    # Capture stdout to see exception traceback
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        # Create game (simulating WebSocket flow)
        game = PokerGame("Human", 3)
        game.start_new_hand(process_ai=False)  # WebSocket mode

        # Simulate human fold that triggers save
        human_index = next(i for i, p in enumerate(game.players) if p.is_human)
        game.apply_action(human_index, "fold")

        # Check if hand was saved
        sys.stdout = old_stdout
        output = captured_output.getvalue()

        if "Warning: Failed to save" in output:
            print("❌ EXCEPTION CAUGHT:")
            print(output)
        else:
            print("✓ No exception")

        print(f"\nHands in history: {len(game.hand_history)}")

        if len(game.hand_history) == 0:
            print("❌ No hands saved!")
        else:
            print(f"✅ {len(game.hand_history)} hands saved")

    finally:
        sys.stdout = old_stdout


if __name__ == "__main__":
    test_websocket_save_exception()
