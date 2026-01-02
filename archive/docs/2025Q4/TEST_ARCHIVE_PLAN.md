# Test Archive Plan - December 2025

**Goal:** Reduce 40+ test files to ~15 high-value tests
**Rationale:** Too many tests create maintenance burden without catching bugs

---

## Summary

| Category | Current | Target | Action |
|----------|---------|--------|--------|
| **KEEP** | - | 15 files | Core functionality tests |
| **ARCHIVE** | - | 25+ files | Redundant, superseded, or low-value |
| **Total** | 45 files | 15 files | 67% reduction |

---

## KEEP: Core Test Files (15 files)

### Backend Core Logic (5 files)
1. ✅ `test_hand_evaluator_validation.py` (17k lines)
   - **Why:** Validates core poker hand ranking logic
   - **Value:** Critical for game correctness
   - **Coverage:** Hand evaluation, card combinations

2. ✅ `test_property_based_enhanced.py` (16k lines)
   - **Why:** Property-based testing catches edge cases
   - **Value:** Finds bugs we didn't think of
   - **Coverage:** Game invariants, state consistency

3. ✅ `test_negative_actions.py` (24k lines)
   - **Why:** Tests invalid input handling
   - **Value:** Prevents exploits and crashes
   - **Coverage:** Invalid actions, edge cases

4. ✅ `test_user_scenarios.py` (24k lines)
   - **Why:** Tests real user workflows
   - **Value:** High user impact
   - **Coverage:** Complete game flows

5. ✅ `test_edge_case_scenarios.py` (24k lines)
   - **Why:** Tests rare but important cases
   - **Value:** Catches corner case bugs
   - **Coverage:** All-ins, side pots, splits

### Feature-Specific Tests (5 files)
6. ✅ `test_llm_analyzer_unit.py` (19k lines, Phase 4)
   - **Why:** Tests LLM analysis logic
   - **Value:** Phase 4 core feature
   - **Coverage:** Prompt generation, parsing, validation

7. ✅ `test_ai_personalities.py` (7k lines, Phase 5)
   - **Why:** Tests AI personality system
   - **Value:** Phase 5 core feature
   - **Coverage:** 3 AI personalities + random assignment

8. ✅ `test_hand_history.py` (10k lines, Phase 3)
   - **Why:** Tests hand history tracking
   - **Value:** Phase 3 core feature
   - **Coverage:** CompletedHand data capture

9. ✅ `test_player_count_support.py` (4k lines, Recent)
   - **Why:** Tests 6-player table support
   - **Value:** Recent feature, needs coverage
   - **Coverage:** 2-6 player games

10. ✅ `test_api_integration.py` (9k lines)
    - **Why:** Tests REST API endpoints
    - **Value:** Backend-frontend contract
    - **Coverage:** All API endpoints

### WebSocket & Network (2 files)
11. ✅ `test_websocket_flow.py` (20k lines)
    - **Why:** Tests complete WebSocket game flow
    - **Value:** Critical for real-time gameplay
    - **Coverage:** Full WebSocket lifecycle
    - **Note:** Consolidates websocket_integration + websocket_simulation

12. ✅ `test_websocket_reliability.py` (18k lines)
    - **Why:** Tests reconnection and error recovery
    - **Value:** User experience under poor network
    - **Coverage:** Disconnects, reconnects, timeouts

### E2E Tests (3 files)
13. ✅ `tests/e2e/test_critical_flows.py` (28k lines)
    - **Why:** Tests critical user journeys
    - **Value:** Highest user impact
    - **Coverage:** Complete game flows in browser
    - **Note:** MUST UPDATE with better assertions (see TESTING_STRATEGY_ANALYSIS.md)

14. ✅ `tests/e2e/test_llm_analysis.py` (13k lines)
    - **Why:** Tests LLM analysis UI
    - **Value:** Phase 4 user-facing feature
    - **Coverage:** Quick + Deep Dive analysis
    - **Note:** MUST ADD Deep Dive test

15. ✅ `tests/e2e/test_browser_refresh.py` (16k lines)
    - **Why:** Tests state persistence on refresh
    - **Value:** Prevents lost game state
    - **Coverage:** Browser refresh, back button

---

## ARCHIVE: Redundant Tests (25+ files)

### Category 1: Diagnostic/Debug Scripts (3 files)
Move to `tests/legacy/diagnostics/`

16. 🗑️ `debug_all_in.py`
    - **Why Archive:** Debug script, not a test
    - **Superseded By:** test_edge_case_scenarios.py
    - **Value:** Low (diagnostic only)

17. 🗑️ `run_all_tests.py`
    - **Why Archive:** Outdated test runner
    - **Superseded By:** pytest directly
    - **Value:** None (pytest handles this)

18. 🗑️ `test_bb_diagnostic.py`
    - **Why Archive:** Diagnostic for big blind bug
    - **Superseded By:** test_user_scenarios.py
    - **Value:** Low (one-time debugging)

### Category 2: Superseded by Better Tests (7 files)
Move to `tests/legacy/superseded/`

19. 🗑️ `test_bb_option_simple.py`
    - **Why Archive:** Simple version of test_bb_option
    - **Superseded By:** test_bb_option.py → test_user_scenarios.py
    - **Value:** Low (redundant)

20. 🗑️ `test_bb_option.py`
    - **Why Archive:** Specific BB option testing
    - **Superseded By:** test_user_scenarios.py covers this
    - **Value:** Low (covered elsewhere)

21. 🗑️ `test_bug_fixes.py`
    - **Why Archive:** Old bug regressions
    - **Superseded By:** test_user_scenarios.py + test_negative_actions.py
    - **Value:** Low (bugs now covered by broader tests)

22. 🗑️ `test_fold_and_allin_bugs.py`
    - **Why Archive:** Specific bug fixes
    - **Superseded By:** test_edge_case_scenarios.py
    - **Value:** Low (covered by edge case tests)

23. 🗑️ `test_fold_resolution.py`
    - **Why Archive:** Basic fold handling
    - **Superseded By:** test_complete_game.py → test_user_scenarios.py
    - **Value:** Low (basic functionality)

24. 🗑️ `test_turn_order.py`
    - **Why Archive:** Basic turn order logic
    - **Superseded By:** test_user_scenarios.py
    - **Value:** Low (basic functionality)

25. 🗑️ `test_complete_game.py`
    - **Why Archive:** Basic complete game test
    - **Superseded By:** test_user_scenarios.py (more comprehensive)
    - **Value:** Low (superseded)

### Category 3: Narrow/Overly Specific Tests (5 files)
Move to `tests/legacy/specific/`

26. 🗑️ `test_action_processing.py`
    - **Why Archive:** Tests internal action processing
    - **Superseded By:** test_state_advancement.py
    - **Value:** Low (implementation detail)

27. 🗑️ `test_game_start_scenarios.py`
    - **Why Archive:** Just game start logic
    - **Superseded By:** test_user_scenarios.py (includes start)
    - **Value:** Low (too narrow)

28. 🗑️ `test_raise_validation.py`
    - **Why Archive:** Just raise amount validation
    - **Superseded By:** test_negative_actions.py (includes raises)
    - **Value:** Low (covered)

29. 🗑️ `test_analysis.py`
    - **Why Archive:** Old rule-based analysis
    - **Superseded By:** test_llm_analyzer_unit.py (Phase 4)
    - **Value:** Low (old system)

30. 🗑️ `test_phase4_gameplay_verification.py`
    - **Why Archive:** Phase-specific verification
    - **Superseded By:** test_user_scenarios.py + E2E tests
    - **Value:** Low (phase-specific, now redundant)

### Category 4: Redundant WebSocket Tests (3 files)
Move to `tests/legacy/websocket/`

**Keep only:** test_websocket_flow.py + test_websocket_reliability.py

31. 🗑️ `test_websocket_integration.py`
    - **Why Archive:** Duplicate of websocket_flow
    - **Superseded By:** test_websocket_flow.py
    - **Value:** Low (redundant coverage)

32. 🗑️ `test_websocket_simulation.py`
    - **Why Archive:** Simulation-based testing
    - **Superseded By:** test_websocket_flow.py
    - **Value:** Low (redundant approach)

33. 🗑️ `tests/e2e/test_modal_pointer_events_simple.py`
    - **Why Archive:** Simple modal test
    - **Superseded By:** test_critical_flows.py (includes modals)
    - **Value:** Low (too simple)

### Category 5: Performance/Stress Tests (5 files)
Move to `tests/performance/` (keep but separate)

**Note:** These are valuable but not for regular CI runs

34. 📊 `test_performance.py` → `tests/performance/`
    - **Keep but separate:** Performance benchmarks
    - **Run:** Weekly, not on every commit
    - **Value:** Medium (performance monitoring)

35. 📊 `test_concurrency.py` → `tests/performance/`
    - **Keep but separate:** Concurrent game handling
    - **Run:** Weekly
    - **Value:** Medium (load testing)

36. 📊 `test_action_fuzzing.py` → `tests/performance/`
    - **Keep but separate:** Fuzzing/security testing
    - **Run:** Weekly
    - **Value:** Medium (security)

37. 📊 `test_network_resilience.py` → `tests/performance/`
    - **Keep but separate:** Network failure scenarios
    - **Run:** Weekly
    - **Value:** Medium (reliability)

38. 📊 `test_rng_fairness.py` → `tests/performance/`
    - **Keep but separate:** RNG statistical validation
    - **Run:** Monthly
    - **Value:** Low (statistical validation)

### Category 6: AI-Only/Stress Tests (3 files)
Move to `tests/performance/`

39. 📊 `test_ai_only_games.py` → `tests/performance/`
    - **Keep but separate:** AI vs AI games
    - **Run:** Weekly (not user-facing)
    - **Value:** Low (AI testing only)

40. 📊 `test_stress_ai_games.py` → `tests/performance/`
    - **Keep but separate:** AI stress testing
    - **Run:** Weekly
    - **Value:** Low (stress testing)

41. 🗑️ `test_ai_spr_decisions.py`
    - **Why Archive:** SPR decision logic only
    - **Superseded By:** test_ai_personalities.py (includes SPR)
    - **Value:** Low (covered by personality tests)

### Category 7: Poker Logic Tests (Keep Some)

**KEEP:**
- test_hand_evaluator_validation.py ✅
- test_hand_strength.py ✅ (Keep - core logic)
- test_side_pots.py ✅ (Keep - important edge case)
- test_heads_up.py ✅ (Keep - 2-player mode)
- test_all_in_scenarios.py ✅ (Keep - critical edge case)
- test_state_advancement.py ✅ (Keep - state machine)

### Category 8: LLM Tests (Keep but Update)

**KEEP:**
- test_llm_analyzer_unit.py ✅

**ARCHIVE:**
42. 🗑️ `test_llm_api_integration.py`
    - **Why Archive:** Incomplete, uses wrong TestClient approach
    - **Superseded By:** tests/e2e/test_llm_analysis.py
    - **Value:** Low (broken integration test)

---

## Final Count

### Tests to KEEP (21 files)
**Regular CI (15 files):**
1. test_hand_evaluator_validation.py
2. test_property_based_enhanced.py
3. test_negative_actions.py
4. test_user_scenarios.py
5. test_edge_case_scenarios.py
6. test_llm_analyzer_unit.py
7. test_ai_personalities.py
8. test_hand_history.py
9. test_player_count_support.py
10. test_api_integration.py
11. test_websocket_flow.py
12. test_websocket_reliability.py
13. tests/e2e/test_critical_flows.py
14. tests/e2e/test_llm_analysis.py
15. tests/e2e/test_browser_refresh.py

**Poker Logic (6 files):**
16. test_hand_strength.py
17. test_side_pots.py
18. test_heads_up.py
19. test_all_in_scenarios.py
20. test_state_advancement.py
21. test_analysis.py (old rule-based, keep for fallback testing)

**Performance (Move to tests/performance/ - 7 files):**
- test_performance.py
- test_concurrency.py
- test_action_fuzzing.py
- test_network_resilience.py
- test_rng_fairness.py
- test_ai_only_games.py
- test_stress_ai_games.py

**Total KEEP:** 21 core + 7 performance = 28 files

### Tests to ARCHIVE (17+ files)

**Move to tests/legacy/:**
- debug_all_in.py
- run_all_tests.py
- test_bb_diagnostic.py
- test_bb_option_simple.py
- test_bb_option.py
- test_bug_fixes.py
- test_fold_and_allin_bugs.py
- test_fold_resolution.py
- test_turn_order.py
- test_complete_game.py
- test_action_processing.py
- test_game_start_scenarios.py
- test_raise_validation.py
- test_phase4_gameplay_verification.py
- test_websocket_integration.py
- test_websocket_simulation.py
- test_ai_spr_decisions.py
- test_llm_api_integration.py
- tests/e2e/test_modal_pointer_events_simple.py

**Total ARCHIVE:** 19 files

---

## Migration Commands

```bash
# Create archive structure
mkdir -p tests/legacy/{diagnostics,superseded,specific,websocket}
mkdir -p tests/performance

# Archive diagnostic scripts
mv tests/debug_all_in.py tests/legacy/diagnostics/
mv tests/run_all_tests.py tests/legacy/diagnostics/
mv tests/test_bb_diagnostic.py tests/legacy/diagnostics/

# Archive superseded tests
mv tests/test_bb_option*.py tests/legacy/superseded/
mv tests/test_bug_fixes.py tests/legacy/superseded/
mv tests/test_fold_and_allin_bugs.py tests/legacy/superseded/
mv tests/test_fold_resolution.py tests/legacy/superseded/
mv tests/test_turn_order.py tests/legacy/superseded/
mv tests/test_complete_game.py tests/legacy/superseded/

# Archive specific/narrow tests
mv tests/test_action_processing.py tests/legacy/specific/
mv tests/test_game_start_scenarios.py tests/legacy/specific/
mv tests/test_raise_validation.py tests/legacy/specific/
mv tests/test_phase4_gameplay_verification.py tests/legacy/specific/
mv tests/test_ai_spr_decisions.py tests/legacy/specific/
mv tests/test_llm_api_integration.py tests/legacy/specific/

# Archive redundant websocket tests
mv tests/test_websocket_integration.py tests/legacy/websocket/
mv tests/test_websocket_simulation.py tests/legacy/websocket/
mv tests/e2e/test_modal_pointer_events_simple.py tests/legacy/websocket/

# Move performance tests
mv tests/test_performance.py tests/performance/
mv tests/test_concurrency.py tests/performance/
mv tests/test_action_fuzzing.py tests/performance/
mv tests/test_network_resilience.py tests/performance/
mv tests/test_rng_fairness.py tests/performance/
mv tests/test_ai_only_games.py tests/performance/
mv tests/test_stress_ai_games.py tests/performance/

# Create archive README
cat > tests/legacy/README.md << 'EOF'
# Legacy Tests Archive

These tests have been archived as they are:
- Superseded by better tests
- Too narrow/specific
- Diagnostic scripts
- Redundant coverage

**Do not delete** - they may be useful for reference or resurrection if needed.

See: docs/TEST_ARCHIVE_PLAN.md for details.
EOF
```

---

## Benefits of Archive Plan

### Before (Current State)
- **Files:** 45 test files in tests/
- **Maintenance:** High (40+ files to maintain)
- **Clarity:** Low (can't find important tests)
- **Run time:** Unknown (likely 30+ min)
- **Value:** Medium (quantity without quality)

### After (Proposed State)
- **Files:** 21 core tests in tests/ + 7 in tests/performance/
- **Maintenance:** Low (focused set)
- **Clarity:** High (clear test organization)
- **Run time:** ~10-15 min for core tests
- **Value:** High (quality over quantity)

### What We Gain
1. ✅ **Faster test runs** (fewer redundant tests)
2. ✅ **Easier to find tests** (logical organization)
3. ✅ **Lower maintenance** (38% fewer files to maintain)
4. ✅ **Clearer coverage** (know what's tested)
5. ✅ **Focus on critical tests** (user-facing bugs)

### What We Keep
- All critical functionality coverage
- All feature-specific tests (Phases 3-5)
- All important edge cases
- Performance tests (just moved, not deleted)

---

## Recommended Test Structure After Archive

```
tests/
├── smoke/                          # NEW: Tier 0
│   └── test_smoke.py               # 3 critical tests
│
├── unit/                           # Core logic (6 files)
│   ├── test_hand_evaluator_validation.py
│   ├── test_hand_strength.py
│   ├── test_side_pots.py
│   ├── test_all_in_scenarios.py
│   ├── test_state_advancement.py
│   └── test_llm_analyzer_unit.py
│
├── integration/                    # Backend tests (6 files)
│   ├── test_contracts.py           # NEW: Contract tests
│   ├── test_property_based_enhanced.py
│   ├── test_negative_actions.py
│   ├── test_api_integration.py
│   ├── test_websocket_flow.py
│   └── test_websocket_reliability.py
│
├── features/                       # Feature tests (4 files)
│   ├── test_ai_personalities.py    # Phase 5
│   ├── test_hand_history.py        # Phase 3
│   ├── test_player_count_support.py
│   └── test_heads_up.py
│
├── scenarios/                      # User scenarios (2 files)
│   ├── test_user_scenarios.py
│   └── test_edge_case_scenarios.py
│
├── e2e/                            # Browser tests (4 files)
│   ├── test_data_accuracy.py       # NEW: Data matching
│   ├── test_critical_flows.py
│   ├── test_llm_analysis.py
│   └── test_browser_refresh.py
│
├── performance/                    # Performance (7 files, run weekly)
│   ├── test_performance.py
│   ├── test_concurrency.py
│   ├── test_action_fuzzing.py
│   ├── test_network_resilience.py
│   ├── test_rng_fairness.py
│   ├── test_ai_only_games.py
│   └── test_stress_ai_games.py
│
└── legacy/                         # Archived (19 files, reference only)
    ├── diagnostics/
    ├── superseded/
    ├── specific/
    └── websocket/
```

**Total Active Tests:** 21 core + 3 new = 24 files
**Archived Tests:** 19 files
**Performance Tests:** 7 files (run separately)

---

## Execution Plan

### Phase 1: Immediate (Today)
1. ✅ Create archive directories
2. ✅ Move 19 files to tests/legacy/
3. ✅ Move 7 files to tests/performance/
4. ✅ Create README in legacy/
5. ✅ Update pytest.ini to exclude legacy/ by default

### Phase 2: This Week
1. ✅ Create new test structure (smoke/, unit/, integration/, etc.)
2. ✅ Move remaining tests to organized structure
3. ✅ Add 3 new critical tests (smoke, contracts, data_accuracy)
4. ✅ Update CI/CD to run organized tests

### Phase 3: Next Sprint
1. ✅ Review archived tests - delete if truly obsolete
2. ✅ Document test organization in README
3. ✅ Set up performance test schedule (weekly)

---

## Success Criteria

**Archive is successful when:**
1. ✅ Reduced from 45 files to ~24 active test files
2. ✅ All critical functionality still covered
3. ✅ Test run time reduced by 30-50%
4. ✅ New developers can easily find relevant tests
5. ✅ No important test coverage lost

---

**Created:** December 19, 2025
**Status:** Ready for Implementation
**Expected Time:** 2-3 hours to execute migration
