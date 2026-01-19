# E2E Debugging Report - Game Creation Blank Page Issue

**Date**: 2026-01-18
**Environment**: Azure Container Apps (Frontend) + Azure App Service (Backend)
**Issue**: Blank white page appears after clicking "Start Game" in production

---

## Executive Summary

After implementing comprehensive fixes across 4 commits, the game creation blank page issue persists in Azure production. All connectivity tests pass, but game creation fails with a completely white screen.

**Test Results**: 21/29 passing (72%)
**Critical Blocker**: Test 3.2 "Create new game" - blocks 6 additional tests

---

## Timeline of Fixes

### Commit 1: f0826903 - Phase 1 Test Infrastructure
**Changes**:
- Fixed `waitUntil: 'networkidle'` → `'domcontentloaded'/'load'` in 6 tests
- Moved user registration from `beforeAll` to per-test (auth state fix)
- Added HTML5 validation (`required`, `minLength`) to all forms

**Impact**: +3 tests fixed (authentication tests)

### Commit 2: d25bc53a - Phase 2 Error Boundaries
**Changes**:
- Created `ErrorBoundary.tsx` component
- Wrapped PokerTable in ErrorBoundary
- Added error display to game creation form
- Verified WebSocket URL configuration

**Impact**: No improvement (error boundary not being reached)

### Commit 3: b572f206 - Phase 3 Loading State
**Changes**:
```typescript
// frontend/app/game/new/page.tsx
if (loading && !gameState) {
  return <LoadingScreen />;  // Show spinner instead of blank
}
```
- Added loading screen between form submission and game table
- Added 10-second WebSocket connection timeout
- Set `loading=false` when WebSocket errors occur
- Added connectionError display with "Try Again" button

**Impact**: No improvement (loading screen not displaying)

### Commit 4: 29c51e3b - Debug Logging
**Changes**:
- Added console logging to track component render state
- Added dialog handler to E2E tests to capture alerts
- Added page content logging on test failure

**Impact**: Logs not appearing in test output (component not rendering)

---

## Evidence Analysis

### Screenshot Evidence
**File**: `test-results/03-game-lifecycle-Suite-3-Game-Lifecycle-3-2-Create-new-game-chromium/test-failed-1.png`

**Observation**: Completely white/blank page
- No loading spinner
- No error message
- No ErrorBoundary fallback UI
- No game table
- Just white background

### Error Context
**File**: `test-results/.../error-context.md`
```yaml
- alert [ref=e1]
```

**Interpretation**:
- Browser alert is present on page
- Not a JavaScript `alert()` (we have no alert calls in code)
- Likely a browser security alert or WebSocket connection error dialog

### Test Helper Analysis
**File**: `e2e/helpers.ts`
```typescript
// Added dialog handler
page.on('dialog', async dialog => {
  console.log(`[DIALOG DETECTED] Type: ${dialog.type()}, Message: ${dialog.message()}`);
  await dialog.accept();
});
```

**Result**: Dialog handler added but no logs captured → dialog may be browser-level, not JavaScript

---

## What Works (Evidence of Correct Configuration)

### ✅ Suite 1: Frontend-Backend Connectivity (5/5 passing)
1. Frontend loads with HTTP 200
2. CORS headers present
3. Backend health endpoint reachable (579ms response)
4. POST requests work (user registration succeeds)
5. **WebSocket connection can be established** ← This is key!

**Conclusion**: Backend API and WebSocket endpoint are functional.

### ✅ Suite 4: Error Handling (5/5 passing)
- HTML5 validation working perfectly
- Duplicate username rejected
- Invalid game ID shows error
- All form validation working

### ✅ Suite 5: Performance (6/6 passing)
- Page loads: 975ms - 1848ms (excellent)
- Backend health: 561-579ms
- Zero console errors on page load
- Zero failed network requests

---

## What Fails

### ❌ Test 3.2: Create new game
**Expected**: After clicking "Start Game", poker table with action buttons should appear
**Actual**: Completely blank white page
**Timeout**: 15 seconds (waiting for Fold/Check buttons)

**Code Path Analysis**:
```typescript
// frontend/app/game/new/page.tsx

export default function NewGamePage() {
  const { gameState, loading, error, connectionError } = useGameStore();

  // Early returns
  if (!isAuthenticated()) return null;  // ✅ User is authenticated (test registers user)
  if (!mounted) return null;            // ✅ Component mounted (useEffect runs)

  // Loading screen - SHOULD SHOW
  if (loading && !gameState) {
    return <LoadingScreen />;  // ❌ NOT RENDERING - why?
  }

  // Game creation form - SHOWS INITIALLY
  if (!gameState) {
    return <GameCreationForm />;  // ✅ User sees this and clicks "Start Game"
  }

  // Game table - SHOULD SHOW AFTER WEBSOCKET CONNECTS
  return (
    <ErrorBoundary>
      <PokerTable />
    </ErrorBoundary>
  );
}
```

**Hypothesis**: Component is stuck in a render state where:
- `loading` is false (timeout expired or never set)
- `gameState` is null (WebSocket never connected)
- `mounted` is true
- `isAuthenticated()` is true
- All conditions pass → renders "game creation form" again? But why blank?

---

## WebSocket Connection Flow

### Expected Flow
```
1. User clicks "Start Game"
2. createGame() called in store
3. API POST /games → returns game_id
4. connectWebSocket(game_id) called
5. WebSocket connects to wss://poker-api-demo.azurewebsites.net/ws/{game_id}?token=xxx
6. onStateUpdate fires → gameState set
7. Component re-renders with PokerTable
```

### Actual Flow (Suspected)
```
1. User clicks "Start Game" ✅
2. createGame() called ✅
3. API POST /games → returns game_id ✅ (we know API works)
4. connectWebSocket(game_id) called ✅
5. WebSocket attempts connection...
   → Connection times out or fails
   → 10-second timeout fires
   → loading set to false
   → connectionError set
6. Component should show error... but shows blank page
```

### WebSocket URL Construction
**File**: `frontend/lib/websocket.ts`
```typescript
private getWebSocketUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = new URL(apiUrl);
  const wsProtocol = url.protocol === 'https:' ? 'wss' : 'ws';
  const token = getToken();

  const baseUrl = `${wsProtocol}://${url.host}/ws/${this.gameId}`;
  const wsUrl = token ? `${baseUrl}?token=${token}` : baseUrl;

  console.log(`[WebSocket] Connecting to: ${wsUrl.replace(/token=.+/, 'token=***')}`);
  return wsUrl;
}
```

**Expected URL**: `wss://poker-api-demo.azurewebsites.net/ws/{game_id}?token=xxx`

**Verification Needed**: Check if WebSocket endpoint exists on backend

---

## Console Logging Added (Not Showing in Tests)

### Component Logging
```typescript
// frontend/app/game/new/page.tsx
console.log('[NewGamePage] Render:', {
  mounted,
  authenticated: isAuthenticated(),
  loading,
  hasGameState: !!gameState,
  error,
  connectionError
});
```

**Expected**: Logs should appear in test output
**Actual**: No logs appearing → component may not be rendering at all

### WebSocket Logging
```typescript
// frontend/lib/websocket.ts
console.log(`[WebSocket] Connecting to: ${wsUrl}...`);
console.log('[WebSocket] Connected!');
console.log('[WebSocket] Error:', error);
```

**Expected**: Logs during WebSocket connection attempt
**Actual**: No logs captured

---

## Possible Root Causes

### 1. WebSocket Endpoint Missing/Broken
**Likelihood**: High
**Evidence**:
- Test 1.5 "WebSocket connection can be established" PASSES
- But uses manually created game, not same flow as Test 3.2

**Verification Needed**:
```bash
curl -I https://poker-api-demo.azurewebsites.net/ws/test-id
# Expected: 101 Switching Protocols or 401 Unauthorized
# Actual: ???
```

### 2. CORS Blocking WebSocket Upgrade
**Likelihood**: Medium
**Evidence**: HTTP requests work, but WebSocket upgrade may have different CORS requirements

**Verification Needed**: Check Azure backend CORS settings for WebSocket

### 3. Browser Security Alert
**Likelihood**: Medium
**Evidence**: Error context shows `alert [ref=e1]`

**Verification Needed**: Manual test in browser to see actual alert message

### 4. React Rendering Issue
**Likelihood**: Low (but possible)
**Evidence**: Component returns null in some conditions

**Hypothesis**:
- Loading state gets stuck in transition
- Component returns null while waiting for state update
- No loading screen, no error, just blank

### 5. Environment Variable Mismatch
**Likelihood**: Low
**Evidence**: Backend URL works for HTTP requests

**Verification**:
```typescript
// .env.production
NEXT_PUBLIC_API_URL=https://poker-api-demo.azurewebsites.net
```

Should generate: `wss://poker-api-demo.azurewebsites.net/ws/{id}?token=xxx`

---

## Next Debugging Steps

### Immediate Actions
1. **Check Azure backend logs** during test run
   - Look for WebSocket connection attempts
   - Look for errors during game creation

2. **Manual browser test**
   - Access https://poker-frontend.braveisland-d54008f6.centralus.azurecontainerapps.io
   - Register a user
   - Click "Start Game"
   - Open browser DevTools console
   - See actual error message

3. **Test WebSocket endpoint directly**
   ```bash
   wscat -c wss://poker-api-demo.azurewebsites.net/ws/test-id?token=xxx
   ```

4. **Check backend WebSocket route**
   - Verify `/ws/{game_id}` route exists
   - Verify token authentication works
   - Check if Azure App Service supports WebSockets

### Code Changes to Test

#### Option A: Add More Aggressive Error Handling
```typescript
// frontend/app/game/new/page.tsx
if (!gameState) {
  // Add timeout to show error if stuck
  useEffect(() => {
    if (loading) {
      const timeout = setTimeout(() => {
        console.error('[NewGamePage] Stuck in loading state!');
        setError('Game creation timed out. Please try again.');
      }, 15000);
      return () => clearTimeout(timeout);
    }
  }, [loading]);
}
```

#### Option B: Force Loading State Display
```typescript
// Show loading screen immediately on button click
const handleCreateGame = async () => {
  setLocalLoading(true);  // Local state
  await createGame(playerName, aiCount);
  // Don't clear localLoading - let WebSocket connection clear it
};

if (localLoading || (loading && !gameState)) {
  return <LoadingScreen />;
}
```

#### Option C: Add Fallback Timeout
```typescript
// frontend/lib/store.ts - createGame
const timeoutId = setTimeout(() => {
  if (!get().gameState) {
    set({
      connectionError: 'WebSocket connection timed out. Please check your internet connection.',
      loading: false
    });
  }
}, 10000);
```

---

## Test Data

### Successful Connection (Test 1.5)
```javascript
// Test creates game via API, then connects WebSocket
const gameData = await page.evaluate(async (backendUrl) => {
  const authRes = await fetch(`${backendUrl}/auth/register`, {...});
  const { token } = await authRes.json();

  const gameRes = await fetch(`${backendUrl}/games`, {
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ player_name: 'WSTest', ai_count: 3 })
  });
  const game = await gameRes.json();

  return { gameId: game.game_id, token };
});

// WebSocket connection succeeds
const wsUrl = `wss://poker-api-demo.azurewebsites.net/ws/${gameId}?token=${token}`;
const ws = new WebSocket(wsUrl);
ws.onopen = () => console.log('Connected!');  // ✅ This fires
```

### Failed Connection (Test 3.2)
```javascript
// Uses createGame helper which calls store.createGame()
await createGame(page, username, 3);

// Waits for action buttons - never appear
await page.waitForSelector('button:has-text("Fold")', { timeout: 15000 });
// ❌ Timeout - buttons never appear
```

**Key Difference**: Test 1.5 connects WebSocket in browser context (page.evaluate), Test 3.2 uses React component flow

---

## Remaining Tests Blocked

Due to Test 3.2 failure, the following tests are skipped:
- 3.3: Player can check when no bet (conditional)
- 3.4: Player can fold (requires active game)
- 3.5: Game progresses as AI players act (requires active game)
- 3.6: Player can quit game (requires active game)
- 3.7: Game appears in history (requires completed game)

**Impact**: 6 tests blocked (including conditionals)

---

## Success Criteria

### Current State
- 21/29 tests passing (72%)
- All infrastructure tests passing
- All performance tests passing
- Game creation blocked

### Target State
- 27/29 tests passing (93%)
- Game creation working
- Full game lifecycle testable
- 2 false failures in password validation (test expectations need update)

### Estimated Time to Fix
- **If WebSocket endpoint issue**: 1-2 hours (backend configuration)
- **If browser security issue**: 2-4 hours (CORS/security headers)
- **If React state issue**: 4-6 hours (deeper debugging)

---

## Conclusions

1. **Backend is functional**: All API endpoints work, WebSocket can be established
2. **Frontend is functional**: Loads correctly, authentication works, validation works
3. **Integration is broken**: WebSocket connection in React component flow fails
4. **Error handling needs improvement**: Blank page should never happen - should show error
5. **Debugging needs browser access**: Console logs and network tab would reveal root cause

**Recommendation**: Manual test in browser with DevTools open to see actual error message, then implement targeted fix.

---

## Appendix: All Commits Made

1. **f0826903** - Phase 1: Test infrastructure improvements
2. **d25bc53a** - Phase 2: Error boundaries and error handling
3. **b572f206** - Phase 3: Loading state and WebSocket timeout
4. **29c51e3b** - Debug: Console logging

**Total Lines Changed**: ~200 lines across 10 files
**Test Pass Rate Improvement**: +10% (62% → 72%)
**Issue Resolution**: ❌ Not yet resolved
