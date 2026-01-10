"""
Test dealer button rotation when players are eliminated.

Texas Hold'em Rule: When a player is eliminated (stack = 0), the dealer
button should move to the next active player without skipping anyone.
This ensures fair rotation and prevents players from avoiding blinds.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame


class TestDeadButton:
    """Test dealer button rotation with player elimination."""

    def test_button_skips_eliminated_player(self):
        """When player eliminated, button moves to next active player."""
        print("\n[DEAD BUTTON] Testing button rotation after elimination...")
        game = PokerGame("P1", ai_count=3)

        # Set up stacks: P2 will be eliminated
        game.players[0].stack = 1000
        game.players[1].stack = 0  # P2 eliminated
        game.players[2].stack = 1000
        game.players[3].stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        # Start hand - should skip P2 (eliminated)
        game.start_new_hand(process_ai=False)

        dealer_player = game.players[game.dealer_index]
        print(f"  Dealer index: {game.dealer_index} ({dealer_player.name})")
        print(f"  Dealer has stack: ${dealer_player.stack}")

        # Dealer should never be the eliminated player (P2, index 1)
        assert game.dealer_index != 1, "Dealer should skip eliminated player"
        assert dealer_player.stack > 0, "Dealer must have chips"

    def test_button_rotation_three_players_one_eliminated(self):
        """Button rotates correctly with one eliminated player."""
        print("\n[DEAD BUTTON] Testing rotation with 3 active, 1 eliminated...")
        game = PokerGame("P1", ai_count=3)

        # Eliminate P3 (index 2)
        game.players[0].stack = 1000
        game.players[1].stack = 1000
        game.players[2].stack = 0  # P3 eliminated
        game.players[3].stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        # Track dealer positions for 5 hands
        dealer_positions = []
        for hand_num in range(5):
            game.start_new_hand(process_ai=False)
            dealer_positions.append(game.dealer_index)
            print(f"  Hand {hand_num + 1}: Dealer at position {game.dealer_index} ({game.players[game.dealer_index].name})")

            # Dealer should never be the eliminated player
            assert game.dealer_index != 2, f"Hand {hand_num + 1}: Dealer should skip eliminated player"

        # Button should rotate among active players (0, 1, 3)
        # Should never land on position 2 (eliminated)
        assert 2 not in dealer_positions, "Button should never land on eliminated player"

        # All active players should get the button
        active_players = {0, 1, 3}
        dealer_set = set(dealer_positions)
        assert dealer_set.issubset(active_players), "Button should only land on active players"

    def test_button_rotation_two_eliminated(self):
        """Button rotates correctly with two eliminated players."""
        print("\n[DEAD BUTTON] Testing rotation with 2 active, 2 eliminated...")
        game = PokerGame("P1", ai_count=3)

        # Eliminate P2 and P4 (indices 1 and 3)
        game.players[0].stack = 1000
        game.players[1].stack = 0  # P2 eliminated
        game.players[2].stack = 1000
        game.players[3].stack = 0  # P4 eliminated
        game.total_chips = sum(p.stack for p in game.players)

        # Track dealer positions for 6 hands
        dealer_positions = []
        for hand_num in range(6):
            game.start_new_hand(process_ai=False)
            dealer_positions.append(game.dealer_index)
            print(f"  Hand {hand_num + 1}: Dealer at position {game.dealer_index}")

            # Dealer should only be active players (0 or 2)
            assert game.dealer_index in [0, 2], f"Hand {hand_num + 1}: Dealer should be P1 or P3 only"

        # Button should alternate between the two active players
        assert set(dealer_positions) == {0, 2}, "Button should only land on two active players"

    def test_button_never_skips_active_player(self):
        """Button rotation never skips an active player over multiple hands."""
        print("\n[DEAD BUTTON] Testing button rotation fairness...")
        game = PokerGame("P1", ai_count=3)

        # All players active
        for p in game.players:
            p.stack = 1000
        game.total_chips = sum(p.stack for p in game.players)

        # Track how many times each player gets the button over 12 hands
        button_count = {i: 0 for i in range(4)}

        for hand_num in range(12):
            game.start_new_hand(process_ai=False)
            button_count[game.dealer_index] += 1

        print(f"  Button distribution over 12 hands: {button_count}")

        # Each player should get button exactly 3 times (12 / 4 = 3)
        for player_index, count in button_count.items():
            assert count == 3, f"Player {player_index} got button {count} times (expected 3)"

    def test_heads_up_after_eliminations(self):
        """Button rotation in heads-up after 2 players eliminated."""
        print("\n[DEAD BUTTON] Testing heads-up after eliminations...")
        game = PokerGame("P1", ai_count=3)

        # Eliminate P3 and P4 (indices 2 and 3) - leaves heads-up
        game.players[0].stack = 1000
        game.players[1].stack = 1000
        game.players[2].stack = 0  # Eliminated
        game.players[3].stack = 0  # Eliminated
        game.total_chips = sum(p.stack for p in game.players)

        # In heads-up, button should alternate between the two active players
        dealer_positions = []
        for hand_num in range(6):
            game.start_new_hand(process_ai=False)
            dealer_positions.append(game.dealer_index)
            print(f"  Hand {hand_num + 1}: Dealer at position {game.dealer_index}")

            # Dealer should only be P1 or P2 (indices 0 or 1)
            assert game.dealer_index in [0, 1], "Heads-up dealer should be P1 or P2"

        # Button should alternate
        assert set(dealer_positions) == {0, 1}, "Button should alternate between two players"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
