# Test Code Review Guidelines

> **Created:** January 12, 2026
> **Purpose:** Standards for reviewing test code quality in poker application

## Overview

This guide provides poker-specific standards for reviewing test code. Use this checklist when reviewing test PRs to ensure tests are correct, meaningful, and maintainable.

---

## Review Checklist

When reviewing test code (backend or frontend), check ALL of these:

### 1. Correctness

- [ ] **Does the test actually test what it claims?**
  - Test name matches what it tests
  - Assertions validate the intended behavior
  - Test would fail if the feature is broken

- [ ] **Are player indices used correctly?** (Poker-specific)
  - Uses `enumerate()` when iterating players
  - Uses `game.current_player_index` for current player
  - Never assumes fixed player positions

- [ ] **Does it follow poker rules accurately?**
  - Respects turn order (can't act out of turn)
  - Honors game state transitions (can't act after showdown)
  - Validates chip conservation (total chips constant)

- [ ] **Are edge cases covered?**
  - Tests boundary conditions (0 chips, max chips, etc.)
  - Tests error paths (invalid actions, malformed data)
  - Tests race conditions (concurrent actions, network delays)

### 2. Assertions

- [ ] **Are assertions meaningful?** (Not just "no crash")
  - Tests verify specific expected values
  - Error messages are clear and actionable
  - Assertions check actual vs expected

- [ ] **Do assertions check correct data?**
  - For UI tests: Verify displayed text matches backend data
  - For API tests: Verify response structure and values
  - For unit tests: Verify function returns correct result

- [ ] **Are there enough assertions?**
  - Tests verify all important side effects
  - Tests check both positive and negative cases
  - Tests validate complete state, not just one field

### 3. Isolation

- [ ] **Does test depend on other tests?**
  - Can run standalone (no dependencies on test order)
  - Creates its own test data (no shared state)
  - Cleans up after itself (no side effects)

- [ ] **Does it modify global state?**
  - Doesn't change environment variables permanently
  - Doesn't modify singletons or class variables
  - Uses fixtures for setup/teardown

- [ ] **Can it run in parallel?**
  - No race conditions with other tests
  - No conflicts over shared resources (ports, files)
  - Thread-safe and process-safe

### 4. Clarity

- [ ] **Can you understand it in 30 seconds?**
  - Test structure is clear (Arrange-Act-Assert)
  - Variable names are descriptive
  - Complex logic is commented

- [ ] **Is the test intent obvious?**
  - Test name describes scenario
  - Comments explain WHY, not WHAT
  - Test setup is minimal and relevant

- [ ] **Is error output helpful?**
  - Assertion messages include context
  - Debug information is logged
  - Failures are easy to diagnose

---

## Common Mistakes in Poker Tests

### Mistake #1: Incorrect Player Index Usage

```python
# ❌ WRONG - uses same index for all players
for player in game.players:
    game.apply_action(game.current_player_index, "call", 0)

# ✅ CORRECT - uses unique index per player
for player_idx, player in enumerate(game.players):
    if game.current_player_index == player_idx:
        game.apply_action(player_idx, "call", 0)
```

**Why it's wrong:** Iterates over ALL players but uses `current_player_index` for ALL of them. Should either check if it's player's turn OR only process current player.

**How to catch:** Look for `for player in game.players:` followed by `game.current_player_index`

---

### Mistake #2: Always-Passing Assertions

```python
# ❌ WRONG - can never fail
for player in game.players:
    assert player is not None  # Player comes from iteration, always exists

# ✅ CORRECT - validates actual behavior
for player in game.players:
    assert player.stack >= 0, f"{player.name} has negative stack: {player.stack}"
```

**Why it's wrong:** Test can't fail even if code is broken. Provides false confidence.

**How to catch:** Ask "Could this assertion ever fail?" If no, it's useless.

---

### Mistake #3: Turn Order Violations

```python
# ❌ WRONG - doesn't respect turn order
for player in game.players:
    if player.is_active:
        player.make_decision()  # Not their turn!

# ✅ CORRECT - follows game flow
while not game.is_hand_complete():
    current_player = game.get_current_player()
    current_idx = game.current_player_index
    game.apply_action(current_idx, "call", 0)
```

**Why it's wrong:** Poker has strict turn order. Can't just loop over players.

**How to catch:** Any loop over players that calls `apply_action()` without checking turn.

---

### Mistake #4: Fragile Object Identity Searches

```python
# ❌ WRONG - fragile object identity comparison
player_idx = None
for i, p in enumerate(game.players):
    if p == current_player:  # Object identity check!
        player_idx = i
        break

# ✅ CORRECT - use game's built-in indexing
player_idx = game.current_player_index

# OR use stable ID comparison
player_idx = next(
    (i for i, p in enumerate(game.players) if p.player_id == target_id),
    None
)
```

**Why it's wrong:** Object identity (`p == current_player`) breaks if objects are copied or recreated. Use IDs or built-in methods.

**How to catch:** Look for manual player index searches with `==`

---

### Mistake #5: Misleading Variable Names

```python
# ❌ WRONG - implies success but checks receipt
success1, result1 = (True, results[0]) if not isinstance(results[0], Exception) else (False, results[0])
print(f"Action {'SUCCESS' if success1 else 'ERROR'}")

# ✅ CORRECT - clear naming
received1, result1 = (True, results[0]) if not isinstance(results[0], Exception) else (False, results[0])
print(f"Response {'RECEIVED' if received1 else 'EXCEPTION'}")
```

**Why it's wrong:** `success` implies action succeeded, but just checks if WebSocket didn't throw exception.

**How to catch:** Variable names that imply more than they check.

---

## Red Flags in Test Code

Watch for these patterns that indicate problems:

### 🚩 Intermittent Failures

```python
# Test passes 90% of time, fails 10% randomly
# Indicates: Race condition, timing issue, or missing test isolation
```

**Action:** Add deterministic timing (mock time, use events) or fix race condition.

---

### 🚩 Skipped Tests Without Explanation

```python
@pytest.skip  # No reason given!
def test_important_feature():
    pass
```

**Action:** Either fix test, delete it, or add clear skip reason with ticket.

---

### 🚩 Tests That Take >1 Second (Unit Tests)

```python
def test_simple_validation():
    time.sleep(5)  # Why?!
    assert validate_input("test")
```

**Action:** Remove sleeps, use async properly, or mark as `@pytest.mark.slow`.

---

### 🚩 Tests Requiring Specific Order

```python
def test_step_1():
    global shared_state
    shared_state = create_game()

def test_step_2():  # Depends on test_step_1!
    assert shared_state.is_valid
```

**Action:** Use fixtures or delete/combine tests.

---

### 🚩 Tests With No Assertions

```python
def test_game_runs():
    game = PokerGame()
    game.start_hand()
    # Test passes if no exception - but is game state correct?
```

**Action:** Add meaningful assertions or clarify it's a smoke test.

---

## Test Classification

Understand which type of test you're reviewing:

**Unit Tests** (fast, isolated)
- ✅ Test single function/method
- ✅ No external dependencies
- ✅ Run in <100ms each
- ✅ Example: hand evaluator tests

**Integration Tests** (moderate, some dependencies)
- ✅ Test multiple components together
- ✅ May use test fixtures/databases
- ✅ Run in 100ms-1s each
- ✅ Example: game flow tests

**E2E Tests** (slow, full system)
- ✅ Test complete user scenarios
- ✅ Use real browser/network
- ✅ Run in 1s-10s each
- ✅ Example: full game UI tests

**Stress Tests** (very slow, nightly only)
- ✅ Test under load or many iterations
- ✅ May run for minutes
- ✅ Mark with `@pytest.mark.slow`
- ✅ Example: 200-game simulations

---

## Review Process

When reviewing a test PR:

1. **Read the test name** - Does it describe what's tested?
2. **Check the assertions** - Are they meaningful?
3. **Look for anti-patterns** - Any from the list above?
4. **Run the test locally** - Does it pass? Does it test the right thing?
5. **Break the code** - Does the test catch it?
6. **Check coverage** - Are edge cases tested?

## Approval Criteria

✅ **Approve if:**
- All checklist items pass
- No red flags present
- Test intent is clear
- Assertions are meaningful
- Test is properly isolated

❌ **Request changes if:**
- Uses anti-patterns (wrong player indices, always-passing, etc.)
- Misleading variable names or test names
- Missing edge cases or assertions
- Can't run independently
- Takes too long for its type

---

## References

- Poker-specific test patterns: `backend/tests/test_*.py`
- E2E test examples: `tests/e2e/test_critical_flows.py`
- Test organization: `docs/TEST-SUITE-REFERENCE.md`

---

**Last Updated:** January 12, 2026
