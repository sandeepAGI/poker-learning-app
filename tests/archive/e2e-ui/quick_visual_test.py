"""Quick visual test to verify blind positions are correct"""
import pytest
from playwright.sync_api import Page
import time


def test_quick_visual_check(page: Page):
    """Quick test to see current blind positions"""
    print("\n=== QUICK VISUAL CHECK ===")

    # Create 6-player game
    page.goto("http://localhost:3000")
    page.fill('input[placeholder="Enter your name"]', 'QuickTest')
    page.select_option('select', '5')  # 6 players
    page.click('button:has-text("Start Game")')
    time.sleep(3)

    # Take screenshot
    page.screenshot(path="/tmp/quick_visual_check.png", full_page=True)
    print("Screenshot saved: /tmp/quick_visual_check.png")

    # Count badges (for diagnostics only, not asserting)
    d_count = page.locator('text=/^D$/').count()
    sb_count = page.locator('text=/^SB$/').count()
    bb_count = page.locator('text=/^BB$/').count()

    print(f"Badges found: D={d_count}, SB={sb_count}, BB={bb_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
