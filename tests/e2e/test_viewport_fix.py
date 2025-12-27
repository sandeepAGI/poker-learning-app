"""Test viewport-relative fix (bottom-[20vh] instead of bottom-44)"""
from playwright.sync_api import sync_playwright
import time

def test_viewport_fix():
    viewports = [
        {"name": "Small Laptop", "width": 1280, "height": 720},
        {"name": "MacBook Air", "width": 1440, "height": 900},
        {"name": "MacBook Pro", "width": 1512, "height": 982},
        {"name": "Full HD", "width": 1920, "height": 1080},
        {"name": "Tall Monitor", "width": 1920, "height": 1200},
        {"name": "Large Monitor", "width": 2560, "height": 1440},
    ]

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)

        for vp in viewports:
            print(f"\n{'='*80}")
            print(f"TESTING FIX: {vp['name']} ({vp['width']}x{vp['height']})")
            print('='*80)

            context = browser.new_context(viewport={"width": vp['width'], "height": vp['height']})
            page = context.new_page()

            # Start game
            page.goto("http://localhost:3000")
            page.fill('input[placeholder="Enter your name"]', 'FixTest')
            page.select_option('select', '3')
            page.click('button:has-text("Start Game")')
            time.sleep(2)

            # Measure layout
            measurements = page.evaluate("""
                () => {
                    const viewport = {
                        width: window.innerWidth,
                        height: window.innerHeight
                    };

                    // Human player container (now using bottom-[20vh])
                    const humanContainer = document.querySelector('.absolute.bottom-\\[20vh\\]');
                    if (!humanContainer) {
                        return {error: 'Container not found - check if class name is correct'};
                    }

                    const containerRect = humanContainer.getBoundingClientRect();
                    const containerStyle = window.getComputedStyle(humanContainer);

                    // PlayerSeat content
                    const playerSeat = humanContainer.querySelector('.relative');
                    const seatRect = playerSeat?.getBoundingClientRect();

                    // Cards
                    const cards = humanContainer.querySelectorAll('.bg-white');
                    const cardData = Array.from(cards).map((card, i) => {
                        const r = card.getBoundingClientRect();
                        const topClipped = r.top < 0;
                        const bottomClipped = r.bottom > viewport.height;
                        const visibleHeight = Math.min(r.bottom, viewport.height) - Math.max(r.top, 0);
                        const percentVisible = (visibleHeight / r.height * 100);

                        return {
                            index: i,
                            top: Math.round(r.top),
                            bottom: Math.round(r.bottom),
                            height: Math.round(r.height),
                            topClipped,
                            bottomClipped,
                            percentVisible: Math.round(percentVisible)
                        };
                    });

                    // Calculate actual bottom distance
                    const actualBottomPx = viewport.height - containerRect.bottom;
                    const actualBottomPercent = (actualBottomPx / viewport.height * 100);
                    const expectedBottomPx = viewport.height * 0.20; // 20vh

                    return {
                        viewport,
                        container: {
                            top: Math.round(containerRect.top),
                            bottom: Math.round(containerRect.bottom),
                            height: Math.round(containerRect.height),
                            bottomPx: actualBottomPx,
                            bottomPercent: actualBottomPercent.toFixed(1),
                            expectedBottomPx: Math.round(expectedBottomPx),
                            bottomCSS: containerStyle.bottom
                        },
                        seat: seatRect ? {
                            height: Math.round(seatRect.height)
                        } : null,
                        cards: cardData
                    };
                }
            """)

            if 'error' in measurements:
                print(f"❌ ERROR: {measurements['error']}")
                results.append({'name': vp['name'], 'size': f"{vp['width']}x{vp['height']}", 'status': 'ERROR'})
                context.close()
                continue

            # Print results
            print(f"Viewport: {measurements['viewport']['width']}x{measurements['viewport']['height']}px")
            print(f"\nContainer positioning:")
            print(f"  Expected bottom: {measurements['container']['expectedBottomPx']}px (20% of {measurements['viewport']['height']}px)")
            print(f"  Actual bottom: {measurements['container']['bottomPx']:.1f}px ({measurements['container']['bottomPercent']}%)")
            print(f"  Container height: {measurements['container']['height']}px")
            if measurements['seat']:
                print(f"  PlayerSeat height: {measurements['seat']['height']}px")

                overflow = measurements['seat']['height'] - measurements['container']['height']
                if overflow > 0:
                    print(f"  ⚠️  Content overflow: {overflow}px")
                else:
                    print(f"  ✅ No overflow")

            # Check cards
            all_cards_visible = True
            print(f"\n🃏 Cards ({len(measurements['cards'])} found):")
            for card in measurements['cards']:
                if card['percentVisible'] < 100:
                    all_cards_visible = False
                    status = f"❌ Only {card['percentVisible']}% visible"
                    if card['bottomClipped']:
                        hidden = card['height'] * (100 - card['percentVisible']) / 100
                        status += f" ({hidden:.0f}px clipped at bottom)"
                    elif card['topClipped']:
                        hidden = card['height'] * (100 - card['percentVisible']) / 100
                        status += f" ({hidden:.0f}px clipped at top)"
                else:
                    status = "✅ Fully visible"

                print(f"  Card {card['index']}: {status}")
                print(f"    Position: top={card['top']}px, bottom={card['bottom']}px, height={card['height']}px")

            # Screenshot
            screenshot_path = f"/tmp/viewport_fix_{vp['name'].replace(' ', '_').lower()}.png"
            page.screenshot(path=screenshot_path)
            print(f"\n📸 Screenshot: {screenshot_path}")

            if all_cards_visible:
                print(f"\n✅ SUCCESS - All cards fully visible!")
                results.append({'name': vp['name'], 'size': f"{vp['width']}x{vp['height']}", 'status': 'PASS'})
            else:
                print(f"\n❌ ISSUE - Some cards clipped!")
                results.append({'name': vp['name'], 'size': f"{vp['width']}x{vp['height']}", 'status': 'FAIL'})

            context.close()
            time.sleep(1)

        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY - VIEWPORT FIX VERIFICATION")
        print('='*80)

        passed = [r for r in results if r['status'] == 'PASS']
        failed = [r for r in results if r['status'] == 'FAIL']

        for result in results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['name']} ({result['size']}) - {result['status']}")

        print(f"\n{'='*80}")
        if len(passed) == len(results):
            print(f"✅ ALL {len(results)} VIEWPORTS PASS - Fix successful!")
        else:
            print(f"⚠️  {len(passed)}/{len(results)} viewports pass")
            print(f"❌ {len(failed)} viewports still have issues")
        print('='*80)

        browser.close()

if __name__ == "__main__":
    test_viewport_fix()
