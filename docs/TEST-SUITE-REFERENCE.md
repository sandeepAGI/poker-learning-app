# Test Suite Reference

**Last Updated:** 2026-01-12
**Status:** ✅ All test suites operational

This document provides a comprehensive reference for all testing infrastructure in the Poker Learning App.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Backend Test Suites](#backend-test-suites)
3. [Frontend Test Suites](#frontend-test-suites)
4. [E2E Test Suites](#e2e-test-suites)
5. [CI/CD Integration](#cicd-integration)
6. [How to Run Tests](#how-to-run-tests)
7. [Test Coverage Summary](#test-coverage-summary)

---

## Quick Reference

| Test Suite | Location | Command | Runtime | Local/CI |
|------------|----------|---------|---------|----------|
| **Backend Unit/Integration** | `backend/tests/` | `PYTHONPATH=backend pytest backend/tests/ -v` | ~2-3 min | Both |
| **Backend Stress Tests** | `backend/tests/test_stress_*.py` | `pytest backend/tests/test_stress_*.py -v` | ~7-10 min | CI Only (Nightly) |
| **Frontend Component Tests** | `frontend/__tests__/` | `cd frontend && npm test` | <30s | Both |
| **E2E Functional Tests** | `tests/e2e/test_short_stack.spec.ts` | `npm run test:e2e` | ~2-3 min | Both |
| **E2E Visual Regression** | `tests/e2e/test_visual_regression.spec.ts` | `npx playwright test test_visual_regression` | ~1-2 min | CI Only (Nightly) |
| **Full Test Suite** | All tests | GitHub Actions trigger | ~8-10 min | CI |

---

## Backend Test Suites

### Location
`backend/tests/` (60 test files, 200+ test cases)

### What It Tests
- **Core Game Logic**: Poker rules, hand evaluation, betting rounds, state transitions
- **AI Opponents**: Strategy classes, decision-making, SPR calculations
- **WebSocket Communication**: Real-time game updates, connection handling, reliability
- **API Endpoints**: REST API, game creation, state retrieval
- **Edge Cases**: Side pots, all-in scenarios, fold resolution, split pots
- **Performance**: Concurrency, stress tests, RNG fairness
- **Bug Regressions**: Fixed bugs from previous issues

### Key Test Files

#### Core Logic Tests
- `test_complete_game.py` - Full game simulation end-to-end
- `test_hand_evaluator_validation.py` - Hand ranking logic (17k lines)
- `test_property_based_enhanced.py` - Property-based testing (16k lines)
  - **⚠️ CRITICAL**: Run before modifying `poker_engine.py` (guards infinite loop regression)
- `test_negative_actions.py` - Invalid action handling (24k lines)
- `test_user_scenarios.py` - Real-world scenarios (24k lines)

#### State Management Tests
- `test_action_processing.py` - Action processing logic
- `test_state_advancement.py` - Game state transitions
- `test_fold_resolution.py` - Fold handling
- `test_all_in_scenarios.py` - All-in situations (16k lines)
- `test_side_pots.py` - Side pot calculations

#### AI Tests
- `test_ai_only_games.py` - AI vs AI games
- `test_ai_personalities.py` - AI personality behavior
- `test_ai_spr_decisions.py` - AI SPR-based decisions
- `test_hand_strength.py` - Hand strength evaluation

#### WebSocket Tests
- `test_websocket_integration.py` - WebSocket messaging (17k lines)
- `test_websocket_flow.py` - WebSocket game flow (20k lines)
- `test_websocket_reliability.py` - Reliability testing (18k lines)
- `test_network_resilience.py` - Network failure handling (16k lines)

#### Performance/Stress Tests
- `test_stress_ai_games.py` - AI stress testing (17k lines, 200 games)
- `test_performance.py` - Performance benchmarks (15k lines)
- `test_concurrency.py` - Concurrent game handling (25k lines)
- `test_action_fuzzing.py` - Fuzzing attacks (16k lines)
- `test_rng_fairness.py` - RNG statistical tests (14k lines)

### Where It Runs
- **Local**: All tests except stress tests
- **CI**:
  - Unit/integration tests run on every push/PR
  - Stress tests run nightly (scheduled at 2 AM UTC)

### How to Run

```bash
# All backend tests (quick suite)
PYTHONPATH=backend pytest backend/tests/ -v

# Specific test file
PYTHONPATH=backend pytest backend/tests/test_complete_game.py -v

# With coverage
PYTHONPATH=backend pytest backend/tests/ --cov=backend --cov-report=html

# Stress tests only (slow)
PYTHONPATH=backend pytest backend/tests/test_stress_ai_games.py -v

# Property-based tests (critical before poker_engine.py changes)
PYTHONPATH=backend pytest backend/tests/test_property_based_enhanced.py -v
```

### Test Results
- **Status**: ✅ 41/41 passing (quick suite)
- **Coverage**: High (core logic, game engine, WebSocket)
- **Runtime**: ~2-3 minutes (quick suite), ~180 minutes (nightly with stress tests)

---

## Frontend Test Suites

### Location
`frontend/__tests__/` (1 test file, 9 test cases)

### What It Tests
- **Short-Stack Logic**: Pure logic functions for handling short-stack scenarios
  - All-in call amount calculations
  - All-in raise amount calculations
  - Button label generation
  - Edge cases for insufficient chips

### Key Test Files
- `short-stack-logic.test.ts` - Short-stack utility functions

### Testing Infrastructure
- **Framework**: Jest 29.7.0
- **Environment**: jsdom (simulated browser)
- **Test Runner**: Next.js Jest integration
- **Config**: `frontend/jest.config.js`
- **Setup**: `frontend/jest.setup.js` (global mocks)

### Mocks Available
- `window.matchMedia` - Media query support
- `localStorage` - Browser storage
- `WebSocket` - WebSocket connections (prevents real connections)

### Where It Runs
- **Local**: Yes (`npm test` in frontend/)
- **CI**: Yes (runs on every push/PR via Frontend Tests workflow)

### How to Run

```bash
cd frontend

# Run all tests
npm test

# Watch mode (re-run on file changes)
npm run test:watch

# With coverage report
npm run test:coverage

# CI mode (no watch, with coverage)
npm run test:ci
```

### Test Results
- **Status**: ✅ 9/9 passing
- **Coverage**: 0% (tests pure logic, doesn't import components)
  - Note: Coverage thresholds disabled until component tests are added
- **Runtime**: <30 seconds

### Future Expansion
The infrastructure is ready for:
- React component tests with React Testing Library v16.3.1
- Store (Zustand) state management tests
- Hook testing
- Component integration tests

---

## E2E Test Suites

### Location
`tests/e2e/` (2 test files, 6 test cases)

### What It Tests

#### 1. Functional Tests (`test_short_stack.spec.ts`)
- **Purpose**: Verify short-stack UI scenarios work correctly
- **Coverage**:
  - Call all-in when stack < call amount
  - Raise all-in when stack < min raise
  - Correct button labels for short stacks
- **Components Tested**:
  - Call button behavior
  - Raise panel and all-in button
  - Button label text
  - Game state manipulation via test endpoint

#### 2. Visual Regression Tests (`test_visual_regression.spec.ts`)
- **Purpose**: Ensure UI renders consistently across changes
- **Coverage**:
  - Home page layout
  - Poker table layout
  - Action buttons rendering
- **Components Tested**:
  - Full page screenshots
  - Component-level screenshots
  - Visual consistency over time

### Testing Infrastructure
- **Framework**: Playwright 1.57.0
- **Browser**: Chromium (Desktop Chrome)
- **Config**: `playwright.config.ts` (root level)
- **Test Server**: Automatically starts backend + frontend
- **Test Endpoint**: Backend `/test/*` endpoints (only active when `TEST_MODE=1`)

### Backend Test Endpoints
Available when `TEST_MODE=1`:
- `POST /test/set_game_state` - Manipulate game state for testing
- `GET /test/health` - Health check for E2E tests
- `GET /test/games/{game_id}` - Get full game state for debugging

**⚠️ Security**: Test endpoints only enabled when `TEST_MODE=1` environment variable is set. NEVER deploy to production with `TEST_MODE=1`.

### Where It Runs
- **Local**: Yes (requires both backend and frontend running)
- **CI**:
  - Functional tests: Run on every push/PR
  - Visual regression tests: Run nightly (scheduled at 2 AM UTC)

### How to Run

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run with browser visible
npm run test:e2e:headed

# Run specific test file
npx playwright test test_short_stack.spec.ts

# Run only visual regression tests
npx playwright test test_visual_regression.spec.ts

# Debug mode (step through tests)
npm run test:e2e:debug

# Update visual baselines (after intentional UI changes)
npx playwright test --update-snapshots
```

### Test Results
- **Status**: ✅ 6/6 passing
- **Functional Tests**: 3/3 passing
- **Visual Tests**: 3/3 passing (baselines generated)
- **Runtime**: ~2-3 minutes (functional), ~1-2 minutes (visual)

### Visual Regression Baselines
- **Location**: `tests/e2e/test_visual_regression.spec.ts-snapshots/`
- **Platform**: Generated on macOS (darwin), verified on ubuntu-latest in CI
- **Tolerance**:
  - Home page: 100 pixels max diff
  - Poker table: 2000 pixels max diff (card animations cause variations)
  - Action buttons: 50 pixels max diff

---

## CI/CD Integration

### Workflows

#### 1. Frontend Tests (`.github/workflows/frontend-tests.yml`)
- **Trigger**: Every push to main, every PR
- **Runtime**: ~38 seconds
- **Jobs**:
  - **Component Tests**: Run Jest tests with coverage collection
  - **Build Verification**: Ensure production build succeeds

#### 2. Comprehensive Test Suite (`.github/workflows/comprehensive-test-suite.yml`)
- **Trigger**: Every push to main, every PR
- **Runtime**: ~8 minutes
- **Jobs**:
  - **Backend Tests**: All unit/integration tests (41 tests)
  - **Frontend Build**: Production build verification
  - **E2E Browser Tests**: Playwright functional tests (3 tests)
  - **Test Summary**: Aggregate results

#### 3. Nightly E2E & Visual Tests (`.github/workflows/nightly-e2e.yml`)
- **Trigger**: Nightly at 2 AM UTC, manual dispatch
- **Runtime**: ~30 minutes
- **Jobs**:
  - **E2E Tests**: All Playwright functional tests
  - **Visual Regression**: Screenshot comparison tests

#### 4. Nightly Stress Tests (`.github/workflows/nightly-stress-tests.yml`)
- **Trigger**: Nightly at 2 AM UTC, manual dispatch
- **Runtime**: ~180 minutes (3 hours)
- **Jobs**:
  - **Backend Stress Tests**: 200-game AI simulations, concurrency tests
  - **Performance Benchmarks**: RNG fairness, fuzzing tests

### Workflow Status
- **Frontend Tests**: ✅ Passing
- **Comprehensive Test Suite**: ✅ Passing
- **Nightly E2E & Visual**: Scheduled
- **Nightly Stress Tests**: Scheduled

### CI Test Commands

```bash
# Backend (in CI)
PYTHONPATH=backend pytest backend/tests/ -v --maxfail=5

# Frontend (in CI)
cd frontend && npm run test:ci

# E2E (in CI)
TEST_MODE=1 npm run test:e2e

# Build verification
cd frontend && npm run build
```

---

## How to Run Tests

### Local Development

#### Quick Test (Before Commit)
```bash
# 1. Run backend property-based tests (guards infinite loop bug)
PYTHONPATH=backend pytest backend/tests/test_property_based_enhanced.py -v

# 2. Run backend quick suite
PYTHONPATH=backend pytest backend/tests/ -v -k "not stress"

# 3. Run frontend tests
cd frontend && npm test

# Total time: ~3-4 minutes
```

#### Full Test Suite (Local)
```bash
# 1. Backend tests
PYTHONPATH=backend pytest backend/tests/ -v

# 2. Frontend tests
cd frontend && npm run test:coverage

# 3. E2E tests (requires backend + frontend running)
npm run test:e2e

# Total time: ~8-10 minutes
```

#### E2E Tests (Requires Setup)
```bash
# Terminal 1: Start backend with test mode
cd backend
TEST_MODE=1 python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run E2E tests
npm run test:e2e

# OR: Let Playwright start servers automatically
npm run test:e2e  # Uses reuseExistingServer: true
```

### CI/CD

#### Automatic Runs
- **On Push/PR**: Frontend tests, backend tests, E2E functional tests
- **Nightly**: Visual regression tests, stress tests, performance benchmarks

#### Manual Trigger
```bash
# Trigger nightly E2E tests manually
gh workflow run nightly-e2e.yml

# Trigger stress tests manually
gh workflow run nightly-stress-tests.yml

# View recent runs
gh run list --limit 10

# View specific run details
gh run view <run-id>

# Watch live run
gh run watch
```

---

## Test Coverage Summary

### Backend Coverage
| Category | Test Files | Test Cases | Coverage | Runtime |
|----------|-----------|------------|----------|---------|
| **Core Logic** | 15 files | ~80 tests | High | 1-2 min |
| **State Management** | 8 files | ~40 tests | High | 30-60s |
| **AI/Strategy** | 6 files | ~30 tests | High | 30-60s |
| **WebSocket** | 8 files | ~40 tests | High | 1-2 min |
| **Performance** | 5 files | ~20 tests | Medium | 3+ hours (stress) |
| **API/Integration** | 8 files | ~30 tests | High | 30-60s |
| **Bug Regression** | 10 files | ~40 tests | High | 1-2 min |
| **TOTAL** | **60 files** | **~280 tests** | **High** | **~180 min** |

### Frontend Coverage
| Category | Test Files | Test Cases | Coverage | Runtime |
|----------|-----------|------------|----------|---------|
| **Logic Tests** | 1 file | 9 tests | 100% (logic) | <30s |
| **Component Tests** | 0 files | 0 tests | 0% | N/A |
| **TOTAL** | **1 file** | **9 tests** | **0%** | **<30s** |

**Note**: Frontend coverage at 0% because tests only cover pure logic functions, not React components. Infrastructure is ready for component tests.

### E2E Coverage
| Category | Test Files | Test Cases | Coverage | Runtime |
|----------|-----------|------------|----------|---------|
| **Functional** | 1 file | 3 tests | Critical flows | 2-3 min |
| **Visual Regression** | 1 file | 3 tests | Key UI components | 1-2 min |
| **TOTAL** | **2 files** | **6 tests** | **Medium** | **3-5 min** |

### Overall Test Metrics
- **Total Test Files**: 63 files
- **Total Test Cases**: ~295 tests
- **Quick Suite Runtime**: ~3-4 minutes
- **Full Suite Runtime**: ~8-10 minutes (without stress tests)
- **Full Suite + Stress**: ~180 minutes (3 hours)
- **CI Success Rate**: 100% (all workflows passing)

---

## Test Infrastructure Components

### Backend Testing Stack
- **Framework**: pytest 7.4.x
- **Assertions**: pytest assertions + custom game state validators
- **Mocking**: unittest.mock, pytest fixtures
- **Test Server**: FastAPI TestClient
- **WebSocket Testing**: Custom WebSocket test client
- **Property Testing**: Hypothesis (in property-based tests)

### Frontend Testing Stack
- **Framework**: Jest 29.7.0
- **Test Library**: React Testing Library 16.3.1 (React 19 compatible)
- **Environment**: jsdom
- **Mocking**: jest.fn(), global mocks in jest.setup.js
- **Test Utils**: Custom utilities in `__tests__/utils/test-utils.tsx`

### E2E Testing Stack
- **Framework**: Playwright 1.57.0
- **Browser**: Chromium (Desktop Chrome)
- **Visual Regression**: Playwright screenshot comparison
- **Test Endpoint**: Backend `/test/*` endpoints with TEST_MODE guard
- **Server Management**: Automatic startup via playwright.config.ts

---

## Test Development Guidelines

### When to Add Tests

#### Backend
- **Before modifying `poker_engine.py`**: Run property-based tests first
- **New game features**: Add unit tests + integration tests
- **Bug fixes**: Add regression test that reproduces the bug
- **API changes**: Update contract tests

#### Frontend
- **New components**: Add React Testing Library tests
- **Logic functions**: Add Jest unit tests
- **UI changes**: Update visual regression baselines

#### E2E
- **New user flows**: Add Playwright functional tests
- **Critical features**: Add to smoke test suite
- **UI changes**: Update visual regression tests

### Test Naming Conventions
- **Backend**: `test_<feature>_<scenario>.py`
- **Frontend**: `<component>.test.tsx` or `<feature>.test.ts`
- **E2E**: `test_<feature>.spec.ts`

### Test Organization
- **Backend**: Organized by feature/component
- **Frontend**: `__tests__/` directory matching source structure
- **E2E**: Root-level `tests/e2e/` directory

---

## Known Limitations & Future Work

### Current Gaps
1. **Frontend Component Testing**: No React component tests yet (infrastructure ready)
2. **E2E Coverage**: Only short-stack scenarios covered, need more user flows
3. **Visual Regression**: Baselines may differ between macOS and Linux
4. **Backend Coverage**: Not measured (no coverage reporting configured)

### Planned Improvements
1. Add React component tests for critical UI components
2. Expand E2E coverage to more user flows (game creation, full hands, analysis)
3. Add contract tests between backend and frontend
4. Set up backend coverage reporting
5. Add smoke test suite for critical paths

---

## Troubleshooting

### Backend Tests Failing
```bash
# Check Python path is correct
echo $PYTHONPATH  # Should include backend/

# Run with verbose output
PYTHONPATH=backend pytest backend/tests/ -vv -s

# Run single test for debugging
PYTHONPATH=backend pytest backend/tests/test_complete_game.py::test_name -vv -s
```

### Frontend Tests Failing
```bash
# Clear Jest cache
cd frontend
npm test -- --clearCache

# Run with verbose output
npm test -- --verbose

# Check for module resolution issues
npm test -- --showConfig
```

### E2E Tests Failing
```bash
# Check servers are running
curl http://localhost:8000/health
curl http://localhost:3000

# Run with debug mode
npm run test:e2e:debug

# Check test mode is enabled
TEST_MODE=1 curl http://localhost:8000/test/health

# View Playwright trace
npx playwright show-trace trace.zip
```

### CI Tests Failing
```bash
# View recent runs
gh run list --limit 5

# View specific run details
gh run view <run-id>

# Download logs
gh run download <run-id>

# Check workflow file
cat .github/workflows/frontend-tests.yml
```

---

## Additional Resources

- **Testing Strategy**: `docs/TESTING.md` (gap analysis and recommendations)
- **Test Suite Optimization**: `docs/test-suite-optimization-plan.md`
- **Frontend Testing Plan**: `docs/frontend-testing-enhancement-plan.md`
- **TDD Execution Log**: `docs/TDD-EXECUTION-LOG.md`
- **Project Setup**: `docs/SETUP.md`
- **Documentation Index**: `docs/INDEX.md`

---

**Document Version**: 1.0
**Last Verified**: 2026-01-12
**Next Review**: After next major feature addition
