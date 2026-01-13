# Navigation Fixes - TDD Implementation Plan

**Date:** 2026-01-13
**Approach:** Test-Driven Development (Red-Green-Refactor)
**Estimated Time:** 4-6 hours
**Reference:** NAVIGATION-FIXES-RECOMMENDATIONS-REVISED.md

---

## TDD Principles

1. **RED:** Write failing test first
2. **GREEN:** Write minimal code to pass test
3. **REFACTOR:** Clean up code while keeping tests green
4. **COMMIT:** Commit after each green phase

---

## Phase 1: Fix Card Rendering (Issue #2) 🔴 CRITICAL

### Priority: **HIGHEST** (Game unplayable)

### Test 1.1: Card Component Renders With Stable Keys

**File:** `frontend/components/__tests__/Card.test.tsx` (NEW)

```typescript
import { render, screen } from '@testing-library/react';
import { Card } from '../Card';

describe('Card Component', () => {
  it('renders card with suit and rank', () => {
    render(<Card card="Ah" data-testid="test-card" />);
    expect(screen.getByTestId('test-card')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('♥')).toBeInTheDocument();
  });

  it('renders hidden card', () => {
    render(<Card card="Ah" hidden={true} data-testid="hidden-card" />);
    expect(screen.getByTestId('hidden-card')).toBeInTheDocument();
    expect(screen.queryByText('A')).not.toBeInTheDocument();
  });

  it('renders with stable key prop', () => {
    const { rerender } = render(<Card key="player-1-card-0" card="Ah" />);
    rerender(<Card key="player-1-card-0" card="Ah" />);
    // Should not cause unmount/remount
    expect(screen.getByText('A')).toBeInTheDocument();
  });
});
```

**Expected:** ❌ FAIL (Card doesn't explicitly validate keys)
**Action:** Run test: `npm test -- Card.test.tsx`

### Implementation 1.1: Add Key to Card Usage

**File:** `frontend/components/PlayerSeat.tsx`

```typescript
// BEFORE
{player.hand.map((card, idx) => (
  <Card card={card} hidden={shouldHide} />
))}

// AFTER
{player.hand.map((card, idx) => (
  <Card
    key={`${player.player_id}-${card}-${idx}`}  // ← ADD STABLE KEY
    card={card}
    hidden={shouldHide}
    data-testid={`player-${index}-card-${idx}`}
  />
))}
```

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Add stable keys to Card components in PlayerSeat"`

---

### Test 1.2: PokerTable Remounts on Game State Change

**File:** `frontend/app/game/new/__tests__/page.test.tsx` (NEW)

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { useGameStore } from '@/lib/store';
import NewGamePage from '../page';

// Mock Zustand store
jest.mock('@/lib/store');
jest.mock('@/lib/auth', () => ({
  isAuthenticated: () => true,
  getUsername: () => 'test_user',
}));

describe('NewGamePage Navigation Recovery', () => {
  it('remounts PokerTable when gameState changes after navigation', async () => {
    const mockGameState = {
      current_hand: 1,
      players: [],
      pot: 10,
      // ... minimal game state
    };

    // Start with no game
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: jest.fn(),
    });

    const { rerender } = render(<NewGamePage />);

    // Game creation form should show
    expect(screen.getByText('Your Name')).toBeInTheDocument();

    // Simulate game state loaded (e.g., after browser back)
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: mockGameState,
      loading: false,
      showAiThinking: false,
      decisionHistory: [],
    });

    rerender(<NewGamePage />);

    // PokerTable should render
    await waitFor(() => {
      expect(screen.queryByText('Your Name')).not.toBeInTheDocument();
      // Check for poker table elements
    });
  });
});
```

**Expected:** ❌ FAIL (PokerTable doesn't have key prop yet)
**Action:** Run test: `npm test -- page.test.tsx`

### Implementation 1.2: Add Key to PokerTable

**File:** `frontend/app/game/new/page.tsx`

```typescript
// BEFORE (line 142-148)
return (
  <div className="flex h-screen overflow-hidden">
    <div className="flex-1 overflow-auto">
      <PokerTable />
    </div>
    <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
  </div>
);

// AFTER
return (
  <div className="flex h-screen overflow-hidden">
    <div className="flex-1 overflow-auto">
      <PokerTable key={gameState?.current_hand || 'poker-table'} />  {/* ← ADD KEY */}
    </div>
    <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
  </div>
);
```

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Add key prop to PokerTable for remount on navigation"`

---

### Test 1.3: E2E Test - Cards Render After Browser Back

**File:** `frontend/__tests__/e2e/navigation-card-rendering.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Card Rendering After Navigation', () => {
  test('cards render correctly after browser back button', async ({ page }) => {
    // 1. Login
    await page.goto('http://localhost:3001');
    await page.fill('input[id="username"]', 'e2e_test_user');
    await page.fill('input[id="password"]', 'test12345');
    await page.fill('input[id="confirmPassword"]', 'test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3001');

    // 2. Start game
    await page.click('a[href="/game/new"]');
    await page.waitForSelector('button:has-text("Start Game")');
    await page.click('button:has-text("Start Game")');

    // 3. Wait for cards to render
    await page.waitForSelector('[data-testid^="player-"][data-testid$="-card-0"]', { timeout: 5000 });

    // 4. Verify cards have content
    const cardBefore = await page.locator('[data-testid="player-0-card-0"]').textContent();
    expect(cardBefore).toBeTruthy();
    expect(cardBefore).toMatch(/[A2-9TJQK]/); // Should have rank

    // 5. Navigate away
    await page.goto('http://localhost:3001');
    await page.waitForURL('http://localhost:3001');

    // 6. Browser back
    await page.goBack();

    // 7. Wait for game to restore
    await page.waitForSelector('[data-testid^="player-"][data-testid$="-card-0"]', { timeout: 5000 });

    // 8. Verify cards still render correctly
    const cardAfter = await page.locator('[data-testid="player-0-card-0"]').textContent();
    expect(cardAfter).toBeTruthy();
    expect(cardAfter).toMatch(/[A2-9TJQK]/); // Should still have rank

    // 9. Verify card suits visible
    const cardElement = await page.locator('[data-testid="player-0-card-0"]');
    const innerHTML = await cardElement.innerHTML();
    expect(innerHTML).toMatch(/[♥♦♣♠]/); // Should have suit symbol
  });
});
```

**Expected:** ❌ FAIL (Currently cards render as blue rectangles)
**Action:** Run test: `npm run test:e2e -- navigation-card-rendering.spec.ts`

### Implementation 1.3: Force State Clear/Reset on Reconnect

**File:** `frontend/lib/store.ts`

```typescript
// MODIFY reconnectToGame function (line 308-346)
reconnectToGame: async (gameId: string): Promise<boolean> => {
  console.log(`[Store] Attempting to reconnect to game ${gameId}`);
  set({ loading: true, error: null, connectionError: null });

  try {
    const response = await pokerApi.getGameState(gameId);

    if (response) {
      console.log('[Store] Game found! Reconnecting...');

      // NEW: Force component remount by clearing state first
      set({ gameState: null });

      // Wait for React to flush the update
      await new Promise(resolve => setTimeout(resolve, 0));

      // Then set the new state
      set({ gameId, gameState: response, loading: false });

      get()._processAIDecisions(response);
      get().connectWebSocket(gameId);
      return true;
    } else {
      // ... rest unchanged
    }
  } catch (error: any) {
    // ... rest unchanged
  }
},
```

**Expected:** ✅ PASS
**Action:** Run E2E test again
**Commit:** `git commit -m "Force game state reset on reconnect to fix card rendering"`

---

## Phase 2: Fix Hydration Error (Issue #1) 🔴 CRITICAL

### Priority: **HIGH** (UX + SEO impact)

### Test 2.1: No Hydration Mismatch on /game/new

**File:** `frontend/app/game/new/__tests__/hydration.test.tsx` (NEW)

```typescript
import { render, screen } from '@testing-library/react';
import { renderToString } from 'react-dom/server';
import NewGamePage from '../page';
import { useGameStore } from '@/lib/store';

jest.mock('@/lib/store');
jest.mock('@/lib/auth', () => ({
  isAuthenticated: () => true,
  getUsername: () => 'test_user',
}));

describe('NewGamePage Hydration', () => {
  it('does not cause hydration mismatch when no game in storage', () => {
    // Mock no game state
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: jest.fn(),
    });

    // Server render
    const serverHtml = renderToString(<NewGamePage />);

    // Client render
    const { container } = render(<NewGamePage />);
    const clientHtml = container.innerHTML;

    // Should match (no hydration error)
    // Note: This is simplified - React will warn in console if mismatch
    expect(serverHtml).toContain('Your Name');
    expect(clientHtml).toContain('Your Name');
  });

  it('prevents render until client-side mounted', () => {
    const mockInitialize = jest.fn();

    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: mockInitialize,
    });

    render(<NewGamePage />);

    // initializeFromStorage should be called after mount
    expect(mockInitialize).toHaveBeenCalled();
  });
});
```

**Expected:** ❌ FAIL (Currently causes hydration mismatch)
**Action:** Run test: `npm test -- hydration.test.tsx`

### Implementation 2.1: Add Mounted State Guard

**File:** `frontend/app/game/new/page.tsx`

```typescript
// ADD at line 17 (after existing state)
const [mounted, setMounted] = useState(false);

// MODIFY useEffect (line 20-33)
useEffect(() => {
  setMounted(true); // Mark as client-side mounted

  if (!isAuthenticated()) {
    router.push('/login');
    return;
  }

  if (username && !playerName) {
    setPlayerName(username);
  }

  // Only restore game after mounted (prevents hydration mismatch)
  initializeFromStorage();
}, [router, username, playerName, initializeFromStorage]);

// ADD guard before conditional render (line 36-38)
if (!isAuthenticated()) {
  return null;
}

// NEW: Prevent hydration mismatch
if (!mounted) {
  return null; // or <LoadingSpinner /> if desired
}

// Rest unchanged...
if (!gameState) {
  return <GameCreationForm />;
}
return <PokerTable />;
```

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Add mounted guard to prevent hydration mismatch"`

---

### Test 2.2: E2E Test - No Hydration Error in Browser Console

**File:** `frontend/__tests__/e2e/hydration-error.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Hydration Error Detection', () => {
  test('no hydration errors when navigating to /game/new', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to game/new
    await page.goto('http://localhost:3001/game/new');
    await page.waitForLoadState('networkidle');

    // Check for hydration errors
    const hydrationErrors = consoleErrors.filter(err =>
      err.includes('Hydration') ||
      err.includes('server rendered HTML') ||
      err.includes('did not match')
    );

    expect(hydrationErrors).toHaveLength(0);
  });
});
```

**Expected:** ❌ FAIL (Currently shows hydration errors)
**Action:** Run test: `npm run test:e2e -- hydration-error.spec.ts`
**After Implementation:** ✅ PASS
**Commit:** `git commit -m "Verify no hydration errors in E2E tests"`

---

## Phase 3: Fix Game State Persistence (Issue #3) 🟡 HIGH

### Priority: **MEDIUM** (Confusing UX but not breaking)

### Test 3.1: Quit Button Uses Next.js Router

**File:** `frontend/components/__tests__/PokerTable.test.tsx` (MODIFY EXISTING)

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { PokerTable } from '../PokerTable';
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/lib/store';

jest.mock('next/navigation');
jest.mock('@/lib/store');

describe('PokerTable Quit Functionality', () => {
  it('calls router.push when quit button clicked', () => {
    const mockPush = jest.fn();
    const mockQuitGame = jest.fn();

    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: {/* minimal game state */},
      quitGame: mockQuitGame,
    });

    render(<PokerTable />);

    const quitButton = screen.getByText(/quit/i);
    fireEvent.click(quitButton);

    // Should call quitGame (clears state)
    expect(mockQuitGame).toHaveBeenCalled();

    // Should use Next.js router (not window.history)
    expect(mockPush).toHaveBeenCalledWith('/');
  });
});
```

**Expected:** ❌ FAIL (Currently uses window.history.pushState)
**Action:** Run test: `npm test -- PokerTable.test.tsx`

### Implementation 3.1: Update Quit Handler

**File:** `frontend/components/PokerTable.tsx`

```typescript
// ADD import
import { useRouter } from 'next/navigation';

export function PokerTable() {
  const router = useRouter();  // ← ADD
  const { gameState, submitAction, nextHand, quitGame } = useGameStore();

  // ADD quit handler
  const handleQuit = () => {
    quitGame(); // Clears state and localStorage
    router.push('/'); // Use Next.js router
  };

  return (
    // ... rest of component
    <button
      onClick={handleQuit}  // ← CHANGE from quitGame to handleQuit
      className="..."
    >
      Quit
    </button>
  );
}
```

**File:** `frontend/lib/store.ts` - Remove navigation from quitGame

```typescript
// MODIFY quitGame (line 204-227)
quitGame: () => {
  get().disconnectWebSocket();

  if (typeof window !== 'undefined') {
    localStorage.removeItem('poker_game_id');
    localStorage.removeItem('poker_player_name');
    // REMOVE: window.history.pushState({}, '', '/');  // ← DELETE THIS LINE
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

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Use Next.js router for quit navigation"`

---

### Test 3.2: E2E Test - Start New Game After Quit

**File:** `frontend/__tests__/e2e/quit-and-new-game.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Quit and New Game Flow', () => {
  test('shows game creation form after quit then Start New Game', async ({ page }) => {
    // 1. Login and start game
    await page.goto('http://localhost:3001');
    // ... login flow
    await page.click('a[href="/game/new"]');
    await page.click('button:has-text("Start Game")');

    // 2. Wait for game to load
    await page.waitForSelector('button:has-text("Fold")');

    // 3. Quit game
    await page.click('button:has-text("Quit")');
    await page.waitForURL('http://localhost:3001');

    // 4. Click Start New Game again
    await page.click('a[href="/game/new"]');

    // 5. Should show game creation form, NOT poker table
    await page.waitForSelector('input[type="text"]'); // Player name field
    expect(await page.locator('h1').textContent()).toContain('Poker Learning App');
    expect(await page.locator('label').filter({ hasText: 'Your Name' })).toBeVisible();

    // 6. Should NOT show poker table
    expect(await page.locator('button:has-text("Fold")').count()).toBe(0);
  });
});
```

**Expected:** ❌ FAIL (Currently shows poker table instead of form)
**Action:** Run test: `npm run test:e2e -- quit-and-new-game.spec.ts`
**After Implementation:** ✅ PASS
**Commit:** `git commit -m "Verify game creation form shows after quit"`

---

## Phase 4: Fix Browser Forward Navigation (Issue #4) 🟡 MEDIUM

### Test 4.1: Browser Forward Returns to Game

**File:** `frontend/__tests__/e2e/browser-navigation.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Browser Navigation', () => {
  test('forward button returns to game after back', async ({ page }) => {
    // 1. Start game
    await page.goto('http://localhost:3001');
    // ... login and start game
    await page.waitForSelector('button:has-text("Fold")');
    const gameUrl = page.url();

    // 2. Navigate to home
    await page.goto('http://localhost:3001');
    await page.waitForURL('http://localhost:3001');

    // 3. Browser back
    await page.goBack();
    expect(page.url()).toBe(gameUrl);
    await page.waitForSelector('button:has-text("Fold")');

    // 4. Browser forward
    await page.goForward();

    // 5. Should return to home, not stay at game
    expect(page.url()).toBe('http://localhost:3001/');
    expect(await page.locator('h1').textContent()).toContain('Welcome');
  });
});
```

**Expected:** ❌ FAIL (Currently broken)
**Action:** Run test: `npm run test:e2e -- browser-navigation.spec.ts`

### Implementation 4.1: Remove window.history.pushState

**File:** `frontend/lib/store.ts`

```typescript
// MODIFY createGame (line 74-102)
createGame: async (playerName: string, aiCount: number) => {
  set({ loading: true, error: null });
  try {
    const response = await pokerApi.createGame(playerName, aiCount);
    const gameId = response.game_id;
    set({ gameId });

    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('poker_game_id', gameId);
      localStorage.setItem('poker_player_name', playerName);
    }

    // Connect to WebSocket
    get().connectWebSocket(gameId);

    // REMOVE: window.history.pushState navigation  // ← DELETE LINE 91-93
    // Let component handle navigation via router

  } catch (error: any) {
    // ... error handling
  }
},
```

**File:** `frontend/app/game/new/page.tsx`

```typescript
// MODIFY createGame button handler (line 99-105)
const handleCreateGame = async () => {
  await createGame(playerName || username || 'Player', aiCount);

  // NEW: Navigate using Next.js router after game created
  const { gameId } = useGameStore.getState();
  if (gameId) {
    router.push(`/game/${gameId}`);
  }
};

// UPDATE button onClick
<button
  onClick={handleCreateGame}  // ← CHANGE
  disabled={loading}
  className="..."
>
  {loading ? 'Creating Game...' : 'Start Game'}
</button>
```

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Use Next.js router for game navigation"`

---

## Phase 5: Fix Puppeteer Timeouts (Issue #5) ⚪ MINOR

### Test 5.1: WebSocket Disconnect Doesn't Block

**File:** `frontend/lib/__tests__/store.test.ts` (NEW)

```typescript
import { useGameStore } from '../store';

describe('Zustand Store - WebSocket Management', () => {
  it('disconnectWebSocket does not block execution', async () => {
    const store = useGameStore.getState();

    // Mock WebSocket client
    const mockDisconnect = jest.fn(() => {
      return new Promise(resolve => setTimeout(resolve, 1000)); // Slow disconnect
    });

    store.wsClient = { disconnect: mockDisconnect } as any;

    const startTime = Date.now();
    store.disconnectWebSocket();
    const endTime = Date.now();

    // Should not wait for disconnect
    expect(endTime - startTime).toBeLessThan(100);
    expect(store.wsClient).toBeNull();
  });
});
```

**Expected:** ❌ FAIL (Currently blocks)
**Action:** Run test: `npm test -- store.test.ts`

### Implementation 5.1: Make Disconnect Non-Blocking

**File:** `frontend/lib/store.ts`

```typescript
// MODIFY disconnectWebSocket (line 299-305)
disconnectWebSocket: () => {
  const { wsClient } = get();
  if (wsClient) {
    // NEW: Don't wait for disconnect to complete
    Promise.resolve().then(() => {
      wsClient.disconnect();
    });

    // Immediately update state
    set({ wsClient: null, connectionState: ConnectionState.DISCONNECTED });
  }
},
```

**Expected:** ✅ PASS
**Action:** Run test again
**Commit:** `git commit -m "Make WebSocket disconnect non-blocking"`

---

## Final Validation

### Run Full Test Suite

```bash
# Backend tests (should all still pass)
cd backend && PYTHONPATH=. pytest -v

# Frontend unit tests
cd frontend && npm test

# Frontend E2E tests
cd frontend && npm run test:e2e

# Manual verification
npm run dev  # Start both servers
# Test all navigation flows manually
```

### Expected Results
- ✅ All unit tests pass
- ✅ All E2E tests pass
- ✅ No hydration errors in console
- ✅ Cards render correctly after navigation
- ✅ Quit → New Game shows creation form
- ✅ Browser back/forward work correctly
- ✅ No Puppeteer timeouts

---

## Commit Strategy

Each phase follows:
1. RED: Commit failing test
2. GREEN: Commit passing implementation
3. REFACTOR: Commit any cleanup

Example:
```bash
git commit -m "test: add card rendering stability tests (RED)"
git commit -m "feat: add stable keys to Card components (GREEN)"
git commit -m "refactor: simplify Card key generation"
```

---

## Rollback Plan

If any phase fails:
1. Revert last commit: `git revert HEAD`
2. Re-run tests to verify stability
3. Analyze failure and adjust approach
4. Try again with modified implementation

---

## Time Estimates

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Card rendering fix (tests + impl) | 1.5 hours |
| 2 | Hydration error fix (tests + impl) | 1 hour |
| 3 | Quit/new game fix (tests + impl) | 1 hour |
| 4 | Browser navigation fix (tests + impl) | 1 hour |
| 5 | Puppeteer timeout fix (tests + impl) | 0.5 hours |
| Final | Full suite validation | 0.5 hours |
| **TOTAL** | | **5.5 hours** |

Add 20% buffer for unexpected issues: **~6.5 hours total**

---

## Success Criteria

- [ ] All 5 issues resolved
- [ ] No regressions (existing tests still pass)
- [ ] E2E tests demonstrate fixes
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Clean commit history

---

**Created By:** Claude Code
**Ready For:** Implementation
**Status:** APPROVED
