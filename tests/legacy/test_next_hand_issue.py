#!/usr/bin/env python3
"""
Test for bugs discovered during user testing:
1. Pot not reflected in stack after winning
2. Next hand hangs waiting for AI to act
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_pot_award_and_next_hand():
    """Test that pot is awarded correctly and next hand starts properly."""
    print("=" * 70)
    print("TEST: Pot Award + Next Hand Auto-Processing")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    print(f"\n✓ Game created with 4 players")

    # Start first hand
    game.start_new_hand()
    print(f"✓ First hand started")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot}")

    # Find human player
    human = next(p for p in game.players if p.is_human)
    initial_stack = human.stack
    print(f"\n✓ Human player: {human.name}")
    print(f"  Initial stack: ${initial_stack}")

    # Track total chips
    def check_chip_conservation():
        total = sum(p.stack for p in game.players) + game.pot
        if total != 4000:
            print(f"❌ CHIP CONSERVATION VIOLATED: Total = ${total}")
            return False
        return True

    # Simulate human folding
    print(f"\n→ Human folds pre-flop")
    game.submit_human_action("fold")

    print(f"\n✓ After human fold:")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot}")
    active_players = [p.name for p in game.players if p.is_active]
    print(f"  Active players: {active_players}")

    # Wait for hand to complete (should auto-process to SHOWDOWN)
    if game.current_state == GameState.SHOWDOWN:
        print(f"✅ PASS: Hand completed and reached SHOWDOWN")
    else:
        print(f"❌ FAIL: Hand stuck in {game.current_state}, expected SHOWDOWN")
        return False

    # Check pot was awarded
    if game.pot == 0:
        print(f"✅ PASS: Pot was awarded (pot now $0)")
    else:
        print(f"❌ FAIL: Pot not awarded (pot still ${game.pot})")
        return False

    # Find winner and check their stack increased
    winner = next((p for p in game.players if p.is_active), None)
    if winner:
        print(f"\n✓ Winner: {winner.name}")
        print(f"  Winner's stack: ${winner.stack}")
        if winner.stack > 1000:  # Winner should have more than starting amount
            print(f"✅ PASS: Winner's stack increased")
        else:
            print(f"⚠️  Winner's stack didn't increase much")

    # Check chip conservation after hand 1
    if not check_chip_conservation():
        return False
    print(f"✅ PASS: Chips conserved after hand 1")

    # Now start next hand
    print(f"\n" + "=" * 70)
    print(f"STARTING NEXT HAND")
    print(f"=" * 70)

    game.start_new_hand()
    print(f"\n✓ Next hand started")
    print(f"  State: {game.current_state}")
    print(f"  Pot: ${game.pot} (should be $15 for blinds)")
    print(f"  Current player index: {game.current_player_index}")

    # Check blinds were posted
    if game.pot == 15:
        print(f"✅ PASS: Blinds posted correctly")
    else:
        print(f"❌ FAIL: Blinds incorrect (pot = ${game.pot}, expected $15)")
        return False

    # Check if game is waiting on a player
    if game.current_player_index is not None:
        current_player = game.players[game.current_player_index]
        print(f"\n✓ Current player to act: {current_player.name}")

        # If current player is AI and game is still pre-flop, that's wrong
        # AI should have already acted via _process_remaining_actions()
        if not current_player.is_human and game.current_state == GameState.PRE_FLOP:
            print(f"❌ FAIL: Game is waiting for AI ({current_player.name}) to act")
            print(f"   This means _process_remaining_actions() wasn't called!")
            return False
        elif current_player.is_human:
            print(f"✅ PASS: Game correctly waiting for human player")
    else:
        print(f"✓ Current player index: None (all AI have acted or all-in)")

    # Check chip conservation after hand 2
    if not check_chip_conservation():
        return False
    print(f"✅ PASS: Chips conserved after hand 2")

    # Check human player's stack
    human_stack_after = human.stack
    print(f"\n✓ Human player stack:")
    print(f"  Before: ${initial_stack}")
    print(f"  After:  ${human_stack_after}")
    print(f"  Change: ${human_stack_after - initial_stack}")

    if human.is_active:
        print(f"✅ PASS: Human player still active in new hand")
    else:
        print(f"⚠️  Human player not active (folded)")

    print(f"\n" + "=" * 70)
    print(f"✅ ALL CHECKS PASSED - Both bugs fixed!")
    print(f"=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_pot_award_and_next_hand()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
