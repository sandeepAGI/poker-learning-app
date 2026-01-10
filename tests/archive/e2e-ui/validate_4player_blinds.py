"""Visual validation of blind positions in 4-player game (working baseline)"""
import pytest
from playwright.sync_api import Page
import time


def test_validate_4_player_blind_positions(page: Page):
    """Visually validate blind positions in 4-player game (should be working correctly)"""

    print("\n=== VISUAL VALIDATION: 4-Player Blind Positions (WORKING BASELINE) ===")

    # Navigate to app
    page.goto("http://localhost:3000")
    time.sleep(1)

    # Create 4-player game (default)
    print("1. Creating 4-player game...")
    page.fill('input[placeholder="Enter your name"]', 'TestPlayer')

    # Select 4 players (3 AI) - this is the default
    page.select_option('select', '3')  # 3 AI = 4 total players
    time.sleep(0.5)

    # Start game
    page.click('button:has-text("Start Game")')
    time.sleep(3)

    # Take screenshot of first hand
    page.screenshot(path="/tmp/fix01_4player_hand1.png", full_page=True)
    print("📸 Screenshot saved: /tmp/fix01_4player_hand1.png")

    # Get game state from page
    print("\n2. Reading blind positions from UI...")

    # Look for SB and BB labels on the page
    sb_elements = page.locator('text=SB').all()
    bb_elements = page.locator('text=BB').all()

    print(f"   Found {len(sb_elements)} SB labels")
    print(f"   Found {len(bb_elements)} BB labels")

    # Check dealer button
    dealer_elements = page.locator('text=D').all()
    print(f"   Found {len(dealer_elements)} Dealer (D) labels")

    # Fold to end hand quickly
    print("\n3. Completing hand 1...")
    fold_btn = page.locator('button:has-text("Fold")').first
    if fold_btn.is_visible(timeout=2000):
        fold_btn.click()
        time.sleep(1)

    # Start hand 2
    next_btn = page.locator('button:has-text("Next Hand")').first
    if next_btn.is_visible(timeout=3000):
        next_btn.click()
        time.sleep(2)

    # Take screenshot of second hand
    page.screenshot(path="/tmp/fix01_4player_hand2.png", full_page=True)
    print("📸 Screenshot saved: /tmp/fix01_4player_hand2.png")

    print("\n=== VALIDATION COMPLETE ===")
    print("This is the WORKING baseline to compare against 6-player")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
