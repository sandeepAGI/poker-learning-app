"""Test individual card sizing at different viewports"""
from playwright.sync_api import sync_playwright
import time

def test_card_dimensions():
    """Measure actual card dimensions at different screen sizes"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()

        print("\n" + "="*70)
        print("CARD SIZING TEST")
        print("="*70)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'CardTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        # Play to get community cards
        fold_btn = page.locator('button:has-text("Fold")').first
        fold_btn.wait_for(state="visible", timeout=5000)
        fold_btn.click()
        time.sleep(1)

        winner_modal = page.locator('[data-testid="winner-modal"]')
        winner_modal.wait_for(state="visible", timeout=10000)
        next_btn = page.locator('[data-testid="winner-modal"] button:has-text("Next Hand")')
        next_btn.click()
        time.sleep(2)

        # Call to see flop
        call_btn = page.locator('button:has-text("Call")').first
        if call_btn.count() > 0:
            call_btn.click()
            time.sleep(3)

        # Test at different viewport sizes
        viewports = [
            {"name": "Desktop", "width": 1920, "height": 1080},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Mobile", "width": 375, "height": 667},
        ]

        for vp in viewports:
            print(f"\n--- {vp['name']}: {vp['width']}x{vp['height']} ---")

            page.set_viewport_size({"width": vp['width'], "height": vp['height']})
            time.sleep(1)

            # Measure card sizes
            measurements = page.evaluate("""
                () => {
                    // Find all community cards (now responsive, look for card containers)
                    const cards = document.querySelectorAll('.flex[class*="gap-"] > div > div.bg-white');

                    if (cards.length === 0) return { error: 'No cards found' };

                    const cardSizes = Array.from(cards).map((card, i) => {
                        const rect = card.getBoundingClientRect();
                        return {
                            index: i,
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            left: Math.round(rect.left),
                            right: Math.round(rect.right)
                        };
                    });

                    // Check for overlap
                    let overlaps = [];
                    for (let i = 0; i < cardSizes.length - 1; i++) {
                        const gap = cardSizes[i + 1].left - cardSizes[i].right;
                        if (gap < 0) {
                            overlaps.push({
                                cards: `${i} and ${i+1}`,
                                overlap: Math.abs(gap)
                            });
                        }
                    }

                    // Get container info (now has responsive gaps)
                    const container = document.querySelector('.flex[class*="gap-"]');
                    const containerRect = container ? container.getBoundingClientRect() : null;

                    return {
                        cards: cardSizes,
                        overlaps: overlaps,
                        container: containerRect ? {
                            width: Math.round(containerRect.width),
                            totalCardsWidth: cardSizes.reduce((sum, c) => sum + c.width, 0)
                        } : null
                    };
                }
            """)

            if 'error' in measurements:
                print(f"  {measurements['error']}")
                continue

            print(f"  Container width: {measurements['container']['width']}px")
            print(f"  Total cards width: {measurements['container']['totalCardsWidth']}px")
            print(f"  Number of cards: {len(measurements['cards'])}")

            if len(measurements['cards']) > 0:
                card_width = measurements['cards'][0]['width']
                card_height = measurements['cards'][0]['height']
                print(f"  Individual card size: {card_width}x{card_height}px")
                print(f"  Expected (w-24 h-32): 96x128px")

                if card_width != 96 or card_height != 128:
                    print(f"  ⚠️  Cards are being scaled! ({card_width}px vs 96px expected)")

            if measurements['overlaps']:
                print(f"  ⚠️  OVERLAPS DETECTED:")
                for overlap in measurements['overlaps']:
                    print(f"     Cards {overlap['cards']}: {overlap['overlap']}px overlap")
            else:
                print(f"  ✅ No card overlaps")

            # Take screenshot
            screenshot_path = f"/tmp/card_sizing_{vp['name'].lower()}.png"
            page.screenshot(path=screenshot_path)
            print(f"  Screenshot: {screenshot_path}")

        print("\n" + "="*70)
        print("Browser stays open for 10 seconds...")
        print("="*70)

        time.sleep(10)
        browser.close()

if __name__ == "__main__":
    test_card_dimensions()
