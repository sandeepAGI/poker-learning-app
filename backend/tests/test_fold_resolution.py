"""
Test hand resolution after human folds - Bug #2 fix
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

def test_hand_continues_after_human_fold():
    """Test that hand continues and resolves even when human folds."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    human_player = next(p for p in game.players if p.is_human)
    initial_pot = game.pot

    # Human folds
    while game.get_current_player() and not game.get_current_player().is_human:
        # Wait for human's turn
        game._process_remaining_actions()
        if game.current_state != GameState.PRE_FLOP:
            break

    if game.get_current_player() and game.get_current_player().is_human:
        result = game.submit_human_action("fold")
        assert result == True, "Fold action should succeed"
        assert human_player.is_active == False, "Human should be inactive after fold"
        print("✓ Human successfully folded")

        # Game should continue with AI players
        assert game.current_state != GameState.PRE_FLOP or game._betting_round_complete(), \
            "Game should continue after human folds"
        print("✓ Game continues after human fold")

        # Eventually reach showdown or complete
        max_iterations = 50
        iterations = 0
        while game.current_state not in [GameState.SHOWDOWN] and iterations < max_iterations:
            game._process_remaining_actions()
            game._maybe_advance_state()
            iterations += 1

        # Verify game reached a conclusion
        assert game.current_state == GameState.SHOWDOWN, "Game should reach showdown"
        print(f"✓ Game reached {game.current_state.value}")

        # Pot should be awarded
        results = game.get_showdown_results()
        assert results is not None, "Showdown results should be available"
        assert len(results['pots']) > 0, "At least one pot should exist"
        print(f"✓ Pot awarded: {len(results['pots'])} pot(s) distributed")

def test_multiple_folds():
    """Test that game handles multiple players folding correctly."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Count initial active players
    initial_active = sum(1 for p in game.players if p.is_active)

    # Human folds if it's their turn
    if game.get_current_player() and game.get_current_player().is_human:
        game.submit_human_action("fold")

    # Process remaining, which may result in more folds
    game._process_remaining_actions()

    # Count active players after
    final_active = sum(1 for p in game.players if p.is_active)

    # Should have fewer or equal active players
    assert final_active <= initial_active, "Active player count should decrease or stay same"
    print(f"✓ Active players: {initial_active} → {final_active}")

    # Game should still be able to complete
    max_iterations = 50
    iterations = 0
    while game.current_state not in [GameState.SHOWDOWN] and iterations < max_iterations:
        game._process_remaining_actions()
        game._maybe_advance_state()
        iterations += 1

    assert iterations < max_iterations, "Game should not hang"
    print("✓ Game completed without hanging")

if __name__ == "__main__":
    print("Testing Bug #2 Fix: Hand Resolution After Fold\n")
    test_hand_continues_after_human_fold()
    test_multiple_folds()
    print("\n✅ All fold resolution tests passed!")
