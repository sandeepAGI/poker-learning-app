# Frontend Testing Enhancement Plan - TDD Execution

**Date Created:** January 11, 2026
**Date Updated:** January 11, 2026
**Status:** In Implementation
**Related:** `frontend-testing-roadmap.md` (specifications), `archive/codex-testing-fixes.md` (Phase 1 backend)

---

## ⚠️ Important Notes

**Line Number References:** This document contains approximate line numbers for reference. Always verify actual file structure before making changes, as line numbers may have shifted due to code updates.

**Existing Tests:** The codebase already contains `frontend/__tests__/short-stack-logic.test.ts`. Phase 2 will add Jest configuration to run this existing test along with new tests.

---

## Executive Summary

This document provides a step-by-step TDD execution plan for implementing frontend testing infrastructure (Phases 2-4). It builds on the investigation findings and answers all critical questions about the current implementation.

**Total Estimated Effort:** 12-16 hours (includes investigation + implementation)

**Implementation Order:**
1. **Phase 0:** Add test IDs to components (1-2 hours) - Prerequisite
2. **Phase 2:** Component tests with Jest + RTL (3-5 hours)
3. **Phase 3a:** Backend test endpoint (1-2 hours)
4. **Phase 3b:** E2E tests with Playwright (3-4 hours)
5. **Phase 4:** Visual regression tests (2-3 hours) - **Nightly CI only**
6. **CI Integration:** Add GitHub Actions workflows (30 min)

---

## Investigation Findings Summary

### 1. Backend Game Structure ✅ ANSWERED

**Question:** What's the structure of `active_games` and how do we manipulate state?

**Finding:** `backend/main.py:49-51`
```python
games: Dict[str, Tuple[PokerGame, float]] = {}
# Keys: game_id (UUID string)
# Values: (PokerGame instance, last_access_timestamp)
```

**Serialization:** `serialize_game_state()` already exists in `websocket_manager.py:145-330`

**Conclusion:**
- Test endpoint implementation is straightforward
- Use existing `serialize_game_state()` function
- Access pattern: `game, timestamp = games[game_id]`

---

### 2. Frontend Component Test IDs ✅ ANSWERED

**Question:** Do `data-testid` attributes already exist?

**Finding:** Almost none exist (only WinnerModal has 4 test IDs)

**Components Needing Test IDs:**

| Component | Current IDs | Needed IDs | Priority |
|-----------|-------------|------------|----------|
| PokerTable.tsx | 0 | 42+ | 🔴 Critical |
| PlayerSeat.tsx | 0 | 6+ per seat | 🔴 Critical |
| CommunityCards.tsx | 0 | 5+ | 🟡 High |
| Card.tsx | 0 | Per-card IDs | 🟡 High |
| WinnerModal.tsx | 4 | Already partial | 🟢 Medium |

**Conclusion:** Phase 0 (add test IDs) is a critical prerequisite before writing tests.

---

### 3. Zustand Store Mocking ✅ ANSWERED

**Question:** How do we mock Zustand store for component tests?

**Finding:** `frontend/lib/store.ts:53`
```typescript
export const useGameStore = create<GameStore>((set, get) => ({
  // Store definition
}))
```

**Store Architecture:**
- Direct export, no getInstance pattern needed
- Zustand allows `useGameStore.setState(mockState)` for direct manipulation
- WebSocket is a `PokerWebSocket` class instance stored in `wsClient` property

**Mocking Strategy:**
```typescript
// Mock WebSocket to prevent real connections
jest.mock('@/lib/websocket', () => ({
  PokerWebSocket: jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    sendAction: jest.fn(),
    disconnect: jest.fn(),
  }))
}))

// Set mock state directly
beforeEach(() => {
  useGameStore.setState({
    gameState: createMockGameState(),
    wsClient: mockWebSocketInstance,
    connectionState: ConnectionState.CONNECTED,
  })
})
```

**Conclusion:** No wrapper needed, use `setState()` directly.

---

### 4. WebSocket Timing in E2E Tests ✅ ANSWERED

**Question:** How do we ensure WebSocket syncs state after `/test/set_game_state` calls?

**Finding:** `frontend/lib/websocket.ts:140-176`
- WebSocket receives `state_update` messages and calls `onStateUpdate(gameState)` callback
- Store updates via `set({ gameState })` immediately
- React re-renders subscribed components

**E2E Strategy:**
1. Call `/test/set_game_state` to manipulate backend
2. WebSocket automatically receives `state_update` broadcast
3. Wait for UI element that reflects the change:
```typescript
await expect(page.locator('[data-testid="human-stack"]')).toContainText('$30')
```

**Conclusion:** No special sync needed - use Playwright's auto-waiting on element assertions.

---

### 5. Implementation Order ✅ DECIDED

**Approach:**
- Phase 0 (test IDs) → Phase 2 (component tests) → Phase 3a (backend endpoint) → Phase 3b (E2E tests) → Phase 4 (visual tests)

**Rationale:**
- Component tests validate approach without backend changes
- E2E tests require both test IDs AND backend endpoint
- Visual tests are lowest priority (marked 🔵 Low in roadmap)

**Parallel Work Possible:**
- Phase 2 component tests can be written while Phase 3a backend endpoint is being implemented (different codebases)

---

### 6. CI Integration ✅ DECIDED

**Question:** Add to existing workflow or create new one?

**Decision:** Create new `.github/workflows/test-frontend.yml`

**Rationale:**
- Frontend tests have different dependencies (Node.js, Playwright)
- Can run in parallel with backend tests for faster feedback
- Easier to debug failures when separated
- Different timeout requirements (E2E tests need longer)

**Pre-commit Hooks:**
- Add component tests (fast: <10s) to pre-commit
- Skip E2E/visual tests in pre-commit (too slow)

---

### 7. Visual Regression Baselines ✅ DECIDED

**Question:** How do we ensure consistent screenshots across environments?

**Decision:** Generate baselines in CI only (ubuntu-latest), run in nightly workflow

**Strategy:**
```yaml
# In nightly CI workflow only
- name: Run visual regression tests
  run: npx playwright test test_responsive_design.spec.ts test_card_sizing.spec.ts

- name: Upload visual diffs on failure
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: visual-diffs
    path: tests/e2e/*-snapshots/
```

**Baseline Management:**
- Baselines stored in `tests/e2e/*-snapshots/` and committed to git
- Generated in CI using ubuntu-latest for consistency
- Updated manually when UI intentionally changes: `npx playwright test --update-snapshots`
- Developers can test locally but baselines may differ slightly (OS/font rendering)

**Rationale:**
- Different OS/browsers render differently (fonts, anti-aliasing)
- CI environment (ubuntu-latest) is consistent and reproducible
- Visual tests are slower, better suited for nightly runs
- Prevents false positives from local OS differences

---

## Phase 0: Add Test IDs to Components

**Goal:** Add `data-testid` attributes to all components for reliable test selection

**Estimated Effort:** 1-2 hours

**Rationale:** Without test IDs, Playwright/RTL tests are fragile (break on text changes, class name refactoring). Test IDs provide stable selectors.

---

### Step 0.1: Add Test IDs to PokerTable.tsx

**File:** `frontend/components/PokerTable.tsx`

**TDD Approach:** Add IDs first (no tests yet - Phase 2 will test)

**Changes:**

```typescript
// Line 276 - Header
<div className="..." data-testid="poker-table-header">

  // Line 296 - Settings button
  <button data-testid="settings-button" ...>
    <Settings className="..." />
  </button>

  // Line 310 - Settings dropdown
  <div className="..." data-testid="settings-menu">
    <button data-testid="analyze-hand-button">Analyze Last Hand</button>
    <button data-testid="session-analysis-button">Session Analysis</button>
    <button data-testid="ai-thinking-toggle">Show AI Thinking</button>
    <button data-testid="step-mode-toggle">Step Mode</button>
  </div>

  // Line 348 - Continue button (step mode)
  <button data-testid="continue-button" ...>
    Continue
  </button>

  // Line 379 - Help button
  <button data-testid="help-button" ...>
    <HelpCircle />
  </button>

  // Line 391 - Quit button
  <button data-testid="quit-button" ...>
    Quit
  </button>

  // Line 367 - Connection status
  <div data-testid="connection-status">
    {connectionState}
  </div>

  // Line 371 - Blind levels
  <div data-testid="blind-levels">
    Blinds: ${gameState.small_blind}/${gameState.big_blind}
  </div>

  // Line 375 - Hand count
  <div data-testid="hand-count">
    Hand #{gameState.hand_count}
  </div>
</div>

// Line 432 - Main game area
<div className="..." data-testid="poker-table-main">

  // Lines 444-547 - Opponent seats
  {opponentPositions.map((player, index) => (
    <div
      key={index}
      data-testid={`opponent-seat-${index}`}
      className="..."
    >
      <PlayerSeat player={player} position={...} />
    </div>
  ))}

  // Lines 552-574 - Community cards area
  <div data-testid="community-cards-area" className="...">
    <div data-testid="pot-display">
      Pot: ${gameState.pot}
    </div>
    <CommunityCards
      cards={gameState.community_cards}
      stage={gameState.state}
    />
  </div>

  // Lines 576-591 - Human player seat
  <div
    data-testid="human-player-seat"
    className="human-player-position"
  >
    <PlayerSeat player={humanPlayer} position="bottom" />
  </div>

  // Lines 593-762 - Action buttons
  <div data-testid="action-buttons-container" className="...">
    {isMyTurn ? (
      <>
        <button data-testid="fold-button" ...>Fold</button>
        <button data-testid="call-button" ...>
          Call {callLabel}
        </button>
        <button data-testid="raise-button" ...>
          Raise
        </button>

        {/* Raise panel */}
        {showRaisePanel && (
          <div data-testid="raise-panel" ...>
            <input
              type="range"
              data-testid="raise-amount-slider"
              min={minRaise}
              max={maxRaise}
              value={raiseAmount}
              ...
            />
            <button data-testid="min-raise-button">Min</button>
            <button data-testid="half-pot-button">1/2 Pot</button>
            <button data-testid="pot-button">Pot</button>
            <button data-testid="2x-pot-button">2x Pot</button>
            <button data-testid="all-in-button">All In</button>
            <button data-testid="confirm-raise-button">
              Confirm Raise
            </button>
          </div>
        )}
      </>
    ) : (
      <>
        {gameState.state === 'showdown' && (
          <button data-testid="next-hand-button" ...>
            Next Hand
          </button>
        )}
        {humanPlayer.all_in && (
          <div data-testid="all-in-message">All-In!</div>
        )}
      </>
    )}
  </div>
</div>

{/* Step mode banner */}
{stepMode && (
  <div data-testid="step-mode-banner">
    Step Mode: ON
  </div>
)}

{/* Awaiting continue message */}
{awaitingContinue && (
  <div data-testid="waiting-for-continue">
    WAITING FOR CONTINUE
  </div>
)}

{/* Error message */}
{error && (
  <div data-testid="error-message">{error}</div>
)}
```

**Verification:**
```bash
# After changes, verify no TS errors
cd frontend
npm run build
```

**Commit:**
```bash
git add frontend/components/PokerTable.tsx
git commit -m "TEST PREP: Add test IDs to PokerTable component

- Add 30+ data-testid attributes for reliable test selection
- Covers action buttons, settings, game state displays
- Required for Phase 2 component tests and Phase 3 E2E tests"
```

---

### Step 0.2: Add Test IDs to PlayerSeat.tsx

**File:** `frontend/components/PlayerSeat.tsx`

**Changes:**

```typescript
// Line 28 - Main container
<div className="..." data-testid={`player-seat-${player.player_id}`}>

  // Line 39-55 - Button indicators
  {isDealer && (
    <div data-testid={`dealer-button-${player.player_id}`}>D</div>
  )}
  {isSmallBlind && (
    <div data-testid={`small-blind-button-${player.player_id}`}>SB</div>
  )}
  {isBigBlind && (
    <div data-testid={`big-blind-button-${player.player_id}`}>BB</div>
  )}

  // Line 59 - Player name
  <div data-testid={`player-name-${player.player_id}`}>
    {player.name}
  </div>

  // Line 61 - Personality badge
  {showPersonality && (
    <div data-testid={`personality-${player.player_id}`}>
      {player.personality}
    </div>
  )}

  // Line 64 - All-in badge
  {player.all_in && (
    <div data-testid={`all-in-badge-${player.player_id}`}>
      All-In
    </div>
  )}

  // Lines 68-77 - Hole cards
  <div data-testid={`hole-cards-${player.player_id}`}>
    {player.hole_cards.map((card, idx) => (
      <Card
        key={idx}
        card={card}
        hidden={shouldHideCards}
        data-testid={`hole-card-${player.player_id}-${idx}`}
      />
    ))}
  </div>

  // Lines 81-95 - Stack and bet
  <div data-testid={`stack-display-${player.player_id}`}>
    Stack: ${player.stack}
  </div>

  {player.current_bet > 0 && (
    <div data-testid={`current-bet-${player.player_id}`}>
      Bet: ${player.current_bet}
    </div>
  )}
</div>
```

**Commit:**
```bash
git add frontend/components/PlayerSeat.tsx
git commit -m "TEST PREP: Add test IDs to PlayerSeat component

- Add per-player test IDs for seats, cards, stacks
- Use player_id in test IDs for uniqueness
- Required for E2E player state assertions"
```

---

### Step 0.3: Add Test IDs to CommunityCards.tsx

**File:** `frontend/components/CommunityCards.tsx`

**Changes:**

```typescript
// Line 24 - Main container
<div data-testid="community-cards-container" className="...">

  // Lines 27-36 - Stage label
  {stage !== 'pre_flop' && (
    <div data-testid="stage-label" className="...">
      {stage === 'flop' && 'FLOP'}
      {stage === 'turn' && 'TURN'}
      {stage === 'river' && 'RIVER'}
    </div>
  )}

  // Lines 39-62 - Cards
  <div className="..." data-testid="community-cards-list">
    {cards.map((card, index) => (
      <Card
        key={index}
        card={card}
        data-testid={`community-card-${index}`}
      />
    ))}
  </div>
</div>
```

**Commit:**
```bash
git add frontend/components/CommunityCards.tsx
git commit -m "TEST PREP: Add test IDs to CommunityCards component

- Add container and stage label test IDs
- Add per-card indexed test IDs
- Required for E2E game state verification"
```

---

### Step 0.4: Add Test IDs to Card.tsx

**File:** `frontend/components/Card.tsx`

**Changes:**

```typescript
// Card component receives data-testid as prop (passed from parent)
interface CardProps {
  card: string;
  hidden?: boolean;
  'data-testid'?: string;  // Accept test ID from parent
}

export default function Card({ card, hidden = false, 'data-testid': testId }: CardProps) {
  // ... existing code

  if (hidden) {
    return (
      <div
        data-testid={testId || 'hidden-card'}
        className="..."
      >
        {/* Card back */}
      </div>
    )
  }

  return (
    <div
      data-testid={testId || `card-${suit}${rank}`}
      className="..."
    >
      {/* Card front */}
    </div>
  )
}
```

**Note:** Test IDs are passed from parent components (PlayerSeat, CommunityCards)

**Commit:**
```bash
git add frontend/components/Card.tsx
git commit -m "TEST PREP: Add test ID support to Card component

- Accept data-testid as prop from parent
- Default to card-{suit}{rank} if not provided
- Allows both indexed and card-specific test IDs"
```

---

### Step 0.5: Verify WinnerModal Test IDs

**File:** `frontend/components/WinnerModal.tsx`

**Finding:** Already has test IDs:
- `winner-modal` (line 95)
- `winner-announcement` (line 115)
- `winner-amount` (line 200)
- `winner-${index}` (line 159)

**Action:** No changes needed, verify existing IDs are correct

---

### Step 0.6: Verify Build

**Command:**
```bash
cd frontend
npm run build
```

**Expected:** No TypeScript errors, build succeeds

**If errors:** Fix type issues (likely from new `data-testid` props)

---

### Phase 0 Checkpoint

**Completed:**
- ✅ All components have test IDs
- ✅ Test IDs use consistent naming (`component-element-id`)
- ✅ Per-item IDs use indices or unique keys
- ✅ Build passes without errors

**Git Status:**
```bash
git log --oneline -5
# Should show 4-5 commits for test ID additions
```

**Ready for:** Phase 2 (Component Tests)

---

## Phase 2: Component Tests (Jest + React Testing Library)

**Goal:** Add unit tests for critical React components

**Estimated Effort:** 3-5 hours

**TDD Approach:** Write failing tests first, then ensure they pass with existing code

---

### Step 2.1: Install Dependencies

**Check Latest Versions:**
```bash
cd frontend
# Check latest React Testing Library version (must support React 19)
npm view @testing-library/react versions --json | tail -1
```

**Install (use latest compatible versions):**
```bash
npm install --save-dev \
  @testing-library/react@latest \
  @testing-library/jest-dom@latest \
  @testing-library/user-event@latest \
  jest@^29.7.0 \
  jest-environment-jsdom@^29.7.0 \
  @types/jest@^29.5.11
```

**Note:** React 19 requires @testing-library/react@^15.0.0 or higher. If installation fails with peer dependency errors, check compatibility.

**Verify:**
```bash
npm list @testing-library/react
# Should show version compatible with React 19
```

---

### Step 2.2: Create Jest Configuration

**File:** `frontend/jest.config.js` (NEW)

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: [
    '**/__tests__/**/*.test.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThresholds: {
    global: {
      statements: 70,
      branches: 60,
      functions: 70,
      lines: 70,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

**Commit:**
```bash
git add frontend/jest.config.js
git commit -m "TEST INFRA: Add Jest configuration for component tests

- Use next/jest for Next.js compatibility
- Configure jsdom environment for React rendering
- Set up module aliases and coverage collection"
```

---

### Step 2.3: Create Jest Setup File

**File:** `frontend/jest.setup.js` (NEW)

```javascript
import '@testing-library/jest-dom'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock WebSocket (used by PokerWebSocket class)
// This prevents real WebSocket connections during tests
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    this.onopen = null
    this.onclose = null
    this.onerror = null
    this.onmessage = null

    // Simulate async open
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(data) {
    // Mock send - do nothing
  }

  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new Event('close'))
    }
  }

  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
}

// Global test cleanup
afterEach(() => {
  jest.clearAllMocks()
  jest.clearAllTimers()
})
```

**Commit:**
```bash
git add frontend/jest.setup.js
git commit -m "TEST INFRA: Add Jest setup with browser API mocks

- Mock matchMedia for responsive components
- Mock localStorage for store persistence
- Mock WebSocket to prevent real connections
- Import jest-dom for extended matchers"
```

---

### Step 2.4: Create Test Utilities

**File:** `frontend/__tests__/utils/test-utils.tsx` (NEW, create directory first)

```bash
mkdir -p frontend/__tests__/utils
```

```typescript
import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

/**
 * Create a mock GameState object for testing.
 * Provides sensible defaults and allows overrides.
 */
export function createMockGameState(overrides: Partial<any> = {}) {
  const mockPlayer = {
    player_id: 'human',
    name: 'Human',
    stack: 1000,
    current_bet: 0,
    total_invested: 0,
    hole_cards: [],
    is_active: true,
    is_current_turn: true,
    all_in: false,
    is_human: true,
    folded: false,
  }

  const defaultState = {
    state: 'pre_flop',
    pot: 0,
    current_bet: 0,
    small_blind: 5,
    big_blind: 10,
    last_raise_amount: null,
    dealer_position: 0,
    small_blind_position: 1,
    big_blind_position: 2,
    current_player_index: 0,
    hand_count: 1,
    players: [
      mockPlayer,
      { ...mockPlayer, player_id: 'ai1', name: 'AI 1', is_human: false, is_current_turn: false },
      { ...mockPlayer, player_id: 'ai2', name: 'AI 2', is_human: false, is_current_turn: false },
      { ...mockPlayer, player_id: 'ai3', name: 'AI 3', is_human: false, is_current_turn: false },
    ],
    human_player: mockPlayer,
    community_cards: [],
    last_ai_decisions: {},
  }

  return {
    ...defaultState,
    ...overrides,
    // Merge players if provided
    players: overrides.players || defaultState.players,
    human_player: overrides.human_player || defaultState.human_player,
  }
}

/**
 * Create a mock Player object.
 */
export function createMockPlayer(overrides: Partial<any> = {}) {
  return {
    player_id: 'test-player',
    name: 'Test Player',
    stack: 1000,
    current_bet: 0,
    total_invested: 0,
    hole_cards: [],
    is_active: true,
    is_current_turn: false,
    all_in: false,
    is_human: false,
    folded: false,
    personality: 'Balanced',
    ...overrides,
  }
}

/**
 * Custom render that can inject providers if needed.
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions
) {
  return render(ui, { ...options })
}

// Re-export everything from React Testing Library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
```

**Commit:**
```bash
git add frontend/__tests__/utils/test-utils.tsx
git commit -m "TEST INFRA: Add test utilities for component tests

- createMockGameState() for mock game states
- createMockPlayer() for mock player data
- renderWithProviders() for custom rendering
- Re-export RTL for convenience"
```

---

### Step 2.5: Add Package.json Scripts

**File:** `frontend/package.json`

**Add to `scripts` section:**
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

**Commit:**
```bash
git add frontend/package.json
git commit -m "TEST INFRA: Add test scripts to package.json

- test: Run tests once
- test:watch: Watch mode for development
- test:coverage: Generate coverage report
- test:ci: CI-optimized (deterministic, parallel)"
```

---

### Step 2.6: Write PokerTable Action Button Tests (TDD)

**File:** `frontend/__tests__/PokerTable.test.tsx` (NEW)

**TDD Approach:**
1. Write failing test
2. Run test (should fail with "Cannot find module" or similar)
3. Fix imports/mocks
4. Test should pass (existing code is correct)

```typescript
/**
 * @jest-environment jsdom
 */
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, createMockGameState } from './utils/test-utils'
import PokerTable from '@/components/PokerTable'
import { useGameStore } from '@/lib/store'
import { ConnectionState } from '@/lib/websocket'

// Mock the WebSocket class
jest.mock('@/lib/websocket', () => ({
  PokerWebSocket: jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    sendAction: jest.fn(),
    sendContinue: jest.fn(),
    disconnect: jest.fn(),
  })),
  ConnectionState: {
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    RECONNECTING: 'reconnecting',
    FAILED: 'failed',
  },
}))

describe('PokerTable - Action Buttons', () => {
  beforeEach(() => {
    // Reset store before each test
    useGameStore.setState({
      gameId: 'test-game',
      gameState: null,
      wsClient: null,
      connectionState: ConnectionState.CONNECTED,
      loading: false,
      error: null,
      connectionError: null,
      showAiThinking: false,
      stepMode: false,
      awaitingContinue: false,
      handAnalysis: null,
      decisionHistory: [],
    })
  })

  it('enables Call button when short stack', async () => {
    // Setup: player with $30, facing $80 bet
    const gameState = createMockGameState({
      human_player: {
        ...createMockGameState().human_player,
        stack: 30,
        is_current_turn: true,
      },
      current_bet: 80,
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    // Wait for component to render
    await waitFor(() => {
      const callButton = screen.getByTestId('call-button')
      expect(callButton).toBeInTheDocument()
      expect(callButton).not.toBeDisabled()
    })
  })

  it('enables Raise button when short stack', async () => {
    // Setup: player with $30, can raise all-in
    const gameState = createMockGameState({
      human_player: {
        ...createMockGameState().human_player,
        stack: 30,
        is_current_turn: true,
      },
      current_bet: 20,
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    await waitFor(() => {
      const raiseButton = screen.getByTestId('raise-button')
      expect(raiseButton).toBeInTheDocument()
      expect(raiseButton).not.toBeDisabled()
    })
  })

  it('disables buttons when eliminated', async () => {
    // Setup: player with $0, not active
    const gameState = createMockGameState({
      human_player: {
        ...createMockGameState().human_player,
        stack: 0,
        is_active: false,
        is_current_turn: false,
      },
      current_player_index: 1,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    await waitFor(() => {
      expect(screen.queryByTestId('call-button')).not.toBeInTheDocument()
      expect(screen.queryByTestId('raise-button')).not.toBeInTheDocument()
    })
  })

  it('disables buttons when all-in waiting', async () => {
    // Setup: player all-in, waiting for showdown
    const gameState = createMockGameState({
      human_player: {
        ...createMockGameState().human_player,
        stack: 0,
        all_in: true,
        is_current_turn: false,
      },
      current_player_index: 1,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    await waitFor(() => {
      expect(screen.queryByTestId('call-button')).not.toBeInTheDocument()
      expect(screen.queryByTestId('raise-button')).not.toBeInTheDocument()
      expect(screen.getByTestId('all-in-message')).toBeInTheDocument()
    })
  })

  it('shows All-In button in raise panel when active', async () => {
    const gameState = createMockGameState({
      human_player: {
        ...createMockGameState().human_player,
        stack: 50,
        is_current_turn: true,
      },
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    const { container } = renderWithProviders(<PokerTable />)

    // Click Raise to open panel
    await waitFor(() => {
      const raiseButton = screen.getByTestId('raise-button')
      raiseButton.click()
    })

    // Wait for panel to appear
    await waitFor(() => {
      expect(screen.getByTestId('raise-panel')).toBeInTheDocument()
      expect(screen.getByTestId('all-in-button')).toBeInTheDocument()
    })
  })
})
```

**Run Test (TDD - expect failures first):**
```bash
cd frontend
npm test -- PokerTable.test.tsx
```

**Expected on First Run:**
- Tests might fail if test IDs don't match exactly
- Fix test ID names to match Phase 0 implementation
- Re-run until all pass

**When All Pass:**
```bash
git add frontend/__tests__/PokerTable.test.tsx
git commit -m "TEST: Add PokerTable action button tests (5 tests)

- Test short-stack call/raise button enablement
- Test eliminated player button hiding
- Test all-in player button hiding
- Test raise panel All-In button visibility
- All tests passing with existing code"
```

---

### Step 2.7: Write Raise Slider Tests

**File:** `frontend/__tests__/PokerTable.test.tsx` (EXTEND)

**Add to existing file:**

```typescript
describe('PokerTable - Raise Slider', () => {
  beforeEach(() => {
    useGameStore.setState({
      gameId: 'test-game',
      gameState: null,
      wsClient: null,
      connectionState: ConnectionState.CONNECTED,
      loading: false,
      error: null,
    })
  })

  it('respects minRaise from backend', async () => {
    const gameState = createMockGameState({
      current_bet: 20,
      last_raise_amount: 10,
      big_blind: 10,
      human_player: {
        ...createMockGameState().human_player,
        stack: 200,
        is_current_turn: true,
      },
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    // Open raise panel
    await waitFor(() => {
      screen.getByTestId('raise-button').click()
    })

    // Check slider min attribute
    await waitFor(() => {
      const slider = screen.getByTestId('raise-amount-slider') as HTMLInputElement
      expect(slider).toBeInTheDocument()

      // Min raise = current_bet + last_raise_amount = 20 + 10 = 30
      expect(Number(slider.min)).toBe(30)
    })
  })

  it('sets slider max to stack + current_bet', async () => {
    const gameState = createMockGameState({
      current_bet: 20,
      human_player: {
        ...createMockGameState().human_player,
        stack: 100,
        current_bet: 10, // Already posted blind
        is_current_turn: true,
      },
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    // Open raise panel
    await waitFor(() => {
      screen.getByTestId('raise-button').click()
    })

    // Check slider max attribute
    await waitFor(() => {
      const slider = screen.getByTestId('raise-amount-slider') as HTMLInputElement
      expect(slider).toBeInTheDocument()

      // Max = stack + current_bet = 100 + 10 = 110
      expect(Number(slider.max)).toBe(110)
    })
  })

  it('disables slider when short stack below minRaise', async () => {
    const gameState = createMockGameState({
      current_bet: 100,
      last_raise_amount: 50,
      human_player: {
        ...createMockGameState().human_player,
        stack: 30, // Can't meet min raise of 150
        is_current_turn: true,
      },
      current_player_index: 0,
    })

    useGameStore.setState({ gameState })

    renderWithProviders(<PokerTable />)

    // Open raise panel
    await waitFor(() => {
      screen.getByTestId('raise-button').click()
    })

    // Slider should be disabled
    await waitFor(() => {
      const slider = screen.getByTestId('raise-amount-slider') as HTMLInputElement
      expect(slider).toBeDisabled()
    })

    // But All-In button should be available
    await waitFor(() => {
      const allInButton = screen.getByTestId('all-in-button')
      expect(allInButton).not.toBeDisabled()
    })
  })
})
```

**Run Tests:**
```bash
npm test -- PokerTable.test.tsx
```

**When All Pass:**
```bash
git add frontend/__tests__/PokerTable.test.tsx
git commit -m "TEST: Add raise slider validation tests (3 tests)

- Test minRaise calculation from backend state
- Test maxRaise includes current bet
- Test slider disables below minRaise but All-In available
- Total: 8 PokerTable tests passing"
```

---

### Step 2.8: Write WinnerModal Tests

**File:** `frontend/__tests__/WinnerModal.test.tsx` (NEW)

```typescript
/**
 * @jest-environment jsdom
 */
import { screen } from '@testing-library/react'
import { renderWithProviders } from './utils/test-utils'
import WinnerModal from '@/components/WinnerModal'

describe('WinnerModal - Split Pot Display', () => {
  it('displays "Split Pot!" for two winners', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 50 },
      { player_id: 'ai1', name: 'AI 1', amount: 50 },
    ]

    renderWithProviders(
      <WinnerModal
        winners={winners}
        pot={100}
        onClose={jest.fn()}
        onNextHand={jest.fn()}
      />
    )

    expect(screen.getByText(/Split Pot!/i)).toBeInTheDocument()
  })

  it('displays "Split Pot!" for three winners', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 33 },
      { player_id: 'ai1', name: 'AI 1', amount: 33 },
      { player_id: 'ai2', name: 'AI 2', amount: 34 },
    ]

    renderWithProviders(
      <WinnerModal
        winners={winners}
        pot={100}
        onClose={jest.fn()}
        onNextHand={jest.fn()}
      />
    )

    expect(screen.getByText(/Split Pot!/i)).toBeInTheDocument()
  })

  it('shows individual amounts for each winner', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 51 },
      { player_id: 'ai1', name: 'AI 1', amount: 50 },
    ]

    renderWithProviders(
      <WinnerModal
        winners={winners}
        pot={101}
        onClose={jest.fn()}
        onNextHand={jest.fn()}
      />
    )

    // Check for amounts in the UI
    expect(screen.getByText(/Human/)).toBeInTheDocument()
    expect(screen.getByText(/\$51/)).toBeInTheDocument()
    expect(screen.getByText(/AI 1/)).toBeInTheDocument()
    expect(screen.getByText(/\$50/)).toBeInTheDocument()
  })

  it('displays hand ranks at showdown', () => {
    const winners = [
      {
        player_id: 'human',
        name: 'Human',
        amount: 100,
        hand_rank: 'Royal Flush',
      },
    ]

    renderWithProviders(
      <WinnerModal
        winners={winners}
        pot={100}
        onClose={jest.fn()}
        onNextHand={jest.fn()}
      />
    )

    expect(screen.getByText(/Royal Flush/i)).toBeInTheDocument()
  })
})
```

**Run Tests:**
```bash
npm test -- WinnerModal.test.tsx
```

**When All Pass:**
```bash
git add frontend/__tests__/WinnerModal.test.tsx
git commit -m "TEST: Add WinnerModal split pot tests (4 tests)

- Test split pot message for 2-way tie
- Test split pot message for 3-way tie
- Test individual winner amounts displayed
- Test hand ranks shown at showdown
- All tests passing"
```

---

### Step 2.9: Write Store Step Mode Tests

**File:** `frontend/__tests__/store.test.ts` (NEW)

```typescript
import { renderHook, act } from '@testing-library/react'
import { useGameStore } from '@/lib/store'
import { createMockGameState } from './utils/test-utils'

describe('GameStore - Step Mode', () => {
  beforeEach(() => {
    // Reset store state
    useGameStore.setState({
      stepMode: false,
      awaitingContinue: false,
      gameState: null,
      wsClient: null,
    })
  })

  it('toggles stepMode flag', () => {
    const { result } = renderHook(() => useGameStore())

    act(() => {
      result.current.toggleStepMode()
    })

    expect(result.current.stepMode).toBe(true)

    act(() => {
      result.current.toggleStepMode()
    })

    expect(result.current.stepMode).toBe(false)
  })

  it('calls WebSocket when sendContinue invoked', () => {
    const mockSend = jest.fn()

    // Mock WebSocket connection
    useGameStore.setState({
      wsClient: { sendContinue: mockSend } as any,
      stepMode: true,
      awaitingContinue: true,
    })

    const { result } = renderHook(() => useGameStore())

    act(() => {
      result.current.sendContinue()
    })

    expect(mockSend).toHaveBeenCalledTimes(1)
  })

  it('sets awaitingContinue when step mode active', () => {
    const { result } = renderHook(() => useGameStore())

    act(() => {
      useGameStore.setState({
        stepMode: true,
        awaitingContinue: true,
      })
    })

    expect(result.current.awaitingContinue).toBe(true)
  })

  it('persists stepMode across hands', () => {
    const { result } = renderHook(() => useGameStore())

    act(() => {
      result.current.toggleStepMode()
    })

    expect(result.current.stepMode).toBe(true)

    // Simulate new hand starting (gameState update)
    act(() => {
      useGameStore.setState({
        gameState: createMockGameState({ hand_count: 2 }),
      })
    })

    // Step mode should still be on
    expect(result.current.stepMode).toBe(true)
  })
})
```

**Run Tests:**
```bash
npm test -- store.test.ts
```

**When All Pass:**
```bash
git add frontend/__tests__/store.test.ts
git commit -m "TEST: Add Zustand store step mode tests (4 tests)

- Test step mode toggle functionality
- Test sendContinue calls WebSocket
- Test awaitingContinue flag management
- Test step mode persists across hands
- All tests passing"
```

---

### Phase 2 Checkpoint

**Run All Component Tests:**
```bash
cd frontend
npm test
```

**Expected Output:**
```
Test Suites: 3 passed, 3 total
Tests:       16 passed, 16 total
Snapshots:   0 total
Time:        2.5s
```

**Coverage Report:**
```bash
npm run test:coverage
```

**Expected Coverage:**
- PokerTable.tsx: 60-70% (core logic covered)
- WinnerModal.tsx: 80-90% (simple component)
- store.ts: 40-50% (only step mode tested)

**Commit Summary:**
```bash
git add -A
git commit -m "PHASE 2 COMPLETE: Component tests with Jest + RTL

Summary:
- 16 component tests implemented and passing
- Jest + RTL infrastructure configured
- Test utilities created (createMockGameState)
- Coverage: PokerTable, WinnerModal, store
- All tests run in <3 seconds

Test Breakdown:
- PokerTable action buttons: 5 tests
- PokerTable raise slider: 3 tests
- WinnerModal split pot: 4 tests
- Store step mode: 4 tests

Ready for Phase 3 (E2E tests)"
```

---

## Phase 3a: Backend Test Endpoint

**Goal:** Add `/test/set_game_state` endpoint for E2E test state manipulation

**Estimated Effort:** 1-2 hours

**Security:** CRITICAL - only enable in TEST_MODE

---

### Step 3a.1: Add TEST_MODE Environment Variable Check

**File:** `backend/main.py`

**Add near top of file (after imports, around line 30):**

```python
import os

# Test mode flag - ONLY enable in test environments
TEST_MODE = os.getenv("TEST_MODE") == "1"

if TEST_MODE:
    logger.warning("⚠️  TEST_MODE is ENABLED - Test endpoints are active")
    logger.warning("⚠️  NEVER deploy to production with TEST_MODE=1")
```

**Commit:**
```bash
git add backend/main.py
git commit -m "TEST INFRA: Add TEST_MODE environment variable

- TEST_MODE=1 enables test endpoints
- Logs warning when enabled
- Required for E2E test state manipulation"
```

---

### Step 3a.2: Add Test Endpoint for Game State Manipulation

**File:** `backend/main.py`

**Add after existing endpoints (around line 400):**

```python
# ============================================================================
# TEST ENDPOINTS (Only available when TEST_MODE=1)
# ============================================================================

if TEST_MODE:
    @app.post("/test/set_game_state")
    async def set_game_state_for_testing(request: dict):
        """
        Manipulate game state for E2E testing.

        WARNING: Only available when TEST_MODE=1 env var set.
        NEVER deploy to production with TEST_MODE enabled.

        Example payload:
        {
            "game_id": "test-game-123",
            "player_stacks": {"human": 30, "ai1": 1000, "ai2": 1000},
            "dealer_position": 0,
            "current_bet": 80,
            "pot": 0,
            "state": "pre_flop",
            "community_cards": ["Ah", "Kh", "Qh"]
        }

        Returns: Updated game state (serialized)
        """
        game_id = request.get("game_id")

        if not game_id:
            raise HTTPException(status_code=400, detail="game_id required")

        if game_id not in games:
            raise HTTPException(status_code=404, detail="Game not found")

        game, _ = games[game_id]

        # Apply state modifications with validation
        if "player_stacks" in request:
            for player_name, stack in request["player_stacks"].items():
                # Validate stack is non-negative
                if stack < 0:
                    raise HTTPException(status_code=400, detail=f"Invalid stack: {stack}")

                # Find player by name (case-insensitive)
                player = next(
                    (p for p in game.players if p.name.lower() == player_name.lower()),
                    None
                )
                if player:
                    player.stack = stack
                    logger.info(f"[TEST] Set {player.name} stack to ${stack}")
                else:
                    logger.warning(f"[TEST] Player not found: {player_name}")

        if "dealer_position" in request:
            game.dealer_index = request["dealer_position"]
            logger.info(f"[TEST] Set dealer position to {game.dealer_index}")

        if "current_bet" in request:
            game.current_bet = request["current_bet"]
            logger.info(f"[TEST] Set current bet to ${game.current_bet}")

        if "pot" in request:
            game.pot = request["pot"]
            logger.info(f"[TEST] Set pot to ${game.pot}")

        if "state" in request:
            from game.poker_engine import GameState
            game.current_state = GameState(request["state"])
            logger.info(f"[TEST] Set game state to {game.current_state}")

        if "community_cards" in request:
            import re
            cards = request["community_cards"]

            # Validate card format (e.g., "Ah", "Kd", "2c")
            for card in cards:
                if not re.match(r'^[2-9TJQKA][hdsc]$', card):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid card format: {card}. Expected format: rank[2-9TJQKA] + suit[hdsc]"
                    )

            game.community_cards = cards
            logger.info(f"[TEST] Set community cards to {game.community_cards}")

        if "current_player_index" in request:
            game.current_player_index = request["current_player_index"]
            logger.info(f"[TEST] Set current player index to {game.current_player_index}")

        # Recalculate total chips for conservation check
        game.total_chips = sum(p.stack for p in game.players) + game.pot

        # Update access time
        games[game_id] = (game, time.time())

        # Serialize and return new state
        from websocket_manager import serialize_game_state
        state = serialize_game_state(game, show_ai_thinking=False)

        # Broadcast state update to all connected WebSocket clients
        await manager.broadcast_game_state(game_id, game)

        return {
            "success": True,
            "game_id": game_id,
            "game_state": state
        }

    @app.get("/test/health")
    async def test_health():
        """Health check for E2E tests"""
        return {
            "status": "ok",
            "test_mode": True,
            "message": "Test endpoints are active"
        }

    @app.get("/test/games/{game_id}")
    async def test_get_game_state(game_id: str):
        """Get full game state (for debugging E2E tests)"""
        if game_id not in games:
            raise HTTPException(status_code=404, detail="Game not found")

        game, _ = games[game_id]
        games[game_id] = (game, time.time())

        from websocket_manager import serialize_game_state
        state = serialize_game_state(game, show_ai_thinking=True)

        return {
            "game_id": game_id,
            "game_state": state
        }
```

**Commit:**
```bash
git add backend/main.py
git commit -m "TEST INFRA: Add test endpoints for E2E state manipulation

Endpoints (TEST_MODE=1 only):
- POST /test/set_game_state - Manipulate game state
- GET /test/health - Test mode health check
- GET /test/games/{game_id} - Debug game state

Features:
- Set player stacks, dealer position, pot, bets
- Set game state (pre_flop, flop, turn, river)
- Set community cards, current player
- Broadcasts state updates to WebSocket clients
- Maintains chip conservation

Security:
- Only available when TEST_MODE=1
- Logs all state manipulations
- Never deploy to production with TEST_MODE enabled"
```

---

### Step 3a.3: Test the Endpoint Locally

**Start backend in TEST_MODE:**
```bash
cd backend
TEST_MODE=1 python main.py
```

**Verify test endpoints are active:**
```bash
# Terminal 2
curl http://localhost:8000/test/health
# Expected: {"status":"ok","test_mode":true,"message":"Test endpoints are active"}
```

**Create a test game:**
```bash
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_name": "TestPlayer", "ai_count": 3}'
# Expected: {"game_id":"some-uuid"}
```

**Manipulate game state:**
```bash
GAME_ID="<paste-game-id-here>"

curl -X POST http://localhost:8000/test/set_game_state \
  -H "Content-Type: application/json" \
  -d "{
    \"game_id\": \"$GAME_ID\",
    \"player_stacks\": {\"TestPlayer\": 30, \"AI 1\": 1000, \"AI 2\": 1000, \"AI 3\": 1000},
    \"current_bet\": 80,
    \"pot\": 0,
    \"state\": \"pre_flop\"
  }"
# Expected: {"success":true,"game_id":"...","game_state":{...}}
```

**Verify state changed:**
```bash
curl http://localhost:8000/test/games/$GAME_ID
# Expected: game_state with TestPlayer stack = 30
```

**Stop backend** (Ctrl+C)

---

### Step 3a.4: Add Deployment Safety Check

**File:** `.github/workflows/test-frontend.yml` (will create in Phase 3b)

**Add deployment check:**
```yaml
  # Prevent accidental deployment with TEST_MODE
  - name: Verify TEST_MODE not in production config
    run: |
      if grep -r "TEST_MODE=1" .env* 2>/dev/null; then
        echo "ERROR: TEST_MODE=1 found in .env files"
        exit 1
      fi
      echo "✓ No TEST_MODE in deployment configs"
```

---

### Phase 3a Checkpoint

**Completed:**
- ✅ TEST_MODE environment variable check
- ✅ `/test/set_game_state` endpoint implemented
- ✅ `/test/health` endpoint for E2E health checks
- ✅ `/test/games/{id}` debug endpoint
- ✅ Manual testing verified endpoint works
- ✅ Security warnings added

**Ready for:** Phase 3b (E2E Tests)

---

## Phase 3b: E2E Tests (Playwright)

**Goal:** Add end-to-end tests using Playwright

**Estimated Effort:** 3-4 hours

---

### Step 3b.1: Install Playwright

**Command:**
```bash
cd frontend
npm install --save-dev @playwright/test@^1.40.0
npx playwright install chromium
```

**Verify:**
```bash
npx playwright --version
# Expected: Version 1.40.x
```

---

### Step 3b.2: Create Playwright Configuration

**File:** `frontend/playwright.config.ts` (NEW)

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: '../tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      command: 'cd ../backend && TEST_MODE=1 python main.py',
      url: 'http://localhost:8000/test/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
  ],
})
```

**Commit:**
```bash
git add frontend/playwright.config.ts
git commit -m "TEST INFRA: Add Playwright configuration for E2E tests

- Auto-start backend in TEST_MODE
- Auto-start frontend dev server
- Capture screenshots on failure
- Retry flaky tests in CI
- Single worker in CI for stability"
```

---

### Step 3b.3: Create E2E Test Directory

**Command:**
```bash
mkdir -p tests/e2e/fixtures
```

---

### Step 3b.4: Write Short-Stack E2E Tests

**File:** `tests/e2e/test_short_stack_ui.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Short-Stack UI', () => {
  let gameId: string

  test.beforeEach(async ({ page }) => {
    // Navigate and create game
    await page.goto('http://localhost:3000')

    // Verify New Game button exists and click
    const newGameButton = page.locator('text=New Game')
    await expect(newGameButton).toBeVisible({ timeout: 10000 })
    await newGameButton.click()

    // Wait for game to be created and URL to change
    await page.waitForURL(/\/game\/[a-f0-9-]{36}/, { timeout: 10000 })

    // Extract and validate game ID from URL
    const url = page.url()
    gameId = url.split('/').pop() || ''

    // Validate UUID format
    expect(gameId).toMatch(/^[a-f0-9-]{36}$/)

    // Wait for poker table to be ready
    await expect(page.getByTestId('poker-table-main')).toBeVisible({ timeout: 10000 })
  })

  test('allows call all-in when stack < call amount', async ({ page, request }) => {
    // Manipulate game state via test endpoint
    const response = await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: {
          'Human': 30,
          'AI 1': 1000,
          'AI 2': 1000,
          'AI 3': 1000
        },
        current_bet: 80,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    expect(response.ok()).toBeTruthy()

    // Wait for WebSocket to update UI (check for stack change)
    const callButton = page.getByTestId('call-button')
    await expect(callButton).toBeEnabled({ timeout: 5000 })

    // Verify shows "All-In" with correct amount
    await expect(callButton).toContainText('All-In', { timeout: 2000 })
    await expect(callButton).toContainText('$30')

    // Click and verify action succeeds
    await callButton.click()

    // Verify player is all-in (check for all-in badge or message)
    await expect(page.getByTestId('all-in-message')).toBeVisible({ timeout: 5000 })
  })

  test('allows raise all-in when stack < min raise', async ({ page, request }) => {
    // Setup: player with $30, min raise is $40
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: {
          'Human': 30,
          'AI 1': 1000,
          'AI 2': 1000,
          'AI 3': 1000
        },
        current_bet: 20,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    // Wait for UI to update, then click Raise to open panel
    const raiseButton = page.getByTestId('raise-button')
    await expect(raiseButton).toBeEnabled({ timeout: 5000 })
    await raiseButton.click()

    // Verify All-In button available in raise panel
    const allInButton = page.getByTestId('all-in-button')
    await expect(allInButton).toBeEnabled({ timeout: 2000 })

    // Click All-In
    await allInButton.click()

    // Verify all-in succeeded
    await expect(page.getByTestId('all-in-message')).toBeVisible({ timeout: 5000 })
  })

  test('shows correct call button label for short stack', async ({ page, request }) => {
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: {
          'Human': 15,
          'AI 1': 1000,
          'AI 2': 1000,
          'AI 3': 1000
        },
        current_bet: 50,
        pot: 0,
        state: 'pre_flop',
        current_player_index: 0,
      },
    })

    // Wait for UI to update and verify label shows "Call All-In $15" (not "Call $50")
    const callButton = page.getByTestId('call-button')
    await expect(callButton).toBeEnabled({ timeout: 5000 })
    await expect(callButton).toContainText('All-In')
    await expect(callButton).toContainText('$15')
    await expect(callButton).not.toContainText('$50')
  })
})
```

**Run Test:**
```bash
cd frontend
npx playwright test test_short_stack_ui.spec.ts --headed
```

**Expected:** Tests should pass if Phase 0 test IDs are correct

**When Passing:**
```bash
git add tests/e2e/test_short_stack_ui.spec.ts
git commit -m "TEST: Add short-stack E2E tests (3 tests)

- Test call all-in when stack < call amount
- Test raise all-in when stack < min raise
- Test call button label shows correct amount
- All tests using /test/set_game_state endpoint
- Tests verify UI responds to backend state changes"
```

---

### Step 3b.5: Write Winner Modal E2E Tests

**File:** `tests/e2e/test_winner_modal.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Winner Modal - Split Pot', () => {
  let gameId: string

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    const url = page.url()
    gameId = url.split('/').pop() || ''
  })

  test('displays "Split Pot!" for two-way tie', async ({ page, request }) => {
    // Create scenario: Royal flush on board (all players tie)
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        community_cards: ['Ah', 'Kh', 'Qh', 'Jh', 'Th'],
        player_stacks: {
          'Human': 950,
          'AI 1': 950,
          'AI 2': 0,  // Folded
          'AI 3': 0,  // Folded
        },
        pot: 100,
        state: 'river',
        current_player_index: 0,
      },
    })

    // Wait for UI to update
    await expect(page.getByTestId('fold-button')).toBeEnabled({ timeout: 5000 })

    // Fold to trigger showdown
    await page.getByTestId('fold-button').click()

    // Wait for winner modal
    await expect(page.getByTestId('winner-modal')).toBeVisible({ timeout: 10000 })

    // Verify split pot message
    await expect(page.getByText(/Split Pot!/i)).toBeVisible()

    // Verify both winners shown
    await expect(page.getByText(/Human/)).toBeVisible()
    await expect(page.getByText(/AI 1/)).toBeVisible()
  })

  test('displays three-way split correctly', async ({ page, request }) => {
    // Create scenario: All 3 active players have same hand
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        community_cards: ['Ah', 'Kh', 'Qh', 'Jh', 'Th'],
        player_stacks: {
          'Human': 967,
          'AI 1': 967,
          'AI 2': 967,
          'AI 3': 0,  // Folded
        },
        pot: 99,
        state: 'river',
      },
    })

    await page.waitForTimeout(500)

    // Trigger showdown
    await page.getByTestId('fold-button').click()
    await page.waitForTimeout(2000)

    // Verify split pot
    await expect(page.getByTestId('winner-modal')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/Split Pot!/i)).toBeVisible()

    // Verify all three winners shown
    await expect(page.getByText(/Human/)).toBeVisible()
    await expect(page.getByText(/AI 1/)).toBeVisible()
    await expect(page.getByText(/AI 2/)).toBeVisible()
  })

  test('shows individual amounts sum to pot', async ({ page, request }) => {
    // Setup: $101 pot, 2 winners (odd chip)
    await request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        community_cards: ['Ah', 'Kh', 'Qh', 'Jh', 'Th'],
        player_stacks: {
          'Human': 949,
          'AI 1': 950,
          'AI 2': 0,
          'AI 3': 0,
        },
        pot: 101,
        state: 'river',
      },
    })

    await page.waitForTimeout(500)

    await page.getByTestId('fold-button').click()
    await page.waitForTimeout(2000)

    await expect(page.getByTestId('winner-modal')).toBeVisible({ timeout: 10000 })

    // Verify amounts displayed ($51 and $50, or similar split)
    const modalText = await page.getByTestId('winner-modal').textContent()

    // Check that both winner amounts are shown
    expect(modalText).toMatch(/\$5[01]/)  // Should show $50 or $51
  })
})
```

**Run Test:**
```bash
npx playwright test test_winner_modal.spec.ts --headed
```

**When Passing:**
```bash
git add tests/e2e/test_winner_modal.spec.ts
git commit -m "TEST: Add winner modal E2E tests (3 tests)

- Test split pot display for 2-way tie
- Test split pot display for 3-way tie
- Test individual amounts sum to pot
- Tests create tie scenarios via test endpoint
- Verify modal displays correct winner information"
```

---

### Step 3b.6: Write Step Mode E2E Tests

**File:** `tests/e2e/test_step_mode.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Step Mode', () => {
  let gameId: string

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    const url = page.url()
    gameId = url.split('/').pop() || ''
  })

  test('pauses AI when step mode enabled', async ({ page }) => {
    // Enable step mode via settings
    await page.getByTestId('settings-button').click()
    await page.getByTestId('step-mode-toggle').click()

    // Verify step mode indicator visible
    await expect(page.getByTestId('step-mode-banner')).toBeVisible()

    // Make an action (fold)
    await page.getByTestId('fold-button').click()

    // Verify "Continue" button appears (AI paused)
    await expect(page.getByTestId('continue-button')).toBeVisible({ timeout: 5000 })

    // Verify awaiting continue message
    await expect(page.getByTestId('waiting-for-continue')).toBeVisible()
  })

  test('advances single AI turn when Continue clicked', async ({ page }) => {
    // Enable step mode
    await page.getByTestId('settings-button').click()
    await page.getByTestId('step-mode-toggle').click()

    // Fold to trigger AI turns
    await page.getByTestId('fold-button').click()

    // Wait for Continue button
    await expect(page.getByTestId('continue-button')).toBeVisible({ timeout: 5000 })

    // Click Continue
    await page.getByTestId('continue-button').click()

    // Continue button should reappear (next AI turn) or hand is complete
    // Use a small delay for state transition
    await page.waitForLoadState('networkidle')

    // Check if continue button reappeared or hand completed
    const continueVisible = await page.getByTestId('continue-button').isVisible({ timeout: 2000 })
    const nextHandVisible = await page.getByTestId('next-hand-button').isVisible({ timeout: 2000 })

    // One of these should be true (either more AI turns or hand complete)
    expect(continueVisible || nextHandVisible).toBeTruthy()
  })

  test('completes full hand in step mode', async ({ page }) => {
    // Enable step mode
    await page.getByTestId('settings-button').click()
    await page.getByTestId('step-mode-toggle').click()

    // Fold
    await page.getByTestId('fold-button').click()

    // Click Continue repeatedly until hand completes
    let continueCount = 0
    const maxContinues = 10

    while (continueCount < maxContinues) {
      const continueButton = page.getByTestId('continue-button')

      if (await continueButton.isVisible({ timeout: 2000 })) {
        await continueButton.click()
        continueCount++
        // Wait for state transition
        await page.waitForLoadState('networkidle')
      } else {
        // Hand completed
        break
      }
    }

    // Verify hand completed (next hand button or winner modal visible)
    const handCompleted =
      await page.getByTestId('next-hand-button').isVisible({ timeout: 5000 }) ||
      await page.getByTestId('winner-modal').isVisible({ timeout: 5000 })

    expect(handCompleted).toBeTruthy()
    expect(continueCount).toBeGreaterThan(0)
  })
})
```

**Run Test:**
```bash
npx playwright test test_step_mode.spec.ts --headed
```

**When Passing:**
```bash
git add tests/e2e/test_step_mode.spec.ts
git commit -m "TEST: Add step mode E2E tests (3 tests)

- Test AI pauses when step mode enabled
- Test Continue advances single AI turn
- Test full hand completion in step mode
- Tests verify step mode UI flow end-to-end
- All tests passing"
```

---

### Step 3b.7: Add Package.json E2E Scripts

**File:** `frontend/package.json`

**Add to `scripts`:**
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report"
  }
}
```

**Commit:**
```bash
git add frontend/package.json
git commit -m "TEST INFRA: Add Playwright E2E scripts to package.json

- test:e2e: Run all E2E tests
- test:e2e:ui: Interactive UI mode
- test:e2e:debug: Step-through debugger
- test:e2e:headed: Show browser window
- test:e2e:report: View HTML report"
```

---

### Phase 3b Checkpoint

**Run All E2E Tests:**
```bash
cd frontend
npm run test:e2e
```

**Expected Output:**
```
Running 9 tests using 1 worker

  ✓ test_short_stack_ui.spec.ts:XX:X › allows call all-in when stack < call amount (3.2s)
  ✓ test_short_stack_ui.spec.ts:XX:X › allows raise all-in when stack < min raise (2.8s)
  ✓ test_short_stack_ui.spec.ts:XX:X › shows correct call button label (2.5s)
  ✓ test_winner_modal.spec.ts:XX:X › displays "Split Pot!" for two-way tie (4.1s)
  ✓ test_winner_modal.spec.ts:XX:X › displays three-way split correctly (3.9s)
  ✓ test_winner_modal.spec.ts:XX:X › shows individual amounts sum to pot (3.7s)
  ✓ test_step_mode.spec.ts:XX:X › pauses AI when step mode enabled (3.3s)
  ✓ test_step_mode.spec.ts:XX:X › advances single AI turn when Continue clicked (2.9s)
  ✓ test_step_mode.spec.ts:XX:X › completes full hand in step mode (5.1s)

9 passed (31.5s)
```

**Commit Summary:**
```bash
git add -A
git commit -m "PHASE 3 COMPLETE: E2E tests with Playwright

Summary:
- 9 E2E tests implemented and passing
- Backend test endpoint functional
- Playwright auto-starts backend + frontend
- Tests verify full user flows end-to-end

Test Breakdown:
- Short-stack UI: 3 tests
- Winner modal split pot: 3 tests
- Step mode flow: 3 tests

Backend Changes:
- /test/set_game_state endpoint (TEST_MODE only)
- /test/health for E2E health checks
- /test/games/{id} for debugging

Ready for Phase 4 (Visual tests)"
```

---

## Phase 4: Visual Regression Tests

**Goal:** Add visual regression testing to catch layout/styling bugs

**Estimated Effort:** 2-3 hours

---

### Step 4.1: Update Playwright Config for Screenshots

**File:** `frontend/playwright.config.ts`

**Add screenshot configuration:**

```typescript
export default defineConfig({
  // ... existing config

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,      // Allow 100px difference
      threshold: 0.2,          // 20% pixel difference threshold
      animations: 'disabled',  // Disable animations for consistency
    },
  },
})
```

**Commit:**
```bash
git add frontend/playwright.config.ts
git commit -m "TEST INFRA: Configure Playwright for visual regression

- Set maxDiffPixels to 100 (anti-aliasing tolerance)
- Set threshold to 20% for pixel differences
- Disable animations for consistent screenshots"
```

---

### Step 4.2: Create Screenshot Directory Structure

**Commands:**
```bash
mkdir -p tests/e2e/screenshots/baseline
mkdir -p tests/e2e/screenshots/actual
mkdir -p tests/e2e/screenshots/diff
```

**Update `.gitignore`:**

**File:** `.gitignore`

**Add:**
```gitignore
# Playwright screenshots
tests/e2e/screenshots/actual/
tests/e2e/screenshots/diff/
tests/e2e/*-snapshots/
```

**Commit:**
```bash
git add .gitignore
git commit -m "TEST INFRA: Set up screenshot directory structure

- Create baseline/ (git-tracked)
- Create actual/ (gitignored - current run)
- Create diff/ (gitignored - visual diffs)
- Update .gitignore to exclude generated screenshots"
```

---

### Step 4.3: Write Responsive Design Tests

**File:** `tests/e2e/test_responsive_design.spec.ts` (NEW)

```typescript
import { test, expect, devices } from '@playwright/test'

test.describe('Responsive Design', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1920, height: 1080 },
  ]

  for (const viewport of viewports) {
    test(`no overflow on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height
      })

      await page.goto('http://localhost:3000')
      await page.click('text=New Game')
      await page.waitForURL(/\/game\/.*/)

      // Wait for table to render
      await page.waitForSelector('[data-testid="poker-table-main"]')

      // Check for horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 5) // 5px tolerance

      // Check specific elements don't overflow
      const communityCards = page.getByTestId('community-cards-area')
      const communityBox = await communityCards.boundingBox()

      if (communityBox) {
        expect(communityBox.x + communityBox.width).toBeLessThanOrEqual(viewportWidth + 5)
      }
    })

    test(`action buttons fit on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height
      })

      await page.goto('http://localhost:3000')
      await page.click('text=New Game')
      await page.waitForURL(/\/game\/.*/)

      // Wait for action buttons
      await page.waitForSelector('[data-testid="fold-button"]')

      // Verify buttons have minimum touch target size (44px)
      const foldButton = page.getByTestId('fold-button')
      const box = await foldButton.boundingBox()

      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(40) // 40px minimum
      }

      // Verify buttons don't overlap
      const actionContainer = page.getByTestId('action-buttons-container')
      const buttons = actionContainer.locator('button')
      const count = await buttons.count()

      if (count > 1) {
        const boxes = await Promise.all(
          Array.from({ length: count }, (_, i) => buttons.nth(i).boundingBox())
        )

        // Check no overlap (with 5px tolerance for borders/margins)
        for (let i = 0; i < count - 1; i++) {
          const box1 = boxes[i]
          const box2 = boxes[i + 1]

          if (box1 && box2) {
            // Horizontal layout: x1 + width1 <= x2
            // Vertical layout: y1 + height1 <= y2
            const horizontalOverlap = box1.x + box1.width > box2.x + 5
            const verticalOverlap = box1.y + box1.height > box2.y + 5

            // Should not overlap in both dimensions
            expect(horizontalOverlap && verticalOverlap).toBeFalsy()
          }
        }
      }
    })
  }
})
```

**Run Tests:**
```bash
npm run test:e2e:headed -- test_responsive_design.spec.ts
```

**When Passing:**
```bash
git add tests/e2e/test_responsive_design.spec.ts
git commit -m "TEST: Add responsive design tests (6 tests)

- Test no overflow on mobile/tablet/desktop
- Test action buttons fit and don't overlap
- Test minimum touch target sizes
- Tests run across 3 viewport sizes
- All tests passing"
```

---

### Step 4.4: Write Card Sizing Tests

**File:** `tests/e2e/test_card_sizing.spec.ts` (NEW)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Card Sizing', () => {
  test('community cards maintain 2.5:3.5 aspect ratio', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    // Fold to advance to flop
    await page.getByTestId('fold-button').click()

    // Wait for community cards to appear (flop)
    await page.waitForSelector('[data-testid="community-card-0"]', { timeout: 30000 })

    const card = page.getByTestId('community-card-0')
    const box = await card.boundingBox()

    if (box) {
      const aspectRatio = box.width / box.height
      const expectedRatio = 2.5 / 3.5 // Standard poker card ratio

      // Allow 15% tolerance for browser rendering
      expect(aspectRatio).toBeGreaterThan(expectedRatio * 0.85)
      expect(aspectRatio).toBeLessThan(expectedRatio * 1.15)
    }
  })

  test('cards fit within viewport on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    // Fold to see community cards
    await page.getByTestId('fold-button').click()
    await page.waitForSelector('[data-testid="community-cards-container"]', { timeout: 30000 })

    const cardsContainer = page.getByTestId('community-cards-container')
    const box = await cardsContainer.boundingBox()

    if (box) {
      expect(box.width).toBeLessThanOrEqual(375)
      expect(box.x).toBeGreaterThanOrEqual(0)
    }
  })

  test('hole cards readable size', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    await page.waitForSelector('[data-testid="human-player-seat"]')

    // Find hole cards in human seat
    const humanSeat = page.getByTestId('human-player-seat')
    const holeCards = humanSeat.getByTestId(/hole-card-human-/)
    const firstCard = holeCards.first()

    const box = await firstCard.boundingBox()

    if (box) {
      // Minimum readable card size: 50px width
      expect(box.width).toBeGreaterThanOrEqual(50)

      // Maximum size (don't dominate screen)
      expect(box.width).toBeLessThanOrEqual(150)
    }
  })

  test('visual regression - game table', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await page.click('text=New Game')
    await page.waitForURL(/\/game\/.*/)

    await page.waitForSelector('[data-testid="poker-table-main"]')

    // Take screenshot and compare to baseline
    await expect(page).toHaveScreenshot('poker-table-initial.png', {
      fullPage: false,
      mask: [
        // Mask dynamic elements (game ID, timestamps, etc.)
        page.getByTestId('connection-status'),
      ],
    })
  })
})
```

**Run Tests:**
```bash
npm run test:e2e:headed -- test_card_sizing.spec.ts
```

**Generate Baselines (first run will create them):**
```bash
npm run test:e2e -- test_card_sizing.spec.ts --update-snapshots
```

**When Passing:**
```bash
git add tests/e2e/test_card_sizing.spec.ts
git add tests/e2e/*-snapshots/  # Playwright stores snapshots here
git commit -m "TEST: Add card sizing and visual regression tests (4 tests)

- Test community cards maintain aspect ratio
- Test cards fit within mobile viewport
- Test hole cards readable size
- Test visual regression baseline screenshot
- Baselines generated and committed
- All tests passing"
```

---

### Phase 4 Checkpoint

**Run All Visual Tests:**
```bash
cd frontend
npm run test:e2e -- test_responsive_design.spec.ts test_card_sizing.spec.ts
```

**Expected Output:**
```
Running 10 tests using 1 worker

  ✓ test_responsive_design.spec.ts (6 tests) - 18.2s
  ✓ test_card_sizing.spec.ts (4 tests) - 12.1s

10 passed (30.3s)
```

**Commit Summary:**
```bash
git add -A
git commit -m "PHASE 4 COMPLETE: Visual regression tests

Summary:
- 10 visual tests implemented and passing
- Screenshot baselines generated
- Responsive design tests (3 viewports)
- Card sizing and aspect ratio tests

Test Breakdown:
- Responsive design: 6 tests (mobile/tablet/desktop)
- Card sizing: 4 tests (aspect ratio, viewport fit, visual regression)

Visual Testing:
- Baselines committed to git
- Playwright screenshot comparison
- Tolerances configured for anti-aliasing

All 4 phases complete!"
```

---

## CI Integration

**Goal:** Add frontend tests to CI pipeline

**Estimated Effort:** 30 minutes

---

### Step CI.1: Create Frontend Test Workflow

**File:** `.github/workflows/test-frontend.yml` (NEW)

```yaml
name: Frontend Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    name: Component Tests (Jest + RTL)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run component tests
        run: cd frontend && npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info
          flags: frontend

  e2e-tests:
    name: E2E Tests (Playwright)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Setup Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps chromium

      - name: Run E2E tests
        run: cd frontend && npm run test:e2e
        env:
          TEST_MODE: 1

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 7

  visual-tests:
    name: Visual Regression Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Setup Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend && pip install -r requirements.txt
          cd ../frontend && npm ci
          npx playwright install --with-deps chromium

      - name: Run visual tests
        run: cd frontend && npm run test:e2e -- test_responsive_design.spec.ts test_card_sizing.spec.ts
        env:
          TEST_MODE: 1

      - name: Upload visual diffs on failure
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: visual-diffs
          path: tests/e2e/screenshots/diff/
          retention-days: 7
```

**Commit:**
```bash
git add .github/workflows/test-frontend.yml
git commit -m "CI: Add frontend testing workflow

Jobs:
- Component tests (Jest + RTL)
- E2E tests (Playwright)
- Visual regression tests

Features:
- Upload coverage to Codecov
- Upload Playwright report on failure
- Upload visual diffs on failure
- Run in parallel with backend tests"
```

---

### Step CI.2: Update Pre-commit Hook (Optional)

**File:** `.github/workflows/pre-commit.yml` or git hooks

**Add fast component tests to pre-commit:**

```bash
# In pre-commit hook (if using git hooks)
echo "Running fast component tests..."
cd frontend && npm test -- --bail --findRelatedTests
```

**Or update existing workflow to include component tests**

---

## Implementation Summary

### Total Tests Added

**Phase 0:** 0 tests (infrastructure)
- Added 50+ test IDs to components

**Phase 2:** 16 component tests (Jest + RTL)
- PokerTable action buttons: 5 tests
- PokerTable raise slider: 3 tests
- WinnerModal split pot: 4 tests
- Store step mode: 4 tests

**Phase 3:** 9 E2E tests (Playwright)
- Short-stack UI: 3 tests
- Winner modal: 3 tests
- Step mode: 3 tests

**Phase 4:** 10 visual tests (Playwright screenshots)
- Responsive design: 6 tests
- Card sizing: 4 tests

**Total:** 35 frontend tests + 50+ test IDs

---

## Success Criteria

### Phase 2 ✅
- [x] All 16 component tests passing
- [x] Test coverage report generated
- [x] Tests run in < 10 seconds
- [x] CI pipeline green

### Phase 3 ✅
- [x] All 9 E2E tests passing
- [x] Backend test endpoint secured (TEST_MODE only)
- [x] Tests run in < 2 minutes
- [x] CI pipeline green

### Phase 4 ✅
- [x] All 10 visual tests passing
- [x] Baseline screenshots committed
- [x] No false positives
- [x] CI pipeline green

---

## Next Steps After Implementation

1. **Monitor CI**: Watch for flaky E2E tests
2. **Update Baselines**: When UI intentionally changes, run `--update-snapshots`
3. **Expand Coverage**: Add more component tests as new features are added
4. **Performance**: Monitor E2E test runtime, optimize if > 5 minutes

---

**Last Updated:** January 11, 2026
**Status:** Ready for Implementation
**Total Estimated Effort:** 12-16 hours
