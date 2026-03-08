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
const MAX_HANDS_PER_GAME = 50;
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

    for (let gameNum = 1; gameNum <= TOTAL_GAMES; gameNum++) {
      console.log(`\n${'='.repeat(60)}`);
      console.log(`GAME ${gameNum}/${TOTAL_GAMES}`);
      console.log(`${'='.repeat(60)}`);

      // TODO: Implement game loop (Task 5)
    }

    // TODO: Write summary report (Task 6)
  });
});
