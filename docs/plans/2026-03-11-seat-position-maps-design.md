# Design: Predefined Seat Position Maps

**Date:** 2026-03-11
**Status:** Approved
**Branch:** `fix/seat-position-maps`

## Problem

Player seats are not distributed properly around the poker table ellipse. This is a recurring issue that has been "fixed" multiple times but keeps regressing. Root cause analysis:

1. **Ellipse is too flat and too high** — `radiusY=30` on `centerY=38%` places the entire ellipse between 8%–68% vertically, leaving the bottom third of the table unused.
2. **Arc math pushes side seats toward the hero** — A 240° arc from 210° to -30° places left/right opponents at y=53%, only 15% above the hero at y=68%. They look bunched together, not evenly spaced.
3. **6-player is worse** — Opponents 0 and 4 land at y=61%, just 7% above the hero.
4. **Ellipse math on a rectangular+sidebar viewport is inherently fragile** — The constraint space (sidebar, header, aspect ratio) is asymmetric; uniform angular spacing doesn't produce uniform visual spacing.

## Solution: Predefined Seat Position Maps

Replace all ellipse math with explicit percentage-based seat coordinates per player count. Since the table container maintains a fixed aspect ratio (16:10 desktop, 4:5 mobile) via the existing `calculateContainerSize()`, percentage positions scale perfectly on window resize with zero additional logic.

## Seat Maps

All coordinates are `(left%, top%)` of the table container, with `transform: translate(-50%, -50%)`.

### 2-Player (Heads-Up)
| Seat | Role | left | top |
|------|------|------|-----|
| 0 | Opponent (top) | 50% | 15% |
| Human | Hero (bottom) | 50% | 78% |

### 4-Player (3 opponents)
| Seat | Role | left | top |
|------|------|------|-----|
| 0 | Top center | 50% | 12% |
| 1 | Left | 10% | 45% |
| 2 | Right | 78% | 45% |
| Human | Bottom center | 50% | 78% |

### 6-Player (5 opponents)
| Seat | Role | left | top |
|------|------|------|-----|
| 0 | Top left | 25% | 12% |
| 1 | Top right | 75% | 12% |
| 2 | Left | 8% | 45% |
| 3 | Right | 80% | 45% |
| 4 | Top center | 50% | 8% |
| Human | Bottom center | 50% | 78% |

### Mobile Variants (4:5 container)
Tighter horizontal positions to fit 375px+ screens.

| Player count | Adjustment |
|---|---|
| 4-player left | 8% → 6% |
| 4-player right | 78% → 76% |
| 6-player right | 80% → 78% |

## Constraints Enforced
- All positions within 8%–80% horizontally — cards stay inside table, clear of sidebar
- All positions within 8%–80% vertically — clear of header and bottom action bar
- Left/right seats at true mid-height (~45%), not pushed toward top or bottom
- Minimum ~25% vertical gap between any two rows of seats

## Files Changed
1. `frontend/lib/poker-table-layout.ts` — Delete ellipse math; add `SEAT_POSITIONS` lookup; update `calculateOpponentPositions()` and `getHumanPlayerPosition()` to use lookup
2. `frontend/components/PokerTable.tsx` — No API changes expected (still receives `PlayerPosition[]`); verify consumption is correct

## Files Unchanged
- `getCenterAreaPosition()` — Still uses ellipse center, unchanged
- `calculateContainerSize()` — Unchanged; still handles responsive sizing
- All backend files — No changes
- Mobile config — Separate mobile seat map replaces `MOBILE_ELLIPSE_CONFIG`

## Scaling Behavior
```
Viewport resizes
  → calculateContainerSize() recomputes container px dimensions (maintains aspect ratio)
    → Container div shrinks/grows proportionally
      → Seat at left:50%, top:12% moves with container
        → Layout looks identical at any viewport size
```

## Validation
1. Run `npm run test` (frontend Jest)
2. Run `npm run test:e2e` and inspect screenshots for all player counts
3. Manually check 4-player and 6-player at multiple window widths
4. Verify no seat overlaps sidebar or extends outside table ellipse

## Why Previous Fixes Failed
Each previous fix adjusted `centerY`, `radiusY`, or arc angles to avoid a specific overlap (hero/community cards), which shifted the problem elsewhere. The fundamental issue — uniform angular spacing doesn't produce uniform visual spacing on a non-square viewport — was never addressed. Predefined coordinates sidestep this entirely.
