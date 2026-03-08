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
