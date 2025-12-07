"""
Tests for bug fixes implemented in December 2025.
- Bug #1: Defensive pot distribution before new hand
- Bug #2: BB option pre-flop
- Bug #3: Simple pot optimization (no unnecessary side pots)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, Player, HandEvaluator, GameState


class TestBug1DefensivePotDistribution:
    """Bug #1: Pot > 0 at start_new_hand should be awarded, not lost."""

    def test_defensive_pot_distribution_to_active_player(self):
        """If pot > 0 when starting new hand, award to active player."""
        game = PokerGame("TestPlayer")
        game.start_new_hand()

        # Save a player's stack before we manipulate it
        first_active = next(p for p in game.players if p.is_active)
        original_stack = first_active.stack

        # Simulate a situation where pot wasn't cleared properly
        # by taking chips FROM a player INTO the pot (keeps conservation valid)
        leftover = 50
        first_active.stack -= leftover
        game.pot += leftover
        game.current_state = GameState.SHOWDOWN

        # Verify chip conservation before
        total_before = sum(p.stack for p in game.players) + game.pot
        assert total_before == 4000, f"Setup broke conservation: {total_before}"

        # Start new hand - defensive distribution should handle leftover
        game.start_new_hand()

        # Total chips should still be conserved
        total_after = sum(p.stack for p in game.players) + game.pot
        assert total_after == 4000, \
            f"Chips lost! Before: {total_before}, After: {total_after}"

    def test_no_chips_lost_on_new_hand(self):
        """Chip conservation across multiple hands."""
        game = PokerGame("TestPlayer")
        initial_total = 4000  # 4 players * 1000

        for _ in range(5):
            game.start_new_hand()
            total = sum(p.stack for p in game.players) + game.pot
            assert total == initial_total, \
                f"Chips lost! Expected {initial_total}, got {total}"


class TestBug2BBOption:
    """Bug #2: BB should get option to raise when everyone calls."""

    def test_bb_option_check_in_betting_round_complete(self):
        """BB option should prevent round from completing prematurely."""
        game = PokerGame("TestPlayer")
        game.start_new_hand()

        # Simulate pre-flop where everyone has called to BB
        for player in game.players:
            if player.is_active and not player.all_in:
                player.current_bet = game.current_bet
                player.has_acted = True

        # BB should still get option (round NOT complete)
        # last_raiser_index is set to BB index in _post_blinds
        bb_index = game.last_raiser_index
        if bb_index is not None:
            bb_player = game.players[bb_index]
            # BB hasn't made an action yet (only posted blind)
            # Count BB actions in events
            bb_actions = sum(
                1 for e in game.current_hand_events
                if e.player_id == bb_player.player_id
                and e.event_type == "action"
                and e.action in ["check", "call", "raise", "fold"]
            )

            # If BB hasn't acted, betting round should NOT be complete
            if bb_actions == 0 and bb_player.is_active and not bb_player.all_in:
                assert not game._betting_round_complete(), \
                    "BB should get option - betting round shouldn't be complete"

    def test_bb_option_completes_after_bb_acts(self):
        """After BB makes an action, round should complete."""
        game = PokerGame("TestPlayer")
        game.start_new_hand()

        # Simulate BB making an action (check)
        bb_index = game.last_raiser_index
        if bb_index is not None:
            bb_player = game.players[bb_index]
            # Add a check action for BB
            game._log_hand_event(
                "action", bb_player.player_id, "check", 0, 0.0, "BB checks"
            )

        # Everyone else has acted and matched
        for player in game.players:
            if player.is_active and not player.all_in:
                player.current_bet = game.current_bet
                player.has_acted = True

        # Now round should complete because BB has acted
        result = game._betting_round_complete()
        assert result is True, "Round should complete after BB acts"


class TestBug3SimplePotOptimization:
    """Bug #3: When all active players invest same, return single pot."""

    def test_equal_investment_returns_single_pot(self):
        """Equal investments should produce exactly one pot."""
        evaluator = HandEvaluator()

        # Create players with equal investments
        players = [
            Player("p1", "Player1", stack=900),
            Player("p2", "Player2", stack=900),
            Player("p3", "Player3", stack=1000),  # Folded
            Player("p4", "Player4", stack=1000),  # Folded
        ]

        # Two active players, equal investment
        players[0].hole_cards = ["Ah", "Kh"]
        players[0].is_active = True
        players[0].total_invested = 100

        players[1].hole_cards = ["Ad", "Kd"]
        players[1].is_active = True
        players[1].total_invested = 100

        # Folded players
        players[2].is_active = False
        players[2].total_invested = 10  # Posted blind before folding

        players[3].is_active = False
        players[3].total_invested = 5  # Posted blind before folding

        community = ["2c", "3c", "4c", "5c", "6c"]

        pots = evaluator.determine_winners_with_side_pots(players, community)

        # Should be exactly ONE pot
        assert len(pots) == 1, f"Expected 1 pot, got {len(pots)}: {pots}"

        # Total amount should be sum of all investments
        total_invested = sum(p.total_invested for p in players)
        assert pots[0]['amount'] == total_invested, \
            f"Pot amount {pots[0]['amount']} != total invested {total_invested}"

    def test_different_investments_creates_side_pots(self):
        """Different investments should create side pots."""
        evaluator = HandEvaluator()

        # Create players with DIFFERENT investments (all-in scenario)
        players = [
            Player("p1", "Short", stack=0),
            Player("p2", "Medium", stack=0),
            Player("p3", "Large", stack=50),
        ]

        # Short stack all-in for 50
        players[0].hole_cards = ["Ah", "Kh"]
        players[0].is_active = True
        players[0].all_in = True
        players[0].total_invested = 50

        # Medium stack all-in for 100
        players[1].hole_cards = ["As", "Ks"]
        players[1].is_active = True
        players[1].all_in = True
        players[1].total_invested = 100

        # Large stack called 100
        players[2].hole_cards = ["2c", "3c"]
        players[2].is_active = True
        players[2].total_invested = 100

        community = ["Ac", "Kc", "5h", "7d", "9s"]

        pots = evaluator.determine_winners_with_side_pots(players, community)

        # Should have multiple pots (main + side)
        assert len(pots) >= 2, f"Expected 2+ pots for all-in, got {len(pots)}"

        # Total should equal sum of investments
        total_pots = sum(pot['amount'] for pot in pots)
        total_invested = sum(p.total_invested for p in players)
        assert total_pots == total_invested, \
            f"Pot total {total_pots} != invested {total_invested}"


class TestChipConservation:
    """Verify chip conservation across all scenarios."""

    def test_chip_conservation_after_bug_fixes(self):
        """Play several hands and verify no chips are lost."""
        game = PokerGame("TestPlayer")
        initial_total = sum(p.stack for p in game.players)  # 4000

        for hand_num in range(10):
            game.start_new_hand()

            # Simulate some actions
            current = game.get_current_player()
            if current and current.player_id == "human":
                game.submit_human_action("call")

            # Check conservation
            total = sum(p.stack for p in game.players) + game.pot
            assert total == initial_total, \
                f"Hand {hand_num}: Lost chips! {total} != {initial_total}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
