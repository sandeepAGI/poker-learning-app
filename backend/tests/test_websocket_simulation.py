"""
Comprehensive WebSocket Flow Simulation Tests

These tests simulate the EXACT code paths used in websocket_manager.py's
process_ai_turns_with_events() function, tracing through complete game flows
to catch bugs before UAT.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState, AIStrategy


class WebSocketSimulator:
    """
    Simulates the websocket_manager.py logic for testing.
    This mirrors process_ai_turns_with_events() exactly.
    """

    def __init__(self, game: PokerGame, verbose: bool = True):
        self.game = game
        self.verbose = verbose
        self.trace_log = []
        self.state_broadcasts = []
        self.iteration_count = 0
        self.max_iterations = 100  # Safety limit

    def log(self, msg: str):
        """Log a trace message."""
        self.trace_log.append(msg)
        if self.verbose:
            print(f"  [TRACE] {msg}")

    def broadcast_state(self, reason: str):
        """Simulate a state broadcast to frontend."""
        current = self.game.get_current_player()
        current_name = current.name if current else "None"
        human = next((p for p in self.game.players if p.is_human), None)
        is_human_turn = (current == human) if current and human else False

        state_info = {
            "reason": reason,
            "game_state": self.game.current_state.value,
            "current_player": current_name,
            "current_player_index": self.game.current_player_index,
            "is_human_turn": is_human_turn,
            "pot": self.game.pot,
            "current_bet": self.game.current_bet,
            "players": [(p.name, p.is_active, p.has_acted, p.current_bet, p.stack)
                       for p in self.game.players]
        }
        self.state_broadcasts.append(state_info)
        self.log(f"BROADCAST: {reason} | State={self.game.current_state.value} | "
                f"CurrentPlayer={current_name} | HumanTurn={is_human_turn}")
        return state_info

    def process_ai_turns(self) -> dict:
        """
        Simulate process_ai_turns_with_events() from websocket_manager.py.
        Returns a summary of what happened.
        """
        self.log(f"=== process_ai_turns() START ===")
        self.log(f"Game state: {self.game.current_state.value}")
        self.log(f"Current player index: {self.game.current_player_index}")

        result = {
            "ai_actions": [],
            "human_waiting": False,
            "round_advanced": False,
            "final_state": None,
            "error": None
        }

        while self.game.current_player_index is not None:
            self.iteration_count += 1
            if self.iteration_count > self.max_iterations:
                result["error"] = f"INFINITE LOOP DETECTED after {self.max_iterations} iterations!"
                self.log(f"ERROR: {result['error']}")
                return result

            # CRITICAL: Check if betting round is complete FIRST (prevents infinite loop)
            if self.game._betting_round_complete():
                self.log(f"Betting round COMPLETE (checked at loop start)")
                break

            current_player = self.game.players[self.game.current_player_index]
            self.log(f"Loop iteration {self.iteration_count}: Checking player {current_player.name} "
                    f"(human={current_player.is_human}, active={current_player.is_active}, "
                    f"all_in={current_player.all_in}, has_acted={current_player.has_acted})")

            # Check 1: Human player who hasn't acted
            if current_player.is_human and not current_player.all_in and not current_player.has_acted:
                self.log(f"STOP: Reached human player {current_player.name} who needs to act")
                result["human_waiting"] = True
                break

            # Check 2: Skip inactive, all-in, or already-acted players
            if not current_player.is_active or current_player.all_in or current_player.has_acted:
                reason = "inactive" if not current_player.is_active else ("all-in" if current_player.all_in else "already acted")
                self.log(f"SKIP: Player {current_player.name} is {reason}")
                self.game.current_player_index = self.game._get_next_active_player_index(
                    self.game.current_player_index + 1
                )
                continue

            # AI player needs to act
            self.log(f"AI ACTION: {current_player.name} deciding...")

            # Get AI decision
            decision = AIStrategy.make_decision_with_reasoning(
                current_player.personality,
                current_player.hole_cards,
                self.game.community_cards,
                self.game.current_bet,
                self.game.pot,
                current_player.stack,
                current_player.current_bet,
                self.game.big_blind
            )

            # Store decision
            self.game.last_ai_decisions[current_player.player_id] = decision

            # Apply action (mirroring websocket_manager.py exactly)
            if decision.action == "fold":
                current_player.is_active = False
                self.game._log_hand_event("action", current_player.player_id, "fold", 0, 0.0,
                                         f"{current_player.name} folded")
                self.log(f"AI ACTION: {current_player.name} FOLDS")
            elif decision.action == "call":
                call_amount = self.game.current_bet - current_player.current_bet
                current_player.bet(call_amount)
                self.game.pot += call_amount
                self.game._log_hand_event("action", current_player.player_id, "call", call_amount, 0.0,
                                         f"{current_player.name} called ${call_amount}")
                self.log(f"AI ACTION: {current_player.name} CALLS ${call_amount}")
            elif decision.action == "raise":
                current_player.bet(decision.amount)
                self.game.current_bet = current_player.current_bet
                self.game.pot += decision.amount
                self.game._log_hand_event("action", current_player.player_id, "raise", decision.amount, 0.0,
                                         f"{current_player.name} raised to ${self.game.current_bet}")
                self.log(f"AI ACTION: {current_player.name} RAISES to ${self.game.current_bet}")
                # Reset has_acted for other players
                for p in self.game.players:
                    if p.player_id != current_player.player_id and p.is_active and not p.all_in:
                        p.has_acted = False
                        self.log(f"  -> Reset has_acted for {p.name}")

            current_player.has_acted = True
            result["ai_actions"].append({
                "player": current_player.name,
                "action": decision.action,
                "amount": decision.amount
            })

            # Broadcast state (before moving to next player - this is the current behavior)
            self.broadcast_state(f"After {current_player.name} {decision.action}")

            # Move to next player
            old_index = self.game.current_player_index
            self.game.current_player_index = self.game._get_next_active_player_index(
                self.game.current_player_index + 1
            )
            self.log(f"Move to next player: index {old_index} -> {self.game.current_player_index}")

            # Check if betting round is complete
            if self.game._betting_round_complete():
                self.log(f"Betting round COMPLETE")
                break

        # After loop: check if we should advance state
        if self.game._betting_round_complete():
            self.log(f"Advancing game state from {self.game.current_state.value}")
            advanced = self.game._advance_state_for_websocket()
            result["round_advanced"] = advanced

            if advanced:
                self.log(f"State advanced to {self.game.current_state.value}")
                self.broadcast_state(f"State advanced to {self.game.current_state.value}")

                # Check if AI should continue (next betting round)
                current = self.game.get_current_player()
                if current and not current.is_human:
                    self.log(f"Next player is AI ({current.name}), recursing...")
                    recursive_result = self.process_ai_turns()
                    result["ai_actions"].extend(recursive_result["ai_actions"])
                    result["human_waiting"] = recursive_result["human_waiting"]
                    result["error"] = recursive_result.get("error")
        else:
            # Betting round NOT complete - send final state so frontend knows it's human's turn
            self.log(f"Betting round NOT complete - sending final state update")
            self.broadcast_state("Final state - waiting for human")

        result["final_state"] = self.game.current_state.value
        self.log(f"=== process_ai_turns() END ===")
        return result


def simulate_human_action(game: PokerGame, action: str, amount: int = None, verbose: bool = True) -> bool:
    """Simulate human player action."""
    human = next((p for p in game.players if p.is_human), None)
    if not human:
        return False

    human_index = game.players.index(human)

    if verbose:
        print(f"  [HUMAN] {human.name} performs {action}" + (f" ${amount}" if amount else ""))

    # Use the actual submit_human_action with process_ai=False
    return game.submit_human_action(action, amount, process_ai=False)


def run_full_hand_simulation(player_count: int = 4, verbose: bool = True) -> dict:
    """
    Run a complete hand simulation from start to showdown.
    Returns detailed trace information.
    """
    print(f"\n{'='*70}")
    print(f"SIMULATING FULL HAND: {player_count} players (1 human + {player_count-1} AI)")
    print(f"{'='*70}")

    game = PokerGame("Human", ai_count=player_count - 1)
    game.start_new_hand(process_ai=False)

    simulator = WebSocketSimulator(game, verbose=verbose)

    results = {
        "success": False,
        "hands_completed": 0,
        "errors": [],
        "streets_played": [],
        "total_iterations": 0,
        "human_actions_required": 0
    }

    max_human_actions = 20  # Safety limit
    human_actions = 0

    print(f"\n--- Initial State ---")
    print(f"Players: {[(p.name, 'Human' if p.is_human else p.personality) for p in game.players]}")
    print(f"Dealer index: {game.dealer_index}")
    print(f"Current player index: {game.current_player_index}")
    print(f"Current bet: ${game.current_bet}, Pot: ${game.pot}")

    # Process initial AI turns (if AI acts first)
    current = game.get_current_player()
    if current and not current.is_human:
        print(f"\n--- AI acts first (pre-flop) ---")
        ai_result = simulator.process_ai_turns()
        if ai_result.get("error"):
            results["errors"].append(ai_result["error"])
            return results

    # Main game loop
    while game.current_state != GameState.SHOWDOWN:
        human_actions += 1
        results["human_actions_required"] = human_actions

        if human_actions > max_human_actions:
            results["errors"].append(f"Too many human actions ({human_actions}), possible infinite loop")
            break

        current = game.get_current_player()
        if not current:
            print(f"\n--- No current player, checking state ---")
            if game._betting_round_complete():
                game._advance_state_for_websocket()
                continue
            else:
                results["errors"].append("No current player but betting round not complete")
                break

        if current.is_human and not current.has_acted:
            print(f"\n--- Human's turn ({game.current_state.value}) ---")
            results["streets_played"].append(game.current_state.value)

            # Human calls (simple strategy for simulation)
            success = simulate_human_action(game, "call", verbose=verbose)
            if not success:
                results["errors"].append(f"Human action failed on {game.current_state.value}")
                break

            # Process AI responses
            print(f"\n--- AI responses ({game.current_state.value}) ---")
            ai_result = simulator.process_ai_turns()
            results["total_iterations"] += simulator.iteration_count

            if ai_result.get("error"):
                results["errors"].append(ai_result["error"])
                break
        else:
            # This shouldn't happen - if it's not human's turn, AI should have processed
            print(f"\n--- Unexpected: current player is {current.name} (human={current.is_human}, has_acted={current.has_acted}) ---")

            if not current.is_human:
                # Process AI turns
                ai_result = simulator.process_ai_turns()
                results["total_iterations"] += simulator.iteration_count
                if ai_result.get("error"):
                    results["errors"].append(ai_result["error"])
                    break
            else:
                # Human has already acted, check if round should advance
                if game._betting_round_complete():
                    game._advance_state_for_websocket()
                else:
                    results["errors"].append(f"Human has acted but round not complete, stuck!")
                    break

    if game.current_state == GameState.SHOWDOWN:
        results["success"] = True
        results["hands_completed"] = 1
        print(f"\n--- SHOWDOWN REACHED ---")
        print(f"Final pot: ${game.pot}")

        # Check chip conservation
        total_chips = sum(p.stack for p in game.players) + game.pot
        expected = len(game.players) * 1000
        if total_chips != expected:
            results["errors"].append(f"Chip conservation failed: {total_chips} != {expected}")

    print(f"\n{'='*70}")
    print(f"SIMULATION RESULT: {'SUCCESS' if results['success'] else 'FAILED'}")
    print(f"Streets played: {results['streets_played']}")
    print(f"Human actions: {results['human_actions_required']}")
    print(f"Total iterations: {results['total_iterations']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    print(f"{'='*70}\n")

    return results


def run_multiple_scenarios():
    """Run multiple game scenarios to catch edge cases."""
    print("\n" + "="*70)
    print("RUNNING MULTIPLE GAME SCENARIOS")
    print("="*70)

    all_results = []

    # Scenario 1: 4 players (standard)
    print("\n>>> Scenario 1: 4 players (1 human + 3 AI)")
    result = run_full_hand_simulation(player_count=4, verbose=True)
    all_results.append(("4 players", result))

    # Scenario 2: 2 players (heads-up)
    print("\n>>> Scenario 2: 2 players (heads-up)")
    result = run_full_hand_simulation(player_count=2, verbose=True)
    all_results.append(("2 players (heads-up)", result))

    # Scenario 3: 3 players
    print("\n>>> Scenario 3: 3 players")
    result = run_full_hand_simulation(player_count=3, verbose=True)
    all_results.append(("3 players", result))

    # Summary
    print("\n" + "="*70)
    print("SCENARIO SUMMARY")
    print("="*70)

    all_passed = True
    for name, result in all_results:
        status = "PASS" if result["success"] and not result["errors"] else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  {name}: {status}")
        if result["errors"]:
            for err in result["errors"]:
                print(f"    ERROR: {err}")

    print("="*70)
    print(f"OVERALL: {'ALL SCENARIOS PASSED' if all_passed else 'SOME SCENARIOS FAILED'}")
    print("="*70)

    return all_passed


# Pytest tests
@pytest.mark.slow
class TestWebSocketSimulation:
    """Pytest tests using the simulator."""

    def test_4_player_full_hand(self):
        """Test a complete 4-player hand reaches showdown."""
        result = run_full_hand_simulation(player_count=4, verbose=False)
        assert result["success"], f"Game did not reach showdown: {result['errors']}"
        assert not result["errors"], f"Errors occurred: {result['errors']}"

    def test_2_player_heads_up(self):
        """Test a complete heads-up hand reaches showdown."""
        result = run_full_hand_simulation(player_count=2, verbose=False)
        assert result["success"], f"Game did not reach showdown: {result['errors']}"
        assert not result["errors"], f"Errors occurred: {result['errors']}"

    def test_3_player_full_hand(self):
        """Test a complete 3-player hand reaches showdown."""
        result = run_full_hand_simulation(player_count=3, verbose=False)
        assert result["success"], f"Game did not reach showdown: {result['errors']}"
        assert not result["errors"], f"Errors occurred: {result['errors']}"

    def test_no_infinite_loops(self):
        """Run multiple hands and ensure no infinite loops."""
        for i in range(5):
            result = run_full_hand_simulation(player_count=4, verbose=False)
            assert result["total_iterations"] < 100, \
                f"Hand {i+1}: Too many iterations ({result['total_iterations']}), possible infinite loop"


if __name__ == "__main__":
    # Run interactive simulation
    run_multiple_scenarios()
