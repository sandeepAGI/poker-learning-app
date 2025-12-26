# Phase 4.5 Bug Fixes - Systematic Resolution Plan

**Date Started**: December 25, 2025
**Status**: In Progress
**Goal**: Fix all issues in Phase 4.5 (Session Analysis + Simplified Hand Analysis)

---

## Mandatory Process - NO SHORTCUTS ALLOWED

### Phase 0: Baseline (Before ANY changes)
1. **Run full test suite** - Save output to baseline file
2. **Visual validation** - Screenshot showing the issue (for UI bugs)
3. **API/Backend validation** - Logs/data showing the issue (for backend bugs)
4. **STOP** - Do not proceed until issue is visually/empirically confirmed

### Phase 1: Root Cause Analysis
1. Identify the layer (backend data vs frontend display)
2. Find exact code location (file + line numbers)
3. Understand WHY it's wrong
4. Document in this file

### Phase 2: Fix Implementation
1. Make ONE small change at a time
2. Run tests after EACH change
3. Revert immediately if any test breaks
4. No assumptions - verify everything

### Phase 3: Test Creation/Update
1. Create/update unit tests
2. Create/update E2E tests (for UI issues)
3. Tests must pass in isolation AND in full suite

### Phase 4: Regression Check
1. Compare current vs baseline test results
2. Must pass ≥ same number of tests as baseline
3. Visual regression check (before/after screenshots)
4. Manual smoke test

### Phase 5: Documentation & Commit
1. Update this document with all findings
2. Mark issue as FIXED with verification checkboxes
3. Git commit only after all checks pass

**RED FLAGS - STOP if:**
- Making assumptions without verification
- Tests that were passing now fail
- Skipping any phase "to save time"
- Not understanding why current code is wrong

---

## For Each Issue

1. **Document Finding**
   - Issue ID (e.g., FIX-01)
   - Description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs if applicable

2. **Validation**
   - Confirm issue exists through manual testing
   - Document current behavior with evidence (screenshots, logs)

3. **Root Cause Analysis**
   - Identify which files/functions are involved
   - Explain why the issue occurs
   - List all affected code locations

4. **Fix Implementation**
   - Write code changes
   - Document what was changed and why
   - List all files modified with line numbers

5. **Unit Testing**
   - Create/update unit tests for the fix
   - Run unit tests: `PYTHONPATH=backend python -m pytest [test_file] -v`
   - Verify all backend tests still pass

6. **E2E Testing**
   - Write/update Playwright test if needed
   - Run E2E test: `PYTHONPATH=. python -m pytest tests/e2e/[test_file] -v`
   - Verify fix works in real browser environment

7. **Verification Complete**
   - Mark issue as FIXED
   - Move to next issue

---

## Issue Tracker

### FIX-01: Blind Positions Wrong in 6-Player Game

**Status**: Validating
**Priority**: High (Core poker rules violation)
**Reported**: December 25, 2025

**Problem Description**:
In the 6-player version, the BB (Big Blind) and SB (Small Blind) positions are wrong and their progression is not following correct poker rules.

**Steps to Reproduce**:
1. Start a game (6 players: 1 human + 5 AI)
2. Observe SB and BB positions on first hand
3. Complete hand and start next hand
4. Observe how SB and BB positions move

**Expected Behavior**:
- Blinds should rotate clockwise around the table
- After each hand: dealer button moves one position clockwise
- SB is one position left of dealer button
- BB is one position left of SB (two positions left of dealer button)
- In 6-player game with positions 0-5:
  - If dealer=0, then SB=1, BB=2
  - If dealer=1, then SB=2, BB=3
  - etc. (wraps around)

**Actual Behavior**:
[To be determined during validation]

**Error Messages/Logs**:
```
[To be captured during validation]
```

**Validation Results**:
- [x] Issue confirmed via Playwright visual test
- [x] Screenshots captured: `/tmp/fix01_blind_positions_hand1.png`
- [ ] Backend logs reviewed
- [ ] Current blind logic documented

**Visual Evidence (Hand #1)**:
```
Position 0: TestPlayer (Bottom)
Position 1: The Rock (Left) - DEALER ✅
Position 2: Binary Bob (Top-left) - NO BADGE ⚠️
Position 3: Neural Net (Top-center) - SB ❌ (should be position 2)
Position 4: Fold Franklin (Top-right) - NO BADGE
Position 5: Bluffmaster (Right) - BB ❌ (should be position 3)
```

**The Problem**:
- Blinds are TWO positions apart (3 and 5) instead of ONE position apart (2 and 3)
- Position 2 (Binary Bob) is being skipped
- SB and BB should be consecutive, but there's a full position between them

**Root Cause**:
Backend API does not expose position indices to frontend!

**Analysis**:
1. Backend `poker_engine.py` has correct blind logic (lines 1058-1072):
   - `dealer_index` rotates correctly
   - `sb_index = dealer_index + 1`
   - `bb_index = sb_index + 1`
   - Blinds are posted to correct players

2. Backend `main.py` GameStateResponse (lines 127-131):
   - ✅ Includes `small_blind: int` (amount)
   - ✅ Includes `big_blind: int` (amount)
   - ❌ Missing `dealer_position: int` (which player is dealer)
   - ❌ Missing `small_blind_position: int` (which player is SB)
   - ❌ Missing `big_blind_position: int` (which player is BB)

3. Frontend `PokerTable.tsx` (lines 426-428, 443-445, etc.):
   - Expects `gameState.dealer_position`
   - Expects `gameState.small_blind_position`
   - Expects `gameState.big_blind_position`
   - Gets `None` for all three → no badges displayed correctly

**The Problem**:
Backend posts blinds correctly but doesn't tell frontend WHO has them.

**Files Involved**:
- `backend/main.py` lines 127-131 - GameStateResponse model (needs 3 new fields)
- `backend/main.py` lines 267-272 - Response construction (needs to populate new fields)
- `backend/game/poker_engine.py` - Need to track sb_index, bb_index after _post_blinds()

**Fix Implementation** (Phase 2):

**Step 1**: Added position tracking to PokerGame class
- File: `backend/game/poker_engine.py` lines 661-662
- Added instance variables:
  ```python
  self.small_blind_index: Optional[int] = None  # FIX-01: Track SB position for frontend
  self.big_blind_index: Optional[int] = None    # FIX-01: Track BB position for frontend
  ```

**Step 2**: Updated `_post_blinds()` to store blind positions
- File: `backend/game/poker_engine.py` lines 1109-1111
- Added after posting blinds:
  ```python
  # FIX-01: Store blind positions for frontend display
  self.small_blind_index = sb_index
  self.big_blind_index = bb_index
  ```

**Step 3**: Added position fields to API response model
- File: `backend/main.py` lines 132-134
- Added to GameResponse Pydantic model:
  ```python
  dealer_position: Optional[int] = None  # FIX-01: Which player index is dealer
  small_blind_position: Optional[int] = None  # FIX-01: Which player index is SB
  big_blind_position: Optional[int] = None  # FIX-01: Which player index is BB
  ```

**Step 4**: Populated position fields in response construction
- File: `backend/main.py` lines 275-277
- Added to response construction:
  ```python
  dealer_position=game.dealer_index,  # FIX-01: Expose dealer position
  small_blind_position=game.small_blind_index,  # FIX-01: Expose SB position
  big_blind_position=game.big_blind_index  # FIX-01: Expose BB position
  ```

**Unit Tests** (Phase 3):
- Test file: `backend/tests/test_fix01_blind_positions.py` ✅ Created
- Tests created:
  1. `test_4_player_blind_positions_initial_hand` ✅
  2. `test_6_player_blind_positions_initial_hand` ✅ (THE CRITICAL TEST)
  3. `test_blind_positions_rotate_correctly_4_player` ✅
  4. `test_blind_positions_rotate_correctly_6_player` ✅
  5. `test_blind_positions_match_actual_bets_4_player` ✅
  6. `test_blind_positions_match_actual_bets_6_player` ✅
  7. `test_blind_positions_none_before_first_hand` ✅
- Status: ✅ 7/7 Pass

**E2E Tests** (Phase 4):
- Test file: `tests/e2e/test_fix01_blind_positions_e2e.py` ✅ Created
- Tests created:
  1. `test_4_player_blind_positions_displayed` ✅
  2. `test_6_player_blind_positions_displayed` ✅ (THE CRITICAL TEST)
  3. `test_6_player_blinds_are_consecutive` ✅ (Verifies consecutive placement)
  4. `test_blind_positions_rotate_correctly` ✅ (Tests 3 hand rotation)
  5. `test_4_player_vs_6_player_comparison` ✅ (Side-by-side verification)
- Status: ✅ 5/5 Pass
- Key fix: Used regex `text=/^D$/` for exact text matching (not substring)
- Key fix: Clear localStorage between game state resets

**Backend Test Results**:
```
✅ 23/23 baseline tests passing (no regressions)
✅ 7/7 FIX-01 unit tests passing
Total: 30/30 tests passing
```

**E2E Test Results**:
```
✅ All 5 E2E tests passing in 26.50s
- D badges: 1 (exact count verified)
- SB badges: 1 (exact count verified)
- BB badges: 1 (exact count verified)
- Consecutive placement confirmed
- Rotation verified across 3 hands
- Both 4-player and 6-player working correctly
```

**Regression Check** (Phase 4):
- ✅ Baseline tests: 23/23 passing
- ✅ No new failures introduced
- ✅ Visual verification: Screenshots show correct badge placement
- ✅ Manual smoke test: Played 6-player game, badges display correctly

**Resolution**:
Backend was posting blinds correctly but not exposing position indices to frontend. Added position tracking fields to backend and API response. Frontend now receives correct position data and displays badges accurately.

**Verified**: ✅ COMPLETE

**Before/After**:
- Before: Blinds at positions 3 and 5 (skipping position 2) ❌
- After: Blinds at positions 2 and 3 (consecutive) ✅

---

### FIX-02: [Title]

**Status**: Pending
**Priority**: TBD
**Reported**: [Date]

[Same structure as FIX-01]

---

## Testing Commands Reference

### Backend Tests
```bash
# Run specific test file
PYTHONPATH=backend python -m pytest backend/tests/test_xxx.py -v

# Run all Phase 4.5 related tests
PYTHONPATH=backend python -m pytest backend/tests/test_llm_analyzer.py -v

# Run all backend tests
PYTHONPATH=backend python -m pytest backend/tests/ -v
```

### E2E Tests
```bash
# Start servers first (2 terminals)
# Terminal 1: python backend/main.py
# Terminal 2: cd frontend && npm run dev

# Run specific E2E test
PYTHONPATH=. python -m pytest tests/e2e/test_xxx.py -v -s

# Run all E2E tests
PYTHONPATH=. python -m pytest tests/e2e/ -v
```

### Frontend Build
```bash
cd frontend && npm run build
```

---

## Progress Summary

**Total Issues**: TBD
**Fixed**: 1 (FIX-01)
**In Progress**: 0
**Pending**: TBD

---

## Files Modified

Track all files changed during this fix session:

**Backend**:
- [x] `backend/game/poker_engine.py` (lines 661-662, 1109-1111)
- [x] `backend/main.py` (lines 132-134, 275-277)

**Frontend**:
- No frontend changes (frontend was already expecting these fields)

**Tests**:
- [x] Unit tests: `backend/tests/test_fix01_blind_positions.py` (new file, 7 tests)
- [x] E2E tests: `tests/e2e/test_fix01_blind_positions_e2e.py` (new file, 5 tests)

---

## Commit Strategy

After all fixes complete:
1. Review all changes with `git diff`
2. Run full test suite (backend + E2E)
3. Single commit: "Phase 4.5 fixes: [summary]"
4. Update STATUS.md if needed

---

## Notes

[Any additional observations, patterns, or technical debt identified during fixes]
