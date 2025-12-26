"""Test responsive design at different viewport sizes"""
from playwright.sync_api import sync_playwright
import time

def test_responsive_scaling():
    """Test UI at different screen sizes to identify scaling issues"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()

        print("\n" + "="*70)
        print("RESPONSIVE DESIGN TEST")
        print("="*70)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'ResponsiveTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        print("\n✓ Game started")

        # Play to flop to get community cards
        fold_btn = page.locator('button:has-text("Fold")').first
        fold_btn.wait_for(state="visible", timeout=5000)
        fold_btn.click()
        time.sleep(1)

        # Click continue through winner modal
        winner_modal = page.locator('[data-testid="winner-modal"]')
        winner_modal.wait_for(state="visible", timeout=10000)
        next_btn = page.locator('[data-testid="winner-modal"] button:has-text("Next Hand")')
        next_btn.click()
        time.sleep(2)

        # Call to see flop
        call_btn = page.locator('button:has-text("Call")').first
        if call_btn.count() > 0:
            call_btn.click()
            time.sleep(2)

        # Test different viewport sizes
        viewports = [
            {"name": "Desktop", "width": 1920, "height": 1080},
            {"name": "Laptop", "width": 1366, "height": 768},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Mobile Large", "width": 414, "height": 896},
            {"name": "Mobile Small", "width": 375, "height": 667},
        ]

        for vp in viewports:
            print(f"\n--- Testing {vp['name']}: {vp['width']}x{vp['height']} ---")

            # Resize viewport
            page.set_viewport_size({"width": vp['width'], "height": vp['height']})
            time.sleep(1)

            # Take screenshot
            screenshot_path = f"/tmp/responsive_{vp['name'].lower().replace(' ', '_')}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✓ Screenshot: {screenshot_path}")

            # Check for overflow
            overflow_check = page.evaluate("""
                () => {
                    // Check if community cards overflow container
                    const communityCards = document.querySelector('div:has(> div.flex.gap-3)');
                    if (communityCards) {
                        const rect = communityCards.getBoundingClientRect();
                        const overflow = rect.width > window.innerWidth;
                        return {
                            width: rect.width,
                            viewportWidth: window.innerWidth,
                            overflow: overflow
                        };
                    }
                    return null;
                }
            """)

            if overflow_check:
                print(f"  Community cards width: {overflow_check['width']}px")
                print(f"  Viewport width: {overflow_check['viewportWidth']}px")
                if overflow_check['overflow']:
                    print(f"  ⚠️  OVERFLOW DETECTED!")
                else:
                    print(f"  ✅ No overflow")

        print("\n" + "="*70)
        print("Browser stays open for 10 seconds...")
        print("="*70)

        time.sleep(10)
        browser.close()

if __name__ == "__main__":
    test_responsive_scaling()
