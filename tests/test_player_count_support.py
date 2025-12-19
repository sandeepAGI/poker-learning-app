"""
Test 4-player and 6-player table support (Phase 1)

Verifies:
1. Backend accepts ai_count 1-5
2. Frontend creates games with 4 or 6 players
3. All opponent seats render correctly on the table
"""
import pytest
import os
from playwright.sync_api import sync_playwright, Page, expect


# Test configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


@pytest.fixture(scope="function")
def browser_page():
    """Fixture to create a browser page for each test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        yield page
        context.close()
        browser.close()


def test_4_player_table_renders_correctly(browser_page: Page):
    """Verify 4-player table (You + 3 AI) works correctly"""
    page = browser_page

    # Navigate to app
    page.goto(FRONTEND_URL)

    # Wait for page to load
    expect(page.locator("h1")).to_contain_text("Poker Learning App")

    # Enter player name
    page.fill("input[placeholder='Enter your name']", "TestPlayer4")

    # Select 4-player table (default value is 3 AI opponents)
    page.select_option("select", "3")

    # Click Start Game
    page.click("button:has-text('Start Game')")

    # Wait for game to load (should see pot)
    expect(page.locator("text=Pot:")).to_be_visible(timeout=10000)

    # Verify we can see the human player
    expect(page.locator("text=TestPlayer4")).to_be_visible()

    # Verify exactly 3 AI opponents by counting Stack displays (excluding human)
    # Each player has "Stack: $X" text
    stack_elements = page.locator("text=/Stack:.*\\$/")
    # Should be 4 total (3 AI + 1 human)
    expect(stack_elements).to_have_count(4, timeout=5000)

    print("✅ 4-player table test passed")


def test_6_player_table_renders_correctly(browser_page: Page):
    """Verify 6-player table (You + 5 AI) works correctly - THIS IS THE KEY TEST"""
    page = browser_page

    # Navigate to app
    page.goto(FRONTEND_URL)

    # Wait for page to load
    expect(page.locator("h1")).to_contain_text("Poker Learning App")

    # Enter player name
    page.fill("input[placeholder='Enter your name']", "TestPlayer6")

    # Select 6-player table (5 AI opponents)
    page.select_option("select", "5")

    # Click Start Game
    page.click("button:has-text('Start Game')")

    # Wait for game to load
    expect(page.locator("text=Pot:")).to_be_visible(timeout=10000)

    # Verify we can see the human player
    expect(page.locator("text=TestPlayer6")).to_be_visible()

    # Verify exactly 5 AI opponents by counting Stack displays
    # Each player has "Stack:" text followed by a dollar amount
    # Get all text and count "Stack:" occurrences
    page_text = page.locator("body").inner_text()
    stack_count = page_text.count("Stack:")

    # Should be 6 total (5 AI + 1 human)
    assert stack_count == 6, f"Expected 6 players (5 AI + human), found {stack_count} Stack labels"

    print("✅ 6-player table test passed - all 5 opponents rendered")


def test_backend_validates_ai_count_correctly():
    """Test that backend properly validates ai_count parameter"""
    import requests

    # Test valid range (1-5)
    for ai_count in [1, 2, 3, 4, 5]:
        response = requests.post(f"{BACKEND_URL}/games", json={
            "player_name": f"TestPlayer{ai_count}",
            "ai_count": ai_count
        })
        assert response.status_code == 200, f"Failed for ai_count={ai_count}: {response.text}"
        data = response.json()
        assert "game_id" in data
        print(f"✅ Backend accepts ai_count={ai_count}")

    # Test invalid values (should fail)
    for ai_count in [0, 6, 10, -1]:
        response = requests.post(f"{BACKEND_URL}/games", json={
            "player_name": f"TestPlayer{ai_count}",
            "ai_count": ai_count
        })
        assert response.status_code == 400, f"Should reject ai_count={ai_count}"
        print(f"✅ Backend correctly rejects ai_count={ai_count}")

    print("✅ Backend validation test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
