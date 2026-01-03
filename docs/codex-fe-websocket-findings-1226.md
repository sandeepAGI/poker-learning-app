# Frontend & WebSocket Review Findings (2024-12-26)

The following items summarize the issues identified while reviewing the poker learning app's frontend and WebSocket workflow. Each entry lists rationale, evidence, and an assessment of criticality to gameplay or reliability.

--

## FIX PROTOCOL (Test-Driven Development)

For each issue, we follow the TDD Red-Green-Refactor cycle:

1. **Review**: Analyze issue and confirm agreement on the problem
2. **Red - Write Failing Test**: Write a test that demonstrates the bug/issue
   - Test should FAIL, proving the issue exists
   - Test should be specific to the issue being fixed
3. **Green - Implement Fix**: Write minimal code to make the test pass
   - Make the failing test pass
   - Don't over-engineer or add extra features
4. **Refactor**: Clean up code if needed while keeping tests green
   - Improve code quality without changing behavior
   - Ensure all tests still pass
5. **Regression**: Run full test suite (unit + integration + e2e)
   - Confirm all existing tests still pass
   - Confirm new test passes
6. **Document**: Update progress tracking below
7. **Commit**: Git commit and push with descriptive message

--

## 1. Mixed Import Paths Break Showdown State (Critical)
**Rationale**: `backend/main.py` mixes relative package roots. When the API is launched from the repository root or any directory where `backend` is not an installed package, importing `HandEvaluator` via `from backend.game…` fails the moment a showdown state is serialized, killing both REST and WebSocket clients during play.

**Evidence**: `backend/main.py:260-283` imports `HandEvaluator` inside `get_game_state` using `from backend.game.poker_engine import HandEvaluator` while the rest of the module—and `websocket_manager.py`—import via `from game import …`. Running `uvicorn backend.main:app` from the repo root raises `ModuleNotFoundError: No module named 'backend'` as soon as the code path executes. The websocket manager version works because it uses the correct `game.` path.

**Criticality**: *Critical* — The process crashes during normal play as soon as a showdown occurs unless the app is launched from exactly the subdirectory that makes `backend` importable, which is fragile and user-hostile for deployment.

## 2. Minimum Raise Calculation Ignores Previous Raise Size (High)
**Rationale**: Texas Hold'em requires each raise to be at least as large as the previous raise. Both the frontend controls and the backend `apply_action` logic hard-code the minimum raise to `current_bet + big_blind`, so after an opponent makes a large raise the UI still allows (and the engine accepts) a much smaller raise, producing illegal betting sequences and incorrect pots.

**Evidence**: `frontend/components/PokerTable.tsx:45-57` computes `minRaise = gameState.current_bet + (gameState.big_blind || 10)` and bounds the slider to that value; `backend/game/poker_engine.py:1199-1218` enforces the same formula. Reproducing a 5/10 game where UTG raises to 60, the next player can "raise" to 70 (a 10-chip increment) which violates standard hold'em rules and results in chips being removed from the pot when later calls are capped.

**Criticality**: *High* — Causes rule violations, incorrect chip accounting, and undermines the learning objective of practicing legal betting lines.

**Research Findings (2026-01-02)**:
- **Backend is BROKEN** — Confirmed `poker_engine.py:1202` uses incorrect formula: `min_raise = self.current_bet + self.big_blind`
- **Correct Texas Hold'em rule**: Min raise = current_bet + (size of previous raise), NOT current_bet + big_blind
- **Example**: BB=10, UTG raises to 30 (raise of 20) → Next raiser must raise by ≥20, so min_raise=50, NOT 40
- **Missing data**: Backend doesn't track `last_raise_amount`, only `last_raiser_index`
- **AI also broken**: All AI decision logic uses same wrong formula (lines 374, 385, 416, 427, 434, 446, 467, 526, 538, 557, 563)
- **Fix requires**:
  1. Add `self.last_raise_amount` field to PokerGame
  2. Track it on each raise: `self.last_raise_amount = raise_total - previous_current_bet`
  3. Update formula: `min_raise = self.current_bet + (self.last_raise_amount or self.big_blind)`
  4. Reset to `self.big_blind` at start of each betting round
  5. Update frontend to use `last_raise_amount` from state

## 3. Reconnect Screen Triggered by Unrelated Errors (Medium)
**Rationale**: The dynamic game route treats any store error as a reconnection failure, immediately replacing the table UI with a red error card and redirecting to the lobby even when the actual issue is just an invalid action or analysis fetch.

**Evidence**: `frontend/app/game/[gameId]/page.tsx:52-74` renders the "Unable to Reconnect" screen whenever `useGameStore().error` is truthy. The same error field is set for mundane UI/API validation errors in `frontend/lib/store.ts:138-205`, so a rejected raise or analysis request boots the user from the table despite the websocket being healthy.

**Criticality**: *Medium* — Disrupts normal gameplay and can force players out of active hands, but does not corrupt data.

## 4. Step Mode Banner Never Clears After Auto-Continue (Medium)
**Rationale**: The store sets `awaitingContinue=true` on the `awaiting_continue` event and only clears it when `sendContinue()` runs. When the backend auto-resumes after the 60 s timeout or the player disables step mode, the UI keeps showing the yellow paused banner and "Continue" button even though the hand is moving.

**Evidence**: `frontend/lib/store.ts:270-275` sets `awaitingContinue` without listening for subsequent `state_update` messages, and `sendContinue()` is the only place that resets it (`frontend/lib/store.ts:153-167`). The backend auto-resumes via `asyncio.wait_for(... timeout=60)` and continues processing without signalling the frontend (`backend/websocket_manager.py:483-515`), leaving the UI stuck in a paused state.

**Criticality**: *Medium* — Misleads users and generates redundant continue requests, but the game does progress.

**Research Findings (2026-01-02)**:
- **Purpose of 60s timeout**: Safety mechanism to prevent game hanging forever if:
  - User closes browser without clicking Continue
  - Frontend crashes while paused
  - Network disconnects during pause
  - User forgets they had the game paused
- **Timeout location**: `websocket_manager.py:507` — `await asyncio.wait_for(manager.step_mode_events[game_id].wait(), timeout=60.0)`
- **Behavior on timeout**: Backend logs "Timeout waiting for continue (proceeding anyway)" and continues processing
- **Recommendation**: Keep timeout at 60s (hardcoded, not configurable) because:
  - Too short (< 30s) frustrates users who need time to think
  - Too long (> 120s) defeats purpose of preventing hangs
  - 60s is industry-standard for user interaction timeouts
  - Users can disable step mode entirely if they don't want pauses
- **Fix requires**:
  1. Backend emit `auto_resumed` event after timeout (line 515)
  2. Frontend listen for `auto_resumed` event and clear `awaitingContinue` flag

## 5. Decision History Loses Deduplication on Refresh (Medium)
**Rationale**: The websocket serializer always includes `decision_id`, but the REST `GameResponse` (used when reconnecting after a refresh) omits that field, so `_processAIDecisions` attempts to deduplicate on `undefined` IDs and the AI reasoning sidebar immediately shows duplicates when the websocket stream resumes.

**Evidence**: `frontend/lib/store.ts:352-386` deduplicates by `decision.decision_id`. On reconnect, `pokerApi.getGameState` returns data from `backend/main.py:216-236`, which includes only `action` and `amount`. In contrast, `backend/websocket_manager.py:180-201` always includes `decision_id`. After a refresh the initial state seeds the history with entries lacking IDs, so every subsequent websocket update is treated as new even if it refers to the same `decision_id`.

**Criticality**: *Medium* — Doesn't break gameplay but confuses learners by showing repeated or ghost AI decisions.

**Research Findings (2026-01-02)**:
- **Confirmed schema divergence**: REST API omits `decision_id` field, WebSocket includes it
- **WebSocket serializer** (`websocket_manager.py:200`): Always includes `decision_id` with comment "Critical for deduplication"
- **REST API serializer** (`main.py:232-236`): Omits `decision_id` field entirely
- **Other schemas**: Verified REST and WebSocket return identical structures for:
  - Player data (same fields, same order)
  - Winner info (same structure)
  - Blind positions (both include dealer_position, small_blind_position, big_blind_position)
  - All other game state fields
- **Root cause**: Oversight when fixing Issue #3 (deduplication) — fix was only applied to WebSocket, not REST
- **Fix requires**: Add `decision_id` to REST API response in `main.py:232-236` (1-line change)

## 6. WebSocket URL Builder Breaks When API Is Behind a Path Prefix (Low)
**Rationale**: The frontend derives the socket URL by stripping `http(s)://` and prepending `ws(s)://`, so if `NEXT_PUBLIC_API_URL` contains a path (e.g., `https://example.com/api` behind a reverse proxy) the client tries to connect to `wss://example.com/api/ws/...`. The FastAPI server exposes `/ws/...` at the root, so connections behind a prefix fail.

**Evidence**: `frontend/lib/websocket.ts:83-88` simply removes the protocol and inherits any path segments. In proxied deployments that serve the REST API under `/api`, HTTP requests work but websocket negotiation fails with 404/403. Using `new URL()` and dropping `pathname` when composing `/ws/${gameId}` avoids this edge case.

**Criticality**: *Low* — Only affects deployments behind prefixed proxies; localhost development works, but production environments that commonly mount APIs under `/api` will see websocket failures.

---

## PROGRESS TRACKING

### Fix Priority Order
1. ✅ Issue #1 (Critical) - Mixed Import Paths - **SKIPPED** - Already fixed in previous commits
2. ✅ Issue #2 (High) - Minimum Raise Calculation - **COMPLETE** - Tests pass, ready to commit
3. ⏳ Issue #5 (Medium) - Decision History Deduplication - **PENDING** (Quick 1-line fix, do before #3/#4)
4. ⏳ Issue #3 (Medium) - Reconnect Screen Errors - **PENDING**
5. ⏳ Issue #4 (Medium) - Step Mode Banner - **PENDING**
6. ⏳ Issue #6 (Low) - WebSocket URL Builder - **PENDING**

### Issue #1: Mixed Import Paths [SKIPPED]
**Status**: Already fixed in codebase
- ✅ Verified `main.py:282` uses `from game.poker_engine import HandEvaluator` (not `from backend.game...`)
- ✅ All imports in `main.py` and `websocket_manager.py` use consistent `from game...` pattern
- ✅ No action needed

### Issue #2: Minimum Raise Calculation [COMPLETE ✅]
**Status**: Fixed and tested
- ✅ Step 1 (Red): Wrote 4 failing tests demonstrating the bug
- ✅ Step 2 (Green): Added `last_raise_amount` field to PokerGame
- ✅ Step 3 (Green): Updated `apply_action` validation to use correct formula
- ✅ Step 4 (Refactor): Updated AI decision logic (all personalities)
- ✅ Step 5 (Refactor): Updated frontend min raise calculation
- ✅ Step 6 (Regression): All 27 tests passing (12 negative + 5 validator + 6 property + 4 new)
- ⏳ Step 7 (Commit): Ready to commit

**Changes Made**:
1. **Backend (`poker_engine.py`)**:
   - Added `self.last_raise_amount` field (initialized in `__init__`, reset in `start_new_hand` and `_start_new_round`)
   - Updated minimum raise formula: `min_raise = current_bet + (last_raise_amount or big_blind)`
   - Track raise amount on each raise: `self.last_raise_amount = raise_total - previous_bet`
   - Set to `big_blind` when BB is posted pre-flop
   - Updated all AI decision logic to use `min_raise_increment` instead of hard-coded `big_blind`

2. **API (`main.py` + `websocket_manager.py`)**:
   - Added `last_raise_amount` to `GameResponse` model
   - Exposed `last_raise_amount` in REST and WebSocket responses

3. **Frontend (`PokerTable.tsx` + `types.ts`)**:
   - Added `last_raise_amount` to `GameState` interface
   - Updated min raise calculation: `minRaise = current_bet + (last_raise_amount ?? big_blind)`

4. **Tests (`test_minimum_raise_rules.py`)**:
   - Created 4 comprehensive tests covering all scenarios
   - All tests pass ✅

### Issue #5: Decision History Deduplication [PENDING]
**Status**: Not started
- ⏳ Step 1 (Red): Write test for REST API response
- ⏳ Step 2 (Green): Add `decision_id` to `main.py:232-236`
- ⏳ Step 3 (Regression): Verify deduplication works after refresh
- ⏳ Step 4 (Commit): Git commit

### Issue #3: Reconnect Screen Errors [PENDING]
**Status**: Not started

### Issue #4: Step Mode Banner [PENDING]
**Status**: Not started

### Issue #6: WebSocket URL Builder [PENDING]
**Status**: Not started

---

## Test Results Log

### 2026-01-02: Initial Research Complete
- ✅ Confirmed Issue #2: Backend uses wrong min raise formula
- ✅ Confirmed Issue #4: 60s timeout is intentional, keep hardcoded
- ✅ Confirmed Issue #5: Only `decision_id` field diverges between REST/WebSocket
- ✅ All 6 issues validated and prioritized

### 2026-01-02: Issue #2 Complete
- ✅ Created 4 comprehensive tests (all passing)
- ✅ Added `last_raise_amount` tracking to backend
- ✅ Updated validation logic to use correct Texas Hold'em formula
- ✅ Updated all AI decision logic (9 locations)
- ✅ Exposed `last_raise_amount` in REST and WebSocket APIs
- ✅ Updated frontend calculation and TypeScript types
- ✅ All regression tests passing (27/27)
- 📝 Ready to commit

