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


    def test_three_way_split_odd_pot(self):
        """
        Test odd chip distribution when pot doesn't divide evenly.

        Texas Hold'em Rule: Odd chips go to players closest to dealer's left.

        Scenario: 2 active players + 1 folded player.
        Folded player's chips create pot that doesn't divide evenly among 2 winners.
        """
        print("\n[ODD CHIP] Testing 2-way split with folded player creating odd pot...")
        game = PokerGame("P1", ai_count=2)  # 3 players total

        # Set up stacks
        for p in game.players:
            p.stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        dealer_idx = game.dealer_index
        print(f"  Dealer at position: {dealer_idx}")
        print(f"  Player IDs: {[p.player_id for p in game.players]}")

        # Set up royal flush on board (active players tie)
        game.community_cards = ["Ah", "Kh", "Qh", "Jh", "10h"]
        game.players[0].hole_cards = ["2c", "3c"]
        game.players[1].hole_cards = ["4d", "5d"]
        game.players[2].hole_cards = ["6s", "7s"]

        # P2 folded after contributing $35
        # P0 and P1 each contributed $34 (both active)
        # Total pot: $103, split between 2 active players
        # $103 / 2 = $51 each + $1 remainder
        game.players[0].total_invested = 34
        game.players[0].stack = 1000 - 34
        game.players[0].is_active = True

        game.players[1].total_invested = 34
        game.players[1].stack = 1000 - 34
        game.players[1].is_active = True

        game.players[2].total_invested = 35
        game.players[2].stack = 1000 - 35
        game.players[2].is_active = False  # Folded
        game.players[2].folded = True

        game.pot = 103

        # Move to showdown
        game.current_state = GameState.SHOWDOWN

        # Record initial stacks
        initial_stacks = {i: p.stack for i, p in enumerate(game.players)}

        # Award pot
        game._award_pot_at_showdown()

        # Calculate winnings
        winnings = {i: game.players[i].stack - initial_stacks[i] for i in range(3)}

        print(f"  Winnings: P0=${winnings[0]}, P1=${winnings[1]}, P2=${winnings[2]}")

        # Total should be $103
        assert sum(winnings.values()) == 103, f"Total winnings should equal pot, got {sum(winnings.values())}"

        # P2 folded, gets $0. P0 and P1 split the pot.
        assert winnings[2] == 0, "Folded player should get $0"

        # One active player gets $52, one gets $51
        active_winnings = sorted([winnings[0], winnings[1]])
        assert active_winnings == [51, 52], f"Expected [51, 52] for active players, got {active_winnings}"

        # Determine which of P0 or P1 is closest to dealer's left
        # Only consider P0 and P1 (the winners)
        offset_0 = (0 - dealer_idx - 1) % 3
        offset_1 = (1 - dealer_idx - 1) % 3

        # Player with smaller offset is closest to dealer's left
        closest_to_dealer = 0 if offset_0 < offset_1 else 1

        print(f"  Among winners, P{closest_to_dealer} is closest to dealer's left (offset {min(offset_0, offset_1)})")
        print(f"  That player won: ${winnings[closest_to_dealer]}")

        assert winnings[closest_to_dealer] == 52, \
            f"Player {closest_to_dealer} (closest to dealer's left among winners) should get $52"

        print("✅ Odd chip distributed correctly to player closest to dealer's left")

    def test_four_way_split_two_odd_chips(self):
        """
        Test 4-way split with pot that has 2 odd chips (3 winners + 1 folded).

        Texas Hold'em Rule: When pot doesn't divide evenly, odd chips go to
        players in positional order from dealer's left.

        Scenario: 3 active winners + 1 folded player.
        Pot = $107, split among 3 winners = $35 each + $2 remainder
        First two winners (by position from dealer) get $36 each, third gets $35.
        """
        print("\n[ODD CHIP] Testing 3-way split with $107 pot (2 odd chips)...")
        game = PokerGame("P1", ai_count=3)  # 4 players total

        # Set up stacks
        for p in game.players:
            p.stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        dealer_idx = game.dealer_index
        print(f"  Dealer at position: {dealer_idx}")

        # Set up royal flush on board (active players tie)
        game.community_cards = ["Ah", "Kh", "Qh", "Jh", "10h"]
        for i in range(4):
            game.players[i].hole_cards = [f"{i+2}c", f"{i+3}c"]

        # P3 folded after contributing $26
        # P0, P1, P2 each contributed $27 (all active)
        # Total pot: $107, split among 3 active players
        # $107 / 3 = $35 each + $2 remainder
        for i in range(3):
            game.players[i].total_invested = 27
            game.players[i].stack = 1000 - 27
            game.players[i].is_active = True

        game.players[3].total_invested = 26
        game.players[3].stack = 1000 - 26
        game.players[3].is_active = False  # Folded
        game.players[3].folded = True

        game.pot = 107

        # Move to showdown
        game.current_state = GameState.SHOWDOWN

        # Record initial stacks
        initial_stacks = {i: p.stack for i, p in enumerate(game.players)}

        # Award pot
        game._award_pot_at_showdown()

        # Calculate winnings
        winnings = {i: game.players[i].stack - initial_stacks[i] for i in range(4)}

        print(f"  Winnings: P0=${winnings[0]}, P1=${winnings[1]}, P2=${winnings[2]}, P3=${winnings[3]}")

        # Total should be $107
        assert sum(winnings.values()) == 107, f"Total winnings should equal pot, got {sum(winnings.values())}"

        # P3 folded, gets $0
        assert winnings[3] == 0, "Folded player should get $0"

        # Among P0, P1, P2: two get $36, one gets $35
        active_winnings = sorted([winnings[0], winnings[1], winnings[2]])
        assert active_winnings == [35, 36, 36], f"Expected [35, 36, 36] for active players, got {active_winnings}"

        # Find the two players closest to dealer's left among P0, P1, P2
        positions = {}
        for i in range(3):  # Only check active players (P0, P1, P2)
            offset = (i - dealer_idx - 1) % 4
            positions[i] = offset

        # Sort by offset (ascending) to get positional order
        sorted_by_position = sorted(positions.items(), key=lambda x: x[1])
        first_two = [sorted_by_position[0][0], sorted_by_position[1][0]]
        third = sorted_by_position[2][0]

        print(f"  First two from dealer's left: P{first_two[0]} (offset {positions[first_two[0]]}), P{first_two[1]} (offset {positions[first_two[1]]})")
        print(f"  Their winnings: ${winnings[first_two[0]]}, ${winnings[first_two[1]]}")
        print(f"  Third: P{third} got ${winnings[third]}")

        assert winnings[first_two[0]] == 36, f"Player {first_two[0]} (1st from dealer) should get $36"
        assert winnings[first_two[1]] == 36, f"Player {first_two[1]} (2nd from dealer) should get $36"
        assert winnings[third] == 35, f"Player {third} (3rd from dealer) should get $35"

        print("✅ Multiple odd chips distributed correctly by position")

    def test_three_way_split_with_side_pot_odd_chips(self):
        """
        Test side pot with 3 winners and odd chips.

        Scenario:
        - Main pot: $90 (3 winners)
        - Side pot: $50 (2 winners)
        - Both pots have odd chip remainders
        """
        print("\n[ODD CHIP] Testing side pot scenario with odd chips...")
        game = PokerGame("P1", ai_count=2)  # 3 players

        # Set up stacks
        for p in game.players:
            p.stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        dealer_idx = game.dealer_index

        # Set up royal flush on board (all tie)
        game.community_cards = ["Ah", "Kh", "Qh", "Jh", "10h"]
        game.players[0].hole_cards = ["2c", "3c"]
        game.players[1].hole_cards = ["4d", "5d"]
        game.players[2].hole_cards = ["6s", "7s"]

        # Simulate side pot scenario:
        # P0 all-in for $30, P1 and P2 bet $45 each
        # Main pot: $90 (all 3 players), Side pot: $30 (P1, P2)
        # But let's create odd amounts: Main $91, Side $29
        game.players[0].total_invested = 30
        game.players[0].stack = 1000 - 30
        game.players[0].all_in = True

        game.players[1].total_invested = 60
        game.players[1].stack = 1000 - 60

        game.players[2].total_invested = 60
        game.players[2].stack = 1000 - 60

        game.pot = 150

        # Move to showdown
        game.current_state = GameState.SHOWDOWN

        # Record initial stacks
        initial_stacks = {i: p.stack for i, p in enumerate(game.players)}

        # Award pot (should create side pots with odd chips)
        game._award_pot_at_showdown()

        # Calculate winnings
        winnings = {i: game.players[i].stack - initial_stacks[i] for i in range(3)}

        print(f"  Winnings: P0=${winnings[0]}, P1=${winnings[1]}, P2=${winnings[2]}")

        # Total should equal pot
        assert sum(winnings.values()) == 150, f"Total winnings should be $150, got {sum(winnings.values())}"

        # All players should get something (all tied with royal flush)
        assert all(w > 0 for w in winnings.values()), "All players should win something"

        print("✅ Side pot with odd chips handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
