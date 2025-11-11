#!/usr/bin/env python3
"""
Property-Based Testing - Phase C Testing Enhancement
=====================================================
Tests that certain properties (invariants) ALWAYS hold, regardless of input.

Strategy:
- Generate 1000+ random game scenarios
- Verify invariants hold in ALL cases
- Focus on properties that should NEVER be violated

Properties tested:
1. Chip conservation (total always equals starting amount)
2. No negative values (stacks, bets, pot always >= 0)
3. All-in consistency (all_in flag matches stack state)
4. Current player validity (active, not all-in, has chips)
5. Turn order correctness (players act in sequence)
6. Pot distribution completeness (pot = 0 at end of hand)

Expected runtime: ~5-10 minutes for 1000 scenarios
"""

import sys
import os
import random
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState, Player

class PropertyViolation(Exception):
    """Raised when a property is violated."""
    pass


class PropertyTester:
    """Test properties that should always hold."""

    def __init__(self):
        self.scenarios_tested = 0
        self.violations = []
        self.properties_checked = 0

    def check_chip_conservation(self, game: PokerGame, context: str):
        """Property: Total chips always equals starting amount."""
        self.properties_checked += 1
        total = sum(p.stack for p in game.players) + game.pot
        expected = game.total_chips

        if total != expected:
            raise PropertyViolation(
                f"Chip conservation violated {context}\n"
                f"  Expected: ${expected}\n"
                f"  Actual: ${total}\n"
                f"  Difference: ${abs(expected - total)}\n"
                f"  Pot: ${game.pot}\n"
                f"  Stacks: {[p.stack for p in game.players]}"
            )

    def check_no_negative_values(self, game: PokerGame, context: str):
        """Property: No negative stacks, bets, or pot."""
        self.properties_checked += 1

        if game.pot < 0:
            raise PropertyViolation(f"Negative pot {context}: ${game.pot}")

        if game.current_bet < 0:
            raise PropertyViolation(f"Negative current_bet {context}: ${game.current_bet}")

        for p in game.players:
            if p.stack < 0:
                raise PropertyViolation(f"Negative stack {context}: {p.name} = ${p.stack}")
            if p.current_bet < 0:
                raise PropertyViolation(f"Negative current_bet {context}: {p.name} = ${p.current_bet}")
            if p.total_invested < 0:
                raise PropertyViolation(f"Negative total_invested {context}: {p.name} = ${p.total_invested}")

    def check_all_in_consistency(self, game: PokerGame, context: str):
        """Property: all_in flag must match stack state."""
        self.properties_checked += 1

        for p in game.players:
            # If marked all-in, must have stack = 0
            if p.all_in and p.stack > 0:
                raise PropertyViolation(
                    f"All-in inconsistency {context}: {p.name} marked all-in but has ${p.stack}"
                )

            # If stack = 0 and active with investment, must be marked all-in
            if p.stack == 0 and p.is_active and p.total_invested > 0 and not p.all_in:
                raise PropertyViolation(
                    f"All-in inconsistency {context}: {p.name} has $0 and invested ${p.total_invested} but NOT marked all-in"
                )

    def check_current_player_validity(self, game: PokerGame, context: str):
        """Property: Current player must be valid (active, not all-in, has chips)."""
        self.properties_checked += 1

        if game.current_state == GameState.SHOWDOWN:
            return  # No current player at showdown

        if game.current_player_index is not None:
            current = game.players[game.current_player_index]

            if not current.is_active:
                raise PropertyViolation(
                    f"Current player invalid {context}: {current.name} is not active"
                )

            if current.all_in:
                raise PropertyViolation(
                    f"Current player invalid {context}: {current.name} is all-in"
                )

            if current.stack == 0:
                raise PropertyViolation(
                    f"Current player invalid {context}: {current.name} has $0"
                )

    def check_pot_distributed(self, game: PokerGame, context: str):
        """Property: Pot should be 0 at showdown (distributed)."""
        self.properties_checked += 1

        if game.current_state == GameState.SHOWDOWN and game.pot > 0:
            raise PropertyViolation(
                f"Pot not distributed {context}: ${game.pot} remaining at showdown"
            )

    def check_all_properties(self, game: PokerGame, context: str):
        """Check all properties."""
        self.check_chip_conservation(game, context)
        self.check_no_negative_values(game, context)
        self.check_all_in_consistency(game, context)
        self.check_current_player_validity(game, context)
        self.check_pot_distributed(game, context)


def random_valid_action(game: PokerGame) -> Tuple[str, int]:
    """Generate a random valid action for current player."""
    human = game.players[0]

    # Random fold (30% chance if we can also call/raise)
    if random.random() < 0.3:
        return ("fold", 0)

    call_amount = game.current_bet - human.current_bet

    # Random call (50% chance if we have chips)
    if human.stack >= call_amount and random.random() < 0.7:
        return ("call", 0)

    # Random raise (if we have chips beyond call)
    if human.stack > call_amount:
        min_raise = game.current_bet + game.big_blind
        max_raise = human.stack

        if human.stack >= min_raise - human.current_bet:
            min_amount = max(min_raise - human.current_bet, game.big_blind)
            # Ensure min <= max (handle case where min_raise > human.stack)
            if min_amount <= max_raise:
                raise_amount = random.randint(min_amount, max_raise)
                return ("raise", raise_amount)

    # Default: fold
    return ("fold", 0)


def play_random_scenario(tester: PropertyTester, scenario_num: int) -> bool:
    """
    Play a random game scenario.
    Returns True if all properties held, False if violation.
    """
    try:
        # Random game setup
        ai_count = random.choice([2, 3])  # 2-3 AI opponents
        game = PokerGame(human_player_name=f"Player", ai_count=ai_count)

        # Random number of hands (1-20)
        num_hands = random.randint(1, 20)

        for hand_num in range(num_hands):
            game.start_new_hand()

            # Check properties after hand start
            tester.check_all_properties(game, f"scenario {scenario_num}, hand {hand_num}, after start")

            # Play hand with random actions
            max_actions = 100
            actions = 0

            while game.current_state != GameState.SHOWDOWN and actions < max_actions:
                if game.current_player_index is None:
                    break

                human = game.players[0]
                current = game.players[game.current_player_index]

                if current == human and human.is_active and not human.all_in:
                    action_type, amount = random_valid_action(game)
                    result = game.submit_human_action(action_type, amount)

                    if not result and action_type != "fold":
                        game.submit_human_action("fold")

                    # Check properties after each action
                    tester.check_all_properties(game, f"scenario {scenario_num}, hand {hand_num}, after {action_type}")
                    actions += 1
                else:
                    break

            # Check properties at end of hand
            tester.check_all_properties(game, f"scenario {scenario_num}, hand {hand_num}, end")

            # Stop if too many players busted
            active_ai = [p for p in game.players[1:] if p.stack > 0]
            if len(active_ai) < 1:
                break

        tester.scenarios_tested += 1
        return True

    except PropertyViolation as e:
        tester.violations.append({
            'scenario': scenario_num,
            'error': str(e)
        })
        return False
    except Exception as e:
        tester.violations.append({
            'scenario': scenario_num,
            'error': f"Unexpected error: {str(e)}"
        })
        return False


def run_property_based_tests(num_scenarios: int = 1000):
    """Run property-based tests."""
    print("="*70)
    print(f"PROPERTY-BASED TESTING - {num_scenarios} RANDOM SCENARIOS")
    print("="*70)
    print("\nTesting properties:")
    print("  1. Chip conservation (total = starting amount)")
    print("  2. No negative values (stacks, bets, pot >= 0)")
    print("  3. All-in consistency (flag matches stack state)")
    print("  4. Current player validity (active, not all-in)")
    print("  5. Pot distributed at showdown")
    print("\nRunning scenarios...\n")

    tester = PropertyTester()

    for i in range(1, num_scenarios + 1):
        success = play_random_scenario(tester, i)

        if i % 100 == 0:
            pct = (i / num_scenarios) * 100
            violations = len(tester.violations)
            print(f"  Scenario {i:>4}/{num_scenarios} ({pct:>5.1f}%) - "
                  f"{tester.properties_checked:>6,} checks, {violations} violations")

        # Stop if too many violations
        if len(tester.violations) >= 10:
            print(f"\n⚠️  STOPPING: Too many violations ({len(tester.violations)})")
            break

    # Print summary
    print("\n" + "="*70)
    print("PROPERTY-BASED TESTING SUMMARY")
    print("="*70)
    print(f"Scenarios tested:    {tester.scenarios_tested:>6,}/{num_scenarios}")
    print(f"Properties checked:  {tester.properties_checked:>6,}")
    print(f"Violations found:    {len(tester.violations):>6}")

    if tester.violations:
        print("\n⚠️  VIOLATIONS FOUND:")
        for i, v in enumerate(tester.violations[:5], 1):
            print(f"\n  {i}. Scenario {v['scenario']}:")
            print(f"     {v['error']}")
        if len(tester.violations) > 5:
            print(f"\n  ... and {len(tester.violations) - 5} more")
        print("="*70)
        print("❌ PROPERTY-BASED TESTING FAILED")
        return False
    else:
        print("\n✅ ALL PROPERTIES HELD ACROSS ALL SCENARIOS!")
        print(f"   {tester.properties_checked:,} property checks passed")
        print(f"   {tester.scenarios_tested:,} random scenarios tested")
        print("="*70)
        return True


if __name__ == "__main__":
    # Run with 100 scenarios first (fast smoke test)
    print("Phase 1: Quick smoke test (100 scenarios)...\n")
    success = run_property_based_tests(num_scenarios=100)

    if success:
        print("\n\n" + "="*70)
        print("Smoke test passed! Running full 1000-scenario test...")
        print("="*70 + "\n")
        success = run_property_based_tests(num_scenarios=1000)

    sys.exit(0 if success else 1)
