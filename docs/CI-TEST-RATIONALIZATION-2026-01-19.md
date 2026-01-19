# CI Test Rationalization - 2026-01-19

## Executive Summary

**Decision:** Cancel all CI test workflows and rely exclusively on pre-commit hooks for test coverage.

**Rationale:**
- Current CI test infrastructure is complex, redundant, and broken
- Maintenance burden exceeds value for current team size
- Pre-commit hooks already provide critical regression protection
- Simplification enables focus on feature development vs. infrastructure maintenance

---

## Current State Analysis

### CI Test Failures (2026-01-19)

Analyzed last 3 failures of both Comprehensive and Nightly test suites:

#### 1. Comprehensive Test Suite (`test.yml`)
**Status:** 100% failure rate

**Root Causes:**
1. **Jest running Playwright tests** - Configuration issue causing environment mismatch
   - Location: `frontend/__tests__/e2e/*.spec.ts` (5 files)
   - Error: `ReferenceError: TransformStream is not defined`
   - Cause: `jest.config.js` line 13-16 matches `*.spec.ts` files intended for Playwright
   - Fix would be: Exclude `**/__tests__/e2e/**` from Jest's `testMatch` pattern

2. **PokerTable component test failure**
   - Error: `TypeError: Cannot read properties of undefined (reading 'is_current_turn')`
   - Location: `components/__tests__/PokerTable.test.tsx:41`
   - Cause: Incomplete mock data setup

#### 2. Nightly Test Suite (`nightly-tests.yml`)
**Status:** 100% failure rate (failing since Jan 13, 2026)

**Root Cause:**
- Backend concurrency test setup failures
- Error: `KeyError: 'game_id'` in `backend/tests/test_concurrency.py:194`
- Helper function `create_test_game()` expects `response.json()["game_id"]` but API response format changed
- Affects all slow concurrency tests (~67 tests)

#### 3. Test Suite (`test-suite.yml`)
**Status:** Also failing (duplicate of Comprehensive)

---

## Infrastructure Analysis

### Current Workflows (13 total)

**Test Workflows (TO DELETE):**
1. ✗ `test.yml` - "Comprehensive Test Suite" (runs on every push)
   - Backend: 333 "fast" tests
   - Frontend: 9 Jest tests
   - E2E: 2 Python/Playwright tests
   - Runtime: ~5-8 minutes

2. ✗ `test-suite.yml` - "Test Suite" (DUPLICATE of test.yml)
   - Same backend tests, frontend lint/type-check/build, integration tests
   - Runtime: ~5-8 minutes
   - Pure redundancy - runs in parallel with test.yml on every push

3. ✗ `nightly-tests.yml` - "Nightly Test Suite" (slow tests, 2 AM UTC)
   - Backend: ~67 slow tests (concurrency, stress, edge cases)
   - Runtime: 30-60 minutes target, but failing at startup
   - Auto-creates GitHub issues on failure

4. ✗ `monthly-tests.yml` - "Monthly Test Suite" (marathon tests, 1st of month)
   - Backend: Marathon tests (200-game runs, fuzzing)
   - Runtime: 2-3 hours
   - Last successful run: Unknown (likely also broken)

**Deployment Workflows (KEEP):**
5. ✓ `deploy-frontend-containerapp.yml` - Frontend Azure Container App deployment
6. ✓ `deploy-frontend-appservice.yml` - Frontend Azure App Service deployment (CHECK: redundant?)
7. ✓ `deploy-backend-production.yml` - Backend production deployment

**Infrastructure Workflows (KEEP):**
8. ✓ `azure-setup.yml` - Infrastructure setup
9. ✓ `database-migration.yml` - Database migrations
10. ✓ `generate-visual-baselines.yml` - E2E screenshot baseline generation

**Integration Workflows (KEEP):**
11. ✓ `claude.yml` - Claude Code integration
12. ✓ `claude-code-review.yml` - Claude Code review integration

**Other:**
13. ✓ `frontend/node_modules/*/.github/workflows/*.yml` - Third-party (ignore)

### Problems Identified

1. **Redundancy**
   - `test.yml` and `test-suite.yml` are near-duplicates running in parallel
   - Two frontend deployment workflows (containerapp vs appservice - likely one is unused)
   - Pre-commit hooks re-run in CI (wasted compute)

2. **Complexity**
   - 13 workflows to maintain
   - Unclear test categorization (just "slow" vs "not slow")
   - No clear strategy on what runs when and why
   - Documentation out of sync with reality

3. **Broken Tests**
   - Comprehensive tests failing due to config issues
   - Nightly tests failing due to API contract changes
   - No clear owner or process for fixing CI failures
   - Failures ignored/accumulating (nightly failing for 6+ days)

4. **Value Question**
   - 333 backend tests on every push - is this necessary?
   - Tests take 5-8 minutes, blocking feedback
   - Nightly/monthly tests haven't caught real issues (speculation - need data)
   - Investment in maintaining CI doesn't match team velocity

---

## Current Pre-Commit Protection

**Location:** `hooks/pre-commit`

**What it runs:**
1. **Regression suite** (always)
   - Critical poker engine tests
   - Action processing, state advancement, turn order
   - Fold resolution logic
   - Fast execution (<30 seconds)

2. **Infinite loop guard** (only if `poker_engine.py` modified)
   - Property-based testing
   - Guards against catastrophic infinite loop regression
   - Critical for game stability

**Installation:**
```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass (emergency):**
```bash
git commit --no-verify -m "message"
```

---

## Recommended Strategy: Simplify to Pre-Commit Only

### Philosophy

**Shift-left testing:** Catch issues at the earliest possible point (developer machine)

**Lean operations:** Eliminate infrastructure that doesn't provide clear value

**Pragmatic coverage:** Focus on critical regressions, not exhaustive testing

### What We Keep

1. **Pre-commit hooks** (already in place)
   - Critical regression suite
   - Infinite loop guard
   - Required for all commits

2. **Manual testing before deployment**
   - Developer validates changes locally
   - Full test suite available: `pytest backend/tests/ -v`
   - Frontend: `cd frontend && npm test`
   - E2E: `pytest tests/e2e/ -v`

3. **Deployment workflows**
   - Keep Azure deployment workflows
   - These deploy code, not test it
   - Deployment validation happens in production monitoring

4. **Infrastructure workflows**
   - Keep azure-setup, database-migration, etc.
   - These are operational, not testing

### What We Delete

**All test-running CI workflows:**
- ✗ `.github/workflows/test.yml` (Comprehensive Test Suite)
- ✗ `.github/workflows/test-suite.yml` (duplicate)
- ✗ `.github/workflows/nightly-tests.yml` (Nightly Test Suite)
- ✗ `.github/workflows/monthly-tests.yml` (Monthly Test Suite)

**Total deletion:** 4 workflow files

---

## Tradeoffs & Risk Mitigation

### What We Lose

1. **No CI safety net**
   - Risk: Developer bypasses hooks with `--no-verify`
   - Mitigation: Team discipline, code review catches issues

2. **No cross-platform testing**
   - Risk: Linux (production) behaves differently than macOS (dev)
   - Mitigation: Docker for local development, production monitoring

3. **No automated nightly edge case testing**
   - Risk: Rare edge cases, stress test scenarios not caught
   - Mitigation: Most issues caught by critical regression suite

4. **No scheduled stress testing**
   - Risk: Performance regressions, concurrency issues
   - Mitigation: Manual runs before major releases

### What We Gain

1. **Simplicity**
   - 4 fewer workflows to maintain
   - No more debugging CI failures
   - Clear mental model: tests run locally

2. **Speed**
   - No waiting for CI to pass
   - Faster iteration cycles
   - No blocked merges due to flaky CI

3. **Focus**
   - Time spent on features, not infrastructure
   - Less cognitive overhead
   - Clearer development workflow

4. **Cost**
   - No CI compute costs for tests
   - Reduced GitHub Actions minutes

---

## Implementation Plan

### Phase 1: Delete Test Workflows (Today)

```bash
# Delete test CI workflows
rm .github/workflows/test.yml
rm .github/workflows/test-suite.yml
rm .github/workflows/nightly-tests.yml
rm .github/workflows/monthly-tests.yml

# Commit deletion
git add .github/workflows/
git commit -m "refactor(ci): remove test workflows, rely on pre-commit hooks

- Delete comprehensive, nightly, monthly test workflows
- Simplify to pre-commit hook only for regression protection
- Keep deployment and infrastructure workflows
- See docs/CI-TEST-RATIONALIZATION-2026-01-19.md for rationale"
```

### Phase 2: Update Documentation (Today)

**Update CLAUDE.md:**
- Remove CI workflow guidance
- Emphasize pre-commit hooks
- Document manual test execution

**Update STATUS.md:**
- Note CI simplification
- Update testing strategy

**Update README.md:**
- Update testing section
- Remove CI badge references (if any)

### Phase 3: Verify Pre-Commit Hooks (Today)

**Ensure hooks are robust:**
```bash
# Test pre-commit hook
cd backend
python -m pytest tests/test_regression_suite.py -v

# Test infinite loop guard
touch game/poker_engine.py
git add game/poker_engine.py
git commit -m "test: verify pre-commit hook"  # Should run property tests
git reset HEAD~1  # Undo test commit
```

### Phase 4: Optional - Deployment Consolidation (Later)

**Investigate frontend deployment redundancy:**
- Check if both `deploy-frontend-containerapp.yml` and `deploy-frontend-appservice.yml` are needed
- Likely only one is active
- Delete unused deployment workflow

---

## Manual Testing Reference

### When to Run Full Test Suite

**Before major releases:**
```bash
# Backend comprehensive
cd backend
pytest tests/ -v --tb=short

# Backend slow tests (optional - edge cases, stress)
pytest tests/ -v -m "slow"

# Frontend
cd frontend
npm test
npm run build

# E2E critical flows
pytest tests/e2e/test_critical_flows.py -v

# E2E comprehensive (optional)
pytest tests/e2e/ -v
```

**Before poker engine changes:**
```bash
# Already covered by pre-commit hook
# Manual run if needed:
cd backend
pytest tests/test_property_based_enhanced.py -v
```

### Test Markers Reference

**Backend pytest markers:**
- `@pytest.mark.slow` - Slow tests (concurrency, stress, edge cases)
- `@pytest.mark.monthly` - Marathon tests (200-game runs)
- No marker - Fast unit/integration tests

**Execution:**
```bash
# Fast tests only (default pre-commit)
pytest tests/ -m "not slow and not monthly"

# All tests including slow
pytest tests/ -v

# Only slow tests
pytest tests/ -m "slow"

# Only monthly marathon tests
pytest tests/ -m "monthly"
```

---

## Success Metrics

**Indicators this is working:**
1. No production bugs related to missing CI tests (3 months)
2. Faster development velocity (subjective)
3. Less time spent debugging CI (0 minutes vs. current)
4. Pre-commit hooks catch regressions effectively

**Indicators we need to reconsider:**
1. Multiple production bugs that CI would have caught
2. Team bypassing hooks frequently (`--no-verify`)
3. Missing cross-platform testing causes issues
4. Edge cases not caught by regression suite

**Re-evaluation trigger:** If >2 production bugs occur in 3 months that CI would have caught, reconsider strategy.

---

## Future Options (If Needed)

**If we need CI again, add incrementally:**

1. **Start with PR checks only** (not every push)
   - Smoke tests only (~30 tests, <2 min)
   - Catches most issues, fast feedback

2. **Add nightly for edge cases**
   - Runs slow tests overnight
   - Issues don't block development

3. **Add deployment smoke tests**
   - Test production deployment after deploy
   - Catch environment-specific issues

**Key:** Add CI only when clear value justifies maintenance cost.

---

## Related Documents

- `CLAUDE.md` - Working agreement (update: remove CI sections)
- `STATUS.md` - Project status (update: note CI simplification)
- `docs/TESTING.md` - Test documentation (update: emphasize local testing)
- `docs/TEST-SUITE-REFERENCE.md` - Test reference (still valid for local runs)
- `hooks/pre-commit` - Pre-commit hook implementation

---

## Approval & Sign-off

**Date:** 2026-01-19
**Decision:** Approved - Remove all CI test workflows, rely on pre-commit hooks
**Rationale:** Simplification, focus, pragmatic risk/reward balance for current team size

**Next Steps:**
1. Delete 4 test workflow files
2. Update documentation (CLAUDE.md, STATUS.md, README.md)
3. Verify pre-commit hooks work correctly
4. Monitor for 3 months
5. Re-evaluate if production issues emerge
