import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for poker table UI.
 *
 * These tests capture screenshots and compare them to baselines.
 * Baselines should be generated in CI (ubuntu-latest) for consistency.
 *
 * To update baselines: npx playwright test --update-snapshots
 */

test.describe('Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('http://localhost:3000')

    // Wait for page to be ready
    await expect(page.locator('text=New Game')).toBeVisible({ timeout: 10000 })
  })

  test('home page matches baseline', async ({ page }) => {
    // Take screenshot of entire page
    await expect(page).toHaveScreenshot('home-page.png', {
      fullPage: true,
      maxDiffPixels: 100, // Allow small rendering differences
    })
  })

  test('poker table layout matches baseline', async ({ page }) => {
    // Create a new game
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/[a-f0-9-]{36}/, { timeout: 10000 })

    // Wait for table to load
    await expect(page.getByTestId('poker-table-main')).toBeVisible({ timeout: 10000 })

    // Take screenshot of poker table
    const table = page.getByTestId('poker-table-main')
    await expect(table).toHaveScreenshot('poker-table.png', {
      maxDiffPixels: 200, // Card animations may cause slight differences
    })
  })

  test('action buttons render correctly', async ({ page }) => {
    // Create game and wait for table
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/[a-f0-9-]{36}/, { timeout: 10000 })
    await expect(page.getByTestId('action-buttons-container')).toBeVisible({ timeout: 10000 })

    // Screenshot action button area
    const actionArea = page.getByTestId('action-buttons-container')
    await expect(actionArea).toHaveScreenshot('action-buttons.png', {
      maxDiffPixels: 50,
    })
  })
})
