# Poker Table Elliptical Layout - Implementation Plan (TypeScript Approach)

**Date:** 2026-01-19 (Revised)
**Goal:** Replace hardcoded positioning with calculated elliptical layout using TypeScript
**Approach:** TypeScript-driven elliptical math leveraging existing architecture (Next.js 15, React 19, Framer Motion, Tailwind 4)

## Problem Analysis

### Current Issues (Why Previous Approaches Failed):
1. **Hardcoded positions** - `top-1/3 left-8`, `left-[25%]` don't scale properly
2. **Overlapping elements** - No z-index management, elements compete for space
3. **Viewport height hacks** - Band-aid media queries in `globals.css:30-51` instead of proper container scaling
4. **No aspect ratio container** - Just `flex-1 relative` doesn't maintain proportions
5. **Conditional positioning logic** - Brittle `{opponents.length === 3 ? ... : ...}` checks
6. **Doesn't leverage architecture** - Not using Framer Motion properly, missing TypeScript type safety

### Why This Approach Will Work:
1. **Mathematical positioning** - Elliptical formula calculates positions dynamically
2. **Proper container** - Fixed aspect ratio that scales with viewport
3. **Type-safe** - TypeScript utilities with proper interfaces
4. **Responsive by design** - Container scales, positions stay proportional
5. **Leverages existing stack** - React 19, Framer Motion for animations, Tailwind for styling

## Solution: TypeScript-Calculated Elliptical Layout

### Core Concept:

```
┌─────────────────────────────────────┐
│                                     │
│        ○    ○    ○                  │  ← Opponents (calculated angles: 180°-0°)
│     ○                 ○             │     Position = (cx + rx*cos(θ), cy - ry*sin(θ))
│                                     │
│         💰 Community Cards          │  ← Center (50%, 40%)
│                                     │
│              🂡🂱                    │  ← Human player (50%, bottom)
│         [Actions]                   │     OUTSIDE container (not affected by container size)
└─────────────────────────────────────┘
```

### Key Principles:

1. **Fixed aspect ratio container** - 16:10 ratio, scales with viewport
2. **Mathematical positioning** - TypeScript calculates all opponent positions
3. **Human player anchored** - Bottom-center, OUTSIDE container (no overlap with buttons)
4. **Consistent spacing** - Angles distributed evenly across 180° arc
5. **Type-safe** - Interfaces for positions, config, player data

## Implementation Phases

### Phase 1: TypeScript Layout Utilities
**Duration:** 60 minutes

**Tasks:**
1. Create `lib/poker-table-layout.ts` with elliptical calculation functions
2. Define TypeScript interfaces for layout config and positions
3. Add unit tests for position calculations
4. Export utility functions for use in components

**TypeScript Implementation:**

```typescript
// frontend/lib/poker-table-layout.ts

export interface EllipseConfig {
  centerX: number;      // % of container width (default: 50)
  centerY: number;      // % of container height (default: 40)
  radiusX: number;      // Horizontal radius % (default: 42)
  radiusY: number;      // Vertical radius % (default: 28)
}

export interface PlayerPosition {
  left: string;         // CSS left value (e.g., "50%")
  top: string;          // CSS top value (e.g., "15%")
  transform: string;    // CSS transform (centering)
}

/**
 * Calculate elliptical positions for opponents
 * Distributes players evenly across 180° arc (top-left to top-right)
 *
 * @param numOpponents - Number of AI opponents (3 or 5)
 * @param config - Ellipse configuration (optional)
 * @returns Array of position objects for each opponent
 */
export function calculateOpponentPositions(
  numOpponents: number,
  config: EllipseConfig = {
    centerX: 50,
    centerY: 40,
    radiusX: 42,
    radiusY: 28
  }
): PlayerPosition[] {
  // Edge case: single opponent (heads-up)
  if (numOpponents === 1) {
    return [{
      left: '50%',
      top: '8%',
      transform: 'translate(-50%, -50%)'
    }];
  }

  // Distribute opponents across 180° arc (left to right)
  const startAngle = 180; // Left side (180°)
  const endAngle = 0;     // Right side (0°)
  const angleStep = (startAngle - endAngle) / (numOpponents - 1);

  return Array.from({ length: numOpponents }, (_, i) => {
    // Calculate angle for this opponent
    const angleDeg = startAngle - i * angleStep;
    const angleRad = (angleDeg * Math.PI) / 180;

    // Elliptical formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
    // Note: Subtract sin(θ) because CSS Y-axis is inverted (0 at top)
    const x = config.centerX + config.radiusX * Math.cos(angleRad);
    const y = config.centerY - config.radiusY * Math.sin(angleRad);

    return {
      left: `${x.toFixed(2)}%`,
      top: `${y.toFixed(2)}%`,
      transform: 'translate(-50%, -50%)' // Center the element on the calculated point
    };
  });
}

/**
 * Get human player position (always bottom-center)
 */
export function getHumanPlayerPosition(): PlayerPosition {
  return {
    left: '50%',
    top: '92%', // Near bottom of container
    transform: 'translate(-50%, -50%)'
  };
}

/**
 * Get center area position (pot + community cards)
 */
export function getCenterAreaPosition(): PlayerPosition {
  return {
    left: '50%',
    top: '50%',
    transform: 'translate(-50%, -50%)'
  };
}

/**
 * Calculate container size to fit viewport
 * Maintains 16:10 aspect ratio
 */
export function calculateContainerSize(
  viewportWidth: number,
  viewportHeight: number
): { width: string; height: string } {
  const aspectRatio = 16 / 10;
  const padding = 32; // 2rem total padding

  // Try fitting by width first
  const widthConstrainedWidth = Math.min(viewportWidth - padding, 1400);
  const widthConstrainedHeight = widthConstrainedWidth / aspectRatio;

  // Check if height fits
  if (widthConstrainedHeight <= viewportHeight * 0.85) {
    return {
      width: `${widthConstrainedWidth}px`,
      height: `${widthConstrainedHeight}px`
    };
  }

  // Fit by height instead
  const heightConstrainedHeight = viewportHeight * 0.85;
  const heightConstrainedWidth = heightConstrainedHeight * aspectRatio;

  return {
    width: `${heightConstrainedWidth}px`,
    height: `${heightConstrainedHeight}px`
  };
}
```

**Tests:**
```typescript
// frontend/lib/__tests__/poker-table-layout.test.ts

describe('calculateOpponentPositions', () => {
  it('should position 3 opponents evenly across 180° arc', () => {
    const positions = calculateOpponentPositions(3);
    expect(positions).toHaveLength(3);

    // Position 0: Left side (~180°)
    expect(parseFloat(positions[0].left)).toBeLessThan(20);

    // Position 1: Top center (~90°)
    expect(parseFloat(positions[1].left)).toBeCloseTo(50, 1);
    expect(parseFloat(positions[1].top)).toBeLessThan(20);

    // Position 2: Right side (~0°)
    expect(parseFloat(positions[2].left)).toBeGreaterThan(80);
  });

  it('should position 5 opponents evenly across 180° arc', () => {
    const positions = calculateOpponentPositions(5);
    expect(positions).toHaveLength(5);

    // Verify even distribution
    expect(parseFloat(positions[0].left)).toBeLessThan(20); // Far left
    expect(parseFloat(positions[2].left)).toBeCloseTo(50, 1); // Center
    expect(parseFloat(positions[4].left)).toBeGreaterThan(80); // Far right
  });

  it('should handle custom ellipse config', () => {
    const positions = calculateOpponentPositions(3, {
      centerX: 50,
      centerY: 35,
      radiusX: 40,
      radiusY: 25
    });

    expect(positions[1].left).toBe('50.00%'); // Center X unchanged
    expect(parseFloat(positions[1].top)).toBeLessThan(15); // Higher (smaller Y)
  });
});
```

---

### Phase 2: Container & Aspect Ratio
**Duration:** 45 minutes

**Tasks:**
1. Replace outer `flex-1 relative` div with proper aspect ratio container
2. Add container styling with oval border and poker felt background
3. Move action buttons OUTSIDE container (separate positioning)
4. Ensure container scales properly with viewport

**Component Structure:**

```tsx
// frontend/components/PokerTable.tsx (updated structure)

export function PokerTable() {
  // ... existing state and hooks ...

  return (
    <div className="flex flex-col h-screen bg-[#0D5F2F] p-2 sm:p-4">
      {/* Header - stays the same */}
      <div className="flex justify-between items-center mb-2 sm:mb-4">
        {/* ... header content ... */}
      </div>

      {/* Main content area - flex container for proper centering */}
      <div className="flex-1 flex items-center justify-center relative overflow-visible">
        {/* Poker table container - FIXED ASPECT RATIO */}
        <div
          data-testid="poker-table-container"
          className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
          style={{
            width: 'min(100vw - 2rem, 90vh * 1.6)',
            aspectRatio: '16 / 10',
            maxWidth: '1400px',
            maxHeight: '85vh'
          }}
        >
          {/* All player seats positioned absolutely within this container */}
          {/* Opponents, human player, center area */}
        </div>

        {/* Action buttons - OUTSIDE container, positioned absolutely relative to viewport */}
        <div
          data-testid="action-buttons-container"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-50"
        >
          {/* Action buttons stay accessible, never overlapped */}
        </div>
      </div>
    </div>
  );
}
```

**Styling:**
```css
/* frontend/app/globals.css - REMOVE old viewport height hacks */

/* DELETE THESE LINES (30-51):
.human-player-position {
  bottom: 4rem;
}
@media (min-height: 700px) { ... }
*/

/* No custom CSS needed - everything is inline styles or Tailwind */
```

**Tests:**
- [ ] Container maintains 16:10 aspect ratio on all screen sizes
- [ ] Container doesn't overflow viewport
- [ ] Action buttons always visible below container
- [ ] Container centers in available space

---

### Phase 3: Apply Calculated Positions to Opponents
**Duration:** 75 minutes

**Tasks:**
1. Import `calculateOpponentPositions` utility
2. Calculate positions dynamically based on opponent count
3. Apply positions as inline styles (not CSS classes)
4. Remove conditional positioning logic
5. Add proper z-index management

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx

import { calculateOpponentPositions, getHumanPlayerPosition, getCenterAreaPosition } from '../lib/poker-table-layout';

export function PokerTable() {
  const { gameState, /* ... */ } = useGameStore();

  // ... existing state ...

  if (!gameState) return null;

  // Calculate opponent positions dynamically
  const opponents = gameState.players.filter((p) => !p.is_human);
  const opponentPositions = calculateOpponentPositions(opponents.length);
  const humanPosition = getHumanPlayerPosition();
  const centerPosition = getCenterAreaPosition();

  // Helper function for player indices
  const getPlayerIndex = (player: Player) => {
    return gameState.players.findIndex(p => p.player_id === player.player_id);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0D5F2F] p-2 sm:p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-2 sm:mb-4">
        {/* ... header ... */}
      </div>

      {/* Main table area */}
      <div className="flex-1 flex items-center justify-center relative overflow-visible">
        {/* Poker table container */}
        <div
          data-testid="poker-table-container"
          className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
          style={{
            width: 'min(100vw - 2rem, 90vh * 1.6)',
            aspectRatio: '16 / 10',
            maxWidth: '1400px',
            maxHeight: '85vh'
          }}
        >
          {/* Opponents - Positioned using calculated positions */}
          {opponents.map((opponent, index) => {
            const position = opponentPositions[index];
            const playerIndex = getPlayerIndex(opponent);

            return (
              <motion.div
                key={opponent.player_id}
                data-testid={`opponent-seat-${index}`}
                className="absolute cursor-pointer"
                style={{
                  left: position.left,
                  top: position.top,
                  transform: position.transform,
                  zIndex: focusedElement === `opponent-${index}` ? 50 : 10
                }}
                onClick={() => setFocusedElement(
                  focusedElement === `opponent-${index}` ? null : `opponent-${index}`
                )}
                animate={{
                  scale: focusedElement === `opponent-${index}` ? 1.1 : 1
                }}
                transition={{ type: 'spring', stiffness: 300 }}
              >
                <PlayerSeat
                  player={opponent}
                  isCurrentTurn={
                    gameState.current_player_index !== null &&
                    gameState.players[gameState.current_player_index]?.player_id === opponent.player_id
                  }
                  aiDecision={gameState.last_ai_decisions[opponent.player_id]}
                  showAiThinking={showAiThinking}
                  isShowdown={isShowdown}
                  isDealer={playerIndex === gameState.dealer_position}
                  isSmallBlind={playerIndex === gameState.small_blind_position}
                  isBigBlind={playerIndex === gameState.big_blind_position}
                />
              </motion.div>
            );
          })}

          {/* Center area - Pot + Community Cards */}
          <motion.div
            data-testid="community-cards-area"
            className="absolute cursor-pointer flex flex-col items-center gap-4"
            style={{
              left: centerPosition.left,
              top: centerPosition.top,
              transform: centerPosition.transform,
              zIndex: focusedElement === 'community' ? 50 : 20
            }}
            onClick={() => setFocusedElement(
              focusedElement === 'community' ? null : 'community'
            )}
            animate={{
              scale: focusedElement === 'community' ? 1.05 : 1
            }}
          >
            {/* Pot Display */}
            <motion.div
              data-testid="pot-display"
              className="bg-[#D97706] text-white px-6 py-3 rounded-full text-2xl sm:text-3xl font-bold shadow-2xl"
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 1, repeat: Infinity, repeatDelay: 2 }}
            >
              Pot: ${gameState.pot}
            </motion.div>

            {/* Community Cards */}
            <div className={`transition-all rounded-xl ${
              focusedElement === 'community' ? 'ring-4 ring-yellow-400 shadow-lg shadow-yellow-400/50 p-2' : ''
            }`}>
              <CommunityCards
                cards={gameState.community_cards}
                gameState={gameState.state}
              />
            </div>
          </motion.div>

          {/* Human Player */}
          <motion.div
            data-testid="human-player-seat"
            className="absolute cursor-pointer"
            style={{
              left: humanPosition.left,
              top: humanPosition.top,
              transform: humanPosition.transform,
              zIndex: focusedElement === 'human' ? 50 : 10
            }}
            onClick={() => setFocusedElement(
              focusedElement === 'human' ? null : 'human'
            )}
            animate={{
              scale: focusedElement === 'human' ? 1.1 : 1
            }}
          >
            <PlayerSeat
              player={gameState.human_player}
              isCurrentTurn={isMyTurn}
              showAiThinking={showAiThinking}
              isShowdown={isShowdown}
              isDealer={gameState.players.findIndex(p => p.is_human) === gameState.dealer_position}
              isSmallBlind={gameState.players.findIndex(p => p.is_human) === gameState.small_blind_position}
              isBigBlind={gameState.players.findIndex(p => p.is_human) === gameState.big_blind_position}
            />
          </motion.div>
        </div>

        {/* Action Buttons - OUTSIDE container */}
        <div
          data-testid="action-buttons-container"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-50"
        >
          {/* ... existing action buttons ... */}
        </div>
      </div>

      {/* Modals - stay the same */}
    </div>
  );
}
```

**Tests:**
- [ ] 4-player table: 3 opponents distributed evenly (180°, 90°, 0°)
- [ ] 6-player table: 5 opponents distributed evenly (180°, 135°, 90°, 45°, 0°)
- [ ] No overlaps between players at any screen size
- [ ] Human player always centered at bottom
- [ ] Center area always centered
- [ ] Click-to-focus works (z-index changes properly)
- [ ] Framer Motion animations smooth

---

### Phase 4: Responsive Optimization
**Duration:** 45 minutes

**Tasks:**
1. Add mobile-specific adjustments (scale PlayerSeat components)
2. Ensure touch targets ≥44px on mobile
3. Test landscape mode
4. Add container query for ultra-small screens

**Mobile Optimizations:**

```tsx
// frontend/components/PlayerSeat.tsx (add responsive scaling)

export function PlayerSeat({ player, isCurrentTurn, /* ... */ }: PlayerSeatProps) {
  return (
    <motion.div
      data-testid={`player-seat-${player.player_id}`}
      className={`
        relative bg-gray-800/90 backdrop-blur-sm rounded-xl p-2 sm:p-3 border-2
        min-w-[120px] sm:min-w-[140px]
        ${isCurrentTurn ? 'border-yellow-400 shadow-lg shadow-yellow-400/50' : 'border-gray-600'}
      `}
      style={{
        // Mobile: scale down slightly to fit more players
        transform: typeof window !== 'undefined' && window.innerWidth < 640
          ? 'scale(0.85)'
          : 'scale(1)'
      }}
    >
      {/* ... existing seat content ... */}
    </motion.div>
  );
}
```

```tsx
// frontend/components/PokerTable.tsx - Mobile container adjustment

<div
  data-testid="poker-table-container"
  className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
  style={{
    // Mobile: Allow smaller max-height to fit action buttons
    width: 'min(100vw - 2rem, 90vh * 1.6)',
    aspectRatio: '16 / 10',
    maxWidth: '1400px',
    maxHeight: typeof window !== 'undefined' && window.innerWidth < 640
      ? '70vh'  // Mobile: Leave room for buttons
      : '85vh'  // Desktop: Larger
  }}
>
```

**Tests:**
- [ ] iPhone SE (375x667) - portrait
- [ ] iPhone SE (667x375) - landscape
- [ ] iPad (768x1024) - portrait
- [ ] Desktop (1920x1080)
- [ ] Touch targets ≥44px on mobile
- [ ] No horizontal scrolling
- [ ] Action buttons always accessible

---

### Phase 5: Visual Polish & E2E Testing
**Duration:** 60 minutes

**Tasks:**
1. Add poker table visual enhancements (inset shadow, border glow)
2. Ensure dealer/blind badges always visible
3. Add subtle hover effects
4. Run E2E tests with Playwright
5. Cross-browser testing

**Visual Enhancements:**

```tsx
// Enhanced container styling
<div
  data-testid="poker-table-container"
  className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
  style={{
    width: 'min(100vw - 2rem, 90vh * 1.6)',
    aspectRatio: '16 / 10',
    maxWidth: '1400px',
    maxHeight: '85vh',
    boxShadow: `
      inset 0 2px 20px rgba(0, 0, 0, 0.3),
      0 8px 32px rgba(0, 0, 0, 0.4),
      0 0 80px rgba(13, 95, 47, 0.5)
    `
  }}
>
```

```tsx
// Enhanced focus effect
<motion.div
  // ... existing props ...
  animate={{
    scale: focusedElement === `opponent-${index}` ? 1.1 : 1,
    zIndex: focusedElement === `opponent-${index}` ? 50 : 10
  }}
  whileHover={{ scale: 1.05 }}
  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
>
```

**E2E Tests:**

```typescript
// e2e/poker-table-layout.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Poker Table Layout', () => {
  test('should position 4-player table correctly', async ({ page }) => {
    await page.goto('/game?players=4');
    await page.waitForSelector('[data-testid="poker-table-container"]');

    // Check container aspect ratio
    const container = page.locator('[data-testid="poker-table-container"]');
    const box = await container.boundingBox();
    expect(box!.width / box!.height).toBeCloseTo(1.6, 1); // 16:10 = 1.6

    // Check 3 opponents visible
    const opponents = page.locator('[data-testid^="opponent-seat-"]');
    await expect(opponents).toHaveCount(3);

    // Check human player at bottom
    const human = page.locator('[data-testid="human-player-seat"]');
    const humanBox = await human.boundingBox();
    const containerBox = await container.boundingBox();
    expect(humanBox!.y + humanBox!.height).toBeGreaterThan(containerBox!.y + containerBox!.height * 0.8);
  });

  test('should handle viewport resize without overlaps', async ({ page }) => {
    await page.goto('/game?players=6');

    // Test desktop size
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('[data-testid^="opponent-seat-"]')).toHaveCount(5);

    // Test mobile size
    await page.setViewportSize({ width: 375, height: 667 });

    // Check no overlaps (all players visible)
    const opponents = page.locator('[data-testid^="opponent-seat-"]');
    const count = await opponents.count();

    for (let i = 0; i < count; i++) {
      await expect(opponents.nth(i)).toBeVisible();
    }

    // Action buttons still visible
    await expect(page.locator('[data-testid="action-buttons-container"]')).toBeVisible();
  });
});
```

**Test Matrix:**
| Viewport | 4 Players | 6 Players | Notes |
|----------|-----------|-----------|-------|
| 375x667 (iPhone SE) | ✓ | ✓ | Portrait, buttons visible |
| 667x375 (iPhone SE) | ✓ | ✓ | Landscape, container fits |
| 768x1024 (iPad) | ✓ | ✓ | Portrait |
| 1024x768 (iPad) | ✓ | ✓ | Landscape |
| 1920x1080 (Desktop) | ✓ | ✓ | Full HD |

**Browser Testing:**
- [ ] Chrome/Edge (Chromium)
- [ ] Safari (WebKit) - aspect ratio support
- [ ] Firefox (Gecko)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Comparison: Current vs New Approach

| Aspect | Current (Hardcoded) | New (TypeScript Calculated) |
|--------|---------------------|------------------------------|
| **Positioning** | ❌ Manual Tailwind classes | ✅ Mathematical elliptical formula |
| **Scaling** | ❌ Viewport height hacks | ✅ Container aspect ratio |
| **Overlaps** | ❌ Frequent z-index issues | ✅ Proper z-index management |
| **Maintainability** | ❌ Conditional logic per player count | ✅ Single calculation function |
| **Type Safety** | ❌ String-based classes | ✅ TypeScript interfaces |
| **Animations** | ❌ Basic transitions | ✅ Framer Motion spring physics |
| **Responsive** | ❌ Media query band-aids | ✅ Scales naturally with container |
| **Testing** | ❌ Hard to test positions | ✅ Unit testable calculation logic |

## Architecture Advantages

**Leveraging Existing Stack:**
1. **Next.js 15** - Server components for initial render, client components for interactivity
2. **React 19** - Automatic batching improves animation performance
3. **Framer Motion** - Spring physics for natural click-to-focus animations
4. **Tailwind 4** - Utility classes for rapid styling, inline styles for calculated positions
5. **TypeScript** - Type-safe position calculations, interfaces for config
6. **Zustand 5** - Centralized state, doesn't interfere with layout calculations

**Key Decisions:**
- **Inline styles for positions** - Calculated values can't be Tailwind classes
- **Action buttons outside container** - Prevents overlap, always accessible
- **Fixed aspect ratio** - Maintains proportions, no responsive aspect ratio changes
- **Framer Motion for z-index** - Smooth animations when focusing elements
- **TypeScript utilities** - Testable, reusable, type-safe

## Success Criteria

### Must Have:
- ✅ Opponents positioned using mathematical elliptical formula
- ✅ No hardcoded positions (all calculated)
- ✅ Container maintains 16:10 aspect ratio on all screen sizes
- ✅ No overlaps between players
- ✅ Action buttons always visible and accessible
- ✅ Works on mobile (375px) to desktop (1920px)
- ✅ Fits in viewport without scrolling
- ✅ Click-to-focus works with proper z-index management

### Nice to Have:
- ✅ Smooth Framer Motion animations
- ✅ Poker table visual polish (shadows, glow)
- ✅ Hover effects on player seats
- ✅ Unit tests for calculation functions
- ✅ E2E tests for layout validation

## Timeline (Realistic)

- **Phase 1:** 60 min (TypeScript utilities + tests)
- **Phase 2:** 45 min (Container & aspect ratio)
- **Phase 3:** 75 min (Apply calculated positions)
- **Phase 4:** 45 min (Responsive optimization)
- **Phase 5:** 60 min (Polish & E2E testing)

**Total:** ~4.5-5 hours (realistic with testing)

## Implementation Notes

### Why TypeScript Calculation Wins:

1. **Unit Testable** - Can verify positions without rendering components
2. **Type Safe** - Interfaces catch errors at compile time
3. **Maintainable** - Single function handles all player counts
4. **Flexible** - Easy to adjust ellipse parameters
5. **Debuggable** - Can log calculated positions
6. **Reusable** - Same logic works for 3, 5, 7, 9 players

### Configuration Tunables:

```typescript
// Easy to adjust without changing component code
const config: EllipseConfig = {
  centerX: 50,    // Horizontal center (%)
  centerY: 40,    // Vertical center (% - above middle for visual balance)
  radiusX: 42,    // Horizontal radius (%)
  radiusY: 28     // Vertical radius (%)
};
```

### Future Enhancements:

- Add 7-10 player support (just pass different `numOpponents`)
- Add table themes (different ellipse configs)
- Add VIP table layout (smaller radiusY for tighter spacing)
- Add animation on player join/leave (Framer Motion layoutId)

---

**Status:** Ready for implementation
**Priority:** High - Fixes scaling and overlay issues
**Dependencies:** None (uses existing architecture)
**Breaking Changes:** Complete layout refactor (keeps same API surface)

## Next Steps

1. **Create feature branch:** `git checkout -b feat/typescript-elliptical-layout`
2. **Phase 1:** Create `lib/poker-table-layout.ts` with tests
3. **Phase 2:** Update container structure in `PokerTable.tsx`
4. **Phase 3:** Apply calculated positions to all elements
5. **Phase 4:** Add mobile optimizations
6. **Phase 5:** Polish and E2E tests
7. **Commit after each phase** - Easy to rollback if needed
8. **Deploy** when all tests pass

---

## References

- [Ellipse Parametric Equations](https://en.wikipedia.org/wiki/Ellipse#Parametric_representation)
- [CSS Aspect Ratio (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/aspect-ratio)
- [Framer Motion Layout Animations](https://www.framer.com/motion/layout-animations/)
- [TypeScript Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [Professional Poker Table Layouts - PokerStars](https://www.pokertracker.com/guides/PT4/site-configuration/pokerstars-configuration-guide)
