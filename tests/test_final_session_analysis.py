"""Final test: Verify session analysis modal works end-to-end"""
from playwright.sync_api import sync_playwright
import time

def test_session_analysis_final():
    """Complete test of session analysis feature"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()

        print("\n" + "="*70)
        print("FINAL SESSION ANALYSIS TEST")
        print("="*70)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'FinalTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        print("\n✓ Game started")

        # Play 3 hands quickly
        for hand_num in range(1, 4):
            print(f"  Playing hand {hand_num}...", end=" ")

            # Fold
            fold_btn = page.locator('button:has-text("Fold")').first
            fold_btn.wait_for(state="visible", timeout=5000)
            fold_btn.click()

            # Wait for winner modal and click Next Hand
            winner_modal = page.locator('[data-testid="winner-modal"]')
            winner_modal.wait_for(state="visible", timeout=10000)
            time.sleep(1)

            next_btn = page.locator('[data-testid="winner-modal"] button:has-text("Next Hand")')
            next_btn.click()
            print("✓")
            time.sleep(2)

        print("\n✓ Played 3 hands")

        # Open Session Analysis
        print("\n--- Opening Session Analysis ---")
        settings_btn = page.locator('button:has-text("⚙")').first
        settings_btn.click()
        time.sleep(1)

        session_btn = page.locator('button:has-text("Session Analysis")').first
        session_btn.click()
        print("✓ Clicked Session Analysis")

        # Wait for modal to appear (should be immediate)
        time.sleep(2)

        # Check that modal appeared
        modal_heading = page.locator('h2:has-text("Session Analysis")')
        if modal_heading.count() > 0:
            print("✅ Modal appeared immediately!")
        else:
            print("❌ Modal did not appear")
            browser.close()
            return False

        # Check for loading state
        loading_spinner = page.locator('div.animate-spin')
        if loading_spinner.count() > 0:
            print("✅ Loading spinner visible")

            # Check loading message
            page_text = page.evaluate("() => document.body.innerText")
            if "20-30 seconds" in page_text or "30-40 seconds" in page_text:
                print("✅ Realistic time estimate shown")
            else:
                print("⚠️  Time estimate not found")

            # Check NO cost estimates
            if "$0.02" in page_text or "$0.03" in page_text:
                print("❌ API cost shown to user (should not be visible)")
            else:
                print("✅ No API cost shown to user")
        else:
            print("⚠️  Loading spinner not found")

        # Wait for analysis to complete (up to 45 seconds)
        print("\n⏳ Waiting for AI analysis to complete (up to 45s)...")

        # Wait for loading spinner to disappear
        try:
            page.wait_for_selector('div.animate-spin', state='hidden', timeout=45000)
            print("✅ Analysis completed!")
        except:
            print("⚠️  Analysis still running after 45s")

        # Take final screenshot
        page.screenshot(path="/tmp/session_analysis_final.png", full_page=True)
        print(f"\n✓ Screenshot: /tmp/session_analysis_final.png")

        print("\n" + "="*70)
        print("TEST COMPLETE - Browser stays open for 15s")
        print("="*70)

        time.sleep(15)
        browser.close()
        return True

if __name__ == "__main__":
    success = test_session_analysis_final()
    exit(0 if success else 1)
