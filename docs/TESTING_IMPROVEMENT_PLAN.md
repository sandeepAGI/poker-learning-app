# Comprehensive Testing Improvement Plan

**Date**: December 9, 2025 (Updated with Industry Best Practices)
**Status**: 🎯 **READY TO EXECUTE**

**Goal**: Build production-ready testing that catches bugs BEFORE users find them.

---

## Executive Summary

**Problem**: All tests passing, yet user found critical bug in <1 minute.
**Root Cause**: Tests only validated success paths, never tested error handling or production conditions.
**Solution**: 11-phase plan covering negative testing, fuzzing, E2E, reconnection, concurrency, RNG, and load testing.

**Total Effort**: 112 hours (2-3 months part-time)
**Tier 1 (Pre-Production)**: 78 hours - Required before ANY real users
**Tier 2 (Production Hardening)**: 34 hours - Required for scale & trust

---

## Overview: 11 Phases

| Phase | Name | Hours | Tier | Status |
|-------|------|-------|------|--------|
| 1 | Fix Current Bug + Regression Test | 2 | 1 | Ready |
| 2 | Negative Testing Suite | 8 | 1 | Planned |
| 3 | Fuzzing + MD5 Validation | 10 | 1 | Planned |
| 4 | Scenario-Based Testing | 8 | 1 | Planned |
| 5 | E2E Browser Testing | 12 | 1 | Planned |
| 6 | CI/CD Infrastructure | 6 | 1 | Planned |
| 7 | WebSocket Reconnection Testing | 16 | 1 | Planned |
| 8 | Concurrency & Race Conditions | 16 | 1 | Planned |
| 9 | RNG Fairness Testing | 12 | 2 | Planned |
| 10 | Load & Stress Testing | 12 | 2 | Planned |
| 11 | Network Failure Simulation | 10 | 2 | Planned |

**Tier 1 Total**: 78 hours (critical path to production)
**Tier 2 Total**: 34 hours (production hardening)
**Grand Total**: 112 hours

---

## Tier 1: Pre-Production Testing (78 hours)

### Phase 1: Fix Current Bug + Regression Test (2 hours)

**Goal**: Fix infinite loop bug using test-driven development.

#### Step 1: Write Failing Test (30 min)

**File**: `backend/tests/test_negative_actions.py` (NEW)

```python
import pytest
from test_websocket_integration import WebSocketTestClient, create_test_game

@pytest.mark.asyncio
async def test_ai_action_failure_doesnt_cause_infinite_loop():
    """
    REGRESSION TEST for infinite loop bug.

    When AI action fails validation, game should NOT loop infinitely.
    This test MUST fail until bug is fixed.
    """
    game_id = await create_test_game(ai_count=3)

    async with WebSocketTestClient(game_id) as ws:
        await ws.wait_for_event("state_update")

        # Trigger scenario causing human to go all-in
        state = await ws.wait_for_event("state_update")
        all_in_amount = state["data"]["human_player"]["stack"] + \
                       state["data"]["human_player"]["current_bet"]

        await ws.send_action("raise", amount=all_in_amount)

        # Collect all AI actions
        events = await ws.drain_events(max_events=100, timeout=15.0)
        ai_actions = [e for e in events if e.get("type") == "ai_action"]

        # Count how many times each player acts
        player_action_counts = {}
        for action in ai_actions:
            player = action["data"]["player_name"]
            player_action_counts[player] = player_action_counts.get(player, 0) + 1

        # CRITICAL: No player should act more than 4 times in one betting round
        for player, count in player_action_counts.items():
            assert count <= 4, f"{player} acted {count} times - INFINITE LOOP DETECTED!"

        # Game should eventually complete
        final_state = ws.get_latest_state()
        assert final_state["state"] in ["showdown", "flop", "turn", "river"], \
            f"Game stuck in {final_state['state']}"
```

**Expected**: Test FAILS (proves it catches the bug)

#### Step 2: Fix The Bug (45 min)

**File**: `backend/websocket_manager.py`

Add after line 237 (after `result = game.apply_action(...)`):

```python
# CRITICAL: Check if action was successful
if not result["success"]:
    print(f"[WebSocket] ⚠️  AI action FAILED for {current_player.name}: {result.get('error')}")
    print(f"[WebSocket] Action: {decision.action}, Amount: {decision.amount}")
    print(f"[WebSocket] Player: stack={current_player.stack}, current_bet={current_player.current_bet}")
    print(f"[WebSocket] Game: current_bet={game.current_bet}, pot={game.pot}")

    # Fallback: Force fold to prevent infinite loop
    print(f"[WebSocket] 🔄 Forcing fold as fallback action")
    fallback_result = game.apply_action(
        player_index=game.current_player_index,
        action="fold",
        amount=0,
        hand_strength=decision.hand_strength,
        reasoning=f"Forced fold due to failed {decision.action}"
    )

    # Emit fallback action event
    await manager.send_event(game_id, {
        "type": "ai_action",
        "data": {
            "player_id": current_player.player_id,
            "player_name": current_player.name,
            "action": "fold",
            "amount": 0,
            "reasoning": f"Forced fold (original action failed)",
            "stack_after": current_player.stack,
            "pot_after": game.pot,
            "bet_amount": 0
        }
    })

    # Broadcast updated state
    await manager.broadcast_state(game_id, game, show_ai_thinking)

    # Check if fold triggered showdown
    if fallback_result["triggers_showdown"]:
        break

    # Move to next player
    game.current_player_index = game._get_next_active_player_index(
        game.current_player_index + 1
    )
    continue
```

#### Step 3: Verify (30 min)

```bash
# New test should PASS
python -m pytest backend/tests/test_negative_actions.py::test_ai_action_failure_doesnt_cause_infinite_loop -v

# Regression tests should still pass
python -m pytest backend/tests/test_action_processing.py tests/test_state_advancement.py -v

# Integration tests
python -m pytest backend/tests/test_websocket_integration.py -v
```

#### Step 4: Commit (15 min)

```bash
git add backend/tests/test_negative_actions.py backend/websocket_manager.py
git commit -m "Phase 1 Complete: Fix infinite loop bug + add regression test"
git push origin main
```

**Deliverable**: Bug fixed, regression test prevents recurrence.

---

### Phase 2: Negative Testing Suite (8 hours)

**Goal**: Test error handling paths (currently 0% coverage).

#### 2.1: Invalid Action Tests (3 hours)

**File**: `backend/tests/test_negative_actions.py` (EXPAND)

```python
class TestInvalidRaiseAmounts:
    """Test invalid raise amounts are handled gracefully"""

    @pytest.mark.asyncio
    async def test_raise_below_minimum(self):
        """Raise below current_bet + big_blind should fail gracefully"""
        # Try to raise to 5 when current_bet is 20, big_blind is 10
        # Should be rejected with clear error

    @pytest.mark.asyncio
    async def test_raise_more_than_stack_plus_current_bet(self):
        """Raise exceeding total chips should cap at all-in"""
        # Try to raise 10,000 when you only have 1,000 total
        # Should auto-cap to all-in (1,000)

    @pytest.mark.asyncio
    async def test_raise_exactly_stack_without_current_bet(self):
        """Raise = stack (forgetting current_bet) should still work"""
        # This is the bug we just fixed - validate fix works

    @pytest.mark.asyncio
    async def test_negative_raise_amount(self):
        """Negative amounts should be rejected"""

    @pytest.mark.asyncio
    async def test_zero_raise_amount(self):
        """Zero raise should be rejected"""
```

#### 2.2: Invalid Action Sequence Tests (3 hours)

```python
class TestInvalidActionSequences:
    """Test actions at wrong times are rejected"""

    @pytest.mark.asyncio
    async def test_action_when_not_your_turn(self):
        """Acting out of turn should be rejected"""

    @pytest.mark.asyncio
    async def test_action_after_already_acted(self):
        """Acting twice in same round should be rejected"""

    @pytest.mark.asyncio
    async def test_action_after_folding(self):
        """Folded players can't act"""

    @pytest.mark.asyncio
    async def test_action_after_hand_complete(self):
        """Can't act after showdown"""
```

#### 2.3: Rapid Action Tests (2 hours)

```python
class TestRapidActions:
    """Test rapid/duplicate actions"""

    @pytest.mark.asyncio
    async def test_rapid_duplicate_actions(self):
        """Clicking button 10 times rapidly - only first counts"""

    @pytest.mark.asyncio
    async def test_action_spam_100_per_second(self):
        """Sending 100 actions/second shouldn't crash"""
```

**Deliverable**: 15+ negative tests, all passing. Error handling validated.

---

### Phase 3: Fuzzing + MD5 Validation (10 hours)

**Goal**: Test with random inputs + validate hand evaluator correctness.

#### 3.1: Action Fuzzing (4 hours)

**File**: `backend/tests/test_action_fuzzing.py` (ENHANCE EXISTING)

```python
@pytest.mark.asyncio
async def test_fuzz_raise_amounts_1000_iterations():
    """Generate 1000 random raise amounts (including invalid)"""
    for i in range(1000):
        game_id = await create_test_game()
        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update")

            # Generate RANDOM amount (50% invalid, 50% valid)
            import random
            if random.random() < 0.5:
                # Invalid amounts
                amount = random.choice([
                    -100,  # Negative
                    0,     # Zero
                    random.randint(1, 5),  # Too small
                    state["data"]["human_player"]["stack"] * 10  # Too large
                ])
            else:
                # Valid amounts
                amount = random.randint(20, 1000)

            await ws.send_action("raise", amount=amount)
            events = await ws.drain_events(timeout=5.0)

            # Game should NOT crash or hang
            assert len(events) > 0, f"Game hung on iteration {i} with amount {amount}"

@pytest.mark.asyncio
async def test_fuzz_action_sequences_1000_iterations():
    """Random action sequences (call/fold/raise)"""
    # Generate 1000 random sequences like: raise→call→fold→raise
    # Verify game always completes correctly
```

#### 3.2: MD5 Checksum Validation (4 hours)

**File**: `backend/tests/test_hand_evaluator_validation.py` (NEW)

```python
def test_hand_evaluator_against_reference():
    """
    Validate our hand evaluator against reference implementation.

    Uses phevaluator as reference (industry-standard library).
    """
    from phevaluator import evaluate_cards
    from game.poker_engine import HandEvaluator

    # Test 10,000 random 7-card combinations
    import random
    deck = [f"{r}{s}" for r in "23456789TJQKA" for s in "shdc"]

    mismatches = []
    for i in range(10000):
        cards = random.sample(deck, 7)

        our_score = HandEvaluator.evaluate_hand(cards[:2], cards[2:])
        reference_score = evaluate_cards(*cards)

        # Scores should be identical (or have known mapping)
        if our_score != reference_score:
            mismatches.append({
                "cards": cards,
                "our_score": our_score,
                "reference": reference_score
            })

    assert len(mismatches) == 0, f"Hand evaluator errors: {mismatches[:5]}"

def test_hand_evaluator_checksum():
    """Generate MD5 checksum of all hands for regression testing"""
    import hashlib

    # Generate ordered list of hand strengths for common scenarios
    results = []
    for test_case in get_standard_test_hands():
        score = HandEvaluator.evaluate_hand(test_case["hole"], test_case["board"])
        results.append(f"{test_case['name']}:{score}")

    checksum = hashlib.md5("\n".join(results).encode()).hexdigest()

    # Compare against known good checksum
    EXPECTED_CHECKSUM = "abc123..."  # Update after first run
    assert checksum == EXPECTED_CHECKSUM, \
        f"Hand evaluator changed! New checksum: {checksum}"
```

#### 3.3: Property-Based Enhancement (2 hours)

**File**: `backend/tests/test_property_based.py` (ENHANCE)

Add new invariants:
```python
def invariant_no_infinite_loops(game_history):
    """No player should act more than 4 times per betting round"""
    for round_actions in game_history.betting_rounds:
        player_counts = {}
        for action in round_actions:
            player_counts[action.player] = player_counts.get(action.player, 0) + 1

        for player, count in player_counts.items():
            assert count <= 4, f"Infinite loop: {player} acted {count} times"

def invariant_failed_actions_advance_turn(game_history):
    """If action fails, turn must still advance"""
    for action_result in game_history.all_actions:
        if not action_result.success:
            # Next action should be different player
            assert action_result.next_player != action_result.current_player
```

**Deliverable**: 1000+ fuzzed inputs tested, hand evaluator validated, enhanced invariants.

---

### Phase 4: Scenario-Based Testing (8 hours)

**Goal**: Test real user journeys (not isolated actions).

**File**: `backend/tests/test_user_scenarios.py` (NEW)

#### 4.1: Multi-Hand Scenarios (3 hours)

```python
@pytest.mark.asyncio
async def test_go_all_in_every_hand_for_10_hands():
    """Aggressive strategy: all-in every hand for 10 hands"""
    game_id = await create_test_game()
    async with WebSocketTestClient(game_id) as ws:
        for hand_num in range(10):
            # Wait for your turn
            state = await ws.wait_for_event("state_update")

            # Go all-in
            all_in = state["data"]["human_player"]["stack"] + \
                    state["data"]["human_player"]["current_bet"]
            await ws.send_action("raise", amount=all_in)

            # Wait for hand to complete
            await ws.drain_events(timeout=10.0)

            # Start next hand
            await ws.send_next_hand()

@pytest.mark.asyncio
async def test_conservative_strategy_fold_90_percent():
    """Conservative strategy: fold 90% of hands"""
    # Play 20 hands, fold 18 of them, call 2
```

#### 4.2: Complex Betting Sequences (3 hours)

```python
@pytest.mark.asyncio
async def test_complex_raise_reraise_all_in_sequence():
    """Human raises → AI re-raises → Human re-raises → AI all-in → Human calls"""
    # This is a 5-action sequence - tests state management

@pytest.mark.asyncio
async def test_all_players_go_all_in_simultaneously():
    """Trigger scenario where all 4 players go all-in"""
    # Tests side pot calculation, showdown with multiple all-ins
```

#### 4.3: Edge Case Scenarios (2 hours)

```python
@pytest.mark.asyncio
async def test_minimum_raise_edge_cases():
    """Test all edge cases around minimum raise amounts"""

@pytest.mark.asyncio
async def test_ui_sends_slightly_wrong_amounts():
    """Simulate frontend bug: sends stack instead of stack+current_bet"""
    # Should auto-correct or reject gracefully
```

**Deliverable**: 20+ scenario tests covering real user flows.

---

### Phase 5: E2E Browser Testing (12 hours)

**Goal**: Test full stack (frontend → WebSocket → backend) with real browser.

#### 5.1: Playwright Setup (2 hours)

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

#### 5.2: Critical User Flows (6 hours)

**File**: `tests/e2e/test_poker_game.py` (NEW)

```python
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_create_game_play_3_hands_quit():
    """Full flow: Create → Play 3 hands → Quit"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate
        await page.goto("http://localhost:3000")

        # Create game
        await page.click('button:has-text("New Game")')
        await page.wait_for_selector('.poker-table')

        # Play 3 hands
        for i in range(3):
            await page.click('button:has-text("Call")')
            await page.wait_for_selector('.showdown', timeout=30000)
            await page.click('button:has-text("Next Hand")')

        # Quit
        await page.click('button:has-text("Quit")')

        await browser.close()

@pytest.mark.asyncio
async def test_go_all_in_and_verify_no_hang():
    """Critical: All-in button works and doesn't hang"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto("http://localhost:3000")
        await page.click('button:has-text("New Game")')
        await page.wait_for_selector('.poker-table')

        # Click all-in
        await page.click('button:has-text("All In")')

        # Verify showdown reached within 30s (not infinite loop)
        try:
            await page.wait_for_selector('.showdown', timeout=30000)
        except:
            # Take screenshot for debugging
            await page.screenshot(path='all_in_hang.png')
            raise AssertionError("Game hung after all-in!")

        await browser.close()

@pytest.mark.asyncio
async def test_step_mode_full_flow():
    """Enable step mode → Play hand → Disable"""

@pytest.mark.asyncio
async def test_rapid_button_clicking():
    """Click buttons rapidly - shouldn't break UI"""
```

#### 5.3: Visual Regression (2 hours)

```python
@pytest.mark.asyncio
async def test_poker_table_visual_snapshot():
    """Take screenshot, compare against baseline"""
    # Ensures UI doesn't break unexpectedly
```

#### 5.4: Error State Testing (2 hours)

```python
@pytest.mark.asyncio
async def test_backend_unavailable():
    """Frontend handles backend unavailable gracefully"""

@pytest.mark.asyncio
async def test_websocket_disconnect_shows_error():
    """Disconnect → User sees error message"""
```

**Deliverable**: 15+ E2E tests, full stack validated.

---

### Phase 6: CI/CD Infrastructure (6 hours)

**Goal**: Automate testing pipeline.

#### 6.1: Pre-Commit Hooks (1 hour)

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running pre-commit tests..."

# Fast tests only (<30s)
python -m pytest backend/tests/test_action_processing.py \
    backend/tests/test_state_advancement.py -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix before committing."
    exit 1
fi

echo "✅ Tests passed!"
```

#### 6.2: GitHub Actions CI/CD (3 hours)

**File**: `.github/workflows/test.yml` (NEW)

```yaml
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Backend tests
      - name: Install Python dependencies
        run: cd backend && pip install -r requirements.txt

      - name: Run unit tests
        run: python -m pytest backend/tests/test_*.py -v

      - name: Run integration tests
        run: python -m pytest backend/tests/test_websocket_integration.py -v

      - name: Run negative tests
        run: python -m pytest backend/tests/test_negative_actions.py -v

      - name: Run fuzzing tests (100 iterations)
        run: python -m pytest backend/tests/test_action_fuzzing.py::test_fuzz_100 -v

      # Frontend tests
      - name: Install Node dependencies
        run: cd frontend && npm install

      - name: Frontend build
        run: cd frontend && npm run build

      # E2E tests
      - name: Start backend
        run: cd backend && python main.py &

      - name: Start frontend
        run: cd frontend && npm run dev &

      - name: Run E2E tests
        run: npx playwright test
```

#### 6.3: Coverage Tracking (2 hours)

```bash
# Generate coverage report
python -m pytest --cov=backend --cov-report=html backend/tests/

# Enforce minimum coverage
python -m pytest --cov=backend --cov-fail-under=80 backend/tests/
```

**Deliverable**: Automated testing on every commit.

---

### Phase 7: WebSocket Reconnection Testing (16 hours)

**Goal**: Test disconnect/reconnect scenarios (CRITICAL production gap).

**Why Critical**: Real users disconnect (network issues, phone calls). Without this, game crashes.

**File**: `backend/tests/test_websocket_reliability.py` (NEW)

#### 7.1: Basic Reconnection (4 hours)

```python
@pytest.mark.asyncio
async def test_reconnect_after_disconnect_mid_hand():
    """Player disconnects mid-hand, reconnects, state restored"""
    game_id = await create_test_game()

    async with WebSocketTestClient(game_id) as ws:
        # Play a few actions
        await ws.send_action("call")
        state_before = ws.get_latest_state()

        # Simulate disconnect
        await ws.disconnect()
        await asyncio.sleep(5)

        # Reconnect
        ws2 = WebSocketTestClient(game_id)
        await ws2.connect()

        # Verify state restored
        state_after = await ws2.wait_for_event("state_update")
        assert state_after["data"]["pot"] == state_before["data"]["pot"]
        assert state_after["data"]["hand_count"] == state_before["data"]["hand_count"]

@pytest.mark.asyncio
async def test_reconnect_after_30_second_disconnect():
    """Longer disconnect - session still valid"""
```

#### 7.2: Exponential Backoff (4 hours)

```python
@pytest.mark.asyncio
async def test_exponential_backoff_reconnection():
    """Client retries with exponential backoff: 1s, 2s, 4s, 8s"""
    # Implement in frontend/lib/websocket.ts
    # Test that reconnection attempts follow exponential pattern

@pytest.mark.asyncio
async def test_max_reconnect_attempts():
    """After 5 failures, show "Unable to connect" error"""
```

#### 7.3: Missed Notification Recovery (4 hours)

```python
@pytest.mark.asyncio
async def test_missed_notifications_catch_up():
    """After disconnect, client receives all missed events"""
    game_id = await create_test_game()

    async with WebSocketTestClient(game_id) as ws:
        await ws.send_action("call")

        # Disconnect
        await ws.disconnect()

        # Let AI play 3 turns while disconnected
        await asyncio.sleep(5)

        # Reconnect
        ws2 = WebSocketTestClient(game_id)
        await ws2.connect()

        # Should receive all 3 missed ai_action events
        events = await ws2.drain_events(timeout=3.0)
        ai_actions = [e for e in events if e.get("type") == "ai_action"]
        assert len(ai_actions) >= 3, "Didn't catch up on missed events"
```

#### 7.4: Backend Session Management (4 hours)

```python
# Implement in backend/websocket_manager.py

class WebSocketSessionManager:
    """Manage sessions for reconnection"""
    def __init__(self):
        self.sessions = {}  # game_id → session_data

    def create_session(self, game_id, connection_id):
        """Create session on first connect"""
        self.sessions[game_id] = {
            "connection_id": connection_id,
            "last_seen": time.time(),
            "missed_events": []
        }

    def on_disconnect(self, game_id):
        """Mark session as disconnected, keep state for 5 minutes"""
        self.sessions[game_id]["disconnected_at"] = time.time()

    def on_reconnect(self, game_id, new_connection_id):
        """Restore session, send missed events"""
        session = self.sessions[game_id]

        # Send all missed events
        for event in session["missed_events"]:
            await send_event(game_id, event)

        session["missed_events"] = []
        session["connection_id"] = new_connection_id
```

**Deliverable**: Reconnection works, sessions preserved, missed events caught up.

---

### Phase 8: Concurrency & Race Conditions (16 hours)

**Goal**: Test simultaneous actions (CRITICAL production gap).

**Why Critical**: Multiple players can act simultaneously. Race conditions = corrupted game state.

**File**: `backend/tests/test_concurrency.py` (NEW)

#### 8.1: Simultaneous Actions (6 hours)

```python
@pytest.mark.asyncio
async def test_two_connections_same_game_simultaneous_actions():
    """Two WebSocket connections send actions at exactly the same time"""
    game_id = await create_test_game(ai_count=2)

    async with WebSocketTestClient(game_id) as ws1, \
               WebSocketTestClient(game_id) as ws2:

        # Both send action simultaneously
        results = await asyncio.gather(
            ws1.send_action("fold"),
            ws2.send_action("call"),
            return_exceptions=True
        )

        # Only one should succeed, other rejected
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) == 1, "Both actions processed - race condition!"

        # Both clients see same final state
        state1 = await ws1.wait_for_event("state_update")
        state2 = await ws2.wait_for_event("state_update")
        assert state1 == state2

@pytest.mark.asyncio
async def test_rapid_action_spam_100_per_second():
    """Player clicks button 100 times in 1 second"""
    game_id = await create_test_game()

    async with WebSocketTestClient(game_id) as ws:
        # Send 100 fold actions rapidly
        tasks = [ws.send_action("fold") for _ in range(100)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Only first action should process, rest ignored
        events = await ws.drain_events(timeout=3.0)
        state_updates = [e for e in events if e.get("type") == "state_update"]

        # Should see consistent state, not 100 folds
        assert len(state_updates) < 10, "Too many state updates - race condition"
```

#### 8.2: State Transition Race Conditions (6 hours)

```python
@pytest.mark.asyncio
async def test_action_during_state_transition():
    """Player sends action while game is transitioning pre_flop → flop"""
    # This is tricky: action arrives while state is changing
    # Should be queued or rejected gracefully, not cause corruption

@pytest.mark.asyncio
async def test_concurrent_game_creation():
    """10 users create games simultaneously"""
    # Test game ID generation doesn't collide
    tasks = [create_test_game() for _ in range(10)]
    game_ids = await asyncio.gather(*tasks)

    # All IDs should be unique
    assert len(set(game_ids)) == 10, "Game ID collision!"
```

#### 8.3: Thread Safety (4 hours)

```python
# Add locking to backend/websocket_manager.py

import asyncio

class ThreadSafeGameManager:
    def __init__(self):
        self.locks = {}  # game_id → asyncio.Lock

    async def execute_action(self, game_id, action_fn):
        """Execute action with lock to prevent race conditions"""
        if game_id not in self.locks:
            self.locks[game_id] = asyncio.Lock()

        async with self.locks[game_id]:
            # Only one action per game can execute at a time
            return await action_fn()

# Usage in websocket_manager.py:
async def handle_action(game_id, action):
    async def action_fn():
        game = games[game_id]
        result = game.apply_action(...)
        return result

    return await thread_safe_manager.execute_action(game_id, action_fn)
```

**Deliverable**: Race conditions prevented, simultaneous actions handled correctly.

---

## Tier 2: Production Hardening (34 hours)

### Phase 9: RNG Fairness Testing (12 hours)

**Goal**: Validate random number generation is fair.

**Why Important**: Player trust. Proves card distribution is actually random.

**File**: `backend/tests/test_rng_fairness.py` (NEW)

#### 9.1: Statistical Tests (6 hours)

```python
def test_card_distribution_chi_squared():
    """Chi-squared test: cards distributed uniformly"""
    from scipy.stats import chisquare

    # Deal 10,000 hands, track each card frequency
    card_counts = {}
    for _ in range(10000):
        game = PokerGame("Test", ai_count=3)
        game.start_new_hand(process_ai=False)

        for player in game.players:
            for card in player.hole_cards:
                card_counts[card] = card_counts.get(card, 0) + 1

    # Expected: each card appears ~1538 times (10000 * 4 * 2 / 52)
    observed = list(card_counts.values())
    expected = [1538] * 52

    _, p_value = chisquare(observed, expected)

    # p > 0.05 means distribution is random (95% confidence)
    assert p_value > 0.05, f"Card distribution not random! p={p_value}"

def test_hand_strength_distribution_matches_theory():
    """Hand strengths match theoretical probabilities"""
    # Royal Flush: 0.00015%
    # Straight Flush: 0.00139%
    # Four of a Kind: 0.0240%
    # ... etc

    hand_counts = {"royal_flush": 0, "straight_flush": 0, ...}

    # Deal 100,000 hands
    for _ in range(100000):
        # ... deal and evaluate
        pass

    # Compare observed vs theoretical
    for hand_type, count in hand_counts.items():
        observed_pct = count / 100000
        theoretical_pct = THEORETICAL_PROBABILITIES[hand_type]

        # Should be within 10% of theoretical
        assert abs(observed_pct - theoretical_pct) < theoretical_pct * 0.1
```

#### 9.2: Diehard Tests (4 hours)

```python
def test_shuffle_randomness_diehard():
    """Run Diehard statistical test suite on shuffle algorithm"""
    # Diehard is industry standard for RNG testing
    from dieharder import run_diehard_tests

    # Generate 1,000,000 random shuffles
    shuffles = []
    for _ in range(1000000):
        deck = Deck()
        deck.shuffle()
        shuffles.append(deck.cards)

    # Run Diehard tests
    results = run_diehard_tests(shuffles)

    # All tests should pass
    assert results.all_passed, f"Diehard tests failed: {results.failures}"
```

#### 9.3: Pattern Detection (2 hours)

```python
def test_no_pattern_in_consecutive_hands():
    """Verify no repeating patterns in consecutive deals"""
    previous_hands = []

    for i in range(1000):
        game = PokerGame("Test", ai_count=3)
        game.start_new_hand(process_ai=False)

        current_hand = [p.hole_cards for p in game.players]

        # Check if this hand repeats any previous hand
        assert current_hand not in previous_hands, \
            f"Hand {i} is a repeat! RNG not random."

        previous_hands.append(current_hand)
```

**Deliverable**: RNG validated as statistically random.

---

### Phase 10: Load & Stress Testing (12 hours)

**Goal**: Determine system limits (how many concurrent games/players).

**File**: `tests/load/test_load_testing.py` (NEW)

#### 10.1: Concurrent Games (4 hours)

```python
@pytest.mark.asyncio
async def test_10_concurrent_games():
    """10 games running simultaneously"""
    tasks = []
    for i in range(10):
        async def play_game():
            game_id = await create_test_game()
            async with WebSocketTestClient(game_id) as ws:
                for _ in range(3):  # Play 3 hands
                    await ws.send_action("call")
                    await ws.drain_events(timeout=10.0)
                    await ws.send_next_hand()

        tasks.append(play_game())

    # All 10 games should complete without timeout
    await asyncio.gather(*tasks, timeout=120.0)

@pytest.mark.asyncio
async def test_100_concurrent_games():
    """Scale test: 100 games simultaneously"""
    # Measure: response time, memory usage, CPU usage
```

#### 10.2: Performance Benchmarking (4 hours)

```python
def test_response_time_vs_load():
    """Measure response time as load increases"""
    results = []

    for num_games in [1, 5, 10, 25, 50, 100]:
        start = time.time()

        # Create N games, measure time
        for _ in range(num_games):
            game = PokerGame("Test", ai_count=3)
            game.start_new_hand()

        elapsed = time.time() - start
        avg_per_game = elapsed / num_games

        results.append({
            "games": num_games,
            "total_time": elapsed,
            "avg_per_game": avg_per_game
        })

    # Response time shouldn't degrade >50% at high load
    baseline = results[0]["avg_per_game"]
    worst = results[-1]["avg_per_game"]
    assert worst < baseline * 1.5, f"Performance degraded {worst/baseline}x"
```

#### 10.3: Stress Testing with Locust (4 hours)

```python
# tests/load/locustfile.py (NEW)
from locust import User, task, between

class PokerPlayer(User):
    wait_time = between(1, 3)

    @task
    def play_hand(self):
        # Create game
        response = self.client.post("/games", json={"ai_count": 3})
        game_id = response.json()["game_id"]

        # Connect via WebSocket
        # Play 3 hands
        # Measure latency

# Run: locust -f locustfile.py --users 100 --spawn-rate 10
```

**Deliverable**: Know system limits, performance benchmarks.

---

### Phase 11: Network Failure Simulation (10 hours)

**Goal**: Test game works under poor network conditions.

**File**: `backend/tests/test_network_conditions.py` (NEW)

#### 11.1: High Latency (3 hours)

```python
@pytest.mark.asyncio
async def test_high_latency_500ms():
    """Game works with 500ms latency"""
    # Add artificial 500ms delay to WebSocket messages

    async def delayed_send(ws, action):
        await asyncio.sleep(0.5)
        await ws.send_action(action)

    game_id = await create_test_game()
    async with WebSocketTestClient(game_id) as ws:
        await delayed_send(ws, "call")

        # Game should complete, just slower
        events = await ws.drain_events(timeout=20.0)  # Longer timeout
        assert len(events) > 0
```

#### 11.2: Packet Loss (4 hours)

```python
@pytest.mark.asyncio
async def test_packet_loss_10_percent():
    """Game works with 10% packet loss"""
    # Randomly drop 10% of WebSocket messages

    class PacketLossWebSocket(WebSocketTestClient):
        async def send_action(self, action, amount=None):
            import random
            if random.random() < 0.1:
                print("Dropped packet!")
                return  # Drop this message
            await super().send_action(action, amount)

    # Game should still complete (with retries)
```

#### 11.3: Intermittent Connectivity (3 hours)

```python
@pytest.mark.asyncio
async def test_intermittent_connectivity():
    """Connection drops every 30s for 5s"""
    # Simulate flaky WiFi

    async def disconnect_periodically(ws):
        while True:
            await asyncio.sleep(30)
            await ws.disconnect()
            await asyncio.sleep(5)
            await ws.connect()

    # Game should pause/resume gracefully
```

**Deliverable**: Game works under poor network conditions.

---

## Implementation Timeline

### Month 1: Foundation (Tier 1 Phases 1-3)
**Week 1**: Phase 1 (Fix bug) + Phase 2 (Negative tests)
**Week 2**: Phase 3 (Fuzzing + MD5 validation)
**Week 3**: Phase 3 continued
**Week 4**: Buffer/catch-up

**Total**: 20 hours, bug fixed + error handling validated

### Month 2: Integration (Tier 1 Phases 4-6)
**Week 5**: Phase 4 (Scenario testing)
**Week 6**: Phase 5 (E2E testing)
**Week 7**: Phase 5 continued + Phase 6 (CI/CD)
**Week 8**: Buffer/catch-up

**Total**: 26 hours, full stack tested + automated

### Month 3: Production Readiness (Tier 1 Phases 7-8)
**Week 9**: Phase 7 (WebSocket reconnection)
**Week 10**: Phase 7 continued
**Week 11**: Phase 8 (Concurrency)
**Week 12**: Phase 8 continued

**Total**: 32 hours, production-ready

**Milestone**: 78 hours, ready for real users

### Month 4+ (Optional): Production Hardening (Tier 2)
**Phase 9**: RNG fairness (12h)
**Phase 10**: Load testing (12h)
**Phase 11**: Network failure (10h)

**Total**: 34 hours, enterprise-grade

---

## Success Criteria

### Tier 1 (Pre-Production) - REQUIRED
- [ ] Bug fixed with regression test (Phase 1)
- [ ] 20+ negative tests passing (Phase 2)
- [ ] 1000+ fuzzed inputs tested (Phase 3)
- [ ] Hand evaluator validated against reference (Phase 3)
- [ ] 20+ scenario tests passing (Phase 4)
- [ ] 15+ E2E tests passing (Phase 5)
- [ ] CI/CD running on every commit (Phase 6)
- [ ] WebSocket reconnection works (Phase 7)
- [ ] Concurrency race conditions prevented (Phase 8)
- [ ] **UAT finds 0 bugs** (ultimate test)

### Tier 2 (Production Hardening) - RECOMMENDED
- [ ] RNG validated as statistically random (Phase 9)
- [ ] System limits known (100+ concurrent games) (Phase 10)
- [ ] Works under poor network conditions (Phase 11)

---

## Key Metrics

| Metric | Before | Tier 1 Target | Tier 2 Target |
|--------|--------|---------------|---------------|
| **Code Coverage** | ~60% | 80%+ | 85%+ |
| **Error Path Coverage** | 0% | 50%+ | 75%+ |
| **Integration Tests** | 7 | 50+ | 75+ |
| **Negative Tests** | 0 | 20+ | 30+ |
| **E2E Tests** | 0 | 15+ | 25+ |
| **Concurrency Tests** | 0 | 10+ | 15+ |
| **UAT Bugs Found** | 4+ | 0-1 | 0 |

---

## Next Steps

1. **Read this plan** - Understand full scope (78h Tier 1, 34h Tier 2)
2. **Execute Phase 1** - Fix bug + regression test (2h)
3. **Decide on scope** - Tier 1 only? Or Tier 1 + 2?
4. **Track progress** - Mark phases complete in this document
5. **Re-evaluate after Tier 1** - If UAT finds 0 bugs, declare victory

**Start here**: Phase 1 (Fix Current Bug + Regression Test)

---

**Version**: 2.0 (Enhanced with industry best practices)
**Last Updated**: December 9, 2025
**Status**: Ready to execute
