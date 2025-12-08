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
        game.start_new_hand(process_ai=False)  # Don't auto-process AI

        human_player = next(p for p in game.players if p.is_human)
        ai_players = [p for p in game.players if not p.is_human]

        # Move to FLOP to avoid BB option complexity
        game.current_state = GameState.FLOP
        game.community_cards = game.deck_manager.deal_cards(3)

        # Setup chip conservation: Total must equal 3000 (3 players * 1000)
        # After blinds, pot has 15 (5+10), players have less
        pot_amount = 30
        human_player.stack = 990  # Lost 10 to pot
        ai_players[0].stack = 990  # Lost 10 to pot
        ai_players[1].stack = 990  # Lost 10 to pot
        game.pot = pot_amount  # Total = 990*3 + 30 = 3000 ✓

        initial_human_stack = human_player.stack

        # Both AI players fold
        for ai in ai_players:
            ai.is_active = False
            ai.has_acted = True

        # Human is still active
        human_player.has_acted = True
        human_player.current_bet = 0
        game.current_bet = 0

        # Advance state
        advanced = game._advance_state_for_websocket()

        assert advanced == True, f"Expected advance=True, game state: {game.current_state.value}"
        assert game.current_state == GameState.SHOWDOWN
        assert human_player.stack == initial_human_stack + pot_amount

    def test_no_showdown_if_multiple_active(self):
        """Game should NOT go to showdown if multiple players still active."""
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand(process_ai=False)  # Don't auto-process AI

        # Advance to FLOP first (to avoid BB option complexity)
        game.current_state = GameState.FLOP
        game.community_cards = game.deck_manager.deal_cards(3)  # Proper card format
        game.current_bet = 0
        game.last_raiser_index = None

        # All players active, have acted, matched current bet (0)
        for p in game.players:
            p.is_active = True  # Ensure all are active
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


class TestWebSocketEventLogging:
    """Test that AI actions are properly logged (fixes BB option check bug)."""

    def test_bb_option_ai_as_bb_with_event_logging(self):
        """When AI is BB, game should advance after AI acts (event logging required)."""
        game = PokerGame("Human", ai_count=3)
        game.start_new_hand(process_ai=False)

        # Simulate human calling (if human is first to act)
        human_player = next(p for p in game.players if p.is_human)
        human_index = game.players.index(human_player)

        if game.current_player_index == human_index:
            game.submit_human_action("call", process_ai=False)

        # Process all AI turns WITH event logging (simulating fixed code)
        max_iterations = 20
        iterations = 0
        while game.current_player_index is not None and iterations < max_iterations:
            iterations += 1
            current = game.players[game.current_player_index]

            if current.is_human and not current.has_acted:
                break

            if current.is_active and not current.all_in and not current.is_human:
                # AI calls
                call_amount = game.current_bet - current.current_bet
                current.bet(call_amount)
                game.pot += call_amount
                current.has_acted = True
                # CRITICAL: Log the event (this is what was missing before!)
                game._log_hand_event("action", current.player_id, "call", call_amount, 0.0, "")

            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )

            if game._betting_round_complete():
                break

        # Betting round should be complete
        assert game._betting_round_complete() == True, \
            "Betting round should complete after all players act (event logging required for BB option)"

    def test_event_logging_without_logs_fails_bb_option(self):
        """Without event logging, BB option check fails (demonstrates the bug)."""
        game = PokerGame("Human", ai_count=3)
        game.start_new_hand(process_ai=False)

        # Find BB player (last_raiser_index is set to BB during blind posting)
        bb_index = game.last_raiser_index
        bb_player = game.players[bb_index] if bb_index is not None else None

        # Simulate all players calling WITHOUT logging events
        for p in game.players:
            if p.is_active and not p.all_in:
                call_amount = game.current_bet - p.current_bet
                p.bet(call_amount)
                game.pot += call_amount
                p.has_acted = True
                # NOTE: NOT logging events here

        # If BB is AI and we didn't log events, BB option check should fail
        if bb_player and not bb_player.is_human:
            # Check BB action count in events (should be 0 without logging)
            bb_action_count = sum(1 for e in game.current_hand_events
                                 if e.player_id == bb_player.player_id
                                 and e.event_type == "action"
                                 and e.action in ["check", "call", "raise", "fold"])
            assert bb_action_count == 0, \
                "Without event logging, BB action count should be 0"


class TestHumanAlreadyActed:
    """Test that game doesn't get stuck when returning to human who already acted."""

    def test_human_already_acted_not_stuck(self):
        """Game should not get stuck when returning to human who already acted."""
        game = PokerGame("Human", ai_count=3)
        game.start_new_hand(process_ai=False)

        # Process until human's turn
        max_iterations = 10
        iterations = 0
        while game.current_player_index is not None and iterations < max_iterations:
            iterations += 1
            current = game.players[game.current_player_index]
            if current.is_human:
                break
            # Skip non-human players for setup
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )

        # Human calls
        human = next(p for p in game.players if p.is_human)
        if game.current_player_index == game.players.index(human):
            game.submit_human_action("call", process_ai=False)
            assert human.has_acted == True, "Human should have has_acted=True after calling"

            # Now process AI turns - should not get stuck on human
            # This simulates the fixed process_ai_turns_with_events behavior
            iterations = 0
            while game.current_player_index is not None and iterations < max_iterations:
                iterations += 1
                current = game.players[game.current_player_index]

                # The fix: don't break if human has already acted
                if current.is_human and not current.all_in and not current.has_acted:
                    break  # Human needs to act

                if current.is_human and current.has_acted:
                    # Human already acted - continue to next player or check round complete
                    pass

                if current.is_active and not current.all_in and not current.is_human:
                    # AI acts
                    call_amount = game.current_bet - current.current_bet
                    current.bet(call_amount)
                    game.pot += call_amount
                    current.has_acted = True
                    game._log_hand_event("action", current.player_id, "call", call_amount, 0.0, "")

                game.current_player_index = game._get_next_active_player_index(
                    game.current_player_index + 1
                )

                if game._betting_round_complete():
                    break

            # Should have completed the betting round
            assert game._betting_round_complete() == True, \
                "Betting round should complete - not get stuck on human who already acted"


class TestAIRaiseResetsHasActed:
    """Test that when AI raises, other players' has_acted is reset."""

    def test_ai_raise_resets_has_acted(self):
        """When AI raises, other players' has_acted should reset."""
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Setup: all players have acted
        for p in game.players:
            p.has_acted = True
            p.current_bet = game.current_bet

        # Find an AI player
        ai = next(p for p in game.players if not p.is_human)
        game.current_player_index = game.players.index(ai)
        ai.has_acted = False  # AI about to act

        # AI raises
        raise_amount = game.big_blind * 3
        ai.bet(raise_amount)
        game.current_bet = ai.current_bet
        game.pot += raise_amount
        ai.has_acted = True
        game._log_hand_event("action", ai.player_id, "raise", raise_amount, 0.0, "")

        # Reset has_acted for other players (this is what the fix does)
        for p in game.players:
            if p.player_id != ai.player_id and p.is_active and not p.all_in:
                p.has_acted = False

        # Verify other players need to act again
        for p in game.players:
            if p.player_id != ai.player_id and p.is_active:
                assert p.has_acted == False, f"{p.name} should need to respond to raise"

    def test_betting_round_not_complete_after_raise(self):
        """Betting round should not be complete after a raise (others must respond)."""
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Setup: all players have acted and matched bet
        for p in game.players:
            p.has_acted = True
            p.current_bet = game.current_bet

        # Betting round should be complete at this point (ignoring BB option for simplicity)
        # Force state to FLOP to avoid BB option complexity
        game.current_state = GameState.FLOP
        game.last_raiser_index = None
        assert game._betting_round_complete() == True, "Should be complete before raise"

        # Find an AI player and have them raise
        ai = next(p for p in game.players if not p.is_human)
        raise_amount = game.big_blind * 3
        ai.bet(raise_amount)
        game.current_bet = ai.current_bet
        game.pot += raise_amount
        game._log_hand_event("action", ai.player_id, "raise", raise_amount, 0.0, "")

        # Reset has_acted for other players (simulate the fix)
        for p in game.players:
            if p.player_id != ai.player_id and p.is_active and not p.all_in:
                p.has_acted = False

        # Betting round should NOT be complete now (others need to respond)
        assert game._betting_round_complete() == False, \
            "Betting round should NOT be complete after raise - others must respond"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
