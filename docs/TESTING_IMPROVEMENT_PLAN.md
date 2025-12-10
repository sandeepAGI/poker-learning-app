# Testing Improvement Plan

**Date**: December 9, 2025
**Status**: 🎯 **ACTION REQUIRED** - Comprehensive testing overhaul

**Goal**: Build a testing strategy that catches bugs BEFORE users find them.

---

## Phase 1: Fix The Current Bug (1 hour)

### Step 1.1: Understand The Root Cause (15 min)

**Task**: Reproduce the exact bug from user logs

```bash
# Create a manual test script
backend/tests/manual_test_all_in_bug.py
```

```python
# Script to reproduce the infinite loop bug
import sys
sys.path.insert(0, '.')

from game.poker_engine import PokerGame

# Create game
game = PokerGame("TestPlayer", ai_count=3)
game.start_new_hand(process_ai=False)

# Simulate the exact scenario from logs:
# 1. Initial state: Human has stack=1005, current_bet=10 (big blind)
# 2. Human raises to 1015 (trying to go all-in)
# 3. AI tries to respond

# ... detailed reproduction steps
```

**Expected Output**: See the exact failure mode and error message

### Step 1.2: Write a Failing Test (30 min)

**File**: `backend/tests/test_websocket_integration.py`

```python
@pytest.mark.asyncio
async def test_human_all_in_causes_ai_action_failure(self):
    """
    REGRESSION TEST for infinite loop bug.

    This test must FAIL until bug is fixed.
    Tests that when human goes all-in, AI actions don't fail validation.
    """
    game_id = await create_test_game(ai_count=3)

    async with WebSocketTestClient(game_id) as ws:
        await ws.wait_for_event("state_update")
        await ws.drain_events(timeout=2.0)

        current_state = ws.get_latest_state()
        human_stack = current_state["human_player"]["stack"]
        human_current_bet = current_state["human_player"]["current_bet"]

        # Go all-in
        all_in_amount = human_stack + human_current_bet
        await ws.send_action("raise", amount=all_in_amount)

        # Collect all events for analysis
        events = await ws.drain_events(max_events=100, timeout=15.0)

        # Check for infinite loop indicators
        ai_actions = [e for e in events if e.get("type") == "ai_action"]
        player_action_counts = {}
        for action in ai_actions:
            player = action["data"]["player_name"]
            player_action_counts[player] = player_action_counts.get(player, 0) + 1

        # No player should act more than 4 times in one betting round
        for player, count in player_action_counts.items():
            assert count <= 4, f"{player} acted {count} times (infinite loop detected!)"

        # Game should reach showdown or complete
        final_state = ws.get_latest_state()
        assert final_state["state"] in ["showdown", "flop", "turn", "river"], \
            f"Game stuck in {final_state['state']} after all-in"
```

### Step 1.3: Fix The Bug (15 min)

**File**: `backend/websocket_manager.py`

```python
# After line 237 (apply_action call)
result = game.apply_action(...)

# ADD THIS:
if not result["success"]:
    print(f"[WebSocket] ⚠️  AI action FAILED: {result.get('error')}")
    # Force fold as fallback
    result = game.apply_action(player_index=game.current_player_index, action="fold", amount=0)
```

**Verify**: Run the failing test → should pass now

---

## Phase 2: Negative Testing Suite (4 hours)

### Step 2.1: Invalid Action Tests (1 hour)

**File**: `backend/tests/test_invalid_actions.py` (NEW FILE)

```python
class TestInvalidRaiseAmounts:
    """Test that invalid raise amounts are handled gracefully"""

    @pytest.mark.asyncio
    async def test_raise_below_minimum(self):
        """Raise amount below current_bet + big_blind should fail gracefully"""
        game_id = await create_test_game()
        async with WebSocketTestClient(game_id) as ws:
            await ws.wait_for_event("state_update")

            # Try to raise to an amount below minimum
            await ws.send_action("raise", amount=5)  # Too small

            events = await ws.drain_events(timeout=3.0)

            # Should receive error OR action should be rejected
            errors = [e for e in events if e.get("type") == "error"]
            assert len(errors) > 0, "Expected error for invalid raise"

    @pytest.mark.asyncio
    async def test_raise_more_than_stack(self):
        """Raise amount > stack + current_bet should be capped at all-in"""
        # Test that attempting to raise more than you have doesn't break the game
        pass

    @pytest.mark.asyncio
    async def test_raise_exactly_stack(self):
        """Raise amount = stack (without current_bet) should work"""
        # This is the bug we just found!
        pass


class TestInvalidActionSequences:
    """Test invalid action sequences"""

    @pytest.mark.asyncio
    async def test_action_when_not_your_turn(self):
        """Acting when it's not your turn should be rejected"""
        pass

    @pytest.mark.asyncio
    async def test_action_after_already_acted(self):
        """Acting twice in same round should be rejected"""
        pass

    @pytest.mark.asyncio
    async def test_action_after_folding(self):
        """Acting after you've folded should be rejected"""
        pass


class TestRapidActions:
    """Test rapid/duplicate actions"""

    @pytest.mark.asyncio
    async def test_rapid_duplicate_actions(self):
        """Sending same action twice rapidly shouldn't cause issues"""
        pass

    @pytest.mark.asyncio
    async def test_action_spam(self):
        """Spamming actions shouldn't break the game"""
        pass
```

**Target**: 15+ negative tests, all passing

### Step 2.2: Error Recovery Tests (1 hour)

```python
class TestErrorRecovery:
    """Test that errors don't leave game in broken state"""

    @pytest.mark.asyncio
    async def test_failed_action_advances_turn(self):
        """If AI action fails, game should move to next player"""
        pass

    @pytest.mark.asyncio
    async def test_multiple_failures_dont_deadlock(self):
        """Multiple AI action failures in a row shouldn't deadlock"""
        pass

    @pytest.mark.asyncio
    async def test_recovery_after_invalid_human_action(self):
        """Game continues normally after human sends invalid action"""
        pass
```

### Step 2.3: Scenario-Based Failure Tests (2 hours)

```python
class TestCommonFailureScenarios:
    """Test scenarios that commonly cause bugs"""

    @pytest.mark.asyncio
    async def test_all_players_try_to_go_all_in(self):
        """All 4 players going all-in simultaneously"""
        pass

    @pytest.mark.asyncio
    async def test_complex_raise_reraise_sequence(self):
        """Human raises → AI re-raises → Human re-raises → AI all-in → Human calls"""
        pass

    @pytest.mark.asyncio
    async def test_human_goes_all_in_every_hand_for_10_hands(self):
        """Stress test: human all-in strategy for 10 consecutive hands"""
        pass

    @pytest.mark.asyncio
    async def test_minimum_raise_edge_cases(self):
        """Test all edge cases around minimum raise amounts"""
        pass
```

---

## Phase 3: Fuzzing & Property-Based Testing (4 hours)

### Step 3.1: Action Fuzzing (2 hours)

**File**: `backend/tests/test_action_fuzzing.py` (ENHANCE EXISTING)

```python
class TestActionFuzzing:
    """Generate random actions and verify game doesn't break"""

    @pytest.mark.asyncio
    async def test_fuzz_raise_amounts_1000_iterations(self):
        """Generate 1000 random raise amounts, verify no crashes"""
        for i in range(1000):
            game_id = await create_test_game()
            async with WebSocketTestClient(game_id) as ws:
                await ws.wait_for_event("state_update")
                await ws.drain_events(timeout=1.0)

                state = ws.get_latest_state()
                if not state["human_player"]["is_current_turn"]:
                    continue

                # Generate random raise amount (including invalid ones)
                import random
                amount = random.randint(0, state["human_player"]["stack"] * 2)

                await ws.send_action("raise", amount=amount)
                events = await ws.drain_events(timeout=5.0)

                # Verify game didn't crash or deadlock
                assert len(events) > 0, f"Game hung on iteration {i} with amount {amount}"

    @pytest.mark.asyncio
    async def test_fuzz_action_sequences(self):
        """Generate random action sequences, verify consistency"""
        pass
```

### Step 3.2: Property-Based Testing (2 hours)

**File**: `backend/tests/test_invariants.py` (NEW FILE)

```python
import hypothesis
from hypothesis import given, strategies as st

class TestGameInvariants:
    """Test that invariants ALWAYS hold"""

    @given(st.integers(min_value=1, max_value=10000))
    @pytest.mark.asyncio
    async def test_chips_always_conserved(self, seed):
        """Total chips in game should never change"""
        random.seed(seed)
        game_id = await create_test_game()

        async with WebSocketTestClient(game_id) as ws:
            initial_state = await ws.wait_for_event("state_update")
            initial_total = sum(p["stack"] for p in initial_state["data"]["players"]) + initial_state["data"]["pot"]

            # Play for 10 actions
            for _ in range(10):
                # ... random actions

                current_state = ws.get_latest_state()
                current_total = sum(p["stack"] for p in current_state["players"]) + current_state["pot"]

                assert current_total == initial_total, "Chips not conserved!"

    @given(st.integers(min_value=1, max_value=100))
    async def test_player_turn_always_advances(self, seed):
        """current_player_index should always advance or become None"""
        pass

    @given(st.integers(min_value=1, max_value=100))
    async def test_no_action_causes_infinite_loop(self, seed):
        """No action sequence should cause same player to act > 4 times"""
        pass
```

---

## Phase 4: End-to-End Testing (8 hours)

### Step 4.1: Playwright Setup (1 hour)

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### Step 4.2: E2E Test Suite (4 hours)

**File**: `tests/e2e/test_poker_game_e2e.py` (NEW)

```python
from playwright.async_api import async_playwright
import pytest

class TestPokerGameE2E:
    """End-to-end tests using real browser"""

    @pytest.mark.asyncio
    async def test_create_game_and_play_one_hand(self):
        """Full flow: Create game → Play one hand → See result"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to app
            await page.goto("http://localhost:3000")

            # Create game
            await page.click('button:has-text("New Game")')

            # Wait for game to start
            await page.wait_for_selector('.poker-table')

            # Take action (fold)
            await page.click('button:has-text("Fold")')

            # Verify hand completed
            await page.wait_for_selector('.showdown')

            await browser.close()

    @pytest.mark.asyncio
    async def test_go_all_in_and_win(self):
        """E2E: Go all-in and win the hand"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto("http://localhost:3000")
            await page.click('button:has-text("New Game")')
            await page.wait_for_selector('.poker-table')

            # Click all-in button
            await page.click('button:has-text("All In")')

            # Wait for showdown (with timeout to detect hang)
            try:
                await page.wait_for_selector('.showdown', timeout=30000)
            except:
                # Take screenshot for debugging
                await page.screenshot(path='all_in_hang.png')
                raise AssertionError("Game hung after all-in!")

            await browser.close()

    @pytest.mark.asyncio
    async def test_rapid_button_clicks(self):
        """E2E: Rapid button clicking doesn't break UI"""
        pass

    @pytest.mark.asyncio
    async def test_step_mode_full_flow(self):
        """E2E: Enable step mode, play hand, disable step mode"""
        pass
```

**Target**: 20+ E2E tests covering critical user flows

### Step 4.3: Visual Regression Testing (2 hours)

```python
@pytest.mark.asyncio
async def test_all_in_ui_state(self):
    """Verify UI shows correct state after all-in"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # ... go all-in

        # Take screenshot
        await page.screenshot(path='all_in_state.png')

        # Compare with expected (using percy or similar)
        await expect(page).to_have_screenshot('all_in_expected.png')
```

### Step 4.4: Performance Testing (1 hour)

```python
@pytest.mark.asyncio
async def test_action_response_time(self):
    """Actions should complete within 2 seconds"""
    import time

    async with WebSocketTestClient(game_id) as ws:
        start = time.time()
        await ws.send_action("call")
        await ws.drain_events(timeout=10.0)
        end = time.time()

        assert end - start < 2.0, f"Action took {end-start}s (too slow!)"
```

---

## Phase 5: Continuous Testing Infrastructure (4 hours)

### Step 5.1: Pre-Commit Hooks (1 hour)

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running tests before commit..."

# Run fast tests
python -m pytest tests/test_action_processing.py tests/test_invalid_actions.py -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix before committing."
    exit 1
fi

echo "✅ Tests passed!"
```

### Step 5.2: CI/CD Pipeline (2 hours)

```yaml
# .github/workflows/test.yml
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Unit tests
      - name: Run unit tests
        run: python -m pytest tests/test_*.py -v

      # Integration tests
      - name: Run integration tests
        run: python -m pytest tests/test_websocket_integration.py -v

      # Negative tests
      - name: Run negative tests
        run: python -m pytest tests/test_invalid_actions.py -v

      # Fuzzing (subset)
      - name: Run fuzzing tests (100 iterations)
        run: python -m pytest tests/test_action_fuzzing.py::test_fuzz_100 -v

      # E2E tests
      - name: Start backend
        run: cd backend && python main.py &

      - name: Start frontend
        run: cd frontend && npm run dev &

      - name: Run E2E tests
        run: python -m pytest tests/e2e/ -v
```

### Step 5.3: Test Coverage Tracking (1 hour)

```bash
# Generate coverage report
python -m pytest --cov=backend --cov-report=html tests/

# Enforce minimum coverage
python -m pytest --cov=backend --cov-fail-under=80 tests/
```

---

## Success Metrics

### Before Shipping Any Code:

1. **Coverage**:
   - ✅ 80%+ code coverage
   - ✅ 100% of error handling paths tested
   - ✅ 100% of previous bugs have regression tests

2. **Test Counts**:
   - ✅ 20+ negative tests (invalid inputs, errors)
   - ✅ 50+ integration tests (happy + sad paths)
   - ✅ 1000+ fuzzed inputs tested
   - ✅ 20+ E2E tests (real browser)

3. **Quality Metrics**:
   - ✅ 0 bugs found in manual UAT
   - ✅ 0 flaky tests
   - ✅ All tests pass in < 5 minutes

4. **Process**:
   - ✅ Pre-commit hooks run tests
   - ✅ CI/CD runs full suite
   - ✅ Code review includes test review

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Fix current bug | 1 hour | Bug fixed, regression test added |
| Phase 2: Negative tests | 4 hours | 15+ negative tests passing |
| Phase 3: Fuzzing | 4 hours | 1000+ inputs tested |
| Phase 4: E2E tests | 8 hours | 20+ E2E tests passing |
| Phase 5: CI/CD | 4 hours | Automated testing pipeline |
| **TOTAL** | **21 hours** | **Production-ready testing** |

---

## Implementation Order

**Week 1 (THIS WEEK)**:
1. Fix the current infinite loop bug (1 hour) ✅
2. Add 15 negative tests (4 hours) ✅
3. Add action fuzzing (4 hours) ✅

**Week 2 (NEXT WEEK)**:
4. Build E2E test suite (8 hours) ✅
5. Set up CI/CD pipeline (4 hours) ✅

**Total**: 2 weeks to production-ready testing

---

## The New Definition of "Tested"

**Before this plan**:
- ✅ Unit tests pass
- ✅ Integration tests pass
- ❌ Manual testing finds bugs

**After this plan**:
- ✅ Unit tests pass
- ✅ Integration tests pass (happy + sad paths)
- ✅ Negative tests pass (error handling)
- ✅ Fuzzing tests pass (1000+ random inputs)
- ✅ E2E tests pass (real browser)
- ✅ Property tests pass (invariants hold)
- ✅ Manual testing finds ZERO bugs

**Goal**: Manual testing becomes a formality, not bug discovery.

---

## Next Action

**RIGHT NOW**: Execute Phase 1 (fix the bug, add regression test)

**Command**:
```bash
# 1. Create failing test
# 2. Fix the bug
# 3. Verify test passes
# 4. Commit with "Regression test + fix for infinite loop bug"
```

**Then**: Continue with Phase 2 (negative testing suite)

---

**Status**: Ready to execute. All phases detailed and actionable.
