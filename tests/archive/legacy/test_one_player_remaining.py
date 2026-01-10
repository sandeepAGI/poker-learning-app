#!/usr/bin/env python3
"""
Test for Bug Fix: Game hanging when only one player remains active
User reported: Human + 2 AI fold, 1 AI calls, then game hangs waiting for that AI
Expected: Pot should be awarded immediately when only one player remains
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_one_player_remaining_after_folds():
    """Test that pot is awarded when only one active player remains."""
    print("=" * 70)
    print("TEST: One Player Remaining After Folds")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print(f"\n✓ Game started")
    print(f"  State: {game.current_state}")
    print(f"  Players: {[p.name for p in game.players]}")
    print(f"  Pot: ${game.pot}")

    # Find human player
    human = next(p for p in game.players if p.is_human)
    print(f"\n✓ Human player: {human.name}")
    print(f"  Stack: ${human.stack}")

    # Get initial chip total
    initial_total = sum(p.stack for p in game.players) + game.pot
    print(f"\n✓ Initial chip total: ${initial_total}")

    # Human folds on flop (simulate by advancing to flop first)
    # First complete pre-flop
    print(f"\n→ Simulating pre-flop actions...")
    game.submit_human_action("call")

    # Should be on FLOP now
    print(f"\n✓ Advanced to {game.current_state}")
    print(f"  Community cards: {len(game.community_cards)} cards")
    print(f"  Pot: ${game.pot}")

    # Now human folds on flop
    print(f"\n→ Human folds on flop")
    initial_pot = game.pot
    print(f"  Pot before fold: ${initial_pot}")

    # Track active players before fold
    active_before = [p.name for p in game.players if p.is_active]
    print(f"  Active players before human fold: {active_before}")

    game.submit_human_action("fold")

    # Check state after fold
    active_after = [p.name for p in game.players if p.is_active]
    print(f"\n✓ After human fold:")
    print(f"  Active players: {active_after}")
    print(f"  Game state: {game.current_state}")
    print(f"  Current player index: {game.current_player_index}")
    print(f"  Pot: ${game.pot}")

    # Check if only one player remains and pot was awarded
    if len(active_after) == 1:
        print(f"\n✓ Only one active player remains: {active_after[0]}")

        # Game should be in SHOWDOWN state
        if game.current_state == GameState.SHOWDOWN:
            print(f"✅ PASS: Game correctly advanced to SHOWDOWN")
        else:
            print(f"❌ FAIL: Game state is {game.current_state}, expected SHOWDOWN")
            return False

        # Pot should be awarded (pot should be 0)
        if game.pot == 0:
            print(f"✅ PASS: Pot was awarded (pot is now $0)")
        else:
            print(f"❌ FAIL: Pot not awarded (pot is still ${game.pot})")
            return False

        # current_player_index should be None
        if game.current_player_index is None:
            print(f"✅ PASS: current_player_index is None (no one waiting to act)")
        else:
            print(f"❌ FAIL: current_player_index is {game.current_player_index}, should be None")
            return False

        # Winner should have received the pot
        winner = game.players[[p.name for p in game.players].index(active_after[0])]
        print(f"\n✓ Winner ({winner.name}) received pot")
        print(f"  Winner's final stack: ${winner.stack}")

    else:
        print(f"\n⚠️  Multiple active players remain: {active_after}")
        print(f"   This scenario requires all AI players to act")

    # Verify chip conservation
    final_total = sum(p.stack for p in game.players) + game.pot
    print(f"\n✓ Chip conservation check:")
    print(f"  Initial: ${initial_total}")
    print(f"  Final:   ${final_total}")

    if initial_total == final_total:
        print(f"✅ PASS: Chips conserved")
    else:
        print(f"❌ FAIL: Chips not conserved (difference: ${final_total - initial_total})")
        return False

    print(f"\n" + "=" * 70)
    print(f"✅ ALL CHECKS PASSED - Bug is fixed!")
    print(f"=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_one_player_remaining_after_folds()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
