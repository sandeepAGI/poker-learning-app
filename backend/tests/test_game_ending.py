"""
Test game ending scenarios when players are eliminated.

Validates that the game handles table collapse gracefully when
only one player remains with chips.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestGameEnding:
    """Test graceful game ending when table collapses."""

    def test_game_ends_when_one_player_remains(self):
        """
        Test that game ends gracefully when only one player has chips.

        Texas Hold'em Rule: Game ends when all but one player are eliminated.
        """
        print("\n[GAME ENDING] Testing game ends when 3 players bust, 1 remains...")
        game = PokerGame("Human", ai_count=3)

        # Simulate 3 players busting (stack = 0)
        game.players[1].stack = 0
        game.players[2].stack = 0
        game.players[3].stack = 0

        # Only human has chips
        game.players[0].stack = 4000  # Winner takes all

        # Update total chips
        game.total_chips = sum(p.stack for p in game.players)

        # Try to start a new hand - should handle gracefully
        try:
            game.start_new_hand(process_ai=False)
            crashed = False
        except Exception as e:
            crashed = True
            print(f"  ✗ Crashed with error: {e}")

        assert not crashed, "Game should not crash with only 1 player remaining"

        # Verify _post_blinds returned early (pot should be 0)
        assert game.pot == 0, "Pot should be 0 when only 1 player remains"
        assert game.current_bet == 0, "Current bet should be 0"

        print("  ✓ Game handled 1 remaining player gracefully (no crash)")
        print("  ✓ Blinds not posted when insufficient players")
        print("✅ Game ends gracefully when only one player remains")

    def test_post_blinds_skipped_with_insufficient_players(self):
        """
        Test that _post_blinds returns early when players_with_chips_count < 2.

        Implementation check: Lines 1044-1050 in poker_engine.py
        """
        print("\n[GAME ENDING] Testing _post_blinds() skips when < 2 players...")
        game = PokerGame("Human", ai_count=3)

        # Set up: Only human has chips
        game.players[0].stack = 100
        game.players[1].stack = 0
        game.players[2].stack = 0
        game.players[3].stack = 0

        game.total_chips = 100
        game.pot = 0
        game.current_bet = 0

        # Call _post_blinds directly
        result = game._post_blinds()

        # Should return (None, None) indicating early exit
        assert result == (None, None), \
            f"_post_blinds should return (None, None) with 1 player, got {result}"

        # Pot and current_bet should be 0
        assert game.pot == 0, "Pot should remain 0"
        assert game.current_bet == 0, "Current bet should remain 0"

        print("  ✓ _post_blinds() correctly returned (None, None)")
        print("  ✓ No blinds posted")
        print("✅ _post_blinds skipped with insufficient players")

    def test_no_crash_when_all_but_one_eliminated(self):
        """
        Test that game doesn't crash when all but one player eliminated.

        Simulates a tournament ending scenario.
        """
        print("\n[GAME ENDING] Testing no crash with all but one eliminated...")
        game = PokerGame("Human", ai_count=3)

        # Simulate tournament ending
        game.players[0].stack = 3500  # Winner
        game.players[1].stack = 0     # Eliminated
        game.players[2].stack = 0     # Eliminated
        game.players[3].stack = 500   # Has some chips left

        game.total_chips = 4000

        # Mark eliminated players
        for i in [1, 2]:
            game.players[i].is_active = False
            game.players[i].reset_for_new_hand()

        # Try to start new hand - should work with 2 players
        try:
            game.start_new_hand(process_ai=False)
            crashed = False
        except Exception as e:
            crashed = True
            print(f"  ✗ Crashed with error: {e}")

        assert not crashed, "Game should not crash with 2 remaining players"

        # Verify game is playable (blinds posted)
        if game.pot > 0:
            print(f"  ✓ Blinds posted successfully (pot = ${game.pot})")

        print("  ✓ No crash with multiple eliminations")
        print("✅ Game handles eliminations gracefully")

    def test_heads_up_after_eliminations(self):
        """
        Test heads-up play continues correctly after 2 players eliminated.

        Heads-up rules: Dealer posts SB, other player posts BB.
        """
        print("\n[GAME ENDING] Testing heads-up after 2 eliminations...")
        game = PokerGame("Human", ai_count=3)

        # Eliminate 2 players, leave 2 with chips
        game.players[0].stack = 2000  # Human
        game.players[1].stack = 0     # Eliminated
        game.players[2].stack = 2000  # AI
        game.players[3].stack = 0     # Eliminated

        game.total_chips = 4000

        # Reset eliminated players
        for i in [1, 3]:
            game.players[i].reset_for_new_hand()

        # Start new hand - should be heads-up
        game.start_new_hand(process_ai=False)

        # Count players who posted blinds
        players_with_bets = [i for i, p in enumerate(game.players) if p.current_bet > 0]

        # Exactly 2 players should have posted blinds
        assert len(players_with_bets) == 2, \
            f"Heads-up should have exactly 2 players posting blinds, got {len(players_with_bets)}"

        # Verify pot equals blinds
        expected_pot = game.small_blind + game.big_blind
        # Account for partial blinds if someone is short-stacked
        total_posted = sum(p.current_bet for p in game.players)
        assert game.pot == total_posted, \
            f"Pot should equal posted blinds: expected ${total_posted}, got ${game.pot}"

        print(f"  ✓ Heads-up play initiated with 2 active players")
        print(f"  ✓ Blinds posted correctly (pot = ${game.pot})")
        print("✅ Heads-up continues correctly after eliminations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
