"""
Test cases for Bug #7 and Bug #8 identified during UAT.

Bug #7: Human fold doesn't trigger showdown when only 1 player remains
Bug #8: Infinite loop when all players are all-in (advance_state called at SHOWDOWN)

These tests are designed to FAIL before the fix and PASS after.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from game.poker_engine import PokerGame, GameState


class TestBug7HumanFoldShowdown:
    """
    Bug #7: When human folds and only 1 active player remains,
    the game should immediately advance to SHOWDOWN.

    Root cause: submit_human_action() with process_ai=False doesn't
    advance to showdown, but QC assertion requires it.
    """

    def test_human_fold_last_player_triggers_showdown(self):
        """
        CRITICAL: When human folds and only 1 player remains,
        game MUST go to showdown (not stay in betting round).
        """
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand(process_ai=False)

        # Find human and AI
        human = next(p for p in game.players if p.is_human)
        ai = next(p for p in game.players if not p.is_human)
        human_index = game.players.index(human)

        # Setup: AI is still active (hasn't folded), betting on flop
        ai.is_active = True  # AI is still in the hand
        ai.has_acted = True

        # Force human to be current player on flop (not pre-flop to avoid BB option)
        game.current_state = GameState.FLOP
        game.current_player_index = human_index
        human.has_acted = False

        # FIXED: Properly set up chip conservation - pot comes from player bets
        # Total chips = human.stack + ai.stack + pot must equal 2000
        pot_amount = 50
        human.stack = 975  # Human contributed 25
        ai.stack = 975     # AI contributed 25
        game.pot = pot_amount  # Total = 975 + 975 + 50 = 2000 ✓

        ai_initial_stack = ai.stack

        # Human folds with process_ai=False (WebSocket mode)
        # This should NOT raise an error, and should go to showdown
        try:
            result = game.submit_human_action("fold", process_ai=False)
        except RuntimeError as e:
            pytest.fail(f"submit_human_action raised error: {e}")

        # Verify: Game should be at showdown (AI wins by default)
        assert game.current_state == GameState.SHOWDOWN, \
            f"Game should be at SHOWDOWN after all but 1 player folds, got {game.current_state.value}"

        # Verify: AI (the remaining player) should have won the pot
        assert ai.stack == ai_initial_stack + pot_amount, \
            f"AI should have won the pot (${pot_amount}), got stack ${ai.stack}"

    def test_human_fold_with_multiple_active_players_continues(self):
        """
        When human folds but other players remain active,
        game should continue (not go to showdown).
        """
        game = PokerGame("Human", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Find human
        human = next(p for p in game.players if p.is_human)
        human_index = game.players.index(human)

        # Setup: 2 AIs still active
        for p in game.players:
            if not p.is_human:
                p.is_active = True
                p.has_acted = True

        # Force human to be current player on flop
        game.current_state = GameState.FLOP
        game.current_player_index = human_index
        human.has_acted = False

        # Human folds
        result = game.submit_human_action("fold", process_ai=False)

        # Game should NOT be at showdown (other players still active)
        # It should continue with AI turns
        assert result == True
        # With 2 active AIs, game continues
        active_count = sum(1 for p in game.players if p.is_active)
        assert active_count == 2, f"Expected 2 active players, got {active_count}"


class TestBug8AllInInfiniteLoop:
    """
    Bug #8: When all players are all-in and _advance_state_for_websocket()
    is called at SHOWDOWN, it causes an infinite loop.

    Root cause: _advance_state_for_websocket() doesn't handle SHOWDOWN state,
    falls through to "reset for new round" code and returns True.
    """

    def test_advance_state_at_showdown_returns_false(self):
        """
        CRITICAL: _advance_state_for_websocket() should return False
        when already at SHOWDOWN (nothing to advance).
        """
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        # Force to showdown state
        game.current_state = GameState.SHOWDOWN
        game.pot = 0  # Already awarded

        # Calling advance should return False (nothing to do)
        result = game._advance_state_for_websocket()

        assert result == False, \
            f"_advance_state_for_websocket() at SHOWDOWN should return False, got {result}"
        assert game.current_state == GameState.SHOWDOWN, \
            "State should remain SHOWDOWN"

    def test_advance_state_at_showdown_doesnt_reset_players(self):
        """
        Calling _advance_state_for_websocket() at SHOWDOWN should NOT
        reset player states (which would enable infinite loop).
        """
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        # Setup: Everyone has acted
        for p in game.players:
            p.has_acted = True
            p.current_bet = 100

        # Force to showdown state
        game.current_state = GameState.SHOWDOWN

        # Store player states
        states_before = [(p.has_acted, p.current_bet) for p in game.players]

        # Call advance (should be a no-op)
        game._advance_state_for_websocket()

        # Player states should NOT be reset
        states_after = [(p.has_acted, p.current_bet) for p in game.players]

        # Note: This will fail with the current bug because the code
        # falls through and calls reset_for_new_round()
        assert states_before == states_after, \
            "Player states should not change when advancing at SHOWDOWN"

    def test_all_in_scenario_reaches_showdown_once(self):
        """
        When both players go all-in, game should advance through
        streets to showdown ONCE (not loop infinitely).
        """
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = next(p for p in game.players if p.is_human)
        ai = next(p for p in game.players if not p.is_human)

        # Setup: Both players all-in on flop
        game.current_state = GameState.FLOP
        game.community_cards = game.deck_manager.deal_cards(3)  # Use proper card format
        game.pot = 2000  # Both stacks in pot

        human.stack = 0
        human.all_in = True
        human.is_active = True
        human.has_acted = True

        ai.stack = 0
        ai.all_in = True
        ai.is_active = True
        ai.has_acted = True

        game.current_bet = 1000
        game.current_player_index = None  # No one can act

        # Count how many times we advance state
        advance_count = 0
        max_advances = 10  # Safety limit

        while game.current_state != GameState.SHOWDOWN and advance_count < max_advances:
            if game._betting_round_complete():
                result = game._advance_state_for_websocket()
                if result:
                    advance_count += 1
                else:
                    break
            else:
                break

        # Should have advanced exactly 3 times: FLOP->TURN->RIVER->SHOWDOWN
        assert advance_count <= 3, \
            f"Should advance at most 3 times (flop->turn->river->showdown), got {advance_count}"
        assert game.current_state == GameState.SHOWDOWN, \
            f"Should reach SHOWDOWN, got {game.current_state.value}"


class TestBettingRoundCompleteWithAllIn:
    """Test _betting_round_complete() behavior with all-in players."""

    def test_betting_complete_when_all_players_all_in(self):
        """Betting round is complete when all active players are all-in."""
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        # Both players all-in
        for p in game.players:
            p.stack = 0
            p.all_in = True
            p.is_active = True
            p.has_acted = True
            p.current_bet = 1000

        game.current_bet = 1000
        game.current_state = GameState.FLOP  # Avoid BB option complexity
        game.last_raiser_index = None

        # Betting round should be complete (no one can act)
        assert game._betting_round_complete() == True, \
            "Betting round should be complete when all players are all-in"

    def test_betting_not_complete_when_one_can_act(self):
        """Betting round is NOT complete if someone can still act."""
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand()

        human = next(p for p in game.players if p.is_human)
        ai = next(p for p in game.players if not p.is_human)

        # FIXED: Proper chip conservation setup
        # AI all-in with 1000 chips (went all-in), human has 500
        # Pot = 500 from AI's partial bet, total = 500 + 1000 + 500 = 2000
        ai.stack = 0
        ai.all_in = True
        ai.is_active = True
        ai.has_acted = True
        ai.current_bet = 1000  # AI bet 1000 to go all-in
        ai.total_invested = 1000

        human.stack = 500  # Human still has 500 chips
        human.all_in = False
        human.is_active = True
        human.has_acted = False  # Human hasn't acted
        human.current_bet = 0
        human.total_invested = 0

        # Pot has 500 chips already (from previous betting/blinds)
        # Total = AI(0) + Human(500) + Pot(500 + AI bet to pot = 1000) = wait...
        # Actually: AI goes all-in for 1000, pot should have that 1000
        # Human has 500 stack + 500 already in pot from blind = 1000 committed by human as well
        # Let's simplify: Total chips = 2000, AI all-in 1000, human has 1000
        human.stack = 1000
        ai.stack = 0
        ai.all_in = True
        ai.current_bet = 1000
        human.current_bet = 0
        game.pot = 1000  # AI's chips are in pot
        # Total = human(1000) + ai(0) + pot(1000) = 2000 ✓

        game.current_bet = 1000
        game.current_state = GameState.FLOP
        game.last_raiser_index = None

        # Betting round should NOT be complete (human can act)
        assert game._betting_round_complete() == False, \
            "Betting round should NOT be complete when human hasn't acted"


class TestWebSocketSimulatorAllIn:
    """
    Simulate the actual WebSocket flow for all-in scenarios.
    This tests the integration between websocket_manager.py and poker_engine.py.
    """

    def test_websocket_flow_all_in_no_infinite_loop(self):
        """
        Simulate WebSocket flow when players go all-in.
        Should reach showdown without infinite loop.

        Note: This test uses a real game with dealt cards to avoid card format issues.
        """
        game = PokerGame("Human", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = next(p for p in game.players if p.is_human)
        ai = next(p for p in game.players if not p.is_human)

        # Get the original total chips for verification
        original_total = sum(p.stack for p in game.players) + game.pot

        # Simulate: Both players go all-in on flop
        # First, deal community cards properly using the game's deck manager
        game.current_state = GameState.FLOP
        game.community_cards = game.deck_manager.deal_cards(3)  # Deal 3 cards for flop

        # Make both players all-in
        human.stack = 0
        human.all_in = True
        human.has_acted = True
        human.current_bet = 1000
        human.total_invested = 1000

        ai.stack = 0
        ai.all_in = True
        ai.has_acted = True
        ai.current_bet = 1000
        ai.total_invested = 1000

        game.pot = 2000  # Both players' 1000 chips each
        game.current_bet = 1000
        # Total = human(0) + ai(0) + pot(2000) = 2000 ✓

        # Simulate the WebSocket loop (process_ai_turns_with_events logic)
        iteration = 0
        max_iterations = 20

        while game.current_state != GameState.SHOWDOWN and iteration < max_iterations:
            iteration += 1

            # Check betting round complete (mirrors websocket_manager.py)
            if game._betting_round_complete():
                advanced = game._advance_state_for_websocket()
                if not advanced:
                    break  # Nothing more to do
            else:
                break  # Waiting for action

        assert iteration < max_iterations, \
            f"Infinite loop detected! Ran {iteration} iterations without reaching showdown"
        assert game.current_state == GameState.SHOWDOWN, \
            f"Should reach SHOWDOWN, got {game.current_state.value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
