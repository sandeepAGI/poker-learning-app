"""
Comprehensive E2E Test Suite for Phase 4.5 Fixes

Tests FIX-01, FIX-02, FIX-03, and FIX-04 (viewport scaling)
Covers multiple viewport sizes, all game states, and both 4/6 player games

CRITICAL REQUIREMENTS:
- Test MULTIPLE viewport sizes (1280x720, 1440x900, 1920x1080, 1920x1200)
- Test ALL game states (PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN)
- Test 4-player AND 6-player games
- Verify NO regressions in FIX-01, FIX-02, FIX-03
"""

import pytest
import time
from playwright.sync_api import sync_playwright, Page, expect


# Viewport configurations to test
VIEWPORTS = [
    {"name": "Small Laptop", "width": 1280, "height": 720},
    {"name": "Standard Laptop", "width": 1440, "height": 900},
    {"name": "Desktop FHD", "width": 1920, "height": 1080},
    {"name": "Desktop WUXGA", "width": 1920, "height": 1200},
]

# Game states to test
GAME_STATES = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]

# Player counts to test
PLAYER_COUNTS = [4, 6]


class TestPhase45Comprehensive:
    """Comprehensive regression and validation tests for Phase 4.5"""

    @pytest.fixture(scope="class")
    def browser(self):
        """Launch browser once for all tests"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            yield browser
            browser.close()

    def start_game(self, page: Page, player_name: str, num_players: int):
        """Start a new game with specified player count"""
        page.goto("http://localhost:3000")
        page.fill('input[placeholder="Enter your name"]', player_name)
        # Convert total players to AI count (frontend uses AI count as option values)
        ai_count = num_players - 1  # 4 players = 3 AI, 6 players = 5 AI
        page.select_option('select', str(ai_count))
        page.click('button:has-text("Start Game")')
        time.sleep(2)  # Wait for game to initialize

    def advance_to_state(self, page: Page, target_state: str):
        """Advance game to target state by clicking AI actions"""
        max_attempts = 30
        attempts = 0

        while attempts < max_attempts:
            # Check current state from the game state display
            # The state is shown as "Game State: PRE_FLOP" (etc) in the header
            current_state = page.evaluate("""
                () => {
                    // Find text containing "Game State:"
                    const stateSpan = Array.from(document.querySelectorAll('span'))
                        .find(el => el.textContent && el.textContent.includes('Game State:'));
                    if (stateSpan) {
                        return stateSpan.textContent.replace('Game State: ', '').trim();
                    }
                    return '';
                }
            """)

            if current_state == target_state:
                time.sleep(1)  # Let UI settle
                return True

            # Check if game ended early
            if page.locator('button:has-text("Next Hand")').is_visible():
                # Game ended before reaching target state
                return False

            # Wait for AI actions to complete
            time.sleep(0.8)
            attempts += 1

        return False

    def check_human_cards_visible(self, page: Page) -> dict:
        """Check if human player cards are fully visible"""
        result = page.evaluate("""
            () => {
                // Find human player container (absolute bottom positioning)
                const containers = Array.from(document.querySelectorAll('.absolute'));
                const humanContainer = containers.find(el => {
                    const style = window.getComputedStyle(el);
                    return style.position === 'absolute' &&
                           (style.bottom.includes('px') || style.bottom.includes('vh'));
                });

                if (!humanContainer) {
                    return {error: 'Human player container not found'};
                }

                // Find all cards in human player container
                const cards = humanContainer.querySelectorAll('.bg-white');
                if (cards.length === 0) {
                    return {error: 'No cards found in human player container'};
                }

                const viewport = {
                    width: window.innerWidth,
                    height: window.innerHeight
                };

                const containerRect = humanContainer.getBoundingClientRect();

                const cardInfo = Array.from(cards).map(card => {
                    const rect = card.getBoundingClientRect();
                    return {
                        top: Math.round(rect.top),
                        bottom: Math.round(rect.bottom),
                        height: Math.round(rect.height),
                        visible: rect.bottom <= viewport.height && rect.top >= 0,
                        percentVisible: rect.bottom > viewport.height
                            ? Math.round((viewport.height - rect.top) / rect.height * 100)
                            : 100
                    };
                });

                return {
                    viewport: viewport,
                    container: {
                        top: Math.round(containerRect.top),
                        bottom: Math.round(containerRect.bottom),
                        height: Math.round(containerRect.height)
                    },
                    cards: cardInfo,
                    allCardsVisible: cardInfo.every(c => c.visible)
                };
            }
        """)
        return result

    def check_blind_positions(self, page: Page, num_players: int) -> dict:
        """FIX-01 Regression Test: Verify blind positions are correct"""
        result = page.evaluate("""
            (numPlayers) => {
                // Find all player seats
                const seats = Array.from(document.querySelectorAll('.relative.p-2, .relative.p-3, .relative.p-4'))
                    .filter(el => el.querySelector('.font-semibold'));

                if (seats.length === 0) {
                    return {error: 'No player seats found'};
                }

                const players = seats.map(seat => {
                    const nameEl = seat.querySelector('.font-semibold');
                    const badgeEls = seat.querySelectorAll('.px-2.py-0\\\\.5.rounded.text-xs.font-bold');
                    const badges = Array.from(badgeEls).map(b => b.textContent.trim());

                    return {
                        name: nameEl ? nameEl.textContent.trim() : 'Unknown',
                        badges: badges
                    };
                });

                // Find SB, BB, and Dealer positions
                const sbPlayer = players.find(p => p.badges.includes('SB'));
                const bbPlayer = players.find(p => p.badges.includes('BB'));
                const dealerPlayer = players.find(p => p.badges.includes('D'));

                // Check if SB and BB are consecutive
                const sbIndex = players.findIndex(p => p.badges.includes('SB'));
                const bbIndex = players.findIndex(p => p.badges.includes('BB'));

                let consecutive = false;
                if (sbIndex !== -1 && bbIndex !== -1) {
                    // BB should be next to SB (wrapping around)
                    consecutive = (bbIndex === (sbIndex + 1) % players.length);
                }

                return {
                    players: players,
                    sbPlayer: sbPlayer ? sbPlayer.name : 'NOT FOUND',
                    bbPlayer: bbPlayer ? bbPlayer.name : 'NOT FOUND',
                    dealerPlayer: dealerPlayer ? dealerPlayer.name : 'NOT FOUND',
                    sbBbConsecutive: consecutive,
                    valid: sbPlayer && bbPlayer && dealerPlayer && consecutive
                };
            }
        """, num_players)
        return result

    def check_responsive_sizing(self, page: Page) -> dict:
        """FIX-03 Regression Test: Verify responsive card sizing"""
        result = page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.bg-white');
                if (cards.length === 0) {
                    return {error: 'No cards found'};
                }

                const viewport = {width: window.innerWidth, height: window.innerHeight};

                const cardSizes = Array.from(cards).slice(0, 5).map(card => {
                    const rect = card.getBoundingClientRect();
                    return {
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };
                });

                // Expected sizes based on viewport width
                let expectedWidth, expectedHeight;
                if (viewport.width < 640) {
                    expectedWidth = 64;  // w-16 (4rem)
                    expectedHeight = 96; // h-24 (6rem)
                } else if (viewport.width < 768) {
                    expectedWidth = 80;  // w-20 (5rem)
                    expectedHeight = 112; // h-28 (7rem)
                } else {
                    expectedWidth = 96;  // w-24 (6rem)
                    expectedHeight = 128; // h-32 (8rem)
                }

                // Allow 2px tolerance
                const sizesCorrect = cardSizes.every(size =>
                    Math.abs(size.width - expectedWidth) <= 2 &&
                    Math.abs(size.height - expectedHeight) <= 2
                );

                return {
                    viewport: viewport,
                    cardSizes: cardSizes,
                    expected: {width: expectedWidth, height: expectedHeight},
                    sizesCorrect: sizesCorrect
                };
            }
        """)
        return result

    @pytest.mark.parametrize("viewport", VIEWPORTS, ids=[v["name"] for v in VIEWPORTS])
    @pytest.mark.parametrize("num_players", PLAYER_COUNTS)
    def test_human_cards_visible_all_states(self, browser, viewport, num_players):
        """
        FIX-04: Test human player cards are fully visible at all game states
        Tests all combinations of viewport sizes and player counts
        """
        context = browser.new_context(viewport={"width": viewport["width"], "height": viewport["height"]})
        page = context.new_page()

        try:
            # Start game
            test_name = f"Test_{viewport['name']}_{num_players}p"
            self.start_game(page, test_name, num_players)

            # Test each game state
            for state in GAME_STATES:
                # Advance to target state
                success = self.advance_to_state(page, state)
                if not success:
                    # Game ended early (e.g., everyone folded)
                    continue

                # Check human cards visibility
                result = self.check_human_cards_visible(page)

                # Assert no error
                assert 'error' not in result, f"Error at {state}: {result.get('error')}"

                # Assert all cards visible
                assert result['allCardsVisible'], (
                    f"Cards not fully visible at {viewport['name']} ({viewport['width']}x{viewport['height']}), "
                    f"{num_players} players, {state} state.\n"
                    f"Viewport height: {result['viewport']['height']}px\n"
                    f"Container bottom: {result['container']['bottom']}px\n"
                    f"Cards: {result['cards']}"
                )

                # Check percentage visible for each card
                for i, card in enumerate(result['cards']):
                    assert card['percentVisible'] == 100, (
                        f"Card {i} only {card['percentVisible']}% visible at {viewport['name']}, "
                        f"{num_players} players, {state} state"
                    )

        finally:
            context.close()

    @pytest.mark.parametrize("num_players", PLAYER_COUNTS)
    def test_fix01_blind_positions_regression(self, browser, num_players):
        """
        FIX-01 Regression Test: Verify blind positions are correct
        Tests at standard viewport (1920x1080) for both 4 and 6 players
        """
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Start game
            self.start_game(page, f"BlindTest_{num_players}p", num_players)

            # Check at PRE_FLOP (blinds most visible)
            self.advance_to_state(page, "PRE_FLOP")

            result = self.check_blind_positions(page, num_players)

            # Assert no error
            assert 'error' not in result, f"Error checking blind positions: {result.get('error')}"

            # Assert all positions found
            assert result['sbPlayer'] != 'NOT FOUND', f"SB badge not found. Players: {result['players']}"
            assert result['bbPlayer'] != 'NOT FOUND', f"BB badge not found. Players: {result['players']}"
            assert result['dealerPlayer'] != 'NOT FOUND', f"Dealer badge not found. Players: {result['players']}"

            # Assert SB and BB are consecutive
            assert result['sbBbConsecutive'], (
                f"SB and BB not consecutive. SB: {result['sbPlayer']}, BB: {result['bbPlayer']}\n"
                f"All players: {result['players']}"
            )

            # Assert overall validity
            assert result['valid'], f"Blind positions invalid: {result}"

        finally:
            context.close()

    @pytest.mark.parametrize("viewport", VIEWPORTS, ids=[v["name"] for v in VIEWPORTS])
    def test_fix03_responsive_sizing_regression(self, browser, viewport):
        """
        FIX-03 Regression Test: Verify responsive card sizing
        Tests at all viewport sizes with 4 players
        """
        context = browser.new_context(viewport={"width": viewport["width"], "height": viewport["height"]})
        page = context.new_page()

        try:
            # Start game
            self.start_game(page, f"SizeTest_{viewport['name']}", 4)

            # Check at PRE_FLOP (all cards visible)
            self.advance_to_state(page, "PRE_FLOP")

            result = self.check_responsive_sizing(page)

            # Assert no error
            assert 'error' not in result, f"Error checking card sizes: {result.get('error')}"

            # Assert sizes correct
            assert result['sizesCorrect'], (
                f"Card sizes incorrect at {viewport['name']} ({viewport['width']}x{viewport['height']}).\n"
                f"Expected: {result['expected']}\n"
                f"Actual: {result['cardSizes']}"
            )

        finally:
            context.close()

    def test_split_screen_mode(self, browser):
        """
        Critical test: Split-screen mode at FLOP state
        This was the specific failure case reported by user
        """
        # Simulate split-screen height (~900px)
        context = browser.new_context(viewport={"width": 1920, "height": 900})
        page = context.new_page()

        try:
            # Start 4-player game (user's failure case)
            self.start_game(page, "SplitScreenTest", 4)

            # Advance to FLOP (user's failure case)
            success = self.advance_to_state(page, "FLOP")
            assert success, "Could not advance to FLOP state"

            # Check human cards visibility
            result = self.check_human_cards_visible(page)

            # Assert no error
            assert 'error' not in result, f"Error in split-screen mode: {result.get('error')}"

            # Assert all cards visible (THIS WAS THE FAILURE)
            assert result['allCardsVisible'], (
                f"Cards not fully visible in split-screen mode at FLOP.\n"
                f"Viewport: 1920x900\n"
                f"Container bottom: {result['container']['bottom']}px\n"
                f"Cards: {result['cards']}\n"
                f"This is the exact failure case reported by user!"
            )

        finally:
            context.close()

    def test_fullscreen_mode(self, browser):
        """
        Test fullscreen mode at FLOP state
        User reported this worked, but split-screen failed
        """
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Start 4-player game
            self.start_game(page, "FullscreenTest", 4)

            # Advance to FLOP
            success = self.advance_to_state(page, "FLOP")
            assert success, "Could not advance to FLOP state"

            # Check human cards visibility
            result = self.check_human_cards_visible(page)

            # Assert no error
            assert 'error' not in result, f"Error in fullscreen mode: {result.get('error')}"

            # Assert all cards visible
            assert result['allCardsVisible'], (
                f"Cards not fully visible in fullscreen mode at FLOP.\n"
                f"This should work according to user feedback!"
            )

        finally:
            context.close()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
