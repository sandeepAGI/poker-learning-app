"""
Simplified BB Option test - verify BB gets their option regardless of who BB is.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from game.poker_engine import PokerGame, GameState


class TestBBOptionSimple(unittest.TestCase):
    """Test that BB gets their option using hand events."""

    def test_bb_gets_option_via_events(self):
        """Verify BB acts after all other players call, using hand events."""
        game = PokerGame("TestPlayer")
        game.start_new_hand()

        # Identify positions
        sb_idx = (game.dealer_index + 1) % len(game.players)
        bb_idx = (game.dealer_index + 2) % len(game.players)
        bb_player = game.players[bb_idx]

        print(f"\nBB is Player {bb_idx} ({bb_player.name})")

        # Track all actions
        actions_log = []

        max_iterations = 30
        iterations = 0

        # Play through pre-flop
        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_player = game.players[game.current_player_index]

            if current_player.is_human:
                # Human calls
                before_events = len(game.current_hand_events)
                game.submit_human_action("call")
                after_events = len(game.current_hand_events)

                # Log all new events
                for i in range(before_events, after_events):
                    event = game.current_hand_events[i]
                    if event.event_type == "action":
                        actions_log.append(f"{event.player_id}: {event.action}")

        print(f"\nActions taken (from events): {len(actions_log)}")
        for action in actions_log:
            print(f"  {action}")

        # Check if BB acted
        bb_actions = [a for a in actions_log if bb_player.player_id in a]

        print(f"\nBB ({bb_player.player_id}) actions: {bb_actions}")
        print(f"BB has_acted flag: {bb_player.has_acted}")

        # BB should have acted at least once
        self.assertGreaterEqual(len(bb_actions), 1,
            f"BB must act at least once. Found {len(bb_actions)} BB actions in {len(actions_log)} total actions")


    def test_bb_acted_flag_set(self):
        """After pre-flop with all calls, BB should have has_acted=True."""
        game = PokerGame("TestPlayer")
        game.start_new_hand()

        bb_idx = (game.dealer_index + 2) % len(game.players)
        bb_player = game.players[bb_idx]

        # Before pre-flop actions, BB should NOT have acted yet
        # (they posted blind but haven't acted in betting round)
        self.assertFalse(bb_player.has_acted,
            "BB should not have has_acted=True immediately after posting blind")

        # Play through pre-flop
        max_iterations = 30
        iterations = 0

        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_player = game.players[game.current_player_index]
            if current_player.is_human:
                game.submit_human_action("call")

        # After pre-flop, BB should have acted
        self.assertTrue(bb_player.has_acted,
            "BB must have has_acted=True after pre-flop completes")


if __name__ == '__main__':
    unittest.main()
