# Test Archive

Archived tests are preserved for historical reference but not run in CI.

## Directory Structure

- **legacy/** - Pre-refactor tests (superseded by current backend tests)
- **debugging/** - One-time debugging investigations and comparison scripts
- **e2e-ui/** - Manual diagnostic tools and validation scripts
- **phase-milestones/** - Historical phase milestone tests (snapshots)

## Why Archived?

Tests are archived when:
- **Redundant** - Covered by newer tests with better coverage
- **One-time debugging** - Specific bug reproductions, no longer needed
- **Manual/interactive** - Test scripts not suitable for automated CI
- **Phase milestones** - Historical documentation of testing evolution

## Archive Date

**Date:** January 10, 2026
**Phase:** Test Suite Optimization Phase 2

### Archived Counts

- **Legacy tests:** 18 files
  - 12 fully redundant (covered by current suite)
  - 6 historical reference (still valuable for context)
- **Debugging scripts:** 9 files
- **E2E diagnostic tools:** 5 files
- **Phase milestones:** 2 files

**Total archived:** 32 test files

### Active Tests Remaining

After archival:
- **backend/tests/:** 52 files (49 original + 3 moved from root)
- **tests/legacy/:** 4 files (still useful)
- **tests/e2e/:** 17 files (active E2E tests)
- **Total active:** ~118 test files

## Archived Files Reference

### Legacy (tests/archive/legacy/)

**Fully Redundant:**
- test_all_in_bug.py → Covered by test_all_in_scenarios.py
- test_blind_bug.py → Covered by test_fix01_blind_positions.py
- test_chip_conservation_debug.py → Covered by test_property_based_enhanced.py
- test_chip_loss_detailed.py → Covered by test_property_based_enhanced.py
- test_debug_fold.py → Covered by test_fold_resolution.py
- test_next_hand_fixed.py → Covered by test_state_advancement.py
- test_next_hand_issue.py → Covered by test_state_advancement.py
- test_showdown_pot_award.py → Covered by test_side_pots.py
- test_one_player_remaining.py → Covered by test_fold_resolution.py
- test_action_fuzzing.py → Covered by test_property_based_enhanced.py
- test_qc_assertions.py → Covered by test_property_based_enhanced.py
- test_all_fixes_cli.py → Debugging artifact

**Historical Reference:**
- test_side_pots_comprehensive.py - Original comprehensive side pot tests
- test_property_based.py - Original property-based testing (before enhancement)
- test_marathon_simulation.py - Long-running stress test
- test_state_exploration.py - Exploratory testing artifact

### Phase Milestones (tests/archive/phase-milestones/)

- tests_phase2_regression.py - Phase 2 regression suite snapshot
- tests_phase3_simulation.py - Phase 3 simulation suite snapshot

### Debugging (tests/archive/debugging/)

- test_both_flows_comparison.py - REST vs WebSocket comparison
- test_websocket_vs_rest_api_final.py - Duplicate comparison
- test_hand_history_rest_vs_websocket.py - Debugging artifact
- test_websocket_save_exception.py - Specific bug investigation
- test_fold_detection.py - Debugging script
- test_next_player_index.py - Debugging script
- test_websocket_python_client.py - Manual client test
- test_websocket_3_hands.py - Manual flow test
- interactive_test.py - Developer interactive tool

### E2E UI (tests/archive/e2e-ui/)

- diagnose_at_flop.py - Developer diagnostic tool
- diagnose_layout.py - Developer diagnostic tool
- quick_visual_test.py - Manual testing script
- validate_blind_positions.py - Validation script
- validate_4player_blinds.py - Validation script

## Files Moved (Not Archived)

**Moved to backend/tests/ (still active):**
- test_multiple_winners.py - Split pot UI validation
- test_player_count_support.py - 2-4 player variations
- test_bugs_real.py - Real-world bug reproductions

These were moved from `tests/` to `backend/tests/` for better organization.

## Usage

**DO NOT delete archived tests** - they serve as:
- Historical reference for bug investigations
- Comparison with current implementation
- Documentation of past issues and fixes
- Context for understanding evolution of test suite

## Restoration

To restore an archived test:

```bash
# Example: Restore marathon simulation test
mv tests/archive/legacy/test_marathon_simulation.py tests/legacy/

# Or move to backend if it's a core test
mv tests/archive/legacy/test_marathon_simulation.py backend/tests/
```

Only restore if the test provides unique coverage not in current suite.

## Related Documentation

- **docs/test-suite-optimization-plan.md** - Full optimization plan
- **docs/TDD-EXECUTION-LOG.md** - Execution log with details
- **docs/TESTING.md** - Testing strategy overview
- **.github/CI_CD_GUIDE.md** - CI/CD infrastructure guide

---

**Archive maintained by:** Claude Sonnet 4.5
**Last updated:** January 10, 2026
