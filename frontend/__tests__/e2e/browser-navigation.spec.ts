import { test, expect } from '@playwright/test';

test.describe('Browser Navigation', () => {
  test('forward button returns to home after back', async ({ page }) => {
    // 1. Login and start game
    await page.goto('http://localhost:3001');
    await page.fill('input[id="username"]', 'nav_test_user');
    await page.fill('input[id="password"]', 'test12345');
    await page.fill('input[id="confirmPassword"]', 'test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3001');

    await page.click('a[href="/game/new"]');
    await page.waitForSelector('button:has-text("Start Game")');
    await page.click('button:has-text("Start Game")');
    await page.waitForSelector('[data-testid="quit-button"]', { timeout: 5000 });
    const gameUrl = page.url();

    // 2. Navigate to home
    await page.goto('http://localhost:3001');
    await page.waitForURL('http://localhost:3001');

    // 3. Browser back
    await page.goBack();
    expect(page.url()).toBe(gameUrl);
    await page.waitForSelector('[data-testid="quit-button"]');

    // 4. Browser forward
    await page.goForward();

    // 5. Should return to home, not stay at game
    expect(page.url()).toBe('http://localhost:3001/');
    const heading = await page.locator('h1').first().textContent();
    expect(heading).toContain('Welcome');
  });
});
