"""Final test: WebSocket vs REST API hand saving via actual HTTP/WS endpoints"""
import requests
import asyncio
import websockets
import json

BASE_URL = "http://localhost:8000"

def test_rest_api_saves_hands():
    """Test REST API (known working)"""
    print("\n" + "="*60)
    print("TEST 1: REST API")
    print("="*60)

    # Create game
    r = requests.post(f"{BASE_URL}/games", json={"player_name": "RestTest", "ai_count": 3})
    game_id = r.json()["game_id"]
    print(f"✓ Created game: {game_id}")

    # Fold
    r = requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})
    print(f"✓ Folded (status={r.status_code})")

    # Check history
    r = requests.get(f"{BASE_URL}/games/{game_id}/history")
    total = r.json().get("total_hands", 0)
    print(f"✓ Hand history: {total} hands")

    return total

async def test_websocket_saves_hands():
    """Test WebSocket (suspected broken)"""
    print("\n" + "="*60)
    print("TEST 2: WEBSOCKET")
    print("="*60)

    # Create game via REST
    r = requests.post(f"{BASE_URL}/games", json={"player_name": "WSTest", "ai_count": 3})
    game_id = r.json()["game_id"]
    print(f"✓ Created game: {game_id}")

    # Connect WebSocket
    uri = f"ws://localhost:8000/ws/{game_id}"
    try:
        async with websockets.connect(uri, ping_interval=None) as ws:
            print(f"✓ Connected to WebSocket")

            # Receive initial state
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print(f"✓ Received initial state")

            # Send fold
            await ws.send(json.dumps({"type": "action", "action": "fold"}))
            print(f"✓ Sent fold action")

            # Wait for state updates (showdown)
            for _ in range(20):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(msg)

                    if data.get("type") == "state_update":
                        state = data.get("data", {}).get("current_state")
                        if state == "SHOWDOWN":
                            print(f"✓ Reached SHOWDOWN")
                            break
                except asyncio.TimeoutError:
                    print(f"⚠️  Timeout waiting for next message")
                    break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

    # Check history
    await asyncio.sleep(1)  # Give time for async task to complete
    r = requests.get(f"{BASE_URL}/games/{game_id}/history")
    total = r.json().get("total_hands", 0)
    print(f"✓ Hand history: {total} hands")

    return total

if __name__ == "__main__":
    rest_result = test_rest_api_saves_hands()

    ws_result = asyncio.run(test_websocket_saves_hands())

    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print(f"  REST API: {rest_result} hands saved")
    print(f"  WebSocket: {ws_result} hands saved")

    if rest_result > 0 and ws_result == 0:
        print(f"\n❌ BUG CONFIRMED: WebSocket doesn't save hands!")
    elif rest_result > 0 and ws_result > 0:
        print(f"\n✅ BOTH WORK: Bug might be fixed or test-specific!")
    print("="*60 + "\n")

    # Check backend logs
    print("Check backend logs at: /tmp/backend_fix02_final_test.txt")
    print("Look for [DEBUG-FIX02] and [DEBUG-FIX02-WS] messages")
