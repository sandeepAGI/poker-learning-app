# Testing Fixes Plan

**Date Created**: December 16, 2025
**Purpose**: Investigate and fix failing tests discovered during React infinite loop fix validation
**Status**: 🔴 IN PROGRESS

---

## Executive Summary

After completing the React infinite loop fix (Bug Fix 5), a full backend test suite run revealed **9 failing tests** and **5 errors** out of 274 total tests. While GitHub Actions CI passes (107/107 tests), the local full suite exposed potential bugs in edge cases and stress scenarios.

**Key Finding**: These failures appear to be **pre-existing bugs**, not regressions from our React fix (frontend-only changes). However, they represent real issues that need investigation.

---

## Test Failure Classification

### 🔴 Critical Issues (1 test)
- Chip conservation violations in complex scenarios

### 🟠 High Priority (3 tests)
- AI tournament hands getting stuck
- Fold cascade scenario failures
- Multi-street hand not reaching showdown

### 🟢 Low Priority (1 test)
- AI count validation (test bug, not production bug)

### ⚪ Infrastructure (9 tests)
- Tests requiring running server (excluded from investigation)

---

## Investigation Plan

### Phase 1: Baseline Validation (30 min)
**Goal**: Confirm these are pre-existing issues, not regressions from React fix

**Tasks**:
1. Checkout commit before React fix: `git checkout 176c60c2`
2. Run same failing tests on old commit
3. Document which tests were already failing
4. Return to current commit: `git checkout main`

**Success Criteria**:
- ✅ Confirm failures existed before our changes
- ✅ Identify if any NEW failures appeared

**Exit Condition**: If any failures are NEW (didn't exist before), investigate React fix impact first

---

### Phase 2: Critical Bug - Chip Conservation (2-4 hours)
**Priority**: 🔴 CRITICAL - #1
**File**: `backend/tests/test_edge_case_scenarios.py::TestChipConservationEdgeCases::test_chip_conservation_complex_scenario`

#### 2.1: Understand the Test (30 min)
**Tasks**:
1. Read test code and understand what scenarios it's testing
2. Review chip conservation invariant definition
3. Identify which of the 100 scenarios are failing (29 failures)
4. Document the test's methodology

**Deliverable**: Summary of what chip conservation means and how test validates it

#### 2.2: Reproduce and Isolate (1 hour)
**Tasks**:
1. Run test with verbose logging: `pytest -vvs`
2. Add debug prints to identify which specific scenarios fail
3. Extract the 29 failing scenarios
4. Create minimal reproduction case for one failing scenario

**Deliverable**: Minimal test case that reproduces chip conservation violation

#### 2.3: Root Cause Analysis (1-2 hours)
**Tasks**:
1. Trace execution through failing scenario
2. Identify where chips are created/destroyed
3. Check `poker_engine.py` chip tracking logic
4. Review pot calculation, side pot logic, all-in handling
5. Check if related to bet accounting

**Deliverable**: Root cause explanation with line numbers

#### 2.4: Fix and Validate (1 hour)
**Tasks**:
1. Implement fix based on root cause
2. Verify fix resolves all 29 failing scenarios
3. Run full chip conservation test suite
4. Run related tests (side pots, all-in scenarios)
5. Commit with detailed message

**Deliverable**:
- Fix committed
- Test passes 100/100 scenarios
- No regressions in related tests

---

### Phase 3: High Bug - Tournament Hands Stuck (2-3 hours)
**Priority**: 🟠 HIGH - #2
**File**: `backend/tests/test_ai_only_games.py::test_ai_only_tournament`

#### 3.1: Understand the Failures (30 min)
**Tasks**:
1. Read test code - what does "ai only tournament" do?
2. Understand why hands get "stuck"
3. Review state advancement logic
4. Check if related to Phase 1 infinite loop bug

**Deliverable**: Understanding of stuck hand conditions

#### 3.2: Reproduce Specific Stuck Hands (1 hour)
**Tasks**:
1. Add logging to capture game state when hand gets stuck
2. Run test multiple times to get consistent failures
3. Extract game state snapshots for stuck hands
4. Identify common patterns (all stuck at same state?)

**Deliverable**: Game state dumps for stuck hands

#### 3.3: Root Cause Analysis (1 hour)
**Tasks**:
1. Review `_advance_state_core()` logic
2. Check `_maybe_advance_state()` conditions
3. Review betting round completion logic
4. Check AI decision processing in tournament mode
5. Look for infinite loop potential

**Deliverable**: Root cause with specific code paths

#### 3.4: Fix and Validate (30 min)
**Tasks**:
1. Implement fix
2. Run tournament test multiple times (10+ runs)
3. Verify 0 stuck hands across all runs
4. Commit fix

**Deliverable**: Tournament test passes 100/100 hands consistently

---

### Phase 4: High Bug - Fold Cascade Failures (1-2 hours)
**Priority**: 🟠 HIGH - #3
**File**: `backend/tests/test_edge_case_scenarios.py::TestFoldCascadeScenarios::test_fold_cascade_random`

#### 4.1: Understand Fold Cascades (20 min)
**Tasks**:
1. Read test - what is a "fold cascade"?
2. Understand the 30 random scenarios
3. Review expected vs actual success rate (25 vs 23)

**Deliverable**: Understanding of fold cascade edge cases

#### 4.2: Identify Failing Scenarios (40 min)
**Tasks**:
1. Run test with detailed logging
2. Capture the 7 failing scenarios
3. Look for patterns in failures

**Deliverable**: List of 7 failing scenarios with details

#### 4.3: Root Cause and Fix (1 hour)
**Tasks**:
1. Analyze fold handling when multiple players fold
2. Check state advancement after folds
3. Review pot awarding logic
4. Implement fix
5. Validate 30/30 scenarios pass

**Deliverable**: Fix committed, test passes consistently

---

### Phase 5: Medium Bug - Multi-Street Showdown (1 hour)
**Priority**: 🟡 MEDIUM - #4
**File**: `backend/tests/test_user_scenarios.py::TestComplexBettingSequences::test_raise_call_multiple_streets`

#### 5.1: Flakiness Analysis (30 min)
**Tasks**:
1. Run test 20 times locally
2. Document pass/fail rate
3. Check GitHub Actions history (does it ever fail in CI?)
4. Review AI behavior (are they just folding early?)

**Deliverable**: Determination if this is a bug or expected AI behavior

#### 5.2: Fix or Mark as Flaky (30 min)
**Tasks**:
- **If bug**: Fix and validate
- **If flaky AI behavior**: Add `@pytest.mark.flaky` decorator or adjust test expectations
- **If expected behavior**: Update test to handle early folds gracefully

**Deliverable**: Test stabilized or properly marked

---

### Phase 6: Low Priority - Test Bug (30 min)
**Priority**: 🟢 LOW - #5
**File**: `backend/tests/test_edge_case_scenarios.py::TestMultipleAllInsSidePots::test_multiple_allin_scenarios_random`

#### 6.1: Fix Test Bug
**Tasks**:
1. Review test code - why is it passing ai_count > 3?
2. Fix test to use valid AI counts (1-3)
3. Verify test passes after fix

**Deliverable**: Test fixed to use valid parameters

---

## Post-Fix Validation

### Full Test Suite Validation
**After each fix**:
1. Run quick test suite: `PYTHONPATH=backend python -m pytest backend/tests/test_negative_actions.py backend/tests/test_hand_evaluator_validation.py backend/tests/test_property_based_enhanced.py -v`
2. Run specific test file that was fixed
3. Run full backend suite: `PYTHONPATH=backend python -m pytest backend/tests/ -v`

### GitHub Actions Validation
**After all fixes**:
1. Commit all fixes
2. Push to GitHub
3. Monitor GitHub Actions run
4. Verify all CI tests still pass

---

## Success Criteria

### Phase 1 Complete
- [x] Confirmed failures are pre-existing (not caused by React fix)

### Phase 2 Complete (Critical)
- [ ] Chip conservation test passes 100/100 scenarios
- [ ] Root cause documented
- [ ] Fix committed

### Phase 3 Complete (High)
- [ ] AI tournament test passes 0 stuck hands
- [ ] Root cause documented
- [ ] Fix committed

### Phase 4 Complete (High)
- [ ] Fold cascade test passes 30/30 scenarios
- [ ] Root cause documented
- [ ] Fix committed

### Phase 5 Complete (Medium)
- [ ] Multi-street test stabilized (passes consistently or properly marked flaky)
- [ ] Decision documented (bug vs expected behavior)

### Phase 6 Complete (Low)
- [ ] Test bug fixed
- [ ] Test passes with valid parameters

### Final Validation
- [ ] All fixed tests pass locally
- [ ] Full backend suite: 274/274 tests pass
- [ ] GitHub Actions: All CI tests pass
- [ ] STATUS.md updated with fixes

---

## Estimated Timeline

| Phase | Priority | Time Estimate | Cumulative |
|-------|----------|---------------|------------|
| Phase 1: Baseline | - | 30 min | 30 min |
| Phase 2: Chip Conservation | 🔴 Critical | 2-4 hours | 2.5-4.5 hours |
| Phase 3: Stuck Hands | 🟠 High | 2-3 hours | 4.5-7.5 hours |
| Phase 4: Fold Cascade | 🟠 High | 1-2 hours | 5.5-9.5 hours |
| Phase 5: Multi-Street | 🟡 Medium | 1 hour | 6.5-10.5 hours |
| Phase 6: Test Bug | 🟢 Low | 30 min | 7-11 hours |
| **Total** | | **7-11 hours** | |

**Recommended Approach**: Fix critical and high priority issues first (Phases 1-4), then decide if medium/low priority warrant immediate fixing.

---

## Risk Assessment

### Low Risk
- Phase 6 (test bug fix) - test code only, no production impact

### Medium Risk
- Phase 4 (fold cascade) - may affect fold handling in production
- Phase 5 (multi-street) - if it's a real bug, could affect multi-street games

### High Risk
- Phase 2 (chip conservation) - **CRITICAL** - affects game integrity and fairness
- Phase 3 (stuck hands) - could cause infinite loops or hangs in production

---

## Rollback Plan

If any fix introduces regressions:

1. **Identify regression** via test suite
2. **Revert commit**: `git revert <commit-hash>`
3. **Document issue** in this plan
4. **Re-analyze** with more information
5. **Attempt alternative fix**

---

## Documentation Updates

After each fix:
1. Update this document with findings
2. Update STATUS.md if fixing a critical bug
3. Add comments to code explaining the fix
4. Consider adding regression tests

---

## Notes

- React infinite loop fix (frontend) is **independent** from these backend test failures
- These failures were likely present before but **not caught** because full test suite isn't run regularly
- This is exactly why comprehensive testing is valuable - it found real bugs
- GitHub Actions doesn't run these specific tests, which is why they weren't caught earlier

---

## Related Documentation

- `STATUS.md` - Bug Fix 5 (React infinite loop)
- `docs/REACT_INFINITE_LOOP_FIX_PLAN.md` - Complete 3-phase fix plan
- `docs/TESTING_IMPROVEMENT_PLAN.md` - Original testing strategy
- `backend/tests/test_edge_case_scenarios.py` - Edge case test suite
- `backend/tests/test_ai_only_games.py` - AI-only stress tests
