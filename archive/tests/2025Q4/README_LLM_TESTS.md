# Phase 4 LLM Analysis E2E Tests

Comprehensive Playwright tests for LLM-powered hand analysis.

## Test Coverage

### Free Tests (No API Calls - $0)
✅ Run in CI/CD without cost

1. **UI Elements Test** - Verifies modal structure, buttons, text
2. **Admin Metrics Endpoint** - Tests `/admin/analysis-metrics` API

### Paid Tests (Require API Key - ~$0.11 total)
⚠️ Skip in CI/CD to avoid costs

1. **Quick Analysis Flow** (~$0.016)
   - Complete flow: Play hand → Analyze → Verify Haiku response
   - Validates analysis content structure
   - Checks cost/model info displayed

2. **Deep Dive Flow** (~$0.029)
   - Tests Sonnet 4.5 analysis
   - Verifies deeper, more technical content
   - Checks longer response time

3. **Caching Test** (~$0.016)
   - First analysis: ~2-3s (API call)
   - Second analysis: <0.5s (cached)
   - Verifies 5x+ speedup

4. **Back Button Test** (~$0.016)
   - Tests navigation between analysis types
   - Verifies state management

5. **Multiple Hands Test** (~$0.032)
   - Analyzes 2 different hands
   - Verifies analysis varies by hand

## Quick Start

### 1. Prerequisites

Start both servers:
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Run Tests

**Free tests only** (no API calls):
```bash
cd tests/e2e
./run_llm_tests.sh
```

**All tests** (including API calls - $0.11 cost):
```bash
cd tests/e2e
./run_llm_tests.sh --with-api
```

### 3. Direct pytest Commands

**Free tests only**:
```bash
# From repo root
export SKIP_LLM_TESTS=1
PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py -v
```

**All tests (costs money)**:
```bash
# From repo root
export SKIP_LLM_TESTS=0
PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py -v
```

**Run specific test**:
```bash
SKIP_LLM_TESTS=0 PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py::test_e2e_llm_quick_analysis_flow -v -s
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SKIP_LLM_TESTS` | `1` | Skip tests that cost money (1=skip, 0=run) |
| `ANTHROPIC_API_KEY` | - | Required for LLM tests (set in backend/.env) |
| `HEADLESS` | `true` | Run browser in headless mode |

## CI/CD Configuration

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
- name: Run LLM E2E Tests (Free Only)
  run: |
    export SKIP_LLM_TESTS=1
    PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py -v
```

This ensures CI runs UI tests but skips API calls (no cost).

## Test Results

### Expected Output (Free Tests)

```
tests/e2e/test_llm_analysis.py::test_e2e_llm_quick_analysis_flow SKIPPED
tests/e2e/test_llm_analysis.py::test_e2e_llm_deep_dive_analysis_flow SKIPPED
tests/e2e/test_llm_analysis.py::test_e2e_llm_analysis_caching SKIPPED
tests/e2e/test_llm_analysis.py::test_e2e_llm_analysis_ui_elements_without_api PASSED
tests/e2e/test_llm_analysis.py::test_e2e_llm_admin_metrics_endpoint PASSED
tests/e2e/test_llm_analysis.py::test_e2e_llm_test_suite_summary PASSED

========================================
🎯 Phase 4 LLM Analysis E2E Test Suite
========================================
SKIP_LLM_TESTS: True
ANTHROPIC_API_KEY: ✅ Set

Tests that call LLM API (cost money):
  - test_e2e_llm_quick_analysis_flow (~$0.016)
  - test_e2e_llm_deep_dive_analysis_flow (~$0.029)
  - test_e2e_llm_analysis_caching (~$0.016)
  - test_e2e_llm_analysis_back_button (~$0.016)
  - test_e2e_llm_multiple_hands_different_analysis (~$0.032)

Free tests (no API calls):
  - test_e2e_llm_analysis_ui_elements_without_api ($0)
  - test_e2e_llm_admin_metrics_endpoint ($0)

Total cost if all LLM tests run: ~$0.11

⚠️  LLM tests SKIPPED (set SKIP_LLM_TESTS=0 to enable)
========================================
```

### Expected Output (All Tests)

```
tests/e2e/test_llm_analysis.py::test_e2e_llm_quick_analysis_flow PASSED
✅ Quick Analysis test passed!

tests/e2e/test_llm_analysis.py::test_e2e_llm_deep_dive_analysis_flow PASSED
✅ Deep Dive Analysis test passed!

tests/e2e/test_llm_analysis.py::test_e2e_llm_analysis_caching PASSED
✅ Caching test passed! First: 2.34s, Cached: 0.12s

tests/e2e/test_llm_analysis.py::test_e2e_llm_analysis_ui_elements_without_api PASSED
✅ UI elements test passed (no API calls)!

tests/e2e/test_llm_analysis.py::test_e2e_llm_analysis_back_button PASSED
✅ Back button test passed!

tests/e2e/test_llm_analysis.py::test_e2e_llm_admin_metrics_endpoint PASSED
✅ Admin metrics endpoint test passed!

tests/e2e/test_llm_analysis.py::test_e2e_llm_multiple_hands_different_analysis PASSED
✅ Multiple hands analysis test passed!

========== 7 passed, 1 skipped in 45.23s ==========

💰 API Costs:
  Estimated: ~$0.11
  Check actual: http://localhost:8000/admin/analysis-metrics
```

## Troubleshooting

### Tests Skip with "ANTHROPIC_API_KEY not set"

**Solution**: Add API key to `backend/.env`:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY" >> backend/.env
```

### "Backend not running" Error

**Solution**: Start backend first:
```bash
cd backend && python main.py
```

### "Frontend not running" Error

**Solution**: Start frontend:
```bash
cd frontend && npm run dev
```

### Tests Time Out Waiting for Analysis

**Possible causes**:
1. API key invalid → Check console.anthropic.com
2. Network issues → Check internet connection
3. Backend error → Check backend logs

### Analysis Content Not Found

**Possible causes**:
1. LLM returned invalid JSON → Check backend logs
2. Modal structure changed → Update test selectors
3. Analysis took too long → Increase timeout

## Debugging

**Run tests with full output**:
```bash
SKIP_LLM_TESTS=0 PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py -v -s --tb=short
```

**Run with browser visible** (not headless):
```bash
HEADLESS=false SKIP_LLM_TESTS=0 PYTHONPATH=. python -m pytest tests/e2e/test_llm_analysis.py::test_e2e_llm_quick_analysis_flow -v -s
```

**Check backend logs** while test runs:
```bash
# In backend terminal, watch for:
# - "LLM analysis complete for hand #X"
# - "Analysis cached: ..."
# - Any errors
```

## Performance Benchmarks

| Test | Duration | API Calls | Cost |
|------|----------|-----------|------|
| UI Elements | 5s | 0 | $0 |
| Admin Metrics | 1s | 0 | $0 |
| Quick Analysis | 8-12s | 1 | $0.016 |
| Deep Dive | 10-15s | 1 | $0.029 |
| Caching | 6-10s | 1 | $0.016 |
| Back Button | 15-20s | 2 | $0.032 |
| Multiple Hands | 15-20s | 2 | $0.032 |
| **Total (All)** | **~60-90s** | **7** | **~$0.13** |

## Integration with Existing Tests

These tests run in parallel with existing E2E tests:

```bash
# Run all E2E tests together (free LLM tests only)
export SKIP_LLM_TESTS=1
PYTHONPATH=. python -m pytest tests/e2e/ -v
```

## Cost Management

**Development**:
- Use `SKIP_LLM_TESTS=1` by default
- Only enable LLM tests when specifically testing that feature
- Budget: ~$1/day for active development

**CI/CD**:
- Always use `SKIP_LLM_TESTS=1`
- Cost: $0 (free tests only)

**Pre-Release Testing**:
- Run all tests once before release
- Cost: ~$0.13 per full test run

## Next Steps

After tests pass:
1. ✅ Verify all 7 tests pass locally
2. ✅ Check `/admin/analysis-metrics` for accurate cost tracking
3. ✅ Add to CI/CD pipeline (with SKIP_LLM_TESTS=1)
4. ✅ Document any flaky tests
5. ✅ Commit to main branch

## Questions?

See:
- Main implementation plan: `docs/PHASE4_IMPLEMENTATION_PLAN.md`
- Testing guide: `docs/PHASE4_NEXT_STEPS.md`
- Completion summary: `docs/PHASE4_COMPLETION_SUMMARY.md`
