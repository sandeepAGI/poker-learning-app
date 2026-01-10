"""Interactive Playwright test - watch what happens in real browser"""
from playwright.sync_api import sync_playwright
import time
import requests

def test_session_analysis_interactive():
    """Test session analysis with visible browser"""
    with sync_playwright() as p:
        # Launch browser in headed mode (visible)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        print("\n" + "="*60)
        print("INTERACTIVE SESSION ANALYSIS TEST")
        print("="*60)

        # Navigate to app
        page.goto("http://localhost:3000")
        print("\n✓ Opened app")

        # Start game
        page.fill('input[placeholder="Enter your name"]', 'InteractiveTest')
        page.select_option('select', '3')  # 4 players
        page.click('button:has-text("Start Game")')
        time.sleep(2)
        print("✓ Started game")

        # Get game ID
        game_id = page.evaluate("() => localStorage.getItem('poker_game_id')")
        print(f"✓ Game ID: {game_id}")

        # Play 3 hands
        for hand_num in range(1, 4):
            print(f"\n--- Hand {hand_num} ---")

            # Wait for Fold button and click
            try:
                fold_btn = page.locator('button:has-text("Fold")').first
                fold_btn.wait_for(state="visible", timeout=5000)
                print(f"  ✓ Fold button visible")
                fold_btn.click()
                print(f"  ✓ Clicked Fold")
                time.sleep(2)  # Wait for AI to finish

                # Check if SHOWDOWN state reached
                state = page.evaluate("() => document.body.textContent")
                if "Next Hand" in state or hand_num == 3:
                    print(f"  ✓ Hand completed")

                # Start next hand if not last
                if hand_num < 3:
                    next_btn = page.locator('button:has-text("Next Hand")').first
                    next_btn.wait_for(state="visible", timeout=8000)
                    print(f"  ✓ Next Hand button visible")
                    next_btn.click()
                    print(f"  ✓ Clicked Next Hand")
                    time.sleep(2)
            except Exception as e:
                print(f"  ❌ Error: {e}")
                break

        # Check hand history via API
        print(f"\n--- Checking Backend ---")
        r = requests.get(f"http://localhost:8000/games/{game_id}/history")
        if r.status_code == 200:
            total = r.json().get('total_hands', 0)
            print(f"✓ API: {total} hands in history")
        else:
            print(f"❌ API error: {r.status_code}")

        # Now try Session Analysis via UI
        print(f"\n--- Testing Session Analysis UI ---")

        # Click settings
        settings_btn = page.locator('button:has-text("⚙")').first
        settings_btn.click()
        time.sleep(1)
        print("✓ Opened settings")

        # Click Session Analysis
        session_btn = page.locator('button:has-text("Session Analysis")').first
        session_btn.click()
        time.sleep(3)
        print("✓ Clicked Session Analysis")

        # Check modal content
        modal = page.locator('[role="dialog"]')
        if modal.count() > 0:
            modal_text = modal.first.text_content()
            print(f"\n--- Modal Content ---")

            if 'No hands to analyze' in modal_text:
                print(f"❌ Modal shows: 'No hands to analyze'")
            elif 'Analysis Failed' in modal_text:
                print(f"❌ Modal shows: 'Analysis Failed'")
                print(f"   Message: {modal_text[:200]}")
            elif 'Session Analysis' in modal_text:
                print(f"✅ Modal shows Session Analysis!")
                print(f"   Preview: {modal_text[:300]}")
            else:
                print(f"⚠️  Unknown modal state")
                print(f"   Text: {modal_text[:200]}")
        else:
            print(f"❌ No modal found!")

        # Take screenshot
        page.screenshot(path="/tmp/session_analysis_test.png", full_page=True)
        print(f"\n✓ Screenshot saved: /tmp/session_analysis_test.png")

        print(f"\n" + "="*60)
        print("Browser will stay open for 30 seconds...")
        print("Check the browser and backend logs")
        print("="*60)

        # Keep browser open for inspection
        time.sleep(30)

        browser.close()

if __name__ == "__main__":
    test_session_analysis_interactive()
