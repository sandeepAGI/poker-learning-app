#!/usr/bin/env python3
"""
Test for showdown pot award bug - chips disappearing when reaching showdown
User reported: After raising and winning at showdown, no winner announced and chips missing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_showdown_pot_award():
    """Test that pot is awarded automatically at showdown."""
    print("=" * 70)
    print("TEST: Showdown Pot Award & Chip Conservation")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print(f"\n✓ Game started")
    initial_total = sum(p.stack for p in game.players) + game.pot
    print(f"  Initial total chips: ${initial_total}")
    assert initial_total == 4000, f"Initial chips should be $4000, got ${initial_total}"

    # Play through to showdown (call all the way)
    print(f"\n→ Playing through to showdown...")

    # Human calls
    human = next(p for p in game.players if p.is_human)
    print(f"  {game.current_state}: Human calls")
    game.submit_human_action("call")

    # Should advance through streets automatically with AI actions
    hand_count = 0
    while game.current_state != GameState.SHOWDOWN and hand_count < 10:
        state_before = game.current_state
        # If it's human's turn, call
        if game.get_current_player() == human:
            print(f"  {game.current_state}: Human calls")
            game.submit_human_action("call")
        hand_count += 1

        if game.current_state != state_before:
            print(f"  Advanced to {game.current_state}")

    print(f"\n✓ Reached {game.current_state}")
    print(f"  Pot: ${game.pot}")
    print(f"  Active players: {sum(1 for p in game.players if p.is_active)}")

    # Check chip conservation after showdown
    final_total = sum(p.stack for p in game.players) + game.pot
    print(f"\n✓ Chip conservation check:")
    print(f"  Initial: ${initial_total}")
    print(f"  Final:   ${final_total}")
    print(f"  Pot:     ${game.pot}")

    if initial_total != final_total:
        print(f"\n❌ FAIL: Chips not conserved!")
        print(f"  Missing: ${initial_total - final_total}")
        print("\n  Player stacks:")
        for p in game.players:
            print(f"    {p.name}: ${p.stack}")
        return False

    if game.pot != 0:
        print(f"\n⚠️  WARNING: Pot not awarded (pot = ${game.pot})")
        print("  This means pot is still sitting there, will be lost on next hand!")
        return False

    print(f"\n✅ PASS: Chips conserved perfectly!")
    print(f"✅ PASS: Pot awarded (pot = $0)")

    # Check that winner_info events exist
    pot_awards = [e for e in game.current_hand_events if e.event_type == "pot_award"]
    if pot_awards:
        print(f"\n✓ Pot award events logged: {len(pot_awards)}")
        for event in pot_awards:
            winner = next((p for p in game.players if p.player_id == event.player_id), None)
            print(f"  - {winner.name if winner else 'Unknown'} won ${event.amount}")
    else:
        print(f"\n⚠️  No pot_award events logged (winner modal won't show)")

    print(f"\n" + "=" * 70)
    print(f"✅ ALL CHECKS PASSED - Showdown pot award works!")
    print(f"=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_showdown_pot_award()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
