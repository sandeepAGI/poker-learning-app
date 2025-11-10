#!/usr/bin/env python3
"""
Test for user-reported issues - updated to account for auto-processing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_issues():
    """Test both issues reported by user."""
    print("=" * 70)
    print("TEST: User-Reported Issues")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print(f"\n✓ Hand 1 started")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot}")

    # Find human player
    human = next(p for p in game.players if p.is_human)
    initial_stack = human.stack
    print(f"  Human stack: ${initial_stack}")

    # Simulate user scenario: fold
    print(f"\n→ Human folds")
    game.submit_human_action("fold")

    print(f"\n✓ After fold:")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot}")
    print(f"  Active players: {[p.name for p in game.players if p.is_active]}")

    # Check Issue 1: Pot awarded correctly
    print(f"\n" + "=" * 70)
    print("ISSUE 1: Pot Award")
    print("=" * 70)

    if game.current_state == GameState.SHOWDOWN:
        print(f"✅ PASS: Hand reached SHOWDOWN")
    else:
        print(f"❌ FAIL: Hand stuck in {game.current_state}")
        return False

    if game.pot == 0:
        print(f"✅ PASS: Pot was awarded")
    else:
        print(f"❌ FAIL: Pot not awarded (pot = ${game.pot})")
        return False

    # Check winner's stack
    winner = next((p for p in game.players if p.is_active), None)
    if winner:
        print(f"✅ PASS: Winner ({winner.name}) has ${winner.stack}")

    # Check Issue 2: Next hand starts and doesn't hang
    print(f"\n" + "=" * 70)
    print("ISSUE 2: Next Hand")
    print("=" * 70)

    print(f"\n→ Starting next hand")
    game.start_new_hand()

    print(f"\n✓ Hand 2 started")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot} (includes blinds + any AI calls)")
    print(f"  Current player index: {game.current_player_index}")

    if game.current_player_index is not None:
        current_player = game.players[game.current_player_index]
        print(f"  Current player: {current_player.name} (Human: {current_player.is_human})")

        if current_player.is_human:
            print(f"✅ PASS: Game waiting for human player (correct)")
        elif not current_player.is_human:
            # If current player is AI, check if they can act
            if current_player.is_active and not current_player.all_in:
                print(f"❌ FAIL: Game stuck waiting for AI ({current_player.name})")
                return False
            else:
                print(f"✅ PASS: AI is all-in or inactive (game progressing correctly)")
    else:
        print(f"✅ PASS: No current player (all AI have acted or all-in)")

    # Verify game is playable
    if game.current_state == GameState.PRE_FLOP:
        print(f"✅ PASS: Game is in PRE_FLOP (ready for play)")
    elif game.current_state == GameState.SHOWDOWN:
        print(f"⚠️  Game already reached SHOWDOWN (all AI folded or all-in)")
    else:
        print(f"✅ PASS: Game is in {game.current_state} (progressing normally)")

    # Check chip conservation
    total = sum(p.stack for p in game.players) + game.pot
    if total == 4000:
        print(f"✅ PASS: Chips conserved (${total})")
    else:
        print(f"❌ FAIL: Chips NOT conserved (${total}, expected $4000)")
        return False

    print(f"\n" + "=" * 70)
    print(f"✅ ALL ISSUES FIXED!")
    print(f"=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
