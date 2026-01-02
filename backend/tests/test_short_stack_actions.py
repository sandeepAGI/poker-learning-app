"""Tests to ensure short-stacked players can still act according to poker rules."""
import pytest

from game.poker_engine import PokerGame


def test_short_stack_can_call_for_less():
    """Human should be able to call all-in even if stack < call amount."""
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)
    game.qc_enabled = False

    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    human = game.players[human_index]

    # Simulate being short-stacked facing a bet larger than remaining stack
    game.current_player_index = human_index
    game.current_bet = human.current_bet + 50
    human.stack = 7

    assert game.submit_human_action("call", process_ai=False) is True, "Short stack should be allowed to call"
    assert human.stack == 0, "Call should consume entire stack"
    assert human.all_in, "Player should be marked all-in"
    assert human.current_bet == human.total_invested, "Investment tracked consistently"


def test_short_stack_can_raise_all_in():
    """Raise action should treat short-stack all-in as legal even if below min raise."""
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)
    game.qc_enabled = False

    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    human = game.players[human_index]

    game.current_player_index = human_index
    human.stack = 12
    human.current_bet = 5  # e.g., already posted small blind
    game.current_bet = 20  # Facing a raise to 20

    assert game.submit_human_action("raise", amount=human.stack + human.current_bet, process_ai=False) is True
    assert human.stack == 0
    assert human.all_in
