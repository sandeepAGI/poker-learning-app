"""Diagnose layout issues - measure actual element positions and sizes"""
from playwright.sync_api import sync_playwright
import time

def diagnose_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("\n" + "="*80)
        print("LAYOUT DIAGNOSTIC TEST - DESKTOP (1920x1080)")
        print("="*80)

        # Start game
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', 'DiagTest')
        page.select_option('select', '3')
        page.click('button:has-text("Start Game")')
        time.sleep(2)

        # Get comprehensive layout measurements
        measurements = page.evaluate("""
            () => {
                const viewport = {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    visualHeight: window.visualViewport?.height || window.innerHeight
                };

                // Main container
                const mainContainer = document.querySelector('.flex.flex-col.h-screen');
                const mainRect = mainContainer?.getBoundingClientRect();

                // Table area (flex-1 relative)
                const tableArea = document.querySelector('.flex-1.relative');
                const tableRect = tableArea?.getBoundingClientRect();

                // Human player container
                const humanPlayer = document.querySelector('.absolute.bottom-44');
                const humanRect = humanPlayer?.getBoundingClientRect();

                // Action buttons container
                const actionButtons = document.querySelector('.absolute.bottom-4');
                const actionRect = actionButtons?.getBoundingClientRect();

                // PlayerSeat content
                const playerSeat = humanPlayer?.querySelector('.relative.p-2');
                const seatRect = playerSeat?.getBoundingClientRect();

                // Cards
                const cards = humanPlayer?.querySelectorAll('.bg-white');
                const cardRects = Array.from(cards || []).map(card => {
                    const r = card.getBoundingClientRect();
                    return {
                        width: r.width,
                        height: r.height,
                        top: r.top,
                        bottom: r.bottom,
                        visibleInViewport: r.bottom <= viewport.height && r.top >= 0
                    };
                });

                // Check computed styles
                const tableStyle = tableArea ? window.getComputedStyle(tableArea) : null;
                const humanStyle = humanPlayer ? window.getComputedStyle(humanPlayer) : null;

                return {
                    viewport,
                    mainContainer: mainRect ? {
                        height: mainRect.height,
                        top: mainRect.top,
                        bottom: mainRect.bottom
                    } : null,
                    tableArea: tableRect ? {
                        height: tableRect.height,
                        top: tableRect.top,
                        bottom: tableRect.bottom,
                        overflow: tableStyle?.overflow,
                        maxHeight: tableStyle?.maxHeight,
                        minHeight: tableStyle?.minHeight
                    } : null,
                    humanPlayer: humanRect ? {
                        height: humanRect.height,
                        top: humanRect.top,
                        bottom: humanRect.bottom,
                        distanceFromViewportBottom: viewport.height - humanRect.bottom,
                        bottomCSS: humanStyle?.bottom
                    } : null,
                    actionButtons: actionRect ? {
                        height: actionRect.height,
                        top: actionRect.top,
                        bottom: actionRect.bottom,
                        distanceFromViewportBottom: viewport.height - actionRect.bottom
                    } : null,
                    playerSeat: seatRect ? {
                        height: seatRect.height,
                        width: seatRect.width
                    } : null,
                    cards: cardRects,
                    gapBetweenHumanAndActions: humanRect && actionRect ?
                        (actionRect.top - humanRect.bottom) : null
                };
            }
        """)

        print("\n📐 VIEWPORT")
        print(f"  Size: {measurements['viewport']['width']}x{measurements['viewport']['height']}")

        if measurements['mainContainer']:
            print("\n📦 MAIN CONTAINER (h-screen)")
            print(f"  Height: {measurements['mainContainer']['height']}px")
            print(f"  Top: {measurements['mainContainer']['top']}px")
            print(f"  Bottom: {measurements['mainContainer']['bottom']}px")

        if measurements['tableArea']:
            print("\n🎲 TABLE AREA (flex-1 relative)")
            print(f"  Height: {measurements['tableArea']['height']}px")
            print(f"  Top: {measurements['tableArea']['top']}px")
            print(f"  Bottom: {measurements['tableArea']['bottom']}px")
            print(f"  Overflow: {measurements['tableArea']['overflow']}")
            print(f"  Max-height: {measurements['tableArea']['maxHeight']}")

        if measurements['humanPlayer']:
            print("\n👤 HUMAN PLAYER CONTAINER (absolute bottom-44)")
            print(f"  Height: {measurements['humanPlayer']['height']}px")
            print(f"  Top: {measurements['humanPlayer']['top']}px")
            print(f"  Bottom: {measurements['humanPlayer']['bottom']}px")
            print(f"  Distance from viewport bottom: {measurements['humanPlayer']['distanceFromViewportBottom']}px")
            print(f"  CSS bottom property: {measurements['humanPlayer']['bottomCSS']}")

        if measurements['playerSeat']:
            print("\n💺 PLAYER SEAT CONTENT")
            print(f"  Height: {measurements['playerSeat']['height']}px")
            print(f"  Width: {measurements['playerSeat']['width']}px")

        if measurements['cards']:
            print(f"\n🃏 CARDS ({len(measurements['cards'])} found)")
            for i, card in enumerate(measurements['cards']):
                status = "✅ VISIBLE" if card['visibleInViewport'] else "❌ CLIPPED"
                print(f"  Card {i}: {card['width']:.0f}x{card['height']:.0f}px")
                print(f"    Top: {card['top']:.0f}px, Bottom: {card['bottom']:.0f}px {status}")
                if card['bottom'] > measurements['viewport']['height']:
                    overflow = card['bottom'] - measurements['viewport']['height']
                    print(f"    ⚠️  OVERFLOWS VIEWPORT BY {overflow:.0f}px")

        if measurements['actionButtons']:
            print("\n🎮 ACTION BUTTONS (absolute bottom-4)")
            print(f"  Height: {measurements['actionButtons']['height']}px")
            print(f"  Top: {measurements['actionButtons']['top']}px")
            print(f"  Bottom: {measurements['actionButtons']['bottom']}px")
            print(f"  Distance from viewport bottom: {measurements['actionButtons']['distanceFromViewportBottom']}px")

        if measurements['gapBetweenHumanAndActions'] is not None:
            print("\n📏 SPACING")
            gap = measurements['gapBetweenHumanAndActions']
            if gap < 0:
                print(f"  ⚠️  OVERLAP: Human player and actions overlap by {abs(gap):.0f}px")
            else:
                print(f"  Gap between human player and actions: {gap:.0f}px")

        # Take screenshot
        screenshot_path = "/tmp/layout_diagnostic.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 Screenshot: {screenshot_path}")

        print("\n" + "="*80)
        input("Press ENTER to close browser and continue...")
        browser.close()

if __name__ == "__main__":
    diagnose_layout()
