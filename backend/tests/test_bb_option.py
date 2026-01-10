"""
Test BB Option - Big Blind must get option to raise when all players call pre-flop.

This is a fundamental Texas Hold'em rule that every poker book teaches.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from game.poker_engine import PokerGame, GameState


class TestBigBlindOption(unittest.TestCase):
    """Test that Big Blind gets their option to raise pre-flop."""

    def test_bb_gets_option_when_all_call(self):
        """BB must get option to act again when all players call pre-flop."""
        # Seed random to ensure consistent AI behavior (prevents flaky test)
        import random
        random.seed(42)

        game = PokerGame("Player1")
        # Position dealer so human (index 0) is BB after start_new_hand
        # dealer moves from 1 to 2, so BB = (2+2)%4 = 0 = human
        game.dealer_index = 1
        game.start_new_hand()

        # Identify BB position - should be human
        bb_idx = (game.dealer_index + 2) % len(game.players)
        bb_player = game.players[bb_idx]

        # Track how many times BB acts
        bb_action_count = 0
        human_is_bb = (bb_player.player_id == "human")

        # Track game state to detect infinite loops
        max_iterations = 20
        iterations = 0

        # Play through pre-flop, having all players call
        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_idx = game.current_player_index
            current_player = game.players[current_idx]

            # Track BB actions
            if current_idx == bb_idx:
                bb_action_count += 1

                if human_is_bb:
                    # BB's turn - they should be able to act
                    if bb_action_count == 1:
                        # First action after everyone called - BB has the "option"
                        # Debug: verify state before action
                        human_player = next(p for p in game.players if p.is_human)
                        human_idx = next(i for i, p in enumerate(game.players) if p.is_human)

                        self.assertEqual(game.current_player_index, human_idx,
                            f"Should be human's turn. current={game.current_player_index}, human={human_idx}")
                        self.assertEqual(game.current_state, GameState.PRE_FLOP,
                            f"Should be pre-flop, got {game.current_state}")

                        # Try to raise (BB should be allowed to)
                        # Raise amount must be >= current_bet + last_raise_amount
                        # If AI raised before us, last_raise_amount will be set correctly
                        if game.last_raise_amount is not None:
                            min_raise = game.current_bet + game.last_raise_amount
                        else:
                            min_raise = game.current_bet + game.big_blind
                        success = game.submit_human_action("raise", min_raise)

                        self.assertTrue(success,
                            f"BB should be able to raise to {min_raise}. current_bet={game.current_bet}, "
                            f"human_bet={human_player.current_bet}, stack={human_player.stack}")
                        # Note: After raise, AI may fold causing game to end.
                        break  # Exit loop after BB exercises option
                    else:
                        # After BB raises, just call to advance
                        game.submit_human_action("call")

            elif current_player.is_human:
                # Other human players just call
                game.submit_human_action("call")

            # AI players will act automatically via _process_remaining_actions
            # (triggered by submit_human_action or state advancement)

        # Verify BB got at least one action (their option)
        self.assertGreaterEqual(bb_action_count, 1,
            f"BB must get option to act after everyone calls. "
            f"BB acted {bb_action_count} times.")

        # Verify we didn't hit infinite loop
        self.assertLess(iterations, max_iterations,
            "Game entered infinite loop during pre-flop")


    def test_bb_can_check_option(self):
        """BB should be able to check (not forced to raise) on their option."""
        game = PokerGame("Player1")
        # Position dealer so human (index 0) is BB after start_new_hand
        game.dealer_index = 1
        game.start_new_hand()

        # Identify BB position - should be human
        bb_idx = (game.dealer_index + 2) % len(game.players)
        bb_player = game.players[bb_idx]
        human_is_bb = (bb_player.player_id == "human")

        bb_got_option = False
        max_iterations = 20
        iterations = 0

        # Play through pre-flop
        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_idx = game.current_player_index
            current_player = game.players[current_idx]

            if current_idx == bb_idx and human_is_bb:
                # BB's turn - try to check/call (not raise)
                success = game.submit_human_action("call")
                self.assertTrue(success, "BB should be able to check/call their option")
                bb_got_option = True
            elif current_player.is_human:
                # Other players call
                game.submit_human_action("call")

        self.assertTrue(bb_got_option,
            "BB must get their option to act")


    def test_sb_completes_before_bb_option(self):
        """SB must complete their bet before BB gets their option."""
        game = PokerGame("Player1")
        game.start_new_hand()

        # Identify positions
        sb_idx = (game.dealer_index + 1) % len(game.players)
        bb_idx = (game.dealer_index + 2) % len(game.players)

        sb_player = game.players[sb_idx]
        bb_player = game.players[bb_idx]

        # Track action order
        action_order = []

        max_iterations = 30
        iterations = 0

        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_idx = game.current_player_index
            current_player = game.players[current_idx]

            # Record who acts
            if current_idx == sb_idx:
                action_order.append("SB")
            elif current_idx == bb_idx:
                action_order.append("BB")

            if current_player.is_human:
                game.submit_human_action("call")

        # Verify SB acted, then BB acted (SB must complete to BB)
        # Action order should have SB before BB
        if "SB" in action_order and "BB" in action_order:
            sb_pos = action_order.index("SB")
            bb_pos = action_order.index("BB")

            # BB should act after SB completes
            self.assertGreater(bb_pos, sb_pos,
                "BB option should come after SB completes their bet")


    def test_bb_option_only_pre_flop(self):
        """BB option is specific to pre-flop, not post-flop."""
        game = PokerGame("Player1")
        game.start_new_hand()

        # Play through pre-flop (everyone calls)
        max_iterations = 30
        iterations = 0

        while game.current_state == GameState.PRE_FLOP and iterations < max_iterations:
            iterations += 1

            if game.current_player_index is None:
                break

            current_player = game.players[game.current_player_index]
            if current_player.is_human:
                game.submit_human_action("call")

        # Now we should be on flop
        self.assertNotEqual(game.current_state, GameState.PRE_FLOP,
            "Should have advanced past pre-flop")

        # Post-flop, there's no special "option" - normal betting rules apply
        # This test just verifies we got past pre-flop correctly


if __name__ == '__main__':
    unittest.main()
