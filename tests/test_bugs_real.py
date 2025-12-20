#!/usr/bin/env python3
"""
Real bug diagnostic - actually tests the bugs, not echo statements
Run with: python test_bugs_real.py
"""
import requests
import sys
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("REAL Bug Investigation")
print("=" * 60)
print()

# Test 1: Check backend is running
print("1. Testing backend connection...")
try:
    response = requests.get(f"{BASE_URL}/admin/analysis-metrics")
    if response.status_code == 200:
        print("✅ Backend is running")
    else:
        print(f"❌ Backend returned status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Backend not running: {e}")
    print("   Start with: cd backend && python main.py")
    sys.exit(1)

print()

# Test 2: Create game and play hand
print("2. Creating game and playing hand...")
try:
    # Create game
    response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
    game_data = response.json()
    game_id = game_data["game_id"]
    print(f"✅ Game created: {game_id}")

    # Play hand (fold)
    response = requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})
    game_state = response.json()

    # Check winner_info
    if game_state.get("winner_info"):
        winner_info = game_state["winner_info"]
        print(f"\n📊 Winner Info from Backend:")
        print(f"   player_id: {winner_info.get('player_id')}")
        print(f"   name: {winner_info.get('name')}")
        print(f"   amount: {winner_info.get('amount')}")

        # Verify player_id exists in players array
        players = game_state.get("players", [])
        player_ids = [p["player_id"] for p in players]

        if winner_info["player_id"] in player_ids:
            print(f"✅ Winner player_id exists in players array")

            # Find the player and verify name matches
            winner_player = next(p for p in players if p["player_id"] == winner_info["player_id"])
            if winner_player["name"] == winner_info["name"]:
                print(f"✅ Winner name matches player record")
            else:
                print(f"❌ BUG FOUND: Winner name mismatch!")
                print(f"   winner_info.name: {winner_info['name']}")
                print(f"   player record name: {winner_player['name']}")
        else:
            print(f"❌ BUG FOUND: Winner player_id '{winner_info['player_id']}' not in players array!")
            print(f"   Available player_ids: {player_ids}")
    else:
        print("⚠️  No winner_info in response (hand still in progress?)")

except Exception as e:
    print(f"❌ Error during game test: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

# Test 3: Test Deep Dive Analysis
print("3. Testing Deep Dive Analysis (Sonnet 4.5)...")
try:
    # Create new game
    response = requests.post(f"{BASE_URL}/games", json={"num_ai_players": 3})
    game_id = response.json()["game_id"]

    # Play hand
    requests.post(f"{BASE_URL}/games/{game_id}/actions", json={"action": "fold"})

    # Request Deep Dive
    print("   Calling Sonnet 4.5 (this may take 5-10 seconds)...")
    response = requests.get(
        f"{BASE_URL}/games/{game_id}/analysis-llm",
        params={"depth": "deep", "use_cache": "false"},
        timeout=30
    )

    analysis_data = response.json()

    if response.status_code == 200:
        print(f"✅ Deep Dive API call succeeded")
        print(f"   Model used: {analysis_data.get('model_used')}")
        print(f"   Cost: ${analysis_data.get('cost')}")

        if analysis_data.get('error'):
            print(f"❌ BUG FOUND: Analysis has error despite 200 status")
            print(f"   Error: {analysis_data['error']}")
        else:
            print(f"✅ No errors in response")

        # Check analysis structure
        analysis = analysis_data.get('analysis', {})
        if 'summary' in analysis:
            print(f"✅ Has summary: {analysis['summary'][:50]}...")
        else:
            print(f"❌ Missing summary field")

        if 'tips_for_improvement' in analysis:
            tips_count = len(analysis['tips_for_improvement'])
            print(f"✅ Has {tips_count} tips")
        else:
            print(f"❌ Missing tips_for_improvement field")

    else:
        print(f"❌ Deep Dive failed with status {response.status_code}")
        print(f"   Response: {response.text[:200]}")

except requests.exceptions.Timeout:
    print(f"❌ BUG FOUND: Deep Dive timed out (>30s)")
except Exception as e:
    print(f"❌ BUG FOUND: Deep Dive error")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Investigation Complete")
print("=" * 60)
