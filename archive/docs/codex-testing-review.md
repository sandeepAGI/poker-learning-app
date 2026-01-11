# Codex Testing Review

_Date: January 15, 2026_

This note captures coverage gaps I found while auditing both the backend poker engine tests and the frontend/UI test suites. Each item ties back to a Texas Hold'em rule or user-facing behavior, cites the implementation, and points out the missing test coverage.

## Backend Poker Rule Coverage Gaps

1. **Short-stack players are forced to sit out permanently**  
   - Implementation: `backend/game/poker_engine.py:124-131` marks a player inactive whenever their stack drops below $5 during `reset_for_new_hand`, and `_post_blinds` never tries to post a partial blind for them. A quick repro (`PYTHONPATH=backend python …`) shows a 3-chip player becomes inactive immediately.  
   - Tests: `backend/tests/test_short_stack_actions.py:1-41` only checks submitting `call`/`raise` while the hand is in progress. There is no regression test for the next-hand path where Texas Hold'em allows partial blinds/all-ins.

2. **Odd-chip remainder logic never exercises real split pots**  
   - Implementation: `_award_pot_at_showdown()` calculates `pot_difference` and distributes remainders by dealer order (`backend/game/poker_engine.py:1594-1657`).  
   - Tests: `backend/tests/test_odd_chip_distribution.py:26-85` sets up a 2-player tie and never touches scenarios with 3+ winners, side pots, or partial blind remainders. Any regression in the dealer-order tie break would slip through.

3. **Minimum-raise reset per street is untested**  
   - Implementation: `_advance_state_core()` clears `last_raise_amount` whenever the state advances (`backend/game/poker_engine.py:1527-1559`). That is how Hold'em rules reset the minimum raise when a new street starts.  
   - Tests: every check in `backend/tests/test_minimum_raise_rules.py:14-118` stays in PRE_FLOP, so a bug leaving `last_raise_amount` intact across streets would not fail a test.

4. **Folded-but-invested players are never validated in side pots**  
   - Implementation: `determine_winners_with_side_pots()` deliberately includes folded players when summing invested chips while excluding them from eligible winners (`backend/game/poker_engine.py:236-304`).  
   - Tests: files such as `backend/tests/test_side_pots.py:17-109` and `backend/tests/test_side_pot_integration.py:1-33` keep every participant active. We never cover the Texas Hold'em rule that folded chips stay in the pot but cannot win, so a future refactor that filters on `is_active` would go unnoticed.

5. **"Table collapses" (only one stack left) have no regression test**  
   - Implementation: `_post_blinds()` short-circuits when `players_with_chips_count < 2` (`backend/game/poker_engine.py:1043-1124`) rather than throwing.  
   - Tests: a repository-wide search for `players_with_chips_count` in `backend/tests` returns nothing, so we never assert that the engine gracefully ends the game once everyone but one player busts.

## Frontend / UI Test Coverage Gaps

1. **Only one frontend unit test exists, and it never renders the table**  
   - File `frontend/__tests__/short-stack-logic.test.ts:1-120` just compares two booleans (`stack > 0` vs. `stack >= callAmount`). It never mounts `PokerTable`, the action buttons, or the Zustand store that actually compute `canCall`/`canRaise`. None of the `PokerTable` safeguards around `isEliminated`, `isWaitingAllIn`, or the raise slider (`frontend/components/PokerTable.tsx:32-205`) are under unit test.

2. **Short-stack E2E tests are placeholders**  
   - `tests/e2e/test_short_stack_ui_fix.py:1-87` immediately calls `pytest.skip("Needs game state manipulation feature for e2e testing")` in all three tests. As a result, we are not verifying the UI regression the backend already fixed (allowing all-ins when `stack < callAmount`).

3. **Winner modal split-pot logic is untested**  
   - The component supports `MultipleWinnersInfo` with `Split Pot!` UI (`frontend/components/WinnerModal.tsx:1-150`), but no test looks for that copy. A repo-wide search for `Split Pot` or for `[data-testid="winner-0"]` in the test suite returns nothing (`rg -n "Split Pot" tests` → empty). The only references to `winner-modal` in tests (`tests/e2e/test_responsive_design.py:1-76`, `tests/e2e/test_card_sizing.py:1-80`) simply wait for the modal and click "Next Hand" while collecting screenshots.

4. **Raise-slider constraints and last-raise handling never get exercised in UI tests**  
   - PokerTable caps raise input between `minRaise` and `maxRaise` and derives `minRaise` from `gameState.last_raise_amount` (`frontend/components/PokerTable.tsx:104-150`). The only tests touching `minRaise` are the synthetic booleans in `frontend/__tests__/short-stack-logic.test.ts`, so there is no coverage that the slider, "All In" button, or amount reset logic honor the backend’s minimum-raise rules.

5. **WebSocket step-mode / reconnection UI is untested**  
   - The Zustand store and `PokerWebSocket` ship features like step-mode pausing, `sendContinue`, auto-resume notices, and exponential reconnect (`frontend/lib/store.ts:28-158`, `frontend/lib/websocket.ts:1-170`). There are no unit tests referencing `PokerWebSocket`, `sendContinue`, or `toggleStepMode` (verified via `rg -n "PokerWebSocket" tests` and `rg -n "sendContinue" tests` → no hits). E2E tests never put the client into awaiting-continue state, so we have zero automated confidence that the UI handles these Texas Hold'em pacing scenarios.

6. **Several Playwright suites rely on manual inspection instead of assertions**  
   - `tests/e2e/test_responsive_design.py:1-90` and `tests/e2e/test_card_sizing.py:1-120` launch headed browsers, take screenshots, and print measurements without asserting pass/fail thresholds. They require the human reviewer to inspect `/tmp/*.png` manually, so regressions in mobile card layout or modal pointer events would not fail CI.

## Recommended Next Steps

1. **Add backend regression tests for each uncovered rule**  
   - Reproduce the short-stack carry-over by starting a hand, busting down to < SB, calling `start_new_hand`, and asserting `is_active` stays true.  
   - Extend existing side-pot tests to include folded players and 3-way ties so `_award_pot_at_showdown`’s odd-chip logic is exercised.  
   - Write a street-transition test that raises pre-flop, advances to the flop, and verifies the next raise may use `big_blind` as the increment.

2. **Invest in deterministic frontend fixtures**  
   - Provide a backend hook or fixture to set chip stacks and current bets so the short-stack E2E suite can stop skipping.  
   - Add unit/component tests (React Testing Library) for `PokerTable` and `WinnerModal` so we can assert on button enablement, split-pot copy, and raise-slider bounds without spinning up Playwright.

3. **Cover WebSocket/step-mode flows**  
   - Unit-test `PokerWebSocket` reconnection by mocking `WebSocket` and verifying we surface `awaiting_continue` → `sendContinue` transitions.  
   - Add an integration test that toggles `stepMode`, waits for `awaitingContinue`, and ensures the "Continue" button unblocks AI turns.

4. **Turn manual visual checks into assertions**  
   - Replace the screenshot-only Playwright scripts with assertions on computed widths/heights (e.g., fail if community cards overflow). That way CI can catch regressions automatically.

Let me know if you’d like me to draft any of these tests next.
