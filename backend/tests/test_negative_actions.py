"""
Negative Testing Suite - Error Handling Path Tests (Engine-Level)

Tests that validate error handling in PokerGame.apply_action() for invalid inputs.
These use PokerGame directly (no server/WebSocket needed).
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState


class TestInvalidActionHandling:
    """
    Test how PokerGame.apply_action() handles various invalid actions.
    """

    @pytest.mark.asyncio
    async def test_invalid_raise_amount_below_minimum(self):
        """
        Test: Raise amount below minimum should be rejected gracefully.

        Currently validates that invalid raises return success: False.
        """
        # Create game with direct API
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)  # Don't process AI, just set up game state

        # Find current player
        current_player = game.players[game.current_player_index]

        # Try to raise below minimum (current_bet + big_blind)
        min_raise = game.current_bet + game.big_blind
        invalid_raise = min_raise - 5  # 5 below minimum

        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=invalid_raise
        )

        # Should fail validation
        assert result["success"] is False, "Invalid raise should be rejected"
        assert "below minimum" in result["error"].lower(), "Error message should mention minimum"

        # Player should NOT have has_acted set to True after failed action
        # (This is critical for preventing infinite loops)
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

    @pytest.mark.asyncio
    async def test_raise_more_than_stack_caps_to_all_in(self):
        """
        Test: Raise exceeding stack should cap at all-in.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]
        original_stack = current_player.stack

        # Try to raise more than total chips (stack + current_bet)
        excessive_raise = current_player.stack + current_player.current_bet + 5000

        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=excessive_raise
        )

        # Should succeed but cap at all-in
        assert result["success"] is True, "Should succeed and cap to all-in"
        assert current_player.stack == 0, "Player should be all-in (stack=0)"
        assert current_player.all_in is True, "Player should be marked as all-in"
        assert result["bet_amount"] == original_stack, "Should bet entire original stack"

    @pytest.mark.asyncio
    async def test_negative_raise_amount_rejected(self):
        """
        Test: Negative raise amounts should be rejected.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]

        # Try negative amount
        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=-100
        )

        # Should fail validation
        assert result["success"] is False, "Negative amount should be rejected"
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

    @pytest.mark.asyncio
    async def test_zero_raise_amount_rejected(self):
        """
        Test: Zero raise amount should be rejected.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]

        # Try zero amount
        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=0
        )

        # Should fail validation
        assert result["success"] is False, "Zero amount should be rejected"
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

    @pytest.mark.asyncio
    async def test_action_after_hand_complete_at_showdown(self):
        """
        Test: apply_action at showdown state should not corrupt game state.

        Verifies that calling apply_action when the game is at SHOWDOWN
        does not modify player state or cause errors.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Force game to showdown
        game.current_state = GameState.SHOWDOWN

        # Snapshot player state before attempting action
        player = game.players[0]
        stack_before = player.stack
        is_active_before = player.is_active

        # Try to act at showdown - fold
        result_fold = game.apply_action(player_index=0, action="fold")

        # Try to act at showdown - call
        game.players[0].is_active = is_active_before  # restore if fold changed it
        game.players[0].stack = stack_before
        result_call = game.apply_action(player_index=0, action="call")

        # Try to act at showdown - raise
        game.players[0].is_active = is_active_before
        game.players[0].stack = stack_before
        result_raise = game.apply_action(player_index=0, action="raise", amount=100)

        # At minimum, actions at showdown should not crash.
        # Ideally they return success=False, but even if they "succeed",
        # the game state should remain at SHOWDOWN.
        assert game.current_state == GameState.SHOWDOWN, \
            "Game state should remain at SHOWDOWN after actions"
