"""Test layout at various realistic viewport sizes (desktop, laptop, etc.)"""
from playwright.sync_api import sync_playwright
import time

def test_multiple_viewport_sizes():
    """Test the EXACT issue user is reporting - cards cut off at different sizes"""

    # Realistic viewport sizes for desktop/laptop
    viewports = [
        {"name": "MacBook Air 13", "width": 1440, "height": 900},
        {"name": "MacBook Pro 14", "width": 1512, "height": 982},
        {"name": "MacBook Pro 16", "width": 1728, "height": 1117},
        {"name": "iMac 24", "width": 1920, "height": 1080},
        {"name": "Full HD Monitor", "width": 1920, "height": 1080},
        {"name": "Tall Monitor", "width": 1920, "height": 1200},
        {"name": "Small Laptop", "width": 1280, "height": 720},
        {"name": "Large Monitor", "width": 2560, "height": 1440},
    ]

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)

        for vp in viewports:
            print(f"\n{'='*80}")
            print(f"TESTING: {vp['name']} ({vp['width']}x{vp['height']})")
            print('='*80)

            context = browser.new_context(viewport={"width": vp['width'], "height": vp['height']})
            page = context.new_page()

            # Start game
            page.goto("http://localhost:3000")
            page.fill('input[placeholder="Enter your name"]', 'Test')
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

                    // Human player container
                    const humanContainer = document.querySelector('.absolute.bottom-44');
                    const containerRect = humanContainer?.getBoundingClientRect();

                    // PlayerSeat content
                    const playerSeat = humanContainer?.querySelector('.relative.p-2, .relative.p-3, .relative.p-4');
                    const seatRect = playerSeat?.getBoundingClientRect();

                    // Cards
                    const cards = humanContainer?.querySelectorAll('.bg-white');
                    const cardData = Array.from(cards || []).map(card => {
                        const r = card.getBoundingClientRect();
                        return {
                            top: Math.round(r.top),
                            bottom: Math.round(r.bottom),
                            height: Math.round(r.height),
                            visibleHeight: Math.min(r.bottom, viewport.height) - Math.max(r.top, 0),
                            percentVisible: ((Math.min(r.bottom, viewport.height) - Math.max(r.top, 0)) / r.height * 100)
                        };
                    });

                    // Action buttons
                    const actionButtons = document.querySelector('.absolute.bottom-4');
                    const actionRect = actionButtons?.getBoundingClientRect();

                    return {
                        viewport,
                        container: containerRect ? {
                            top: Math.round(containerRect.top),
                            bottom: Math.round(containerRect.bottom),
                            height: Math.round(containerRect.height),
                            bottomPx: Math.round(viewport.height - containerRect.bottom)
                        } : null,
                        seat: seatRect ? {
                            height: Math.round(seatRect.height)
                        } : null,
                        cards: cardData,
                        actions: actionRect ? {
                            top: Math.round(actionRect.top),
                            height: Math.round(actionRect.height)
                        } : null,
                        overflow: containerRect && seatRect ?
                            Math.max(0, seatRect.height - containerRect.height) : null
                    };
                }
            """)

            # Analyze results
            issue_found = False
            issue_details = []

            if measurements['cards']:
                for i, card in enumerate(measurements['cards']):
                    if card['percentVisible'] < 100:
                        issue_found = True
                        visible = card['percentVisible']
                        issue_details.append(f"Card {i}: Only {visible:.0f}% visible (bottom clipped)")

            if measurements['overflow'] and measurements['overflow'] > 0:
                issue_found = True
                issue_details.append(f"PlayerSeat overflow: {measurements['overflow']}px taller than container")

            # Print results
            print(f"Container bottom: {measurements['container']['bottomPx']}px from viewport bottom")
            print(f"Container height: {measurements['container']['height']}px")
            print(f"PlayerSeat height: {measurements['seat']['height']}px")

            if measurements['overflow']:
                if measurements['overflow'] > 0:
                    print(f"⚠️  OVERFLOW: PlayerSeat is {measurements['overflow']}px taller than container")
                else:
                    print(f"✅ No overflow")

            print(f"\n🃏 Cards ({len(measurements['cards'])} found):")
            for i, card in enumerate(measurements['cards']):
                status = "✅" if card['percentVisible'] == 100 else "❌"
                print(f"  Card {i}: {card['percentVisible']:.0f}% visible {status}")
                if card['percentVisible'] < 100:
                    hidden = card['height'] - card['visibleHeight']
                    print(f"    ⚠️  {hidden}px clipped at bottom!")

            if issue_found:
                print(f"\n❌ ISSUE FOUND:")
                for detail in issue_details:
                    print(f"   {detail}")
            else:
                print(f"\n✅ NO ISSUES - All cards fully visible")

            # Screenshot
            screenshot_path = f"/tmp/viewport_{vp['name'].replace(' ', '_').lower()}.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot: {screenshot_path}")

            results.append({
                'name': vp['name'],
                'size': f"{vp['width']}x{vp['height']}",
                'issue': issue_found,
                'details': issue_details
            })

            context.close()
            time.sleep(1)

        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY - VIEWPORT SIZE TESTING")
        print('='*80)

        issues_found = [r for r in results if r['issue']]

        for result in results:
            status = "❌" if result['issue'] else "✅"
            print(f"{status} {result['name']} ({result['size']})")
            if result['issue']:
                for detail in result['details']:
                    print(f"     {detail}")

        print(f"\n{'='*80}")
        if issues_found:
            print(f"❌ ISSUES FOUND on {len(issues_found)}/{len(results)} viewport sizes")
            print(f"\n💡 ROOT CAUSE: Fixed 'bottom-44' (176px) doesn't scale with viewport height")
            print(f"   As viewport gets taller, container stays 176px from bottom,")
            print(f"   but PlayerSeat content grows, causing overflow and clipping.")
        else:
            print(f"✅ ALL VIEWPORTS OK - No clipping detected")
        print('='*80)

        browser.close()

if __name__ == "__main__":
    test_multiple_viewport_sizes()
