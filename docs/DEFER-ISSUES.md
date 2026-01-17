# Deferred Issues - Known Technical Debt

**Date Created:** 2026-01-17
**Status:** Active tracking of deferred technical issues
**Priority:** Address before production deployment

---

## Overview

This document tracks 3 technical issues that were identified as blocking but deferred for later resolution. These issues should be addressed before production deployment.

**Source Files Archived:**
- `archive/deferred/CI-failure-fixes.md` - CI test failures and process issues
- `archive/deferred/CURRENT_FIX_LOG.md` - Viewport scaling UI bug
- `archive/deferred/test-runtime-audit.md` - Test suite optimization incomplete

---

## DEFER-01: CI Test Failures (Critical)

**Original File:** `archive/deferred/CI-failure-fixes.md`
**Date Identified:** 2026-01-12
**Status:** 🔴 CRITICAL - Unresolved bugs affecting test stability
**Estimated Effort:** 15-60+ minutes

### Problem Summary

Two critical bugs discovered during CI failure analysis:

#### Bug 1.1: Logic Error in Performance Test
- **Location:** `backend/tests/test_performance.py:367`
- **Issue:** Loop iterates over ALL players but uses same `game.current_player_index` for ALL actions
- **Error:** `TypeError: '<' not supported between instances of 'NoneType' and 'int'`
- **Root Cause:** Incorrect loop logic introduced during infrastructure work
- **Impact:** Test fails intermittently, indicates potential code review gap

**Problematic Code Pattern:**
```python
for player in game.players:
    if player.is_active and not player.has_acted:
        success = game.apply_action(
            game.current_player_index,  # WRONG - same index for all players!
            "call",
            0
        )
```

**Fix Approach:**
```python
for idx, player in enumerate(game.players):
    if player.is_active and not player.has_acted:
        success = game.apply_action(
            idx,  # CORRECT - use actual player index
            "call",
            0
        )
```

#### Bug 1.2: Segmentation Fault (SIGSEGV)
- **Location:** Backend test cleanup phase (intermittent)
- **Issue:** Segmentation fault (exit code 139) after tests pass
- **Status:** Dismissed without investigation in original analysis
- **Impact:** May indicate memory corruption or C extension issues

**Potential Causes (Not Investigated):**
1. `treys` library C extension crash (most likely)
2. Memory corruption in long-running stress tests
3. Threading issues in asyncio + WebSocket layer
4. Resource exhaustion during test cleanup

**Investigation Steps:**
```bash
# Check for core dumps
ls -la /cores/

# Enable core dumps if disabled
ulimit -c unlimited

# Run tests with memory debugging
valgrind --leak-check=full python -m pytest backend/tests/

# Check for threading issues
python -X dev -m pytest backend/tests/
```

### Why Deferred

- Logic bug is straightforward but needs verification across test suite
- Segfault requires deeper investigation (unknown time commitment)
- Not blocking MVP deployment (tests pass, only cleanup issue)
- Should be addressed before production for test suite stability

### Action Items (When Tackled)

1. ✅ Fix logic error in test_performance.py:367
2. ✅ Search codebase for similar incorrect loop patterns
3. ✅ Investigate segmentation fault with debugging tools
4. ✅ Add process safeguards to prevent similar issues (CI validation gates)
5. ✅ Document findings and update test code review guidelines

---

## DEFER-02: Viewport Scaling UI Bug (High Priority)

**Original File:** `archive/deferred/CURRENT_FIX_LOG.md`
**Date Identified:** 2025-12-27 (fix attempted 2026-01-12)
**Status:** 🔴 HIGH PRIORITY - Core UX broken in split-screen mode
**Estimated Effort:** 2-6 hours (test suite + fix implementation)

### Problem Summary

Human player cards at bottom of screen are cut off in split-screen/windowed mode:
- ✅ Works in fullscreen (1920x1080+)
- ❌ Fails in split-screen (~900px height)
- ❌ Previous fix attempt broke FIX-01 (blind position badges)

### Why Previous Fix Failed

**Attempted Solution:**
- Changed `bottom-44` (176px fixed) to `bottom-[20vh]` (20% viewport height)

**Failure Reasons:**
1. **20vh insufficient in split-screen:**
   - Split-screen ~900px height → 20vh = 180px
   - PlayerSeat content requires ~248px
   - Not enough clearance → cards clipped

2. **Only tested PRE_FLOP state:**
   - ✅ PRE_FLOP works (minimal UI)
   - ❌ FLOP/TURN/RIVER fail (community cards + bet text add vertical space)

3. **Didn't run FIX-01 regression tests:**
   - Blind position badges broke (non-consecutive positions)
   - Dealer badge disappeared
   - Unclear how frontend change affected backend position logic

4. **Violated mandatory process:**
   - Committed without user approval
   - No comprehensive testing across viewport sizes/game states

### Root Cause Analysis

**Fundamental Issue:** Absolute positioning is fragile and doesn't scale well across:
- 4 viewport sizes: 1280x720, 1440x900, 1920x1080, 1920x1200
- 5 game states: PRE_FLOP, FLOP, TURN, RIVER, SHOWDOWN
- 2 player counts: 4-player, 6-player games

### Required Before Any Fix Attempt

**1. Comprehensive E2E Test Suite**

Must cover all combinations:
- 4 viewport sizes × 5 game states × 2 player counts = **40 test scenarios**
- All 8 previous fix regression tests:
  - FIX-01: Blind positions (consecutive, correct rotation)
  - FIX-02: Session analysis modal (opens immediately)
  - FIX-03: Responsive card sizing (all cards visible)
  - FIX-04 (Z-Index): Community cards visible above player seats
  - FIX-09: Winner modal (poker-accurate hand reveals)
  - FIX-10: Compact winner modal (fits viewport)
  - FIX-11: VPIP/PFR calculation accuracy
  - FIX-12: Hand analysis modal (reopens, auto-triggers)

**Estimated:** 2-4 hours to build comprehensive test suite

**2. Design Decision (User Approval Required)**

Three architectural options:

**Option A: Continue Absolute Positioning**
- Pros: Minimal code changes, familiar pattern
- Cons: Fragile, hard to maintain, requires complex calculations
- Effort: 1-2 hours after test suite

**Option B: Refactor to CSS Grid**
- Pros: Proper table structure, responsive by design, maintainable
- Cons: Significant rewrite, may affect other components
- Effort: 4-8 hours (major refactor)

**Option C: Use Poker UI Library**
- Pros: Proven solution, faster implementation
- Cons: May limit customization, external dependency
- Effort: 2-4 hours (integration work)

**3. Mandatory Testing Process**

Before commit:
- ✅ All 40 viewport/state/player scenarios pass
- ✅ All 8 regression tests pass
- ✅ User manual testing at multiple resolutions
- ✅ Explicit user approval with screenshots
- ✅ Document test results

### Why Deferred

- Requires comprehensive test infrastructure first (2-4 hours)
- Needs architectural decision (Option A/B/C)
- Not blocking core functionality (works in fullscreen)
- UX issue but workaround exists (use fullscreen mode)
- Should be addressed before production for professional UX

### Action Items (When Tackled)

1. ✅ Build comprehensive E2E test suite (40 scenarios + 8 regressions)
2. ✅ Present 3 architectural options to user with pros/cons
3. ✅ Get user approval on chosen approach
4. ✅ Implement fix following chosen architecture
5. ✅ Run full test suite and document results
6. ✅ Get user approval with multi-resolution screenshots
7. ✅ Commit with comprehensive test evidence

### Files Involved

- `frontend/components/PokerTable.tsx` line 522 - Bottom positioning
- `frontend/components/PlayerSeat.tsx` - Player card rendering
- Test files to create: `frontend/__tests__/e2e/viewport-scaling.spec.ts`

---

## DEFER-03: Test Suite Optimization Incomplete (Medium Priority)

**Original File:** `archive/deferred/test-runtime-audit.md`
**Date Identified:** 2026-01-12
**Status:** ⚠️ MEDIUM PRIORITY - CI runs inefficiently
**Estimated Effort:** 20 minutes

### Problem Summary

Test suite categorization plan (Fast vs Slow) created but not fully implemented:

**Incomplete Tasks:**
- **Task 0.5.4:** 8 slow tests not marked with `@pytest.mark.slow` decorator
- **Task 0.5.5:** 5 CI workflows not consolidated to 2 workflows
- **Impact:** 48 fast tests not running automatically in CI (only 18 run currently)

### Current State

**Backend Tests:** 56 total files
- **Fast Tests:** 48 files (~86%) - Should run per-commit
- **Slow Tests:** 8 files (~14%) - Should run nightly only

**Current Coverage:**
- ✅ 13 tests in comprehensive workflow (explicit list)
- ❌ 35 fast tests NOT running (missing from CI)
- Coverage: 18/56 tests (31%) vs target 48/56 (86%)

### What's Missing

#### 1. Pytest Markers Not Applied (Task 0.5.4)

**8 files need `@pytest.mark.slow` decorator:**
1. `test_user_scenarios.py` - 19 minutes runtime
2. `test_edge_case_scenarios.py` - 350+ scenarios
3. `test_stress_ai_games.py` - 200-game AI marathon
4. `test_rng_fairness.py` - Statistical validation
5. `test_performance.py` - Performance benchmarks
6. `test_action_fuzzing.py` - Fuzzing attacks
7. `test_concurrency.py` - Concurrent game handling
8. `test_websocket_simulation.py` - Long-running WebSocket scenarios

**Add to each file:**
```python
import pytest

@pytest.mark.slow
def test_name():
    # ... test code ...
```

**Estimated:** 5 minutes

#### 2. Workflows Not Using Markers (Task 0.5.5)

**Comprehensive Workflow** should auto-discover fast tests:
```yaml
- name: Run fast backend tests
  run: |
    PYTHONPATH=backend python -m pytest backend/tests/ \
      -v --tb=short \
      -m "not slow" \
      --timeout=60
```

**Nightly Workflow** should run only slow tests:
```yaml
- name: Run slow backend tests
  run: |
    PYTHONPATH=backend python -m pytest backend/tests/ \
      -v --tb=long \
      -m "slow" \
      --timeout=600
```

**Estimated:** 10 minutes

#### 3. Local Validation (Task 0.5.6)

```bash
# Test fast tests (what Comprehensive will run)
time PYTHONPATH=backend pytest backend/tests/ -m "not slow" -v

# Test slow tests (what Nightly will run)
time PYTHONPATH=backend pytest backend/tests/ -m "slow" -v

# Verify counts
pytest backend/tests/ -m "not slow" --collect-only | grep "tests collected"
pytest backend/tests/ -m "slow" --collect-only | grep "tests collected"
```

**Estimated:** 5 minutes

### Expected Outcomes

**Coverage Increase:**
- Before: 18 tests in CI (31%)
- After: 48 tests in CI (86%)
- Improvement: +30 tests, +55% coverage

**Runtime Impact:**
- Comprehensive: 7-8 min → 8-10 min (+25% time, +167% tests)
- Nightly: 167 min → 60-120 min (-28% to -64% time)

**Maintainability:**
- Before: Explicit file lists (brittle, easy to forget new tests)
- After: Auto-discovery via markers (robust, automatic inclusion)

### Why Deferred

- CI currently works (18 tests running, no failures)
- Quick task but not blocking development
- Nice-to-have optimization, not critical for MVP
- Should be done for production to ensure full test coverage

### Action Items (When Tackled)

1. ✅ Add `@pytest.mark.slow` to 8 test files (5 min)
2. ✅ Update comprehensive workflow to use `-m "not slow"` (5 min)
3. ✅ Update nightly workflow to use `-m "slow"` (5 min)
4. ✅ Run local validation commands (5 min)
5. ✅ Push to CI and verify both workflows work correctly
6. ✅ Update TEST-SUITE-REFERENCE.md with new counts

### Files Involved

**Test Files (add markers):**
- `backend/tests/test_user_scenarios.py`
- `backend/tests/test_edge_case_scenarios.py`
- `backend/tests/test_stress_ai_games.py`
- `backend/tests/test_rng_fairness.py`
- `backend/tests/test_performance.py`
- `backend/tests/test_action_fuzzing.py`
- `backend/tests/test_concurrency.py`
- `backend/tests/test_websocket_simulation.py`

**Workflow Files (update):**
- `.github/workflows/test-suite.yml` (or current comprehensive workflow)
- `.github/workflows/nightly-tests.yml` (or current nightly workflow)

**Documentation (update):**
- `docs/TEST-SUITE-REFERENCE.md`

---

## Priority Summary

| Issue | Priority | Estimated Effort | Blocks MVP? | Blocks Production? |
|-------|----------|------------------|-------------|-------------------|
| DEFER-01: CI Test Failures | 🔴 Critical | 15-60+ min | No | **Yes** |
| DEFER-02: Viewport Scaling | 🔴 High | 2-6 hours | No | **Yes** |
| DEFER-03: Test Optimization | ⚠️ Medium | 20 min | No | Recommended |

**Recommended Order:**
1. **DEFER-03** (quickest, improves CI immediately)
2. **DEFER-01** (critical bugs, affects test stability)
3. **DEFER-02** (requires design decision, most complex)

---

## Notes

- All source documentation archived in `archive/deferred/` with full git history
- This document created: 2026-01-17
- Review before production deployment to ensure all issues addressed
- Update this document when issues are resolved (mark with ✅ RESOLVED and date)

---

## Resolution Tracking

When an issue is resolved, update here:

- [ ] DEFER-01: CI Test Failures - **Not started**
- [ ] DEFER-02: Viewport Scaling UI Bug - **Not started**
- [ ] DEFER-03: Test Suite Optimization - **Not started**
