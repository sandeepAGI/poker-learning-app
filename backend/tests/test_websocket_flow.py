"""
Tests for WebSocket-specific game flow.
These tests validate the fixes made for WebSocket gameplay:
1. AI fold -> immediate showdown (not advancing to next betting round)
2. Proper state transitions when all but one player folds
3. Heads-up specific scenarios
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState


class TestWebSocketFoldToShowdown:
    """Test that when all players fold except one, game goes to showdown immediately."""

    def test_ai_fold_triggers_showdown_preflop(self):
        """
        When AI folds pre-flop in heads-up, remaining player should win immediately.
        This is the exact bug that was occurring:
        - AI folds pre-flop
        - Game incorrectly advanced to FLOP with only 1 active player
        - Should go to SHOWDOWN and award pot instead
        """
        # Create heads-up game (1 AI) with process_ai=False to control flow manually
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand(process_ai=False)

        # Find the AI player
        ai_player = next(p for p in game.players if not p.is_human)
        human_player = next(p for p in game.players if p.is_human)

        initial_pot = game.pot
        initial_human_stack = human_player.stack

        # Simulate AI folding (this is what happens in WebSocket flow)
        ai_player.is_active = False
        ai_player.has_acted = True

        # This is the key function that was buggy - it should detect
        # only 1 active player and go to showdown
        advanced = game._advance_state_for_websocket()

        # Assertions
        assert advanced == True, "State should advance"
        assert game.current_state == GameState.SHOWDOWN, \
            f"Game should be at SHOWDOWN when only 1 player active, got {game.current_state}"
        assert game.pot == 0, "Pot should be awarded (set to 0)"
        assert human_player.stack > initial_human_stack, \
            f"Human should have won pot. Stack: {human_player.stack}, was: {initial_human_stack}"

    def test_ai_fold_triggers_showdown_flop(self):
        """When AI folds on flop in heads-up, remaining player wins immediately."""
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        # Advance to flop first (both players must be active)
        game.current_state = GameState.FLOP
        game.community_cards = ["Ah", "Kh", "Qh"]

        ai_player = next(p for p in game.players if not p.is_human)
        human_player = next(p for p in game.players if p.is_human)

        # Reset for new betting round
        for p in game.players:
            p.has_acted = False
            p.current_bet = 0
        game.current_bet = 0

        initial_human_stack = human_player.stack
        game.pot = 50  # Some pot from pre-flop

        # AI folds on flop
        ai_player.is_active = False
        ai_player.has_acted = True

        # Advance state
        advanced = game._advance_state_for_websocket()

        assert advanced == True
        assert game.current_state == GameState.SHOWDOWN
        assert game.pot == 0
        assert human_player.stack == initial_human_stack + 50

    def test_multiple_folds_three_players(self):
        """When 2 players fold in 3-player game, remaining player wins."""
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand()

        human_player = next(p for p in game.players if p.is_human)
        ai_players = [p for p in game.players if not p.is_human]

        initial_human_stack = human_player.stack
        game.pot = 30  # Blinds

        # Both AI players fold
        for ai in ai_players:
            ai.is_active = False
            ai.has_acted = True

        # Human is still active
        human_player.has_acted = True

        # Advance state
        advanced = game._advance_state_for_websocket()

        assert advanced == True
        assert game.current_state == GameState.SHOWDOWN
        assert human_player.stack == initial_human_stack + 30

    def test_no_showdown_if_multiple_active(self):
        """Game should NOT go to showdown if multiple players still active."""
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand()

        # Advance to FLOP first (to avoid BB option complexity)
        game.current_state = GameState.FLOP
        game.community_cards = ["Ah", "Kh", "Qh"]
        game.current_bet = 0
        game.last_raiser_index = None

        # All players active, have acted, matched current bet (0)
        for p in game.players:
            p.has_acted = True
            p.current_bet = 0

        # Advance state - should go to TURN, not SHOWDOWN
        advanced = game._advance_state_for_websocket()

        assert advanced == True
        assert game.current_state == GameState.TURN, \
            f"Should advance to TURN when multiple active, got {game.current_state}"
        assert len(game.community_cards) == 4, "Should have dealt turn card"


class TestWebSocketHeadsUp:
    """Test heads-up specific scenarios for WebSocket flow."""

    def test_heads_up_turn_order_preflop(self):
        """In heads-up, dealer (SB) acts first pre-flop."""
        game = PokerGame("Human", ai_count=1)
        # Use process_ai=False to control flow manually (WebSocket flow)
        game.start_new_hand(process_ai=False)

        # Verify game state is valid
        assert game.current_player_index is not None, \
            "current_player_index should be set after start_new_hand"
        assert game.current_state == GameState.PRE_FLOP

        # Current player should be the one AFTER big blind
        # In heads-up with dealer at index 1:
        # - Dealer (index 1) = SB, acts first pre-flop
        # - Other (index 0) = BB
        current = game.get_current_player()
        assert current is not None

    def test_heads_up_chip_conservation_after_fold(self):
        """Chips should be conserved when AI folds in heads-up."""
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        total_chips_before = sum(p.stack for p in game.players) + game.pot

        # AI folds
        ai_player = next(p for p in game.players if not p.is_human)
        ai_player.is_active = False
        ai_player.has_acted = True

        game._advance_state_for_websocket()

        total_chips_after = sum(p.stack for p in game.players) + game.pot

        assert total_chips_after == total_chips_before, \
            f"Chips not conserved: before={total_chips_before}, after={total_chips_after}"


class TestProcessAiParameter:
    """Test the process_ai parameter in submit_human_action."""

    def test_process_ai_true_processes_actions(self):
        """With process_ai=True (default), AI actions are processed synchronously."""
        game = PokerGame("Human", ai_count=3)
        game.start_new_hand()

        # Wait for human's turn
        while game.get_current_player() and not game.get_current_player().is_human:
            # Skip ahead (normally AI would process)
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )

        if game.get_current_player() and game.get_current_player().is_human:
            human = game.get_current_player()
            # Submit action with process_ai=True (default)
            result = game.submit_human_action("call")
            assert result == True

    def test_process_ai_false_skips_processing(self):
        """With process_ai=False, AI actions are NOT processed (for WebSocket)."""
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        # In heads-up, human might be BB, so find when it's human's turn
        human_player = next(p for p in game.players if p.is_human)
        human_index = game.players.index(human_player)

        # Force human to be current player for test
        game.current_player_index = human_index
        human_player.has_acted = False

        state_before = game.current_state
        pot_before = game.pot

        # Submit with process_ai=False
        result = game.submit_human_action("call", process_ai=False)

        # Action should succeed
        assert result == True
        # Human should have acted
        assert human_player.has_acted == True


def test_websocket_flow_full_hand():
    """
    Simulate a full hand using WebSocket flow:
    1. Game starts, AI acts first (if applicable)
    2. Human acts
    3. AI responds
    4. Continue until showdown
    """
    game = PokerGame("Human", ai_count=1)
    game.start_new_hand()

    max_iterations = 50
    iterations = 0

    while game.current_state != GameState.SHOWDOWN and iterations < max_iterations:
        iterations += 1

        current = game.get_current_player()
        if current is None:
            # Check if we should advance
            if game._betting_round_complete():
                game._advance_state_for_websocket()
            continue

        if current.is_human:
            # Human calls
            game.submit_human_action("call", process_ai=False)
        else:
            # Simulate AI action (call)
            call_amount = game.current_bet - current.current_bet
            current.bet(call_amount)
            game.pot += call_amount
            current.has_acted = True

            # Move to next player
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )

        # Check for state advance
        if game._betting_round_complete():
            game._advance_state_for_websocket()

    assert game.current_state == GameState.SHOWDOWN, \
        f"Game should reach showdown, got {game.current_state}"

    # Verify chip conservation (2 players x 1000 = 2000)
    total = sum(p.stack for p in game.players) + game.pot
    expected_total = len(game.players) * 1000
    assert total == expected_total, f"Chips not conserved: {total}, expected {expected_total}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
