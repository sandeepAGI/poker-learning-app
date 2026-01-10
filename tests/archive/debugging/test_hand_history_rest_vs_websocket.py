"""Test if hand history works via REST API vs WebSocket"""
import requests
import json


def test_hand_history_via_rest_api():
    """Test if hands are saved when using REST API"""
    print("\n=== Testing Hand History via REST API ===")

    # Create game via REST
    response = requests.post("http://localhost:8000/games", json={
        "player_name": "RestTester",
        "ai_count": 3
    })
    assert response.status_code == 200
    game_id = response.json()["game_id"]
    print(f"✓ Created game: {game_id}")

    # Play 3 hands via REST API
    for hand_num in range(1, 4):
        print(f"\n--- Hand {hand_num} via REST ---")

        # Fold via REST
        response = requests.post(
            f"http://localhost:8000/games/{game_id}/actions",
            json={"action": "fold"}
        )

        if response.status_code != 200:
            print(f"  Action failed: {response.text}")
            break

        print(f"  ✓ Folded")

        # Start next hand if not last
        if hand_num < 3:
            response = requests.post(f"http://localhost:8000/games/{game_id}/next")
            if response.status_code != 200:
                print(f"  Next hand failed: {response.text}")
                break
            print(f"  ✓ Next hand started")

    # Check hand history
    print(f"\n--- Checking Hand History ---")
    response = requests.get(f"http://localhost:8000/games/{game_id}/history")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        total_hands = data.get('total_hands', 0)
        print(f"Total hands in history: {total_hands}")

        if total_hands == 0:
            print("❌ FAIL: No hands saved via REST API either!")
        elif total_hands == 3:
            print(f"✅ SUCCESS: All {total_hands} hands saved via REST API")
        else:
            print(f"⚠️  PARTIAL: Only {total_hands}/3 hands saved")

        return total_hands
    else:
        print(f"❌ History endpoint error: {response.text}")
        return -1


if __name__ == "__main__":
    result = test_hand_history_via_rest_api()
    print(f"\n{'='*50}")
    print(f"Result: {result} hands saved")
    print(f"{'='*50}")
