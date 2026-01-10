"""
Diagnostic test to understand why action buttons don't appear after clicking "Next Hand"

This test will:
1. Play one hand to completion
2. Click "Next Hand"
3. Monitor state updates via console logs
4. Check what state the UI is in when buttons should appear
"""
import pytest
import time
from playwright.sync_api import sync_playwright, Page
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


@pytest.fixture(scope="function")
def browser_page():
    """Fixture to create a browser page for each test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})

        # Enable console logging
        page = context.new_page()

        # Capture console logs
        def log_console(msg):
            print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}")

        page.on("console", log_console)

        yield page
        page.close()
        context.close()
        browser.close()


def create_game(page: Page) -> None:
    """Helper: Navigate to app and create a new game."""
    page.goto(FRONTEND_URL)
    page.wait_for_load_state("networkidle")

    # Click Start Game button
    page.click("button:has-text('Start Game')")

    # Wait for poker table to load
    page.wait_for_selector("text=Pot:", timeout=10000)
    time.sleep(2)  # Allow animations


def test_next_hand_state_diagnosis(browser_page):
    """
    Diagnostic test: Monitor exact state after clicking Next Hand
    """
    page = browser_page

    # Create game
    create_game(page)
    print("\n[TEST] Game created successfully")

    # Play first hand to completion by calling
    print("[TEST] Playing first hand...")
    page.click("button:has-text('Call')")

    # Wait for hand to complete (Next Hand button appears)
    max_wait = 60  # seconds
    start = time.time()
    while time.time() - start < max_wait:
        try:
            page.wait_for_selector("text=Next Hand", timeout=2000)
            print("[TEST] First hand completed!")
            break
        except:
            # Keep clicking Call if it appears (multi-street hand)
            try:
                if page.locator("button:has-text('Call')").is_visible(timeout=500):
                    page.click("button:has-text('Call')")
                    print("[TEST] Called again (next street)")
                    time.sleep(1)
            except:
                pass

    # Take screenshot before clicking Next Hand
    page.screenshot(path="/tmp/e2e-screenshots/diagnosis-before-next-hand.png")

    # Get body text before next hand
    text_before = page.inner_text("body")
    print(f"\n[TEST] State before Next Hand:")
    print(f"  - Has 'Next Hand' button: {'Next Hand' in text_before}")
    print(f"  - Has 'Quit' button: {'Quit' in text_before}")
    print(f"  - State keyword: {[x for x in ['PRE_FLOP', 'FLOP', 'TURN', 'RIVER', 'SHOWDOWN'] if x in text_before]}")

    time.sleep(2)

    # Click Next Hand using JavaScript (same as flaky tests)
    print("\n[TEST] Clicking 'Next Hand' button...")
    page.evaluate("""
        () => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const nextButton = buttons.find(b => b.textContent.includes('Next Hand'));
            if (nextButton) {
                console.log('[NEXT HAND CLICK] Found and clicking Next Hand button');
                nextButton.click();
            } else {
                console.log('[NEXT HAND CLICK] ERROR: Next Hand button not found!');
            }
        }
    """)

    # Wait and monitor state changes
    print("[TEST] Waiting 3 seconds after Next Hand click...")
    time.sleep(3)

    # Take screenshot after waiting
    page.screenshot(path="/tmp/e2e-screenshots/diagnosis-after-3sec-wait.png")

    # Get current state
    text_after_3s = page.inner_text("body")
    print(f"\n[TEST] State after 3 seconds:")
    print(f"  - Has 'Fold' button: {'Fold' in text_after_3s}")
    print(f"  - Has 'Call' button: {'Call' in text_after_3s}")
    print(f"  - Has 'Raise' button: {'Raise' in text_after_3s}")
    print(f"  - State keyword: {[x for x in ['PRE_FLOP', 'FLOP', 'TURN', 'RIVER', 'SHOWDOWN'] if x in text_after_3s]}")
    print(f"  - Has 'Next Hand': {'Next Hand' in text_after_3s}")

    # Try to extract game state info using JavaScript
    state_info = page.evaluate("""
        () => {
            const bodyText = document.body.innerText;

            // Try to find visible buttons
            const buttons = Array.from(document.querySelectorAll('button'))
                .filter(b => b.offsetParent !== null)  // Only visible buttons
                .map(b => b.textContent?.trim())
                .filter(t => t && t.length > 0);

            return {
                allText: bodyText.slice(0, 500),  // First 500 chars
                visibleButtons: buttons,
                hasCallButton: buttons.some(b => b.includes('Call')),
                hasFoldButton: buttons.some(b => b.includes('Fold')),
                hasRaiseButton: buttons.some(b => b.includes('Raise')),
            };
        }
    """)

    print(f"\n[TEST] JavaScript state extraction:")
    print(f"  - Visible buttons: {state_info['visibleButtons']}")
    print(f"  - Has Call: {state_info['hasCallButton']}")
    print(f"  - Has Fold: {state_info['hasFoldButton']}")
    print(f"  - Has Raise: {state_info['hasRaiseButton']}")

    # Now try waiting for action buttons with detailed logging
    print("\n[TEST] Attempting to wait for action buttons (15s timeout)...")
    try:
        page.wait_for_selector("button:has-text('Fold'), button:has-text('Call'), button:has-text('Raise')", timeout=15000)
        print("[TEST] ✓ Action buttons appeared!")
        page.screenshot(path="/tmp/e2e-screenshots/diagnosis-buttons-appeared.png")
    except Exception as e:
        print(f"[TEST] ✗ Action buttons did NOT appear: {e}")
        page.screenshot(path="/tmp/e2e-screenshots/diagnosis-buttons-failed.png")

        # Get final state for debugging
        final_text = page.inner_text("body")
        print(f"\n[TEST] Final state (excerpt):")
        print(final_text[:1000])

        raise
