"""
API Integration Test - Phase 2
Tests complete game flow through FastAPI endpoints
"""
import requests
import time
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Test 1: Health Check ===")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["status"] == "ok", "Health check failed"
    assert data["phase"] == "Phase 2 - Simple API Layer", "Wrong phase"

    print(f"✓ Health check passed: {data}")

def test_create_game():
    """Test creating a new game"""
    print("\n=== Test 2: Create Game ===")
    response = requests.post(
        f"{BASE_URL}/games",
        json={"player_name": "IntegrationTest", "ai_count": 3}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "game_id" in data, "No game_id returned"

    game_id = data["game_id"]
    print(f"✓ Game created: {game_id}")
    return game_id

def test_get_game_state(game_id):
    """Test getting game state"""
    print("\n=== Test 3: Get Game State ===")
    response = requests.get(f"{BASE_URL}/games/{game_id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["game_id"] == game_id, "Game ID mismatch"
    assert data["state"] == "pre_flop", "Game should start at pre_flop"
    assert len(data["players"]) == 4, "Should have 4 players"
    assert data["pot"] > 0, "Pot should have blinds"

    # Find human player
    human = data["human_player"]
    assert human["name"] == "IntegrationTest", "Human player name mismatch"
    assert len(human["hole_cards"]) == 2, "Human should have 2 hole cards"

    print(f"✓ Game state retrieved")
    print(f"  State: {data['state']}")
    print(f"  Pot: ${data['pot']}")
    print(f"  Human cards: {human['hole_cards']}")
    print(f"  Human is current turn: {human['is_current_turn']}")

    return data

def test_submit_action(game_id):
    """Test submitting player actions"""
    print("\n=== Test 4: Submit Actions ===")

    # Play through the hand
    max_actions = 20
    actions = 0

    while actions < max_actions:
        # Get current state
        state_response = requests.get(f"{BASE_URL}/games/{game_id}")
        state_data = state_response.json()

        current_state = state_data["state"]
        print(f"\n  [{actions+1}] State: {current_state}, Pot: ${state_data['pot']}")

        # Check if showdown
        if current_state == "showdown":
            print(f"  ✓ Reached showdown after {actions} actions")
            break

        # Check if human needs to act
        human = state_data["human_player"]
        if human["is_current_turn"] and human["is_active"]:
            # Submit call action
            action_response = requests.post(
                f"{BASE_URL}/games/{game_id}/actions",
                json={"action": "call"}
            )
            assert action_response.status_code == 200, f"Action failed: {action_response.status_code}"

            print(f"  → Human called")
            actions += 1
        else:
            # Wait for AI to act (they act automatically in _process_remaining_actions)
            time.sleep(0.1)
            actions += 1

    assert current_state == "showdown", f"Did not reach showdown (stuck at {current_state})"
    print(f"\n✓ Played through complete hand")

    return state_data

def test_chip_conservation(game_state):
    """Test chip conservation throughout game"""
    print("\n=== Test 5: Chip Conservation ===")

    total_chips = sum(p["stack"] for p in game_state["players"]) + game_state["pot"]
    expected_chips = 4 * 1000  # 4 players × 1000 starting stack

    assert total_chips == expected_chips, f"Chips not conserved: {total_chips} != {expected_chips}"
    print(f"✓ Chips conserved: ${total_chips} (expected ${expected_chips})")

def test_next_hand(game_id):
    """Test starting next hand"""
    print("\n=== Test 6: Next Hand ===")

    response = requests.post(f"{BASE_URL}/games/{game_id}/next")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["state"] == "pre_flop", "New hand should start at pre_flop"
    assert data["pot"] == 15, "Pot should reset with blinds (5+10)"

    print(f"✓ New hand started")
    print(f"  State: {data['state']}")
    print(f"  Pot: ${data['pot']}")

    return data

def test_invalid_game_id():
    """Test error handling for invalid game ID"""
    print("\n=== Test 7: Invalid Game ID ===")

    response = requests.get(f"{BASE_URL}/games/invalid-id")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    data = response.json()
    assert "not found" in data["detail"].lower(), "Wrong error message"

    print(f"✓ Invalid game ID handled correctly: {data['detail']}")

def test_invalid_action():
    """Test error handling for invalid action"""
    print("\n=== Test 8: Invalid Action ===")

    # Create a new game
    create_response = requests.post(
        f"{BASE_URL}/games",
        json={"player_name": "ErrorTest", "ai_count": 3}
    )
    game_id = create_response.json()["game_id"]

    # Try invalid action
    response = requests.post(
        f"{BASE_URL}/games/{game_id}/actions",
        json={"action": "invalid"}
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    data = response.json()
    assert "invalid" in data["detail"].lower(), "Wrong error message"

    print(f"✓ Invalid action handled correctly: {data['detail']}")

def test_ai_decisions(game_id):
    """Test that AI decisions are returned with reasoning"""
    print("\n=== Test 9: AI Decisions ===")

    response = requests.get(f"{BASE_URL}/games/{game_id}")
    data = response.json()

    if data["last_ai_decisions"]:
        # Check first AI decision
        decision = list(data["last_ai_decisions"].values())[0]

        assert "action" in decision, "Missing action"
        assert "reasoning" in decision, "Missing reasoning"
        assert "spr" in decision, "Missing SPR"
        assert "pot_odds" in decision, "Missing pot odds"
        assert "hand_strength" in decision, "Missing hand strength"

        print(f"✓ AI decision format validated")
        print(f"  Action: {decision['action']}")
        print(f"  SPR: {decision['spr']:.2f}")
        print(f"  Reasoning: {decision['reasoning'][:60]}...")
    else:
        print(f"⚠ No AI decisions recorded yet")

def run_all_tests():
    """Run complete integration test suite"""
    print("=" * 80)
    print("API INTEGRATION TEST SUITE - Phase 2")
    print("=" * 80)
    print(f"Testing against: {BASE_URL}")

    try:
        # Test 1: Health check
        test_health_check()

        # Test 2-6: Complete game flow
        game_id = test_create_game()
        initial_state = test_get_game_state(game_id)
        final_state = test_submit_action(game_id)
        test_chip_conservation(final_state)
        next_hand_state = test_next_hand(game_id)

        # Test 7-8: Error handling
        test_invalid_game_id()
        test_invalid_action()

        # Test 9: AI decisions
        test_ai_decisions(game_id)

        print("\n" + "=" * 80)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 80)
        print("\nPhase 2 API Layer: COMPLETE")
        print("- Health check: ✓")
        print("- Create game: ✓")
        print("- Get game state: ✓")
        print("- Submit actions: ✓")
        print("- Next hand: ✓")
        print("- Error handling: ✓")
        print("- AI decisions: ✓")
        print("- Chip conservation: ✓")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION FAILED: Is the server running at {BASE_URL}?")
        print("   Start the server with: python main.py")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
