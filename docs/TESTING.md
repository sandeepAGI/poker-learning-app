# Testing Documentation

> **Purpose:** Central hub for test-related documentation
> **Last Updated:** January 12, 2026

## Active Documentation

### 📋 [TEST-SUITE-REFERENCE.md](TEST-SUITE-REFERENCE.md)
Complete reference for all test suites (backend, frontend, E2E, CI/CD). Use this to understand what tests exist and how to run them.

### ✅ [TEST-CODE-REVIEW-GUIDE.md](TEST-CODE-REVIEW-GUIDE.md)
Standards for reviewing test code quality. Use this checklist when reviewing test PRs.

### 🏗️ [frontend-testing-enhancement-plan.md](frontend-testing-enhancement-plan.md)
TDD execution plan for frontend tests (Phases 0-4, currently 48% complete).

## Historical Documentation

### 📚 [TESTING-GAP-ANALYSIS-DEC2025.md](../archive/docs/TESTING-GAP-ANALYSIS-DEC2025.md)
Historical gap analysis from December 2025 that led to test suite optimization work.

### 📝 [test-suite-optimization-plan.md](../archive/2026-planning/test-suite-optimization-plan.md)
Completed 4-phase optimization plan (archived January 2026).

### 📊 [TDD-EXECUTION-LOG.md](../archive/execution-logs/TDD-EXECUTION-LOG.md)
Execution log showing completion of all 4 optimization phases.

## Pending Test Work

### High Priority
- [ ] **Smoke Test Suite** (`tests/e2e/test_smoke.py`) - 3 critical tests (3 min runtime)
- [ ] **Contract Test Suite** (`tests/integration/test_contracts.py`) - Backend/frontend contracts
- [ ] **Data Accuracy Tests** (`tests/e2e/test_data_accuracy.py`) - Verify UI matches backend
- [ ] **Frontend Component Tests** - 16 React component tests (see frontend-testing-enhancement-plan.md)

### Medium Priority
- [ ] **E2E Assertion Improvements** - Verify correctness, not just presence
- [ ] **Visual Regression with OCR** - Screenshot comparison with tolerance
- [ ] **Test Suite Reorganization** - Organize into smoke/, unit/, integration/, e2e/, performance/

### Reference
For detailed descriptions of pending work, see:
- Archive: `archive/docs/TESTING-GAP-ANALYSIS-DEC2025.md` (lines 310-636)
- Active plan: `frontend-testing-enhancement-plan.md`

## Test Strategy Summary

**Current Status:**
- ✅ Backend: 333+ tests, comprehensive coverage
- ✅ E2E: 21 tests covering critical flows
- ⚠️ Frontend: 9 tests (minimal component coverage)
- ✅ CI: Fast tests (<30 min) + Nightly slow tests

**Key Principles:**
1. **Fast tests in CI** - Use `@pytest.mark.slow` for expensive tests
2. **Meaningful assertions** - Verify correctness, not just "no crash"
3. **Poker-specific patterns** - See TEST-CODE-REVIEW-GUIDE.md
4. **Test isolation** - No shared state, can run in parallel

## Running Tests

**Backend:**
```bash
# All fast tests (CI)
PYTHONPATH=backend pytest backend/tests/ -m "not slow"

# All tests including slow
PYTHONPATH=backend pytest backend/tests/
```

**Frontend:**
```bash
cd frontend
npm test                    # Jest unit tests
npm run test:e2e           # Playwright E2E tests
```

**Full CI simulation:**
```bash
# See .github/workflows/test.yml
```

---

**For more details:** See [TEST-SUITE-REFERENCE.md](TEST-SUITE-REFERENCE.md)
