# Issues Identified Through Stress Test

**Date:** 2026-03-09
**Branch:** `refactor/codebase-cleanup`
**Test:** `e2e/stress-test-gameplay.spec.ts` — 20 full poker games, always-call strategy, 25 max hands per game

## Test Coverage

| Metric | Value |
|--------|-------|
| Games completed | 15 of 20 (across multiple runs) |
| Total hands played | ~300+ |
| Unique failure categories | 4 (excluding test false positives) |
| Games with 0 failures | 11 of 15 (73%) |
| Chip conservation failures | 0 |
| UI clipping failures | 0 |

## Run History

The stress test was iterated through 7 versions to reach stability:
- v1-v3: Fixed action detection (winner modal not in wait selector, stale state between games)
- v4: Found game-over overlay bug, ran 7 games before cascading errors
- v5-v6: Fixed game-over detection, reduced max hands from 50 to 25
- v7: Added early elimination detection ($0 stack), completed 15 games in ~1 hour

---

## Issue 1: Game-Over Overlay Blocks Winner Modal

**Severity:** Medium
**Category:** UX Bug
**Observed in:** v4 run (Games 4-7), reproducible whenever player is eliminated on final hand

### Description

When the player loses their last chips and is eliminated, two modals appear simultaneously:
1. The **winner modal** (`[data-testid="winner-modal"]`) showing who won the hand
2. The **game-over modal** showing "Thanks for playing! Every hand is a learning opportunity..."

The game-over modal's overlay intercepts pointer events on the winner modal's "Next Hand" button, making it unclickable. The user gets stuck and cannot proceed.

### Technical Details

From Playwright error log:
```
locator.click: Timeout 10000ms exceeded.
- waiting for locator('[data-testid="winner-modal"]').locator('button:has-text("Next Hand")')
- locator resolved to <button class="w-full bg-gray-900 hover:bg-gray-800 text-white font-bold py-4 px-6 rounded-lg text-lg transition-colors">Next Hand</button>
- attempting click action
  - element is visible, enabled and stable
  - scrolling into view if needed
  - done scrolling
  - <p class="text-sm">Thanks for playing! Every hand is a learning oppo…</p>
    from <div class="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">…</div>
    subtree intercepts pointer events
```

The game-over container has `pointer-events-none` but a child `<p>` element within it still intercepts clicks because `pointer-events` is inherited and likely reset on children.

### Reproduction

1. Start a game with 3 AI opponents
2. Play until eliminated (always call — will happen eventually)
3. On the final hand where the player loses all chips, both modals appear
4. Try clicking "Next Hand" — blocked by game-over overlay

### Suggested Fix

Option A: Don't show the winner modal when the game is over — go straight to game-over modal.

Option B: Ensure game-over modal's entire subtree has `pointer-events-none` until the winner modal is dismissed:
```css
.game-over-overlay * { pointer-events: none; }
```

Option C: Set a higher `z-index` on the winner modal than the game-over overlay, or dismiss the winner modal before showing game-over.

---

## Issue 2: Stage Label / Card Count Timing Mismatch

**Severity:** Low
**Category:** UI Race Condition
**Observed in:** 2 occurrences across ~300 hands (< 1% frequency)

### Description

The stage label text (FLOP/TURN/RIVER) briefly shows the wrong value relative to the number of community cards visible on screen.

### Occurrences

| Run | Game | Hand | Stage Label | Card Count | Expected Label |
|-----|------|------|-------------|------------|----------------|
| v6  | 6    | 3    | TURN        | 3          | FLOP           |
| v7  | 10   | 3    | RIVER       | 4          | TURN           |

### Technical Details

The validation logic in the stress test reads `[data-testid="stage-label"]` text and counts children of `[data-testid="community-cards-list"]` at the same moment. The mismatch suggests:

1. The game state updates the stage label via WebSocket state update
2. The community cards component receives the new cards array
3. There's a brief window where one has updated but the other hasn't rendered yet

In `CommunityCards.tsx` (line 15-22), the stage label is derived from both `cards.length` and `gameState`:
```typescript
if (cards.length === 3 && gameState === 'flop') stageLabel = 'FLOP';
else if (cards.length === 4 && gameState === 'turn') stageLabel = 'TURN';
else if (cards.length === 5 && gameState === 'river') stageLabel = 'RIVER';
```

The issue likely occurs when `gameState` has advanced (e.g., to 'turn') but `cards` still has the previous count (3), causing the label to show based on the new state while cards haven't updated yet. Or the reverse — cards update before the state label re-renders.

### Impact

Purely cosmetic, very brief (< 1 frame typically). Users would rarely notice this during normal play. The stress test catches it because it reads both values in rapid succession.

### Suggested Fix

Option A: Derive the stage label solely from card count (ignore `gameState`):
```typescript
if (cards.length === 3) stageLabel = 'FLOP';
else if (cards.length === 4) stageLabel = 'TURN';
else if (cards.length === 5) stageLabel = 'RIVER';
```

Option B: Accept as cosmetic — the label self-corrects on next render cycle.

---

## Issue 3: Pot Display Shows Decrease After Call

**Severity:** Low
**Category:** UI Timing / Display Bug
**Observed in:** 1 occurrence across ~300 hands (< 0.5% frequency)

### Description

The pot display value decreased from $90 to $15 immediately after the player clicked "Call". In normal poker, calling should always increase or maintain the pot — it should never decrease mid-hand.

### Occurrence

| Run | Game | Hand | Pre-Call Pot | Post-Call Pot |
|-----|------|------|-------------|--------------|
| v4  | 3    | 45   | $90         | $15          |

### Technical Details

The stress test reads `[data-testid="pot-display"]` before and after clicking the call button, with a 1500ms wait between reads. The $90 → $15 drop suggests:

1. The call action resolved the hand (showdown)
2. A new hand started within the 1500ms wait
3. The post-call pot read caught the new hand's blind posting ($5 + $10 = $15)

This means the pot display is technically correct at both read times — it's the timing of the reads that creates the false positive. The pot was $90, the hand ended, a new hand started with $15 in blinds.

### Impact

Not a real bug in the game — it's a stress test timing artifact. The game correctly resolves hands and starts new ones. However, it does highlight that there's no visual separator between "hand ended" and "new hand started" — the pot just silently resets.

### Suggested Fix

This is a test false positive. No game fix needed.

To fix the test: skip pot-decrease validation when the hand has just transitioned (check if community card count reset to 0).

---

## Issue 4: React Duplicate Key Warning

**Severity:** Low
**Category:** Code Quality
**Observed in:** Browser console errors during multiple runs

### Description

React logs warnings about duplicate keys in component lists:
```
Encountered two children with the same key, `%s`. Keys should be unique so that
components maintain their identity across updates. Non-unique keys may cause
children to be duplicated and/or omitted — the behavior is unsupported and could
change in a future version. ai2
```

Observed for player IDs: `ai2`, `ai3`

### Technical Details

A React component is rendering a list of elements using player IDs as keys, but somehow produces duplicates. Likely locations:

1. **Opponent seat rendering** in `PokerTable.tsx` — if the opponent position calculation produces duplicate entries
2. **Showdown results** in `WinnerModal.tsx` — if the winner/showdown data contains duplicate player references
3. **Player list rendering** — if a player appears in multiple arrays that get concatenated

### Impact

May cause React rendering glitches — components could be duplicated or omitted during updates. In practice, the poker table appeared to render correctly despite the warning, but this could cause subtle UI issues under certain conditions.

### Suggested Fix

Search for list renderings that use player IDs as keys:
```bash
grep -n "key={.*player" frontend/components/PokerTable.tsx frontend/components/WinnerModal.tsx
```

Ensure each key is unique. If a player can appear in multiple contexts (e.g., both as a seat and in showdown results), prefix the key: `seat-${playerId}`, `result-${playerId}`.

---

## Not a Bug: Heads-Up Blind Rotation

**Category:** Stress Test False Positive
**Observed in:** All runs, whenever 2+ opponents eliminated

### Description

When only 2 players remain (heads-up), the stress test reports that D, SB, and BB positions "didn't rotate." This is **correct poker behavior** — in heads-up play, the dealer posts the small blind and the other player posts the big blind. With only 2 players, positions alternate but the same player can hold D+SB on consecutive hands.

### Fix Required

Fix the `validateButtonRotation` function in the stress test to skip rotation validation when only 2 players remain:
```typescript
// Count active players (visible stack > $0)
const activePlayers = [...stacks.values()].filter(s => s > 0).length;
if (activePlayers <= 2) {
  // Heads-up: D=SB is correct, skip rotation validation
  return current;
}
```

---

## Summary

| # | Issue | Severity | Type | Fix Target |
|---|-------|----------|------|------------|
| 1 | Game-over overlay blocks winner modal | Medium | UX Bug | Game code |
| 2 | Stage label / card count timing | Low | Race condition | Game code or accept |
| 3 | Pot decrease after call | N/A | Test false positive | Test code |
| 4 | React duplicate key warning | Low | Code quality | Game code |
| 5 | Heads-up rotation validation | N/A | Test false positive | Test code |

### Positive Findings

The stress test validated that **core game logic is solid**:
- **Chip conservation:** 0 failures across ~300 hands — no chips created or destroyed
- **UI clipping:** 0 failures — hero seat, control panel, and poker table all within viewport
- **Community card counts:** Always valid (0, 3, 4, or 5) — no skips or decreases
- **Winner modal:** Always appeared with visible "Next Hand" button (except when blocked by game-over overlay)
- **Game creation and WebSocket:** Stable across 15+ consecutive games with same user
- **Session analysis:** Triggered successfully in Game 5 without crashing
