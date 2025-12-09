# Testing Strategy - Poker Learning App

**Date**: December 9, 2025
**Status**: ⚠️ **IN PROGRESS** - Building comprehensive test infrastructure

---

## 🚨 Problem Statement

After 3 days of UAT testing, we've discovered **4 critical bugs** that our 600-game stress test did NOT catch:

| Bug | Severity | Caught By | Why Tests Missed It |
|-----|----------|-----------|---------------------|
| UAT-5: All-in hang | CRITICAL | Manual UAT | Stress tests = AI-only, didn't test WebSocket |
| UAT-11: Hand analysis intermittent | HIGH | Manual UAT | Stress tests don't call `/analysis` endpoint |
| Step Mode: Deadlock | CRITICAL | Manual UAT | WebSocket blocking not tested |
| Infinite loop: Same player | CRITICAL | Manual UAT | All-in scenario with human not tested |

### Root Cause

Our stress tests (`test_stress_ai_games.py`) run **AI-only games** directly against the **PokerEngine**, bypassing:
- ❌ WebSocket layer (`websocket_manager.py`)
- ❌ FastAPI endpoints (`main.py`)
- ❌ Human action sequences
- ❌ Frontend integration
- ❌ Real user scenarios

**The bugs are in the integration layer, not the core engine.**

---

## 📊 Current Test Coverage

### ✅ What We Have

| Test Suite | File | Tests | Coverage | Speed |
|------------|------|-------|----------|-------|
| Unit: Action Processing | `test_action_processing.py` | 20 | apply_action() | Instant |
| Unit: Hand Strength | `test_hand_strength.py` | 24 | score_to_strength() | Instant |
| Unit: State Advancement | `test_state_advancement.py` | 15 | _advance_state_core() | Instant |
| Unit: Heads-Up | `test_heads_up.py` | 20 | 2-player rules | Instant |
| Stress: AI-Only Games | `test_stress_ai_games.py` | 600 games | Core engine | 50min |
| Edge Cases | `test_edge_case_scenarios.py` | 350+ | Side pots, ties, etc. | Instant |

**Total**: ~1,000 tests, 600 complete games

### ❌ What We're Missing

| Test Type | File | Status | Would Catch |
|-----------|------|--------|-------------|
| **WebSocket Integration** | `test_websocket_integration.py` | 🟡 Created, needs fixes | All 4 UAT bugs |
| **Scenario-Based Tests** | `test_scenarios.py` | ❌ Not created | User flows |
| **E2E Browser Tests** | Playwright | ❌ Not created | Full stack bugs |
| **API Integration** | `test_api_integration.py` | ❌ Not created | REST bugs |

---

## 🎯 Test Strategy Going Forward

### Test Pyramid (Proper)

```
        /\
       /  \  E2E (Playwright) - 10 tests, critical user flows
      /    \
     /------\
    / Integration \ WebSocket + API - 50 tests, real scenarios
   /--------------\
  /    Unit Tests  \ Engine + Utils - 500+ tests, fast
 /------------------\
```

### Priority 1: WebSocket Integration Tests (COMPLETED - Tests Running, Bugs Found!)

**File**: `backend/tests/test_websocket_integration.py`
**Results**: `backend/tests/INTEGRATION_TEST_RESULTS.md`

**Critical Tests**:
1. ✅ `test_connection_and_initial_state` - **PASSING** - Basic WebSocket flow works
2. ✅ `test_simple_call_action` - **PASSING** - Human action → AI response works
3. ❌ `test_human_all_in_basic` - **FAILING** - **FOUND BUG: Game stuck in pre_flop after all-in**
4. ⏸️ `test_human_all_in_after_ai_raise` - Not run yet (blocked by Bug #1)
5. ❌ `test_step_mode_basic` - **FAILING** - **FOUND BUG: Step Mode not sending awaiting_continue events**
6. ⏸️ `test_step_mode_no_deadlock` - Not run yet (blocked by Bug #2)
7. ⏸️ `test_play_three_hands` - Not run yet

**Status**: ✅ Test framework working! Fixed `TestClient` compatibility by using `websockets` library directly. **Tests are now catching real bugs!**

**Bugs Discovered**:
- 🐛 **Bug #1**: All-in state advancement failure (game stuck in pre_flop)
- 🐛 **Bug #2**: Step Mode not emitting awaiting_continue events

**How to Run**:
```bash
cd backend
python -m pytest tests/test_websocket_integration.py -v

# Run specific test
python -m pytest tests/test_websocket_integration.py::TestWebSocketBasicFlow::test_connection_and_initial_state -v
```

### Priority 2: Scenario-Based Tests (TODO)

**File**: `backend/tests/test_scenarios.py` (to be created)

**Scenarios to Test**:
1. **All-In Scenarios**:
   - Human all-in pre-flop
   - Human all-in after AI raise ← **The bug!**
   - Multiple players all-in
   - All-in with side pots

2. **Step Mode Scenarios**:
   - Toggle Step Mode mid-hand
   - Step Mode through full hand
   - Step Mode + all-in combination

3. **Edge Cases**:
   - Player eliminated mid-game
   - Blind increases over 100+ hands
   - 4 players all-in (max side pots)

### Priority 3: E2E Browser Tests (TODO)

**Tool**: Playwright
**File**: `tests/e2e/test_poker_game.py`

**Critical Flows**:
1. Create game → Play 3 hands → Quit
2. Enable Step Mode → Play hand → Disable
3. Go all-in → Verify no hang
4. Analyze hand → Verify display

---

## 🛠️ Implementation Plan

### Phase 1: Fix WebSocket Integration Tests (2-3 hours)

1. **Fix TestClient API issues**
   - Update to correct Starlette API
   - Test WebSocket connection/sending/receiving

2. **Run all WebSocket tests**
   - Verify they catch the infinite loop bug
   - Verify they catch the Step Mode deadlock

3. **Add to CI/CD**
   - Run on every PR
   - Must pass before merge

### Phase 2: Create Scenario Tests (2-3 hours)

1. **Extract common patterns** from WebSocket tests
2. **Create deterministic scenarios** (not random)
3. **Test specific bug conditions**:
   - Human all-in after AI raise
   - Step Mode toggle mid-sequence
   - Multiple players all-in

### Phase 3: Set Up Playwright (3-4 hours)

1. **Install Playwright**
   ```bash
   cd frontend
   npm install -D @playwright/test
   npx playwright install
   ```

2. **Write 5-10 critical E2E tests**
   - Full game flow
   - Step Mode usage
   - Error handling

3. **Add to CI/CD**

---

## 📈 Success Metrics

### Before (Current State)
- ✅ 1,000+ unit tests
- ✅ 600 AI-only stress tests
- ❌ 0 WebSocket integration tests
- ❌ 0 E2E tests
- ❌ 4 UAT bugs missed

### After (Target State)
- ✅ 1,000+ unit tests
- ✅ 600 AI-only stress tests
- ✅ 50+ WebSocket integration tests ← **NEW**
- ✅ 20+ scenario-based tests ← **NEW**
- ✅ 10+ E2E browser tests ← **NEW**
- ✅ UAT bugs caught by automated tests

**Target**: **Catch 90%+ of UAT bugs in automated tests before manual testing**

---

## 🚀 How to Run Tests

### Quick Smoke Test (2 min)
```bash
# Unit tests
cd backend
python -m pytest tests/test_action_processing.py tests/test_hand_strength.py tests/test_state_advancement.py -v

# WebSocket integration (when fixed)
python -m pytest tests/test_websocket_integration.py::TestWebSocketBasicFlow -v
```

### Full Regression (15 min)
```bash
# All unit + integration tests
cd backend
python -m pytest tests/ -v --ignore=tests/test_stress_ai_games.py

# E2E tests (when created)
cd frontend
npx playwright test
```

### Comprehensive (60 min)
```bash
# Everything including stress tests
cd backend
python -m pytest tests/ -v
```

---

## 🐛 Known Issues

1. **TestClient WebSocket API** - Need to update to correct Starlette API
2. **Async test handling** - May need `pytest-asyncio` for async WebSocket tests
3. **Test isolation** - Games may share state, need proper cleanup

---

## 📝 Next Steps

1. ✅ Create WebSocket integration test framework - **DONE**
2. ✅ Fix TestClient API compatibility - **DONE** (used websockets library)
3. ✅ Run WebSocket tests - **DONE** - **Found 2 critical bugs!**
4. 🟡 **Fix Bug #1: All-in state advancement** - **IN PROGRESS**
5. 🟡 **Fix Bug #2: Step Mode awaiting_continue events** - **IN PROGRESS**
6. ⏳ Complete remaining WebSocket tests (infinite loop, deadlock)
7. ⏳ Create scenario-based test suite
8. ⏳ Set up Playwright E2E tests
9. ⏳ Add all tests to CI/CD pipeline

## 🎯 Current Status

**✅ Major Achievement**: WebSocket integration test framework is working and catching real bugs that our 600-game stress tests missed!

**Bugs Found by Integration Tests**:
1. 🐛 All-in state advancement failure (game stuck in pre_flop)
2. 🐛 Step Mode not sending awaiting_continue events

**Next Immediate Action**: Fix the two bugs discovered by integration tests, then continue running the remaining critical tests (infinite loop detection, deadlock prevention).

---

**Last Updated**: December 9, 2025
**Contributors**: Claude, Sandeep
