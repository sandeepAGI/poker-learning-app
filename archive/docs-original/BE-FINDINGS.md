# Backend Findings

## Scope
- Reviewed FastAPI service (`backend/main.py`) and core engine (`backend/poker_engine.py`).
- Focused on Texas Hold'em rule compliance, betting flow, and chip accounting; did not evaluate frontend or deployment tooling.

## Critical Issues
1. **Turn order not enforced** (`backend/poker_engine.py`): Each human action immediately calls `_process_ai_actions()` (`backend/poker_engine.py:433`), which iterates every AI regardless of position (`backend/poker_engine.py:443`). There is no field tracking the next player to act, so one human API call resolves the entire betting sequence and AI raises never give earlier players a response window. This violates the sequential betting required by Hold'em and allows illegal multi-raise loops.
2. **Hand cannot resolve after human folds** (`backend/poker_engine.py`): Folding sets the human inactive (`backend/poker_engine.py:416`) and future `/player-action` calls are rejected because the method exits early when `is_active` is false (`backend/poker_engine.py:389`). AI decisions are only triggered from that method (`backend/poker_engine.py:433`), so once the human folds, remaining AI players never act and the state machine never reaches showdown. Chips remain frozen in the pot and the hand stalls indefinitely.
3. **Raise validation allows stack manipulation** (`backend/poker_engine.py`): The backend accepts any positive `amount` for a raise (`backend/main.py:78`), and `submit_human_action` blindly forwards it to `Player.bet(amount)` (`backend/poker_engine.py:426`). If a user sends a value below the current bet, later callers compute a negative `call_amount` (`backend/poker_engine.py:460`) and `Player.bet` adds chips back to their stack because it subtracts the passed amount (`backend/poker_engine.py:58`). Players can therefore shrink the pot or mint chips simply by "raising" too little.

## Major Issues
1. **Raise accounting incorrect for human** (`backend/poker_engine.py`): Human raises call `Player.bet(amount)` with the full target bet (`backend/poker_engine.py:426`), while `Player.bet` itself adds the wager to the running `current_bet` (`backend/poker_engine.py:52`). If the human has already posted chips—e.g., called the blind and then raises—the existing contribution is counted again, inflating the pot (`backend/poker_engine.py:428`) and shrinking the stack incorrectly.
2. **Showdown payout ignores side pots** (`backend/poker_engine.py`): Winners are simply divided into equal shares of `self.pot` (`backend/poker_engine.py:513`), without recording individual stakes or handling remainders. In all-in scenarios, players who contributed less than the leaders can still win equal payouts, and any leftover chips from integer division vanish when `self.pot` is zeroed (`backend/poker_engine.py:519`). Hold'em requires side-pot accounting tied to contributions.

## Minor Issues
1. **Zero-chip “raise” decisions** (`backend/poker_engine.py`): Several AI branches compute raise sizes from `current_bet` (`backend/poker_engine.py:196`, `backend/poker_engine.py:219`, `backend/poker_engine.py:236`, `backend/poker_engine.py:249`). After `_maybe_advance_state` resets `current_bet` between streets (`backend/poker_engine.py:500`), these formulas yield a zero amount, yet the action is still labeled "raise". The move functions as a check but logs misleading telemetry.

## Recommendations
1. Move turn enforcement into the backend state machine, exposing next-to-act information to the UI and rejecting out-of-turn requests.
2. Rework the betting loop to track per-player contributions, validate raises as increments over the current bet (with minimum raise sizing), and loop players until all have folded or matched.
3. Track contributions per street so you can build side pots and distribute winnings precisely (including any remainder) during showdown.

## Confidence
High for the identified issues—they stem from direct code inspection and violate core Hold'em rules. Additional defects may emerge while reworking the betting engine and payout logic.
