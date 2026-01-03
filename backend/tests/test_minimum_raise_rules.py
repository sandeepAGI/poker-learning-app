"""
Test minimum raise calculation follows Texas Hold'em rules.

Texas Hold'em Rule: Each raise must be at least as large as the previous raise.
Example: BB=10, UTG raises to 60 (raise of 50), next raiser must raise by ≥50, so min total bet = 110

Current Bug: Backend uses min_raise = current_bet + big_blind (incorrect)
Should be: min_raise = current_bet + last_raise_amount
"""

import pytest
from game.poker_engine import PokerGame


def test_minimum_raise_follows_previous_raise_size():
    """Test that minimum raise equals the size of the previous raise, not the big blind."""

    # Setup: 4-player game, BB=10
    game = PokerGame(human_player_name="TestPlayer", ai_count=3)
    # Set blinds to 5/10 for testing
    game.small_blind = 5
    game.big_blind = 10
    game.start_new_hand()

    # Verify initial state: blinds posted
    assert game.small_blind == 5
    assert game.big_blind == 10
    assert game.current_bet == 10  # BB is current bet

    # Find positions
    bb_index = game.big_blind_index
    utg_index = (bb_index + 1) % 4
    next_player_index = (bb_index + 2) % 4

    # UTG raises to 60 (a raise of 50 from the BB of 10)
    utg_player = game.players[utg_index]
    result = game.apply_action(utg_index, "raise", 60)
    assert result["success"], f"UTG raise to 60 should succeed: {result.get('error')}"
    assert game.current_bet == 60

    # CRITICAL TEST: Next player tries to raise to 70 (only a 10 raise)
    # This should FAIL because the previous raise was 50, so min raise should be 110
    next_player = game.players[next_player_index]
    result = game.apply_action(next_player_index, "raise", 70)

    # This test will FAIL with current implementation (it allows 70)
    assert not result["success"], (
        f"Raise to 70 should FAIL (min raise should be 110, not 70). "
        f"Previous raise was 50 (from 10 to 60), so next raise must be at least 50 (to 110). "
        f"Result: {result}"
    )
    assert "below minimum" in result.get("error", "").lower()

    # Next player raises to 110 (a raise of 50, matching previous raise)
    # This should SUCCEED
    result = game.apply_action(next_player_index, "raise", 110)
    assert result["success"], f"Raise to 110 should succeed: {result.get('error')}"
    assert game.current_bet == 110


def test_minimum_raise_resets_each_betting_round():
    """Test that minimum raise amount is tracked and can reset."""

    # Setup: 4-player game
    game = PokerGame(human_player_name="TestPlayer", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10
    game.start_new_hand()

    # Pre-flop: P1 raises to 60 (raise of 50 from BB of 10)
    bb_index = game.big_blind_index
    p1_index = (bb_index + 1) % 4
    result = game.apply_action(p1_index, "raise", 60)
    assert result["success"]
    assert game.last_raise_amount == 50  # Raise of 50 (from 10 to 60)

    # Verify that after the raise, the minimum for next raiser is based on last_raise_amount
    # current_bet is 60, last_raise_amount is 50, so min next raise = 60 + 50 = 110
    p2_index = (bb_index + 2) % 4

    # Try to raise to 80 (only 20 raise) - should FAIL
    result = game.apply_action(p2_index, "raise", 80)
    assert not result["success"], "Raise of only 20 should fail when previous raise was 50"

    # Raise to 110 (raise of 50) - should SUCCEED
    result = game.apply_action(p2_index, "raise", 110)
    assert result["success"], f"Raise of 50 should succeed: {result.get('error')}"
    assert game.last_raise_amount == 50  # Still 50 (from 60 to 110)


def test_minimum_raise_with_multiple_raises():
    """Test minimum raise tracking through multiple raises in same round."""

    # Setup: 4-player game, BB=10
    game = PokerGame(human_player_name="TestPlayer", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10
    game.start_new_hand()

    bb_index = game.big_blind_index
    p1_index = (bb_index + 1) % 4
    p2_index = (bb_index + 2) % 4
    p3_index = (bb_index + 3) % 4

    # P1 raises to 30 (raise of 20)
    result = game.apply_action(p1_index, "raise", 30)
    assert result["success"]

    # P2 raises to 80 (raise of 50)
    result = game.apply_action(p2_index, "raise", 80)
    assert result["success"]

    # P3 tries to raise to 100 (only raise of 20) - should FAIL
    # Previous raise was 50, so min raise should be 130
    result = game.apply_action(p3_index, "raise", 100)
    assert not result["success"], "Raise of 20 should fail when previous raise was 50"

    # P3 raises to 130 (raise of 50) - should SUCCEED
    result = game.apply_action(p3_index, "raise", 130)
    assert result["success"], f"Raise to 130 should succeed: {result.get('error')}"


def test_first_raise_in_round_uses_big_blind_as_minimum():
    """Test that the first raise in a betting round can use big_blind as minimum increment."""

    # Setup
    game = PokerGame(human_player_name="TestPlayer", ai_count=3)
    game.small_blind = 5
    game.big_blind = 10
    game.start_new_hand()

    bb_index = game.big_blind_index
    utg_index = (bb_index + 1) % 4

    # First raise should allow min raise = BB + big_blind = 10 + 10 = 20
    result = game.apply_action(utg_index, "raise", 20)
    assert result["success"], "First raise to 20 should succeed (BB + big_blind)"

    # But trying to raise to 15 should fail
    game2 = PokerGame(human_player_name="TestPlayer2", ai_count=3)
    game2.small_blind = 5
    game2.big_blind = 10
    game2.start_new_hand()
    utg_index2 = (game2.big_blind_index + 1) % 4
    result2 = game2.apply_action(utg_index2, "raise", 15)
    assert not result2["success"], "Raise to 15 should fail (below min raise of 20)"


if __name__ == "__main__":
    # Run tests
    print("Running minimum raise tests...")
    print("\nTest 1: Minimum raise follows previous raise size")
    try:
        test_minimum_raise_follows_previous_raise_size()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")

    print("\nTest 2: Minimum raise resets each betting round")
    try:
        test_minimum_raise_resets_each_betting_round()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")

    print("\nTest 3: Multiple raises tracking")
    try:
        test_minimum_raise_with_multiple_raises()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")

    print("\nTest 4: First raise uses big blind")
    try:
        test_first_raise_in_round_uses_big_blind_as_minimum()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
