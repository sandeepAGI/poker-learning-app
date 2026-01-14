import { test, expect } from '@playwright/test';

test.describe('Combined Navigation Scenarios', () => {
  test('handles complex navigation flow: back → forward → quit → new game', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Capture console errors for hydration detection
    page.on('console', msg => {
      if (msg.type() === 'error' &&
          (msg.text().includes('Hydration') || msg.text().includes('did not match'))) {
        consoleErrors.push(msg.text());
      }
    });

    // 1. Login and start game
    await page.goto('http://localhost:3001');
    await page.fill('input[id="username"]', 'nav_integration_test');
    await page.fill('input[id="password"]', 'test12345');
    await page.fill('input[id="confirmPassword"]', 'test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3001');

    await page.click('a[href="/game/new"]');
    await page.waitForSelector('button:has-text("Start Game")');
    await page.click('button:has-text("Start Game")');
    await page.waitForSelector('[data-testid="quit-button"]', { timeout: 5000 });
    const gameUrl = page.url();

    // 2. Verify cards render correctly (if hole cards are visible)
    const holeCards = await page.locator('[data-testid^="hole-card-"]').first();
    if (await holeCards.isVisible()) {
      const cardText = await holeCards.textContent();
      expect(cardText).toBeTruthy();
    }

    // 3. Navigate to home
    await page.goto('http://localhost:3001');
    await page.waitForURL('http://localhost:3001');

    // 4. Browser back - should restore game
    await page.goBack();
    expect(page.url()).toBe(gameUrl);
    await page.waitForSelector('[data-testid="quit-button"]');

    // Verify cards still render after back (if visible)
    if (await holeCards.isVisible()) {
      const cardAfterBack = await holeCards.textContent();
      expect(cardAfterBack).toBeTruthy();
    }

    // 5. Browser forward - should return to home
    await page.goForward();
    expect(page.url()).toBe('http://localhost:3001/');

    // 6. Navigate back to game again
    await page.goBack();
    await page.waitForSelector('[data-testid="quit-button"]');

    // 7. Quit game
    await page.click('[data-testid="quit-button"]');
    await page.waitForURL('http://localhost:3001/');

    // 8. Start new game - should show creation form, not old game
    await page.click('a[href="/game/new"]');
    await page.waitForSelector('input[type="text"]');
    const yourNameLabel = page.locator('label').filter({ hasText: 'Your Name' });
    await expect(yourNameLabel).toBeVisible();

    // Should NOT show poker table from previous game
    const quitButtons = await page.locator('[data-testid="quit-button"]').count();
    expect(quitButtons).toBe(0);

    // 9. Verify no hydration errors occurred during entire flow
    expect(consoleErrors).toHaveLength(0);
  });
});
