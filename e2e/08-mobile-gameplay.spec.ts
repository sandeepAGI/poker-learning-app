import { test, expect } from '@playwright/test';
import { registerUser, createGame, quitGame, dismissMobileGate } from './helpers';

/**
 * Suite 8: Mobile Gameplay
 *
 * Validates the mobile experience after dismissing the mobile gate.
 * Tests run at iPhone viewport sizes (375x812 or 390x844).
 */

test.describe('Suite 8: Mobile Gameplay', () => {
  test('8.1: Mobile gate appears and can be dismissed', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    // Gate should appear
    await expect(page.locator('[data-testid="mobile-gate"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('h1:has-text("Optimized for Larger Screens")')).toBeVisible();

    // Dismiss it
    await page.locator('[data-testid="mobile-gate-continue"]').click();
    await expect(page.locator('[data-testid="mobile-gate"]')).not.toBeVisible();

    // App content should be visible
    const loginVisible = await page.locator('input#username').isVisible({ timeout: 5000 }).catch(() => false);
    const authVisible = await page.locator('text=Start New Game').isVisible().catch(() => false);
    expect(loginVisible || authVisible).toBe(true);
  });

  test('8.2: Login form usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);

    // Check login form is visible and usable
    const usernameInput = page.locator('input#username');
    if (await usernameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await usernameInput.fill('mobileuser');
      await expect(usernameInput).toHaveValue('mobileuser');

      const passwordInput = page.locator('input#password');
      await passwordInput.fill('TestPass123!');
      await expect(passwordInput).toHaveValue('TestPass123!');
    }
  });

  test('8.3: Game creation works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);

    // Navigate to game creation
    await page.goto('/game/new');
    await dismissMobileGate(page);

    // Game creation page should be visible
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible({ timeout: 10000 });
  });

  test('8.4: Table renders without horizontal scroll', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Check no horizontal overflow
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 5); // 5px tolerance

    await quitGame(page);
  });

  test('8.5: Action buttons visible without scrolling', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Wait for game to load and check for mobile action buttons
    // The mobile bottom bar should be visible
    const mobileActionBar = page.locator('[data-testid="mobile-fold-button"], [data-testid="mobile-call-button"], [data-testid="mobile-next-hand-button"]').first();

    // Also check desktop buttons exist (for non-mobile)
    const desktopFold = page.locator('[data-testid="fold-button"]');

    // At mobile viewport, the mobile buttons or waiting text should be visible
    const hasMobileActions = await mobileActionBar.isVisible({ timeout: 10000 }).catch(() => false);
    const hasWaiting = await page.locator('text=Waiting for other players').isVisible().catch(() => false);
    const hasNextHand = await page.locator('[data-testid="mobile-next-hand-button"]').isVisible().catch(() => false);

    // At least one mobile element should be visible (actions, waiting, or next hand)
    expect(hasMobileActions || hasWaiting || hasNextHand).toBe(true);

    // Desktop control panel should be hidden on mobile
    const controlPanel = page.locator('[data-testid="control-panel"]');
    await expect(controlPanel).not.toBeVisible();

    await quitGame(page);
  });

  test('8.6: Pot display visible on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Mobile pot display should be visible in the bottom bar
    const mobilePot = page.locator('[data-testid="mobile-pot-display"]');
    await expect(mobilePot).toBeVisible({ timeout: 10000 });

    await quitGame(page);
  });

  test('8.7: Raise panel opens and is usable', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Wait for it to be player's turn
    const raiseButton = page.locator('[data-testid="mobile-raise-button"]');
    const isPlayerTurn = await raiseButton.isVisible({ timeout: 15000 }).catch(() => false);

    if (isPlayerTurn) {
      // Click raise to open panel
      await raiseButton.click();

      // Raise panel should slide up — look for the visible Confirm Raise button
      // (desktop one is hidden, mobile one is visible)
      const confirmBtns = page.locator('button:has-text("Confirm Raise")');
      const count = await confirmBtns.count();
      let foundVisible = false;
      for (let i = 0; i < count; i++) {
        if (await confirmBtns.nth(i).isVisible().catch(() => false)) {
          foundVisible = true;
          break;
        }
      }
      expect(foundVisible).toBe(true);
    }
    // If not player's turn, that's OK — skip raise test

    await quitGame(page);
  });

  test('8.8: Player seats don\'t overlap - 4 player game', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page, undefined, 3); // 3 AI opponents = 4 players
    await dismissMobileGate(page);

    // Check that opponent seats are present
    const seat0 = page.locator('[data-testid="opponent-seat-0"]');
    const seat1 = page.locator('[data-testid="opponent-seat-1"]');
    const seat2 = page.locator('[data-testid="opponent-seat-2"]');

    await expect(seat0).toBeVisible({ timeout: 10000 });
    await expect(seat1).toBeVisible();
    await expect(seat2).toBeVisible();

    // Get bounding boxes and verify no major overlaps
    const box0 = await seat0.boundingBox();
    const box1 = await seat1.boundingBox();
    const box2 = await seat2.boundingBox();

    expect(box0).toBeTruthy();
    expect(box1).toBeTruthy();
    expect(box2).toBeTruthy();

    // Verify seats are not stacked at identical positions
    if (box0 && box1 && box2) {
      // At least the left values should differ by some amount
      const positions = [box0.x, box1.x, box2.x].sort((a, b) => a - b);
      const minSpread = positions[positions.length - 1] - positions[0];
      expect(minSpread).toBeGreaterThan(20); // At least 20px spread
    }

    await quitGame(page);
  });

  test('8.9: Header buttons don\'t overflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // All header buttons should be visible
    const header = page.locator('[data-testid="poker-table-header"]');
    await expect(header).toBeVisible({ timeout: 10000 });

    const settingsBtn = page.locator('[data-testid="settings-button"]');
    const helpBtn = page.locator('[data-testid="help-button"]');
    const quitBtn = page.locator('[data-testid="quit-button"]');

    await expect(settingsBtn).toBeVisible();
    await expect(helpBtn).toBeVisible();
    await expect(quitBtn).toBeVisible();

    // Verify header doesn't exceed viewport width
    const headerBox = await header.boundingBox();
    expect(headerBox).toBeTruthy();
    if (headerBox) {
      expect(headerBox.x + headerBox.width).toBeLessThanOrEqual(375 + 5);
    }

    await quitGame(page);
  });

  test('8.10: Settings dropdown doesn\'t clip', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Open settings
    const settingsBtn = page.locator('[data-testid="settings-button"]');
    await expect(settingsBtn).toBeVisible({ timeout: 10000 });
    await settingsBtn.click();

    // Settings menu should be visible
    const settingsMenu = page.locator('[data-testid="settings-menu"]');
    await expect(settingsMenu).toBeVisible({ timeout: 3000 });

    // Verify dropdown is within viewport
    const menuBox = await settingsMenu.boundingBox();
    expect(menuBox).toBeTruthy();
    if (menuBox) {
      expect(menuBox.x).toBeGreaterThanOrEqual(0);
      expect(menuBox.x + menuBox.width).toBeLessThanOrEqual(375 + 5);
    }

    // Close settings
    await settingsBtn.click();
    await quitGame(page);
  });

  test('8.11: Full gameplay loop - create, play 2 hands, quit', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await dismissMobileGate(page);
    await registerUser(page);
    await createGame(page);
    await dismissMobileGate(page);

    // Play hand 1: fold if it's our turn
    const foldBtn = page.locator('[data-testid="mobile-fold-button"]');
    const isOurTurn = await foldBtn.isVisible({ timeout: 15000 }).catch(() => false);

    if (isOurTurn) {
      await foldBtn.click();
      // Wait for next hand to start
      await page.waitForTimeout(3000);
    } else {
      // Wait for hand to complete (AI actions)
      await page.waitForTimeout(5000);
    }

    // Check for next-hand or winner modal
    const nextHandBtn = page.locator('[data-testid="mobile-next-hand-button"]');
    const winnerModal = page.locator('[data-testid="winner-modal"]');
    const hasNextHand = await nextHandBtn.isVisible({ timeout: 10000 }).catch(() => false);
    const hasWinnerModal = await winnerModal.isVisible().catch(() => false);

    if (hasWinnerModal) {
      // Dismiss winner modal
      await page.locator('[data-testid="winner-modal"] button:has-text("Next Hand")').click();
      await page.waitForTimeout(2000);
    } else if (hasNextHand) {
      await nextHandBtn.click();
      await page.waitForTimeout(2000);
    }

    // Play hand 2: fold again if possible
    const foldBtn2 = page.locator('[data-testid="mobile-fold-button"]');
    if (await foldBtn2.isVisible({ timeout: 10000 }).catch(() => false)) {
      await foldBtn2.click();
      await page.waitForTimeout(3000);
    }

    // Quit game
    await quitGame(page);

    // Verify we're back at home
    await expect(page).toHaveURL('/', { timeout: 10000 });
  });
});
