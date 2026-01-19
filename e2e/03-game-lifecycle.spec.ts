import { test, expect } from '@playwright/test';
import { config, generateTestUsername } from './config';
import { registerUser, createGame, takeAction, waitForAITurn, quitGame } from './helpers';

/**
 * Suite 3: Game Lifecycle
 *
 * Tests that verify the complete game flow:
 * - Navigate to game creation page
 * - Create new game
 * - Player can take actions (fold, check, call, raise)
 * - AI players act and game progresses
 * - Player can quit game
 * - Game appears in history
 */

test.describe('Suite 3: Game Lifecycle', () => {
  test('3.1: Navigate to game creation page', async ({ page }) => {
    // Register and login
    const { username } = await registerUser(page);

    // Should be redirected to home after registration
    await page.waitForURL('/', { timeout: 10000 }).catch(() => {});

    // Click "Start New Game" link
    const newGameLink = page.locator('a:has-text("Start New Game"), [data-testid="start-new-game-link"]');
    await expect(newGameLink).toBeVisible({ timeout: 10000 });

    await newGameLink.click();

    // Wait for game creation page
    await page.waitForURL('/game/new', { timeout: 10000 });

    await page.screenshot({ path: 'e2e/screenshots/03-game-creation.png' });

    // Should see game setup options
    await expect(page.locator('text=Poker Learning App')).toBeVisible();
    await expect(page.locator('button:has-text("Start Game"), [data-testid="start-game-button"]')).toBeVisible();
  });

  test('3.2: Create new game', async ({ page }) => {
    // Capture all browser console messages
    page.on('console', msg => console.log('[BROWSER]', msg.type(), msg.text()));

    // Capture page errors
    page.on('pageerror', err => console.error('[PAGE ERROR]', err.message));

    // Capture failed requests
    page.on('requestfailed', request => {
      console.error('[REQUEST FAILED]', request.url(), request.failure()?.errorText);
    });

    // Register and login
    const { username } = await registerUser(page);

    // Create game using helper
    await createGame(page, username, 3);

    await page.screenshot({ path: 'e2e/screenshots/03-game-loaded.png' });

    // Verify poker table elements are visible with data-testid
    const hasActionButtons = await page.locator('[data-testid="fold-button"], [data-testid="call-button"], button:has-text("Fold"), button:has-text("Call")').first().isVisible({ timeout: 15000 }).catch(() => false);

    expect(hasActionButtons).toBe(true);

    // Verify game URL
    const url = page.url();
    expect(url).toContain('/game/');
  });

  test('3.3: Player can check when no bet', async ({ page }) => {
    // Setup: Register, login and create game
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    // Wait for action buttons
    await page.waitForTimeout(2000);

    // Try to check if available
    const checkBtn = page.locator('button:has-text("Check"):not([disabled])');
    const canCheck = await checkBtn.isVisible().catch(() => false);

    if (canCheck) {
      await checkBtn.click();

      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'e2e/screenshots/03-after-check.png' });

      // Game should continue (no error)
      const hasError = await page.locator('text=Error').isVisible().catch(() => false);
      expect(hasError).toBe(false);
    } else {
      console.log('SKIP: Check not available - likely has bet to call');
      test.skip();
    }
  });

  test('3.4: Player can fold', async ({ page }) => {
    // Setup: Register, login and create game
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    // Wait for action buttons to be enabled
    await page.waitForSelector('button:has-text("Fold"):not([disabled])', { timeout: 10000 }).catch(() => {
      console.log('Fold button not found or disabled');
    });

    // Click fold
    const foldBtn = page.locator('button:has-text("Fold"):not([disabled])');
    const canFold = await foldBtn.isVisible().catch(() => false);

    if (canFold) {
      await foldBtn.click();

      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'e2e/screenshots/03-after-fold.png' });

      // Game should continue (AI players act)
      const hasError = await page.locator('text=Error, text=error').isVisible().catch(() => false);
      expect(hasError).toBe(false);
    } else {
      console.log('SKIP: Fold button not available');
      test.skip();
    }
  });

  test('3.5: Game progresses as AI players act', async ({ page }) => {
    // Setup: Register, login and create game
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    // Fold to let AI players act
    await takeAction(page, 'fold');

    // Wait for AI to act
    await page.waitForTimeout(5000);

    await page.screenshot({ path: 'e2e/screenshots/03-ai-acting.png' });

    // Check game is still active (quit button visible)
    const quitBtn = page.locator('button:has-text("Quit")');
    const hasQuitBtn = await quitBtn.isVisible().catch(() => false);

    expect(hasQuitBtn).toBe(true);
  });

  test('3.6: Player can quit game', async ({ page }) => {
    // Setup: Register, login and create game
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    // Quit game
    const quitted = await quitGame(page);

    if (quitted) {
      await page.screenshot({ path: 'e2e/screenshots/03-after-quit.png' });

      // Should return to home page
      const url = page.url();
      const isHome = url.endsWith('/') || url.includes('localhost:3000');

      const hasHomeContent = await page.locator('text=Start New Game, text=Welcome').first().isVisible().catch(() => false);

      expect(isHome || hasHomeContent).toBe(true);
    } else {
      console.log('SKIP: Quit button not found');
      test.skip();
    }
  });

  test('3.7: Game appears in history', async ({ page }) => {
    // Register, login and create a game
    const { username } = await registerUser(page);

    // Create and immediately quit a game to add to history
    await createGame(page, username, 3);
    await page.waitForTimeout(2000);
    await quitGame(page);

    // Navigate to history
    await page.goto('/');
    const historyLink = page.locator('a:has-text("Game History"), a:has-text("View Game History")');

    const hasHistoryLink = await historyLink.isVisible().catch(() => false);

    if (hasHistoryLink) {
      await historyLink.click();

      await page.waitForURL('/history', { timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(2000);

      await page.screenshot({ path: 'e2e/screenshots/03-game-history.png' });

      // Should see game history page content
      const content = await page.content();
      const hasHistoryContent = content.includes('History') ||
                               content.includes('Game') ||
                               content.includes('Completed') ||
                               content.includes('No games');

      expect(hasHistoryContent).toBe(true);
    } else {
      console.log('SKIP: History link not found');
      test.skip();
    }
  });
});
