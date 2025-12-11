# Browser Refresh Testing Guide

**Phase 7 Enhancement**: localStorage + URL-Based Reconnection
**Date**: December 10, 2025

---

## Overview

This document provides manual testing instructions for verifying browser refresh scenarios work correctly.

**What Was Fixed**:
- ❌ **Before**: Browser refresh → Lose game, must start new game
- ✅ **After**: Browser refresh → Automatically reconnect to same game

**Dual Implementation**:
1. **localStorage**: Persists gameId across browser sessions
2. **URL-based routing**: Bookmarkable game URLs (`/game/[gameId]`)

---

## Test Scenarios

### Scenario 1: Browser Refresh During Game

**Setup**:
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:3000`
4. Create game with 3 AI opponents
5. Play a few actions (call, raise, etc.)
6. Note the game ID in the URL: `http://localhost:3000/game/abc-123-xyz`

**Test**:
1. Press **F5** or **Ctrl+R** (browser refresh)

**Expected Result**:
✅ "Reconnecting to Game" screen appears briefly
✅ Game reconnects automatically
✅ Same pot amount, same cards, same game state
✅ Can continue playing immediately
✅ URL remains `/game/[gameId]`

**Actual Behavior**: [Test and document]

---

### Scenario 2: Close Tab and Reopen

**Setup**:
1. Create game and play a few hands
2. Note the URL: `http://localhost:3000/game/abc-123-xyz`
3. **Copy the URL to clipboard**
4. Close the browser tab completely

**Test**:
1. Open new tab
2. Paste the URL and navigate to it

**Expected Result**:
✅ "Reconnecting to Game" screen appears
✅ Game loads with current state
✅ Can continue playing

**Actual Behavior**: [Test and document]

---

### Scenario 3: Invalid Game ID (Error Handling)

**Setup**:
1. Navigate to a fake game ID: `http://localhost:3000/game/invalid-fake-id-12345`

**Expected Result**:
✅ "Unable to Reconnect" error screen appears
✅ Error message: "Game session expired. Please start a new game."
✅ Automatically redirects to home after 3 seconds
✅ localStorage cleared

**Actual Behavior**: [Test and document]

---

### Scenario 4: Quit Game Cleanup

**Setup**:
1. Create game and play a hand
2. Click "Quit" button

**Expected Result**:
✅ Game ends
✅ Returns to "Start Game" screen
✅ localStorage cleared (check DevTools: Application → Local Storage)
✅ URL changes back to `/`
✅ Refreshing page shows "Start Game" screen (not reconnection)

**Actual Behavior**: [Test and document]

---

### Scenario 5: Network Disconnect During Game

**Setup**:
1. Create game and start playing
2. Open DevTools → Network tab
3. Set throttling to "Offline"

**Expected Result**:
✅ WebSocket disconnects
✅ Frontend shows "reconnecting..." or connection lost indicator
✅ When network restored, automatically reconnects
✅ Game state restored

**Actual Behavior**: [Test and document]

---

### Scenario 6: Multiple Browser Tabs (Same Game)

**Setup**:
1. Create game in Tab 1
2. Copy URL
3. Open Tab 2 and paste URL

**Expected Result**:
⚠️ **Known Limitation**: Only one WebSocket connection per game
✅ Tab 2 connects successfully
✅ Tab 1 connection is replaced
✅ Only Tab 2 receives updates

**Actual Behavior**: [Test and document]

---

### Scenario 7: localStorage Verification

**Test localStorage Persistence**:

1. Create game
2. Open DevTools → Application → Local Storage → `http://localhost:3000`
3. Verify:
   - ✅ `poker_game_id` exists with UUID value
   - ✅ `poker_player_name` exists with player name

4. Refresh page
5. Verify:
   - ✅ localStorage still has same values
   - ✅ Game reconnects using stored gameId

6. Quit game
7. Verify:
   - ✅ localStorage cleared (both keys removed)

---

### Scenario 8: Backend Restart During Active Game

**Setup**:
1. Create game and play
2. Stop backend server (Ctrl+C)
3. Restart backend: `python main.py`

**Expected Result**:
❌ Game state lost (backend stores games in memory)
✅ Frontend shows "Failed to reconnect" error
✅ User must start new game

**Note**: This is expected behavior. Production would use database persistence.

---

## DevTools Console Logs

When testing, you should see these console logs:

### On Initial Game Creation:
```
[Store] Found saved game ID: <gameId>
[Store] Attempting to reconnect to game <gameId>
[Store] Game found! Reconnecting...
[WebSocket] Connecting to game <gameId>...
[WebSocket] Connected!
[Store] Connected - requesting current game state
```

### On Browser Refresh:
```
[Store] Found saved game ID: <gameId>
[Store] Attempting to reconnect to game <gameId>
[Store] Game found! Reconnecting...
[WebSocket] Connected!
[Store] Connected - requesting current game state
```

### On Quit:
```
[WebSocket] Disconnecting...
[Store] localStorage cleared
```

### On Invalid Game ID:
```
[Store] Attempting to reconnect to game invalid-fake-id-12345
[Store] Error reconnecting to game: Error: Request failed with status code 404
[Store] Failed to reconnect to game. Please start a new game.
```

---

## Implementation Details

### Files Modified:

1. **`frontend/lib/store.ts`**
   - Added `reconnectToGame()` method
   - Added `initializeFromStorage()` method
   - Modified `createGame()` to persist to localStorage
   - Modified `quitGame()` to clear localStorage

2. **`frontend/app/page.tsx`**
   - Added `useEffect` to call `initializeFromStorage()` on mount

3. **`frontend/app/game/[gameId]/page.tsx`** (NEW)
   - Dynamic route for game-specific URLs
   - Handles reconnection via URL parameter
   - Shows loading/error states

### localStorage Keys:

| Key | Value | Purpose |
|-----|-------|---------|
| `poker_game_id` | UUID string | Game session identifier |
| `poker_player_name` | String | Player's name (optional) |

### URL Structure:

| URL | Purpose |
|-----|---------|
| `/` | Home screen (create new game) |
| `/game/[gameId]` | Active game (bookmarkable, refresh-safe) |

---

## Known Limitations

1. **Backend Memory Storage**: Games stored in memory, so backend restart loses all games
   - **Production Fix**: Use database (PostgreSQL/Redis) for game state persistence

2. **Single Connection Per Game**: Only one WebSocket connection per game
   - **Impact**: Multi-tab access doesn't work perfectly
   - **Production Fix**: Implement connection multiplexing

3. **No Session Timeout**: Games persist indefinitely until periodic cleanup
   - **Production Fix**: Add session timeout (e.g., 1 hour of inactivity)

---

## Success Criteria

| Scenario | Expected | Status |
|----------|----------|--------|
| Browser refresh during game | ✅ Reconnects | ⏸️ TEST |
| Close/reopen tab | ✅ Reconnects | ⏸️ TEST |
| Invalid game ID | ✅ Error + redirect | ⏸️ TEST |
| Quit game cleanup | ✅ localStorage cleared | ⏸️ TEST |
| Network disconnect | ✅ Auto-reconnect | ⏸️ TEST |
| Multiple tabs | ⚠️ Last tab wins | ⏸️ TEST |
| localStorage persistence | ✅ Survives refresh | ⏸️ TEST |
| Backend restart | ❌ Game lost (expected) | ⏸️ TEST |

---

## Next Steps

1. Run manual tests following scenarios above
2. Update "Actual Behavior" sections with test results
3. File any bugs discovered
4. Consider automated E2E tests for browser refresh (Phase 8+)

---

**Questions?** See `STATUS.md` or `TESTING_IMPROVEMENT_PLAN.md` for overall project status.
