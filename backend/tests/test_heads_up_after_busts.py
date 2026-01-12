"""
Test heads-up blind positioning after players bust out mid-game.

USER REPORTED BUG (Jan 12, 2026):
In a 4-player game where 2 players have Stack: $0, the remaining 2 players
should follow heads-up rules:
- Dealer posts Small Blind (D = SB)
- Other player posts Big Blind (BB)

But user sees incorrect blind badges displayed.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame
from websocket_manager import serialize_game_state


class TestHeadsUpAfterBusts:
    """Test heads-up blind positioning when players bust mid-game."""

    def test_backend_heads_up_blind_positions_after_two_busts(self):
        """
        Test backend calculates correct blind positions when 2 of 4 players bust.

        Expected: Dealer = SB, other player = BB (heads-up rules)
        """
        print("\n[BACKEND TEST] Heads-up blind positions after 2 busts...")
        game = PokerGame("Human", ai_count=3)

        # Simulate 2 players busted
        game.players[1].stack = 0  # Busted
        game.players[2].stack = 0  # Busted
        game.players[0].stack = 2000
        game.players[3].stack = 2000
        game.total_chips = 4000

        # Start new hand
        game.start_new_hand(process_ai=False)

        print(f"\nPlayers with chips: {sum(1 for p in game.players if p.stack > 0)}")
        print(f"Dealer: Position {game.dealer_index} ({game.players[game.dealer_index].name})")
        print(f"SB: Position {game.small_blind_index} ({game.players[game.small_blind_index].name})")
        print(f"BB: Position {game.big_blind_index} ({game.players[game.big_blind_index].name})")

        # Verify exactly 2 players with chips
        active_count = sum(1 for p in game.players if p.stack > 0)
        assert active_count == 2, f"Should have 2 active players, got {active_count}"

        # CRITICAL: In heads-up, dealer MUST equal SB
        assert game.dealer_index == game.small_blind_index, \
            f"BACKEND BUG: In heads-up, dealer ({game.dealer_index}) should equal SB ({game.small_blind_index})"

        # Dealer must NOT equal BB
        assert game.dealer_index != game.big_blind_index, \
            f"BACKEND BUG: Dealer ({game.dealer_index}) and BB ({game.big_blind_index}) must be different"

        print("✅ Backend calculates correct heads-up blind positions")

    def test_websocket_state_includes_correct_blind_positions(self):
        """
        Test that WebSocket serialization includes correct blind positions.
        This is what frontend receives.
        """
        print("\n[BACKEND TEST] WebSocket state has correct blind positions...")
        game = PokerGame("Human", ai_count=3)

        # Bust 2 players
        game.players[1].stack = 0
        game.players[2].stack = 0
        game.total_chips = sum(p.stack for p in game.players)

        # Start hand
        game.start_new_hand(process_ai=False)

        # Serialize (this is what WebSocket sends)
        state = serialize_game_state(game, show_ai_thinking=False)

        print(f"\nSerialized State:")
        print(f"  dealer_position: {state.get('dealer_position')}")
        print(f"  small_blind_position: {state.get('small_blind_position')}")
        print(f"  big_blind_position: {state.get('big_blind_position')}")

        # Verify fields exist
        assert "dealer_position" in state
        assert "small_blind_position" in state
        assert "big_blind_position" in state

        # Verify not None
        assert state["dealer_position"] is not None
        assert state["small_blind_position"] is not None
        assert state["big_blind_position"] is not None

        # In heads-up: dealer == SB
        assert state["dealer_position"] == state["small_blind_position"], \
            f"BACKEND BUG: Dealer ({state['dealer_position']}) should equal SB ({state['small_blind_position']})"

        # Dealer != BB
        assert state["dealer_position"] != state["big_blind_position"], \
            f"BACKEND BUG: Dealer and BB must be different"

        print("✅ WebSocket state has correct blind positions")

    def test_all_four_players_with_chips_normal_blinds(self):
        """
        Control test: With 4 active players, should use normal blind positioning.

        Expected: D at position X, SB at X+1, BB at X+2
        """
        print("\n[BACKEND TEST] Normal blind positions with 4 active players...")
        game = PokerGame("Human", ai_count=3)

        # All players have chips
        game.start_new_hand(process_ai=False)

        print(f"\nPlayers with chips: {sum(1 for p in game.players if p.stack > 0)}")
        print(f"Dealer: {game.dealer_index}")
        print(f"SB: {game.small_blind_index}")
        print(f"BB: {game.big_blind_index}")

        # With 4 active players, use normal rules (not heads-up)
        active_count = sum(1 for p in game.players if p.stack > 0)
        assert active_count == 4

        # SB should be dealer + 1
        expected_sb = (game.dealer_index + 1) % 4
        assert game.small_blind_index == expected_sb, \
            f"With 4 players, SB should be D+1: expected {expected_sb}, got {game.small_blind_index}"

        # BB should be dealer + 2
        expected_bb = (game.dealer_index + 2) % 4
        assert game.big_blind_index == expected_bb, \
            f"With 4 players, BB should be D+2: expected {expected_bb}, got {game.big_blind_index}"

        print("✅ Normal blind positions correct with 4 active players")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
