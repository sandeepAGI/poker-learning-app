import { test, expect } from '@playwright/test';
import { registerUser } from './helpers';
import { config } from './config';

/**
 * Suite 7: Mobile Gate
 *
 * Validates the mobile gate component:
 * - Desktop users see the app normally (no gate)
 * - Mobile users see a "Best Experienced on Desktop" message
 * - "Continue anyway" dismisses the gate and shows the app
 */

test.describe('Suite 7: Mobile Gate', () => {
  test('7.1: Desktop loads normally — mobile gate is NOT visible, login form IS visible', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    // Mobile gate should not be present
    await expect(page.locator('[data-testid="mobile-gate"]')).not.toBeVisible();

    // Login form or authenticated content should be visible
    const loginVisible = await page.locator('input#username').isVisible().catch(() => false);
    const authVisible = await page.locator('text=Start New Game').isVisible().catch(() => false);
    expect(loginVisible || authVisible).toBe(true);
  });

  test('7.2: Desktop game page loads normally — no gate blocking gameplay', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await registerUser(page);

    // Navigate to game creation
    await page.goto('/game/new');

    // Mobile gate should not be present
    await expect(page.locator('[data-testid="mobile-gate"]')).not.toBeVisible();

    // Game creation page content should be visible
    const pageContent = await page.locator('button:has-text("Start Game"), text=Start New Game').first().isVisible().catch(() => false);
    expect(pageContent).toBe(true);
  });

  test('7.3: Mobile shows gate message with "Continue anyway" link', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    // Mobile gate should be visible
    const gate = page.locator('[data-testid="mobile-gate"]');
    await expect(gate).toBeVisible({ timeout: 5000 });

    // Should contain the heading
    await expect(gate.locator('text=Best Experienced on Desktop')).toBeVisible();

    // Should contain the continue button
    await expect(page.locator('[data-testid="mobile-gate-continue"]')).toBeVisible();

    // App content should NOT be visible behind the gate
    await expect(page.locator('input#username')).not.toBeVisible();
  });

  test('7.4: Clicking "Continue anyway" dismisses gate and shows the app', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    // Wait for the gate
    await expect(page.locator('[data-testid="mobile-gate"]')).toBeVisible({ timeout: 5000 });

    // Click continue
    await page.locator('[data-testid="mobile-gate-continue"]').click();

    // Gate should disappear
    await expect(page.locator('[data-testid="mobile-gate"]')).not.toBeVisible();

    // App content should now be visible (login form or authenticated content)
    const loginVisible = await page.locator('input#username').isVisible({ timeout: 5000 }).catch(() => false);
    const authVisible = await page.locator('text=Start New Game').isVisible().catch(() => false);
    expect(loginVisible || authVisible).toBe(true);
  });

  test('7.5: After dismissal, app content is accessible', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    // Dismiss the gate
    await expect(page.locator('[data-testid="mobile-gate"]')).toBeVisible({ timeout: 5000 });
    await page.locator('[data-testid="mobile-gate-continue"]').click();
    await expect(page.locator('[data-testid="mobile-gate"]')).not.toBeVisible();

    // Verify we can interact with the app — login form fields should be interactable
    const usernameInput = page.locator('input#username');
    if (await usernameInput.isVisible().catch(() => false)) {
      await usernameInput.fill('testuser');
      await expect(usernameInput).toHaveValue('testuser');
    }
  });
});
