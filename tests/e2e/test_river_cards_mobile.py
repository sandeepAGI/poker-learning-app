"""Test 5 community cards (river) on mobile to see overflow/overlap"""
from playwright.sync_api import sync_playwright
import time

def test_river_mobile():
    """Test all 5 community cards on small screen"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={"width": 375, "height": 667})
        page = context.new_page()

        print("\n" + "="*70)
        print("RIVER CARDS ON MOBILE TEST (375px)")
        print("="*70)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'RiverTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        # Keep calling to get to river
        for round_num in range(4):  # preflop, flop, turn, river
            print(f"\nRound {round_num + 1}...")

            # Check if we have action buttons
            call_btn = page.locator('button:has-text("Call")').first
            if call_btn.count() > 0 and call_btn.is_visible():
                call_btn.click()
                print("  Called")
                time.sleep(2)
            else:
                print("  No action needed")

            # Check community cards count
            card_count = page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.flex.gap-3 > div > div.w-24');
                    return cards.length;
                }
            """)
            print(f"  Community cards: {card_count}")

            if card_count >= 5:
                print("  ✓ Reached river (5 cards)")
                break

        time.sleep(2)

        # Measure final state
        print("\n--- Measuring River State ---")
        measurements = page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.flex.gap-3 > div > div.w-24');
                const container = document.querySelector('.flex.gap-3');

                if (cards.length === 0) return { error: 'No cards' };

                const cardData = Array.from(cards).map((card, i) => {
                    const rect = card.getBoundingClientRect();
                    return {
                        index: i,
                        width: Math.round(rect.width),
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        visible: rect.left >= 0 && rect.right <= window.innerWidth
                    };
                });

                // Calculate gaps between cards
                const gaps = [];
                for (let i = 0; i < cardData.length - 1; i++) {
                    gaps.push({
                        between: `${i}-${i+1}`,
                        gap: cardData[i+1].left - cardData[i].right
                    });
                }

                const containerRect = container.getBoundingClientRect();

                return {
                    viewport: window.innerWidth,
                    cardCount: cards.length,
                    cards: cardData,
                    gaps: gaps,
                    container: {
                        width: Math.round(containerRect.width),
                        left: Math.round(containerRect.left),
                        right: Math.round(containerRect.right)
                    },
                    totalCardsWidth: cardData.reduce((sum, c) => sum + c.width, 0),
                    overflow: containerRect.width < cardData.reduce((sum, c) => sum + c.width, 0)
                };
            }
        """)

        if 'error' not in measurements:
            print(f"Viewport width: {measurements['viewport']}px")
            print(f"Container width: {measurements['container']['width']}px")
            print(f"Total cards width: {measurements['totalCardsWidth']}px")
            print(f"Number of cards: {measurements['cardCount']}")

            if measurements['overflow']:
                print(f"⚠️  OVERFLOW: Cards ({measurements['totalCardsWidth']}px) > Container ({measurements['container']['width']}px)")
                overflow_amount = measurements['totalCardsWidth'] - measurements['container']['width']
                print(f"   Overflow amount: {overflow_amount}px")

            print("\nCard visibility:")
            for card in measurements['cards']:
                status = "✅ Visible" if card['visible'] else "❌ Cut off/Hidden"
                print(f"  Card {card['index']}: {card['width']}px wide, left={card['left']}px, {status}")

            print("\nGaps between cards:")
            for gap in measurements['gaps']:
                gap_size = gap['gap']
                if gap_size < 0:
                    print(f"  Cards {gap['between']}: OVERLAP by {abs(gap_size)}px!")
                elif gap_size < 12:
                    print(f"  Cards {gap['between']}: {gap_size}px gap (expected 12px)")
                else:
                    print(f"  Cards {gap['between']}: {gap_size}px gap ✅")

        # Take screenshot
        page.screenshot(path="/tmp/river_mobile_375px.png", full_page=True)
        print(f"\n✓ Screenshot: /tmp/river_mobile_375px.png")

        print("\n" + "="*70)
        print("Browser stays open for 15 seconds for inspection...")
        print("="*70)

        time.sleep(15)
        browser.close()

if __name__ == "__main__":
    test_river_mobile()
