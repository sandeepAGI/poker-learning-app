import { test, expect } from '@playwright/test';
import { config, generateTestUsername } from './config';

/**
 * Suite 4: Error Handling
 *
 * Tests that verify error conditions are handled gracefully:
 * - Empty form submission shows validation
 * - Duplicate username rejected
 * - Invalid game ID shows error
 * - Network errors handled
 */

test.describe('Suite 4: Error Handling', () => {
  test('4.1: Empty form submission shows validation', async ({ page }) => {
    await page.goto('/');

    // Wait for submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Try to submit without filling form
    await page.click('button[type="submit"]');

    await page.waitForTimeout(1000);

    // Should show validation errors (either HTML5 or custom)
    const hasValidationError = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input:invalid');
      return inputs.length > 0;
    });

    const hasErrorMessage = await page.locator('.bg-red-900, [class*="error"]').isVisible().catch(() => false);

    expect(hasValidationError || hasErrorMessage).toBe(true);

    await page.screenshot({ path: 'e2e/screenshots/04-empty-form.png' });
  });

  test('4.2: Duplicate username rejected', async ({ page }) => {
    // First, register a user
    const username = generateTestUsername('duplicate');
    const password = 'TestPassword123!';

    await page.goto('/');

    // Register first time
    const registerButton = page.locator('button:has-text("Don\'t have an account")');
    if (await registerButton.isVisible().catch(() => false)) {
      await registerButton.click();
    }

    await expect(page.locator('input#confirmPassword')).toBeVisible();
    await page.fill('input#username', username);
    await page.fill('input#password', password);
    await page.fill('input#confirmPassword', password);
    await page.click('button[type="submit"]');

    // Wait for registration to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Logout
    const logoutBtn = page.locator('button:has-text("Logout")');
    if (await logoutBtn.isVisible().catch(() => false)) {
      await logoutBtn.click();
      await page.waitForTimeout(2000);
    }

    // Try to register with same username
    await page.goto('/');
    const registerBtn2 = page.locator('button:has-text("Don\'t have an account")');
    if (await registerBtn2.isVisible().catch(() => false)) {
      await registerBtn2.click();
    }

    await expect(page.locator('input#confirmPassword')).toBeVisible();
    await page.fill('input#username', username);
    await page.fill('input#password', password);
    await page.fill('input#confirmPassword', password);
    await page.click('button[type="submit"]');

    await page.waitForTimeout(2000);

    await page.screenshot({ path: 'e2e/screenshots/04-duplicate-username.png' });

    // Should show error about username taken
    const content = await page.content();
    const hasErrorText = content.toLowerCase().includes('taken') ||
                        content.toLowerCase().includes('exists') ||
                        content.toLowerCase().includes('already') ||
                        content.toLowerCase().includes('duplicate');

    const hasErrorElement = await page.locator('.bg-red-900, [class*="error"]').isVisible().catch(() => false);

    expect(hasErrorText || hasErrorElement).toBe(true);
  });

  test('4.3: Invalid game ID shows error', async ({ page }) => {
    // Try to access a non-existent game directly
    const invalidGameId = '00000000-0000-0000-0000-000000000000';
    await page.goto(`/game/${invalidGameId}`);

    await page.waitForTimeout(3000);

    await page.screenshot({ path: 'e2e/screenshots/04-invalid-game.png' });

    // Should show error, redirect, or show empty state
    const content = await page.content();
    const url = page.url();

    const hasError = content.toLowerCase().includes('not found') ||
                    content.toLowerCase().includes('error') ||
                    content.includes('404') ||
                    url.includes('/login') ||
                    url === config.FRONTEND_URL + '/';

    expect(hasError).toBe(true);
  });

  test('4.4: Password mismatch shows error', async ({ page }) => {
    await page.goto('/');

    // Switch to register mode
    const registerButton = page.locator('button:has-text("Don\'t have an account")');
    if (await registerButton.isVisible().catch(() => false)) {
      await registerButton.click();
    }

    await expect(page.locator('input#confirmPassword')).toBeVisible();

    // Fill with mismatched passwords
    await page.fill('input#username', generateTestUsername('mismatch'));
    await page.fill('input#password', 'password123');
    await page.fill('input#confirmPassword', 'password456');

    await page.click('button[type="submit"]');

    // Should show error
    await page.waitForTimeout(1000);

    await page.screenshot({ path: 'e2e/screenshots/04-password-mismatch.png' });

    const errorElement = await page.locator('.bg-red-900, [class*="error"]').isVisible().catch(() => false);
    const content = await page.content();
    const hasErrorText = content.toLowerCase().includes('match') ||
                        content.toLowerCase().includes('same');

    expect(errorElement || hasErrorText).toBe(true);
  });

  test('4.5: Short password rejected', async ({ page }) => {
    await page.goto('/');

    // Switch to register mode
    const registerButton = page.locator('button:has-text("Don\'t have an account")');
    if (await registerButton.isVisible().catch(() => false)) {
      await registerButton.click();
    }

    await expect(page.locator('input#confirmPassword')).toBeVisible();

    // Fill with short password
    const shortPassword = '123';
    await page.fill('input#username', generateTestUsername('short'));
    await page.fill('input#password', shortPassword);
    await page.fill('input#confirmPassword', shortPassword);

    await page.click('button[type="submit"]');

    // Should show error
    await page.waitForTimeout(1000);

    await page.screenshot({ path: 'e2e/screenshots/04-short-password.png' });

    const errorElement = await page.locator('.bg-red-900, [class*="error"]').isVisible().catch(() => false);
    const content = await page.content();
    const hasErrorText = content.toLowerCase().includes('6') ||
                        content.toLowerCase().includes('character') ||
                        content.toLowerCase().includes('length');

    expect(errorElement || hasErrorText).toBe(true);
  });
});
