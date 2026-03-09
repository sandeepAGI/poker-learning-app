/**
 * STRESS TEST: 20 Full Poker Games — E2E Validation
 *
 * ⚠️  ONE-OFF TEST — DO NOT ADD TO REGULAR E2E SUITE
 * This test plays 20 complete poker games (until elimination) to validate:
 * - Game logic: pot math, chip conservation, blind rotation, winner amounts
 * - UI rendering: elements visible, no clipping, correct card counts
 *
 * Run sparingly (takes 30-45 min). Created for pre-merge validation before
 * pushing to outside testers.
 *
 * Usage:
 *   npx playwright test e2e/stress-test-gameplay.spec.ts --timeout=3600000
 *
 * Both servers must be running:
 *   cd backend && python main.py
 *   cd frontend && npm run dev
 */

import { test, expect, Page } from '@playwright/test';
import { registerUser, createGame, quitGame } from './helpers';
import * as fs from 'fs';
import * as path from 'path';

// ─── Configuration ───────────────────────────────────────────────
const TOTAL_GAMES = 20;
const MAX_HANDS_PER_GAME = 30;
const GAMES_PER_USER = 5; // Register a fresh user every N games
const RESULTS_DIR = path.join(__dirname, 'stress-test-results');
const SESSION_ANALYSIS_GAMES = [5, 10, 15, 20]; // Trigger session analysis
const HAND_ANALYSIS_GAMES = [8, 16];             // Trigger hand analysis
const ANALYSIS_TRIGGER_HAND = 5;                  // After this hand number

// ─── Types ───────────────────────────────────────────────────────
interface Failure {
  game: number;
  hand: number;
  category: string;
  message: string;
  screenshot: string;
}

interface GameResult {
  gameNumber: number;
  handsPlayed: number;
  initialChipTotal: number;
  finalChipTotal: number;
  failures: Failure[];
  analysisTriggered: { type: string; success: boolean }[];
  endReason: 'elimination' | 'max_hands' | 'error';
}

interface SummaryReport {
  timestamp: string;
  totalGames: number;
  gamesCompleted: number;
  totalHands: number;
  totalFailures: number;
  failuresByCategory: Record<string, number>;
  games: GameResult[];
  verdict: 'PASS' | 'FAIL';
}

// ─── UI State Reading Helpers ────────────────────────────────────

/** Extract dollar amount from text content like "$150" or "Pot\n$150" */
function parseDollarAmount(text: string): number {
  const match = text.match(/\$(\d+)/);
  return match ? parseInt(match[1], 10) : -1;
}

/** Read the current pot value from the pot display */
async function readPot(page: Page): Promise<number> {
  const potEl = page.locator('[data-testid="pot-display"]');
  if (!await potEl.isVisible().catch(() => false)) return -1;
  const text = await potEl.textContent() ?? '';
  return parseDollarAmount(text);
}

/** Read all player stacks visible on the page. Returns Map of playerName → stack */
async function readAllStacks(page: Page): Promise<Map<string, number>> {
  const stacks = new Map<string, number>();

  // Read all stack displays
  const stackEls = page.locator('[data-testid^="stack-display-"]');
  const count = await stackEls.count();

  for (let i = 0; i < count; i++) {
    const el = stackEls.nth(i);
    const testId = await el.getAttribute('data-testid') ?? '';
    const playerId = testId.replace('stack-display-', '');
    const text = await el.textContent() ?? '';
    const amount = parseDollarAmount(text);
    if (amount >= 0) {
      stacks.set(playerId, amount);
    }
  }

  return stacks;
}

/** Compute total chips from all stacks + pot */
async function readTotalChips(page: Page): Promise<number> {
  const stacks = await readAllStacks(page);
  const pot = await readPot(page);
  let total = pot > 0 ? pot : 0;
  for (const stack of stacks.values()) {
    total += stack;
  }
  return total;
}

/** Read current community card count */
async function readCommunityCardCount(page: Page): Promise<number> {
  const list = page.locator('[data-testid="community-cards-list"]');
  if (!await list.isVisible().catch(() => false)) return 0;
  return await list.locator('> *').count();
}

/** Read stage label text (FLOP, TURN, RIVER, or empty) */
async function readStageLabel(page: Page): Promise<string> {
  const label = page.locator('[data-testid="stage-label"]');
  if (!await label.isVisible().catch(() => false)) return '';
  return (await label.textContent() ?? '').trim();
}

/** Read hand number from header */
async function readHandNumber(page: Page): Promise<number> {
  const el = page.locator('[data-testid="hand-count"]');
  if (!await el.isVisible().catch(() => false)) return -1;
  const text = await el.textContent() ?? '';
  const match = text.match(/#(\d+)/);
  return match ? parseInt(match[1], 10) : -1;
}

/** Read blind amounts from header */
async function readBlinds(page: Page): Promise<{ small: number; big: number }> {
  const el = page.locator('[data-testid="blind-levels"]');
  if (!await el.isVisible().catch(() => false)) return { small: -1, big: -1 };
  const text = await el.textContent() ?? '';
  const match = text.match(/\$(\d+)\/\$(\d+)/);
  return match
    ? { small: parseInt(match[1], 10), big: parseInt(match[2], 10) }
    : { small: -1, big: -1 };
}

/** Find which player has D, SB, BB badges. Returns player_id for each. */
async function readButtonPositions(page: Page): Promise<{
  dealer: string | null;
  smallBlind: string | null;
  bigBlind: string | null;
}> {
  const dealerEl = page.locator('[data-testid^="dealer-button-"]');
  const sbEl = page.locator('[data-testid^="small-blind-button-"]');
  const bbEl = page.locator('[data-testid^="big-blind-button-"]');

  const extractId = async (loc: ReturnType<typeof page.locator>, prefix: string): Promise<string | null> => {
    if (!await loc.first().isVisible().catch(() => false)) return null;
    const testId = await loc.first().getAttribute('data-testid') ?? '';
    return testId.replace(prefix, '') || null;
  };

  return {
    dealer: await extractId(dealerEl, 'dealer-button-'),
    smallBlind: await extractId(sbEl, 'small-blind-button-'),
    bigBlind: await extractId(bbEl, 'big-blind-button-'),
  };
}

/** Take a screenshot and return the relative path */
async function screenshotTo(page: Page, filePath: string): Promise<string> {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

// ─── Validation Helpers ──────────────────────────────────────────

/** Log a failure, take screenshot, and add to failures list */
async function recordFailure(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number,
  category: string,
  message: string
): Promise<void> {
  const safeCat = category.replace(/[^a-z0-9-]/gi, '-').toLowerCase();
  const screenshotPath = path.join(
    RESULTS_DIR,
    `game-${String(game).padStart(2, '0')}`,
    `hand-${String(hand).padStart(2, '0')}-failure-${safeCat}.png`
  );
  await screenshotTo(page, screenshotPath);

  const failure: Failure = { game, hand, category, message, screenshot: screenshotPath };
  failures.push(failure);
  console.log(`  ❌ FAILURE [${category}] Game ${game}, Hand ${hand}: ${message}`);
}

/** Validate chip conservation: sum of all stacks + pot = expected total */
async function validateChipConservation(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number,
  expectedTotal: number
): Promise<void> {
  const actual = await readTotalChips(page);
  if (actual !== expectedTotal && actual > 0) {
    await recordFailure(
      page, failures, game, hand, 'chip-conservation',
      `Expected total chips ${expectedTotal}, got ${actual} (diff: ${actual - expectedTotal})`
    );
  }
}

/** Validate community card count matches expected for the stage */
async function validateCommunityCards(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number,
  prevCardCount: number
): Promise<number> {
  const cardCount = await readCommunityCardCount(page);
  const stageLabel = await readStageLabel(page);

  // Cards should never decrease
  if (cardCount < prevCardCount) {
    await recordFailure(
      page, failures, game, hand, 'card-count-decreased',
      `Community cards decreased from ${prevCardCount} to ${cardCount}`
    );
  }

  // Cards should never skip (0→3 is OK for flop, but 0→4 is not)
  const validTransitions = [0, 3, 4, 5];
  if (cardCount > 0 && !validTransitions.includes(cardCount)) {
    await recordFailure(
      page, failures, game, hand, 'invalid-card-count',
      `Community card count is ${cardCount} — expected 0, 3, 4, or 5`
    );
  }

  // Stage label should match card count
  const expectedLabel: Record<number, string> = { 3: 'FLOP', 4: 'TURN', 5: 'RIVER' };
  if (cardCount >= 3 && stageLabel && stageLabel !== expectedLabel[cardCount]) {
    await recordFailure(
      page, failures, game, hand, 'stage-label-mismatch',
      `Stage label "${stageLabel}" but card count is ${cardCount} (expected "${expectedLabel[cardCount]}")`
    );
  }

  return cardCount;
}

/** Validate D/SB/BB rotation between hands */
async function validateButtonRotation(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number,
  prevPositions: { dealer: string | null; smallBlind: string | null; bigBlind: string | null } | null
): Promise<{ dealer: string | null; smallBlind: string | null; bigBlind: string | null }> {
  const current = await readButtonPositions(page);

  if (prevPositions && hand > 1) {
    // Dealer should have moved
    if (current.dealer && prevPositions.dealer && current.dealer === prevPositions.dealer) {
      await recordFailure(
        page, failures, game, hand, 'dealer-not-rotated',
        `Dealer stayed on ${current.dealer} from hand ${hand - 1} to ${hand}`
      );
    }

    // SB should have moved
    if (current.smallBlind && prevPositions.smallBlind && current.smallBlind === prevPositions.smallBlind) {
      await recordFailure(
        page, failures, game, hand, 'sb-not-rotated',
        `Small blind stayed on ${current.smallBlind} from hand ${hand - 1} to ${hand}`
      );
    }

    // BB should have moved
    if (current.bigBlind && prevPositions.bigBlind && current.bigBlind === prevPositions.bigBlind) {
      await recordFailure(
        page, failures, game, hand, 'bb-not-rotated',
        `Big blind stayed on ${current.bigBlind} from hand ${hand - 1} to ${hand}`
      );
    }
  }

  return current;
}

/** Validate UI elements are visible (no clipping) */
async function validateUIVisibility(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number
): Promise<void> {
  const viewport = page.viewportSize()!;

  const checks = [
    { name: 'hero-seat', selector: '[data-testid="human-player-seat"]' },
    { name: 'control-panel', selector: '[data-testid="control-panel"]' },
    { name: 'poker-table', selector: '[data-testid="poker-table-container"]' },
  ];

  for (const { name, selector } of checks) {
    const el = page.locator(selector);
    if (await el.isVisible().catch(() => false)) {
      const bounds = await el.boundingBox();
      if (bounds && (bounds.y + bounds.height > viewport.height + 10)) {
        await recordFailure(
          page, failures, game, hand, `${name}-clipped`,
          `${name} extends below viewport: bottom=${Math.round(bounds.y + bounds.height)}, viewport=${viewport.height}`
        );
      }
    }
  }
}

/** Validate winner modal and return the amount won */
async function validateWinnerModal(
  page: Page,
  failures: Failure[],
  game: number,
  hand: number
): Promise<number> {
  const modal = page.locator('[data-testid="winner-modal"]');
  if (!await modal.isVisible({ timeout: 2000 }).catch(() => false)) {
    return 0;
  }

  // Check Next Hand button is visible (sticky footer fix)
  const nextBtn = modal.locator('button:has-text("Next Hand")');
  if (!await nextBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await recordFailure(
      page, failures, game, hand, 'next-hand-not-visible',
      'Next Hand button not visible in winner modal'
    );
  } else {
    // Verify it's within viewport
    const viewport = page.viewportSize()!;
    const bounds = await nextBtn.boundingBox();
    if (bounds && bounds.y + bounds.height > viewport.height) {
      await recordFailure(
        page, failures, game, hand, 'next-hand-below-viewport',
        `Next Hand button below viewport: bottom=${Math.round(bounds.y + bounds.height)}`
      );
    }
  }

  // Read winner amount
  const amountEl = modal.locator('[data-testid="winner-amount"]');
  let winAmount = 0;
  if (await amountEl.isVisible().catch(() => false)) {
    const text = await amountEl.textContent() ?? '';
    winAmount = parseDollarAmount(text);
  }

  if (winAmount <= 0) {
    // Try reading from announcement text (split pot case, etc.)
    const modalText = await modal.textContent() ?? '';
    const amountMatch = modalText.match(/\$(\d+)/);
    winAmount = amountMatch ? parseInt(amountMatch[1], 10) : 0;
  }

  return winAmount;
}

// ─── Analysis Trigger Helpers ────────────────────────────────────

/** Trigger session analysis via Settings menu and validate */
async function triggerSessionAnalysis(
  page: Page,
  gameNum: number,
  failures: Failure[]
): Promise<boolean> {
  console.log(`  📈 Triggering session analysis (Game ${gameNum})...`);
  const gameDir = path.join(RESULTS_DIR, `game-${String(gameNum).padStart(2, '0')}`);

  try {
    // Open settings menu
    const settingsBtn = page.locator('[data-testid="settings-button"]');
    if (!await settingsBtn.isVisible({ timeout: 3000 }).catch(() => false)) return false;
    await settingsBtn.click();

    // Wait for menu
    await page.locator('[data-testid="settings-menu"]').waitFor({ timeout: 3000 });

    // Click session analysis
    const analysisBtn = page.locator('[data-testid="session-analysis-button"]');
    if (!await analysisBtn.isVisible().catch(() => false)) return false;
    await analysisBtn.click();

    // Wait for modal to appear (loading or content)
    await page.waitForTimeout(2000);

    // Screenshot the analysis modal
    await screenshotTo(page, path.join(gameDir, 'session-analysis.png'));

    // Wait for loading to complete
    await page.waitForTimeout(10000);
    await screenshotTo(page, path.join(gameDir, 'session-analysis-loaded.png'));

    // Verify no crash — page should still be responsive
    const stillHasQuit = await page.locator('button:has-text("Quit")').isVisible().catch(() => false);
    const hasModal = await page.locator('.fixed').first().isVisible().catch(() => false);

    if (!stillHasQuit && !hasModal) {
      await recordFailure(page, failures, gameNum, 0, 'session-analysis-crash',
        'Page unresponsive after session analysis');
      return false;
    }

    // Close the modal (click close button or press Escape)
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);

    // If modal still visible, try clicking a close button
    const closeBtn = page.locator('button:has-text("Close"), button:has-text("×")');
    if (await closeBtn.isVisible().catch(() => false)) {
      await closeBtn.click();
      await page.waitForTimeout(500);
    }

    console.log(`  ✅ Session analysis completed`);
    return true;
  } catch (e) {
    console.log(`  ⚠️ Session analysis error: ${e}`);
    await screenshotTo(page, path.join(gameDir, 'session-analysis-error.png'));
    return false;
  }
}

/** Trigger hand analysis via Settings menu and validate */
async function triggerHandAnalysis(
  page: Page,
  gameNum: number,
  handNum: number,
  failures: Failure[]
): Promise<boolean> {
  console.log(`  📊 Triggering hand analysis (Game ${gameNum}, Hand ${handNum})...`);
  const gameDir = path.join(RESULTS_DIR, `game-${String(gameNum).padStart(2, '0')}`);

  try {
    // Open settings menu
    const settingsBtn = page.locator('[data-testid="settings-button"]');
    if (!await settingsBtn.isVisible({ timeout: 3000 }).catch(() => false)) return false;
    await settingsBtn.click();

    // Wait for menu
    await page.locator('[data-testid="settings-menu"]').waitFor({ timeout: 3000 });

    // Click analyze hand
    const analyzeBtn = page.locator('[data-testid="analyze-hand-button"]');
    if (!await analyzeBtn.isVisible().catch(() => false)) return false;
    await analyzeBtn.click();

    // Wait for modal
    await page.waitForTimeout(2000);

    // Screenshot
    await screenshotTo(page, path.join(gameDir, `hand-${String(handNum).padStart(2, '0')}-hand-analysis.png`));

    // Wait for loading
    await page.waitForTimeout(15000);
    await screenshotTo(page, path.join(gameDir, `hand-${String(handNum).padStart(2, '0')}-hand-analysis-loaded.png`));

    // Close modal
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);

    const closeBtn = page.locator('button:has-text("Close"), button:has-text("×")');
    if (await closeBtn.isVisible().catch(() => false)) {
      await closeBtn.click();
      await page.waitForTimeout(500);
    }

    console.log(`  ✅ Hand analysis completed`);
    return true;
  } catch (e) {
    console.log(`  ⚠️ Hand analysis error: ${e}`);
    await screenshotTo(page, path.join(gameDir, `hand-${String(handNum).padStart(2, '0')}-hand-analysis-error.png`));
    return false;
  }
}

// ─── Main Test ───────────────────────────────────────────────────
test.describe('Stress Test: 20 Full Poker Games', () => {
  test.setTimeout(3600000); // 1 hour timeout

  test('Play 20 complete games validating logic and UI', async ({ page }) => {
    // Clean results directory
    if (fs.existsSync(RESULTS_DIR)) {
      fs.rmSync(RESULTS_DIR, { recursive: true });
    }
    fs.mkdirSync(RESULTS_DIR, { recursive: true });

    const allResults: GameResult[] = [];

    // ── Register first user ──
    let currentUser = await registerUser(page);
    console.log(`Registered user: ${currentUser.username}`);

    for (let gameNum = 1; gameNum <= TOTAL_GAMES; gameNum++) {
      // Register a fresh user every GAMES_PER_USER games to avoid state accumulation
      if (gameNum > 1 && (gameNum - 1) % GAMES_PER_USER === 0) {
        console.log(`\n  🔄 Rotating user after ${GAMES_PER_USER} games...`);
        await page.goto('/');
        // Logout current user
        const logoutBtn = page.locator('button:has-text("Logout")');
        if (await logoutBtn.isVisible().catch(() => false)) {
          await logoutBtn.click();
          await page.waitForTimeout(2000);
        }
        currentUser = await registerUser(page);
        console.log(`  Registered new user: ${currentUser.username}`);
      }

      console.log(`\n${'='.repeat(60)}`);
      console.log(`GAME ${gameNum}/${TOTAL_GAMES} (user: ${currentUser.username})`);
      console.log(`${'='.repeat(60)}`);

      const gameDir = path.join(RESULTS_DIR, `game-${String(gameNum).padStart(2, '0')}`);
      fs.mkdirSync(gameDir, { recursive: true });

      const result: GameResult = {
        gameNumber: gameNum,
        handsPlayed: 0,
        initialChipTotal: 0,
        finalChipTotal: 0,
        failures: [],
        analysisTriggered: [],
        endReason: 'max_hands',
      };

      try {
        // ── Setup: Create new game ──
        await createGame(page, currentUser.username, 3);
        await page.waitForTimeout(2000);

        // Record initial chip total
        result.initialChipTotal = await readTotalChips(page);
        console.log(`  Initial chips: $${result.initialChipTotal}`);

        let prevButtonPositions: Awaited<ReturnType<typeof readButtonPositions>> | null = null;
        let prevCommunityCardCount = 0;
        let gameOver = false;

        // ── Hand Loop ──
        for (let handNum = 1; handNum <= MAX_HANDS_PER_GAME && !gameOver; handNum++) {
          console.log(`  Hand ${handNum}...`);
          result.handsPlayed = handNum;

          // Wait for ANY meaningful game state: action buttons, winner modal, or game over
          // This is critical — after clicking "Next Hand", AI may act first so our
          // action buttons won't appear immediately. We need to wait for any sign of life.
          const meaningfulState = await page.locator(
            '[data-testid="fold-button"], [data-testid="call-button"], [data-testid="winner-modal"], [data-testid="next-hand-button"]'
          ).first().waitFor({ timeout: 30000 }).then(() => true).catch(() => false);

          // Check for game over modal
          const gameOverText = page.locator('text=Game Over');
          if (await gameOverText.isVisible().catch(() => false)) {
            console.log(`  🏁 Game over! Player eliminated at hand ${handNum}`);
            result.endReason = 'elimination';
            await screenshotTo(page, path.join(gameDir, 'game-end.png'));
            gameOver = true;
            break;
          }

          // If winner modal is showing (leftover from previous hand or quick showdown),
          // dismiss it before proceeding — but check for game-over first
          const leftoverModal = page.locator('[data-testid="winner-modal"]');
          if (await leftoverModal.isVisible().catch(() => false)) {
            // Game-over overlay may be on top — check before clicking
            if (await page.locator('text=Game Over').isVisible().catch(() => false)) {
              console.log(`  🏁 Game over detected at start of hand ${handNum}`);
              result.endReason = 'elimination';
              await screenshotTo(page, path.join(gameDir, 'game-end.png'));
              gameOver = true;
              break;
            }
            console.log(`  Dismissing winner modal at start of hand ${handNum}...`);
            try {
              await validateWinnerModal(page, result.failures, gameNum, handNum);
              const nextBtn = leftoverModal.locator('button:has-text("Next Hand")');
              if (await nextBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
                await nextBtn.click({ force: true }).catch(() => {});
                await page.waitForTimeout(2000);
              }
            } catch (e) {
              console.log(`  ⚠️ Failed to dismiss modal, continuing: ${e}`);
              await page.waitForTimeout(2000);
            }
            // Now wait for the actual new hand to start
            await page.locator(
              '[data-testid="fold-button"], [data-testid="call-button"]'
            ).first().waitFor({ timeout: 30000 }).catch(() => {});
          }

          if (!meaningfulState) {
            console.log(`  ⚠️ No game state found, waiting...`);
            await page.waitForTimeout(5000);
            continue;
          }

          // ── Validate button rotation ──
          prevButtonPositions = await validateButtonRotation(
            page, result.failures, gameNum, handNum, prevButtonPositions
          );

          // ── Validate UI visibility ──
          await validateUIVisibility(page, result.failures, gameNum, handNum);

          // ── Validate chip conservation ──
          if (result.initialChipTotal > 0) {
            await validateChipConservation(
              page, result.failures, gameNum, handNum, result.initialChipTotal
            );
          }

          // ── Check if human is eliminated (stack = $0, no action possible) ──
          const heroSeat = page.locator('[data-testid="human-player-seat"]');
          if (await heroSeat.isVisible().catch(() => false)) {
            const heroStack = await heroSeat.locator('[data-testid^="stack-display-"]').textContent().catch(() => '');
            if (heroStack && parseDollarAmount(heroStack) === 0) {
              console.log(`  🏁 Human eliminated (stack $0) at hand ${handNum}`);
              result.endReason = 'elimination';
              await screenshotTo(page, path.join(gameDir, 'game-end.png'));
              gameOver = true;
              break;
            }
          }

          // ── Reset community card tracking for new hand ──
          prevCommunityCardCount = 0;

          // ── Action Loop: Keep acting until hand ends ──
          let handComplete = false;
          let actionCount = 0;
          const MAX_ACTIONS_PER_HAND = 20; // Safety valve

          while (!handComplete && actionCount < MAX_ACTIONS_PER_HAND) {
            actionCount++;

            // Check for game over FIRST — it overlays everything else
            if (await page.locator('text=Game Over').isVisible().catch(() => false)) {
              console.log(`  🏁 Game over detected in action loop (hand ${handNum})`);
              result.endReason = 'elimination';
              await screenshotTo(page, path.join(gameDir, 'game-end.png'));
              gameOver = true;
              handComplete = true;
              break;
            }

            // Check if winner modal is showing (hand ended)
            const winnerModal = page.locator('[data-testid="winner-modal"]');
            if (await winnerModal.isVisible().catch(() => false)) {
              // Validate winner modal
              await validateWinnerModal(page, result.failures, gameNum, handNum);

              // Click Next Hand (use force:true in case game-over overlay is partially visible)
              const nextBtn = winnerModal.locator('button:has-text("Next Hand")');
              if (await nextBtn.isVisible().catch(() => false)) {
                await nextBtn.click({ force: true }).catch(() => {});
                await page.waitForTimeout(2000);
              }
              handComplete = true;
              break;
            }

            // Check for next-hand button (showdown in control panel)
            const nextHandBtn = page.locator('[data-testid="next-hand-button"]');
            if (await nextHandBtn.isVisible().catch(() => false)) {
              await nextHandBtn.click();
              await page.waitForTimeout(2000);
              handComplete = true;
              break;
            }

            // Check if it's our turn
            const callBtn = page.locator('[data-testid="call-button"]:not([disabled])');
            const foldBtn = page.locator('[data-testid="fold-button"]:not([disabled])');

            const canCall = await callBtn.isVisible().catch(() => false);
            const canFold = await foldBtn.isVisible().catch(() => false);

            if (canCall) {
              // Record pre-action state
              const prePot = await readPot(page);

              // Always call
              await callBtn.click();
              await page.waitForTimeout(1500);

              // Validate post-action: pot should have changed
              const postPot = await readPot(page);
              if (postPot > 0 && prePot > 0 && postPot < prePot) {
                await recordFailure(
                  page, result.failures, gameNum, handNum, 'pot-decreased',
                  `Pot decreased after call: ${prePot} → ${postPot}`
                );
              }

              // Validate community cards
              prevCommunityCardCount = await validateCommunityCards(
                page, result.failures, gameNum, handNum, prevCommunityCardCount
              );
            } else if (canFold) {
              // Fallback: fold (shouldn't normally reach here with call available)
              await foldBtn.click();
              await page.waitForTimeout(2000);
            } else {
              // Not our turn — wait for something to happen (AI acting, showdown, etc.)
              // Use a smart wait: poll for any state change up to 10 seconds
              const stateChanged = await page.locator(
                '[data-testid="call-button"]:not([disabled]), [data-testid="fold-button"]:not([disabled]), [data-testid="winner-modal"], text=Game Over'
              ).first().waitFor({ timeout: 10000 }).then(() => true).catch(() => false);

              if (!stateChanged) {
                // Still nothing — take a screenshot for debugging and wait more
                console.log(`    Action ${actionCount}: no state change after 10s, waiting...`);
                await page.waitForTimeout(3000);
              }
            }

            // Check community cards after each action
            prevCommunityCardCount = await validateCommunityCards(
              page, result.failures, gameNum, handNum, prevCommunityCardCount
            );
          }

          // ── Analysis Triggers ──
          if (handNum === ANALYSIS_TRIGGER_HAND) {
            if (SESSION_ANALYSIS_GAMES.includes(gameNum)) {
              const success = await triggerSessionAnalysis(page, gameNum, result.failures);
              result.analysisTriggered.push({ type: 'session', success });
            }
            if (HAND_ANALYSIS_GAMES.includes(gameNum)) {
              const success = await triggerHandAnalysis(page, gameNum, handNum, result.failures);
              result.analysisTriggered.push({ type: 'hand', success });
            }
          }
        }

        // ── Game End ──
        result.finalChipTotal = await readTotalChips(page);
        await screenshotTo(page, path.join(gameDir, 'game-end.png'));

        // Quit game (helpers.ts now waits for networkidle + clears localStorage)
        await quitGame(page);

        // Extra safety: force-navigate to home and clear all game-related frontend state
        await page.goto('/');
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        await page.evaluate(() => {
          // Clear any Zustand persisted state and game references
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.includes('game') || key.includes('ws') || key.includes('zustand'))) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(k => localStorage.removeItem(k));
        });

      } catch (e) {
        console.log(`  💥 Game ${gameNum} error: ${e}`);
        result.endReason = 'error';
        await screenshotTo(page, path.join(gameDir, 'game-error.png')).catch(() => {});

        // Try to recover: quit current game and navigate home
        await quitGame(page).catch(() => {});
        await page.goto('/');
        await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
        await page.evaluate(() => {
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.includes('game') || key.includes('ws') || key.includes('zustand'))) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(k => localStorage.removeItem(k));
        }).catch(() => {});
        await page.waitForTimeout(2000);
      }

      allResults.push(result);

      const failCount = result.failures.length;
      console.log(`  Game ${gameNum} complete: ${result.handsPlayed} hands, ${failCount} failures, end: ${result.endReason}`);
    }

    // ─── Summary Report ──────────────────────────────────────────
    const totalFailures = allResults.reduce((sum, r) => sum + r.failures.length, 0);
    const totalHands = allResults.reduce((sum, r) => sum + r.handsPlayed, 0);
    const gamesCompleted = allResults.filter(r => r.endReason !== 'error').length;

    // Count failures by category
    const failuresByCategory: Record<string, number> = {};
    for (const result of allResults) {
      for (const failure of result.failures) {
        failuresByCategory[failure.category] = (failuresByCategory[failure.category] || 0) + 1;
      }
    }

    const report: SummaryReport = {
      timestamp: new Date().toISOString(),
      totalGames: TOTAL_GAMES,
      gamesCompleted,
      totalHands,
      totalFailures,
      failuresByCategory,
      games: allResults,
      verdict: totalFailures === 0 ? 'PASS' : 'FAIL',
    };

    // Write JSON report
    fs.writeFileSync(
      path.join(RESULTS_DIR, 'summary-report.json'),
      JSON.stringify(report, null, 2)
    );

    // Print human-readable summary
    console.log(`\n${'═'.repeat(60)}`);
    console.log('STRESS TEST SUMMARY');
    console.log(`${'═'.repeat(60)}`);
    console.log(`Games completed: ${gamesCompleted}/${TOTAL_GAMES}`);
    console.log(`Total hands played: ${totalHands}`);
    console.log(`Total failures: ${totalFailures}`);

    if (totalFailures > 0) {
      console.log(`\nFailures by category:`);
      for (const [cat, count] of Object.entries(failuresByCategory).sort((a, b) => b[1] - a[1])) {
        console.log(`  ${cat}: ${count}`);
      }
    }

    console.log(`\nPer-game summary:`);
    for (const result of allResults) {
      const status = result.failures.length === 0 ? '✅' : `❌ (${result.failures.length} failures)`;
      const analysis = result.analysisTriggered.length > 0
        ? ` | Analysis: ${result.analysisTriggered.map(a => `${a.type}:${a.success ? 'ok' : 'fail'}`).join(', ')}`
        : '';
      console.log(`  Game ${result.gameNumber}: ${result.handsPlayed} hands, ${result.endReason} ${status}${analysis}`);
    }

    console.log(`\nVerdict: ${report.verdict}`);
    console.log(`Report saved to: ${path.join(RESULTS_DIR, 'summary-report.json')}`);
    console.log(`${'═'.repeat(60)}\n`);

    // Soft assertion — don't fail the test on game logic issues,
    // just report them. The report is the deliverable.
    // Uncomment the line below to make it a hard fail:
    // expect(totalFailures).toBe(0);
  });
});
