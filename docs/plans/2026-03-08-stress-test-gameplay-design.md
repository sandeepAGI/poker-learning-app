# Stress Test Gameplay — Design Document

**Date:** 2026-03-08
**Purpose:** One-time E2E stress test to validate poker game logic and UI rendering across 20 full games before merging to main for outside testers.
**Status:** Design approved, ready for implementation.

> **WARNING:** This is a one-off validation test. Run sparingly — it takes 30-45 minutes and creates a fresh user per game. Not part of the regular E2E suite.

## Overview

Playwright drives 20 complete poker games (register → play until elimination → quit). The human player always calls (or checks). Every hand validates game logic (pot math, chip conservation, blind rotation) and UI rendering (elements visible, no clipping, correct card counts). Failures are logged with screenshots but don't stop execution.

## Approach

**Page-level validation (Approach A):** All assertions are based on what's visible in the UI. No WebSocket interception or API calls. This tests the real user experience end-to-end. If this reveals UI/state mismatches, Approach B (dual-channel with WebSocket validation) can be added later.

## File & Folder Structure

```
e2e/stress-test-gameplay.spec.ts     # The test (standalone, not in regular suite)

e2e/stress-test-results/              # Wiped at start of each run, gitignored
├── game-01/
│   ├── hand-03-failure-pot-mismatch.png
│   ├── hand-07-failure-chips-not-conserved.png
│   └── game-end.png
├── game-05/
│   ├── session-analysis.png
│   └── game-end.png
├── game-08/
│   ├── hand-05-hand-analysis.png
│   └── game-end.png
├── ...
└── summary-report.json
```

## Game Loop

```
For each game (1-20):
  1. Register fresh user, create 3-opponent game
  2. Record initial chip total (sum all stacks)
  3. For each hand (up to 50 per game):
     a. Record D/SB/BB positions → validate rotation from previous hand
     b. Validate blind deductions from SB/BB stacks
     c. When it's our turn: always call (or check if no bet, fold as last resort)
     d. After each action: validate pot, stack, no errors, UI visible
     e. After stage transitions: validate community card count + stage label
     f. On winner modal: validate amount > 0, Next Hand button visible
     g. Click Next Hand → validate chip conservation
     h. If game 5/10/15/20 AND hand == 5: trigger session analysis + screenshot
     i. If game 8/16 AND hand == 5: trigger hand analysis + screenshot
     j. If game over modal appears: log final stats, screenshot, break
  4. Quit game, save game-end screenshot

After all 20 games:
  - Write summary-report.json
  - Print human-readable summary to console
```

## Validations

### After each action (call/check)
- Pot display value increased (or stayed same for check)
- Hero stack decreased by the call amount
- No error banners visible
- Hero seat, control panel, community cards area all visible

### After stage transitions (pre_flop → flop → turn → river)
- Community card count: 0 → 3 → 4 → 5 (never skips, never decreases)
- Stage label matches card count (FLOP=3, TURN=4, RIVER=5)
- Stage label is below cards (not above)

### At showdown / winner modal
- Winner modal appears with data-testid="winner-modal"
- Winner amount > 0
- "Next Hand" button visible without scrolling (sticky footer)
- Modal closes after clicking Next Hand

### Between hands
- **Chip conservation:** sum of all visible stacks + pot = initial total chips
- No player has negative stack
- Hand count incremented
- **Dealer rotation:** D, SB, BB on different players than previous hand
- **Blind order:** SB one seat after D, BB one seat after SB (skipping eliminated)
- **Blind deductions:** correct amounts deducted from SB/BB stacks

### At game end
- Game over modal appears OR only one player has chips
- Final chip total still conserved

### Analysis triggers
- Modal opens, loading state shows, resolves without crash
- Content or graceful "not configured" error (no crash)
- Screenshot captured

## Player Strategy

Always call. This maximizes hands reaching showdown, giving maximum coverage of pot math, winner determination, and community card stages.

## Analysis Triggers

| Trigger | Games | Condition |
|---------|-------|-----------|
| Session analysis | 5, 10, 15, 20 | After hand 5 |
| Hand analysis | 8, 16 | After hand 5 |

Total: 4 session + 2 hand = 6 analysis triggers across 20 games.

## Running

```bash
# Both servers must be running first
npx playwright test e2e/stress-test-gameplay.spec.ts --timeout=3600000
```

Estimated runtime: 30-45 minutes.

## Data Testids Used

| Element | Testid |
|---------|--------|
| Poker table | `poker-table-container` |
| Hero seat | `human-player-seat` |
| Opponent seats | `opponent-seat-{N}` |
| Fold button | `fold-button` |
| Call button | `call-button` |
| Pot display | `pot-display` |
| Community cards | `community-cards-area` |
| Community card list | `community-cards-list` |
| Stage label | `stage-label` |
| Winner modal | `winner-modal` |
| Winner amount | `winner-amount` |
| Control panel | `control-panel` |
| D/SB/BB badges | `dealer-button-{id}`, `small-blind-button-{id}`, `big-blind-button-{id}` |
| Settings button | `settings-button` |
| Analyze hand button | `analyze-hand-button` |
| Session analysis button | `session-analysis-button` |
| Hand count | `hand-count` |
| Connection status | `connection-status` |
