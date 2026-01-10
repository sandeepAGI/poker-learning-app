"""
Test all-in for less doesn't reopen betting.

Texas Hold'em Rule: If a player is all-in for less than the minimum raise,
it doesn't reopen betting for players who have already acted.

Example:
- P1 raises to $100
- P2 calls $100
- P3 all-in for $80 (less than min raise of $110)
→ P1 and P2 CANNOT re-raise (betting round should complete)
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestAllInNoReopen:
    """Test all-in for less doesn't reopen betting."""

    def test_allin_for_less_completes_betting_round(self):
        """All-in for less than min raise completes betting round."""
        print("\n[ALL-IN NO REOPEN] Testing betting round completion...")
        game = PokerGame("P1", ai_count=2)

        # Set up stacks
        game.players[0].stack = 1000  # P1
        game.players[1].stack = 1000  # P2
        game.players[2].stack = 80    # P3 (short stack)
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        # Move to FLOP to avoid BB option logic in pre-flop
        from game.poker_engine import GameState
        game.current_state = GameState.FLOP
        print(f"  State: {game.current_state}")

        # Simulate betting scenario on the flop
        # P1 raises to $100, P2 calls, P3 all-in for $80 (less than min raise)
        game.players[0].current_bet = 100
        game.players[0].has_acted = True
        game.players[1].current_bet = 100
        game.players[1].has_acted = True
        game.players[2].current_bet = 80  # All-in for less
        game.players[2].all_in = True
        game.players[2].has_acted = True

        game.current_bet = 100
        game.last_raiser_index = 0

        # All players have acted, betting round should be complete
        is_complete = game._betting_round_complete()

        print(f"  All players acted (P3 all-in for less)")
        print(f"  Betting round complete: {is_complete}")

        assert is_complete, "Betting round should be complete when all players acted (even with all-in for less)"

    def test_allin_for_less_no_reopen_action(self):
        """Players who already acted cannot re-raise after all-in for less."""
        print("\n[ALL-IN NO REOPEN] Testing no reopen for previous actors...")
        game = PokerGame("P1", ai_count=2)

        game.players[0].stack = 1000
        game.players[1].stack = 1000
        game.players[2].stack = 50  # Short stack
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        # Move to FLOP to avoid BB option logic
        from game.poker_engine import GameState
        game.current_state = GameState.FLOP

        # Simulate betting scenario on the flop
        # P1 raises to $100, P2 calls, P3 all-in for $50 (less than min raise)
        game.current_bet = 100
        game.players[0].current_bet = 100
        game.players[0].has_acted = True
        game.players[0].stack = 900  # Spent $100
        game.last_raiser_index = 0

        # P2 calls $100
        game.players[1].current_bet = 100
        game.players[1].has_acted = True
        game.players[1].stack = 900

        # P3 goes all-in for $50 (less than $110 minimum raise)
        game.players[2].current_bet = 50
        game.players[2].all_in = True
        game.players[2].has_acted = True
        game.players[2].stack = 0

        # Betting round should be complete (no reopening)
        is_complete = game._betting_round_complete()
        print(f"  P1 raised to $100, P2 called, P3 all-in for $50")
        print(f"  Betting round complete: {is_complete}")

        assert is_complete, "All-in for less should not reopen betting"

    def test_allin_for_full_raise_reopens(self):
        """All-in for full raise amount DOES reopen betting."""
        print("\n[ALL-IN NO REOPEN] Testing full raise reopens betting...")
        game = PokerGame("P1", ai_count=2)

        game.players[0].stack = 1000
        game.players[1].stack = 1000
        game.players[2].stack = 120  # Can make full raise
        game.total_chips = sum(p.stack for p in game.players)

        game.start_new_hand(process_ai=False)

        # Move to FLOP to avoid BB option logic
        from game.poker_engine import GameState
        game.current_state = GameState.FLOP

        # P1 raises to $100 on the flop
        game.current_bet = 100
        game.players[0].current_bet = 100
        game.players[0].has_acted = True
        game.last_raiser_index = 0

        # P2 calls
        game.players[1].current_bet = 100
        game.players[1].has_acted = True

        # P3 goes all-in for $120 (full raise to $110+)
        game.players[2].current_bet = 120
        game.players[2].all_in = True
        game.players[2].has_acted = True
        game.last_raiser_index = 2  # This was a raise
        game.current_bet = 120

        # Reset has_acted for P1 and P2 (they can act again after raise)
        game.players[0].has_acted = False
        game.players[1].has_acted = False

        # Betting round should NOT be complete (reopened)
        is_complete = game._betting_round_complete()
        print(f"  P1 raised to $100, P2 called, P3 all-in for $120 (full raise)")
        print(f"  Betting round complete: {is_complete}")

        assert not is_complete, "Full raise all-in should reopen betting"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
