#!/usr/bin/env python3
"""
Debug test to trace what happens when human folds and only 1 player remains
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_fold_with_debug():
    """Test folding with detailed debug output."""
    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print("=" * 70)
    print("INITIAL STATE AFTER start_new_hand()")
    print("=" * 70)
    print(f"State: {game.current_state}")
    print(f"Pot: ${game.pot}")
    print(f"Current bet: ${game.current_bet}")
    print(f"Current player index: {game.current_player_index}")

    for i, p in enumerate(game.players):
        print(f"  Player {i}: {p.name} | Active: {p.is_active} | Stack: ${p.stack} | Acted: {p.has_acted} | Bet: ${p.current_bet}")

    print(f"\n" + "=" * 70)
    print("HUMAN FOLDS")
    print("=" * 70)

    # Get human player
    human = next((p for p in game.players if p.is_human), None)
    human_index = game.players.index(human)
    print(f"Human is player {human_index}: {human.name}")
    print(f"Human stack before fold: ${human.stack}")

    # Submit fold
    result = game.submit_human_action("fold")
    print(f"\nFold result: {result}")

    print(f"\n" + "=" * 70)
    print("STATE AFTER FOLD")
    print("=" * 70)
    print(f"State: {game.current_state}")
    print(f"Pot: ${game.pot}")
    print(f"Current bet: ${game.current_bet}")
    print(f"Current player index: {game.current_player_index}")

    active_count = sum(1 for p in game.players if p.is_active)
    print(f"\nActive player count: {active_count}")

    for i, p in enumerate(game.players):
        status = "ACTIVE" if p.is_active else "FOLDED"
        print(f"  Player {i}: {p.name} | {status} | Stack: ${p.stack} | Acted: {p.has_acted} | Bet: ${p.current_bet}")

    print(f"\n" + "=" * 70)
    print("HAND EVENTS (last 10)")
    print("=" * 70)
    for event in game.current_hand_events[-10:]:
        print(f"  {event.event_type}: {event.player_id} | {event.action} | ${event.amount} | {event.description[:60]}")

    # Check expected behavior
    print(f"\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    if active_count == 1:
        print(f"✓ Only 1 active player remains")
        if game.current_state == GameState.SHOWDOWN:
            print(f"✅ CORRECT: Game advanced to SHOWDOWN")
        else:
            print(f"❌ BUG: Game in {game.current_state}, should be SHOWDOWN")

        if game.pot == 0:
            print(f"✅ CORRECT: Pot was awarded")
        else:
            print(f"❌ BUG: Pot not awarded (pot = ${game.pot})")
    elif active_count > 1:
        print(f"⚠️  Multiple players still active")
        print(f"   Expected game to continue")
    else:
        print(f"❌ ERROR: No active players!")

    # Check chip conservation
    total = sum(p.stack for p in game.players) + game.pot
    if total == 4000:
        print(f"✅ Chips conserved: ${total}")
    else:
        print(f"❌ Chips NOT conserved: ${total} (expected $4000)")

if __name__ == "__main__":
    test_fold_with_debug()
