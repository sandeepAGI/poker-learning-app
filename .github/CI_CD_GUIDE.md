# CI/CD Infrastructure Guide

**Phase 6**: Automated Testing Pipeline
**Status**: ✅ COMPLETE
**Date**: December 10, 2025

---

## Overview

Automated testing infrastructure ensures code quality on every commit and pull request.

**Components**:
1. **Pre-commit hooks** - Fast local tests before committing
2. **GitHub Actions workflows** - Comprehensive CI/CD pipeline
3. **Coverage tracking** - Code coverage reports and enforcement

---

## 1. Pre-Commit Hooks

### What It Does
Runs fast regression tests (<1 second) before allowing git commits.

### Location
`.git/hooks/pre-commit`

### Tests Run
- `test_action_processing.py` (20 tests)
- `test_state_advancement.py` (13 tests)
- `test_turn_order.py` (3 tests)
- `test_fold_resolution.py` (2 tests)

**Total**: 41 tests in ~0.2 seconds

### How to Use

```bash
# Automatic - runs on every commit
git commit -m "Your message"

# Skip if needed (use sparingly!)
git commit -m "Your message" --no-verify
```

### Manual Test

```bash
.git/hooks/pre-commit
```

---

## 2. GitHub Actions Workflows

### 2.1 Full Test Suite (`test.yml`)

**Triggers**: Push to main/develop, Pull Requests
**Runtime**: ~27 minutes
**Jobs**:

#### Job 1: Backend Tests (22 min)
- Phase 1-3 tests (23 tests)
- Critical poker logic tests (35 tests) - **NEW**
- Phase 4 scenario tests (12 tests)
- Core regression tests (11 tests)
- Coverage report generation

#### Job 2: Frontend Build (2 min)
- npm install
- npm run build
- Build validation

#### Job 3: E2E Tests (2.5 min)
- Start backend + frontend servers
- Run Phase 5 E2E tests (13 tests)
- Screenshot capture on failure

#### Job 4: Test Summary
- Aggregate results from all jobs
- Display pass/fail status
- Generate GitHub summary

**Critical Poker Logic Tests (35 tests):**
- test_side_pots.py (4 tests) - side pot distribution
- test_all_in_scenarios.py (10 tests) - all-in edge cases
- test_bb_option.py (4 tests) - Big Blind option rule
- test_raise_validation.py (4 tests) - minimum raise enforcement
- test_heads_up.py (13 tests) - 2-player special rules

**Total**: 81 backend tests + 21 E2E = 102 tests across all phases

### 2.2 Quick Tests (`quick-tests.yml`)

**Triggers**: Pull Requests only
**Runtime**: ~1 minute
**Tests**:
- Core regression (41 tests)
- Negative testing (12 tests)

**Purpose**: Fast feedback loop for PR reviews

---

## 3. Coverage Tracking

### Configuration
File: `pytest.ini`

```ini
[coverage:run]
source = backend/game,backend/main.py,backend/websocket_manager.py

[coverage:report]
precision = 2
show_missing = True
```

### Generate Coverage Locally

```bash
# Generate HTML report
PYTHONPATH=backend python -m pytest backend/tests/ \
  --cov=backend/game \
  --cov=backend/main \
  --cov-report=html \
  --cov-report=term-missing

# Open report
open htmlcov/index.html
```

### Coverage Enforcement

```bash
# Fail if coverage below 80%
PYTHONPATH=backend python -m pytest backend/tests/ \
  --cov=backend/game \
  --cov-fail-under=80
```

### GitHub Integration
Coverage reports are uploaded to Codecov on each CI run.

---

## 4. Workflow Files

### `.github/workflows/test.yml`
Comprehensive test suite for all commits and PRs.

**Key Features**:
- Runs all 49 tests
- Generates coverage reports
- Uploads E2E screenshots on failure
- Creates test summary in PR comments

### `.github/workflows/quick-tests.yml`
Fast regression tests for PR validation.

**Key Features**:
- Runs in <1 minute
- Core tests only
- Quick feedback for reviewers

---

## 5. Local Development Workflow

### Before Committing
Pre-commit hook runs automatically (41 tests, ~0.2s)

### Manual Full Test Suite

```bash
# Phase 1-3 (fast - 48s)
PYTHONPATH=backend python -m pytest \
  backend/tests/test_negative_actions.py \
  backend/tests/test_hand_evaluator_validation.py \
  backend/tests/test_property_based_enhanced.py -v

# Phase 4 (slow - 19 min)
PYTHONPATH=backend python -m pytest \
  backend/tests/test_user_scenarios.py -v

# Phase 5 (requires servers - 2.5 min)
# Terminal 1: python backend/main.py
# Terminal 2: cd frontend && npm run dev
# Terminal 3:
PYTHONPATH=. python -m pytest tests/e2e/test_critical_flows.py -v
```

### Frontend Build Check

```bash
cd frontend
npm run build
```

---

## 6. GitHub Actions Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/poker-learning-app/workflows/Comprehensive%20Test%20Suite/badge.svg)
![Quick Tests](https://github.com/YOUR_USERNAME/poker-learning-app/workflows/Quick%20Tests%20(PR)/badge.svg)
```

---

## 7. Troubleshooting

### Pre-commit hook not running
```bash
# Ensure hook is executable
chmod +x .git/hooks/pre-commit

# Verify it works
.git/hooks/pre-commit
```

### GitHub Actions failing
1. Check the Actions tab in GitHub
2. Review failed job logs
3. Run tests locally to reproduce
4. Fix issues and push again

### Coverage report missing
```bash
# Install coverage package
pip install pytest-cov

# Generate report
PYTHONPATH=backend python -m pytest backend/tests/ --cov=backend/game
```

---

## 8. Best Practices

### Commit Frequency
- Commit often with small, focused changes
- Pre-commit hook keeps commits clean
- Each commit passes basic tests

### Pull Request Workflow
1. Create feature branch
2. Make changes
3. Pre-commit hook validates on each commit
4. Push to GitHub
5. Quick Tests run automatically
6. Full Test Suite runs on PR creation
7. Review CI results before merging

### Test Failures
- **Pre-commit fails**: Fix immediately before committing
- **Quick tests fail**: Fix before requesting review
- **Full tests fail**: Investigate and fix before merging

---

## 9. Phase 6 Deliverables

✅ **Completed**:
1. Pre-commit hook (41 tests, <1s)
2. GitHub Actions workflows (2 files)
3. Coverage configuration (pytest.ini)
4. CI/CD documentation (this file)

**Test Coverage**:
- All 49 tests run in CI
- Coverage reports generated
- E2E tests include screenshot capture
- Automated summary generation

**Time Saved**:
- Pre-commit: Catches issues in <1s
- Quick Tests: PR feedback in 1 min
- Full Suite: Comprehensive validation in 25 min
- **Result**: No broken code reaches main branch

---

## 10. Next Steps (Phase 7+)

- **Phase 7**: WebSocket reconnection testing
- **Phase 8**: Concurrency & race condition testing
- **Phase 9**: RNG fairness testing
- **Phase 10**: Load & stress testing
- **Phase 11**: Network failure simulation

---

**Questions?** See [STATUS.md](../STATUS.md) for overall project status.
