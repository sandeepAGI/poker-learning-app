#!/usr/bin/env python3
"""Detailed reproduction of chip loss bug from simulation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_chip_loss_scenario():
    """
    Reproduce the exact scenario from simulation:
    - Player goes bust (stack=0)
    - Start new hand
    - Chips disappear during blind posting
    """
    game = PokerGame("Player", ai_count=3)

    # Simulate player going bust after a hand
    print("="*70)
    print("SCENARIO: Player goes bust, then new hand starts")
    print("="*70)

    # Play one hand to completion
    game.start_new_hand()
    print(f"\nHand 1 started:")
    print(f"  Total chips: ${sum(p.stack for p in game.players) + game.pot}")
    print(f"  Pot: ${game.pot}")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")

    # Manually bust the player by transferring their chips to AI
    print(f"\n>>> Manually busting player...")
    transfer_amount = game.players[0].stack
    game.players[0].stack = 0
    game.players[1].stack += transfer_amount

    print(f"After bust:")
    print(f"  Total chips: ${sum(p.stack for p in game.players) + game.pot}")
    for p in game.players:
        print(f"  {p.name}: ${p.stack} (active={p.is_active})")

    # Move to showdown
    game.current_state = GameState.SHOWDOWN
    game.pot = 0  # Pot already awarded

    print(f"\nAt SHOWDOWN (pot awarded):")
    print(f"  Total chips: ${sum(p.stack for p in game.players) + game.pot}")
    print(f"  Pot: ${game.pot}")

    # Start new hand (this is where chip loss happens)
    print(f"\n>>> Starting new hand...")
    try:
        # Temporarily disable QC to see what happens
        game.qc_enabled = False
        game.start_new_hand()

        print(f"\nAfter start_new_hand():")
        print(f"  Total chips: ${sum(p.stack for p in game.players) + game.pot}")
        print(f"  Pot: ${game.pot}")
        for p in game.players:
            print(f"  {p.name}: ${p.stack}, current_bet=${p.current_bet}, total_invested=${p.total_invested}, active={p.is_active}")

        # Check chip conservation manually
        total = sum(p.stack for p in game.players) + game.pot
        if total != game.total_chips:
            print(f"\n🚨 CHIP LOSS DETECTED!")
            print(f"   Expected: ${game.total_chips}")
            print(f"   Got: ${total}")
            print(f"   Missing: ${game.total_chips - total}")
        else:
            print(f"\n✅ Chip conservation OK")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_chip_loss_scenario()
