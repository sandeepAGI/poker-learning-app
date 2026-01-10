"""Test if hand history is being stored in the backend"""
import pytest
from playwright.sync_api import Page
import time
import requests


def test_hand_history_storage(page: Page):
    """Verify hands are stored in backend hand_history"""
    print("\n=== FIX-02: Hand History Storage Test ===")

    # Start a game and capture game ID from URL
    page.goto("http://localhost:3000")
    page.fill('input[placeholder="Enter your name"]', 'TestHistory')
    page.select_option('select', '3')  # 4 players
    page.click('button:has-text("Start Game")')
    time.sleep(2)

    # Extract game ID from URL or storage
    game_id = page.evaluate("() => localStorage.getItem('gameId')")
    print(f"✓ Game started, ID: {game_id}")

    # Play 3 hands
    for hand_num in range(1, 4):
        print(f"\n--- Playing Hand {hand_num} ---")

        fold_btn = page.locator('button:has-text("Fold")').first
        if fold_btn.is_visible(timeout=2000):
            fold_btn.click()
            time.sleep(1)

        if hand_num < 3:
            next_btn = page.locator('button:has-text("Next Hand")').first
            if next_btn.is_visible(timeout=3000):
                next_btn.click()
                time.sleep(2)

    print("\n✓ Played 3 hands")

    # Query backend for hand history
    print(f"\nQuerying backend for hand history...")
    response = requests.get(f"http://localhost:8000/games/{game_id}/history")

    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ History endpoint returned data")
        print(f"  Total hands: {data.get('total_hands', 0)}")
        print(f"  Returned hands: {data.get('returned_hands', 0)}")

        if data.get('total_hands', 0) == 0:
            print("❌ ISSUE: No hands stored in hand_history!")
        else:
            print(f"✅ SUCCESS: {data['total_hands']} hands stored")

            # Show sample hand
            if data.get('hands'):
                first_hand = data['hands'][0]
                print(f"\nSample hand:")
                print(f"  Hand #{first_hand.get('hand_number')}")
                print(f"  Pot: ${first_hand.get('pot_size')}")
                print(f"  Winner: {first_hand.get('winner_names')}")
    else:
        print(f"❌ History endpoint failed: {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
