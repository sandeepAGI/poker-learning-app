import { test, expect } from '@playwright/test';

test.describe('Quit and New Game Flow', () => {
  test('shows game creation form after quit then Start New Game', async ({ page }) => {
    // 1. Login and start game
    await page.goto('http://localhost:3001');
    await page.fill('input[id="username"]', 'quit_test_user');
    await page.fill('input[id="password"]', 'test12345');
    await page.fill('input[id="confirmPassword"]', 'test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3001');

    await page.click('a[href="/game/new"]');
    await page.waitForSelector('button:has-text("Start Game")');
    await page.click('button:has-text("Start Game")');

    // 2. Wait for game to load
    await page.waitForSelector('[data-testid="quit-button"]', { timeout: 5000 });

    // 3. Quit game
    await page.click('[data-testid="quit-button"]');
    await page.waitForURL('http://localhost:3001');

    // 4. Click Start New Game again
    await page.click('a[href="/game/new"]');

    // 5. Should show game creation form, NOT poker table
    await page.waitForSelector('input[type="text"]'); // Player name field
    const heading = await page.locator('h1').textContent();
    expect(heading).toContain('Poker Learning App');

    const yourNameLabel = page.locator('label').filter({ hasText: 'Your Name' });
    await expect(yourNameLabel).toBeVisible();

    // 6. Should NOT show poker table
    const quitButtons = await page.locator('[data-testid="quit-button"]').count();
    expect(quitButtons).toBe(0);
  });
});
