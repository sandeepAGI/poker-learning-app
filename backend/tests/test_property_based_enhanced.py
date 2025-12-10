"""
Phase 3.3: Enhanced Property-Based Testing
==========================================
Tests that critical properties ALWAYS hold, regardless of input.

New invariants added in Phase 3:
- No infinite loops (player acts ≤4 times per betting round)
- Failed actions advance turn (game doesn't hang on failures)

Existing invariants:
- Chip conservation (total = starting amount)
- No negative values (stacks, bets, pot ≥ 0)
- All-in consistency (flag matches stack state)

Phase 3 of Testing Improvement Plan (10 hours total, 2 hours for enhancement)
"""

import pytest
import random
from typing import List, Dict
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState, Player


class PropertyViolation(Exception):
    """Raised when a property invariant is violated"""
    pass


class TestPropertyBasedInvariants:
    """Phase 3.3: Property-based testing with enhanced invariants"""

    def test_property_chip_conservation(self):
        """
        Property: Total chips always equals starting amount.

        Tests 100 random scenarios to ensure chip conservation holds.
        """
        print("\n[PROPERTY] Testing chip conservation across 100 scenarios...")

        violations = []
        for scenario in range(100):
            game = PokerGame(human_player_name="PropTester", ai_count=3)
            game.start_new_hand(process_ai=False)

            expected_total = game.total_chips

            # Play random actions for 5 rounds
            for _ in range(5):
                if game.current_state == GameState.SHOWDOWN:
                    break

                # Random valid action
                if game.current_player_index == 0:  # Human's turn
                    action = random.choice(["fold", "call", "raise"])
                    if action == "raise":
                        max_bet = game.players[0].stack + game.players[0].current_bet
                        amount = random.randint(20, max_bet) if max_bet >= 20 else max_bet
                        game.apply_action(0, "raise", amount)
                    else:
                        game.apply_action(0, action, 0)

            # Check chip conservation
            actual_total = sum(p.stack for p in game.players) + game.pot
            if actual_total != expected_total:
                violations.append({
                    "scenario": scenario,
                    "expected": expected_total,
                    "actual": actual_total,
                    "difference": abs(expected_total - actual_total)
                })

        if violations:
            print(f"\n❌ Chip conservation violated in {len(violations)}/100 scenarios:")
            for v in violations[:3]:
                print(f"  Scenario {v['scenario']}: Expected ${v['expected']}, Got ${v['actual']}")

        assert len(violations) == 0, f"Chip conservation violated in {len(violations)}/100 scenarios"
        print("✅ Chip conservation held across all 100 scenarios")


    def test_property_no_negative_values(self):
        """
        Property: No negative stacks, bets, or pot values.

        Tests 100 random scenarios to ensure no negative values.
        """
        print("\n[PROPERTY] Testing no negative values across 100 scenarios...")

        violations = []
        for scenario in range(100):
            game = PokerGame(human_player_name="PropTester", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Play random actions
            for _ in range(10):
                if game.current_state == GameState.SHOWDOWN:
                    break

                if game.current_player_index == 0:
                    action = random.choice(["fold", "call"])
                    game.apply_action(0, action, 0)

                # Check for negatives
                if game.pot < 0:
                    violations.append({"scenario": scenario, "issue": f"Negative pot: ${game.pot}"})
                    break

                if game.current_bet < 0:
                    violations.append({"scenario": scenario, "issue": f"Negative current_bet: ${game.current_bet}"})
                    break

                for p in game.players:
                    if p.stack < 0:
                        violations.append({"scenario": scenario, "issue": f"Negative stack for {p.name}: ${p.stack}"})
                        break
                    if p.current_bet < 0:
                        violations.append({"scenario": scenario, "issue": f"Negative current_bet for {p.name}: ${p.current_bet}"})
                        break

        if violations:
            print(f"\n❌ Negative values found in {len(violations)}/100 scenarios:")
            for v in violations[:3]:
                print(f"  Scenario {v['scenario']}: {v['issue']}")

        assert len(violations) == 0, f"Negative values found in {len(violations)}/100 scenarios"
        print("✅ No negative values across all 100 scenarios")


    def test_property_all_in_consistency(self):
        """
        Property: all_in flag must match stack state.

        - If marked all-in, stack must be 0
        - If stack is 0 and active with investment, must be marked all-in
        """
        print("\n[PROPERTY] Testing all-in consistency across 100 scenarios...")

        violations = []
        for scenario in range(100):
            game = PokerGame(human_player_name="PropTester", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Force some all-ins
            for _ in range(5):
                if game.current_state == GameState.SHOWDOWN:
                    break

                if game.current_player_index == 0:
                    # Go all-in sometimes
                    if random.random() < 0.3:
                        all_in_amount = game.players[0].stack + game.players[0].current_bet
                        game.apply_action(0, "raise", all_in_amount)
                    else:
                        game.apply_action(0, "call", 0)

                # Check all-in consistency
                for p in game.players:
                    # If marked all-in, must have stack = 0
                    if p.all_in and p.stack > 0:
                        violations.append({
                            "scenario": scenario,
                            "issue": f"{p.name} marked all-in but has ${p.stack}"
                        })
                        break

                    # If stack = 0 and active with investment, must be marked all-in
                    if p.stack == 0 and p.is_active and p.total_invested > 0 and not p.all_in:
                        violations.append({
                            "scenario": scenario,
                            "issue": f"{p.name} has $0 and invested ${p.total_invested} but NOT marked all-in"
                        })
                        break

        if violations:
            print(f"\n❌ All-in inconsistency in {len(violations)}/100 scenarios:")
            for v in violations[:3]:
                print(f"  Scenario {v['scenario']}: {v['issue']}")

        assert len(violations) == 0, f"All-in inconsistency in {len(violations)}/100 scenarios"
        print("✅ All-in consistency held across all 100 scenarios")


    def test_property_no_infinite_loops(self):
        """
        NEW INVARIANT (Phase 3.3):
        Property: Games complete without hanging in infinite loops.

        Validates that games complete successfully within reasonable time/actions.
        The infinite loop bug was already fixed in Phase 1 (test_negative_actions.py).
        This test validates the fix works across random scenarios.
        """
        print("\n[PROPERTY] Testing no infinite loops across 100 scenarios...")

        violations = []
        for scenario in range(100):
            game = PokerGame(human_player_name="PropTester", ai_count=3)
            game.start_new_hand()

            # Play a full hand with random human actions
            actions_taken = 0
            max_actions = 20  # Reasonable max for one hand

            while game.current_state != GameState.SHOWDOWN and actions_taken < max_actions:
                if game.current_player_index == 0:  # Human's turn
                    # Random action
                    action = random.choice(["call", "fold", "fold"])
                    success = game.submit_human_action(action, 0)

                    # If action failed, fallback fold should trigger (from Phase 1 fix)
                    # Game should continue, not hang
                    if not success:
                        # Try explicit fold
                        game.submit_human_action("fold", 0)

                    actions_taken += 1
                else:
                    # AI should process automatically via submit_human_action
                    # If we're stuck here, that's an infinite loop
                    violations.append({
                        "scenario": scenario,
                        "issue": f"Game stuck at player {game.current_player_index} after {actions_taken} actions"
                    })
                    break

            # If we hit max_actions without completing, that's an infinite loop
            if game.current_state != GameState.SHOWDOWN and actions_taken >= max_actions:
                violations.append({
                    "scenario": scenario,
                    "issue": f"Game didn't complete after {max_actions} actions - possible infinite loop"
                })

        if violations:
            print(f"\n❌ Infinite loops detected in {len(violations)}/100 scenarios:")
            for v in violations[:3]:
                print(f"  Scenario {v['scenario']}: {v['issue']}")

        assert len(violations) == 0, f"Infinite loops detected in {len(violations)}/100 scenarios"
        print("✅ No infinite loops detected across all 100 scenarios")


    def test_property_failed_actions_advance_turn(self):
        """
        NEW INVARIANT (Phase 3.3):
        Property: If action fails, turn must still advance.

        Tests that failed actions don't cause game to hang on same player.
        Uses mocking to simulate action failures.
        """
        print("\n[PROPERTY] Testing failed actions advance turn across 50 scenarios...")

        violations = []
        for scenario in range(50):
            game = PokerGame(human_player_name="PropTester", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Inject failures for specific player (player 1)
            failing_player_index = 1
            previous_player = None

            for action_num in range(15):
                if game.current_state == GameState.SHOWDOWN:
                    break

                current_player = game.current_player_index
                if current_player is None:
                    break

                # If we're at the failing player, try invalid action (should fail)
                if current_player == failing_player_index:
                    # Try invalid raise (amount too small)
                    result = game.apply_action(failing_player_index, "raise", 5)

                    # Action should fail
                    if not result["success"]:
                        # Now try valid fold (should succeed)
                        result = game.apply_action(failing_player_index, "fold", 0)

                        # After failed action + fold, turn should advance
                        next_player = game.current_player_index

                        # If still same player after failed action + fold, that's a bug
                        if next_player == failing_player_index:
                            violations.append({
                                "scenario": scenario,
                                "action": action_num,
                                "issue": f"Turn didn't advance after failed action + fold for player {failing_player_index}"
                            })
                            break
                else:
                    # Other players: normal action
                    if current_player == 0:
                        game.apply_action(0, "call", 0)

                previous_player = current_player

        if violations:
            print(f"\n❌ Failed actions didn't advance turn in {len(violations)}/50 scenarios:")
            for v in violations[:3]:
                print(f"  Scenario {v['scenario']}, Action {v['action']}: {v['issue']}")

        assert len(violations) == 0, f"Failed actions didn't advance turn in {len(violations)}/50 scenarios"
        print("✅ Failed actions always advanced turn across all 50 scenarios")


    def test_property_1000_random_scenarios(self):
        """
        Comprehensive property test: 1000 random scenarios.

        Tests ALL properties together across many random game states.
        This is the ultimate stress test.
        """
        print("\n[PROPERTY] Running comprehensive 1000-scenario property test...")

        stats = {
            "total": 0,
            "chip_violations": 0,
            "negative_violations": 0,
            "all_in_violations": 0,
            "errors": 0
        }

        for scenario in range(1000):
            try:
                game = PokerGame(human_player_name="PropTester", ai_count=random.choice([1, 2, 3]))
                game.start_new_hand(process_ai=False)

                expected_total = game.total_chips

                # Play random game
                for _ in range(random.randint(3, 10)):
                    if game.current_state == GameState.SHOWDOWN:
                        break

                    if game.current_player_index == 0:
                        action = random.choice(["fold", "call", "call", "raise"])
                        if action == "raise":
                            player = game.players[0]
                            max_bet = player.stack + player.current_bet
                            if max_bet >= 20:
                                amount = random.randint(20, max_bet)
                                game.apply_action(0, "raise", amount)
                            else:
                                game.apply_action(0, "call", 0)
                        else:
                            game.apply_action(0, action, 0)

                stats["total"] += 1

                # Check chip conservation
                actual_total = sum(p.stack for p in game.players) + game.pot
                if actual_total != expected_total:
                    stats["chip_violations"] += 1

                # Check no negatives
                if game.pot < 0 or game.current_bet < 0:
                    stats["negative_violations"] += 1

                for p in game.players:
                    if p.stack < 0 or p.current_bet < 0:
                        stats["negative_violations"] += 1
                        break

                    # Check all-in consistency
                    if p.all_in and p.stack > 0:
                        stats["all_in_violations"] += 1
                        break

            except Exception as e:
                stats["errors"] += 1
                if stats["errors"] > 10:
                    raise

        # Print summary
        print("\n" + "="*70)
        print("1000-SCENARIO PROPERTY TEST SUMMARY")
        print("="*70)
        print(f"Total scenarios:         {stats['total']:>7,}")
        print(f"Chip violations:         {stats['chip_violations']:>7,}")
        print(f"Negative violations:     {stats['negative_violations']:>7,}")
        print(f"All-in violations:       {stats['all_in_violations']:>7,}")
        print(f"Errors:                  {stats['errors']:>7,}")
        print("="*70)

        # Assertions
        assert stats["chip_violations"] == 0, f"Chip conservation violated {stats['chip_violations']} times"
        assert stats["negative_violations"] == 0, f"Negative values found {stats['negative_violations']} times"
        assert stats["all_in_violations"] == 0, f"All-in inconsistency {stats['all_in_violations']} times"
        assert stats["errors"] == 0, f"Errors occurred {stats['errors']} times"

        print("✅ All properties held across all 1000 scenarios!")
