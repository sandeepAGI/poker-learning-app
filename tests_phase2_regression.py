#!/usr/bin/env python3
"""
PHASE 2: Regression Tests for ALL User-Discovered Bugs

This test suite ensures bugs found during user testing NEVER come back.
Each test represents a real bug that was found and fixed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

class TestResults:
    def __init__(self):
        self.tests = []

    def add(self, name, passed, details=""):
        self.tests.append((name, passed, details))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if details and not passed:
            print(f"    {details}")

    def summary(self):
        passed = sum(1 for _, p, _ in self.tests if p)
        total = len(self.tests)
        print(f"\n{'='*70}")
        print(f"PHASE 2 REGRESSION TEST SUMMARY: {passed}/{total} passed")
        print(f"{'='*70}")
        return passed == total

# User Bug #1: Chips disappearing at showdown
def test_bug_chips_disappear_at_showdown(results):
    """User reported: Chips missing after showdown ($675 disappeared)"""
    print("\nTEST: Bug #1 - Chips Disappearing at Showdown")
    print("-" * 70)

    game = PokerGame("Player", ai_count=3)
    game.start_new_hand()

    # Play to showdown
    while game.current_state != GameState.SHOWDOWN:
        human = next((p for p in game.players if p.is_human), None)
        if game.get_current_player() == human:
            game.submit_human_action("call")

    # Check chip conservation
    total = sum(p.stack for p in game.players) + game.pot
    results.add(
        "Chips conserved at showdown",
        total == 4000,
        f"Total=${total}, expected=$4000"
    )

    # Check pot awarded
    results.add(
        "Pot awarded at showdown",
        game.pot == 0,
        f"Pot=${game.pot}, should be $0"
    )

# User Bug #2: Game hanging when only 1 player remains
def test_bug_game_hangs_after_folds(results):
    """User reported: Game hung waiting for AI after everyone folded"""
    print("\nTEST: Bug #2 - Game Hanging After Folds")
    print("-" * 70)

    game = PokerGame("Player", ai_count=3)
    game.start_new_hand()

    # Human folds
    game.submit_human_action("fold")

    # Should reach SHOWDOWN (not hang)
    results.add(
        "Game advances to SHOWDOWN after folds",
        game.current_state == GameState.SHOWDOWN,
        f"State={game.current_state.value}, expected=showdown"
    )

    # Pot should be awarded
    results.add(
        "Pot awarded when 1 player remains",
        game.pot == 0,
        f"Pot=${game.pot}, should be $0"
    )

    # Check chip conservation
    total = sum(p.stack for p in game.players) + game.pot
    results.add(
        "Chips conserved after folds",
        total == 4000,
        f"Total=${total}, expected=$4000"
    )

# User Bug #3: Next hand hanging waiting for AI
def test_bug_next_hand_hangs(results):
    """User reported: Next hand starts but hangs waiting for AI"""
    print("\nTEST: Bug #3 - Next Hand Hanging")
    print("-" * 70)

    game = PokerGame("Player", ai_count=3)

    # Play first hand to completion
    game.start_new_hand()
    while game.current_state != GameState.SHOWDOWN:
        human = next((p for p in game.players if p.is_human), None)
        if game.get_current_player() == human:
            game.submit_human_action("fold")

    # Start second hand
    game.start_new_hand()

    # Should either be waiting for human OR already processed AI actions
    human = next((p for p in game.players if p.is_human), None)
    current = game.get_current_player()

    # Game should NOT be stuck waiting for AI
    if current and not current.is_human:
        # If AI is current player, they should have acted OR be all-in
        results.add(
            "Next hand: AI acts automatically",
            current.has_acted or current.all_in,
            f"AI {current.name} hasn't acted and not all-in"
        )
    else:
        # Human's turn or no one's turn - that's fine
        results.add(
            "Next hand: Human's turn or hand complete",
            True
        )

# User Bug #4: Raise button always disabled
def test_bug_raise_validation(results):
    """User reported: Raise button always disabled"""
    print("\nTEST: Bug #4 - Raise Validation")
    print("-" * 70)

    game = PokerGame("Player", ai_count=3)
    game.start_new_hand()

    human = next((p for p in game.players if p.is_human), None)

    # Valid raise should work
    min_raise = game.current_bet + game.big_blind
    result = game.submit_human_action("raise", min_raise)

    results.add(
        "Valid raise accepted",
        result == True,
        f"Raise to ${min_raise} rejected"
    )

    # Check chip conservation after raise
    total = sum(p.stack for p in game.players) + game.pot
    results.add(
        "Chips conserved after raise",
        total == 4000,
        f"Total=${total}, expected=$4000"
    )

# Integration Test: Complete game flow
def test_complete_game_flow(results):
    """Test multiple complete hands in sequence"""
    print("\nTEST: Complete Game Flow (5 hands)")
    print("-" * 70)

    game = PokerGame("Player", ai_count=3)

    for hand_num in range(5):
        game.start_new_hand()

        # Play hand (mix of folds and calls)
        action_count = 0
        while game.current_state != GameState.SHOWDOWN and action_count < 20:
            human = next((p for p in game.players if p.is_human), None)
            if game.get_current_player() == human:
                # Alternate between fold and call
                if hand_num % 2 == 0:
                    game.submit_human_action("fold")
                else:
                    game.submit_human_action("call")
            action_count += 1

        # Check chip conservation after each hand
        total = sum(p.stack for p in game.players) + game.pot
        if total != 4000:
            results.add(
                f"Hand {hand_num + 1}: Chip conservation",
                False,
                f"Total=${total}, expected=$4000"
            )
            return

        # Check pot awarded
        if game.pot != 0:
            results.add(
                f"Hand {hand_num + 1}: Pot awarded",
                False,
                f"Pot=${game.pot}, should be $0"
            )
            return

    results.add(
        "5 consecutive hands: All chip conservation checks passed",
        True
    )

# Run all regression tests
if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 2: REGRESSION TEST SUITE")
    print("Testing all user-discovered bugs")
    print("="*70)

    results = TestResults()

    try:
        test_bug_chips_disappear_at_showdown(results)
        test_bug_game_hangs_after_folds(results)
        test_bug_next_hand_hangs(results)
        test_bug_raise_validation(results)
        test_complete_game_flow(results)

        success = results.summary()

        if success:
            print("\n🎉 ALL REGRESSION TESTS PASSED!")
            print("All user-found bugs are fixed and won't come back!")
            sys.exit(0)
        else:
            print("\n❌ SOME REGRESSION TESTS FAILED")
            print("A previously fixed bug may have returned!")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ REGRESSION TESTS CRASHED:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
