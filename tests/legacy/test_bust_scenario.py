#!/usr/bin/env python3
"""Test what happens when a player goes completely bust."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_player_goes_bust():
    """Force a player to go bust and see if chip conservation holds."""
    print("="*70)
    print("TEST: Player Goes Bust Scenario")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    # Play hand 1 normally
    print("\n--- HAND 1 ---")
    game.start_new_hand()
    print(f"After blind posting:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}, invested=${p.total_invested}, active={p.is_active}")
    print(f"Pot: ${game.pot}")
    print(f"Total: ${sum(p.stack for p in game.players) + game.pot}")

    # Human folds immediately
    game.submit_human_action("fold")

    print(f"\nAfter human folds:")
    print(f"  State: {game.current_state.value}")
    print(f"  Pot: ${game.pot}")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Total: ${sum(p.stack for p in game.players) + game.pot}")

    # Manually bust the player by giving their chips to AI
    # (Simulating them losing all chips over several hands)
    print(f"\n>>> Manually busting player (simulating losses)...")
    transfer = game.players[0].stack
    game.players[0].stack = 0
    game.players[1].stack += transfer

    print(f"After manual transfer:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Total: ${sum(p.stack for p in game.players) + game.pot}")

    # Now start hand 2 with a busted player
    print(f"\n--- HAND 2 (Player is BUSTED) ---")
    try:
        game.start_new_hand()

        print(f"\nAfter start_new_hand():")
        for p in game.players:
            print(f"  {p.name}: ${p.stack}, invested=${p.total_invested}, active={p.is_active}")
        print(f"Pot: ${game.pot}")

        total = sum(p.stack for p in game.players) + game.pot
        print(f"Total: ${total}")

        if total != game.total_chips:
            print(f"\n🚨 CHIP LOSS DETECTED!")
            print(f"   Expected: ${game.total_chips}")
            print(f"   Got: ${total}")
            print(f"   Missing: ${game.total_chips - total}")
            return False
        else:
            print(f"\n✅ Chip conservation OK!")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_player_goes_bust()
    sys.exit(0 if success else 1)
