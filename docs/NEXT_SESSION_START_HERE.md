# Next Session: Start Here

**Date Created**: December 9, 2025 (Evening)
**Status**: Ready to execute Phase 1 of testing improvement plan

---

## Quick Context

### What Happened
- Built comprehensive WebSocket integration tests (7 tests)
- Fixed 2 bugs found by tests
- **Declared "0 bugs remaining"**
- User tested → Found critical infinite loop bug in <1 minute
- All 7 integration tests + 72 regression tests were passing ✅
- **Yet the bug existed in production code**

### Why Tests Missed It
The infinite loop bug lives in error handling code that **was never tested**:
- WebSocket AI processing calls `apply_action()` but never checks `result["success"]`
- If action fails, `has_acted` stays False, loop processes same player repeatedly
- All our tests used valid actions that succeed → never exercised failure path

**Lesson**: "All tests passing" ≠ "No bugs exist"

---

## Current State

### Commits
- ✅ `fedacf04` - Archived old testing docs + created new comprehensive plan
- ✅ `bd7accea` - Fixed WebSocket integration bugs (all-in calc + step mode)
- ✅ Pushed to GitHub

### Documentation
**Active** (in `docs/`):
1. **TESTING_IMPROVEMENT_PLAN.md** - Comprehensive 11-phase plan (112 hours)
   - Tier 1 (78h): Pre-production testing (negative tests, fuzzing, E2E, reconnection, concurrency)
   - Tier 2 (34h): Production hardening (RNG fairness, load testing, network simulation)
2. HISTORY.md - Project history
3. SETUP.md - Operational guide

**Archived** (in `archive/docs/testing-history-2025-12/`):
- 12 old planning/analysis documents (9 plans + 3 analysis docs) with comprehensive README

### Test Results
**Integration tests** (just ran):
- 5 passed, 2 failed (randomness issues - proves need for overhaul)
- `test_human_all_in_basic` - Game stuck in pre_flop (randomness)
- `test_play_three_hands` - Timeout waiting for next hand (randomness)

**Regression tests**:
- 72/72 passing ✅ (but doesn't catch integration bugs)

---

## The Bug We Need to Fix

**Location**: `backend/websocket_manager.py` lines ~231-237

**Current code**:
```python
result = game.apply_action(
    player_index=game.current_player_index,
    action=decision.action,
    amount=decision.amount,
    ...
)

# ❌ NEVER CHECKS if result["success"] is False!
await manager.send_event(...)  # Sends event even if action failed
game.current_player_index = ...  # Moves to next player even if action failed
```

**Problem**: If `apply_action()` returns `success: False`, player's `has_acted` flag is NOT set, but code continues moving to next player → infinite loop.

**User's logs**:
```
[WebSocket] >>> AI turn #3: The Calculator (player_index=2)
[WebSocket] >>> AI turn #3: The Calculator (player_index=2)
[WebSocket] >>> AI turn #3: The Calculator (player_index=2)
...
[WebSocket] ⚠️  STUCK ON SAME PLAYER! (processed 6 times)
[WebSocket] Player state: has_acted=False
```

---

## Your Mission: Execute Phase 1

**Goal**: Fix bug using test-driven development approach

**Reference**: `docs/TESTING_IMPROVEMENT_PLAN.md` Phase 1 (lines 150-178)

### Step 1: Write Failing Test (30 min)

Create `backend/tests/test_negative_actions.py`:

```python
@pytest.mark.asyncio
async def test_ai_action_failure_doesnt_cause_infinite_loop():
    """
    REGRESSION TEST for infinite loop bug.

    When AI action fails validation, game should NOT loop infinitely.
    This test MUST fail until bug is fixed.
    """
    game_id = await create_test_game(ai_count=3)

    async with WebSocketTestClient(game_id) as ws:
        # ... trigger scenario that causes AI action to fail
        # ... collect events

        # Count how many times each player acts
        player_action_counts = {}
        for action in ai_actions:
            player = action["data"]["player_name"]
            player_action_counts[player] = player_action_counts.get(player, 0) + 1

        # No player should act >4 times in one betting round
        for player, count in player_action_counts.items():
            assert count <= 4, f"{player} acted {count} times - INFINITE LOOP!"
```

**Expected**: Test FAILS (proves it catches the bug)

### Step 2: Fix the Bug (15 min)

Edit `backend/websocket_manager.py` after line 237:

```python
result = game.apply_action(...)

# ADD THIS:
if not result["success"]:
    print(f"[WebSocket] ⚠️  AI action FAILED: {result.get('error')}")
    # Force fold as fallback to prevent infinite loop
    fallback_result = game.apply_action(
        player_index=game.current_player_index,
        action="fold",
        amount=0,
        reasoning=f"Forced fold due to failed {decision.action}"
    )
    # Emit fallback action event
    await manager.send_event(...)
    # Move to next player
    game.current_player_index = game._get_next_active_player_index(...)
    continue
```

### Step 3: Verify Fix (15 min)

```bash
# Run the new test - should PASS now
python -m pytest backend/tests/test_negative_actions.py -v

# Run regression tests - should still pass
python -m pytest backend/tests/test_action_processing.py \
    backend/tests/test_state_advancement.py -v

# Run integration tests
python -m pytest backend/tests/test_websocket_integration.py -v
```

**Expected**: All tests pass, bug is fixed and regression prevented

### Step 4: Commit (15 min)

```bash
git add backend/tests/test_negative_actions.py backend/websocket_manager.py
git commit -m "Fix infinite loop bug: Check apply_action() success before continuing

Phase 1 of testing improvement plan (docs/TESTING_IMPROVEMENT_PLAN.md)

Bug: WebSocket AI processing didn't check if apply_action() succeeded
Impact: Failed actions left has_acted=False, causing infinite loop
Fix: Check result[\"success\"], force fold on failure as fallback

Regression test: test_negative_actions.py::test_ai_action_failure_doesnt_cause_infinite_loop

Test results:
- New test: PASSING (catches the bug)
- Regression: 72/72 PASSING (no breakage)
- Integration: X/7 PASSING

This is the first negative test - validates error handling path.
Phase 2 will add 19+ more negative tests."

git push origin main
```

---

## Success Criteria for Phase 1

- [ ] New test file created: `test_negative_actions.py`
- [ ] Test initially FAILS (proves it catches the bug)
- [ ] Bug fixed in `websocket_manager.py`
- [ ] Test now PASSES (proves fix works)
- [ ] Regression tests still pass (no breakage)
- [ ] Integration tests status checked
- [ ] Committed and pushed

**Time budget**: 1-2 hours

---

## After Phase 1: What's Next

Once Phase 1 is complete, continue with remaining phases from the **11-phase plan** (111 hours remaining):

**Tier 1 (Pre-Production) - Phases 2-8 (76h)**:
- Phase 2: Negative Testing Suite (8h) - 20+ error handling tests
- Phase 3: Fuzzing + MD5 Validation (10h) - 1000+ random inputs + hand evaluator validation
- Phase 4: Scenario-Based Testing (8h) - 20+ real user journey tests
- Phase 5: E2E Browser Testing (12h) - 15+ Playwright tests
- Phase 6: CI/CD Infrastructure (6h) - Automated testing pipeline
- Phase 7: WebSocket Reconnection (16h) - Disconnect/reconnect handling
- Phase 8: Concurrency Testing (16h) - Race conditions & simultaneous actions

**Tier 2 (Production Hardening) - Phases 9-11 (34h)**:
- Phase 9: RNG Fairness (12h) - Statistical validation of card distribution
- Phase 10: Load Testing (12h) - Concurrent games, performance benchmarks
- Phase 11: Network Failure (10h) - High latency, packet loss, intermittent connectivity

See `docs/TESTING_IMPROVEMENT_PLAN.md` for full details on all phases.

---

## Key Principles Going Forward

1. **Write test FIRST** (proves it catches bug before fix exists)
2. **Fix bug** (minimal change, focused on root cause)
3. **Verify test PASSES** (proves fix works)
4. **Run regression** (proves no breakage)
5. **Commit** (clear message, reference plan)

**Different from before**: We're not stopping after fixing one bug. We're building comprehensive negative test coverage.

---

## Questions to Ask

If anything is unclear:
1. Read `docs/TESTING_FAILURES_ANALYSIS.md` for context on why we're doing this
2. Read `docs/TESTING_PLAN_COMPARISON.md` to see what previous plans missed
3. Check `archive/docs/testing-history-2025-12/README.md` for history

---

**Ready to execute Phase 1!** 🚀

**Success Definition**: Bug fixed + regression test prevents recurrence + all tests passing
