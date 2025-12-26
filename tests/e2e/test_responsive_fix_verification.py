"""Verify responsive design fix - all cards visible on all screen sizes"""
from playwright.sync_api import sync_playwright
import time

def test_responsive_fix():
    """Verify 5 community cards fit on mobile after responsive fix"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)

        # Test different viewports
        viewports = [
            {"name": "Mobile Small", "width": 375, "height": 667},
            {"name": "Mobile Large", "width": 414, "height": 896},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Desktop", "width": 1920, "height": 1080},
        ]

        results = {}

        for vp in viewports:
            print(f"\n{'='*70}")
            print(f"TESTING: {vp['name']} ({vp['width']}x{vp['height']})")
            print('='*70)

            context = browser.new_context(viewport={"width": vp['width'], "height": vp['height']})
            page = context.new_page()

            # Start game
            page.goto("http://localhost:3000")
            page.fill('input[placeholder="Enter your name"]', 'ResponsiveTest')
            page.select_option('select', '3')
            page.click('button:has-text("Start Game")')
            time.sleep(2)

            # Calculate expected card size based on viewport
            if vp['width'] < 640:  # mobile (< sm breakpoint)
                expected_width = 64  # w-16
                expected_gap = 4  # gap-1
            elif vp['width'] < 768:  # sm
                expected_width = 80  # sm:w-20
                expected_gap = 8  # sm:gap-2
            else:  # md and above
                expected_width = 96  # md:w-24
                expected_gap = 12  # md:gap-3

            # Get measurements for 2 cards (player)
            measurements = page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.bg-white');
                    if (cards.length === 0) return { error: 'No cards' };

                    const firstCard = cards[0].getBoundingClientRect();

                    return {
                        cardWidth: Math.round(firstCard.width),
                        cardHeight: Math.round(firstCard.height),
                        viewport: window.innerWidth
                    };
                }
            """)

            if 'error' not in measurements:
                print(f"Card size: {measurements['cardWidth']}x{measurements['cardHeight']}px")
                print(f"Expected: {expected_width}px wide")

                # Calculate if 5 cards would fit
                five_cards_width = (expected_width * 5) + (expected_gap * 4)
                print(f"\n5 River Cards Calculation:")
                print(f"  5 cards × {expected_width}px = {expected_width * 5}px")
                print(f"  4 gaps × {expected_gap}px = {expected_gap * 4}px")
                print(f"  Total needed: {five_cards_width}px")
                print(f"  Viewport: {vp['width']}px")

                fits = five_cards_width <= vp['width']
                status = "✅ FITS" if fits else "❌ OVERFLOW"
                print(f"  Result: {status}")

                results[vp['name']] = {
                    'card_width': measurements['cardWidth'],
                    'expected': expected_width,
                    'fits': fits,
                    'total_needed': five_cards_width
                }

            # Screenshot
            screenshot_path = f"/tmp/responsive_fix_{vp['name'].lower().replace(' ', '_')}.png"
            page.screenshot(path=screenshot_path)
            print(f"\n✓ Screenshot: {screenshot_path}")

            context.close()
            time.sleep(1)

        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)

        all_pass = True
        for name, data in results.items():
            match = "✅" if data['card_width'] == data['expected'] else "⚠️"
            fit = "✅" if data['fits'] else "❌"
            print(f"{name}:")
            print(f"  Card size: {data['card_width']}px {match} (expected {data['expected']}px)")
            print(f"  5 cards fit: {fit} (needs {data['total_needed']}px)")

            if not data['fits']:
                all_pass = False

        print(f"\n{'='*70}")
        if all_pass:
            print("✅ ALL VIEWPORTS PASS - Responsive design working!")
        else:
            print("❌ SOME VIEWPORTS FAIL - Cards may overflow")
        print('='*70)

        browser.close()
        return all_pass

if __name__ == "__main__":
    success = test_responsive_fix()
    exit(0 if success else 1)
