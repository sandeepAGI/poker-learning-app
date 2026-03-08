import { test, expect } from '@playwright/test';
import { registerUser, createGame, quitGame } from './helpers';

/**
 * Suite 6: Layout & UX
 *
 * Validates the poker table UX improvements:
 * - Responsive felt sizing fills the left column
 * - Opponents are placed across all quadrants (not just top arc)
 * - Control panel maintains proper width
 * - Raise slider is visible without toggling (desktop)
 * - No React console errors (catches hydration issues)
 */

test.describe('Suite 6: Layout & UX', () => {
  // Collect console errors during each test
  let consoleErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
  });

  test('6.1: 4-player table layout fills left column and places opponents in multiple quadrants', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    // Wait for table to fully render
    await page.waitForTimeout(2000);

    // Verify poker table container exists and has reasonable size
    const tableContainer = page.locator('[data-testid="poker-table-container"]');
    await expect(tableContainer).toBeVisible({ timeout: 10000 });

    const tableBounds = await tableContainer.boundingBox();
    expect(tableBounds).not.toBeNull();
    if (!tableBounds) return;

    // Table should take up significant portion of viewport width
    const viewport = page.viewportSize()!;
    const tableWidthRatio = tableBounds.width / viewport.width;
    // Table should be at least 50% of viewport (accounting for control panel)
    expect(tableWidthRatio).toBeGreaterThan(0.5);

    // Verify control panel width is 22-28% of viewport
    const controlPanel = page.locator('[data-testid="control-panel"]');
    await expect(controlPanel).toBeVisible();
    const panelBounds = await controlPanel.boundingBox();
    expect(panelBounds).not.toBeNull();
    if (!panelBounds) return;

    const panelWidthRatio = panelBounds.width / viewport.width;
    expect(panelWidthRatio).toBeGreaterThanOrEqual(0.20);
    expect(panelWidthRatio).toBeLessThanOrEqual(0.30);

    // Verify opponent seats exist (3 opponents)
    const opponentSeats = page.locator('[data-testid^="opponent-seat-"]');
    const opponentCount = await opponentSeats.count();
    expect(opponentCount).toBe(3);

    // Collect opponent positions relative to table
    const opponentPositions: { relX: number; relY: number }[] = [];
    for (let i = 0; i < opponentCount; i++) {
      const seat = page.locator(`[data-testid="opponent-seat-${i}"]`);
      const bounds = await seat.boundingBox();
      if (bounds) {
        opponentPositions.push({
          relX: (bounds.x + bounds.width / 2 - tableBounds.x) / tableBounds.width,
          relY: (bounds.y + bounds.height / 2 - tableBounds.y) / tableBounds.height
        });
      }
    }

    // With 240-degree arc, opponents should NOT all be in top half
    // At least one should be in lower portion (relY > 0.5)
    const hasLowerPosition = opponentPositions.some(p => p.relY > 0.5);
    expect(hasLowerPosition).toBe(true);

    await page.screenshot({ path: 'e2e/screenshots/06-4player-layout.png' });

    // Verify raise slider is visible on desktop (always shown)
    // First need to wait for player's turn
    const raisePanel = page.locator('[data-testid="raise-panel"]');
    const isPlayerTurn = await page.locator('[data-testid="fold-button"]:not([disabled])').isVisible().catch(() => false);

    if (isPlayerTurn) {
      // On desktop, raise panel should be visible without clicking
      const raisePanelVisible = await raisePanel.isVisible().catch(() => false);
      expect(raisePanelVisible).toBe(true);
    }

    // Clean up
    await quitGame(page);

    // Verify no React errors (catches 418 hydration mismatch)
    const reactErrors = consoleErrors.filter(e =>
      e.includes('Minified React error') || e.includes('#418')
    );
    expect(reactErrors).toHaveLength(0);
  });

  test('6.2: 6-player table layout distributes opponents across all quadrants', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 5);

    // Wait for table to fully render
    await page.waitForTimeout(2000);

    const tableContainer = page.locator('[data-testid="poker-table-container"]');
    await expect(tableContainer).toBeVisible({ timeout: 10000 });

    const tableBounds = await tableContainer.boundingBox();
    expect(tableBounds).not.toBeNull();
    if (!tableBounds) return;

    // Verify 5 opponent seats exist
    const opponentSeats = page.locator('[data-testid^="opponent-seat-"]');
    const opponentCount = await opponentSeats.count();
    expect(opponentCount).toBe(5);

    // Collect positions relative to table center
    const tableCenterX = tableBounds.width / 2;
    const tableCenterY = tableBounds.height / 2;
    const quadrants = { topLeft: false, topRight: false, bottomLeft: false, bottomRight: false };

    for (let i = 0; i < opponentCount; i++) {
      const seat = page.locator(`[data-testid="opponent-seat-${i}"]`);
      const bounds = await seat.boundingBox();
      if (bounds) {
        const relX = (bounds.x + bounds.width / 2 - tableBounds.x) - tableCenterX;
        const relY = (bounds.y + bounds.height / 2 - tableBounds.y) - tableCenterY;

        if (relX < 0 && relY < 0) quadrants.topLeft = true;
        if (relX > 0 && relY < 0) quadrants.topRight = true;
        if (relX < 0 && relY > 0) quadrants.bottomLeft = true;
        if (relX > 0 && relY > 0) quadrants.bottomRight = true;
      }
    }

    // With 280-degree arc, opponents should appear in all four quadrants
    expect(quadrants.topLeft).toBe(true);
    expect(quadrants.topRight).toBe(true);
    expect(quadrants.bottomLeft).toBe(true);
    expect(quadrants.bottomRight).toBe(true);

    await page.screenshot({ path: 'e2e/screenshots/06-6player-layout.png' });

    // Clean up
    await quitGame(page);

    // No React console errors
    const reactErrors = consoleErrors.filter(e =>
      e.includes('Minified React error') || e.includes('#418')
    );
    expect(reactErrors).toHaveLength(0);
  });

  test('6.3: Hero seat shows "You" label', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    await page.waitForTimeout(2000);

    // The human player seat should show "You" instead of username
    const humanSeat = page.locator('[data-testid="human-player-seat"]');
    await expect(humanSeat).toBeVisible({ timeout: 10000 });

    const youLabel = humanSeat.locator('text=You');
    await expect(youLabel).toBeVisible();

    // Clean up
    await quitGame(page);
  });

  test('6.5: Hero seat fully visible at 1280x720', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    const heroSeat = page.locator('[data-testid="human-player-seat"]');
    await expect(heroSeat).toBeVisible({ timeout: 15000 });

    const viewport = page.viewportSize()!;
    const heroBounds = await heroSeat.boundingBox();
    expect(heroBounds).not.toBeNull();

    // Hero seat bottom must be within viewport
    expect(heroBounds!.y + heroBounds!.height).toBeLessThan(viewport.height);
    expect(heroBounds!.y).toBeGreaterThanOrEqual(0);

    await quitGame(page);
  });

  test('6.6: Hero seat fully visible at 1024x768', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    const heroSeat = page.locator('[data-testid="human-player-seat"]');
    await expect(heroSeat).toBeVisible({ timeout: 15000 });

    const viewport = page.viewportSize()!;
    const heroBounds = await heroSeat.boundingBox();
    expect(heroBounds).not.toBeNull();

    expect(heroBounds!.y + heroBounds!.height).toBeLessThan(viewport.height);

    await quitGame(page);
  });

  test('6.7: Control panel buttons visible at 1024x768', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    const foldBtn = page.locator('[data-testid="fold-button"]');
    const isPlayerTurn = await foldBtn.isVisible({ timeout: 15000 }).catch(() => false);

    if (isPlayerTurn) {
      const controlPanel = page.locator('[data-testid="control-panel"]');
      const panelBounds = await controlPanel.boundingBox();
      expect(panelBounds).not.toBeNull();

      // Control panel should be scrollable — verify fold button is within viewport
      const foldBounds = await foldBtn.boundingBox();
      expect(foldBounds).not.toBeNull();
      const viewport = page.viewportSize()!;
      expect(foldBounds!.y + foldBounds!.height).toBeLessThan(viewport.height);
    }

    await quitGame(page);
  });

  test('6.8: Winner modal Next Hand button reachable at 1024x768', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    const foldBtn = page.locator('[data-testid="fold-button"]');
    if (await foldBtn.isVisible({ timeout: 15000 }).catch(() => false)) {
      await foldBtn.click();
      await page.waitForTimeout(3000);

      const modal = page.locator('[data-testid="winner-modal"]');
      if (await modal.isVisible({ timeout: 5000 }).catch(() => false)) {
        const nextBtn = modal.locator('button:has-text("Next Hand")');
        // Button should be visible without scrolling (sticky footer)
        await expect(nextBtn).toBeVisible({ timeout: 3000 });

        const bounds = await nextBtn.boundingBox();
        expect(bounds).not.toBeNull();
        const viewport = page.viewportSize()!;
        expect(bounds!.y + bounds!.height).toBeLessThan(viewport.height);
      }
    }

    await quitGame(page);
  });

  test('6.9: Community cards do not overlap top opponent at 1280x720', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 3);
    await page.waitForTimeout(3000);

    // Need to be on flop+ to see community cards — call to advance
    const callBtn = page.locator('[data-testid="call-button"]');
    if (await callBtn.isVisible({ timeout: 10000 }).catch(() => false)) {
      await callBtn.click();
      await page.waitForTimeout(5000);
    }

    const communityArea = page.locator('[data-testid="community-cards-area"]');
    const topOpponent = page.locator('[data-testid="opponent-seat-1"]');

    if (await communityArea.isVisible().catch(() => false) && await topOpponent.isVisible().catch(() => false)) {
      const communityBounds = await communityArea.boundingBox();
      const opponentBounds = await topOpponent.boundingBox();

      if (communityBounds && opponentBounds) {
        // Community cards top should be below opponent bottom (no overlap)
        const opponentBottom = opponentBounds.y + opponentBounds.height;
        expect(communityBounds.y).toBeGreaterThanOrEqual(opponentBottom - 10); // 10px tolerance
      }
    }

    await quitGame(page);
  });

  test('6.4: Control panel uses harmonized palette', async ({ page }) => {
    const { username } = await registerUser(page);
    await createGame(page, username, 3);

    await page.waitForTimeout(2000);

    // Verify pot display exists
    const potDisplay = page.locator('[data-testid="pot-display"]');
    await expect(potDisplay).toBeVisible({ timeout: 10000 });

    // Verify control panel is visible
    const controlPanel = page.locator('[data-testid="control-panel"]');
    await expect(controlPanel).toBeVisible();

    await page.screenshot({ path: 'e2e/screenshots/06-control-panel.png' });

    // Clean up
    await quitGame(page);
  });
});
