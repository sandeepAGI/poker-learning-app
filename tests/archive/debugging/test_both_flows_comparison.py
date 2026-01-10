"""Direct comparison of REST vs WebSocket internal flow"""
import sys
sys.path.insert(0, '/Users/sandeepmangaraj/myworkspace/Utilities/Games/poker-learning-app/backend')

from game.poker_engine import PokerGame

def test_rest_flow():
    """Simulate REST API flow (process_ai=True)"""
    print("\n" + "="*60)
    print("REST API FLOW (process_ai=True)")
    print("="*60)

    game = PokerGame("Human", 3)
    print(f"✓ Created game with {len(game.players)} players")
    print(f"  Initial hand_history: {len(game.hand_history)}")

    # Start hand (REST mode: process_ai=True)
    game.start_new_hand(process_ai=True)
    print(f"\n✓ Started hand (process_ai=True)")
    print(f"  Current state: {game.current_state}")
    print(f"  Current player: {game.get_current_player().name if game.get_current_player() else None}")

    # Human folds (REST mode: process_ai=True)
    success = game.submit_human_action("fold", process_ai=True)
    print(f"\n✓ Human folded (success={success})")
    print(f"  Current state: {game.current_state}")
    print(f"  hand_history length: {len(game.hand_history)}")

    return len(game.hand_history)


def test_websocket_flow():
    """Simulate WebSocket flow (process_ai=False)"""
    print("\n" + "="*60)
    print("WEBSOCKET FLOW (process_ai=False)")
    print("="*60)

    game = PokerGame("Human", 3)
    print(f"✓ Created game with {len(game.players)} players")
    print(f"  Initial hand_history: {len(game.hand_history)}")

    # Start hand (WebSocket mode: process_ai=False)
    game.start_new_hand(process_ai=False)
    print(f"\n✓ Started hand (process_ai=False)")
    print(f"  Current state: {game.current_state}")
    print(f"  Current player: {game.get_current_player().name if game.get_current_player() else None}")

    # Human folds (WebSocket mode: process_ai=False)
    success = game.submit_human_action("fold", process_ai=False)
    print(f"\n✓ Human folded (success={success})")
    print(f"  Current state: {game.current_state}")
    print(f"  Current player index: {game.current_player_index}")
    print(f"  hand_history length: {len(game.hand_history)}")

    # NOW simulate what websocket_manager.py should do
    print(f"\n--- Simulating websocket_manager AI processing ---")

    # Check if betting round complete
    if game._betting_round_complete():
        print(f"  Betting round complete (shouldn't happen yet!)")
    else:
        print(f"  Betting round NOT complete (correct - AI turns needed)")

        # Process AI turns
        game._process_remaining_actions()
        print(f"  ✓ Processed AI turns")
        print(f"  Current state: {game.current_state}")
        print(f"  hand_history length: {len(game.hand_history)}")

        # Advance state if needed
        if game._betting_round_complete():
            print(f"\n  Betting round NOW complete, advancing state...")
            advanced = game._advance_state_for_websocket()
            print(f"  Advanced: {advanced}")
            print(f"  New state: {game.current_state}")
            print(f"  hand_history length: {len(game.hand_history)}")

    return len(game.hand_history)


if __name__ == "__main__":
    rest_result = test_rest_flow()
    ws_result = test_websocket_flow()

    print(f"\n" + "="*60)
    print(f"RESULTS:")
    print(f"  REST API: {rest_result} hands saved")
    print(f"  WebSocket: {ws_result} hands saved")

    if rest_result > 0 and ws_result > 0:
        print(f"  ✅ Both flows save hands!")
    elif rest_result > 0 and ws_result == 0:
        print(f"  ❌ Only REST saves hands - WebSocket broken!")
    elif rest_result == 0 and ws_result > 0:
        print(f"  ❌ Only WebSocket saves hands - REST broken!")
    else:
        print(f"  ❌ Neither flow saves hands!")
    print(f"="*60)
