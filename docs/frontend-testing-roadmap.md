# Frontend Testing Infrastructure Roadmap

**Date Created:** January 11, 2026
**Status:** Planned (Not Started)
**Related:** Phase 1 backend tests completed (see archive/codex-testing-fixes.md)

---

## Executive Summary

Phase 1 of the TDD execution plan completed successfully with 17 backend tests added. Phases 2-4 (frontend/E2E testing) require infrastructure setup before tests can be written. This document provides a complete roadmap for implementing frontend test coverage.

**Estimated Total Effort:** 10-14 hours
- Phase 2: 3-5 hours (Component tests)
- Phase 3: 4-6 hours (E2E tests)
- Phase 4: 2-3 hours (Visual regression)

---

## Phase 2: Frontend Component Tests (Jest + React Testing Library)

### Overview

**Goal:** Add unit tests for critical React components to catch UI regressions

**Current State:**
- 1 unit test exists (`frontend/__tests__/short-stack-logic.test.ts`) - pure logic only
- No test framework configured for component rendering
- Next.js 15 with App Router + Turbopack

**Estimated Effort:** 3-5 hours
- Setup: 1-2 hours
- Tests: 2-3 hours

---

### Infrastructure Requirements

#### 1. Dependencies to Install

```bash
cd frontend
npm install --save-dev \
  @testing-library/react@^14.0.0 \
  @testing-library/jest-dom@^6.1.5 \
  @testing-library/user-event@^14.5.1 \
  jest@^29.7.0 \
  jest-environment-jsdom@^29.7.0 \
  @types/jest@^29.5.11
```

#### 2. Configuration Files

**`frontend/jest.config.js`:**

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
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
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
```

**`frontend/jest.setup.js`:**

```javascript
import '@testing-library/jest-dom'

// Mock window.matchMedia (used by responsive components)
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

// Mock WebSocket (used by useGameStore)
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      this.onopen?.()
    }, 0)
  }

  send(data) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.()
  }

  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
}
```

#### 3. Test Utilities

**`frontend/__tests__/utils/test-utils.tsx`:**

```typescript
import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

// Mock game state builder
export function createMockGameState(overrides = {}) {
  return {
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
      {
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
      },
      // ... AI players
    ],
    human_player: {
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
    },
    community_cards: [],
    last_ai_decisions: {},
    ...overrides,
  }
}

// Custom render with providers
export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions
) {
  return render(ui, { ...options })
}

export * from '@testing-library/react'
```

#### 4. Package.json Scripts

**Add to `frontend/package.json`:**

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

---

### Tests to Implement

#### 2.1: PokerTable Action Button Logic (5 tests)

**File:** `frontend/__tests__/PokerTable.test.tsx`

**Purpose:** Validate button enablement logic for short-stack scenarios

**Tests:**

```typescript
describe('PokerTable - Action Buttons', () => {
  it('enables Call button when short stack', () => {
    // Setup: player with $30, facing $80 bet
    const gameState = createMockGameState({
      human_player: { ...mockPlayer, stack: 30 },
      current_bet: 80,
    })

    render(<PokerTable />) // with mocked store

    const callButton = screen.getByText(/Call/i)
    expect(callButton).not.toBeDisabled()
  })

  it('enables Raise button when short stack', () => {
    // Setup: player with $30, can raise all-in
    const gameState = createMockGameState({
      human_player: { ...mockPlayer, stack: 30 },
      current_bet: 20,
    })

    render(<PokerTable />)

    const raiseButton = screen.getByText(/Raise/i)
    expect(raiseButton).not.toBeDisabled()
  })

  it('disables buttons when eliminated', () => {
    // Setup: player with $0, not active
    const gameState = createMockGameState({
      human_player: {
        ...mockPlayer,
        stack: 0,
        is_active: false
      },
    })

    render(<PokerTable />)

    expect(screen.queryByText(/Call/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Raise/i)).not.toBeInTheDocument()
  })

  it('disables buttons when all-in waiting', () => {
    // Setup: player all-in, waiting for showdown
    const gameState = createMockGameState({
      human_player: {
        ...mockPlayer,
        stack: 0,
        all_in: true,
        is_current_turn: false,
      },
    })

    render(<PokerTable />)

    expect(screen.queryByText(/Call/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Raise/i)).not.toBeInTheDocument()
  })

  it('shows All-In button when active', () => {
    const gameState = createMockGameState({
      human_player: {
        ...mockPlayer,
        stack: 50,
        is_current_turn: true,
      },
    })

    render(<PokerTable />)

    // Click Raise to open panel
    fireEvent.click(screen.getByText(/Raise/i))

    expect(screen.getByText(/All In/i)).toBeInTheDocument()
  })
})
```

**Priority:** 🟡 High (catches short-stack UI regression)

---

#### 2.2: Raise Slider Constraints (3 tests)

**File:** `frontend/__tests__/PokerTable.test.tsx` (extend)

**Purpose:** Validate slider respects min/max from backend

**Tests:**

```typescript
describe('PokerTable - Raise Slider', () => {
  it('respects minRaise from backend', () => {
    const gameState = createMockGameState({
      current_bet: 20,
      last_raise_amount: 10,
      big_blind: 10,
      human_player: { ...mockPlayer, stack: 200 },
    })

    render(<PokerTable />)
    fireEvent.click(screen.getByText(/Raise/i))

    const slider = screen.getByRole('slider')
    expect(slider).toHaveAttribute('min', '30') // current_bet + last_raise_amount
  })

  it('sets slider max to stack + current_bet', () => {
    const gameState = createMockGameState({
      current_bet: 20,
      human_player: {
        ...mockPlayer,
        stack: 100,
        current_bet: 10, // Already posted blind
      },
    })

    render(<PokerTable />)
    fireEvent.click(screen.getByText(/Raise/i))

    const slider = screen.getByRole('slider')
    expect(slider).toHaveAttribute('max', '110') // stack + current_bet
  })

  it('disables slider when short stack below minRaise', () => {
    const gameState = createMockGameState({
      current_bet: 100,
      last_raise_amount: 50,
      human_player: { ...mockPlayer, stack: 30 }, // Can't meet min raise
    })

    render(<PokerTable />)
    fireEvent.click(screen.getByText(/Raise/i))

    const slider = screen.getByRole('slider')
    expect(slider).toBeDisabled()

    // But All-In button should be available
    expect(screen.getByText(/All In/i)).not.toBeDisabled()
  })
})
```

**Priority:** 🟡 High (validates min raise logic)

---

#### 2.3: WinnerModal Split Pot Display (4 tests)

**File:** `frontend/__tests__/WinnerModal.test.tsx`

**Purpose:** Validate split pot UI rendering

**Tests:**

```typescript
describe('WinnerModal - Split Pot Display', () => {
  it('displays "Split Pot!" for two winners', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 50 },
      { player_id: 'ai1', name: 'AI 1', amount: 50 },
    ]

    render(<WinnerModal winners={winners} pot={100} onClose={jest.fn()} />)

    expect(screen.getByText(/Split Pot!/i)).toBeInTheDocument()
  })

  it('displays "Split Pot!" for three winners', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 33 },
      { player_id: 'ai1', name: 'AI 1', amount: 33 },
      { player_id: 'ai2', name: 'AI 2', amount: 34 },
    ]

    render(<WinnerModal winners={winners} pot={100} onClose={jest.fn()} />)

    expect(screen.getByText(/Split Pot!/i)).toBeInTheDocument()
  })

  it('shows individual amounts for each winner', () => {
    const winners = [
      { player_id: 'human', name: 'Human', amount: 51 },
      { player_id: 'ai1', name: 'AI 1', amount: 50 },
    ]

    render(<WinnerModal winners={winners} pot={101} onClose={jest.fn()} />)

    expect(screen.getByText(/Human.*\$51/)).toBeInTheDocument()
    expect(screen.getByText(/AI 1.*\$50/)).toBeInTheDocument()
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

    render(<WinnerModal winners={winners} pot={100} onClose={jest.fn()} />)

    expect(screen.getByText(/Royal Flush/i)).toBeInTheDocument()
  })
})
```

**Priority:** 🟢 Medium (validates split pot display)

---

#### 2.4: WebSocket Store Step Mode (4 tests)

**File:** `frontend/__tests__/store.test.ts`

**Purpose:** Validate Zustand store step mode logic

**Tests:**

```typescript
import { useGameStore } from '@/lib/store'
import { act, renderHook } from '@testing-library/react'

describe('GameStore - Step Mode', () => {
  beforeEach(() => {
    // Reset store state
    useGameStore.setState({
      stepMode: false,
      awaitingContinue: false,
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
      ws: { send: mockSend } as any,
      stepMode: true,
      awaitingContinue: true,
    })

    const { result } = renderHook(() => useGameStore())

    act(() => {
      result.current.sendContinue()
    })

    expect(mockSend).toHaveBeenCalledWith(
      JSON.stringify({ type: 'continue' })
    )
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

    // Simulate new hand starting
    act(() => {
      useGameStore.setState({
        gameState: { ...mockGameState, hand_count: 2 },
      })
    })

    expect(result.current.stepMode).toBe(true)
  })
})
```

**Priority:** 🟢 Medium (validates step mode state)

---

## Phase 3: Frontend E2E Tests (Playwright)

### Overview

**Goal:** Add end-to-end tests that exercise full backend-frontend flows

**Current State:**
- Zero E2E tests
- No E2E framework configured
- No backend test endpoint for state manipulation

**Estimated Effort:** 4-6 hours
- Setup: 2-3 hours (Playwright + backend endpoint)
- Tests: 2-3 hours

---

### Infrastructure Requirements

#### 1. Dependencies to Install

```bash
cd frontend
npm install --save-dev @playwright/test@^1.40.0
npx playwright install chromium
```

#### 2. Configuration Files

**`playwright.config.ts`:**

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
      url: 'http://localhost:8000/health',
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

#### 3. Backend Test Endpoint (CRITICAL)

**`backend/main.py`** - Add test-only endpoint:

```python
import os

# Test mode flag (set via TEST_MODE=1 env var)
TEST_MODE = os.getenv("TEST_MODE") == "1"

if TEST_MODE:
    @app.post("/test/set_game_state")
    async def set_game_state_for_testing(request: dict):
        """
        Manipulate game state for E2E testing.

        WARNING: Only available when TEST_MODE=1 env var set.
        Never deploy to production with TEST_MODE enabled.

        Example payload:
        {
            "game_id": "test-game-123",
            "player_stacks": {"human": 30, "ai1": 1000, "ai2": 1000},
            "dealer_position": 0,
            "current_bet": 80,
            "pot": 0,
            "state": "pre_flop"
        }
        """
        game_id = request.get("game_id")
        game = active_games.get(game_id)

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Apply state modifications
        if "player_stacks" in request:
            for player_id, stack in request["player_stacks"].items():
                player = next((p for p in game.players if p.player_id == player_id), None)
                if player:
                    player.stack = stack

        if "dealer_position" in request:
            game.dealer_index = request["dealer_position"]

        if "current_bet" in request:
            game.current_bet = request["current_bet"]

        if "pot" in request:
            game.pot = request["pot"]

        if "state" in request:
            game.current_state = GameState(request["state"])

        # Recalculate total chips for conservation check
        game.total_chips = sum(p.stack for p in game.players) + game.pot

        return {"success": True, "game_state": game.to_dict()}

    @app.get("/test/health")
    async def test_health():
        """Health check for E2E tests"""
        return {"status": "ok", "test_mode": True}
```

**Security Note:** Ensure `TEST_MODE` is never set in production. Add checks in deployment config.

#### 4. Directory Structure

```
tests/
└── e2e/
    ├── fixtures/
    │   └── game-page.ts          # Page object model
    ├── test_short_stack_ui.spec.ts
    ├── test_winner_modal.spec.ts
    └── test_step_mode.spec.ts
```

#### 5. Package.json Scripts

**Add to `frontend/package.json`:**

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed"
  }
}
```

---

### Tests to Implement

#### 3.1: Short-Stack E2E Tests (3 tests)

**File:** `tests/e2e/test_short_stack_ui.spec.ts`

**Purpose:** Validate short-stack UI behavior end-to-end

**Tests:**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Short-Stack UI', () => {
  test('allows call all-in when stack < call amount', async ({ page }) => {
    // Setup: Create game, manipulate state
    await page.goto('/')
    await page.click('text=New Game')

    // Extract game ID from URL or API
    const gameId = await page.evaluate(() => {
      return window.location.pathname.split('/').pop()
    })

    // Manipulate game state via test endpoint
    await page.request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: { human: 30, ai1: 1000, ai2: 1000, ai3: 1000 },
        current_bet: 80,
        pot: 0,
        state: 'pre_flop',
      },
    })

    // Reload to reflect state change
    await page.reload()

    // Verify Call button enabled
    const callButton = page.locator('button:has-text("Call")')
    await expect(callButton).toBeEnabled()

    // Verify shows "Call All-In $30"
    await expect(callButton).toContainText('All-In')
    await expect(callButton).toContainText('$30')

    // Click and verify action succeeds
    await callButton.click()

    // Wait for backend to process
    await page.waitForTimeout(500)

    // Verify player is all-in
    await expect(page.locator('text=All-In').first()).toBeVisible()
  })

  test('allows raise all-in when stack < min raise', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    const gameId = await page.evaluate(() => {
      return window.location.pathname.split('/').pop()
    })

    // Setup: player with $30, min raise is $40
    await page.request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: { human: 30, ai1: 1000, ai2: 1000, ai3: 1000 },
        current_bet: 20,
        pot: 0,
        state: 'pre_flop',
      },
    })

    await page.reload()

    // Click Raise to open panel
    await page.click('button:has-text("Raise")')

    // Verify All-In button available
    const allInButton = page.locator('button:has-text("All In")')
    await expect(allInButton).toBeEnabled()

    // Click All-In
    await allInButton.click()

    await page.waitForTimeout(500)

    // Verify all-in succeeded
    await expect(page.locator('text=All-In').first()).toBeVisible()
  })

  test('shows correct call button label for short stack', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    const gameId = await page.evaluate(() => {
      return window.location.pathname.split('/').pop()
    })

    await page.request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        player_stacks: { human: 15, ai1: 1000, ai2: 1000, ai3: 1000 },
        current_bet: 50,
        pot: 0,
        state: 'pre_flop',
      },
    })

    await page.reload()

    // Verify label shows "Call All-In $15" (not "Call $50")
    const callButton = page.locator('button:has-text("Call")')
    await expect(callButton).toContainText('All-In')
    await expect(callButton).toContainText('$15')
  })
})
```

**Priority:** 🟡 High (validates critical short-stack fix)

---

#### 3.2: Winner Modal Split Pot E2E (3 tests)

**File:** `tests/e2e/test_winner_modal.spec.ts`

**Purpose:** Validate split pot modal displays correctly

**Tests:**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Winner Modal - Split Pot', () => {
  test('displays "Split Pot!" for two-way tie', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    const gameId = await page.evaluate(() => {
      return window.location.pathname.split('/').pop()
    })

    // Setup: Royal flush on board, all players tie
    await page.request.post('http://localhost:8000/test/set_game_state', {
      data: {
        game_id: gameId,
        community_cards: ['Ah', 'Kh', 'Qh', 'Jh', '10h'],
        player_stacks: { human: 950, ai1: 950 },
        pot: 100,
        state: 'river',
        // Force to showdown
      },
    })

    await page.reload()

    // Fast-forward to showdown
    // (Implementation depends on how to trigger showdown in test mode)

    // Wait for winner modal
    await expect(page.locator('text=Split Pot!')).toBeVisible({ timeout: 10000 })

    // Verify amounts displayed
    await expect(page.locator('text=$50')).toHaveCount(2)
  })

  test('displays three-way split correctly', async ({ page }) => {
    // Similar setup with 3 players tying
    // Verify "Split Pot!" and three amounts displayed
  })

  test('shows individual amounts sum to pot', async ({ page }) => {
    // Setup: $101 pot, 2 winners
    // Verify displayed amounts are $51 and $50, sum to $101
  })
})
```

**Priority:** 🟢 Medium (validates split pot display)

---

#### 3.3: Step Mode E2E Tests (3 tests)

**File:** `tests/e2e/test_step_mode.spec.ts`

**Purpose:** Validate step mode UI flow

**Tests:**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Step Mode', () => {
  test('pauses AI when step mode enabled', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    // Enable step mode via settings
    await page.click('[data-testid="settings-button"]')
    await page.click('text=Toggle Step Mode')

    // Verify step mode indicator visible
    await expect(page.locator('text=Step Mode: ON')).toBeVisible()

    // Make an action (fold)
    await page.click('button:has-text("Fold")')

    // Wait for AI turn
    await page.waitForTimeout(1000)

    // Verify "Continue" button appears
    await expect(page.locator('button:has-text("Continue")')).toBeVisible()

    // Verify game is paused (awaiting continue)
    await expect(page.locator('text=WAITING FOR CONTINUE')).toBeVisible()
  })

  test('advances single AI turn when Continue clicked', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    // Enable step mode
    await page.click('[data-testid="settings-button"]')
    await page.click('text=Toggle Step Mode')

    // Fold to trigger AI turns
    await page.click('button:has-text("Fold")')

    // Wait for Continue button
    await page.waitForSelector('button:has-text("Continue")')

    // Click Continue
    await page.click('button:has-text("Continue")')

    // Verify one AI action occurred
    await page.waitForTimeout(500)

    // Continue button should reappear (next AI turn)
    await expect(page.locator('button:has-text("Continue")')).toBeVisible()
  })

  test('completes full hand in step mode', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    // Enable step mode
    await page.click('[data-testid="settings-button"]')
    await page.click('text=Toggle Step Mode')

    // Fold
    await page.click('button:has-text("Fold")')

    // Click Continue repeatedly until hand completes
    let continueCount = 0
    while (continueCount < 10) { // Safety limit
      const continueButton = page.locator('button:has-text("Continue")')

      if (await continueButton.isVisible({ timeout: 2000 })) {
        await continueButton.click()
        continueCount++
        await page.waitForTimeout(500)
      } else {
        // Hand completed
        break
      }
    }

    // Verify hand completed (winner modal or next hand button)
    const handCompleted = await page.locator('text=Next Hand').isVisible({ timeout: 5000 }) ||
                          await page.locator('button:has-text("Next Hand")').isVisible()

    expect(handCompleted).toBeTruthy()
    expect(continueCount).toBeGreaterThan(0)
  })
})
```

**Priority:** 🟢 Medium (validates step mode flow)

---

## Phase 4: Visual Test Assertions (Playwright Visual Regression)

### Overview

**Goal:** Add visual regression testing to catch layout/styling bugs

**Current State:**
- No visual tests
- Depends on Phase 3 (Playwright setup)

**Estimated Effort:** 2-3 hours
- Setup: 1 hour
- Tests: 1-2 hours

---

### Infrastructure Requirements

#### 1. Configuration

**Update `playwright.config.ts`:**

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
      maxDiffPixels: 100, // Allow 100px difference (anti-aliasing, etc.)
      threshold: 0.2,     // 20% pixel difference threshold
    },
  },
})
```

#### 2. Directory Structure

```
tests/
└── e2e/
    ├── screenshots/
    │   ├── baseline/          # Baseline images (git-tracked)
    │   ├── actual/            # Current test run (gitignored)
    │   └── diff/              # Diff images (gitignored)
    ├── test_responsive_design.spec.ts
    └── test_card_sizing.spec.ts
```

**`.gitignore` additions:**

```
tests/e2e/screenshots/actual/
tests/e2e/screenshots/diff/
```

---

### Tests to Implement

#### 4.1: Responsive Design Assertions (1 file)

**File:** `tests/e2e/test_responsive_design.spec.ts`

**Purpose:** Assert no overflow, correct sizes at breakpoints

**Tests:**

```typescript
import { test, expect, devices } from '@playwright/test'

test.describe('Responsive Design', () => {
  const viewports = [
    { name: 'mobile', ...devices['iPhone 13'] },
    { name: 'tablet', ...devices['iPad Pro'] },
    { name: 'desktop', width: 1920, height: 1080 },
  ]

  for (const viewport of viewports) {
    test(`no overflow on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width || 375,
        height: viewport.height || 667
      })

      await page.goto('/')
      await page.click('text=New Game')

      // Wait for table to render
      await page.waitForSelector('[data-testid="poker-table"]')

      // Check for horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
      const viewportWidth = await page.evaluate(() => window.innerWidth)

      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)

      // Check specific elements don't overflow
      const communityCards = page.locator('[data-testid="community-cards"]')
      const communityBox = await communityCards.boundingBox()

      if (communityBox) {
        expect(communityBox.x + communityBox.width).toBeLessThanOrEqual(viewportWidth)
      }
    })

    test(`action buttons fit on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width || 375,
        height: viewport.height || 667
      })

      await page.goto('/')
      await page.click('text=New Game')

      // Wait for action buttons
      await page.waitForSelector('button:has-text("Fold")')

      // Verify buttons have minimum touch target size (44px)
      const foldButton = page.locator('button:has-text("Fold")')
      const box = await foldButton.boundingBox()

      expect(box?.height).toBeGreaterThanOrEqual(44)

      // Verify buttons don't overlap
      const buttons = page.locator('[data-testid="action-buttons"] button')
      const count = await buttons.count()

      for (let i = 0; i < count - 1; i++) {
        const box1 = await buttons.nth(i).boundingBox()
        const box2 = await buttons.nth(i + 1).boundingBox()

        if (box1 && box2) {
          // Check no overlap (with 2px tolerance for borders)
          expect(box1.x + box1.width).toBeLessThanOrEqual(box2.x + 2)
        }
      }
    })
  }
})
```

**Priority:** 🔵 Low (nice-to-have, caught manually)

---

#### 4.2: Card Sizing Assertions (1 file)

**File:** `tests/e2e/test_card_sizing.spec.ts`

**Purpose:** Assert cards maintain aspect ratio, don't overflow

**Tests:**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Card Sizing', () => {
  test('community cards maintain 2.5:3.5 aspect ratio', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    // Wait for community cards to appear (flop)
    await page.waitForSelector('[data-testid="community-card-0"]', { timeout: 30000 })

    const card = page.locator('[data-testid="community-card-0"]')
    const box = await card.boundingBox()

    if (box) {
      const aspectRatio = box.width / box.height
      const expectedRatio = 2.5 / 3.5 // Standard poker card ratio

      // Allow 10% tolerance
      expect(aspectRatio).toBeGreaterThan(expectedRatio * 0.9)
      expect(aspectRatio).toBeLessThan(expectedRatio * 1.1)
    }
  })

  test('cards fit within viewport on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/')
    await page.click('text=New Game')

    await page.waitForSelector('[data-testid="community-cards"]')

    const cardsContainer = page.locator('[data-testid="community-cards"]')
    const box = await cardsContainer.boundingBox()

    if (box) {
      expect(box.width).toBeLessThanOrEqual(375)
      expect(box.x).toBeGreaterThanOrEqual(0)
    }
  })

  test('hole cards readable size', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    await page.waitForSelector('[data-testid="hole-card-0"]')

    const card = page.locator('[data-testid="hole-card-0"]')
    const box = await card.boundingBox()

    if (box) {
      // Minimum readable card size: 50px width
      expect(box.width).toBeGreaterThanOrEqual(50)

      // Maximum size (don't dominate screen)
      expect(box.width).toBeLessThanOrEqual(150)
    }
  })

  test('visual regression - game table', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Game')

    await page.waitForSelector('[data-testid="poker-table"]')

    // Take screenshot and compare to baseline
    await expect(page).toHaveScreenshot('poker-table-initial.png')
  })
})
```

**Priority:** 🔵 Low (nice-to-have)

---

## Implementation Checklist

### Phase 2: Component Tests

- [ ] Install Jest + RTL dependencies
- [ ] Create `jest.config.js`
- [ ] Create `jest.setup.js` with mocks
- [ ] Create test utilities (`test-utils.tsx`)
- [ ] Add test scripts to `package.json`
- [ ] Write 5 PokerTable button tests
- [ ] Write 3 raise slider tests
- [ ] Write 4 WinnerModal tests
- [ ] Write 4 store step mode tests
- [ ] Run tests and verify all pass
- [ ] Add to CI pipeline

### Phase 3: E2E Tests

- [ ] Install Playwright
- [ ] Create `playwright.config.ts`
- [ ] Add backend test endpoint (`/test/set_game_state`)
- [ ] Add TEST_MODE env var check
- [ ] Create E2E directory structure
- [ ] Write 3 short-stack E2E tests
- [ ] Write 3 winner modal E2E tests
- [ ] Write 3 step mode E2E tests
- [ ] Run tests and verify all pass
- [ ] Add to CI pipeline

### Phase 4: Visual Tests

- [ ] Update Playwright config for screenshots
- [ ] Create screenshot directory structure
- [ ] Update `.gitignore`
- [ ] Write responsive design tests
- [ ] Write card sizing tests
- [ ] Generate baseline screenshots
- [ ] Run tests and verify all pass
- [ ] Add to CI pipeline

---

## CI Integration

### GitHub Actions Workflow

**`.github/workflows/test-frontend.yml`:**

```yaml
name: Frontend Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run unit tests
        run: cd frontend && npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install backend dependencies
        run: cd backend && pip install -r requirements.txt

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps chromium

      - name: Run E2E tests
        run: cd frontend && npm run test:e2e
        env:
          TEST_MODE: 1

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Estimated Timeline

**Total Effort:** 10-14 hours

### Phase 2: Component Tests (3-5 hours)
- Day 1, Session 1: Setup infrastructure (1-2 hours)
- Day 1, Session 2: Write button + slider tests (1-1.5 hours)
- Day 2, Session 1: Write modal + store tests (1-1.5 hours)

### Phase 3: E2E Tests (4-6 hours)
- Day 3, Session 1: Setup Playwright + backend endpoint (2-3 hours)
- Day 3, Session 2: Write short-stack + modal tests (1-1.5 hours)
- Day 4, Session 1: Write step mode tests (1-1.5 hours)

### Phase 4: Visual Tests (2-3 hours)
- Day 5, Session 1: Setup + write tests (1-1.5 hours)
- Day 5, Session 2: Generate baselines, verify (1-1.5 hours)

---

## Success Criteria

### Phase 2
- ✅ All 16 component tests passing
- ✅ Test coverage report generated
- ✅ Tests run in < 10 seconds
- ✅ CI pipeline green

### Phase 3
- ✅ All 9 E2E tests passing
- ✅ Backend test endpoint secured (TEST_MODE only)
- ✅ Tests run in < 2 minutes
- ✅ CI pipeline green

### Phase 4
- ✅ All visual tests passing
- ✅ Baseline screenshots committed
- ✅ No false positives (anti-aliasing handled)
- ✅ CI pipeline green

---

## Notes

- **Phase 1** (backend tests) completed: 17/17 tests passing, 1 bug fixed
- **Phases 2-4** documented here for future implementation
- **Security:** Ensure TEST_MODE never enabled in production
- **CI:** Add frontend tests to existing `.github/workflows/test.yml`
- **Coverage:** Aim for 80%+ coverage on critical components

---

**Last Updated:** January 11, 2026
**Status:** Planning phase - implementation pending
**Related:** See `archive/codex-testing-fixes.md` for Phase 1 execution log
