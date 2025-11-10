#!/usr/bin/env python3
"""Test chip conservation across multiple hands naturally (no manual manipulation)."""

import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

random.seed(42)  # Reproducible

def play_random_hand(game):
    """Play one hand with random actions until completion."""
    game.start_new_hand()

    hand_num = game.hand_count
    print(f"\n{'='*70}")
    print(f"HAND #{hand_num}")
    print(f"{'='*70}")
    print(f"Starting stacks:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack} (active={p.is_active})")
    print(f"Pot: ${game.pot}")
    print(f"Total: ${sum(p.stack for p in game.players) + game.pot}")

    # Play until hand completes
    max_actions = 50
    action_count = 0

    while game.current_state != GameState.SHOWDOWN and action_count < max_actions:
        human = next((p for p in game.players if p.is_human), None)
        current = game.get_current_player()

        if not current:
            break

        if current == human:
            # Random human action
            actions = ["fold", "call"]
            action = random.choice(actions)
            try:
                game.submit_human_action(action)
            except:
                # If action fails, try fold
                try:
                    game.submit_human_action("fold")
                except:
                    break

        action_count += 1

    print(f"\nHand complete (state={game.current_state.value}):")
    print(f"Final stacks:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Pot: ${game.pot}")
    print(f"Total: ${sum(p.stack for p in game.players) + game.pot}")

    # Check conservation
    total = sum(p.stack for p in game.players) + game.pot
    if total != 4000:
        print(f"🚨 CHIP LOSS! Missing ${4000 - total}")
        return False
    return True

def test_multi_hand_game():
    """Play multiple hands and check chip conservation."""
    print("="*70)
    print("MULTI-HAND CHIP CONSERVATION TEST")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    for hand_num in range(20):
        try:
            if not play_random_hand(game):
                print(f"\n❌ Chip conservation violated at hand {hand_num + 1}")
                return False

            # Check if any player is busted
            busted = [p for p in game.players if p.stack == 0]
            if busted:
                print(f"\n⚠️  Busted players: {[p.name for p in busted]}")

        except Exception as e:
            print(f"\n❌ ERROR at hand {hand_num + 1}: {e}")
            import traceback
            traceback.print_exc()
            return False

    print(f"\n✅ All 20 hands completed with chip conservation!")
    return True

if __name__ == "__main__":
    success = test_multi_hand_game()
    sys.exit(0 if success else 1)
