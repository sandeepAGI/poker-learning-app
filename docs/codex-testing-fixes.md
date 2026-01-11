# Codex Testing Fixes - TDD Execution Plan

**Date Started:** January 11, 2026
**Execution Mode:** Autonomous TDD (all phases)
**Success Criteria:** 100% tests passing at each phase boundary
**Based On:** docs/codex-testing-review.md analysis

---

## Overview

This plan addresses critical testing gaps identified in the codex review. Fixes are organized by risk level and logical grouping to ensure poker rule correctness and prevent regressions.

### Priority Levels
- 🔴 **Critical**: Poker rule violations or money bugs
- 🟡 **High**: UX bugs or state management issues
- 🟢 **Medium**: Coverage improvements
- 🔵 **Low**: Developer experience improvements

---

## Phase 1: Critical Backend Poker Rules (3-4 hours)

**Goal:** Fix untested poker rules that could cause incorrect gameplay or money bugs.

### 1.1: Minimum Raise Reset Across Streets 🔴
**Issue:** `last_raise_amount` reset logic untested when advancing from pre-flop → flop → turn → river
**Risk:** Players could be blocked from valid raises or allowed invalid raises post-flop
**Implementation:** `poker_engine.py:1527-1559` (_advance_state_core)

**TDD Steps:**
1. **Red**: Write test that raises pre-flop, advances to flop, verifies min raise = BB (not previous raise)
2. **Green**: Verify existing implementation resets correctly
3. **Refactor**: Add comprehensive multi-street raise sequence test
4. **Regression**: Run all poker logic tests

**Test File:** `backend/tests/test_minimum_raise_across_streets.py`
**Tests to Add:**
- `test_min_raise_resets_on_flop()`
- `test_min_raise_resets_on_turn()`
- `test_min_raise_resets_on_river()`
- `test_multi_street_raise_sequence()`

**Status:** ⏸️ Not Started

---

### 1.2: Odd Chip Distribution in 3+ Way Splits 🔴
**Issue:** Only 2-player split tested, never 3+ winners or side pots with odd chips
**Risk:** Incorrect chip distribution in split pots (money bug)
**Implementation:** `poker_engine.py:1620-1629` (position-based sorting)

**TDD Steps:**
1. **Red**: Write test with 3 players tying, pot = $101 (not divisible by 3)
2. **Green**: Verify position-from-dealer sorting gives extra chips correctly
3. **Refactor**: Add side pot + odd chip scenario
4. **Regression**: Run all side pot tests

**Test File:** `backend/tests/test_odd_chip_distribution.py` (extend existing)
**Tests to Add:**
- `test_three_way_split_odd_pot()`
- `test_four_way_split_odd_remainder()`
- `test_side_pot_with_odd_chips_multi_winner()`

**Status:** ⏸️ Not Started

---

### 1.3: Folded Players in Side Pot Calculations 🔴
**Issue:** Side pot tests never include folded players' invested chips
**Risk:** Side pot calculations could be wrong if folded player filtering logic changes
**Implementation:** `poker_engine.py:236-304` (determine_winners_with_side_pots)

**TDD Steps:**
1. **Red**: Write test where Player A folds, B/C go all-in, verify A's chips in pot but A not eligible to win
2. **Green**: Verify existing implementation handles correctly
3. **Refactor**: Add multi-side-pot with folded players
4. **Regression**: Run all side pot tests

**Test File:** `backend/tests/test_side_pots.py` (extend existing)
**Tests to Add:**
- `test_folded_player_chips_stay_in_pot()`
- `test_folded_player_not_eligible_for_side_pot()`
- `test_multi_fold_side_pot_distribution()`

**Status:** ⏸️ Not Started

---

### 1.4: Short Stack Next-Hand Behavior 🟡
**Issue:** No test for `reset_for_new_hand()` when stack < $5 (SB amount)
**Risk:** Players incorrectly marked inactive instead of posting partial blinds
**Implementation:** `poker_engine.py:124-131` (reset_for_new_hand)

**TDD Steps:**
1. **Red**: Write test where player has $3, new hand starts, verify can post partial blind (all-in)
2. **Green**: Fix if needed - should allow partial blind posting
3. **Refactor**: Add edge cases (stack = $1, stack = $4)
4. **Regression**: Run all blind posting tests

**Test File:** `backend/tests/test_short_stack_actions.py` (extend existing)
**Tests to Add:**
- `test_short_stack_can_post_partial_blind_next_hand()`
- `test_very_short_stack_all_in_blind()`
- `test_short_stack_remains_active_across_hands()`

**Status:** ⏸️ Not Started

---

### 1.5: Table Collapse (One Player Remaining) 🟢
**Issue:** No test for `_post_blinds()` early exit when `players_with_chips_count < 2`
**Risk:** Graceful game ending not validated
**Implementation:** `poker_engine.py:1043-1124` (_post_blinds)

**TDD Steps:**
1. **Red**: Write test where 3 players bust, 1 remains, verify game ends gracefully
2. **Green**: Verify existing implementation short-circuits correctly
3. **Refactor**: Test edge case (all players bust simultaneously)
4. **Regression**: Run elimination tests

**Test File:** `backend/tests/test_game_ending.py` (new file)
**Tests to Add:**
- `test_game_ends_when_one_player_remains()`
- `test_post_blinds_skipped_with_insufficient_players()`
- `test_no_crash_when_all_but_one_eliminated()`

**Status:** ⏸️ Not Started

---

## Phase 2: Frontend Component Tests (2-3 hours)

**Goal:** Add unit tests for critical React components to catch UI regressions.

### 2.1: PokerTable Action Button Logic 🟡
**Issue:** Button enablement logic (canCall, canRaise) never tested in components
**Risk:** Short-stack players blocked from valid actions in UI

**TDD Steps:**
1. **Red**: Write React Testing Library test rendering PokerTable with short stack
2. **Green**: Verify buttons enabled correctly (stack > 0 enables both)
3. **Refactor**: Test all button states (eliminated, all-in, waiting)
4. **Regression**: Run frontend unit tests

**Test File:** `frontend/__tests__/PokerTable.test.tsx` (new file)
**Tests to Add:**
- `test_call_button_enabled_when_short_stack()`
- `test_raise_button_enabled_when_short_stack()`
- `test_buttons_disabled_when_eliminated()`
- `test_buttons_disabled_when_all_in_waiting()`
- `test_all_in_button_always_available_when_active()`

**Status:** ⏸️ Not Started

---

### 2.2: Raise Slider Constraints 🟡
**Issue:** Slider min/max logic based on `last_raise_amount` never tested

**TDD Steps:**
1. **Red**: Write test that verifies slider respects minRaise from backend
2. **Green**: Verify slider correctly derives min/max from game state
3. **Refactor**: Test edge cases (short stack, maxRaise = stack)
4. **Regression**: Run frontend unit tests

**Test File:** `frontend/__tests__/PokerTable.test.tsx` (extend)
**Tests to Add:**
- `test_raise_slider_respects_min_raise()`
- `test_raise_slider_max_is_stack_plus_current_bet()`
- `test_raise_slider_disabled_when_short_stack_below_min()`

**Status:** ⏸️ Not Started

---

### 2.3: WinnerModal Split Pot Display 🟢
**Issue:** MultipleWinnersInfo and "Split Pot!" UI never tested

**TDD Steps:**
1. **Red**: Write test rendering WinnerModal with 2 winners
2. **Green**: Verify "Split Pot!" text appears
3. **Refactor**: Test 3+ winners, individual amounts displayed
4. **Regression**: Run frontend unit tests

**Test File:** `frontend/__tests__/WinnerModal.test.tsx` (new file)
**Tests to Add:**
- `test_displays_split_pot_for_two_winners()`
- `test_displays_split_pot_for_three_plus_winners()`
- `test_shows_individual_amounts_for_each_winner()`
- `test_displays_hand_ranks_at_showdown()`

**Status:** ⏸️ Not Started

---

### 2.4: WebSocket Store Step Mode 🟢
**Issue:** Zustand store step-mode logic (toggleStepMode, sendContinue) untested in frontend

**TDD Steps:**
1. **Red**: Write test that toggles stepMode in store, verifies flag set
2. **Green**: Verify store correctly manages awaiting_continue state
3. **Refactor**: Mock WebSocket, test sendContinue flow
4. **Regression**: Run frontend unit tests

**Test File:** `frontend/__tests__/store.test.ts` (new file)
**Tests to Add:**
- `test_toggle_step_mode_updates_flag()`
- `test_send_continue_calls_websocket()`
- `test_awaiting_continue_state_management()`
- `test_step_mode_persists_across_hands()`

**Status:** ⏸️ Not Started

---

## Phase 3: Frontend E2E Tests (2-3 hours)

**Goal:** Convert placeholder tests to working E2E tests with proper game state setup.

### 3.1: Enable Short-Stack E2E Tests 🟡
**Issue:** All 3 tests in `test_short_stack_ui_fix.py` skip due to no state manipulation

**TDD Steps:**
1. **Red**: Remove pytest.skip(), tests will fail without state setup
2. **Green**: Add backend fixture/endpoint to set player stacks for testing
3. **Refactor**: Implement all 3 short-stack E2E scenarios
4. **Regression**: Run E2E suite

**Prerequisites:**
- Add `POST /test/set_game_state` endpoint in main.py (only in test mode)
- Endpoint allows setting player stacks, current_bet, dealer position

**Test File:** `tests/e2e/test_short_stack_ui_fix.py` (enable existing)
**Tests to Enable:**
- `test_short_stack_can_call_all_in()`
- `test_short_stack_can_raise_all_in()`
- `test_call_button_label_shows_all_in_when_short_stack()`

**Status:** ⏸️ Not Started

---

### 3.2: Winner Modal Split Pot E2E 🟢
**Issue:** No E2E test verifies split pot UI display in browser

**TDD Steps:**
1. **Red**: Write Playwright test that forces a tie (royal flush on board)
2. **Green**: Verify modal shows "Split Pot!" and correct amounts
3. **Refactor**: Test 3-way split display
4. **Regression**: Run E2E suite

**Test File:** `tests/e2e/test_winner_modal_split_pots.py` (new file)
**Tests to Add:**
- `test_split_pot_modal_displays_correctly()`
- `test_three_way_split_shows_all_winners()`
- `test_split_pot_amounts_sum_to_pot()`

**Status:** ⏸️ Not Started

---

### 3.3: Step Mode E2E Flow 🟢
**Issue:** No E2E test exercises step-mode UI (Continue button, pausing)

**TDD Steps:**
1. **Red**: Write Playwright test that enables step mode
2. **Green**: Verify "Continue" button appears, click advances AI turn
3. **Refactor**: Test full hand in step mode
4. **Regression**: Run E2E suite

**Test File:** `tests/e2e/test_step_mode_ui.py` (new file)
**Tests to Add:**
- `test_step_mode_toggle_pauses_ai()`
- `test_continue_button_advances_single_ai_turn()`
- `test_step_mode_full_hand_completion()`

**Status:** ⏸️ Not Started

---

## Phase 4: Convert Visual Tests to Assertions (1-2 hours)

**Goal:** Make visual regression tests fail automatically instead of requiring human review.

### 4.1: Responsive Design Assertions 🔵
**Issue:** `test_responsive_design.py` prints overflow warnings but doesn't assert/fail

**TDD Steps:**
1. **Red**: Add assertions to existing overflow checks
2. **Green**: Tests will pass if no overflow detected
3. **Refactor**: Add more specific element size checks
4. **Regression**: Run E2E suite

**Test File:** `tests/e2e/test_responsive_design.py` (modify existing)
**Changes:**
- Replace `print("⚠️ OVERFLOW DETECTED!")` with `assert not overflow_check['overflow']`
- Add assertions for button sizes, card dimensions
- Remove manual screenshot review requirement

**Status:** ⏸️ Not Started

---

### 4.2: Card Sizing Assertions 🔵
**Issue:** `test_card_sizing.py` takes measurements but doesn't validate them

**TDD Steps:**
1. **Red**: Add min/max size assertions for cards
2. **Green**: Define acceptable ranges, verify cards fit
3. **Refactor**: Test aspect ratios, font scaling
4. **Regression**: Run E2E suite

**Test File:** `tests/e2e/test_card_sizing.py` (modify existing)
**Changes:**
- Assert card width in range [50px, 150px] for mobile
- Assert aspect ratio maintains 2.5:3.5 (poker card standard)
- Assert cards don't overflow container at any viewport

**Status:** ⏸️ Not Started

---

## Execution Summary

### Phase Breakdown

| Phase | Tests to Add | Estimated Time | Priority |
|-------|--------------|----------------|----------|
| **Phase 1: Backend Rules** | 17 tests | 3-4 hours | 🔴 Critical |
| **Phase 2: Frontend Components** | 16 tests | 2-3 hours | 🟡 High |
| **Phase 3: E2E Tests** | 9 tests | 2-3 hours | 🟢 Medium |
| **Phase 4: Visual Assertions** | 2 files modified | 1-2 hours | 🔵 Low |
| **TOTAL** | **42 tests** | **8-12 hours** | |

### Success Criteria per Phase

- ✅ All new tests written following TDD Red-Green-Refactor
- ✅ 100% of new tests passing
- ✅ 100% of existing tests still passing (no regressions)
- ✅ Documentation updated (this file)
- ✅ Changes committed with descriptive messages

### Files to Create

**Backend:**
- `backend/tests/test_minimum_raise_across_streets.py` (new)
- `backend/tests/test_game_ending.py` (new)

**Frontend:**
- `frontend/__tests__/PokerTable.test.tsx` (new)
- `frontend/__tests__/WinnerModal.test.tsx` (new)
- `frontend/__tests__/store.test.ts` (new)
- `tests/e2e/test_winner_modal_split_pots.py` (new)
- `tests/e2e/test_step_mode_ui.py` (new)

**Modified:**
- `backend/tests/test_odd_chip_distribution.py` (extend)
- `backend/tests/test_side_pots.py` (extend)
- `backend/tests/test_short_stack_actions.py` (extend)
- `tests/e2e/test_short_stack_ui_fix.py` (enable)
- `tests/e2e/test_responsive_design.py` (add assertions)
- `tests/e2e/test_card_sizing.py` (add assertions)

---

## Execution Log

### Phase 1: Critical Backend Poker Rules
**Status:** ✅ COMPLETED
**Started:** January 11, 2026
**Completed:** January 11, 2026

**Test Results:** 17/17 tests PASSING
- All backend tests passing
- 1 bug fixed (short stack activation threshold)
- All pre-commit tests passing
- Changes committed: da2af221

#### 1.1: Minimum Raise Reset Across Streets
**Status:** ✅ COMPLETED
**Tests Added:** 4 tests in `test_minimum_raise_across_streets.py`
- test_last_raise_amount_resets_on_flop()
- test_last_raise_amount_resets_on_turn()
- test_last_raise_amount_resets_on_river()
- test_multi_street_raise_sequence_full_hand()

#### 1.2: Odd Chip Distribution 3+ Way
**Status:** ✅ COMPLETED
**Tests Added:** 3 tests in `test_odd_chip_distribution.py`
- test_three_way_split_odd_pot()
- test_four_way_split_two_odd_chips()
- test_three_way_split_with_side_pot_odd_chips()

#### 1.3: Folded Players in Side Pots
**Status:** ✅ COMPLETED
**Tests Added:** 3 tests in `test_side_pots.py`
- test_folded_player_chips_stay_in_pot()
- test_folded_player_not_eligible_for_side_pot()
- test_multi_fold_side_pot_distribution()

#### 1.4: Short Stack Next-Hand
**Status:** ✅ COMPLETED + BUG FIX
**Tests Added:** 3 tests in `test_short_stack_actions.py`
- test_short_stack_can_post_partial_blind_next_hand()
- test_very_short_stack_all_in_blind()
- test_short_stack_remains_active_across_hands()
**Bug Fix:** `poker_engine.py:131` changed from `stack >= 5` to `stack > 0`

#### 1.5: Table Collapse
**Status:** ✅ COMPLETED
**Tests Added:** 4 tests in `test_game_ending.py`
- test_game_ends_when_one_player_remains()
- test_post_blinds_skipped_with_insufficient_players()
- test_no_crash_when_all_but_one_eliminated()
- test_heads_up_after_eliminations()

---

### Phase 2: Frontend Component Tests
**Status:** 🚫 BLOCKED - Infrastructure Required
**Started:** January 11, 2026
**Blocked Reason:** No testing framework configured for frontend

**Infrastructure Required:**
1. Jest + React Testing Library setup for Next.js 15
2. Test configuration (jest.config.js)
3. Mock setup for Zustand store and WebSocket
4. Add test scripts to package.json

**Current State:**
- Only 1 unit test exists (`short-stack-logic.test.ts`) - pure logic, no component rendering
- No `jest.config.js` or test runner configured
- Cannot run React Testing Library tests

**Recommended Next Steps:**
1. Set up Jest + RTL for Next.js 15 (see Next.js testing docs)
2. Create test utilities for mocking game state
3. Then proceed with component tests as outlined in Phase 2.1-2.4

#### 2.1: PokerTable Action Buttons
**Status:** ⏸️ Blocked by infrastructure

#### 2.2: Raise Slider Constraints
**Status:** ⏸️ Blocked by infrastructure

#### 2.3: WinnerModal Split Pot
**Status:** ⏸️ Blocked by infrastructure

#### 2.4: WebSocket Store Step Mode
**Status:** ⏸️ Blocked by infrastructure

---

### Phase 3: Frontend E2E Tests
**Status:** 🚫 BLOCKED - Test Files Don't Exist
**Started:** January 11, 2026
**Blocked Reason:** E2E test files referenced in codex review don't exist

**Infrastructure Required:**
1. Playwright setup (or Puppeteer, per codex review references)
2. Create E2E test directory structure
3. Add backend test endpoint for state manipulation
4. Write E2E tests from scratch

**Current State:**
- No `tests/e2e/` directory exists
- Files referenced in codex review (`test_short_stack_ui_fix.py`, `test_responsive_design.py`, `test_card_sizing.py`) not found in filesystem or git history
- Would need to create all E2E infrastructure + tests

**Recommended Next Steps:**
1. Set up Playwright for Next.js
2. Add backend `POST /test/set_game_state` endpoint (test mode only)
3. Create E2E tests as outlined in Phase 3.1-3.3

#### 3.1: Short-Stack E2E
**Status:** ⏸️ Blocked - test files don't exist

#### 3.2: Winner Modal Split Pot E2E
**Status:** ⏸️ Blocked - test files don't exist

#### 3.3: Step Mode E2E
**Status:** ⏸️ Blocked - test files don't exist

---

### Phase 4: Visual Test Assertions
**Status:** 🚫 BLOCKED - Depends on Phase 3
**Started:** January 11, 2026
**Blocked Reason:** Visual tests (referenced in codex review) don't exist

**Infrastructure Required:**
1. Depends on Phase 3 E2E tests existing
2. Would need to create visual regression tests from scratch

**Current State:**
- No visual test files exist
- Would need E2E framework first

**Recommended Next Steps:**
1. Complete Phase 3 first
2. Add visual assertions to E2E tests

#### 4.1: Responsive Design Assertions
**Status:** ⏸️ Blocked - test files don't exist

#### 4.2: Card Sizing Assertions
**Status:** ⏸️ Blocked - test files don't exist

---

## Notes

- **Execution Order:** Phases should be executed sequentially (1 → 2 → 3 → 4)
- **Within Phase:** Items can be executed in any order unless dependencies noted
- **Commit Frequency:** Commit after each sub-item (1.1, 1.2, etc.) passes
- **CI Validation:** Push after each phase completes to validate in CI
- **Documentation:** Update this file's Execution Log after each item

---

## Final Summary

**Date Completed:** January 11, 2026

### Phases Completed

- ✅ **Phase 1:** 17/17 backend tests implemented and passing
  - All critical poker rules now have test coverage
  - 1 bug fixed (short stack activation)
  - Committed: da2af221

### Phases Blocked

- 🚫 **Phase 2:** Requires Jest + RTL setup for Next.js 15
- 🚫 **Phase 3:** Requires Playwright setup + E2E test creation
- 🚫 **Phase 4:** Depends on Phase 3

### Overall Results

- **Tests Added:** 17 backend tests
- **Bugs Fixed:** 1 (poker_engine.py:131 activation threshold)
- **Test Pass Rate:** 100% (17/17)
- **Pre-commit Tests:** All passing (41/41)

### Infrastructure Gaps Identified

1. **Frontend Unit Testing:** No Jest/RTL configured for component tests
2. **E2E Testing:** No Playwright/Puppeteer setup, test files don't exist
3. **Visual Regression:** No infrastructure for visual testing

### Recommended Follow-up

1. **Short-term:** Set up Jest + RTL for Next.js 15, add Phase 2 tests
2. **Medium-term:** Set up Playwright, create E2E test suite (Phase 3)
3. **Long-term:** Add visual regression testing (Phase 4)

**Note:** The codex-testing-review.md referenced test files that don't exist in the codebase. Phases 2-4 require creating testing infrastructure from scratch, which is beyond the scope of adding tests to existing frameworks.

---

**Last Updated:** January 11, 2026
**Phase 1 Completed:** January 11, 2026
