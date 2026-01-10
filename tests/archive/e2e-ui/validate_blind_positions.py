"""Visual validation of blind positions in 6-player game"""
import pytest
from playwright.sync_api import Page
import time


def test_validate_6_player_blind_positions(page: Page):
    """Visually validate blind positions in 6-player game"""

    print("\n=== VISUAL VALIDATION: 6-Player Blind Positions ===")

    # Navigate to app
    page.goto("http://localhost:3000")
    time.sleep(1)

    # Create 6-player game
    print("1. Creating 6-player game...")
    page.fill('input[placeholder="Enter your name"]', 'TestPlayer')

    # Select 6 players (5 AI)
    page.select_option('select', '5')  # 5 AI = 6 total players
    time.sleep(0.5)

    # Start game
    page.click('button:has-text("Start Game")')
    time.sleep(3)

    # Take screenshot of first hand
    page.screenshot(path="/tmp/fix01_blind_positions_hand1.png", full_page=True)
    print("📸 Screenshot saved: /tmp/fix01_blind_positions_hand1.png")

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

    # Get all visible player names/positions
    print("\n3. Player layout:")
    player_seats = page.locator('[class*="player"]').all()
    for i, seat in enumerate(player_seats[:10]):  # Limit to first 10
        if seat.is_visible():
            text = seat.text_content()
            if text:
                print(f"   Position {i}: {text[:100]}")

    # Fold to end hand quickly
    print("\n4. Completing hand 1...")
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
    page.screenshot(path="/tmp/fix01_blind_positions_hand2.png", full_page=True)
    print("📸 Screenshot saved: /tmp/fix01_blind_positions_hand2.png")

    print("\n=== VALIDATION COMPLETE ===")
    print("Review screenshots to confirm:")
    print("  - Are SB and BB adjacent (one position apart)?")
    print("  - Do blinds rotate clockwise each hand?")
    print("  - Is dealer button progression correct?")

    # Don't assert anything - this is just visual validation
    # User will review screenshots manually


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
