"""Test WebSocket flow using Python client"""
import asyncio
import websockets
import json
import requests
import time

async def test_websocket_hand_saving():
    """Test if hands are saved via WebSocket"""
    print("\n" + "="*60)
    print("TESTING WEBSOCKET HAND SAVING")
    print("="*60)

    # Create game via REST API
    response = requests.post("http://localhost:8000/games", json={
        "player_name": "WSTest",
        "ai_count": 3
    })
    assert response.status_code == 200
    game_id = response.json()["game_id"]
    print(f"\n✓ Created game: {game_id}")

    # Connect via WebSocket
    uri = f"ws://localhost:8000/ws/{game_id}"
    async with websockets.connect(uri) as websocket:
        print(f"✓ Connected to WebSocket")

        # Receive initial state
        message = await websocket.recv()
        data = json.loads(message)
        print(f"✓ Received initial state: {data['type']}")

        # Play 3 hands
        for hand_num in range(1, 4):
            print(f"\n--- Hand {hand_num} ---")

            # Human folds
            await websocket.send(json.dumps({
                "type": "action",
                "action": "fold"
            }))
            print(f"  → Sent fold action")

            # Wait for state updates
            showdown_reached = False
            for _ in range(50):  # Max 50 messages
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)

                if data['type'] == 'state' and data.get('data', {}).get('current_state') == 'SHOWDOWN':
                    showdown_reached = True
                    print(f"  ✓ Reached SHOWDOWN")
                    break

            if not showdown_reached:
                print(f"  ❌ Did not reach SHOWDOWN!")
                break

            # Start next hand (except for last hand)
            if hand_num < 3:
                await websocket.send(json.dumps({"type": "next_hand"}))
                print(f"  → Sent next_hand")
                await asyncio.sleep(2)  # Wait for hand to start

        print(f"\n✓ Played 3 hands via WebSocket")

    # Check hand history via REST API
    print(f"\n--- Checking Hand History ---")
    response = requests.get(f"http://localhost:8000/games/{game_id}/history")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        total_hands = data.get('total_hands', 0)
        print(f"Total hands in history: {total_hands}")

        if total_hands == 0:
            print(f"❌ FAIL: No hands saved via WebSocket!")
        elif total_hands == 3:
            print(f"✅ SUCCESS: All {total_hands} hands saved")
        else:
            print(f"⚠️  PARTIAL: Only {total_hands}/3 hands saved")

        return total_hands
    else:
        print(f"❌ Error: {response.text}")
        return -1

if __name__ == "__main__":
    result = asyncio.run(test_websocket_hand_saving())
    print(f"\n{'='*60}")
    print(f"RESULT: {result} hands saved via WebSocket")
    print(f"{'='*60}\n")
