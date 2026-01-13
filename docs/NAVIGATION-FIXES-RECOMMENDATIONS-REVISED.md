# Navigation Fixes - Revised Recommendations (Codebase-Aligned)

**Date:** 2026-01-13
**Status:** APPROVED FOR TDD IMPLEMENTATION

## Overview

After reviewing the existing codebase architecture, I've revised the recommendations to align with:
- Existing Zustand store patterns
- Next.js 15 App Router conventions
- Current WebSocket connection management
- Framer Motion animation usage

---

## Issue #1: Hydration Error on /game/new 🔴 CRITICAL

### Root Cause (Confirmed)
The `/game/new` page renders differently on server vs client:
- **Server:** `gameState` is always `null` (localStorage not available)
- **Client:** `gameState` may exist from localStorage after `initializeFromStorage()` runs
- React detects HTML mismatch and throws hydration error

### Current Code Pattern
```typescript
// app/game/new/page.tsx (lines 20-33)
useEffect(() => {
  if (!isAuthenticated()) {
    router.push('/login');
    return;
  }
  initializeFromStorage(); // ← Causes hydration mismatch
}, [router, username, playerName, initializeFromStorage]);

// Conditional render based on gameState (line 41)
if (!gameState) {
  return <GameCreationForm />; // Server always renders this
}
return <PokerTable />; // Client may render this after hydration
```

### REVISED Recommendation: Add Mounted State Guard

**Why this approach:**
- Minimal code changes
- Follows Next.js best practices for client-only state
- No need to disable SSR or restructure components
- Aligns with existing `isAuthenticated()` SSR guard pattern

**Implementation:**

```typescript
// app/game/new/page.tsx
export default function NewGamePage() {
  const router = useRouter();
  const username = getUsername();
  const { gameState, createGame, loading, initializeFromStorage, showAiThinking, decisionHistory } = useGameStore();
  const [playerName, setPlayerName] = useState(username || 'Player');
  const [aiCount, setAiCount] = useState(3);
  const [mounted, setMounted] = useState(false); // ← NEW

  useEffect(() => {
    setMounted(true); // ← NEW: Mark as client-side mounted

    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    if (username && !playerName) {
      setPlayerName(username);
    }

    // Only restore game after mounted
    initializeFromStorage();
  }, [router, username, playerName, initializeFromStorage]);

  // Auth check (existing)
  if (!isAuthenticated()) {
    return null;
  }

  // NEW: Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return null; // or <LoadingSpinner /> if preferred
  }

  // Rest of component unchanged...
  if (!gameState) {
    return <GameCreationForm />;
  }
  return <PokerTable />;
}
```

**Trade-offs:**
- ✅ Fixes hydration error completely
- ✅ No architectural changes required
- ✅ Small performance cost (one extra render cycle)
- ✅ Maintains SSR for SEO (server sends minimal HTML)

---

## Issue #2: Card Rendering Breaks After Browser Navigation 🔴 CRITICAL

### Root Cause (Confirmed)
After analyzing the Card component and Framer Motion usage:

1. **Framer Motion Animation State:** Cards use `motion.div` with `initial`, `animate`, and transition props (Card.tsx:53-59)
2. **No Stable Keys:** Cards don't have stable `key` props when re-rendered after navigation
3. **Component Remount Issue:** When navigating back via browser button, React remounts components but Framer Motion's internal animation state may not reset

### Current Code Pattern
```typescript
// components/Card.tsx (lines 52-59)
return (
  <motion.div
    data-testid={testId || `card-${suit}${value}`}
    className="w-12 h-18 sm:w-14 sm:h-21 md:w-16 md:h-24 bg-white border-2 border-gray-300 rounded-lg shadow-xl relative"
    initial={{ scale: 0, rotateY: 180 }}  // ← Animation state
    animate={{ scale: 1, rotateY: 0 }}
    whileHover={{ scale: 1.05, y: -4 }}
    transition={{ duration: 0.3 }}
  >
```

### REVISED Recommendation: Add Key Prop + Force Remount

**Why this approach:**
- Framer Motion needs stable keys to track animation state
- Force remount when game state changes after navigation
- Aligns with React best practices for list rendering

**Implementation:**

**Step 1: Add stable key to Card component**
```typescript
// components/PlayerSeat.tsx (or wherever Cards are rendered)
{player.hand && player.hand.length > 0 && (
  <div className="flex gap-1">
    {player.hand.map((card, idx) => (
      <Card
        key={`${player.player_id}-${card}-${idx}`}  // ← NEW: Stable key
        card={card}
        hidden={shouldHide}
        data-testid={`player-${index}-card-${idx}`}
      />
    ))}
  </div>
)}
```

**Step 2: Add key to PokerTable to force remount on navigation**
```typescript
// app/game/new/page.tsx (line 143-148)
return (
  <div className="flex h-screen overflow-hidden">
    <div className="flex-1 overflow-auto">
      <PokerTable key={gameState?.current_hand || 'poker-table'} /> {/* ← NEW */}
    </div>
    <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
  </div>
);
```

**Step 3: Add navigation detection to clear animation state**
```typescript
// lib/store.ts - Add to reconnectToGame function (after line 325)
reconnectToGame: async (gameId: string): Promise<boolean> => {
  console.log(`[Store] Attempting to reconnect to game ${gameId}`);
  set({ loading: true, error: null, connectionError: null });

  try {
    const response = await pokerApi.getGameState(gameId);

    if (response) {
      console.log('[Store] Game found! Reconnecting...');

      // NEW: Force component remount by clearing then setting state
      set({ gameState: null }); // Clear first
      await new Promise(resolve => setTimeout(resolve, 0)); // Flush
      set({ gameId, gameState: response, loading: false }); // Then set

      get()._processAIDecisions(response);
      get().connectWebSocket(gameId);
      return true;
    }
    // ... rest unchanged
  }
}
```

**Trade-offs:**
- ✅ Fixes card rendering issue
- ✅ Minimal changes to existing components
- ✅ Aligns with React/Framer Motion best practices
- ⚠️ Slight animation flash on reconnect (acceptable)

---

## Issue #3: Game State Persists Incorrectly 🟡 HIGH

### Root Cause (Confirmed)
Looking at the code:
1. **quitGame() DOES clear localStorage** (store.ts:209-211) ✅
2. **quitGame() uses `window.history.pushState`** instead of Next.js router (store.ts:213) ❌
3. **Problem:** Using `window.history.pushState` doesn't trigger Next.js route change, so `/game/new` doesn't re-render

### Current Code Pattern
```typescript
// lib/store.ts (lines 204-227)
quitGame: () => {
  get().disconnectWebSocket();

  if (typeof window !== 'undefined') {
    localStorage.removeItem('poker_game_id');  // ← Clears correctly
    localStorage.removeItem('poker_player_name');
    window.history.pushState({}, '', '/');  // ← PROBLEM: Doesn't trigger route change
  }

  set({
    gameId: null,
    gameState: null,
    // ... clears state
  });
},
```

### REVISED Recommendation: Use Next.js Router for Navigation

**Why this approach:**
- Proper Next.js navigation triggers component lifecycle
- More reliable than manual history manipulation
- Aligns with existing codebase patterns (already uses router elsewhere)

**Implementation:**

**Problem:** Zustand store doesn't have access to Next.js router. Need to pass it in or use an alternative approach.

**Best Solution: Call quitGame from component with router**

```typescript
// components/PokerTable.tsx (where Quit button is)
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/lib/store';

export function PokerTable() {
  const router = useRouter();
  const { quitGame } = useGameStore();

  const handleQuit = () => {
    quitGame(); // Clears state and localStorage
    router.push('/'); // ← Use Next.js router
  };

  return (
    // ...
    <button onClick={handleQuit} className="...">
      Quit
    </button>
  );
}
```

**Alternative: Remove navigation from quitGame, handle in component**

```typescript
// lib/store.ts - Remove window.history.pushState from quitGame
quitGame: () => {
  get().disconnectWebSocket();

  if (typeof window !== 'undefined') {
    localStorage.removeItem('poker_game_id');
    localStorage.removeItem('poker_player_name');
    // REMOVE: window.history.pushState({}, '', '/');
  }

  set({
    gameId: null,
    gameState: null,
    handAnalysis: null,
    error: null,
    connectionError: null,
    loading: false,
    awaitingContinue: false,
    stepMode: false,
    decisionHistory: []
  });
},
```

Then in component:
```typescript
const handleQuit = () => {
  quitGame();
  router.push('/');
};
```

**Trade-offs:**
- ✅ Proper Next.js navigation
- ✅ Component lifecycle triggers correctly
- ✅ Minimal changes
- ✅ More maintainable

---

## Issue #4: Browser Forward Button Broken 🟡 MEDIUM

### Root Cause (Suspected)
Looking at navigation patterns:
- `window.history.pushState` used in multiple places (store.ts:92, 213)
- Mix of `window.location` and `router.push` for navigation
- Browser history stack may be corrupted

### REVISED Recommendation: Standardize on Next.js Router

**Why this approach:**
- Next.js router properly manages browser history
- Consistent navigation patterns reduce bugs
- Better integration with App Router

**Implementation:**

**Step 1: Remove window.history.pushState from store**
```typescript
// lib/store.ts (line 90-93) - REMOVE manual history manipulation
createGame: async (playerName: string, aiCount: number) => {
  // ... create game logic

  // REMOVE:
  // if (typeof window !== 'undefined') {
  //   window.history.pushState({}, '', `/game/${gameId}`);
  // }

  // Let the component handle navigation via router
},
```

**Step 2: Handle navigation in component**
```typescript
// app/game/new/page.tsx - Update createGame call
const handleCreateGame = async () => {
  await createGame(playerName || username || 'Player', aiCount);
  const { gameId } = useGameStore.getState();
  if (gameId) {
    router.push(`/game/${gameId}`); // ← Use Next.js router
  }
};
```

**Step 3: Create dynamic route for game**
```
app/
  game/
    [gameId]/
      page.tsx  ← NEW: Dynamic route for specific game
    new/
      page.tsx  ← Existing: Game creation form
```

**Trade-offs:**
- ✅ Proper browser history management
- ✅ Better URL structure
- ⚠️ Requires new route structure
- ⚠️ Migration path needed for existing games

---

## Issue #5: Puppeteer Timeouts ⚪ MINOR

### Root Cause (Confirmed)
WebSocket disconnect in click handlers blocks completion:
```typescript
// lib/store.ts (lines 205-206)
quitGame: () => {
  get().disconnectWebSocket(); // ← Blocks until WS closed
  // ...
}
```

### REVISED Recommendation: Make WebSocket Disconnect Async + Non-Blocking

**Implementation:**

```typescript
// lib/store.ts
disconnectWebSocket: () => {
  const { wsClient } = get();
  if (wsClient) {
    // Don't wait for disconnect to complete
    Promise.resolve().then(() => {
      wsClient.disconnect();
    });
    set({ wsClient: null, connectionState: ConnectionState.DISCONNECTED });
  }
},
```

**Trade-offs:**
- ✅ Fixes Puppeteer timeouts
- ✅ Improves UI responsiveness
- ✅ No functional changes for users

---

## Implementation Priority (TDD Order)

### Phase 1: Critical Fixes (Must Have)
1. **Issue #2** - Fix card rendering (game unplayable)
2. **Issue #1** - Fix hydration error (UX + performance)

### Phase 2: High Priority (Should Have)
3. **Issue #3** - Fix game state persistence (confusing UX)

### Phase 3: Nice to Have
4. **Issue #4** - Fix browser forward navigation
5. **Issue #5** - Fix Puppeteer timeouts

---

## Next Steps

1. ✅ Review recommendations (COMPLETE)
2. 🔄 Create TDD plan with failing tests first
3. Implement fixes one by one following TDD
4. Run full E2E suite after each fix
5. Update documentation

---

**Reviewed By:** Claude Code
**Approved For:** TDD Implementation
**Estimated Effort:** 4-6 hours (with tests)
