"""
Test game start scenarios - Bug #9: Game sometimes starts with completed hand.

UAT Issue: With 1 or 2 players, game sometimes starts with hand already complete.
This happens when AI folds immediately in heads-up, ending the hand before human acts.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestGameStartScenarios:
    """Test various game start scenarios."""

    def test_heads_up_game_start_not_at_showdown(self):
        """
        In heads-up, game should NOT start at showdown.
        Even if AI would fold, we should wait for human to see the state first.
        """
        # Run multiple times since AI behavior is random
        showdown_starts = 0
        total_runs = 20

        for _ in range(total_runs):
            game = PokerGame("TestPlayer", ai_count=1)
            # WebSocket flow: process_ai=False means AI doesn't act yet
            game.start_new_hand(process_ai=False)

            if game.current_state == GameState.SHOWDOWN:
                showdown_starts += 1

        # With process_ai=False, game should NEVER start at showdown
        assert showdown_starts == 0, \
            f"Game started at showdown {showdown_starts}/{total_runs} times with process_ai=False"

    def test_three_player_game_start_not_at_showdown(self):
        """With 3 players, game should not start at showdown."""
        showdown_starts = 0
        total_runs = 20

        for _ in range(total_runs):
            game = PokerGame("TestPlayer", ai_count=2)
            game.start_new_hand(process_ai=False)

            if game.current_state == GameState.SHOWDOWN:
                showdown_starts += 1

        assert showdown_starts == 0, \
            f"Game started at showdown {showdown_starts}/{total_runs} times"

    def test_heads_up_with_process_ai_true(self):
        """
        With process_ai=True, AI acts synchronously.
        If AI folds, hand ends - this is the REST API behavior.
        """
        fold_count = 0
        total_runs = 50

        for _ in range(total_runs):
            game = PokerGame("TestPlayer", ai_count=1)
            game.start_new_hand(process_ai=True)

            # In heads-up with synchronous AI, hand might end if AI folds
            if game.current_state == GameState.SHOWDOWN:
                fold_count += 1

        print(f"\nHeads-up with process_ai=True: {fold_count}/{total_runs} ended at showdown")
        # This is expected behavior for REST API - just documenting it

    def test_websocket_flow_human_sees_cards_first(self):
        """
        In WebSocket flow (process_ai=False), human should always see their cards
        before any AI actions. The game state should show:
        - Cards dealt to human
        - Either human's turn OR AI's turn (but not showdown)
        """
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]

        # Human should have cards
        assert len(human.hole_cards) == 2, "Human should have 2 hole cards"

        # Game should NOT be at showdown
        assert game.current_state != GameState.SHOWDOWN, \
            "Game should not start at showdown in WebSocket flow"

        # Get state for frontend
        state = game.get_game_state()
        assert state['game_state'] != 'showdown', \
            "Frontend state should not show showdown at game start"

    def test_game_start_state_for_frontend(self):
        """Verify the state sent to frontend at game start is valid."""
        for ai_count in [1, 2, 3]:
            game = PokerGame("TestPlayer", ai_count=ai_count)
            game.start_new_hand(process_ai=False)

            state = game.get_game_state()

            # Should have players
            assert len(state['players']) == ai_count + 1

            # Human should have visible hole cards
            human_state = next(p for p in state['players'] if p['player_id'] == 'human')
            assert len(human_state['hole_cards']) == 2
            assert human_state['hole_cards'] != ['hidden', 'hidden']

            # Game should be in pre_flop
            assert state['game_state'] == 'pre_flop', \
                f"Expected pre_flop, got {state['game_state']} with {ai_count} AI"

            # Pot should have blinds
            assert state['pot'] > 0, "Pot should have blinds"

            print(f"\nWith {ai_count} AI: state={state['game_state']}, pot={state['pot']}")


class TestHeadsUpSpecificScenarios:
    """Test heads-up specific scenarios that might cause issues."""

    def test_heads_up_blind_posting(self):
        """Verify blinds are posted correctly in heads-up."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        ai = game.players[1]

        # In heads-up, one player posts SB, other posts BB
        total_blinds = human.current_bet + ai.current_bet
        expected_blinds = game.small_blind + game.big_blind

        assert total_blinds == expected_blinds, \
            f"Total blinds {total_blinds} != expected {expected_blinds}"

        assert game.pot == expected_blinds, \
            f"Pot {game.pot} != expected blinds {expected_blinds}"

    def test_heads_up_current_player_is_set(self):
        """In heads-up, there should always be a current player at start."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        assert game.current_player_index is not None, \
            "Current player should be set at game start"

        current = game.players[game.current_player_index]
        assert current.is_active, "Current player should be active"
        assert not current.all_in, "Current player should not be all-in"

    def test_maybe_advance_state_not_called_prematurely(self):
        """
        _maybe_advance_state should not advance to showdown at game start.
        """
        game = PokerGame("TestPlayer", ai_count=1)

        # Manually set up the game state
        game.deck_manager.reset()
        for player in game.players:
            player.reset_for_new_hand()
            if player.is_active:
                player.hole_cards = game.deck_manager.deal_cards(2)

        game.current_state = GameState.PRE_FLOP
        game.pot = 15  # Blinds
        game.current_bet = 10  # BB

        # Set current player
        game.current_player_index = 0

        # Call _maybe_advance_state
        game._maybe_advance_state()

        # Should NOT advance since betting round is not complete
        assert game.current_state == GameState.PRE_FLOP, \
            f"Should still be PRE_FLOP, got {game.current_state}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
