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


def test_short_stack_can_post_partial_blind_next_hand():
    """
    Test that player with stack < small blind can still participate in next hand.

    Texas Hold'em Rule: Player with ANY chips can post a partial blind (all-in).
    """
    print("\n[SHORT STACK] Testing player with $3 can post partial blind...")
    game = PokerGame("Human", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10

    # Give human player $3 (less than small blind)
    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    human = game.players[human_index]
    human.stack = 3

    # Update total chips for conservation check
    game.total_chips = sum(p.stack for p in game.players)

    # Reset for new hand (this is what gets called at start of each hand)
    human.reset_for_new_hand()

    # Player should still be active (can post partial blind)
    assert human.is_active, \
        f"Player with ${human.stack} should be active (can post partial blind)"

    # Start new hand
    game.start_new_hand(process_ai=False)

    # If human is small blind, they should post $3 all-in
    # If human is big blind, they should post $3 all-in
    # Either way, they should be marked all-in
    if human.current_bet > 0:
        assert human.current_bet == 3, f"Should post entire $3 as partial blind"
        assert human.all_in, "Should be marked all-in after posting partial blind"
        assert human.stack == 0, "Stack should be 0 after posting partial blind"

    print(f"  ✓ Player with $3 correctly allowed to post partial blind")
    print("✅ Short stack can post partial blind on next hand")


def test_very_short_stack_all_in_blind():
    """
    Test player with $1 can post partial blind (all-in for any blind position).

    Texas Hold'em Rule: Even $1 chip allows participation with partial blind.
    """
    print("\n[SHORT STACK] Testing player with $1 can post partial blind...")
    game = PokerGame("Human", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10

    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    human = game.players[human_index]
    human.stack = 1

    # Update total chips for conservation check
    game.total_chips = sum(p.stack for p in game.players)

    # Reset for new hand
    human.reset_for_new_hand()

    # Should remain active
    assert human.is_active, "Player with $1 should be active (can post partial blind)"

    # Start new hand
    game.start_new_hand(process_ai=False)

    # Check if human posted a blind
    if human.current_bet > 0:
        assert human.current_bet == 1, "Should post entire $1 as partial blind"
        assert human.all_in, "Should be all-in after posting $1"
        assert human.stack == 0, "Stack should be 0"

    print("  ✓ Player with $1 correctly allowed to participate")
    print("✅ Very short stack ($1) can post partial blind")


def test_short_stack_remains_active_across_hands():
    """
    Test that short-stacked player remains active across multiple hands.

    Scenario: Player wins small pot, has $4, should be able to play next hand.
    """
    print("\n[SHORT STACK] Testing player with $4 remains active across hands...")
    game = PokerGame("Human", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10

    human_index = next(i for i, p in enumerate(game.players) if p.is_human)
    human = game.players[human_index]

    # Simulate player having won a small pot, now has $4
    human.stack = 4

    # Update total chips for conservation check
    game.total_chips = sum(p.stack for p in game.players)

    # Complete current hand and start new one
    human.reset_for_new_hand()

    assert human.is_active, \
        "Player with $4 should remain active for next hand (can post partial blind)"

    # Start another hand
    game.start_new_hand(process_ai=False)

    # Player should be in the hand (either posted blind or waiting to act)
    # They should not be eliminated
    assert human.stack >= 0, "Player should still have non-negative stack"

    # If they posted a blind, it should be partial (all-in)
    if human.current_bet > 0:
        assert human.current_bet <= 4, "Should post at most $4"
        if human.current_bet == 4:
            assert human.all_in, "Should be all-in if posting entire stack"

    print("  ✓ Player with $4 correctly remains active")
    print("✅ Short stack remains active across hands")
