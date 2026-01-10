"""Test WebSocket with 3 hands (like E2E test)"""
import requests
import asyncio
import websockets
import json

async def test_3_hands_websocket():
    """Play 3 hands via WebSocket and check if all are saved"""
    print("\n" + "="*60)
    print("WEBSOCKET: 3 HANDS TEST")
    print("="*60)

    # Create game
    r = requests.post("http://localhost:8000/games", json={"player_name": "WS3Test", "ai_count": 3})
    game_id = r.json()["game_id"]
    print(f"✓ Created game: {game_id}")

    uri = f"ws://localhost:8000/ws/{game_id}"
    async with websockets.connect(uri, ping_interval=None) as ws:
        print(f"✓ Connected to WebSocket")

        # Receive initial state
        await ws.recv()
        print(f"✓ Received initial state")

        # Play 3 hands
        for hand_num in range(1, 4):
            print(f"\n--- Hand {hand_num} ---")

            # Fold
            await ws.send(json.dumps({"type": "action", "action": "fold"}))
            print(f"  → Sent fold")

            # Wait for SHOWDOWN
            showdown_reached = False
            for _ in range(30):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(msg)

                    if data.get("type") == "state_update" and data.get("data", {}).get("current_state") == "SHOWDOWN":
                        showdown_reached = True
                        print(f"  ✓ SHOWDOWN reached")
                        break
                except asyncio.TimeoutError:
                    break

            if not showdown_reached:
                print(f"  ❌ SHOWDOWN not reached!")

            # Start next hand (except last)
            if hand_num < 3:
                await ws.send(json.dumps({"type": "next_hand"}))
                print(f"  → Sent next_hand")
                await asyncio.sleep(2)  # Wait for hand to start

        print(f"\n✓ Played 3 hands")

    # Check history
    await asyncio.sleep(1)
    r = requests.get(f"http://localhost:8000/games/{game_id}/history")
    if r.status_code == 200:
        total = r.json().get("total_hands", 0)
        print(f"\n--- Final Check ---")
        print(f"Total hands in history: {total}")

        if total == 0:
            print(f"❌ NO HANDS SAVED!")
        elif total == 3:
            print(f"✅ ALL 3 HANDS SAVED!")
        else:
            print(f"⚠️  PARTIAL: {total}/3 hands saved")

        return total
    else:
        print(f"❌ Error checking history: {r.status_code}")
        return -1

if __name__ == "__main__":
    result = asyncio.run(test_3_hands_websocket())
    print(f"\n{'='*60}")
    print(f"RESULT: {result}/3 hands saved")
    print(f"{'='*60}\n")
