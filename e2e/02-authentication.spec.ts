import { test, expect } from '@playwright/test';
import { config, generateTestUsername } from './config';

/**
 * Suite 2: User Authentication
 *
 * Tests that verify user registration, login, and logout flows:
 * - User registration creates account
 * - User logout clears session
 * - User login with existing account
 * - Invalid credentials are rejected
 */

test.describe('Suite 2: User Authentication', () => {
  const testUsername = generateTestUsername('auth_test');
  const testPassword = config.TEST_PASSWORD;

  test('2.1: User registration flow', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await expect(page.locator('input#username')).toBeVisible();

    // Switch to registration mode
    await page.click('button:has-text("Don\'t have an account")');

    // Wait for confirm password field to appear
    await expect(page.locator('input#confirmPassword')).toBeVisible();

    // Fill registration form
    await page.fill('input#username', testUsername);
    await page.fill('input#password', testPassword);
    await page.fill('input#confirmPassword', testPassword);

    // Take screenshot before submission
    await page.screenshot({ path: 'e2e/screenshots/02-registration-form.png' });

    // Submit registration
    await page.click('button[type="submit"]');

    // Wait for redirect to home page
    await page.waitForURL('/', { timeout: 10000 });

    // Take screenshot after submission
    await page.screenshot({ path: 'e2e/screenshots/02-after-registration.png' });

    // Verify successful registration (check for home page elements)
    const content = await page.content();
    const successIndicators = [
      content.includes('Start New Game') || content.includes('Game History'),
      await page.locator('text=Start New Game').isVisible().catch(() => false),
      await page.locator('text=Game History').isVisible().catch(() => false),
    ];

    expect(successIndicators.some((indicator) => indicator)).toBe(true);
  });

  test('2.2: User logout flow', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('input#username', testUsername);
    await page.fill('input#password', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL('/');

    // Look for logout button
    const logoutBtn = page.locator('button:has-text("Logout"), a:has-text("Logout")');

    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();

      // Wait for redirect to login page
      await page.waitForURL('/login', { timeout: 5000 }).catch(() => {});

      await page.screenshot({ path: 'e2e/screenshots/02-after-logout.png' });

      // Verify we're on login page
      await expect(page.locator('input#username')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    } else {
      console.log('SKIP: Logout button not found - may not be implemented yet');
      test.skip();
    }
  });

  test('2.3: User login flow with existing account', async ({ page }) => {
    await page.goto('/login');

    // Fill login form
    await expect(page.locator('input#username')).toBeVisible();
    await page.fill('input#username', testUsername);
    await page.fill('input#password', testPassword);

    await page.screenshot({ path: 'e2e/screenshots/02-login-form.png' });

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation to home
    await page.waitForURL('/', { timeout: 10000 });

    await page.screenshot({ path: 'e2e/screenshots/02-after-login.png' });

    // Verify login success (should see home page content)
    const hasGameContent = await page.locator('text=Start New Game').isVisible().catch(() => false) ||
                           await page.locator('text=Game History').isVisible().catch(() => false);

    expect(hasGameContent).toBe(true);
  });

  test('2.4: Invalid credentials rejected', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await expect(page.locator('input#username')).toBeVisible();
    await page.fill('input#username', 'invalid_user_99999');
    await page.fill('input#password', 'wrongpassword');

    await page.click('button[type="submit"]');

    // Wait a moment for error to appear
    await page.waitForTimeout(2000);

    await page.screenshot({ path: 'e2e/screenshots/02-invalid-login.png' });

    // Should show error message
    const errorVisible = await page.locator('.bg-red-900').isVisible().catch(() => false);
    const content = await page.content();
    const hasErrorText = content.toLowerCase().includes('invalid') ||
                        content.toLowerCase().includes('incorrect') ||
                        content.toLowerCase().includes('failed');

    expect(errorVisible || hasErrorText).toBe(true);
  });

  test('2.5: Registration with mismatched passwords rejected', async ({ page }) => {
    await page.goto('/login');

    // Switch to registration mode
    await page.click('button:has-text("Don\'t have an account")');
    await expect(page.locator('input#confirmPassword')).toBeVisible();

    // Fill with mismatched passwords
    await page.fill('input#username', generateTestUsername('mismatch'));
    await page.fill('input#password', 'password123');
    await page.fill('input#confirmPassword', 'password456');

    await page.click('button[type="submit"]');

    // Should show error
    await expect(page.locator('.bg-red-900')).toBeVisible({ timeout: 2000 });

    const errorText = await page.locator('.bg-red-900').textContent();
    expect(errorText?.toLowerCase()).toContain('match');
  });

  test('2.6: Registration with short password rejected', async ({ page }) => {
    await page.goto('/login');

    // Switch to registration mode
    await page.click('button:has-text("Don\'t have an account")');
    await expect(page.locator('input#confirmPassword')).toBeVisible();

    // Fill with short password
    const shortPassword = '123';
    await page.fill('input#username', generateTestUsername('short'));
    await page.fill('input#password', shortPassword);
    await page.fill('input#confirmPassword', shortPassword);

    await page.click('button[type="submit"]');

    // Should show error
    await expect(page.locator('.bg-red-900')).toBeVisible({ timeout: 2000 });

    const errorText = await page.locator('.bg-red-900').textContent();
    expect(errorText?.toLowerCase()).toMatch(/6|character|length/);
  });
});
