"""
Test odd chip distribution in split pots.

Texas Hold'em Rule: When a pot cannot be split evenly, the odd chip(s)
go to the player closest to the left of the dealer button (earliest
position clockwise from the dealer).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestOddChipDistribution:
    """Test odd chip distribution in split pots.

    Note: Odd chip scenarios are difficult to test in isolation due to chip
    conservation constraints. The implementation sorts winners by position
    relative to dealer when distributing odd chips, which is verified by
    code inspection and integration tests with side pots.
    """

    def test_odd_chip_two_way_split_odd_pot(self):
        """In 2-way split with odd pot, player left of dealer gets extra."""
        print("\n[ODD CHIP] Testing 2-way split with $101 pot...")
        game = PokerGame("P1", ai_count=1)  # Just 2 players for simplicity

        # Set up stacks
        for p in game.players:
            p.stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        dealer_idx = game.dealer_index
        other_idx = 1 - dealer_idx  # The other player
        print(f"  Dealer at position: {dealer_idx}")
        print(f"  Other player at position: {other_idx}")

        # Set up royal flush on board
        game.community_cards = ["Ah", "Kh", "Qh", "Jh", "10h"]
        game.players[0].hole_cards = ["2c", "3c"]
        game.players[1].hole_cards = ["4d", "5d"]

        # Create odd pot: $101 / 2 = $50 each + $1 remainder
        # The $1 should go to the player left of dealer
        game.players[0].total_invested = 51
        game.players[0].stack = 1000 - 51  # Deduct invested chips
        game.players[1].total_invested = 50
        game.players[1].stack = 1000 - 50  # Deduct invested chips
        game.pot = 101

        # Move to showdown
        game.current_state = GameState.SHOWDOWN

        # Record initial stacks
        initial_stacks = {i: p.stack for i, p in enumerate(game.players)}

        # Award pot
        game._award_pot_at_showdown()

        # Calculate winnings
        winnings = {i: game.players[i].stack - initial_stacks[i] for i in range(2)}

        print(f"  Winnings: P{0}=${winnings[0]}, P{1}=${winnings[1]}")

        # Total should be $101
        assert sum(winnings.values()) == 101, "Total winnings should equal pot"

        # One player gets $51, one gets $50
        winning_amounts = sorted(winnings.values())
        assert winning_amounts == [50, 51], f"Expected [50, 51], got {winning_amounts}"

        # The player left of dealer should get $51
        # In heads-up, dealer is position dealer_idx, so player left is (dealer_idx + 1) % 2
        player_left_of_dealer = (dealer_idx + 1) % 2

        print(f"  Player left of dealer: {player_left_of_dealer}")
        print(f"  That player won: ${winnings[player_left_of_dealer]}")

        assert winnings[player_left_of_dealer] == 51, \
            f"Player {player_left_of_dealer} (left of dealer) should get $51"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
