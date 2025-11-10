#!/usr/bin/env python3
"""
Debug test for chip conservation issue.
Runs until first error, then prints detailed game state.
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def get_valid_actions(game: PokerGame):
    """Get list of valid actions for current player."""
    human = game.players[0]
    actions = []

    if game.players[game.current_player_index] == human:
        actions.append({"type": "fold", "amount": 0})

    call_amount = game.current_bet - human.current_bet
    if call_amount >= 0 and human.stack >= call_amount:
        actions.append({"type": "call", "amount": 0})

    if human.stack > call_amount:
        min_raise = game.current_bet + game.big_blind
        max_raise = human.stack
        if human.stack >= min_raise - human.current_bet:
            raise_amount = random.randint(
                max(min_raise - human.current_bet, game.big_blind),
                max_raise
            )
            actions.append({"type": "raise", "amount": raise_amount})

    return actions

def play_hand(game: PokerGame, hand_num: int):
    """Play a single hand."""
    print(f"\n{'='*70}")
    print(f"HAND #{hand_num}")
    print(f"{'='*70}")

    # Print stacks before hand
    print("\nStacks before hand:")
    total_before = 0
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
        total_before += p.stack
    print(f"  Total: ${total_before}")
    print(f"  Pot: ${game.pot}")

    try:
        game.start_new_hand()

        # Print stacks after blinds
        print("\nAfter blinds posted:")
        for p in game.players:
            print(f"  {p.name}: ${p.stack}, invested=${p.total_invested}")
        print(f"  Pot: ${game.pot}")
        print(f"  Current bet: ${game.current_bet}")

        # Play until showdown
        max_actions = 100
        actions_count = 0

        while game.current_state != GameState.SHOWDOWN and actions_count < max_actions:
            if game.current_player_index is None:
                break

            human = game.players[0]
            current_player = game.players[game.current_player_index]

            if current_player == human and human.is_active and not human.all_in:
                valid_actions = get_valid_actions(game)
                if not valid_actions:
                    break

                # Weighted random action
                action = random.choices(
                    valid_actions,
                    weights=[30 if a["type"]=="fold" else 50 if a["type"]=="call" else 20 for a in valid_actions],
                    k=1
                )[0]

                print(f"\n{human.name} action: {action['type']}" +
                      (f" ${action['amount']}" if action['amount'] else ""))

                result = game.submit_human_action(action["type"], action["amount"])
                if not result:
                    game.submit_human_action("fold")

                actions_count += 1
            else:
                break

        # Print final state
        print(f"\nHand complete - State: {game.current_state.value}")
        print("\nFinal stacks:")
        total_after = 0
        for p in game.players:
            print(f"  {p.name}: ${p.stack}")
            total_after += p.stack
        print(f"  Total: ${total_after}")
        print(f"  Pot: ${game.pot}")

        if total_after + game.pot != 4000:
            print(f"\n❌ CHIP CONSERVATION VIOLATED!")
            print(f"   Expected: $4000")
            print(f"   Actual: ${total_after + game.pot}")
            print(f"   Missing: ${4000 - total_after - game.pot}")
            return False

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Chip Conservation Debug Test")
    print("="*70)

    game = PokerGame(human_player_name="Player", ai_count=3)

    for hand_num in range(1, 100):
        success = play_hand(game, hand_num)
        if not success:
            print(f"\n{'='*70}")
            print(f"STOPPED AT HAND #{hand_num}")
            print(f"{'='*70}")
            break

        # Stop if too many players busted
        active_ai = [p for p in game.players[1:] if p.stack > 0]
        if len(active_ai) < 2:
            print(f"\n⚠️  Only {len(active_ai)} AI players with chips - stopping")
            break
    else:
        print(f"\n✅ All 100 hands completed successfully!")

if __name__ == "__main__":
    main()
