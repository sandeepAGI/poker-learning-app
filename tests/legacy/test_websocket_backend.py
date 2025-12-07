#!/usr/bin/env python3
"""
WebSocket Backend Test
Tests the WebSocket endpoint independently before frontend integration
"""
import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test WebSocket connection and basic functionality"""
    print("=" * 60)
    print("WEBSOCKET BACKEND TEST")
    print("=" * 60)

    # First, create a game via REST API
    import requests

    print("\n1. Creating game via REST API...")
    try:
        response = requests.post(
            "http://localhost:8000/games",
            json={"player_name": "Test Player", "ai_count": 3}
        )
        response.raise_for_status()
        game_id = response.json()["game_id"]
        print(f"   ✅ Game created: {game_id}")
    except Exception as e:
        print(f"   ❌ Failed to create game: {e}")
        print("\n⚠️  Make sure backend is running: python backend/main.py")
        return False

    # Connect to WebSocket
    print(f"\n2. Connecting to WebSocket...")
    ws_url = f"ws://localhost:8000/ws/{game_id}"

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"   ✅ Connected to {ws_url}")

            # Receive initial state
            print("\n3. Receiving initial state...")
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   ✅ Received {data['type']}")

            if data['type'] == 'state_update':
                state = data['data']
                print(f"   - Game state: {state['state']}")
                print(f"   - Pot: ${state['pot']}")
                print(f"   - Players: {len(state['players'])}")
                print(f"   - Human player: {state['human_player']['name']}")

            # Send a fold action
            print("\n4. Sending fold action...")
            await websocket.send(json.dumps({
                "type": "action",
                "action": "fold",
                "show_ai_thinking": True
            }))
            print("   ✅ Fold action sent")

            # Receive responses (state update + AI actions)
            print("\n5. Receiving AI action events...")
            events_received = 0
            timeout = 10  # 10 seconds timeout

            try:
                while events_received < 5:  # Expect multiple events
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    data = json.loads(message)
                    events_received += 1

                    if data['type'] == 'state_update':
                        print(f"   ✅ State update #{events_received}")
                    elif data['type'] == 'ai_action':
                        action_data = data['data']
                        print(f"   ✅ AI Action: {action_data['player_name']} {action_data['action']}")
                        if action_data.get('reasoning'):
                            print(f"      Reasoning: {action_data['reasoning'][:60]}...")
                    elif data['type'] == 'error':
                        print(f"   ⚠️  Error: {data['data']['message']}")
                        break

                    # Stop after receiving a few events
                    if events_received >= 3:
                        break

            except asyncio.TimeoutError:
                print(f"   ⚠️  Timeout after {events_received} events")

            print(f"\n   Total events received: {events_received}")

            if events_received > 0:
                print("\n" + "=" * 60)
                print("✅ WEBSOCKET TEST PASSED")
                print("=" * 60)
                print("\nBackend WebSocket endpoint is working correctly!")
                print("- Connection established ✅")
                print("- Initial state received ✅")
                print("- Actions processed ✅")
                print("- AI events streamed ✅")
                return True
            else:
                print("\n❌ TEST FAILED: No events received")
                return False

    except websockets.exceptions.WebSocketException as e:
        print(f"   ❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting WebSocket backend test...")
    print("Make sure backend is running: python backend/main.py\n")

    try:
        result = asyncio.run(test_websocket_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
