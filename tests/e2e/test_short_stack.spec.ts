import { test, expect } from '@playwright/test';

/**
 * E2E tests for short-stack all-in scenarios.
 *
 * Issue #1: Short-Stack Call/Raise UI Blocks Valid Actions
 * This test suite verifies that the UI correctly handles scenarios where
 * a player has insufficient chips to match the full bet amount.
 */

test.describe('Short-Stack UI', () => {
  let gameId: string

  test.beforeEach(async ({ page }) => {
    // Navigate and create game
    await page.goto('http://localhost:3000')

    // Verify Start Game button exists and click
    const startGameButton = page.locator('text=Start Game')
    await expect(startGameButton).toBeVisible({ timeout: 10000 })
    await startGameButton.click()

    // Wait for game to be created and URL to change
    await page.waitForURL(/\/game\/[a-f0-9-]{36}/, { timeout: 10000 })

    // Extract and validate game ID from URL
    const url = page.url()
    gameId = url.split('/').pop() || ''

    // Validate UUID format
    expect(gameId).toMatch(/^[a-f0-9-]{36}$/)

    // Wait for poker table to be ready
    await expect(page.getByTestId('poker-table-main')).toBeVisible({ timeout: 10000 })
  })

  test('allows call all-in when stack < call amount', async ({ page, request }) => {
    // Manipulate game state via test endpoint
    const response = await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: {
          Player: 30,
        },
        current_bet: 80,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    expect(response.ok()).toBeTruthy()

    // Wait for WebSocket to update UI (check for stack change)
    const callButton = page.getByTestId('call-button')
    await expect(callButton).toBeEnabled({ timeout: 5000 })

    // Verify shows "All-In" with correct amount
    await expect(callButton).toContainText('All-In', { timeout: 2000 })
    await expect(callButton).toContainText('$30')

    // Click and verify action succeeds
    await callButton.click()

    // Verify action was accepted (button should disappear or change)
    await expect(callButton).not.toBeVisible({ timeout: 5000 })
  })

  test('allows raise all-in when stack < min raise', async ({ page, request }) => {
    // Setup: player with $30, min raise is $40
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: { Player: 30 },
        current_bet: 20,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    // Wait for UI to update, then click Raise to open panel
    const raiseButton = page.getByTestId('raise-button')
    await expect(raiseButton).toBeEnabled({ timeout: 5000 })
    await raiseButton.click()

    // Verify All-In button available in raise panel
    const allInButton = page.getByTestId('all-in-button')
    await expect(allInButton).toBeEnabled({ timeout: 2000 })

    // Click All-In
    await allInButton.click()

    // Verify action was accepted (raise panel should close)
    await expect(allInButton).not.toBeVisible({ timeout: 5000 })
  })

  test('shows correct call button label for short stack', async ({ page, request }) => {
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: { Player: 15 },
        current_bet: 50,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    // Wait for UI to update and verify label shows "Call All-In $15" (not "Call $50")
    const callButton = page.getByTestId('call-button')
    await expect(callButton).toBeEnabled({ timeout: 5000 })
    await expect(callButton).toContainText('All-In')
    await expect(callButton).toContainText('$15')
    await expect(callButton).not.toContainText('$50')
  })
})
