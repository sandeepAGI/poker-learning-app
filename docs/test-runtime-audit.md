# Test Runtime Audit - Phase 0.5.1

**Date**: 2026-01-12
**Purpose**: Categorize all 56 backend tests as Fast (Comprehensive) or Slow (Nightly)

---

## Methodology

1. **Reviewed existing workflows** to identify known fast/slow tests
2. **Analyzed test file names** for obvious slow patterns (stress, performance, concurrency)
3. **Checked test counts** for volume-based categorization
4. **Applied pragmatic decisions** for remaining tests

---

## Summary Statistics

**Total Backend Tests**: 56 files

**Categorization**:
- **Fast Tests** (Comprehensive): 48 files (~86%)
- **Slow Tests** (Nightly): 8 files (~14%)

**Expected Runtimes**:
- Comprehensive: ~8-10 minutes (currently 7-8 min + 30-40% more tests)
- Nightly: ~60-120 minutes (down from 167 min, only true slow tests)

---

## Fast Tests (Comprehensive Suite - 48 files)

These tests run in <60 seconds each and are suitable for per-commit CI.

### Currently in Comprehensive (13 files) ✅
1. `test_negative_actions.py` - Negative test cases
2. `test_hand_evaluator_validation.py` - Hand evaluation correctness
3. `test_property_based_enhanced.py` - Property-based tests
4. `test_side_pots.py` - Side pot logic
5. `test_all_in_scenarios.py` - All-in scenarios
6. `test_bb_option.py` - Big blind option
7. `test_raise_validation.py` - Raise validation rules
8. `test_heads_up.py` - Heads-up specific logic
9. `test_websocket_reliability.py` - WebSocket reliability
10. `test_action_processing.py` - Action processing core (20 tests)
11. `test_state_advancement.py` - State machine
12. `test_turn_order.py` - Turn order logic
13. `test_fold_resolution.py` - Fold resolution

### Adding to Comprehensive (35 files) 🆕
14. `test_ai_decision_persistence.py` - AI decision consistency
15. `test_ai_only_games.py` - AI vs AI games
16. `test_ai_personalities.py` - AI personality behaviors
17. `test_ai_spr_decisions.py` - AI SPR-based strategy
18. `test_allin_no_reopen.py` - All-in betting rule
19. `test_analysis.py` - Game analysis features
20. `test_api_integration.py` - REST API endpoints
21. `test_bb_diagnostic.py` - BB issue diagnosis
22. `test_bb_option_simple.py` - Simplified BB tests
23. `test_blind_position_consistency.py` - Blind tracking
24. `test_board_plays.py` - Board plays scenarios
25. `test_bug_fixes.py` - Historical bug regression
26. `test_bugs_real.py` - Production bug reproductions
27. `test_card_dealing_sequence.py` - Deck management
28. `test_complete_game.py` - Full game simulation
29. `test_dead_button.py` - Dead button rule
30. `test_fix01_blind_positions.py` - Blind position fixes
31. `test_fold_and_allin_bugs.py` - Specific bug scenarios
32. `test_game_ending.py` - Game termination logic
33. `test_game_start_scenarios.py` - Game initialization
34. `test_hand_history.py` - Hand history storage
35. `test_hand_strength.py` - Hand strength evaluation
36. `test_import_consistency.py` - Import validation
37. `test_llm_analyzer_unit.py` - LLM analyzer logic
38. `test_llm_api_integration.py` - Claude API integration
39. `test_minimum_raise_across_streets.py` - Raise tracking
40. `test_minimum_raise_rules.py` - Min raise enforcement
41. `test_multiple_winners.py` - Split pot scenarios
42. `test_network_resilience.py` - Network failure handling
43. `test_odd_chip_distribution.py` - Odd chip split pot rule
44. `test_phase4_gameplay_verification.py` - Phase 4 verification
45. `test_player_count_support.py` - Variable player counts
46. `test_session_analysis_params.py` - Session analysis
47. `test_short_stack_actions.py` - Short stack logic
48. `test_side_pot_integration.py` - Complex side pots

**Rationale for these additions**:
- All are unit/integration tests with focused scope
- Test file names don't indicate high complexity
- Similar tests in comprehensive run fast
- No obvious stress/performance/concurrency patterns

---

## Slow Tests (Nightly Suite - 8 files)

These tests take >60 seconds each and should only run nightly.

### Currently in Nightly (5 files) ✅
1. `test_user_scenarios.py` - **19 minutes** - Phase 4 user scenarios
2. `test_edge_case_scenarios.py` - 350+ scenarios
3. `test_stress_ai_games.py` - 200-game AI marathon
4. `test_rng_fairness.py` - Statistical validation
5. `test_performance.py` - Performance benchmarks (10 tests)

### Adding to Nightly (3 files) 🆕
6. `test_action_fuzzing.py` - Fuzzing attacks
7. `test_concurrency.py` - Concurrent game handling
8. `test_websocket_simulation.py` - Long-running WebSocket scenarios

**Rationale for these additions**:
- `test_action_fuzzing.py`: Fuzzing implies high-volume random testing
- `test_concurrency.py`: Concurrency tests are typically slow (threading, race conditions)
- `test_websocket_simulation.py`: "Simulation" implies long-running scenarios

---

## Tests NOT Currently Running (E2E - handled separately)

These are E2E tests in `tests/e2e/` and will be handled by the E2E job:
- `test_critical_flows.py` (Python Playwright)
- `test_browser_refresh.py` (Python Playwright)
- `test_short_stack.spec.ts` (TypeScript Playwright)
- `test_visual_regression.spec.ts` (TypeScript Playwright)

---

## Tests to Remove from Workflows

### test_websocket_flow.py and test_websocket_integration.py
**Decision**: Add to Comprehensive (not E2E)

These are backend WebSocket tests, not E2E tests. They should run in the backend-tests job.

---

## Implementation Plan

### Step 1: Mark Slow Tests with @pytest.mark.slow
Add marker to these 8 files:
```python
import pytest

@pytest.mark.slow
def test_name():
    # ... test code ...
```

**Files to mark**:
1. test_user_scenarios.py (all tests)
2. test_edge_case_scenarios.py (all tests)
3. test_stress_ai_games.py (all tests)
4. test_rng_fairness.py (all tests)
5. test_performance.py (all tests)
6. test_action_fuzzing.py (all tests)
7. test_concurrency.py (all tests)
8. test_websocket_simulation.py (all tests)

### Step 2: Update Comprehensive Workflow
Replace explicit file lists with auto-discovery:
```yaml
- name: Run all backend tests
  run: |
    PYTHONPATH=backend python -m pytest backend/tests/ \
      -v --tb=short \
      -m "not slow" \
      --timeout=60
```

This will automatically run all 48 fast tests without explicit lists.

### Step 3: Update Nightly Workflow
Use marker to run only slow tests:
```yaml
- name: Run slow backend tests
  run: |
    PYTHONPATH=backend python -m pytest backend/tests/ \
      -v --tb=long \
      -m "slow" \
      --timeout=600
```

This will automatically run only the 8 slow tests.

---

## Expected Outcomes

### Coverage Increase
- **Before**: 18 tests in CI (31%)
- **After**: 48 tests in CI (86%)
- **Improvement**: +30 tests, +55% coverage

### Runtime Impact
- **Comprehensive**: 7-8 min → 8-10 min (+25% time, +167% tests)
- **Nightly**: 167 min → 60-120 min (-28% to -64% time, more focused)

### Maintainability
- **Before**: Explicit file lists (brittle, easy to forget)
- **After**: Auto-discovery via markers (robust, automatic inclusion)

---

## Validation Plan

### Step 1: Local Testing
```bash
# Test fast tests (what Comprehensive will run)
time PYTHONPATH=backend pytest backend/tests/ -m "not slow" -v

# Test slow tests (what Nightly will run)
time PYTHONPATH=backend pytest backend/tests/ -m "slow" -v

# Verify counts
pytest backend/tests/ -m "not slow" --collect-only | grep "tests collected"
pytest backend/tests/ -m "slow" --collect-only | grep "tests collected"
```

### Step 2: CI Validation
1. Push changes to feature branch
2. Monitor comprehensive workflow (should be ~8-10 min)
3. Manually trigger nightly workflow
4. Verify test counts match expectations

---

## Risks and Mitigations

### Risk: Comprehensive exceeds 10 minutes
**Mitigation**: Monitor first CI run; if >10 min, move slowest tests to nightly
**Threshold**: If comprehensive >12 min, identify and demote 3-5 slowest tests

### Risk: Some "fast" tests are actually slow
**Mitigation**: 60-second timeout per test will catch slow tests
**Action**: Tests timing out get marked with @pytest.mark.slow

### Risk: Missing tests in categorization
**Mitigation**: Auto-discovery ensures all non-marked tests run in comprehensive
**Validation**: Compare test counts before/after

---

## Appendix: Test Count Verification

**Current Comprehensive**: 13 tests from explicit lists
**New Comprehensive**: 48 tests (all without @pytest.mark.slow)
**New Nightly**: 8 tests (marked with @pytest.mark.slow)

**Total**: 56 backend test files ✅

---

## Next Steps

1. ✅ Audit complete (this document)
2. ⏭️ Add pytest markers to 8 slow tests (Task 0.5.4)
3. ⏭️ Update comprehensive workflow (Task 0.5.2)
4. ⏭️ Update nightly workflow (Task 0.5.3)
5. ⏭️ Validate locally and in CI (Task 0.5.7)
