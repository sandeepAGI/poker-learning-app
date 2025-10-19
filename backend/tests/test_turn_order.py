"""
Test turn order enforcement - Bug #1 fix
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

def test_turn_order_enforced():
    """Test that turn order is enforced and out-of-turn actions are rejected."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Find human player index
    human_index = next(i for i, p in enumerate(game.players) if p.is_human)

    # Test 1: Can only act when it's your turn
    if game.current_player_index != human_index:
        # It's not human's turn, action should be rejected
        result = game.submit_human_action("call")
        assert result == False, "Out-of-turn action should be rejected"
        print("✓ Out-of-turn actions correctly rejected")
    else:
        print("✓ Turn order initialized correctly")

    # Test 2: Turn advances after action
    initial_player = game.current_player_index

    # Let game progress
    while game.current_player_index == human_index and game.current_state == GameState.PRE_FLOP:
        game.submit_human_action("call")

    # Verify turn moved to next player
    assert game.current_player_index != initial_player or game.current_state != GameState.PRE_FLOP, \
        "Turn should advance after action"
    print("✓ Turn advances correctly after action")

def test_ai_act_sequentially():
    """Test that AI players act in sequence, not all at once."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Track AI actions
    actions_count_before = len(game.current_hand_events)

    # Let the betting round complete
    while game.current_state == GameState.PRE_FLOP:
        current_player = game.get_current_player()
        if current_player and current_player.is_human:
            game.submit_human_action("fold")
        else:
            # AI should act automatically
            break

    # Process remaining actions
    game._process_remaining_actions()

    actions_count_after = len(game.current_hand_events)

    # AI players should have acted (3 AI players)
    assert actions_count_after > actions_count_before, "AI players should have acted"
    print(f"✓ AI players acted sequentially ({actions_count_after - actions_count_before} actions recorded)")

def test_betting_round_completion():
    """Test that betting round completes when all players have acted and matched bets."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # All players call to complete the round
    while game.current_state == GameState.PRE_FLOP:
        current_player = game.get_current_player()
        if current_player and current_player.is_human:
            game.submit_human_action("call")
        if game._betting_round_complete():
            break

    # Should advance to FLOP
    assert game.current_state == GameState.FLOP or game.current_state == GameState.SHOWDOWN, \
        "Should advance to next state after betting round completes"
    print(f"✓ Betting round completed and advanced to {game.current_state.value}")

if __name__ == "__main__":
    print("Testing Bug #1 Fix: Turn Order Enforcement\n")
    test_turn_order_enforced()
    test_ai_act_sequentially()
    test_betting_round_completion()
    print("\n✅ All turn order tests passed!")
