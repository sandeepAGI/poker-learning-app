"""Diagnose layout at FLOP state (like user's screenshots)"""
from playwright.sync_api import sync_playwright
import time

def diagnose_at_flop():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("\n" + "="*80)
        print("DIAGNOSING AT FLOP STATE (matching user's screenshot)")
        print("="*80)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'DiagTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        # Get to FLOP by calling/checking
        try:
            call_btn = page.locator('button:has-text("Call")').first
            if call_btn.is_visible():
                call_btn.click()
                time.sleep(3)  # Wait for AI actions and flop
        except:
            pass

        # Get measurements at FLOP
        measurements = page.evaluate("""
            () => {
                // Find human player container
                const humanPlayer = document.querySelector('.absolute.bottom-44');
                if (!humanPlayer) return {error: 'Human player container not found'};

                const humanRect = humanPlayer.getBoundingClientRect();

                // Get all cards in human player
                const cards = humanPlayer.querySelectorAll('.bg-white');
                const cardInfo = Array.from(cards).map((card, i) => {
                    const r = card.getBoundingClientRect();
                    return {
                        index: i,
                        top: Math.round(r.top),
                        bottom: Math.round(r.bottom),
                        height: Math.round(r.height),
                        clippedTop: r.top < 0,
                        clippedBottom: r.bottom > window.innerHeight,
                        partiallyVisible: (r.top < 0 && r.bottom > 0) || (r.top < window.innerHeight && r.bottom > window.innerHeight)
                    };
                });

                // Check container
                const containerStyle = window.getComputedStyle(humanPlayer);

                return {
                    viewport: {height: window.innerHeight, width: window.innerWidth},
                    containerBottom: Math.round(humanRect.bottom),
                    containerHeight: Math.round(humanRect.height),
                    containerOverflow: containerStyle.overflow,
                    containerPosition: containerStyle.position,
                    containerBottomCSS: containerStyle.bottom,
                    cards: cardInfo,
                    gameState: document.querySelector('.text-xl.sm\\:text-2xl.font-bold')?.nextElementSibling?.textContent
                };
            }
        """)

        if 'error' in measurements:
            print(f"❌ {measurements['error']}")
        else:
            print(f"\n🎮 Game State: {measurements.get('gameState', 'Unknown')}")
            print(f"\n📐 Viewport: {measurements['viewport']['width']}x{measurements['viewport']['height']}")
            print(f"\n👤 Human Player Container:")
            print(f"  Bottom edge: {measurements['containerBottom']}px")
            print(f"  Height: {measurements['containerHeight']}px")
            print(f"  CSS bottom: {measurements['containerBottomCSS']}")
            print(f"  Overflow: {measurements['containerOverflow']}")

            print(f"\n🃏 Cards ({len(measurements['cards'])} found):")
            for card in measurements['cards']:
                print(f"  Card {card['index']}:")
                print(f"    Top: {card['top']}px, Bottom: {card['bottom']}px, Height: {card['height']}px")
                if card['clippedBottom']:
                    overflow = card['bottom'] - measurements['viewport']['height']
                    print(f"    ❌ CLIPPED AT BOTTOM - extends {overflow}px below viewport!")
                elif card['clippedTop']:
                    print(f"    ❌ CLIPPED AT TOP")
                elif card['partiallyVisible']:
                    print(f"    ⚠️  PARTIALLY VISIBLE")
                else:
                    print(f"    ✅ FULLY VISIBLE")

        # Take screenshot
        screenshot_path = "/tmp/layout_diagnostic_flop.png"
        page.screenshot(path=screenshot_path)
        print(f"\n📸 Screenshot: {screenshot_path}")

        print("\n" + "="*80)
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    diagnose_at_flop()
