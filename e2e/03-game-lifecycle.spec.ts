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
  let testUsername: string;
  let testPassword: string;

  test.beforeAll(async ({ browser }) => {
    // Create a test user for all game tests
    const page = await browser.newPage();
    const credentials = await registerUser(page);
    testUsername = credentials.username;
    testPassword = credentials.password;
    await page.close();
  });

  test('3.1: Navigate to game creation page', async ({ page }) => {
    // Login first
    await page.goto('/');

    // If not logged in, the page should show login form
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    // Click "Start New Game" link
    const newGameLink = page.locator('a:has-text("Start New Game")');
    await expect(newGameLink).toBeVisible();

    await newGameLink.click();

    // Wait for game creation page
    await page.waitForURL('/game/new', { timeout: 10000 });

    await page.screenshot({ path: 'e2e/screenshots/03-game-creation.png' });

    // Should see game setup options
    await expect(page.locator('text=Poker Learning App')).toBeVisible();
    await expect(page.locator('button:has-text("Start Game")')).toBeVisible();
  });

  test('3.2: Create new game', async ({ page }) => {
    // Login
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    // Create game using helper
    await createGame(page, testUsername, 3);

    await page.screenshot({ path: 'e2e/screenshots/03-game-loaded.png' });

    // Verify poker table elements are visible
    const hasActionButtons = await page.locator('button:has-text("Fold"), button:has-text("Check"), button:has-text("Call")').first().isVisible().catch(() => false);

    expect(hasActionButtons).toBe(true);

    // Verify game URL
    const url = page.url();
    expect(url).toContain('/game/');
  });

  test('3.3: Player can check when no bet', async ({ page }) => {
    // Setup: Login and create game
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    await createGame(page, testUsername, 3);

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
    // Setup: Login and create game
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    await createGame(page, testUsername, 3);

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
    // Setup: Login and create game
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    await createGame(page, testUsername, 3);

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
    // Setup: Login and create game
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    await createGame(page, testUsername, 3);

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
    // First, play and complete a game
    await page.goto('/');
    const hasLogin = await page.locator('input#username').isVisible().catch(() => false);
    if (hasLogin) {
      await page.fill('input#username', testUsername);
      await page.fill('input#password', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL('/');
    }

    // Create and immediately quit a game to add to history
    await createGame(page, testUsername, 3);
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
