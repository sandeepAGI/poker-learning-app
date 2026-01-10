#!/usr/bin/env python3
"""
PHASE 3: Simulation Testing - Run 1000s of Random Games

This test suite runs massive simulations to find edge cases and ensure
poker rule violations never happen under any circumstances.
"""

import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

class SimulationResults:
    def __init__(self):
        self.games_played = 0
        self.hands_played = 0
        self.actions_taken = 0
        self.violations = []
        self.edge_cases = {
            "all_in_scenarios": 0,
            "side_pots": 0,
            "fold_victories": 0,
            "showdown_victories": 0,
            "split_pots": 0
        }

    def add_violation(self, game_num, hand_num, violation):
        self.violations.append({
            "game": game_num,
            "hand": hand_num,
            "violation": violation
        })

    def summary(self):
        print("\n" + "="*70)
        print("PHASE 3 SIMULATION TEST SUMMARY")
        print("="*70)
        print(f"Games Played:     {self.games_played}")
        print(f"Hands Played:     {self.hands_played}")
        print(f"Actions Taken:    {self.actions_taken}")
        print(f"\nEdge Cases Tested:")
        for case, count in self.edge_cases.items():
            print(f"  {case.replace('_', ' ').title()}: {count}")
        print(f"\nViolations Found: {len(self.violations)}")
        if self.violations:
            print("\n❌ VIOLATIONS DETECTED:")
            for v in self.violations[:10]:  # Show first 10
                print(f"  Game {v['game']}, Hand {v['hand']}: {v['violation']}")
        print("="*70)
        return len(self.violations) == 0

def simulate_random_game(game_num, hands_per_game, results):
    """Simulate a single game with random actions."""
    try:
        game = PokerGame("Player", ai_count=3)

        for hand_num in range(hands_per_game):
            # Start new hand
            game.start_new_hand()
            results.hands_played += 1

            # Track initial chip total
            initial_total = sum(p.stack for p in game.players) + game.pot
            if initial_total != 4000:
                results.add_violation(game_num, hand_num,
                                    f"Initial chip total {initial_total} != 4000")

            # Play hand with random human actions
            action_count = 0
            max_actions = 50  # Prevent infinite loops

            while game.current_state != GameState.SHOWDOWN and action_count < max_actions:
                human = next((p for p in game.players if p.is_human), None)
                current = game.get_current_player()

                if not current:
                    break  # No current player (hand over)

                if current == human:
                    # Random human action
                    action = random_human_action(game, human)
                    try:
                        game.submit_human_action(action["action"], action.get("amount"))
                        results.actions_taken += 1
                    except Exception as e:
                        # Some random actions may be invalid - that's okay
                        # Try a safe action (fold)
                        try:
                            game.submit_human_action("fold")
                            results.actions_taken += 1
                        except Exception as e2:
                            results.add_violation(game_num, hand_num,
                                                f"Failed to fold: {str(e2)}")
                            break

                action_count += 1

            # Check chip conservation after hand
            final_total = sum(p.stack for p in game.players) + game.pot
            if final_total != 4000:
                results.add_violation(game_num, hand_num,
                                    f"Chip conservation violated: {final_total} != 4000")

            # Check pot was awarded (should be 0 at showdown)
            if game.current_state == GameState.SHOWDOWN and game.pot > 0:
                results.add_violation(game_num, hand_num,
                                    f"Pot not awarded at showdown: ${game.pot} remaining")

            # Track edge cases
            if any(p.all_in for p in game.players):
                results.edge_cases["all_in_scenarios"] += 1

            if sum(1 for p in game.players if not p.is_active) >= 3:
                results.edge_cases["fold_victories"] += 1
            else:
                results.edge_cases["showdown_victories"] += 1

            # Check if any player is busted (stack <= 0)
            for player in game.players:
                if player.stack < 0:
                    results.add_violation(game_num, hand_num,
                                        f"{player.name} has negative stack: ${player.stack}")

        results.games_played += 1

    except Exception as e:
        results.add_violation(game_num, -1, f"Game crashed: {type(e).__name__}: {str(e)}")

def random_human_action(game, human):
    """Generate a random valid-ish action."""
    actions = ["fold", "call", "raise"]

    # Weight actions (more calls than raises, occasional folds)
    weights = [0.15, 0.6, 0.25]
    action = random.choices(actions, weights)[0]

    if action == "raise":
        min_raise = game.current_bet + game.big_blind
        max_raise = human.stack

        if min_raise <= max_raise:
            # Random raise amount (favor smaller raises)
            if random.random() < 0.7:
                # Small raise (min to 2x min)
                amount = random.randint(min_raise, min(min_raise * 2, max_raise))
            else:
                # Big raise (2x min to all-in)
                amount = random.randint(min(min_raise * 2, max_raise), max_raise)

            return {"action": "raise", "amount": amount}
        else:
            # Can't raise - call instead
            return {"action": "call"}

    return {"action": action}

def test_simulation_small(results):
    """Run 50 games with 10 hands each (500 hands total)."""
    print("\nTEST: Small Simulation (50 games × 10 hands = 500 hands)")
    print("-" * 70)

    for game_num in range(50):
        simulate_random_game(game_num + 1, 10, results)

        # Progress indicator
        if (game_num + 1) % 10 == 0:
            print(f"  Completed {game_num + 1}/50 games...")

    print(f"✅ Small simulation complete: {results.hands_played} hands played")

def test_simulation_medium(results):
    """Run 100 games with 20 hands each (2000 hands total)."""
    print("\nTEST: Medium Simulation (100 games × 20 hands = 2000 hands)")
    print("-" * 70)

    for game_num in range(100):
        simulate_random_game(game_num + 51, 20, results)

        # Progress indicator
        if (game_num + 1) % 20 == 0:
            print(f"  Completed {game_num + 1}/100 games...")

    print(f"✅ Medium simulation complete: {results.hands_played} hands played")

def test_simulation_stress(results):
    """Run stress test: 50 games with 50 hands each (2500 hands total)."""
    print("\nTEST: Stress Test (50 games × 50 hands = 2500 hands)")
    print("-" * 70)

    for game_num in range(50):
        simulate_random_game(game_num + 151, 50, results)

        # Progress indicator
        if (game_num + 1) % 10 == 0:
            print(f"  Completed {game_num + 1}/50 games...")

    print(f"✅ Stress test complete: {results.hands_played} hands played")

def test_edge_case_all_ins(results):
    """Test edge case: Force all-in scenarios."""
    print("\nTEST: Edge Case - All-In Scenarios")
    print("-" * 70)

    for game_num in range(20):
        try:
            game = PokerGame("Player", ai_count=3)

            for hand_num in range(5):
                game.start_new_hand()
                results.hands_played += 1

                human = next((p for p in game.players if p.is_human), None)

                # Try to force all-in on first action
                if game.get_current_player() == human and human.stack > 0:
                    try:
                        game.submit_human_action("raise", human.stack)
                        results.actions_taken += 1
                        results.edge_cases["all_in_scenarios"] += 1
                    except:
                        game.submit_human_action("fold")
                        results.actions_taken += 1

                # Check chip conservation
                total = sum(p.stack for p in game.players) + game.pot
                if total != 4000:
                    results.add_violation(game_num + 200, hand_num,
                                        f"All-in scenario: chips {total} != 4000")

            results.games_played += 1

        except Exception as e:
            results.add_violation(game_num + 200, -1,
                                f"All-in test crashed: {type(e).__name__}: {str(e)}")

    print(f"✅ All-in edge case test complete: {results.edge_cases['all_in_scenarios']} all-ins tested")

# Run all simulation tests
if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 3: SIMULATION TEST SUITE")
    print("Running 1000s of random games to find edge cases")
    print("="*70)

    results = SimulationResults()

    try:
        # Run simulation tests
        test_simulation_small(results)
        test_simulation_medium(results)
        test_simulation_stress(results)
        test_edge_case_all_ins(results)

        # Print summary
        success = results.summary()

        if success:
            print("\n🎉 ALL SIMULATION TESTS PASSED!")
            print(f"Tested {results.hands_played} hands with {results.actions_taken} actions")
            print("No poker rule violations found!")
            sys.exit(0)
        else:
            print("\n❌ SIMULATION TESTS FOUND VIOLATIONS")
            print("Poker rules were violated in some scenarios!")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ SIMULATION TESTS CRASHED:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
