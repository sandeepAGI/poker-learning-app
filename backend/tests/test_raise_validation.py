"""
Test raise validation and accounting - Bug #3 and #4 fixes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

def test_minimum_raise_enforced():
    """Test that minimum raise (current_bet + big_blind) is enforced."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Wait for human's turn
    while game.get_current_player() and not game.get_current_player().is_human:
        game._process_remaining_actions()
        if game.current_state != GameState.PRE_FLOP:
            break

    if game.get_current_player() and game.get_current_player().is_human:
        current_bet = game.current_bet
        big_blind = game.big_blind

        # Try to raise too small (should fail)
        invalid_raise = current_bet + (big_blind // 2)  # Less than minimum
        human_player = next(p for p in game.players if p.is_human)

        if invalid_raise < human_player.stack:
            result = game.submit_human_action("raise", invalid_raise)
            assert result == False, f"Raise of {invalid_raise} should be rejected (min: {current_bet + big_blind})"
            print(f"✓ Invalid raise ({invalid_raise}) correctly rejected")

        # Try valid raise (should succeed)
        valid_raise = current_bet + big_blind
        result = game.submit_human_action("raise", valid_raise)
        assert result == True, f"Valid raise of {valid_raise} should succeed"
        assert game.current_bet == valid_raise, "Current bet should be updated to raise amount"
        print(f"✓ Valid raise ({valid_raise}) accepted and current_bet updated")

def test_raise_accounting_no_double_count():
    """Test that raise accounting doesn't double-count chips."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Get to human's turn
    while game.get_current_player() and not game.get_current_player().is_human:
        game._process_remaining_actions()
        if game.current_state != GameState.PRE_FLOP:
            break

    if game.get_current_player() and game.get_current_player().is_human:
        human_player = next(p for p in game.players if p.is_human)
        initial_stack = human_player.stack
        initial_pot = game.pot
        current_bet = game.current_bet

        # Calculate expected values
        # Human needs to match current_bet (e.g., 10 for BB)
        call_amount = current_bet - human_player.current_bet
        raise_amount = current_bet + game.big_blind
        raise_increment = raise_amount - human_player.current_bet

        # Make a raise
        result = game.submit_human_action("raise", raise_amount)
        if result:
            # Verify chip accounting
            expected_stack = initial_stack - raise_increment
            expected_pot = initial_pot + raise_increment

            assert human_player.stack == expected_stack, \
                f"Stack should be {expected_stack}, got {human_player.stack}"
            assert game.pot == expected_pot, \
                f"Pot should be {expected_pot}, got {game.pot}"
            print(f"✓ Raise accounting correct: stack {initial_stack}→{human_player.stack}, pot {initial_pot}→{game.pot}")

def test_no_chip_creation_or_destruction():
    """Test that chips are conserved throughout the game."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Calculate total chips at start
    total_chips_start = sum(p.stack for p in game.players) + game.pot
    print(f"Total chips at start: {total_chips_start}")

    # Play through some actions
    for _ in range(10):  # Multiple actions
        current_player = game.get_current_player()
        if current_player and current_player.is_human:
            game.submit_human_action("call")
        if game.current_state == GameState.SHOWDOWN:
            break
        game._process_remaining_actions()
        game._maybe_advance_state()

    # Calculate total chips after
    total_chips_end = sum(p.stack for p in game.players) + game.pot
    print(f"Total chips at end: {total_chips_end}")

    # Chips should be conserved
    assert total_chips_start == total_chips_end, \
        f"Chips not conserved: {total_chips_start} → {total_chips_end}"
    print("✓ Chips conserved throughout game")

def test_all_in_handling():
    """Test that all-in situations are handled correctly."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Find a player and reduce their stack to test all-in
    test_player = game.players[1]  # AI player
    test_player.stack = 15  # Small stack

    # Wait for their turn and they should be able to go all-in
    while game.get_current_player() != test_player and game.current_state == GameState.PRE_FLOP:
        current = game.get_current_player()
        if current and current.is_human:
            game.submit_human_action("call")
        game._process_remaining_actions()

    if game.get_current_player() == test_player:
        initial_stack = test_player.stack
        game._process_single_ai_action(test_player, game.players.index(test_player))

        # If they bet/called, verify all-in flag set correctly
        if test_player.stack == 0:
            assert test_player.all_in == True, "All-in flag should be set when stack is 0"
            print(f"✓ All-in correctly detected for player with {initial_stack} chips")

if __name__ == "__main__":
    print("Testing Bug #3 & #4 Fixes: Raise Validation and Accounting\n")
    test_minimum_raise_enforced()
    test_raise_accounting_no_double_count()
    test_no_chip_creation_or_destruction()
    test_all_in_handling()
    print("\n✅ All raise validation and accounting tests passed!")
