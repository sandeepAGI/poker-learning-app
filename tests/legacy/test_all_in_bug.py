#!/usr/bin/env python3
"""Test all-in handling to reproduce the negative call bug."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_all_in_scenario():
    """Test what happens when human goes all-in."""
    print("="*70)
    print("TEST: All-In Scenario")
    print("="*70)

    game = PokerGame("Player", ai_count=3)
    game.qc_enabled = False  # Disable QC for testing
    game.pot = 0  # Reset pot
    game.start_new_hand()

    print(f"\nInitial state:")
    print(f"  Game state: {game.current_state.value}")
    print(f"  Current bet: ${game.current_bet}")
    print(f"  Pot: ${game.pot}")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}, current_bet=${p.current_bet}, all_in={p.all_in}, active={p.is_active}")

    # Find human player
    human = next(p for p in game.players if p.is_human)
    print(f"\nHuman's turn? {game.get_current_player() == human}")

    # Wait for human's turn
    while game.get_current_player() != human and game.current_state == GameState.PRE_FLOP:
        # Skip (AI will act automatically via _process_remaining_actions in submit_human_action)
        break

    # Human goes all-in
    print(f"\n>>> Human goes ALL-IN with ${human.stack}")
    result = game.submit_human_action("raise", human.stack)
    print(f"Action result: {result}")

    print(f"\nAfter all-in:")
    print(f"  Game state: {game.current_state.value}")
    print(f"  Current bet: ${game.current_bet}")
    print(f"  Pot: ${game.pot}")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}, current_bet=${p.current_bet}, all_in={p.all_in}, active={p.is_active}")

    # Check who's turn it is
    current = game.get_current_player()
    print(f"\nCurrent player: {current.name if current else 'None'}")
    print(f"Current player index: {game.current_player_index}")

    # Check if human would see action buttons
    if current == human:
        print(f"\n❌ BUG: Human is still current player even though they're all-in!")
        print(f"   Human stack: ${human.stack}")
        print(f"   Human all_in: {human.all_in}")
        print(f"   Call amount would be: ${game.current_bet - human.current_bet}")
        return False
    else:
        print(f"\n✅ Correct: Next player ({current.name if current else 'None'}) is current")

        # Check call amount calculation
        call_amount = game.current_bet - human.current_bet
        print(f"\nIf human were to see call button:")
        print(f"  Current bet: ${game.current_bet}")
        print(f"  Human current_bet: ${human.current_bet}")
        print(f"  Call amount: ${call_amount}")

        if call_amount < 0:
            print(f"❌ BUG: Call amount is NEGATIVE!")
            return False
        else:
            print(f"✅ Call amount is non-negative")

    return True

if __name__ == "__main__":
    try:
        success = test_all_in_scenario()
        if success:
            print("\n" + "="*70)
            print("✅ ALL-IN TEST PASSED")
            print("="*70)
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("❌ ALL-IN TEST FAILED")
            print("="*70)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
