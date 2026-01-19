# Poker Table Split-Panel Layout - Implementation Plan

**Date:** 2026-01-19 (Redesigned)
**Goal:** Two-column layout with poker table (left 70%) and control panel (right 30%)
**Approach:** Split-panel design leveraging elliptical positioning math for table, dedicated control panel for actions
**Philosophy:** Learning app functionality over casino aesthetics

## Problem Analysis

### Why Centered Oval Table Failed:

**User Feedback (2026-01-19):**
> "Why don't we use the room better. Have the table in the left 2/3rd of the screen (or maybe a little more) and then have the action button in the right as a panel."

**Current Issues:**
1. **Wasted horizontal space** - Centered oval leaves ~30% unused on both sides
2. **Poor wide monitor support** - Gets worse on 16:9 displays and ultrawides
3. **Action buttons floating** - Positioned absolutely below table, not part of UI structure
4. **No AI Thinking home** - Future feature has nowhere to go
5. **Casino aesthetic wrong** - This is a LEARNING app, not a visual replica

### Why Split-Panel Works:

**Desktop (≥768px):**
```
┌────────────────────────────────────────────────────────┐
│  POKER TABLE (70%)            │  CONTROL PANEL (30%)   │
│                               │                        │
│    ○    ○    ○                │  ┌──────────────────┐ │
│  ○             ○              │  │  Action Buttons  │ │
│                               │  │  ✓ Fold          │ │
│      💰 Pot: $150             │  │  ✓ Call $20      │ │
│      🂡 🂱 🂲 🂳 🂴             │  │  ✓ Raise         │ │
│                               │  └──────────────────┘ │
│         🂡🂱                   │                        │
│   (Human player)              │  ┌──────────────────┐ │
│                               │  │  AI Thinking     │ │
│                               │  │  (optional)      │ │
│                               │  └──────────────────┘ │
│                               │                        │
│                               │  ┌──────────────────┐ │
│                               │  │  Game Controls   │ │
│                               │  │  • New Hand      │ │
│                               │  │  • Settings      │ │
│                               │  └──────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**Mobile (<768px):**
```
┌──────────────────────────┐
│    POKER TABLE (100%)    │
│                          │
│       ○    ○    ○        │
│     ○           ○        │
│                          │
│       💰 🂡 🂱 🂲        │
│                          │
│          🂡🂱            │
└──────────────────────────┘
┌──────────────────────────┐
│   CONTROL PANEL (100%)   │
│  [Fold] [Call] [Raise]   │
└──────────────────────────┘
```

### Key Improvements:

1. **Better space utilization** - Uses 100% of viewport width
2. **Natural UI structure** - Two-column flex layout (not absolute positioning)
3. **Dedicated control area** - Right panel is consistent, predictable location
4. **AI Thinking integration** - Fits naturally in right panel
5. **Learning-focused** - Prioritizes functionality and clarity
6. **Responsive** - Graceful degradation to mobile vertical stack

---

## Solution: Split-Panel Layout with Elliptical Table

### Core Architecture:

**Two-column flex layout:**
- Left column (70%): Poker table with elliptical player positioning
- Right column (30%): Control panel (buttons, AI thinking, game controls)
- Mobile (<768px): Vertical stack (table full-width, controls below)

**Elliptical positioning still valid:**
- Opponents distributed across 180° arc on table
- Formula: (x, y) = (cx + rx*cos(θ), cy - ry*sin(θ))
- Human player at bottom-center
- Pot and community cards separated at center

### Key Design Decisions:

1. **70/30 split on desktop** - Gives table breathing room while maximizing control panel
2. **Table fills left column** - Aspect ratio maintained (16:10 or adjust to column)
3. **Right panel is scrollable** - Future-proof for coaching insights, hand history
4. **Breakpoint at 768px** - Below this, switch to vertical layout
5. **Pot separated from community cards** - Pot above cards to avoid overlap
6. **Action buttons in dedicated panel** - Always visible, proper z-index

---

## Implementation Phases

### Phase 1: Split-Panel Container Structure
**Duration:** 45 minutes

**Tasks:**
1. Replace single-column layout with two-column flex layout
2. Add responsive breakpoint (desktop vs mobile)
3. Structure right panel with sections (actions, AI thinking placeholder, game controls)
4. Ensure table fills left column properly

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx (new structure)

export function PokerTable() {
  const { gameState, /* ... */ } = useGameStore();
  const [showAiThinking, setShowAiThinking] = useState(false);

  // ... existing state ...

  if (!gameState) return null;

  return (
    <div className="flex flex-col h-screen bg-[#0D5F2F]">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-2 sm:py-3 border-b border-gray-700">
        {/* ... existing header content ... */}
      </div>

      {/* Main Content - Two-column layout on desktop, vertical on mobile */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">

        {/* LEFT COLUMN: Poker Table (70% on desktop, 100% on mobile) */}
        <div className="flex-1 md:w-[70%] flex items-center justify-center p-2 sm:p-4 relative">
          <div
            data-testid="poker-table-container"
            className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
            style={{
              width: '100%',
              maxWidth: 'min(100%, 90vh * 1.6)',
              aspectRatio: '16 / 10',
              boxShadow: `
                inset 0 2px 20px rgba(0, 0, 0, 0.3),
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 0 80px rgba(13, 95, 47, 0.5)
              `
            }}
          >
            {/* Opponents, human player, pot, community cards go here */}
            {/* Using elliptical positioning (Phase 2) */}
          </div>
        </div>

        {/* RIGHT COLUMN: Control Panel (30% on desktop, auto-height on mobile) */}
        <div
          data-testid="control-panel"
          className="w-full md:w-[30%] bg-gray-900 border-t md:border-t-0 md:border-l border-gray-700 flex flex-col"
        >
          {/* Section 1: Action Buttons */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-white text-sm font-semibold mb-3 uppercase tracking-wide">Actions</h3>
            <div className="space-y-2">
              {/* Action buttons go here (Phase 3) */}
            </div>
          </div>

          {/* Section 2: AI Thinking (optional, collapsible) */}
          {showAiThinking && (
            <div className="p-4 border-b border-gray-700 max-h-[300px] overflow-y-auto">
              <h3 className="text-white text-sm font-semibold mb-3 uppercase tracking-wide">AI Thinking</h3>
              <div className="text-gray-300 text-xs space-y-2">
                {/* AI thinking content goes here */}
              </div>
            </div>
          )}

          {/* Section 3: Game Controls */}
          <div className="p-4 mt-auto">
            <div className="space-y-2">
              {/* New Hand, Settings, etc. go here */}
            </div>
          </div>
        </div>
      </div>

      {/* Modals - stay the same */}
    </div>
  );
}
```

**Responsive Tailwind Classes:**
- `flex-col md:flex-row` - Vertical on mobile, horizontal on desktop
- `md:w-[70%]` - 70% width on desktop (≥768px)
- `md:w-[30%]` - 30% width on desktop
- `border-t md:border-t-0 md:border-l` - Top border on mobile, left border on desktop

**Tests:**
- [ ] Desktop (≥768px): Two columns side-by-side
- [ ] Mobile (<768px): Vertical stack (table, then controls)
- [ ] Table fills left column properly
- [ ] Right panel scrollable when content exceeds viewport height
- [ ] Responsive breakpoint triggers at 768px

---

### Phase 2: Elliptical Positioning on Table
**Duration:** 60 minutes

**Tasks:**
1. Apply elliptical positioning utilities (already created in previous implementation)
2. Position opponents across 180° arc
3. Position human player at bottom-center
4. Separate pot display from community cards (pot above, cards below)
5. Adjust ellipse config for wider table (left column is wider than previous centered oval)

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx (table content)

import {
  calculateOpponentPositions,
  getHumanPlayerPosition,
  getCenterAreaPosition
} from '@/lib/poker-table-layout';

export function PokerTable() {
  // ... existing state ...

  // Calculate positions
  const opponents = gameState.players.filter((p) => !p.is_human);
  const opponentPositions = calculateOpponentPositions(opponents.length);
  const humanPosition = getHumanPlayerPosition();
  const potPosition = { left: '50%', top: '40%', transform: 'translate(-50%, -50%)' };
  const cardsPosition = { left: '50%', top: '52%', transform: 'translate(-50%, -50%)' };

  return (
    <div className="flex flex-col h-screen bg-[#0D5F2F]">
      {/* ... header ... */}

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* LEFT COLUMN: Poker Table */}
        <div className="flex-1 md:w-[70%] flex items-center justify-center p-2 sm:p-4 relative">
          <div
            data-testid="poker-table-container"
            className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
            style={{
              width: '100%',
              maxWidth: 'min(100%, 90vh * 1.6)',
              aspectRatio: '16 / 10',
              boxShadow: 'inset 0 2px 20px rgba(0, 0, 0, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 80px rgba(13, 95, 47, 0.5)'
            }}
          >
            {/* Opponents - Elliptical positioning */}
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
                  animate={{ scale: focusedElement === `opponent-${index}` ? 1.1 : 1 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  whileHover={{ scale: 1.05 }}
                >
                  <PlayerSeat
                    player={opponent}
                    isCurrentTurn={gameState.current_player_index !== null &&
                      gameState.players[gameState.current_player_index]?.player_id === opponent.player_id}
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

            {/* Pot Display (separated from community cards) */}
            <motion.div
              data-testid="pot-display"
              className="absolute cursor-pointer"
              style={{
                left: potPosition.left,
                top: potPosition.top,
                transform: potPosition.transform,
                zIndex: 20
              }}
              onClick={() => setFocusedElement(focusedElement === 'pot' ? null : 'pot')}
              animate={{ scale: focusedElement === 'pot' ? 1.1 : 1 }}
            >
              <div className="bg-[#D97706] text-white px-4 sm:px-6 py-2 sm:py-3 rounded-full text-xl sm:text-2xl font-bold shadow-2xl">
                Pot: ${gameState.pot}
              </div>
            </motion.div>

            {/* Community Cards (below pot) */}
            <motion.div
              data-testid="community-cards-area"
              className="absolute cursor-pointer"
              style={{
                left: cardsPosition.left,
                top: cardsPosition.top,
                transform: cardsPosition.transform,
                zIndex: 20
              }}
              onClick={() => setFocusedElement(focusedElement === 'community' ? null : 'community')}
              animate={{ scale: focusedElement === 'community' ? 1.05 : 1 }}
            >
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
              onClick={() => setFocusedElement(focusedElement === 'human' ? null : 'human')}
              animate={{ scale: focusedElement === 'human' ? 1.1 : 1 }}
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
        </div>

        {/* RIGHT COLUMN: Control Panel */}
        {/* ... (from Phase 1) ... */}
      </div>
    </div>
  );
}
```

**Ellipse Configuration (already exists):**
```typescript
// frontend/lib/poker-table-layout.ts
export const DEFAULT_ELLIPSE_CONFIG: EllipseConfig = {
  centerX: 50,
  centerY: 40,
  radiusX: 42,
  radiusY: 28
};
```

**Note:** Existing elliptical positioning utilities from previous implementation are reused. The math is still valid - we're just changing the page layout around the table.

**Tests:**
- [ ] 4-player table: 3 opponents evenly distributed (180°, 90°, 0°)
- [ ] 6-player table: 5 opponents evenly distributed
- [ ] Human player at bottom-center (82% from top)
- [ ] Pot and community cards don't overlap
- [ ] Click-to-focus works on all elements
- [ ] Framer Motion animations smooth

---

### Phase 3: Control Panel Actions
**Duration:** 45 minutes

**Tasks:**
1. Move action buttons from floating position to right panel
2. Style buttons for vertical list layout
3. Add loading states and disabled states
4. Ensure buttons always visible (no scrolling required on desktop)
5. Add responsive button sizing (larger on mobile)

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx (control panel actions)

<div
  data-testid="control-panel"
  className="w-full md:w-[30%] bg-gray-900 border-t md:border-t-0 md:border-l border-gray-700 flex flex-col"
>
  {/* Section 1: Action Buttons */}
  <div className="p-3 sm:p-4 border-b border-gray-700">
    <h3 className="text-white text-sm font-semibold mb-3 uppercase tracking-wide">Your Actions</h3>

    {/* Only show if it's human player's turn */}
    {isMyTurn && !isShowdown && (
      <div className="space-y-2">
        {/* Fold Button */}
        <motion.button
          data-testid="action-fold"
          onClick={() => handleAction('fold')}
          disabled={sendingAction}
          className="w-full px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors min-h-[44px] flex items-center justify-center"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {sendingAction === 'fold' ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Folding...
            </span>
          ) : 'Fold'}
        </motion.button>

        {/* Call/Check Button */}
        <motion.button
          data-testid="action-call"
          onClick={() => handleAction('call')}
          disabled={sendingAction}
          className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors min-h-[44px] flex items-center justify-center"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {sendingAction === 'call' ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {callAmount === 0 ? 'Checking...' : 'Calling...'}
            </span>
          ) : (
            callAmount === 0 ? 'Check' : `Call $${callAmount}`
          )}
        </motion.button>

        {/* Raise Button (with slider) */}
        {canRaise && (
          <div className="space-y-2">
            <motion.button
              data-testid="action-raise"
              onClick={() => handleAction('raise', raiseAmount)}
              disabled={sendingAction}
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors min-h-[44px] flex items-center justify-center"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {sendingAction === 'raise' ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Raising...
                </span>
              ) : `Raise to $${raiseAmount}`}
            </motion.button>

            {/* Raise Slider */}
            <div className="px-1">
              <input
                type="range"
                min={minRaise}
                max={maxRaise}
                step={10}
                value={raiseAmount}
                onChange={(e) => setRaiseAmount(parseInt(e.target.value))}
                disabled={sendingAction}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>${minRaise}</span>
                <span>${maxRaise}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    )}

    {/* Waiting state */}
    {!isMyTurn && !isShowdown && (
      <div className="text-gray-400 text-sm text-center py-6">
        Waiting for other players...
      </div>
    )}

    {/* Showdown state */}
    {isShowdown && (
      <div className="space-y-2">
        <motion.button
          data-testid="action-next-hand"
          onClick={handleNextHand}
          className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors min-h-[44px]"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Next Hand
        </motion.button>
      </div>
    )}
  </div>

  {/* Section 2: AI Thinking (placeholder) */}
  {showAiThinking && (
    <div className="p-3 sm:p-4 border-b border-gray-700 max-h-[300px] overflow-y-auto">
      <h3 className="text-white text-sm font-semibold mb-3 uppercase tracking-wide">AI Thinking</h3>
      <div className="text-gray-300 text-xs space-y-2">
        <p className="text-gray-500 italic">AI thinking display will be integrated here in future updates.</p>
      </div>
    </div>
  )}

  {/* Section 3: Game Controls */}
  <div className="p-3 sm:p-4 mt-auto space-y-2">
    <motion.button
      onClick={() => setShowAiThinking(!showAiThinking)}
      className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
      whileHover={{ scale: 1.02 }}
    >
      {showAiThinking ? 'Hide' : 'Show'} AI Thinking
    </motion.button>

    <motion.button
      onClick={handleQuitGame}
      className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-red-400 rounded-lg text-sm transition-colors"
      whileHover={{ scale: 1.02 }}
    >
      Quit Game
    </motion.button>
  </div>
</div>
```

**Key Features:**
- Vertical button stack (easier on eyes than horizontal)
- Loading states with spinner
- Disabled states during action processing
- Min-height 44px touch targets (mobile accessibility)
- Framer Motion hover/tap animations
- Raise slider integrated in panel
- Clear visual hierarchy

**Tests:**
- [ ] All action buttons work (fold, call, raise)
- [ ] Loading states display during action processing
- [ ] Disabled states prevent double-clicks
- [ ] Raise slider adjusts amount correctly
- [ ] Touch targets ≥44px on mobile
- [ ] Buttons stack vertically in panel
- [ ] Panel scrolls if content exceeds viewport height

---

### Phase 4: Responsive Behavior
**Duration:** 45 minutes

**Tasks:**
1. Test desktop layout (≥768px): Table left, controls right
2. Test mobile layout (<768px): Table full-width, controls below
3. Ensure table scales properly in left column
4. Add smooth transitions at breakpoint
5. Test portrait and landscape orientations

**Responsive Behavior:**

**Desktop (≥768px):**
- Two-column flex layout (`flex-row`)
- Table in left column (70% width, `md:w-[70%]`)
- Control panel in right column (30% width, `md:w-[30%]`)
- Control panel scrollable if content exceeds viewport height
- Table maintains aspect ratio within column

**Tablet (768px - 1024px):**
- Same two-column layout
- Slightly smaller table to fit better
- Control panel may need scrolling for AI thinking section

**Mobile (<768px):**
- Vertical flex layout (`flex-col`)
- Table full-width at top
- Control panel full-width below (auto-height)
- Action buttons horizontally spaced (if needed)
- No scrolling required for actions

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx (responsive adjustments)

<div className="flex-1 flex flex-col md:flex-row overflow-hidden">
  {/* LEFT COLUMN: Poker Table */}
  <div className="flex-1 md:w-[70%] flex items-center justify-center p-2 sm:p-4 relative">
    <div
      data-testid="poker-table-container"
      className="relative bg-[#0D5F2F] rounded-[200px] border-4 border-[#0A4D26] shadow-2xl"
      style={{
        width: '100%',
        maxWidth: 'min(100%, 90vh * 1.6)',
        aspectRatio: '16 / 10',
        // Mobile: Smaller max-height to leave room for controls
        maxHeight: typeof window !== 'undefined' && window.innerWidth < 768
          ? '60vh'
          : '80vh',
        boxShadow: 'inset 0 2px 20px rgba(0, 0, 0, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 80px rgba(13, 95, 47, 0.5)'
      }}
    >
      {/* Players positioned with elliptical math */}
    </div>
  </div>

  {/* RIGHT COLUMN: Control Panel */}
  <div
    data-testid="control-panel"
    className="w-full md:w-[30%] bg-gray-900 border-t md:border-t-0 md:border-l border-gray-700 flex flex-col overflow-y-auto"
    style={{
      // Mobile: Auto-height, no scrolling
      // Desktop: Scrollable if needed
      maxHeight: typeof window !== 'undefined' && window.innerWidth < 768
        ? 'auto'
        : '100%'
    }}
  >
    {/* Control panel sections */}
  </div>
</div>
```

**Alternative Mobile Layout (Horizontal Buttons):**

If vertical button stack feels cramped on mobile, use horizontal layout:

```tsx
{/* Mobile: Horizontal button layout */}
<div className="flex md:flex-col gap-2">
  <button className="flex-1 md:w-full">Fold</button>
  <button className="flex-1 md:w-full">Call</button>
  <button className="flex-1 md:w-full">Raise</button>
</div>
```

**Tests:**
- [ ] Desktop (1920x1080): Two columns, 70/30 split
- [ ] Tablet (768x1024): Two columns, smaller table
- [ ] Mobile portrait (375x667): Vertical stack, table full-width
- [ ] Mobile landscape (667x375): Vertical stack or adjust as needed
- [ ] Smooth transition at 768px breakpoint
- [ ] No horizontal scrolling at any viewport size
- [ ] Control panel scrollable on desktop if needed
- [ ] Action buttons always accessible on mobile

---

### Phase 5: AI Thinking Integration & Polish
**Duration:** 60 minutes

**Tasks:**
1. Add AI thinking display in right panel
2. Make AI thinking section collapsible
3. Add visual polish (shadows, borders, spacing)
4. Add smooth transitions for panel sections
5. Test with real AI thinking data
6. Cross-browser testing

**Implementation:**

```tsx
// frontend/components/PokerTable.tsx (AI Thinking section)

<div
  data-testid="control-panel"
  className="w-full md:w-[30%] bg-gray-900 border-t md:border-t-0 md:border-l border-gray-700 flex flex-col overflow-y-auto"
>
  {/* Section 1: Action Buttons */}
  <div className="p-3 sm:p-4 border-b border-gray-700">
    {/* ... action buttons ... */}
  </div>

  {/* Section 2: AI Thinking (collapsible, scrollable) */}
  <AnimatePresence>
    {showAiThinking && (
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: 'auto', opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="border-b border-gray-700 overflow-hidden"
      >
        <div className="p-3 sm:p-4 max-h-[400px] overflow-y-auto">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-white text-sm font-semibold uppercase tracking-wide">AI Thinking</h3>
            <button
              onClick={() => setShowAiThinking(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>

          {/* AI decisions for each opponent */}
          <div className="space-y-3">
            {opponents.map((opponent, index) => {
              const aiDecision = gameState.last_ai_decisions[opponent.player_id];
              if (!aiDecision) return null;

              return (
                <div key={opponent.player_id} className="bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <span className="text-white text-xs font-semibold">{opponent.name}</span>
                  </div>

                  {/* Decision */}
                  <div className="text-gray-300 text-xs mb-2">
                    <strong>Action:</strong> {aiDecision.action}
                    {aiDecision.amount && ` ($${aiDecision.amount})`}
                  </div>

                  {/* Reasoning (if available) */}
                  {aiDecision.reasoning && (
                    <div className="text-gray-400 text-xs">
                      <strong>Reasoning:</strong> {aiDecision.reasoning}
                    </div>
                  )}

                  {/* Strategy type */}
                  {aiDecision.strategy && (
                    <div className="mt-2 inline-block px-2 py-1 bg-gray-700 rounded text-gray-300 text-[10px] uppercase tracking-wide">
                      {aiDecision.strategy}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Empty state */}
          {opponents.every(opp => !gameState.last_ai_decisions[opp.player_id]) && (
            <div className="text-gray-500 text-xs text-center py-6">
              AI decisions will appear here after opponents act.
            </div>
          )}
        </div>
      </motion.div>
    )}
  </AnimatePresence>

  {/* Section 3: Game Controls */}
  <div className="p-3 sm:p-4 mt-auto space-y-2">
    <motion.button
      onClick={() => setShowAiThinking(!showAiThinking)}
      className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors flex items-center justify-between"
      whileHover={{ scale: 1.02 }}
    >
      <span>{showAiThinking ? 'Hide' : 'Show'} AI Thinking</span>
      <motion.span
        animate={{ rotate: showAiThinking ? 180 : 0 }}
        transition={{ duration: 0.3 }}
      >
        ▼
      </motion.span>
    </motion.button>

    <motion.button
      onClick={handleQuitGame}
      className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-red-400 rounded-lg text-sm transition-colors"
      whileHover={{ scale: 1.02 }}
    >
      Quit Game
    </motion.button>
  </div>
</div>
```

**Visual Polish:**

```css
/* Additional shadow and depth effects */
.control-panel-section {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.control-panel-section:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

**Features:**
- Collapsible AI thinking section with smooth animation
- Scrollable when content exceeds panel height
- Individual AI decision cards with reasoning
- Strategy type badges (e.g., "AGGRESSIVE", "CONSERVATIVE")
- Empty state when no AI decisions available
- Close button in section header
- Auto-expands when AI decisions available (optional)

**Tests:**
- [ ] AI thinking section expands/collapses smoothly
- [ ] AI decisions display correctly (action, reasoning, strategy)
- [ ] Scrolling works when many AI decisions
- [ ] Empty state shows when no decisions
- [ ] Visual polish (shadows, borders) looks professional
- [ ] Cross-browser: Chrome, Safari, Firefox
- [ ] Mobile: AI thinking readable and scrollable

---

## Comparison: Centered Oval vs Split-Panel

| Aspect | Centered Oval (Old) | Split-Panel (New) |
|--------|---------------------|-------------------|
| **Horizontal space usage** | ❌ ~40% wasted on sides | ✅ 100% utilized |
| **Wide monitor support** | ❌ Looks worse on 16:9, ultrawides | ✅ Scales perfectly |
| **Action button placement** | ❌ Floating below table (absolute) | ✅ Dedicated panel (structured) |
| **AI Thinking location** | ❌ Nowhere to go | ✅ Natural fit in right panel |
| **Visual hierarchy** | ❌ Single focus (table) | ✅ Clear two-column structure |
| **Responsive** | ✅ Works but not ideal | ✅ Graceful vertical stack on mobile |
| **Learning app focus** | ❌ Casino aesthetic | ✅ Functionality-first design |
| **Maintainability** | ❌ Absolute positioning hacks | ✅ Flex layout (semantic HTML) |
| **Future features** | ❌ Hard to add (coaching, history) | ✅ Easy to add in right panel |

---

## Success Criteria

### Must Have:
- ✅ Two-column layout on desktop (≥768px): Table 70%, controls 30%
- ✅ Vertical layout on mobile (<768px): Table full-width, controls below
- ✅ Action buttons in dedicated right panel
- ✅ Table uses elliptical positioning (reuse existing math)
- ✅ Pot separated from community cards
- ✅ Control panel scrollable when content exceeds viewport
- ✅ Responsive breakpoint at 768px
- ✅ No wasted horizontal space on wide monitors

### Nice to Have:
- ✅ AI Thinking integrated in right panel (collapsible)
- ✅ Smooth Framer Motion animations for panel sections
- ✅ Visual polish (shadows, borders, depth)
- ✅ Touch-friendly buttons on mobile (≥44px)
- ✅ Hover effects on interactive elements
- ✅ Cross-browser tested

---

## Timeline (Realistic)

- **Phase 1:** 45 min (Split-panel container structure)
- **Phase 2:** 60 min (Elliptical positioning on table)
- **Phase 3:** 45 min (Control panel actions)
- **Phase 4:** 45 min (Responsive behavior)
- **Phase 5:** 60 min (AI Thinking integration & polish)

**Total:** ~4 hours

---

## Architecture Decisions

### Why Split-Panel Wins:

1. **Better space utilization** - Uses 100% of viewport width effectively
2. **Natural UI structure** - Flex layout (not absolute positioning hacks)
3. **Future-proof** - Easy to add coaching, hand history, insights in right panel
4. **Learning app focus** - Prioritizes functionality over casino aesthetics
5. **Responsive by design** - Graceful degradation to mobile vertical stack
6. **Maintainable** - Semantic HTML, clear component boundaries

### Key Technical Decisions:

1. **Two-column flex layout** - `flex flex-col md:flex-row`
2. **70/30 split on desktop** - Gives table breathing room, maximizes control panel
3. **Breakpoint at 768px** - Standard tablet/desktop boundary
4. **Right panel scrollable** - Future-proof for long content (coaching insights)
5. **Elliptical positioning reused** - Mathematical positioning still valid
6. **Pot separated from cards** - Avoids overlap, better visual hierarchy
7. **Framer Motion animations** - Smooth panel transitions and button interactions

### Existing Code Reused:

- `frontend/lib/poker-table-layout.ts` - Elliptical positioning utilities (no changes needed)
- `frontend/lib/__tests__/poker-table-layout.test.ts` - Unit tests (still valid)
- `frontend/components/PlayerSeat.tsx` - Player seat component (no changes needed)
- `frontend/components/CommunityCards.tsx` - Community cards component (no changes needed)

**Only changes:**
- `frontend/components/PokerTable.tsx` - Layout structure (two-column flex)
- Move action buttons from floating position to right panel
- Add AI thinking section in right panel
- Separate pot from community cards on table

---

## Future Enhancements

### Easy Additions (Fits in Right Panel):
1. **Hand History** - Collapsible section below AI thinking
2. **Coaching Insights** - Real-time tips from Claude API
3. **Session Statistics** - Win rate, hands played, earnings
4. **Settings Panel** - AI difficulty, game speed, visual preferences
5. **Tournament Mode** - Bracket display, blind levels
6. **Chat/Notes** - Quick notes during hands

### Example: Coaching Section
```tsx
<div className="p-4 border-b border-gray-700">
  <h3 className="text-white text-sm font-semibold mb-3">Coaching Tip</h3>
  <div className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-3 text-xs text-blue-100">
    💡 With top pair, consider a value bet to build the pot...
  </div>
</div>
```

---

## Files Changed

```
frontend/components/PokerTable.tsx              Modified (layout structure)
frontend/lib/poker-table-layout.ts              No changes (reused)
frontend/lib/__tests__/poker-table-layout.test.ts  No changes (still valid)
docs/POKER-TABLE-ELLIPTICAL-LAYOUT-PLAN.md      Replaced (this document)
```

**No breaking changes:**
- Elliptical positioning math unchanged
- PlayerSeat component unchanged
- CommunityCards component unchanged
- Unit tests still valid

---

## Next Steps

1. **Commit this plan:** `git add docs/ && git commit -m "docs: replace elliptical plan with split-panel layout"`
2. **Create feature branch:** `git checkout -b feat/split-panel-layout`
3. **Phase 1:** Two-column flex layout structure
4. **Phase 2:** Apply elliptical positioning to table
5. **Phase 3:** Move action buttons to right panel
6. **Phase 4:** Test responsive behavior (desktop/mobile)
7. **Phase 5:** Integrate AI thinking and polish
8. **Commit after each phase** - Easy to rollback if needed
9. **Test thoroughly** - Desktop, tablet, mobile (portrait/landscape)
10. **Deploy** when all tests pass

---

**Status:** Ready for implementation
**Priority:** High - Fixes wasted screen space and provides better UX
**Dependencies:** Reuses existing elliptical positioning utilities
**Breaking Changes:** Layout structure only (API surface unchanged)
**User Feedback:** Approved on 2026-01-19

---

## References

- [CSS Flexbox (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Flexible_Box_Layout)
- [Responsive Design Breakpoints (Best Practices)](https://www.freecodecamp.org/news/css-breakpoints-for-responsive-design/)
- [Framer Motion Layout Animations](https://www.framer.com/motion/layout-animations/)
- [Tailwind Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [Ellipse Parametric Equations](https://en.wikipedia.org/wiki/Ellipse#Parametric_representation)
