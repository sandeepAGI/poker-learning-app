import { test, expect } from '@playwright/test';

test.describe('Card Rendering After Navigation', () => {
  test('cards render correctly after browser back button', async ({ page }) => {
    // 1. Login
    await page.goto('http://localhost:3001');
    await page.fill('input[id="username"]', 'e2e_test_user');
    await page.fill('input[id="password"]', 'test12345');
    await page.fill('input[id="confirmPassword"]', 'test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3001');

    // 2. Start game
    await page.click('a[href="/game/new"]');
    await page.waitForSelector('button:has-text("Start Game")');
    await page.click('button:has-text("Start Game")');

    // 3. Wait for cards to render
    await page.waitForSelector('[data-testid^="player-"][data-testid$="-card-0"]', { timeout: 5000 });

    // 4. Verify cards have content
    const cardBefore = await page.locator('[data-testid="player-0-card-0"]').textContent();
    expect(cardBefore).toBeTruthy();
    expect(cardBefore).toMatch(/[A2-9TJQK]/); // Should have rank

    // 5. Navigate away
    await page.goto('http://localhost:3001');
    await page.waitForURL('http://localhost:3001');

    // 6. Browser back
    await page.goBack();

    // 7. Wait for game to restore
    await page.waitForSelector('[data-testid^="player-"][data-testid$="-card-0"]', { timeout: 5000 });

    // 8. Verify cards still render correctly
    const cardAfter = await page.locator('[data-testid="player-0-card-0"]').textContent();
    expect(cardAfter).toBeTruthy();
    expect(cardAfter).toMatch(/[A2-9TJQK]/); // Should still have rank

    // 9. Verify card suits visible
    const cardElement = await page.locator('[data-testid="player-0-card-0"]');
    const innerHTML = await cardElement.innerHTML();
    expect(innerHTML).toMatch(/[♥♦♣♠]/); // Should have suit symbol
  });
});
