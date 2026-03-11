# Seat Position Maps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace fragile ellipse-math player positioning with hardcoded percentage-based seat maps that produce correct, evenly-distributed player layouts for 2, 4, and 6-player games at any window size.

**Architecture:** Three lookup tables (one per player count) define seat coordinates as percentages of the fixed-aspect-ratio table container. The container's existing `calculateContainerSize()` maintains 16:10 (desktop) / 4:5 (mobile) aspect ratio on resize, so percentage positions scale automatically. No ellipse math is retained for seat placement.

**Tech Stack:** TypeScript, Next.js 15, existing `frontend/lib/poker-table-layout.ts` and `frontend/components/PokerTable.tsx`

---

### Task 1: Create feature branch

**Files:**
- No file changes

**Step 1: Create and switch to feature branch**

```bash
git checkout -b fix/seat-position-maps
```

Expected: `Switched to a new branch 'fix/seat-position-maps'`

**Step 2: Verify clean state**

```bash
git status
```

Expected: `nothing to commit, working tree clean`

---

### Task 2: Write failing tests for the new seat map API

**Files:**
- Create: `frontend/__tests__/lib/poker-table-layout.test.ts`

**Context:** There are currently no tests for `poker-table-layout.ts`. We'll write tests that define the expected behavior of the new seat map, then implement to make them pass. The test file goes in `frontend/__tests__/lib/` alongside the existing `auth.test.ts`.

**Step 1: Write the failing tests**

Create `frontend/__tests__/lib/poker-table-layout.test.ts` with this content:

```typescript
import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
} from '../../lib/poker-table-layout';

describe('calculateOpponentPositions', () => {
  describe('2-player (heads-up)', () => {
    it('returns 1 position', () => {
      expect(calculateOpponentPositions(1)).toHaveLength(1);
    });

    it('places single opponent at top center', () => {
      const [pos] = calculateOpponentPositions(1);
      const left = parseFloat(pos.left);
      const top = parseFloat(pos.top);
      expect(left).toBeCloseTo(50, 0);
      expect(top).toBeLessThan(25);
    });
  });

  describe('4-player (3 opponents)', () => {
    it('returns 3 positions', () => {
      expect(calculateOpponentPositions(3)).toHaveLength(3);
    });

    it('has one seat at the top (top < 25%)', () => {
      const positions = calculateOpponentPositions(3);
      const tops = positions.map(p => parseFloat(p.top));
      expect(tops.some(t => t < 25)).toBe(true);
    });

    it('has one seat on the left (left < 25%)', () => {
      const positions = calculateOpponentPositions(3);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.some(l => l < 25)).toBe(true);
    });

    it('has one seat on the right (left > 60%)', () => {
      const positions = calculateOpponentPositions(3);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.some(l => l > 60)).toBe(true);
    });

    it('left and right seats are at similar vertical height (within 10%)', () => {
      const positions = calculateOpponentPositions(3);
      const sorted = [...positions].sort((a, b) => parseFloat(a.left) - parseFloat(b.left));
      const leftTop = parseFloat(sorted[0].top);
      const rightTop = parseFloat(sorted[sorted.length - 1].top);
      expect(Math.abs(leftTop - rightTop)).toBeLessThan(10);
    });

    it('all seats are within table bounds (8%–82% horizontal, 5%–82% vertical)', () => {
      const positions = calculateOpponentPositions(3);
      positions.forEach(pos => {
        const left = parseFloat(pos.left);
        const top = parseFloat(pos.top);
        expect(left).toBeGreaterThanOrEqual(8);
        expect(left).toBeLessThanOrEqual(82);
        expect(top).toBeGreaterThanOrEqual(5);
        expect(top).toBeLessThanOrEqual(82);
      });
    });

    it('all positions have centering transform', () => {
      calculateOpponentPositions(3).forEach(pos => {
        expect(pos.transform).toBe('translate(-50%, -50%)');
      });
    });
  });

  describe('6-player (5 opponents)', () => {
    it('returns 5 positions', () => {
      expect(calculateOpponentPositions(5)).toHaveLength(5);
    });

    it('has seats on left, right, and top', () => {
      const positions = calculateOpponentPositions(5);
      const lefts = positions.map(p => parseFloat(p.left));
      const tops = positions.map(p => parseFloat(p.top));
      expect(lefts.some(l => l < 20)).toBe(true);   // left side
      expect(lefts.some(l => l > 70)).toBe(true);   // right side
      expect(tops.some(t => t < 20)).toBe(true);    // top area
    });

    it('all seats are within table bounds', () => {
      const positions = calculateOpponentPositions(5);
      positions.forEach(pos => {
        const left = parseFloat(pos.left);
        const top = parseFloat(pos.top);
        expect(left).toBeGreaterThanOrEqual(5);
        expect(left).toBeLessThanOrEqual(85);
        expect(top).toBeGreaterThanOrEqual(5);
        expect(top).toBeLessThanOrEqual(82);
      });
    });
  });

  describe('mobile variant', () => {
    it('4-player right seat is within mobile bounds (left < 80%)', () => {
      const positions = calculateOpponentPositions(3, true);
      const lefts = positions.map(p => parseFloat(p.left));
      expect(lefts.every(l => l <= 80)).toBe(true);
    });
  });
});

describe('getHumanPlayerPosition', () => {
  it('places human at bottom center', () => {
    const pos = getHumanPlayerPosition();
    expect(parseFloat(pos.left)).toBeCloseTo(50, 0);
    expect(parseFloat(pos.top)).toBeGreaterThan(70);
  });

  it('has centering transform', () => {
    expect(getHumanPlayerPosition().transform).toBe('translate(-50%, -50%)');
  });
});
```

**Step 2: Run tests to verify they fail**

```bash
cd frontend && npm run test -- --testPathPattern="poker-table-layout" --no-coverage 2>&1 | tail -20
```

Expected: Tests fail with errors like `calculateOpponentPositions is not meeting expectations` or import errors if the function signatures change.

---

### Task 3: Replace ellipse math with seat position maps

**Files:**
- Modify: `frontend/lib/poker-table-layout.ts`

**Context:** We're replacing the body of `calculateOpponentPositions` and `getHumanPlayerPosition`. We also remove `DEFAULT_ELLIPSE_CONFIG`, `MOBILE_ELLIPSE_CONFIG`, and `EllipseConfig` (the `config` parameter is replaced by a `isMobile: boolean` flag). `getCenterAreaPosition` and `calculateContainerSize` are unchanged.

**Step 1: Rewrite `poker-table-layout.ts`**

Replace the entire file with:

```typescript
/**
 * Poker Table Seat Layout Utilities
 *
 * Defines fixed seat positions for each player count.
 * Positions are percentages of the table container, which maintains
 * a fixed aspect ratio (16:10 desktop, 4:5 mobile) via calculateContainerSize().
 * Percentage-based positions therefore scale automatically on window resize.
 *
 * Seat order: opponents are assigned seats in array order (index 0 = first opponent).
 * The human player always sits at bottom-center.
 */

export interface PlayerPosition {
  left: string;       // CSS left value as percentage (e.g., "50%")
  top: string;        // CSS top value as percentage (e.g., "15%")
  transform: string;  // CSS transform for centering (always "translate(-50%, -50%)")
}

// ---------------------------------------------------------------------------
// Seat maps: [left%, top%] per seat, indexed by opponent seat number.
// Desktop (16:10 aspect ratio container)
// ---------------------------------------------------------------------------

const DESKTOP_SEATS: Record<number, Array<[number, number]>> = {
  1: [
    [50, 15],   // heads-up: top center
  ],
  3: [
    [50, 12],   // top center
    [10, 45],   // left
    [78, 45],   // right
  ],
  5: [
    [50,  8],   // top center
    [20, 15],   // top left
    [80, 15],   // top right
    [ 8, 48],   // left
    [78, 48],   // right
  ],
};

// Mobile (4:5 aspect ratio container) — tighter horizontal to fit 375px+
const MOBILE_SEATS: Record<number, Array<[number, number]>> = {
  1: [
    [50, 15],
  ],
  3: [
    [50, 12],
    [ 8, 45],
    [76, 45],
  ],
  5: [
    [50,  8],
    [20, 15],
    [78, 15],
    [ 6, 48],
    [76, 48],
  ],
};

// Human player seat: always bottom center
const HUMAN_DESKTOP: [number, number] = [50, 78];
const HUMAN_MOBILE:  [number, number] = [50, 78];

function toPosition([left, top]: [number, number]): PlayerPosition {
  return {
    left: `${left}%`,
    top: `${top}%`,
    transform: 'translate(-50%, -50%)',
  };
}

/**
 * Returns seat positions for AI opponents.
 *
 * @param numOpponents - Number of AI opponents (1, 3, or 5)
 * @param isMobile - Use tighter mobile layout (default: false)
 */
export function calculateOpponentPositions(
  numOpponents: number,
  isMobile: boolean = false
): PlayerPosition[] {
  const map = isMobile ? MOBILE_SEATS : DESKTOP_SEATS;
  const seats = map[numOpponents];

  if (!seats) {
    // Fallback: evenly distribute along top arc for unsupported counts
    console.warn(`No seat map for ${numOpponents} opponents, falling back`);
    return Array.from({ length: numOpponents }, (_, i) => ({
      left: `${10 + (i * 80) / Math.max(numOpponents - 1, 1)}%`,
      top: '15%',
      transform: 'translate(-50%, -50%)',
    }));
  }

  return seats.map(toPosition);
}

/**
 * Returns the human player's seat position (always bottom center).
 *
 * @param isMobile - Use mobile layout (default: false)
 */
export function getHumanPlayerPosition(isMobile: boolean = false): PlayerPosition {
  return toPosition(isMobile ? HUMAN_MOBILE : HUMAN_DESKTOP);
}

/**
 * Get center area position (community cards).
 * Positioned at 50% horizontal, 45% vertical — center of the table.
 */
export function getCenterAreaPosition(): PlayerPosition {
  return {
    left: '50%',
    top: '45%',
    transform: 'translate(-50%, -50%)',
  };
}

/**
 * Calculate container size to fit viewport while maintaining aspect ratio.
 * 16:10 on desktop, 4:5 on mobile.
 */
export function calculateContainerSize(
  viewportWidth: number,
  viewportHeight: number,
  headerHeight: number = 0,
  isMobile: boolean = false
): { width: string; height: string } {
  const aspectRatio = isMobile ? 4 / 5 : 16 / 10;
  const padding = isMobile ? 16 : 32;
  const bottomBarHeight = isMobile ? 140 : 0;

  const availableWidth = Math.min(viewportWidth - padding, 1400);
  const availableHeight = viewportHeight - headerHeight - padding - bottomBarHeight;

  const wWidth = availableWidth;
  const wHeight = wWidth / aspectRatio;

  const hHeight = availableHeight;
  const hWidth = hHeight * aspectRatio;

  let finalWidth: number;
  let finalHeight: number;

  if (wHeight <= availableHeight) {
    finalWidth = wWidth;
    finalHeight = wHeight;
  } else {
    finalWidth = Math.min(hWidth, availableWidth);
    finalHeight = finalWidth / aspectRatio;
  }

  return {
    width: `${finalWidth}px`,
    height: `${finalHeight}px`,
  };
}
```

**Step 2: Run tests to verify they pass**

```bash
cd frontend && npm run test -- --testPathPattern="poker-table-layout" --no-coverage 2>&1 | tail -20
```

Expected: All tests PASS.

**Step 3: Commit**

```bash
git add frontend/lib/poker-table-layout.ts frontend/__tests__/lib/poker-table-layout.test.ts
git commit -m "feat: replace ellipse math with predefined seat position maps"
```

---

### Task 4: Update PokerTable.tsx to use the new API

**Files:**
- Modify: `frontend/components/PokerTable.tsx`

**Context:** The import and call sites need updating because:
1. `MOBILE_ELLIPSE_CONFIG` is removed — replaced by `isMobile` boolean parameter
2. `EllipseConfig` type is removed
3. `calculateOpponentPositions(n, config)` → `calculateOpponentPositions(n, isMobile)`
4. `getHumanPlayerPosition(config)` → `getHumanPlayerPosition(isMobile)`
5. `getCenterAreaPosition(config)` → `getCenterAreaPosition()` (no args)

**Step 1: Update the import in PokerTable.tsx**

Find line 16-22:
```typescript
import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
  getCenterAreaPosition,
  calculateContainerSize,
  MOBILE_ELLIPSE_CONFIG
} from '../lib/poker-table-layout';
```

Replace with:
```typescript
import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
  getCenterAreaPosition,
  calculateContainerSize,
} from '../lib/poker-table-layout';
```

**Step 2: Update the ellipseConfig variable usage**

Find (around line 109):
```typescript
const ellipseConfig = isMobileView ? MOBILE_ELLIPSE_CONFIG : undefined;
```

Delete this line entirely.

**Step 3: Update calculateOpponentPositions call site**

Find (around line 499):
```typescript
const opponentPositions = calculateOpponentPositions(opponents.length, ellipseConfig);
```

Replace with:
```typescript
const opponentPositions = calculateOpponentPositions(opponents.length, isMobileView);
```

**Step 4: Update getHumanPlayerPosition call sites**

Find (around lines 578-580):
```typescript
left: getHumanPlayerPosition(ellipseConfig).left,
top: getHumanPlayerPosition(ellipseConfig).top,
transform: getHumanPlayerPosition(ellipseConfig).transform,
```

Replace with:
```typescript
left: getHumanPlayerPosition(isMobileView).left,
top: getHumanPlayerPosition(isMobileView).top,
transform: getHumanPlayerPosition(isMobileView).transform,
```

**Step 5: Update getCenterAreaPosition call site (if it takes config)**

Search for `getCenterAreaPosition(` in PokerTable.tsx. If it passes `ellipseConfig`, remove the argument since the new version takes no parameters.

**Step 6: Verify TypeScript compiles**

```bash
cd frontend && npm run build 2>&1 | tail -30
```

Expected: Build succeeds with no TypeScript errors. Fix any remaining references to `ellipseConfig` or `MOBILE_ELLIPSE_CONFIG` if the build reports errors.

**Step 7: Commit**

```bash
git add frontend/components/PokerTable.tsx
git commit -m "fix: update PokerTable to use new seat map API"
```

---

### Task 5: Run full test suite

**Files:** No changes

**Step 1: Run frontend Jest tests**

```bash
cd frontend && npm run test --no-coverage 2>&1 | tail -20
```

Expected: All tests pass.

**Step 2: Run backend regression tests**

```bash
PYTHONPATH=backend pytest backend/tests/ -v 2>&1 | tail -20
```

Expected: All tests pass.

---

### Task 6: Visual validation via Playwright

**Files:** No changes

**Context:** Both servers must be running. Start them first, then run E2E.

**Step 1: Start servers (in separate terminals)**

```bash
# Terminal 1
cd backend && python main.py

# Terminal 2
cd frontend && npm run dev
```

**Step 2: Run stress test**

```bash
npm run test:e2e 2>&1 | tail -40
```

**Step 3: Inspect screenshots**

```bash
ls e2e/stress-test-results/game-01/
open e2e/stress-test-results/game-01/
```

Look for:
- 4-player games: top, left, right, and bottom seats clearly separated, left/right at true mid-height
- 6-player games: two top seats, two mid seats, one top-center, human at bottom
- No seat overlapping the sidebar or extending outside the table ellipse
- Human seat clearly at bottom center

**Step 4: If positions need tuning**

Edit the coordinate values in `DESKTOP_SEATS` / `MOBILE_SEATS` in `frontend/lib/poker-table-layout.ts`, rebuild, rerun E2E, reinspect. This is now trivial — just change a number.

**Step 5: Commit tuned positions (if any)**

```bash
git add frontend/lib/poker-table-layout.ts
git commit -m "fix: tune seat positions based on visual validation"
```

---

### Task 7: Final cleanup and merge preparation

**Step 1: Verify no dead references**

```bash
grep -r "MOBILE_ELLIPSE_CONFIG\|DEFAULT_ELLIPSE_CONFIG\|EllipseConfig\|ellipseConfig" frontend/
```

Expected: No results (all cleaned up).

**Step 2: Run full test suite one final time**

```bash
cd frontend && npm run test --no-coverage && cd .. && PYTHONPATH=backend pytest backend/tests/ -v 2>&1 | tail -10
```

Expected: All pass.

**Step 3: Final commit (if needed) and push**

```bash
git push -u origin fix/seat-position-maps
```

Then open a PR or merge to main per your workflow.
