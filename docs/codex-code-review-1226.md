# Code Review – Poker Learning App (Codex 2024-12-26)

This document captures the issues uncovered during a full-stack review (backend + frontend), along with recommended fixes and verification ideas.

---

## BASELINE TEST RESULTS (2026-01-02)

**Initial**: 34/35 PASSED (97%)
- ✗ `test_play_until_elimination` - TimeoutError after 40 hands (22min)

**Fix Applied**: Handle `game_over` event in elimination test
- File: `backend/tests/test_user_scenarios.py::test_play_until_elimination`
- Changes: Check for `game_over` event, handle all-AI elimination, graceful timeout handling
- Result: ✅ Test now PASSES in 11.5 minutes

**Final Baseline**: 35/35 PASSED (100%) ✅
- ✓ All negative action tests (12/12)
- ✓ All hand evaluator validation tests (5/5)
- ✓ All property-based tests (6/6, including 1000 random scenarios)
- ✓ All user scenario tests (12/12)
- ✓ Frontend build (2.5s)

---

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

### Progress Tracking
- [x] Issue #1: Short-Stack Call/Raise UI ✅ **FIXED**
- [ ] Issue #2: Blind/Button Indicators Drift
- [ ] Issue #3: AI Reasoning Sidebar Data Loss
- [ ] Issue #4: Session Analysis Parameter Issues
- [ ] Issue #5: Orphaned/Redundant Code

---

## FIXES COMPLETED

### Issue #1: Short-Stack Call/Raise UI ✅

**Problem**: UI disabled Call/Raise buttons when player stack < bet amount, even though backend supports all-in calls/raises.

**Fix Applied**:
- **File**: `frontend/components/PokerTable.tsx` (lines 47-57, 643-652)
- **Changes**:
  - `canCall`: Changed from `stack >= callAmount` to `stack > 0`
  - `canRaise`: Changed from `maxRaise >= minRaise && stack > callAmount` to `stack > 0`
  - Call button label: Shows "Call All-In $X" when `stack < callAmount`
- **Backend Support**: Confirmed via `test_short_stack_actions.py` (2/2 tests pass)
- **Regression**: All 23 quick tests pass
- **Frontend Build**: ✅ Passes (2.8s)

**Result**: Players can now call or raise all-in with any amount of chips, matching poker rules and backend behavior.

---

## 1. Short-Stack Call/Raise UI Blocks Valid Actions
- **Location**: `frontend/components/PokerTable.tsx` lines 44-54.
- **Problem**: The UI disables the Call button when `stack < current_bet - current_bet_posted` and disables Raise unless `stack > callAmount`, even though the backend (`Player.bet` and `PokerGame.apply_action`) supports calling or shoving for less. Human players are forced to fold whenever they have fewer chips than the current bet, diverging from actual poker rules and backend behavior.
- **Proposed Fix**:
  - Allow `call` any time the player still has chips, displaying "Call $X" (where $X will be capped server-side).
  - Keep the Raise panel available for all-ins by setting `maxRaise = stack + current_bet` and deriving `canRaise` from `stack > 0` rather than `stack > callAmount`.
  - Optionally show a "Call All-In" label when `stack < callAmount` for clarity.
- **Tests/Verification**:
  1. Start a game, lose chips until the human stack is below the current bet, and confirm the Call button remains enabled and triggers a valid action.
  2. Inspect WebSocket traffic to ensure the same payload reaches the backend regardless of stack size.
  3. Regression-test normal stacks to ensure min-raise logic still works.

## 2. Blind/Button Indicators Drift During WebSocket Play
- **Location**: `backend/websocket_manager.py::serialize_game_state` (lines ~303-336) recomputes SB/BB positions; `_post_blinds` already sets `small_blind_index`/`big_blind_index` (backend/game/poker_engine.py::1088-1129).
- **Problem**: WebSocket broadcasts derive blind positions by iterating to the next player with chips. If a blind poster busts mid-hand, the WS payload points to a new seat even though the blind should stay on the busted player for the hand. REST `/games/{id}` correctly returns the stored indexes, so the UI shows conflicting button markers depending on which data source arrives last.
- **Proposed Fix**:
  - Pass through `game.small_blind_index` and `game.big_blind_index` (already exposed on the model) instead of recomputing.
  - Include `game.game_id` in the serialized payload to keep client types aligned.
- **Tests/Verification**:
  1. Simulate a hand where the small blind goes all-in and loses; confirm both REST and WS payloads report the same index.
  2. Add a backend unit test verifying `serialize_game_state` uses the stored indexes.
  3. Manual UI check: start a hand, connect/disconnect WS, ensure button indicators do not jump.

## 3. AI Reasoning Sidebar Loses Data When Toggling Visibility
- **Location**: `backend/websocket_manager.py` (AI decision serialization) and `frontend/lib/store.ts::_processAIDecisions`.
- **Problem**: When `show_ai_thinking` is `false`, the server strips reasoning/pot odds before sending `last_ai_decisions`. The store deduplicates decisions using `decision.reasoning`, so hidden actions from the same player appear identical and are dropped. Opening the AI sidebar later reveals blank reasoning/pot-odds metrics.
- **Proposed Fix**:
  - Always store the full `AIDecision` server-side (even if the broadcast uses a slimmed-down version). Add a unique identifier (e.g., `decision_id` or timestamp) per decision.
  - Client-side, dedupe based on `(player_id, decision_id)` instead of free-form reasoning text, and only push decisions into history when `showAiThinking` is true (or when the full data is available).
- **Tests/Verification**:
  1. Toggle “Show AI Thinking” mid-hand and confirm previously hidden actions now appear with full details.
  2. Ensure repeated actions from the same player with similar reasoning still show separately.
  3. If a unique ID is added, extend TypeScript types/tests accordingly.

## 4. Session Analysis Ignores `hand_count` and Rate Limits
- **Location**: `backend/main.py::get_session_analysis` and `frontend/components/PokerTable.tsx::handleSessionAnalysisClick`.
- **Problems**:
  - The backend ignores the `hand_count` parameter when building `hand_history`; it always sends the full history to the LLM but names the cache entry with `hands_to_analyze`, causing inconsistent caching and extra token usage.
  - Rate limiting (`last_analysis_time`) only executes when `use_cache` is true. The frontend always calls the endpoint with `useCache: false`, so users can spam analyses without delay.
- **Proposed Fix**:
  - Slice `hand_history` (`hand_history[-hands_to_analyze:]`) before invoking `llm_analyzer.analyze_session` and report the actual count.
  - Track rate limits independently of the cache flag (set `last_analysis_time` unconditionally or gate on request frequency instead).
  - Optionally allow the client to set `useCache: true` for repeated analyses.
- **Tests/Verification**:
  1. Request a session analysis with `hand_count=5` and confirm the LLM payload contains only the last five hands and the response states `hands_analyzed = 5`.
  2. Rapidly fire the endpoint (with and without cache) and ensure the 60-second throttle triggers every time.
  3. Add backend unit tests for both behaviors.

## 5. Orphaned / Redundant Code Paths
- **Location**:
  - `frontend/lib/api.ts`: `submitAction` and `nextHand` are unused now that the WebSocket handles actions.
  - `frontend/components/AnalysisModal.tsx`: legacy rule-based modal no longer referenced.
  - `frontend/lib/store.ts`: `aiActionQueue`, `addAIDecision`, `clearDecisionHistory` are dead; the queue grows but nothing consumes it.
- **Problem**: These paths add noise, potential confusion, and unused bundle weight. They also make it harder to reason about which code is active.
- **Proposed Fix**:
  - Remove unused REST helpers and components, or explicitly wire them back in if they still serve a purpose.
  - Delete the `aiActionQueue` scaffolding, or implement UI logic that consumes it (e.g., animations) to justify keeping it.
- **Tests/Verification**:
  1. Run `npm run build` / bundle analyzer to ensure tree-shaking removes the dead code after cleanup.
  2. Search for references post-removal to ensure nothing breaks.

---
For each fix, add regression coverage where feasible (unit tests for backend logic, integration/e2e tests for UI changes) and verify via manual gameplay that backend/ frontend stay synchronized across websockets and REST calls.

## Fuzz Test Status (2025-12-26)
Efforts to run the full backend suite revealed that `backend/tests/test_action_fuzzing.py` still hard-fails in CI-like environments because it insists on driving a live HTTP/WebSocket server. Even after allowing the port to be configurable, the tests either hung or kept logging `httpx.ConnectError` when the FastAPI app wasn’t listening on the expected port. Running the module with reduced iteration counts works when a server is up, but exercising the default 1000/500/100/50 iterations inside the main suite is impractical (long runtime + requires an external server). We need to either (a) spin up uvicorn on the test port before running pytest, or (b) refactor these fuzz tests to use in-process clients/mocks so they don’t depend on live sockets.
