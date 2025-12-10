# Comprehensive Refactoring Plan

**Date**: December 8, 2025
**Version**: 1.0
**Status**: Planning Phase

---

## Executive Summary

This document outlines a comprehensive refactoring plan to address code divergence issues discovered during UAT testing. The refactoring will consolidate duplicated logic, improve testability, and add comprehensive test coverage based on industry best practices.

---

## Part 1: Research Findings

### 1.1 Industry Best Practices (from PokerKit, PyPokerEngine, etc.)

| Practice | Source | Our Status |
|----------|--------|------------|
| 99% code coverage | PokerKit (U of Toronto) | ~60% estimated |
| Static type checking | PokerKit | Partial (no mypy) |
| Famous hand recreation | PokerKit (2023 WSOP) | Not implemented |
| MD5 checksum validation | PokerKit hand evaluator | Not implemented |
| Side pot algorithm with proofs | danielpaz6/Poker-Hand-Evaluator | Basic implementation |
| CI/CD integration | PyPokerEngine (Travis CI) | Not implemented |

### 1.2 Critical Test Scenarios Identified

Based on research from open-source poker engines and poker rules documentation:

#### Category A: Hand Evaluation (HIGH PRIORITY)

1. All 10 hand rankings (Royal Flush -> High Card)
2. Kicker comparison for same-rank hands
3. Split pot detection (identical 5-card hands)
4. Board-only winners (community cards beat all hole cards)
5. Tie-breaking with shared cards

#### Category B: Betting Logic (CRITICAL PRIORITY)

1. **All-in scenarios**:
   - Player can't match bet, goes all-in for less
   - Multiple players all-in with different stacks
   - All players all-in simultaneously
   - Single player all-in, others fold
2. **Side pot creation**:
   - Main pot + 1 side pot (3 players, 2 stack sizes)
   - Main pot + 2 side pots (4 players, 3 stack sizes)
   - Main pot + N side pots (N+1 players)
3. **Side pot distribution**:
   - Short stack wins main pot only
   - Medium stack wins main + side pot 1
   - Large stack wins all pots
   - Split pots with odd chips

#### Category C: Position & Blinds (HIGH PRIORITY)

1. Heads-up button/blind position (button = SB, acts first preflop)
2. BB option (can raise when everyone just calls)
3. Dead button scenarios
4. Blind escalation (tournament mode)
5. Player elimination mid-hand

#### Category D: State Management (CRITICAL PRIORITY)

1. Chip conservation (total chips never change)
2. Pot consistency (pot = sum of all bets)
3. State transitions (PRE_FLOP -> FLOP -> TURN -> RIVER -> SHOWDOWN)
4. Action validity per state
5. Player turn order (clockwise from dealer)

#### Category E: Edge Cases (MEDIUM PRIORITY)

1. Minimum raise rules (must raise at least previous raise amount)
2. Re-raise limits (no-limit vs fixed-limit)
3. String betting prevention
4. Action out of turn handling
5. Disconnection/timeout handling

### 1.3 Sources

- [PokerKit](https://github.com/uoftcprg/pokerkit) - 99% coverage, WSOP hand validation
- [PyPokerEngine](https://github.com/ishikota/PyPokerEngine) - AI development focus
- [danielpaz6/Poker-Hand-Evaluator](https://github.com/danielpaz6/Poker-Hand-Evaluator) - Side pot algorithms
- [Upswing Poker](https://upswingpoker.com/poker-rules/blinds-antes-button/) - Blind/button rules
- [PokerListings](https://www.pokerlistings.com/poker-side-pot-calculator) - All-in/side pot rules

---

## Part 2: Code Divergence Issues Found

### 2.1 Critical Issues (Must Fix)

| # | Issue | Location 1 | Location 2 | Impact |
|---|-------|------------|------------|--------|
| 1 | Raise bet calculation | `poker_engine.py:1139-1148` | `websocket_manager.py:195-198` | Pot grows incorrectly via WebSocket |
| 2 | `current_bet` update on raise | `poker_engine.py:1149` | `websocket_manager.py:197` | Wrong bet tracking via WebSocket |
| 3 | All-in fast-forward missing | `poker_engine.py:1238-1258` | `_advance_state_for_websocket` | **UAT-5 hang bug** |
| 4 | `last_raiser_index` not set | `poker_engine.py:1150` | `websocket_manager.py:200` | BB option broken via WebSocket |

### 2.2 High Priority Issues

| # | Issue | Location 1 | Location 2 | Impact |
|---|-------|------------|------------|--------|
| 5 | Fold doesn't set `has_acted` | `poker_engine.py:1127` | `websocket_manager.py:187` | Potential infinite loop |
| 6 | Hand strength (4 copies, 2 incomplete) | Lines 291, 982, 1437, 1518 | N/A | Wrong analysis for some hands |
| 7 | 0 active players not handled | `poker_engine.py:1191-1215` | `_advance_state_for_websocket` | Edge case crash |

### 2.3 Medium Priority Issues

| # | Issue | Location 1 | Location 2 | Impact |
|---|-------|------------|------------|--------|
| 8 | QC assertions missing | `poker_engine.py:1402-1403` | `websocket_manager.py:1314-1320` | Silent bugs |
| 9 | Return value inconsistency | `_maybe_advance_state` (void) | `_advance_state_for_websocket` (bool) | Confusing API |

---

## Part 3: Consolidation Plan

### Phase 1: Consolidate Action Processing

**Goal**: Single `apply_action()` method called by both REST and WebSocket paths.

**Current State**:

```text
REST API path:
  submit_human_action() -> calls player.bet(), updates state directly
  _process_single_ai_action() -> calls player.bet(), updates state directly

WebSocket path:
  process_ai_turns_with_events() -> DUPLICATES betting logic inline
```

**Target State**:

```text
New method in poker_engine.py:
  apply_action(player_index, action, amount) -> bool
    - Validates action
    - Applies to player (fold/call/raise)
    - Updates pot, current_bet, last_raiser_index
    - Logs event
    - Sets has_acted = True
    - Returns success/failure

All paths call this single method:
  submit_human_action() -> calls apply_action()
  _process_single_ai_action() -> calls apply_action()
  websocket_manager.py -> calls game.apply_action()
```

**Files Changed**:

- `backend/game/poker_engine.py`: Add `apply_action()` method, refactor existing methods
- `backend/websocket_manager.py`: Replace inline logic with `game.apply_action()` calls

### Phase 2: Consolidate State Advancement

**Goal**: Single `_advance_state_core()` method with all edge case handling.

**Current State**:

```text
_maybe_advance_state():
  - Handles single player fold -> award pot
  - Handles 0 active players
  - Handles all-in fast-forward
  - Processes remaining AI actions
  - Recursive call to self

_advance_state_for_websocket():
  - Handles single player fold -> award pot
  - MISSING: 0 active players
  - MISSING: all-in fast-forward
  - Does NOT process AI actions
  - Returns boolean
```

**Target State**:

```text
_advance_state_core(process_ai: bool = True) -> bool:
  - Handles ALL edge cases (single fold, 0 active, all-in)
  - Optionally processes AI actions
  - Returns True if state changed
  - Has QC assertions

_maybe_advance_state():
  - Calls _advance_state_core(process_ai=True)

_advance_state_for_websocket():
  - Calls _advance_state_core(process_ai=False)
```

**Files Changed**:

- `backend/game/poker_engine.py`: Create `_advance_state_core()`, refactor existing methods

### Phase 3: Consolidate Hand Strength Calculation

**Goal**: Single `calculate_hand_strength(score)` function.

**Current State**:

```text
4 separate implementations:
  1. AIStrategy.make_decision_with_reasoning (lines 291-308) - COMPLETE
  2. submit_human_action (lines 982-999) - COMPLETE (duplicate)
  3. _save_hand_on_early_end (lines 1437-1450) - INCOMPLETE
  4. _save_completed_hand (lines 1518-1531) - INCOMPLETE
```

**Target State**:

```python
@staticmethod
def calculate_hand_strength(score: int) -> float:
    """Convert hand evaluator score to 0-1 strength value."""
    if score <= 10:
        return 0.95  # Royal/Straight Flush
    elif score <= 166:
        return 0.90  # Four of a Kind
    elif score <= 322:
        return 0.85  # Full House
    elif score <= 1599:
        return 0.75  # Flush
    elif score <= 1609:
        return 0.70  # Straight
    elif score <= 2467:
        return 0.55  # Three of a Kind
    elif score <= 3325:
        return 0.40  # Two Pair
    elif score <= 6185:
        return 0.25  # One Pair
    else:
        return 0.05  # High Card

# All 4 locations call this single function.
```

**Files Changed**:

- `backend/game/poker_engine.py`: Add static method, update all 4 call sites

### Phase 4: Implement Step Mode (UAT-1 Fix)

**Goal**: Toggle between auto-advance and step-by-step AI turns.

**Implementation**:

```text
Frontend:
  - Add "Step Mode" toggle next to "Show AI Thinking"
  - When enabled, show "Continue" button after each AI action
  - Store preference in Zustand store

Backend (WebSocket):
  - Accept step_mode: bool in WebSocket messages
  - When step_mode=True, send "awaiting_continue" event after AI action
  - Wait for "continue" message before processing next AI

New WebSocket Events:
  - Server -> Client: { type: "awaiting_continue", player_name: "AI-ce" }
  - Client -> Server: { type: "continue" }
```

**Files Changed**:

- `backend/websocket_manager.py`: Add step mode handling
- `frontend/lib/store.ts`: Add stepMode state
- `frontend/lib/websocket.ts`: Handle new events
- `frontend/components/PokerTable.tsx`: Add toggle and Continue button

---

## Part 4: Test Coverage Plan

### 4.1 New Test Files to Create

| File | Purpose | Priority |
|------|---------|----------|
| `tests/test_action_processing.py` | Test `apply_action()` method | CRITICAL |
| `tests/test_state_advancement.py` | Test `_advance_state_core()` | CRITICAL |
| `tests/test_side_pots.py` | Multi-player all-in scenarios | HIGH |
| `tests/test_heads_up.py` | 2-player specific rules | HIGH |
| `tests/test_hand_strength.py` | Hand strength calculation | MEDIUM |
| `tests/test_websocket_flow.py` | WebSocket-specific paths | CRITICAL |

### 4.2 Specific Test Cases

#### test_action_processing.py

```python
# Fold tests
test_fold_sets_inactive()
test_fold_sets_has_acted()
test_fold_logs_event()

# Call tests
test_call_calculates_correct_amount()
test_call_updates_pot()
test_call_handles_partial_call_all_in()

# Raise tests
test_raise_calculates_bet_increment()
test_raise_updates_current_bet()
test_raise_sets_last_raiser_index()
test_raise_resets_other_players_has_acted()
test_raise_handles_all_in_for_less()
```

#### test_state_advancement.py

```python
# Single player remaining
test_advance_when_all_fold_to_one()
test_award_pot_to_last_active()

# All-in scenarios (UAT-5 bug)
test_all_players_all_in_preflop()
test_all_players_all_in_flop()
test_all_players_all_in_turn()
test_fast_forward_deals_remaining_cards()
test_fast_forward_goes_to_showdown()

# Normal advancement
test_preflop_to_flop()
test_flop_to_turn()
test_turn_to_river()
test_river_to_showdown()
```

#### test_side_pots.py

```python
# Basic side pot
test_two_players_different_stacks()
test_three_players_two_stack_sizes()

# Complex side pots
test_four_players_three_stack_sizes()
test_five_players_cascading_all_ins()

# Distribution
test_short_stack_wins_main_only()
test_medium_stack_wins_main_and_side()
test_split_pot_odd_chip_to_button_left()
```

#### test_heads_up.py

```python
# Position rules
test_button_is_small_blind()
test_button_acts_first_preflop()
test_button_acts_last_postflop()

# BB option
test_bb_gets_option_when_button_calls()
test_bb_can_raise_or_check()
```

#### test_websocket_flow.py

```python
# Matches REST behavior
test_websocket_fold_matches_rest()
test_websocket_call_matches_rest()
test_websocket_raise_matches_rest()

# All-in via WebSocket
test_websocket_all_in_single_player()
test_websocket_all_in_multiple_players()
test_websocket_all_in_fast_forward()

# Step mode
test_step_mode_pauses_after_ai()
test_step_mode_continue_advances()
```

### 4.3 Property-Based Tests (Existing Enhancement)

Update `tests/legacy/test_property_based.py`:

```python
# Add these invariants
invariant_chip_conservation()  # Total chips never change
invariant_pot_consistency()    # Pot = sum of bets
invariant_single_current_player()  # 0 or 1 current player
invariant_valid_state_transitions()  # State only moves forward
invariant_action_validity()  # Actions valid for current state
```

---

## Part 5: Implementation Schedule

### Execution Order

```text
Phase 1: Action Consolidation
├── 1.1 Create apply_action() method with tests
├── 1.2 Refactor submit_human_action() to use it
├── 1.3 Refactor _process_single_ai_action() to use it
├── 1.4 Refactor websocket_manager.py to use it
└── 1.5 Run full test suite, verify no regressions

Phase 2: State Advancement Consolidation
├── 2.1 Create _advance_state_core() method with tests
├── 2.2 Refactor _maybe_advance_state() to use it
├── 2.3 Refactor _advance_state_for_websocket() to use it
└── 2.4 Run full test suite, verify UAT-5 is fixed

Phase 3: Hand Strength Consolidation
├── 3.1 Create calculate_hand_strength() function
├── 3.2 Update all 4 call sites
└── 3.3 Add comprehensive tests

Phase 4: Step Mode Implementation
├── 4.1 Backend WebSocket changes
├── 4.2 Frontend store changes
├── 4.3 Frontend UI changes
└── 4.4 Manual UAT testing

Phase 5: Test Suite Enhancement
├── 5.1 Create new test files per 4.1
├── 5.2 Implement test cases per 4.2
├── 5.3 Enhance property-based tests per 4.3
└── 5.4 Achieve >90% code coverage
```

---

## Part 6: Success Criteria

### Code Quality

- [ ] No duplicated action processing logic
- [ ] No duplicated state advancement logic
- [ ] No duplicated hand strength calculation
- [ ] All methods have single responsibility

### Test Coverage

- [ ] >90% code coverage
- [ ] All 4 test files created (4.1)
- [ ] All test cases implemented (4.2)
- [ ] Property-based invariants added (4.3)

### UAT Fixes

- [ ] UAT-1: Step Mode working
- [ ] UAT-5: All-in no longer hangs
- [ ] UAT-11: Analysis modal stable

### Regression

- [ ] All existing tests pass
- [ ] 10K+ property-based scenarios pass
- [ ] Manual play-through of 10+ hands

---

## Appendix A: File Change Summary

| File | Lines Added | Lines Removed | Net Change |
|------|-------------|---------------|------------|
| `poker_engine.py` | ~100 | ~150 | -50 |
| `websocket_manager.py` | ~20 | ~50 | -30 |
| `tests/test_action_processing.py` | ~100 | 0 | +100 |
| `tests/test_state_advancement.py` | ~80 | 0 | +80 |
| `tests/test_side_pots.py` | ~100 | 0 | +100 |
| `tests/test_heads_up.py` | ~50 | 0 | +50 |
| `tests/test_websocket_flow.py` | ~80 | 0 | +80 |
| Frontend (Step Mode) | ~50 | 0 | +50 |
| **Total** | ~580 | ~200 | +380 |

---

## Appendix B: Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Refactoring breaks existing functionality | Run tests after each sub-phase |
| New tests don't catch all edge cases | Use property-based testing for invariants |
| WebSocket flow has untested paths | Add WebSocket-specific integration tests |
| Step Mode affects normal gameplay | Make it opt-in, default to auto-advance |

---

**Document Version History**:

- v1.0 (Dec 8, 2025): Initial comprehensive plan
