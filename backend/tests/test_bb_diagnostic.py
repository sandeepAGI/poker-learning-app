"""
Diagnostic test to understand BB option behavior.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState


def test_bb_diagnostic():
    """Diagnostic: trace BB option scenario step by step."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    print("\n=== INITIAL STATE ===")
    print(f"Dealer: Player {game.dealer_index}")

    sb_idx = (game.dealer_index + 1) % len(game.players)
    bb_idx = (game.dealer_index + 2) % len(game.players)

    print(f"SB: Player {sb_idx} ({game.players[sb_idx].name})")
    print(f"BB: Player {bb_idx} ({game.players[bb_idx].name})")
    print(f"Current bet: ${game.current_bet}")
    print(f"Pot: ${game.pot}")

    print("\n=== AFTER BLINDS ===")
    for i, p in enumerate(game.players):
        print(f"Player {i} ({p.name}): " +
              f"current_bet=${p.current_bet}, has_acted={p.has_acted}, " +
              f"is_active={p.is_active}, stack=${p.stack}")

    print(f"\nFirst to act: Player {game.current_player_index}")
    print(f"State: {game.current_state}")

    # Now simulate everyone calling
    print("\n=== SIMULATING PRE-FLOP ACTIONS ===")
    action_count = 0
    max_actions = 20

    while game.current_state == GameState.PRE_FLOP and action_count < max_actions:
        action_count += 1

        if game.current_player_index is None:
            print("current_player_index is None, breaking")
            break

        current_idx = game.current_player_index
        current_player = game.players[current_idx]

        position_label = ""
        if current_idx == sb_idx:
            position_label = " (SB)"
        elif current_idx == bb_idx:
            position_label = " (BB)"

        print(f"\nAction {action_count}: Player {current_idx} ({current_player.name}){position_label} to act")
        print(f"  current_bet=${current_player.current_bet}, game.current_bet=${game.current_bet}")
        print(f"  has_acted={current_player.has_acted}, is_active={current_player.is_active}")

        if current_player.is_human:
            # Human calls
            print(f"  → Human calls")
            success = game.submit_human_action("call")
            print(f"  → Result: {success}")
        else:
            # AI will act automatically
            print(f"  → AI will act automatically")

        # Check if betting round is complete
        is_complete = game._betting_round_complete()
        print(f"  Betting round complete: {is_complete}")

        if is_complete:
            print("  Betting round marked complete, should advance state")
            break

    print("\n=== FINAL STATE ===")
    print(f"State: {game.current_state}")
    print(f"Actions taken: {action_count}")

    for i, p in enumerate(game.players):
        position_label = ""
        if i == sb_idx:
            position_label = " (SB)"
        elif i == bb_idx:
            position_label = " (BB)"

        print(f"Player {i} ({p.name}){position_label}: " +
              f"current_bet=${p.current_bet}, has_acted={p.has_acted}, " +
              f"is_active={p.is_active}")

    # Check if BB got to act
    bb_player = game.players[bb_idx]
    print(f"\nBB has_acted: {bb_player.has_acted}")
    print(f"BB got their option: {bb_player.has_acted}")


if __name__ == '__main__':
    test_bb_diagnostic()
