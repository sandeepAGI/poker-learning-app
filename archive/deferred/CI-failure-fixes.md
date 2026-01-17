# CI Failure Analysis & Remediation Plan

**Date**: 2026-01-12
**Status**: In Progress
**Author**: Multi-Agent Investigation (4 specialized agents)

---

## Executive Summary

Investigation of CI failures from Jan 10-12, 2026 revealed **5 distinct failures** during a major test infrastructure overhaul (30 commits, 16K+ lines in 3 days).

**Key Finding**: Most failures were preventable test infrastructure issues, not production bugs. However, the analysis uncovered a **process breakdown**: rapid development velocity without adequate validation allowed easily preventable failures to reach CI.

**Critical Issues**:
1. ❌ **Unfixed Bug**: Logic error in `test_performance.py` (player_index iteration)
2. ⚠️ **Uninvestigated**: Segmentation fault dismissed without proper analysis
3. ✅ **Fixed**: 3 test infrastructure issues (chip conservation, visual baselines, Jest coverage)

**Recommendation**: Pause new infrastructure work, fix critical issues, establish process safeguards, then resume with improved discipline.

---

## Investigation Summary

### Agent Findings

**Agent 1 (Commit Analysis)**: Reviewed 29 commits from Jan 10-12
- Major test suite optimization (Phases 0-4)
- Frontend test infrastructure: Jest, Playwright, visual regression
- Backend test expansion: 5 new gap test suites
- Documentation: 8,000+ new lines
- Pattern: Systematic phased approach, but very rapid execution

**Agent 2 (CI Failure Analysis)**: Analyzed GitHub Actions failures
- 6 failure instances between Jan 11 21:29 UTC - Jan 12 04:03 UTC
- Identified specific error messages and failure patterns
- Current status: 3/5 fixed, 2/5 require attention

**Agent 3 (Root Cause Analysis)**: Analyzed relationship between commits and failures
- Categorized failures by type (test infra vs real bugs)
- Assessed preventability for each failure
- Concluded: "Expected growing pains" of rapid infrastructure development

**Agent 4 (Senior Review)**: Critical review of Agent 3's analysis
- **Challenged** several findings as incomplete or incorrect
- Identified false claims (missing test files actually exist)
- Criticized segfault dismissal as "unacceptable"
- Concluded: **Process breakdown**, not just growing pains

---

## Detailed Failure Analysis

### Failure #1: Chip Conservation Bug ✅ FIXED
**Type**: Test Infrastructure (False Positive)
**Status**: Resolved (commit fe1121de)
**Location**: E2E tests triggering QC checks in poker_engine.py:726

**What Happened**:
- E2E tests created artificial game states to test UI rendering
- These states violated game-level invariants (e.g., $30 stack vs $80 bet)
- QC checks correctly detected violations and failed tests

**Root Cause**:
- Test endpoint added without `qc_enabled=False` flag
- Tests were checking UI logic, not poker correctness

**Fix Applied**:
```python
# backend/main.py - Test endpoint now disables QC checks
game.qc_enabled = False  # Tests create artificial states
```

**Prevention**: Test endpoints should explicitly disable validation when creating artificial states.

---

### Failure #2: Visual Baselines Missing ✅ FIXED
**Type**: Test Infrastructure (Platform Mismatch)
**Status**: Resolved (commit fe1121de)
**Location**: Visual regression tests

**What Happened**:
- Visual tests developed locally on macOS (darwin)
- Baselines generated with macOS Chromium rendering
- CI runs on Linux (ubuntu-latest) with different rendering
- Pixel-perfect comparisons failed

**Root Cause**:
- Platform-specific baselines committed (darwin PNGs)
- Linux CI expected Linux baselines
- Chromium renders differently across platforms (fonts, anti-aliasing)

**Fix Applied**:
1. Deleted darwin baseline PNGs
2. Created `generate-visual-baselines.yml` workflow
3. Generated Linux baselines in CI environment

**Prevention**: Visual regression baselines must always be generated in CI environment, not locally.

**Best Practice Violation**: Well-known Playwright issue documented in official docs.

---

### Failure #3: Performance Test TypeError ❌ NOT FIXED
**Type**: Logic Error in Test Code
**Status**: **REQUIRES IMMEDIATE FIX**
**Location**: `backend/tests/test_performance.py:367`

**What Happened**:
- Stress tests fail with `TypeError: '<' not supported between instances of 'NoneType' and 'int'`
- Error in `poker_engine.py:1160` at `apply_action()` method
- `player_index` parameter is `None` instead of integer

**Root Cause** (Agent 4's Finding):
```python
# backend/tests/test_performance.py:367 (BROKEN)
for player in game.players:
    if player.is_active and not player.has_acted:
        success = game.apply_action(
            game.current_player_index,  # WRONG - same index for all players!
            "call",
            0
        )
```

**Analysis**:
- Test iterates over ALL players
- Uses `game.current_player_index` for ALL of them (incorrect)
- Should iterate with proper player indices
- This is a **new bug introduced during infrastructure work**, not pre-existing

**Impact**:
- Test fails intermittently in stress scenarios
- Indicates insufficient code review for test changes
- Unknown if similar pattern exists elsewhere

**Agent 3 vs Agent 4 Disagreement**:
- Agent 3: "Pre-existing bug exposed by new tests"
- Agent 4: "Logic error in test code written during infrastructure work"
- **Agent 4 is correct** based on code review

---

### Failure #4: Jest Coverage Thresholds ✅ FIXED
**Type**: Test Infrastructure (Premature Enforcement)
**Status**: Resolved (commit 4789af7b)
**Location**: `frontend/jest.config.ts`

**What Happened**:
- Coverage thresholds set to 70% during infrastructure setup
- Actual coverage: 0% (only logic tests, no component tests yet)
- CI failed: 0% < 70%

**Root Cause**:
- Aspirational configuration added without validation
- Thresholds enforced before tests existed
- Configuration copied without adaptation

**Fix Applied**:
```javascript
// Coverage thresholds disabled until we have component tests
// Current tests are logic-only without component coverage
// coverageThreshold: { ... }  // Commented out
```

**Agent 4's Critique**: This indicates either copy-paste from another project or adding configuration without testing - both are process failures.

**Prevention**: Never add configuration that will fail without testing it first. Set coverage thresholds to current baseline + 5%, increase gradually.

---

### Failure #5: Segmentation Fault ⚠️ NOT INVESTIGATED
**Type**: Unknown (Potential Memory Corruption)
**Status**: **REQUIRES IMMEDIATE INVESTIGATION**
**Location**: Backend tests (cleanup phase)

**What Happened** (per user report):
- Intermittent segmentation fault during test cleanup
- Occurred after all tests passed
- Exit code 139 (SIGSEGV)

**Agent 3's Finding**: "No evidence found, possibly intermittent or misreported"

**Agent 4's Critique** (Grade: F):
> "Segfaults are NEVER 'misreported' - they're kernel signals (SIGSEGV). 'No evidence' doesn't mean it didn't happen - it means investigation was insufficient. This dismissal is UNACCEPTABLE."

**Potential Causes (Not Investigated)**:
1. `treys` library C extension crash (most likely)
2. Memory corruption in long-running stress tests
3. Threading issues in asyncio + WebSocket layer
4. Resource exhaustion during nightly runs

**Required Investigation**:
```bash
# Check core dumps
ls -la /cores/

# Run with debug malloc
PYTHONMALLOC=debug pytest backend/tests/test_stress_ai_games.py

# Enable fault handler
python -X faulthandler -m pytest backend/tests/test_stress_ai_games.py -v

# Check system logs
dmesg | grep -i segfault
```

**Severity**: Unknown until investigated, but potentially HIGH
- Could corrupt game state in production
- May indicate memory safety issue
- Could be exploitable security issue

---

## Critical Discovery: False Claims in Analysis

**Agent 4 identified factual errors in Agent 3's analysis:**

### Claim: "Missing Test Files"
**Agent 3 stated**: `test_performance.py` and `test_rng_fairness.py` are "missing" and referenced in workflow but don't exist.

**Agent 4 verification**:
```bash
$ find backend/tests -name "test_performance.py" -o -name "test_rng_fairness.py"
/Users/.../backend/tests/test_rng_fairness.py
/Users/.../backend/tests/test_performance.py
```

**Both files exist.** This false claim undermines the credibility of Agent 3's analysis.

**Implication**: If basic facts are wrong, what else in the analysis might be incorrect?

---

## Root Cause: Process Breakdown

### Agent 4's Critical Assessment

**The Real Issue**: Not the failures themselves, but the **process that allowed them to reach CI**.

**Evidence of Process Breakdown**:
1. **30 commits in 3 days** (avg 10/day) - too fast for quality
2. **16,000+ lines changed** - insufficient validation between commits
3. **4/5 failures preventable** with basic local testing
4. **Test code not reviewed** as rigorously as production code
5. **Configuration added without testing** (Jest coverage thresholds)

**Symptoms**:
- Velocity pressure (complete Phases 0-4 quickly)
- CI used as primary validation tool (not safety net)
- Test infrastructure changes not validated in isolation
- False confidence from "same-day fixes"

**Risk**: This pattern could continue without intervention.

---

## Phased Remediation Plan

### Phase 0: Planning & Documentation ✅
**Goal**: Create this document and establish execution framework

**Tasks**:
- [x] Document all findings from 4-agent investigation
- [x] Categorize failures by severity and status
- [x] Create phased implementation plan
- [x] Review with stakeholder (user approval received)

**Deliverable**: This document

---

### Phase 0.5: Test Suite Consolidation & Coverage (NEW - IMMEDIATE)
**Goal**: Simplify to 2 workflows and fix critical coverage gaps

**Timeline**: Today (1-2 hours)

**Rationale**:
- Current state: 5 workflows with redundancy and gaps
- Only 31% of backend tests run in CI
- User directive: "Comprehensive should be comprehensive, Nightly for slow tests only"

#### Proposed New Structure

**Workflow 1: Comprehensive Test Suite** (Per-commit, <10 minutes)
- ALL backend tests that run fast (<10 min total)
- ALL frontend tests (build + Jest)
- ALL fast E2E tests (critical flows, browser refresh)
- Visual regression (if <2 min)
- Target runtime: 8-10 minutes
- Runs on: Every push to main/develop, every PR

**Workflow 2: Nightly Test Suite** (Nightly, unlimited time)
- ONLY slow tests: stress tests (200-game AI marathon)
- ONLY slow tests: property-based fuzzing (1000 scenarios)
- ONLY slow tests: performance benchmarks
- Long-running E2E scenarios
- Concurrency and load tests
- Target runtime: 60-180 minutes
- Runs on: 2 AM UTC daily, manual dispatch

**Workflows to DELETE**:
- `quick-tests.yml` (redundant with comprehensive)
- `frontend-tests.yml` (merge into comprehensive)
- `nightly-e2e.yml` (merge fast E2E into comprehensive, slow into nightly)
- Keep: `generate-visual-baselines.yml` (manual utility)

---

#### Task 0.5.1: Audit Test Runtime
**Goal**: Categorize all 58 backend tests by runtime

**Process**:
1. Run each test file individually with timing
2. Categorize as:
   - **Fast** (<10 seconds) → Comprehensive
   - **Medium** (10-60 seconds) → Comprehensive
   - **Slow** (>60 seconds) → Nightly
3. Document findings

**Script**:
```bash
# Test all backend tests with timing
for test_file in backend/tests/test_*.py; do
    echo "Testing: $test_file"
    time PYTHONPATH=backend pytest "$test_file" -v --tb=short
done
```

**Deliverable**: List of all tests with runtimes

**Acceptance Criteria**:
- [ ] All 58 backend tests categorized by runtime
- [ ] Clear list of Fast vs Slow tests
- [ ] Total estimated runtime for Comprehensive (<10 min)

---

#### Task 0.5.2: Create New Comprehensive Workflow
**Goal**: Single comprehensive workflow with ALL fast tests

**File**: `.github/workflows/test.yml` (update existing)

**New Structure**:
```yaml
name: Comprehensive Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-timeout

      # Run ALL fast backend tests (auto-discovery)
      - name: Run all backend tests
        run: |
          PYTHONPATH=backend python -m pytest backend/tests/ \
            -v --tb=short \
            -m "not slow" \
            --timeout=60

  frontend-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run Jest tests
        run: cd frontend && npm test

      - name: Build frontend
        run: cd frontend && npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: |
          cd backend && pip install -r requirements.txt
          cd ../frontend && npm ci
          npx playwright install chromium

      - name: Start backend
        run: |
          cd backend
          python main.py &
          sleep 5

      - name: Start frontend
        run: |
          cd frontend
          npm run dev &
          sleep 10

      - name: Run E2E tests
        run: |
          PYTHONPATH=backend pytest tests/e2e/test_critical_flows.py -v
          PYTHONPATH=backend pytest tests/e2e/test_browser_refresh.py -v
          npx playwright test tests/e2e/test_visual_regression.spec.ts
```

**Key Changes**:
1. **Auto-discovery**: Use `pytest backend/tests/ -m "not slow"` instead of explicit file lists
2. **All jobs in one workflow**: Backend, frontend, E2E together
3. **Pytest markers**: Use `-m "not slow"` to exclude slow tests
4. **Timeout protection**: 15 min timeout to prevent runaway tests

**Deliverable**: Updated test.yml with comprehensive coverage

**Acceptance Criteria**:
- [ ] Workflow includes ALL fast tests (auto-discovery)
- [ ] Runtime <10 minutes
- [ ] No explicit file lists (uses pytest markers)
- [ ] Includes backend, frontend, E2E

---

#### Task 0.5.3: Create New Nightly Workflow
**Goal**: Single nightly workflow with ONLY slow tests

**File**: `.github/workflows/nightly-tests.yml` (update existing)

**New Structure**:
```yaml
name: Nightly Test Suite

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:

jobs:
  slow-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 180
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-timeout

      # Run ONLY slow tests (marked with @pytest.mark.slow)
      - name: Run slow backend tests
        run: |
          PYTHONPATH=backend python -m pytest backend/tests/ \
            -v --tb=long \
            -m "slow" \
            --timeout=600

      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const runUrl = `https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Nightly Tests Failed (${new Date().toISOString().split('T')[0]})`,
              body: `## Nightly Test Failure\n\n**Run**: ${runUrl}\n\n### Action Required\n\n1. Review logs\n2. Investigate failure\n3. Fix or document issue\n\n### Quick Links\n- [View Logs](${runUrl})`,
              labels: ['ci-failure', 'nightly', 'needs-investigation']
            });
```

**Key Changes**:
1. **Marker-based**: Only run tests marked with `@pytest.mark.slow`
2. **Long timeout**: 600 seconds per test (10 min)
3. **Auto-issue creation**: Creates GitHub issue on failure
4. **No redundancy**: Only slow tests, nothing from comprehensive

**Deliverable**: Updated nightly-tests.yml with slow tests only

**Acceptance Criteria**:
- [ ] Only runs tests marked with `@pytest.mark.slow`
- [ ] No overlap with comprehensive workflow
- [ ] Creates issue on failure
- [ ] Reasonable timeout (180 min total)

---

#### Task 0.5.4: Add Pytest Markers to Tests
**Goal**: Mark all tests as either default (fast) or slow

**Process**:
1. Add markers to conftest.py
2. Mark slow tests with `@pytest.mark.slow`
3. Leave fast tests unmarked (default)

**File 1**: `backend/conftest.py`
```python
import pytest

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselected by default, run in nightly)"
    )
```

**File 2**: Mark slow tests (example)
```python
# backend/tests/test_stress_ai_games.py
import pytest

@pytest.mark.slow
def test_200_game_ai_marathon():
    """Slow test: 200 AI games"""
    # ... test code ...

@pytest.mark.slow
def test_stress_concurrent_games():
    """Slow test: concurrent game stress"""
    # ... test code ...
```

**Tests to Mark as Slow**:
- `test_stress_ai_games.py` (all tests)
- `test_property_based_enhanced.py` (1000 scenario test only)
- `test_action_fuzzing.py` (all tests)
- `test_concurrency.py` (all tests)
- `test_performance.py` (benchmark tests only)
- `test_rng_fairness.py` (statistical tests)
- Any test taking >60 seconds

**Deliverable**: Pytest markers configured and applied

**Acceptance Criteria**:
- [ ] conftest.py has `slow` marker defined
- [ ] All slow tests marked with `@pytest.mark.slow`
- [ ] Fast tests left unmarked (default)
- [ ] Documentation updated

---

#### Task 0.5.5: Delete Redundant Workflows
**Goal**: Remove 3 redundant workflow files

**Files to Delete**:
1. `.github/workflows/quick-tests.yml` (redundant with comprehensive)
2. `.github/workflows/frontend-tests.yml` (merged into comprehensive)
3. `.github/workflows/nightly-e2e.yml` (merged into comprehensive + nightly)

**Process**:
```bash
# Delete redundant workflows
rm .github/workflows/quick-tests.yml
rm .github/workflows/frontend-tests.yml
rm .github/workflows/nightly-e2e.yml

# Verify only 3 workflows remain
ls -la .github/workflows/
# Should show:
# - test.yml (comprehensive)
# - nightly-tests.yml (slow tests only)
# - generate-visual-baselines.yml (manual utility)
```

**Deliverable**: 3 workflows deleted, 3 remaining

**Acceptance Criteria**:
- [ ] quick-tests.yml deleted
- [ ] frontend-tests.yml deleted
- [ ] nightly-e2e.yml deleted
- [ ] Only 3 workflows remain (comprehensive, nightly, visual-baselines)

---

#### Task 0.5.6: Update Documentation
**Goal**: Document new test suite structure

**File**: `docs/TEST-SUITE-REFERENCE.md`

**Add Section**:
```markdown
## Test Suite Organization (Updated 2026-01-12)

### Philosophy
We maintain exactly **2 test workflows**:

1. **Comprehensive Test Suite** (Per-commit, <10 min)
   - ALL fast tests (unmarked or not marked `slow`)
   - Runs on every commit and PR
   - Must pass before merge
   - Target: <10 minutes total runtime

2. **Nightly Test Suite** (Daily, unlimited)
   - ONLY slow tests (marked with `@pytest.mark.slow`)
   - Runs at 2 AM UTC daily
   - Can take hours if needed
   - Failure creates GitHub issue

### Running Tests Locally

**Run all fast tests (what CI runs per-commit):**
```bash
PYTHONPATH=backend pytest backend/tests/ -m "not slow" -v
```

**Run only slow tests (what CI runs nightly):**
```bash
PYTHONPATH=backend pytest backend/tests/ -m "slow" -v
```

**Run ALL tests (comprehensive + slow):**
```bash
PYTHONPATH=backend pytest backend/tests/ -v
```

### Marking Tests

**Default (fast tests):**
```python
def test_hand_evaluation():
    # No marker needed - runs in comprehensive suite
    pass
```

**Slow tests:**
```python
import pytest

@pytest.mark.slow
def test_200_game_marathon():
    # Only runs in nightly suite
    pass
```

### Adding New Tests

**Decision tree:**
1. Does your test take >60 seconds? → Mark with `@pytest.mark.slow`
2. Otherwise → No marker needed (runs in comprehensive)

**Guidelines:**
- Comprehensive suite must stay <10 minutes total
- If comprehensive exceeds 10 min, promote slowest tests to nightly
- Nightly suite can be unlimited (within 180 min timeout)
```

**Deliverable**: Updated documentation

**Acceptance Criteria**:
- [ ] TEST-SUITE-REFERENCE.md updated with new structure
- [ ] CLAUDE.md updated with workflow commands
- [ ] Clear guidelines for marking tests

---

#### Task 0.5.7: Verify New Structure
**Goal**: Test new workflows locally and in CI

**Process**:
1. **Test marker discovery locally**:
   ```bash
   # Should show all fast tests
   pytest backend/tests/ -m "not slow" --collect-only

   # Should show only slow tests
   pytest backend/tests/ -m "slow" --collect-only
   ```

2. **Run comprehensive suite locally**:
   ```bash
   # Should complete in <10 minutes
   time PYTHONPATH=backend pytest backend/tests/ -m "not slow" -v
   ```

3. **Commit and push**:
   ```bash
   git add .github/workflows/ backend/conftest.py backend/tests/ docs/
   git commit -m "Phase 0.5: Consolidate to 2 test workflows (comprehensive + nightly)"
   git push
   ```

4. **Monitor first CI run**:
   - Check comprehensive workflow runs
   - Verify all expected tests run
   - Confirm runtime <10 minutes
   - Check test count matches expectations

**Deliverable**: Working 2-workflow structure

**Acceptance Criteria**:
- [ ] Comprehensive workflow runs successfully
- [ ] Runtime <10 minutes
- [ ] All fast tests execute
- [ ] No redundant workflows running
- [ ] Test count documented

---

### Phase 0.5 Success Metrics

**Before Phase 0.5**:
- 5 workflows (3 redundant)
- 31% backend test coverage in CI (18/58 files)
- Explicit file lists (brittle, easy to forget new tests)
- Nightly tests 100% failure rate

**After Phase 0.5**:
- 2 workflows (clean, purposeful)
- ~90% backend test coverage in CI (50+/58 files)
- Auto-discovery via pytest markers (new tests automatically included)
- Nightly tests stable or disabled temporarily

**Expected Runtime**:
- Comprehensive: 8-10 minutes (currently 7-8 min, adding ~50% more tests)
- Nightly: 60-120 minutes (down from 167 min, only true slow tests)

---

### Phase 1: Critical Bug Fixes (IMMEDIATE)
**Goal**: Fix the two critical issues that remain unresolved

**Timeline**: Today (1-2 hours)

#### Task 1.1: Fix Performance Test Logic Error
**File**: `backend/tests/test_performance.py`
**Line**: 367

**Current (BROKEN)**:
```python
for player in game.players:
    if player.is_active and not player.has_acted:
        success = game.apply_action(
            game.current_player_index,  # WRONG
            "call",
            0
        )
```

**Proposed Fix**:
```python
for player_idx, player in enumerate(game.players):
    if player.is_active and not player.has_acted:
        # Skip if not this player's turn
        if game.current_player_index != player_idx:
            continue

        success = game.apply_action(
            player_idx,  # CORRECT - unique index per player
            "call",
            0
        )
        if success:
            actions_processed += 1
```

**Validation**:
1. Read full test file to understand intent
2. Apply fix
3. Run test locally: `pytest backend/tests/test_performance.py -v`
4. Verify all assertions pass
5. Commit with descriptive message

**Acceptance Criteria**:
- [ ] Test passes locally 100% of the time (run 3x)
- [ ] No TypeErrors related to player_index
- [ ] Test validates correct poker game behavior

---

#### Task 1.2: Investigate Segmentation Fault
**Location**: Backend tests (cleanup phase)

**Investigation Steps**:
1. **Search for historical evidence**:
   ```bash
   git log --all --grep="segfault" --oneline
   git log --all --grep="core dump" --oneline
   git log --all --grep="crash" --oneline
   ```

2. **Check current test suite for patterns**:
   ```bash
   # Look for tests that might cause memory issues
   grep -r "stress" backend/tests/
   grep -r "property_based" backend/tests/
   ```

3. **Run tests with debug instrumentation**:
   ```bash
   # Enable Python fault handler
   PYTHONPATH=backend python -X faulthandler -m pytest \
     backend/tests/test_stress_ai_games.py -v

   # Run with memory debugging
   PYTHONMALLOC=debug pytest backend/tests/ -v
   ```

4. **Check for treys-related issues**:
   ```bash
   # treys is a C extension - potential source of segfaults
   grep -r "from treys import" backend/
   ```

5. **Monitor CI logs for segfault patterns**:
   ```bash
   gh run list --limit 20 --json conclusion,name,createdAt
   gh run view <failed-run-id> --log | grep -i "segfault\|core dump\|signal 11"
   ```

**Deliverable**: Investigation report documenting:
- Whether segfault is reproducible
- If reproducible: stack trace and root cause
- If not reproducible: evidence checked and confidence level
- Recommendations for prevention/monitoring

**Acceptance Criteria**:
- [ ] Thorough investigation documented
- [ ] If reproducible: fix implemented
- [ ] If not reproducible: monitoring added to detect recurrence
- [ ] Decision made: ignore, monitor, or fix

---

### Phase 2: Code Quality Audit (SHORT-TERM)
**Goal**: Review recent test changes for similar issues

**Timeline**: This week (2-3 hours)

#### Task 2.1: Audit All Test Files Changed in Last 3 Days
**Scope**: Review all test files modified during infrastructure work

**Process**:
1. **List all test changes**:
   ```bash
   git log --since="3 days ago" --name-only --oneline | grep "test_" | sort -u
   ```

2. **Review each test for common issues**:
   - Incorrect player_index usage
   - Iterating over players without checking turn order
   - Using `current_player_index` when `player_idx` should be used
   - Assertions that could always pass
   - Missing edge case handling

3. **Create checklist**:
   - [ ] Does test use correct player indices?
   - [ ] Are assertions meaningful?
   - [ ] Is test isolated (no dependencies)?
   - [ ] Does it test what it claims?
   - [ ] Are edge cases covered?

**Deliverable**:
- List of issues found (if any)
- Fixes for each issue
- Summary of code quality findings

**Acceptance Criteria**:
- [ ] All test files from last 3 days reviewed
- [ ] Issues documented with severity
- [ ] High-severity issues fixed
- [ ] Low-severity issues tracked for future fix

---

#### Task 2.2: Validate CI Configuration References
**Goal**: Ensure all workflow files reference existing files

**Process**:
1. **List all workflow files**:
   ```bash
   ls -la .github/workflows/
   ```

2. **Extract file references from each workflow**:
   ```bash
   grep -h "pytest\|test_\|\.py" .github/workflows/*.yml
   ```

3. **Verify each referenced file exists**:
   ```bash
   # For each file reference, check:
   test -f backend/tests/test_performance.py && echo "EXISTS" || echo "MISSING"
   ```

4. **Check test counts match expectations**:
   ```bash
   # Count actual tests
   pytest backend/tests/ --collect-only -q | tail -1

   # Compare to documentation in docs/TEST-SUITE-REFERENCE.md
   ```

**Deliverable**: Validation report with:
- All workflow file references
- Confirmation each referenced file exists
- Test count vs expected count comparison
- Recommendations for fixing mismatches

**Acceptance Criteria**:
- [ ] All workflow references validated
- [ ] No references to non-existent files
- [ ] Test counts match expectations
- [ ] Documentation updated if needed

---

### Phase 3: Process Safeguards (SHORT-TERM)
**Goal**: Establish safeguards to prevent similar failures

**Timeline**: This week (2-3 hours)

#### Task 3.1: Add Pre-Commit Validation Hook
**Goal**: Run critical tests before every commit

**Implementation**:
1. **Create pre-commit config**:
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: pytest-critical
           name: Critical Test Suite
           entry: bash -c 'cd backend && PYTHONPATH=backend pytest backend/tests/test_property_based_enhanced.py -v'
           language: system
           pass_filenames: false
           stages: [commit]
   ```

2. **Install pre-commit**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Test the hook**:
   ```bash
   # Make a trivial change and commit
   touch test_file
   git add test_file
   git commit -m "Test pre-commit hook"
   # Should run pytest automatically
   ```

4. **Document in CLAUDE.md**:
   ```markdown
   ## Pre-Commit Hooks

   Critical tests run automatically before each commit:
   - Property-based tests (infinite loop guard)
   - Basic poker logic validation

   To bypass (emergency only):
   git commit --no-verify -m "message"
   ```

**Deliverable**: Working pre-commit hook configuration

**Acceptance Criteria**:
- [ ] Pre-commit config created and tested
- [ ] Hook runs automatically on commit
- [ ] Blocks commit if tests fail
- [ ] Documented in CLAUDE.md
- [ ] Can be bypassed with --no-verify (emergency)

---

#### Task 3.2: Create Infrastructure Change Checklist
**Goal**: Template for making safe infrastructure changes

**Implementation**:
Create `.github/INFRASTRUCTURE_CHANGE_CHECKLIST.md`:

```markdown
# Infrastructure Change Checklist

Use this checklist for changes to:
- CI workflows (.github/workflows/*.yml)
- Test configuration (jest.config.ts, pytest.ini)
- Build configuration (package.json, requirements.txt)

## Pre-Change
- [ ] Document current state (test count, runtime, coverage)
- [ ] Create rollback plan
- [ ] Test in fork (if CI changes)
- [ ] Identify affected systems

## During Change
- [ ] Make minimal change (one thing at a time)
- [ ] Add comments explaining WHY, not just WHAT
- [ ] Update documentation
- [ ] Test locally if possible

## Post-Change
- [ ] Run affected tests locally (100% pass)
- [ ] Monitor first CI run closely
- [ ] Compare metrics (before vs after)
- [ ] Update STATUS.md with changes

## Rollback Plan
If CI fails after merge:
1. Revert commit immediately
2. Investigate locally
3. Re-apply with fix
4. Document what went wrong

## Platform-Specific Changes
For visual/snapshot tests:
- [ ] Generate baselines in CI environment (not local)
- [ ] Test on target platform (Linux for CI)
- [ ] Document baseline generation process

For coverage thresholds:
- [ ] Set to current baseline (not aspirational)
- [ ] Increase gradually (+5% per sprint)
- [ ] Test that thresholds pass before committing
```

**Deliverable**: Infrastructure change checklist template

**Acceptance Criteria**:
- [ ] Checklist created
- [ ] Added to .github/ directory
- [ ] Referenced in CLAUDE.md
- [ ] Covers all identified failure patterns

---

#### Task 3.3: Update CLAUDE.md with Prevention Guidelines
**Goal**: Add lessons learned to working agreement

**Additions to CLAUDE.md**:

```markdown
## Test Infrastructure Changes (NEW)

### Before Committing Test Changes
1. Run affected tests locally (100% pass rate required)
2. Check for platform-specific assumptions (macOS vs Linux)
3. Validate configuration files (jest.config.ts, pytest.ini)
4. Update test count in docs/TEST-SUITE-REFERENCE.md

### CI Workflow Changes
1. Test in personal fork first
2. Use Infrastructure Change Checklist (.github/INFRASTRUCTURE_CHANGE_CHECKLIST.md)
3. Monitor first run after merge
4. Have rollback plan ready

### Visual/Snapshot Tests
- Generate baselines in CI environment (Linux), never locally
- Use `generate-visual-baselines.yml` workflow for updates
- Document baseline generation in test comments

### Coverage Thresholds
- Set to current baseline, not aspirational targets
- Increase gradually (+5% per sprint max)
- Always test locally before enforcing

### Velocity Guidelines
- Maximum 5-7 commits per day during infrastructure work
- Pause every 5 commits to validate (run full test suite)
- Don't merge large changes on Fridays (need monitoring time)

### Code Review for Tests
- Test code gets same rigor as production code
- Check: correct player indices, meaningful assertions, proper isolation
- Red flags: intermittent failures, always-passing assertions, global state
```

**Deliverable**: Updated CLAUDE.md

**Acceptance Criteria**:
- [ ] Guidelines added to CLAUDE.md
- [ ] Covers all identified failure patterns
- [ ] Includes specific examples
- [ ] References Infrastructure Change Checklist

---

### Phase 4: Monitoring & Detection (LONG-TERM)
**Goal**: Add monitoring to detect issues early

**Timeline**: Next sprint (2-3 hours)

#### Task 4.1: Add Segfault Detection to CI
**Goal**: Detect and report segmentation faults in CI

**Implementation**:
Update `.github/workflows/nightly-tests.yml`:

```yaml
- name: Run stress tests with crash detection
  run: |
    # Enable core dumps
    ulimit -c unlimited

    # Run with Python fault handler
    PYTHONPATH=backend python -X faulthandler -m pytest \
      backend/tests/test_stress_ai_games.py \
      backend/tests/test_property_based_enhanced.py \
      -v --tb=long

    # Check for crashes
    if [ -f core.* ]; then
      echo "::error::Segmentation fault detected!"
      ls -lh core.*
      file core.*
      exit 1
    fi
```

**Deliverable**: Enhanced CI monitoring for crashes

**Acceptance Criteria**:
- [ ] Fault handler enabled in nightly tests
- [ ] Core dumps detected automatically
- [ ] Failures create clear error messages
- [ ] Stack traces captured for debugging

---

#### Task 4.2: Add Automatic Issue Creation for Nightly Failures
**Goal**: Track failures automatically

**Implementation**:
Add to `.github/workflows/nightly-tests.yml` and `.github/workflows/nightly-e2e.yml`:

```yaml
- name: Create issue on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      const runUrl = `https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `Nightly test failure: ${context.workflow} (${new Date().toISOString().split('T')[0]})`,
        body: `## Nightly Test Failure\n\n**Workflow**: ${context.workflow}\n**Run**: ${runUrl}\n**Date**: ${new Date().toISOString()}\n\n### Action Required\n\n1. Review logs: [View Run](${runUrl})\n2. Investigate failure cause\n3. Create fix or update this issue with findings\n4. Close issue when resolved\n\n### Investigation Checklist\n\n- [ ] Logs reviewed\n- [ ] Root cause identified\n- [ ] Fix implemented or issue documented\n- [ ] Verified fix in next nightly run`,
        labels: ['ci-failure', 'needs-investigation', 'automated']
      });
```

**Deliverable**: Automatic issue creation for failures

**Acceptance Criteria**:
- [ ] Issues created automatically on nightly failures
- [ ] Issues include links to logs and run details
- [ ] Issues include investigation checklist
- [ ] Issues properly labeled for triage

---

#### Task 4.3: Create Test Quality Review Guide
**Goal**: Document standards for reviewing test code

**Implementation**:
Add section to `docs/TESTING.md`:

```markdown
## Test Code Review Guidelines

### Review Checklist

When reviewing test code, check:

#### Correctness
- [ ] Does the test actually test what it claims?
- [ ] Are player indices used correctly?
- [ ] Does it follow poker rules accurately?
- [ ] Are edge cases covered?

#### Assertions
- [ ] Are assertions meaningful? (not just "no crash")
- [ ] Do assertions check actual vs expected values?
- [ ] Are error messages clear?

#### Isolation
- [ ] Does test depend on other tests?
- [ ] Does it modify global state?
- [ ] Can it run in any order?

#### Clarity
- [ ] Can you understand it in 30 seconds?
- [ ] Are variable names descriptive?
- [ ] Is the test intent clear?

### Common Mistakes in Poker Tests

#### Incorrect Player Index Usage
```python
# WRONG - uses same index for all players
for player in game.players:
    game.apply_action(game.current_player_index, "call", 0)

# CORRECT - uses unique index per player
for player_idx, player in enumerate(game.players):
    if game.current_player_index == player_idx:
        game.apply_action(player_idx, "call", 0)
```

#### Always-Passing Assertions
```python
# WRONG - can never fail
assert player is not None  # player comes from list iteration, always exists

# CORRECT - actually validates behavior
assert player.stack >= 0, f"Player {player.name} has negative stack"
```

#### Turn Order Violations
```python
# WRONG - doesn't respect turn order
for player in game.players:
    player.make_decision()  # Not their turn!

# CORRECT - follows game flow
while not game.is_hand_complete():
    current = game.get_current_player()
    game.apply_action(current.index, current.decide_action(), 0)
```

### Red Flags

Watch for:
- Tests that pass but production code is broken
- Intermittent failures (suggests race condition or dependency)
- Tests requiring specific order to pass
- Skipped tests (`pytest.skip`) without explanation
- Tests that take >1 second (consider moving to nightly)

### Test Classification

**Unit Tests** (fast, isolated):
- Test single function/method
- No external dependencies
- Run in <100ms each
- Example: hand evaluator tests

**Integration Tests** (moderate, some dependencies):
- Test multiple components together
- May use test database/fixtures
- Run in 100ms-1s each
- Example: game flow tests

**E2E Tests** (slow, full system):
- Test complete user scenarios
- Use real browser/network
- Run in 1s-10s each
- Example: full game UI tests

**Stress Tests** (very slow, nightly only):
- Test under load or many iterations
- May run for minutes
- Example: 200-game AI simulations
```

**Deliverable**: Test quality review guide

**Acceptance Criteria**:
- [ ] Guide added to docs/TESTING.md
- [ ] Includes specific examples of common mistakes
- [ ] Covers all failure patterns found in this investigation
- [ ] Referenced in CLAUDE.md

---

### Phase 5: Long-Term Process Improvements (FUTURE)
**Goal**: Establish sustainable development practices

**Timeline**: Next month (ongoing)

#### Task 5.1: Establish Change Management Process
**Goal**: Prevent velocity-driven quality issues

**Recommendations**:
1. **The "5-Commit Rule"**:
   - After 5 commits, pause and validate
   - Run full test suite locally
   - Review commit messages for clarity
   - Update STATUS.md with progress

2. **Work in Phases**:
   - Complete one phase fully before starting next
   - Merge, monitor, then proceed
   - Don't bundle multiple phases in one branch

3. **Maximum Daily Commits**:
   - Infrastructure work: 5-7 commits/day max
   - Feature work: 10 commits/day max
   - Allows time for validation and testing

4. **The "Friday Rule"**:
   - Don't merge large infrastructure changes on Fridays
   - Weekend monitoring is difficult
   - If urgent, monitor actively through weekend

**Deliverable**: Process guidelines document

**Acceptance Criteria**:
- [ ] Guidelines documented
- [ ] Team agreement on velocity limits
- [ ] Enforcement mechanism established
- [ ] Success metrics defined

---

#### Task 5.2: Create "Smoke Test" Suite
**Goal**: Fast validation before every commit

**Requirements**:
- Runs in <30 seconds
- Covers critical paths
- High confidence in system health

**Proposed Tests**:
1. One complete hand of poker (deal → showdown)
2. One AI decision (tight vs loose)
3. One WebSocket message (connection → action)
4. One hand evaluation (royal flush, high card)
5. One chip conservation check

**Implementation**:
```python
# backend/tests/test_smoke.py
"""
Smoke tests - fast validation of critical paths.
Run before every commit.
Target: <30 seconds total
"""

def test_complete_hand_end_to_end():
    """One hand from deal to showdown"""
    # ~3 seconds

def test_ai_makes_decision():
    """AI opponent makes valid decision"""
    # ~1 second

def test_websocket_message():
    """WebSocket connection and action"""
    # ~2 seconds

def test_hand_evaluator():
    """Hand evaluation accuracy"""
    # ~0.5 seconds

def test_chip_conservation():
    """Chips conserved through hand"""
    # ~3 seconds
```

**Deliverable**: Smoke test suite

**Acceptance Criteria**:
- [ ] Smoke test suite created
- [ ] Runs in <30 seconds
- [ ] Covers all critical paths
- [ ] Added to pre-commit hook
- [ ] Documented in TESTING.md

---

#### Task 5.3: Documentation Audit and Maintenance
**Goal**: Ensure documentation reflects current state

**Process**:
1. **Audit all docs**:
   - Check dates (last updated)
   - Verify accuracy (current vs documented)
   - Identify gaps (missing information)

2. **Update key documents**:
   - `docs/TEST-SUITE-REFERENCE.md` (test counts, new suites)
   - `docs/TESTING.md` (new guidelines)
   - `CLAUDE.md` (working agreement updates)
   - `STATUS.md` (current state)

3. **Archive outdated docs**:
   - Move to `archive/` with date
   - Update `docs/INDEX.md`
   - Keep only current docs in main directory

**Deliverable**: Updated and accurate documentation

**Acceptance Criteria**:
- [ ] All docs reviewed for accuracy
- [ ] Test counts match actual
- [ ] Outdated docs archived
- [ ] INDEX.md updated

---

## Success Metrics

### Immediate Success (Phase 1-2)
- [ ] Performance test bug fixed and verified
- [ ] Segfault investigated with clear conclusion
- [ ] All tests pass locally and in CI
- [ ] No false claims in documentation

### Short-Term Success (Phase 3-4)
- [ ] Pre-commit hooks installed and working
- [ ] Infrastructure change checklist in use
- [ ] CI detects segfaults automatically
- [ ] Nightly failures create issues automatically

### Long-Term Success (Phase 5)
- [ ] CI failure rate <5% (currently ~20%)
- [ ] No preventable failures reach CI
- [ ] Test code quality equal to production code
- [ ] Documentation stays current (monthly reviews)

---

## Risk Assessment

### Risks During Remediation

**Risk**: Fixing one thing breaks another
- **Mitigation**: Run full test suite after each fix
- **Detection**: Pre-commit hooks catch regressions

**Risk**: Segfault investigation takes too long
- **Mitigation**: Time-box to 2 hours, decide monitor vs fix
- **Escalation**: If can't reproduce, add monitoring and move on

**Risk**: Process changes slow down development
- **Mitigation**: Balance speed and quality
- **Adjustment**: Review velocity limits after 1 sprint

---

## Open Questions

1. **Performance Test Intent**: What was the original intent of the stress test loop?
   - Option A: Test each player's actions in turn order
   - Option B: Test rapid action processing regardless of turn
   - **Decision needed before fixing**

2. **Segfault Reproducibility**: Can we reproduce it locally?
   - If yes: Root cause and fix
   - If no: Add monitoring and document uncertainty

3. **Velocity Limits**: What's the right balance?
   - Current: 30 commits/3 days = 10/day (too fast)
   - Proposed: 5-7/day for infrastructure (50% slower)
   - **Decision needed for Phase 5**

---

## Appendix: Agent Analysis Details

### Agent 1: Commit History Analysis
- **Date**: 2026-01-12
- **Scope**: 29 commits from Jan 10-12
- **Key Finding**: Systematic phased approach, but very rapid execution
- **Full Report**: See conversation history

### Agent 2: CI Failure Analysis
- **Date**: 2026-01-12
- **Scope**: GitHub Actions failures Jan 11-12
- **Key Finding**: 6 failure instances, 3 fixed, 3 need attention
- **Full Report**: See conversation history

### Agent 3: Root Cause Analysis
- **Date**: 2026-01-12
- **Assessment**: "Expected growing pains"
- **Limitations**: Some incorrect claims (missing files), dismissed segfault
- **Full Report**: See conversation history

### Agent 4: Senior Review
- **Date**: 2026-01-12
- **Assessment**: "Process breakdown, not just growing pains"
- **Grade**: Agent 3 analysis received grades A-F by component
- **Key Contribution**: Identified false claims, deeper root causes
- **Full Report**: See conversation history

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-12 | 1.0 | Initial plan created | Multi-Agent Investigation |

---

## Next Steps

1. **User Review**: Review this plan and approve Phase 1 execution
2. **Phase 1 Execution**: Fix critical bugs (performance test, segfault investigation)
3. **Phase 1 Checkpoint**: Discuss findings and results before proceeding
4. **Phase 2+**: Continue through phases with checkpoints

**Status**: Awaiting user approval to begin Phase 1
