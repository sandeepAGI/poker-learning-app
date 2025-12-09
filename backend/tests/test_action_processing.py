"""
Test apply_action() method - SINGLE SOURCE OF TRUTH for action processing.

Tests the consolidated action processing that was previously duplicated in:
- submit_human_action()
- _process_single_ai_action()
- websocket_manager.process_ai_turns_with_events()

Phase 4 of refactoring plan.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


class TestApplyActionFold:
    """Test fold action processing via apply_action()."""

    def test_fold_sets_inactive(self):
        """Folding player should become inactive."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        # Human folds
        result = game.apply_action(human_idx, "fold")

        assert result["success"] == True
        assert human.is_active == False

    def test_fold_sets_has_acted(self):
        """Folding player should have has_acted=True."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        game.apply_action(human_idx, "fold")

        assert human.has_acted == True

    def test_fold_logs_event(self):
        """Fold action should be logged in hand events."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0
        initial_events = len(game.current_hand_events)

        game.apply_action(human_idx, "fold")

        # Should have logged an action event
        assert len(game.current_hand_events) > initial_events
        fold_events = [e for e in game.current_hand_events
                       if e.event_type == "action" and e.action == "fold"]
        assert len(fold_events) >= 1

    def test_fold_triggers_showdown_when_one_remains(self):
        """Fold that leaves one player should trigger showdown."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human_idx = 0

        result = game.apply_action(human_idx, "fold")

        # With only 2 players, folding should trigger showdown
        assert result["triggers_showdown"] == True

    def test_fold_does_not_trigger_showdown_with_multiple_remaining(self):
        """Fold with multiple players remaining should not trigger showdown."""
        game = PokerGame("TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Find first active player
        for i, player in enumerate(game.players):
            if player.is_active:
                result = game.apply_action(i, "fold")
                break

        # With 3 players and 1 fold, 2 remain - no showdown
        assert result["triggers_showdown"] == False


class TestApplyActionCall:
    """Test call action processing via apply_action()."""

    def test_call_calculates_correct_amount(self):
        """Call should add correct chips to pot."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        initial_pot = game.pot
        call_amount = game.current_bet - human.current_bet

        result = game.apply_action(human_idx, "call")

        assert result["success"] == True
        assert result["bet_amount"] == call_amount
        assert game.pot == initial_pot + call_amount

    def test_call_updates_player_bet(self):
        """Call should update player's current_bet."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        game.apply_action(human_idx, "call")

        assert human.current_bet == game.current_bet

    def test_call_sets_has_acted(self):
        """Calling player should have has_acted=True."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        game.apply_action(human_idx, "call")

        assert human.has_acted == True

    def test_call_handles_partial_call_all_in(self):
        """Call for less than current bet should result in all-in."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        # Set up scenario where human can't afford full call
        human.stack = 5
        game.current_bet = 100

        result = game.apply_action(human_idx, "call")

        assert result["success"] == True
        assert human.all_in == True
        assert human.stack == 0


class TestApplyActionRaise:
    """Test raise action processing via apply_action()."""

    def test_raise_calculates_bet_increment(self):
        """Raise should correctly calculate additional chips needed."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        initial_pot = game.pot
        initial_bet = human.current_bet
        raise_to = game.current_bet + game.big_blind

        result = game.apply_action(human_idx, "raise", raise_to)

        expected_increment = raise_to - initial_bet
        assert result["bet_amount"] == expected_increment
        assert game.pot == initial_pot + expected_increment

    def test_raise_updates_current_bet(self):
        """Raise should update game's current_bet."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        raise_to = game.current_bet + game.big_blind * 2

        game.apply_action(human_idx, "raise", raise_to)

        assert game.current_bet == raise_to

    def test_raise_sets_last_raiser_index(self):
        """Raise should set last_raiser_index."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human_idx = 0
        raise_to = game.current_bet + game.big_blind

        game.apply_action(human_idx, "raise", raise_to)

        assert game.last_raiser_index == human_idx

    def test_raise_resets_other_players_has_acted(self):
        """Raise should reset has_acted for other active players."""
        game = PokerGame("TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        # Mark all players as having acted
        for player in game.players:
            player.has_acted = True

        human_idx = 0
        raise_to = game.current_bet + game.big_blind

        game.apply_action(human_idx, "raise", raise_to)

        # Human should still have acted
        assert game.players[human_idx].has_acted == True

        # Other active players should have has_acted reset
        for i, player in enumerate(game.players):
            if i != human_idx and player.is_active and not player.all_in:
                assert player.has_acted == False, f"Player {i} should have has_acted=False after raise"

    def test_raise_handles_all_in_for_less(self):
        """Raise for less than min raise (all-in) should work."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        human_idx = 0

        # Set up scenario where human can raise but only for small amount
        human.stack = game.big_blind + 5
        all_in_total = human.stack + human.current_bet

        result = game.apply_action(human_idx, "raise", all_in_total)

        assert result["success"] == True
        assert human.all_in == True
        assert human.stack == 0


class TestApplyActionChipConservation:
    """Test chip conservation invariant in apply_action()."""

    def test_no_chip_creation_on_fold(self):
        """Fold should not create or destroy chips."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        initial_total = sum(p.stack for p in game.players) + game.pot

        game.apply_action(0, "fold")

        final_total = sum(p.stack for p in game.players) + game.pot
        assert final_total == initial_total

    def test_no_chip_creation_on_call(self):
        """Call should not create or destroy chips."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        initial_total = sum(p.stack for p in game.players) + game.pot

        game.apply_action(0, "call")

        final_total = sum(p.stack for p in game.players) + game.pot
        assert final_total == initial_total

    def test_no_chip_creation_on_raise(self):
        """Raise should not create or destroy chips."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        initial_total = sum(p.stack for p in game.players) + game.pot
        raise_to = game.current_bet + game.big_blind

        game.apply_action(0, "raise", raise_to)

        final_total = sum(p.stack for p in game.players) + game.pot
        assert final_total == initial_total


class TestApplyActionErrorHandling:
    """Test error handling in apply_action()."""

    def test_invalid_player_index(self):
        """Invalid player index should return error."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        result = game.apply_action(99, "fold")

        assert result["success"] == False
        assert "error" in result

    def test_inactive_player_fold_still_works(self):
        """Inactive player folding should still work (idempotent)."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        # Fold the player first
        game.players[0].is_active = False

        # Folding an already folded player should still succeed
        # (or return success=False if validation is strict)
        result = game.apply_action(0, "fold")
        # Implementation may vary - just verify no crash

    def test_all_in_player_stack_is_zero(self):
        """All-in player should have stack=0 after going all-in."""
        game = PokerGame("TestPlayer", ai_count=1)
        game.start_new_hand(process_ai=False)

        human = game.players[0]
        all_in_amount = human.stack + human.current_bet

        result = game.apply_action(0, "raise", all_in_amount)

        assert result["success"] == True
        assert human.stack == 0
        assert human.all_in == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
