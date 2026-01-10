"""
E2E Test for Issue #1: Short-Stack Call/Raise UI Fix

This test verifies that players with short stacks can still call or go all-in,
even when their stack is less than the current bet.

TDD Red Phase: This test should FAIL before the fix is applied.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def base_url():
    """Base URL for the application"""
    return "http://localhost:3000"


def test_short_stack_can_call_all_in(page: Page, base_url: str):
    """
    Test that a player with a short stack can call (all-in) when stack < current_bet.

    Steps:
    1. Start a new game
    2. Manipulate game state to give player a short stack (e.g., 30 chips)
    3. Wait for a situation where current_bet > player_stack (e.g., 80 chips)
    4. Verify Call button is ENABLED (not disabled)
    5. Click Call and verify action is sent
    """
    # Navigate to game
    page.goto(base_url)
    page.click("text=Start New Game")

    # Wait for game to load
    page.wait_for_selector("[data-testid='poker-table']", timeout=10000)

    # TODO: Need a way to manipulate game state for testing
    # For now, this is a placeholder that shows what we need to test
    # The actual test will need backend support to set up specific scenarios

    # This test will FAIL if the UI disables Call when stack < current_bet
    # Expected: Call button should be enabled when player has any chips

    # For now, let's just verify the page loaded
    expect(page.locator("[data-testid='poker-table']")).to_be_visible()

    # Mark as incomplete - need game state manipulation
    pytest.skip("Needs game state manipulation feature for e2e testing")


def test_short_stack_can_raise_all_in(page: Page, base_url: str):
    """
    Test that a player with a short stack can raise (all-in) when stack < min_raise.

    Steps:
    1. Start a new game
    2. Give player a short stack (e.g., 50 chips)
    3. Wait for situation where min_raise > player_stack (e.g., 80 chips)
    4. Verify Raise button is ENABLED
    5. Verify raise slider allows all-in amount
    """
    page.goto(base_url)
    page.click("text=Start New Game")
    page.wait_for_selector("[data-testid='poker-table']", timeout=10000)

    # This test will FAIL if the UI disables Raise when stack < min_raise
    expect(page.locator("[data-testid='poker-table']")).to_be_visible()

    pytest.skip("Needs game state manipulation feature for e2e testing")


def test_call_button_label_shows_all_in_when_short_stack(page: Page, base_url: str):
    """
    Test that Call button shows 'Call All-In' or similar when stack < call_amount.

    This helps users understand they're going all-in.
    """
    page.goto(base_url)
    page.click("text=Start New Game")
    page.wait_for_selector("[data-testid='poker-table']", timeout=10000)

    # Verify helpful label
    # Expected: "Call All-In $50" or "Call $50 (All-In)"

    expect(page.locator("[data-testid='poker-table']")).to_be_visible()
    pytest.skip("Needs game state manipulation feature for e2e testing")
