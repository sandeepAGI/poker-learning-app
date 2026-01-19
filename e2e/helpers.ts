import { Page, expect } from '@playwright/test';
import { generateTestUsername } from './config';

/**
 * E2E Test Helpers
 * Reusable functions for common test operations
 */

/**
 * Register a new user and return credentials
 */
export async function registerUser(page: Page, username?: string, password?: string) {
  const testUsername = username || generateTestUsername('user');
  const testPassword = password || 'TestPassword123!';

  await page.goto('/');

  // Check if already authenticated
  const isAuth = await page.locator('text=Start New Game').isVisible().catch(() => false);
  if (isAuth) {
    return { username: testUsername, password: testPassword, alreadyLoggedIn: true };
  }

  // Switch to register mode if on login page
  const registerButton = page.locator('button:has-text("Don\'t have an account")');
  if (await registerButton.isVisible().catch(() => false)) {
    await registerButton.click();
  }

  // Wait for confirm password field
  await expect(page.locator('input#confirmPassword')).toBeVisible({ timeout: 5000 });

  // Fill form
  await page.fill('input#username', testUsername);
  await page.fill('input#password', testPassword);
  await page.fill('input#confirmPassword', testPassword);

  // Submit
  await page.click('button[type="submit"]');

  // Wait for redirect to home
  await page.waitForURL('/', { timeout: 10000 });

  return { username: testUsername, password: testPassword, alreadyLoggedIn: false };
}

/**
 * Login with existing credentials
 */
export async function loginUser(page: Page, username: string, password: string) {
  await page.goto('/');

  // Check if already authenticated
  const isAuth = await page.locator('text=Start New Game').isVisible().catch(() => false);
  if (isAuth) {
    return true;
  }

  // Fill login form
  await expect(page.locator('input#username')).toBeVisible();
  await page.fill('input#username', username);
  await page.fill('input#password', password);

  // Submit
  await page.click('button[type="submit"]');

  // Wait for redirect
  await page.waitForURL('/', { timeout: 10000 });

  return true;
}

/**
 * Logout current user
 */
export async function logoutUser(page: Page) {
  const logoutButton = page.locator('button:has-text("Logout")');
  if (await logoutButton.isVisible().catch(() => false)) {
    await logoutButton.click();
    await page.waitForURL('/login', { timeout: 5000 }).catch(() => {});
    return true;
  }
  return false;
}

/**
 * Create a new game and wait for it to load
 */
export async function createGame(page: Page, playerName?: string, aiCount: number = 3) {
  // Capture any dialogs (alerts, confirms, prompts) and log them
  page.on('dialog', async dialog => {
    console.log(`[DIALOG DETECTED] Type: ${dialog.type()}, Message: ${dialog.message()}`);
    await dialog.accept(); // Auto-accept to prevent blocking
  });

  // Navigate to new game page
  await page.goto('/game/new');

  // Check if already in a game
  const inGame = await page.locator('button:has-text("Fold")').isVisible().catch(() => false);
  if (inGame) {
    console.log('Already in a game');
    return;
  }

  // Fill game creation form if visible
  const startButton = page.locator('button:has-text("Start Game")');
  if (await startButton.isVisible().catch(() => false)) {
    if (playerName) {
      const nameInput = page.locator('input[type="text"]').first();
      await nameInput.clear();
      await nameInput.fill(playerName);
    }

    // Select AI count if provided
    if (aiCount === 5) {
      await page.selectOption('select', { value: '5' });
    }

    // Click Start Game
    await startButton.click();

    // Wait for game to load (action buttons appear) OR error message
    try {
      await page.waitForSelector('button:has-text("Fold"), button:has-text("Check"), text=Connection Error, text=Something went wrong', {
        timeout: 15000
      });
    } catch (e) {
      // Log page content for debugging
      const content = await page.content();
      console.log('[DEBUG] Page content after game creation:', content.substring(0, 500));
      throw e;
    }
  }
}

/**
 * Take a poker action (fold, check, call, raise)
 */
export async function takeAction(page: Page, action: 'fold' | 'check' | 'call' | 'raise', amount?: number) {
  // Wait for action buttons to be enabled
  await page.waitForTimeout(1000);

  switch (action) {
    case 'fold':
      const foldBtn = page.locator('button:has-text("Fold"):not([disabled])');
      if (await foldBtn.isVisible().catch(() => false)) {
        await foldBtn.click();
      }
      break;

    case 'check':
      const checkBtn = page.locator('button:has-text("Check"):not([disabled])');
      if (await checkBtn.isVisible().catch(() => false)) {
        await checkBtn.click();
      }
      break;

    case 'call':
      const callBtn = page.locator('button:has-text("Call"):not([disabled])');
      if (await callBtn.isVisible().catch(() => false)) {
        await callBtn.click();
      }
      break;

    case 'raise':
      const raiseBtn = page.locator('button:has-text("Raise"):not([disabled])');
      if (await raiseBtn.isVisible().catch(() => false)) {
        await raiseBtn.click();
        // Wait for raise panel
        await page.waitForTimeout(500);

        if (amount) {
          // Enter custom amount if provided
          const amountInput = page.locator('input[type="range"], input[type="number"]').first();
          if (await amountInput.isVisible().catch(() => false)) {
            await amountInput.fill(amount.toString());
          }
        }

        // Click confirm raise button
        const confirmBtn = page.locator('button:has-text("Confirm"), button:has-text("Raise")').last();
        await confirmBtn.click();
      }
      break;
  }

  // Wait for action to process
  await page.waitForTimeout(1000);
}

/**
 * Wait for AI players to act
 */
export async function waitForAITurn(page: Page, maxWait: number = 10000) {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWait) {
    // Check if it's player's turn (action buttons enabled)
    const hasActions = await page.locator('button:has-text("Fold"):not([disabled]), button:has-text("Check"):not([disabled])').isVisible().catch(() => false);

    if (hasActions) {
      return true;
    }

    await page.waitForTimeout(500);
  }

  return false;
}

/**
 * Quit the current game
 */
export async function quitGame(page: Page) {
  const quitBtn = page.locator('button:has-text("Quit")');

  if (await quitBtn.isVisible().catch(() => false)) {
    await quitBtn.click();

    // Handle confirmation modal if present
    const confirmBtn = page.locator('button:has-text("Yes"), button:has-text("Confirm")');
    if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmBtn.click();
    }

    // Wait for redirect to home
    await page.waitForURL('/', { timeout: 5000 }).catch(() => {});

    return true;
  }

  return false;
}
