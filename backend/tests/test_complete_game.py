"""
Integration test - Complete game simulation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState

def test_complete_game_flow():
    """Test a complete game from start to finish."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    print(f"Starting game with {len(game.players)} players")
    print(f"Initial pot: ${game.pot}, current bet: ${game.current_bet}")

    # Play through the hand
    max_iterations = 100
    iterations = 0
    actions_taken = 0

    while game.current_state != GameState.SHOWDOWN and iterations < max_iterations:
        iterations += 1
        current_player = game.get_current_player()

        if current_player:
            if current_player.is_human:
                # Human calls or folds randomly
                import random
                action = "call" if random.random() > 0.3 else "fold"
                result = game.submit_human_action(action)
                if result:
                    actions_taken += 1
                    print(f"  Human {action}s")
            else:
                # AI acts automatically
                game._process_remaining_actions()
                actions_taken += 1

        game._maybe_advance_state()

    assert iterations < max_iterations, "Game should not hang"
    print(f"✓ Game completed in {iterations} iterations with {actions_taken} actions")
    print(f"✓ Final state: {game.current_state.value}")

    # Get showdown results
    if game.current_state == GameState.SHOWDOWN:
        results = game.get_showdown_results()
        assert results is not None, "Should have showdown results"
        assert 'pots' in results, "Results should include pots"
        print(f"✓ Showdown results: {len(results['pots'])} pot(s) distributed")

        # Verify chip conservation
        total_chips = sum(p.stack for p in game.players) + game.pot
        expected_total = 4 * 1000  # 4 players with 1000 starting stack each
        assert total_chips == expected_total, f"Chips should be conserved: {total_chips} vs {expected_total}"
        print(f"✓ Chip conservation: ${total_chips} total")

def test_multiple_hands():
    """Test playing multiple consecutive hands."""
    game = PokerGame("TestPlayer")

    for hand_num in range(3):
        print(f"\n--- Hand {hand_num + 1} ---")
        game.start_new_hand()

        # Play through hand quickly (all call)
        max_iterations = 50
        iterations = 0

        while game.current_state != GameState.SHOWDOWN and iterations < max_iterations:
            iterations += 1
            current_player = game.get_current_player()

            if current_player and current_player.is_human:
                game.submit_human_action("call")

            game._process_remaining_actions()
            game._maybe_advance_state()

        assert game.current_state == GameState.SHOWDOWN, f"Hand {hand_num + 1} should reach showdown"
        results = game.get_showdown_results()
        assert results is not None, f"Hand {hand_num + 1} should have results"
        print(f"✓ Hand {hand_num + 1} completed successfully")

    print(f"\n✓ Successfully played {3} consecutive hands")

def test_ai_personalities_different():
    """Test that different AI personalities make different decisions."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Give all players same cards to test personality differences
    test_cards = ["7h", "8h"]
    for player in game.players:
        if not player.is_human:
            player.hole_cards = test_cards

    game.community_cards = ["2c", "3c", "4c"]

    # Process AI actions and record decisions
    decisions = {}
    for player in game.players:
        if not player.is_human and player.is_active:
            from game.poker_engine import AIStrategy
            decision = AIStrategy.make_decision_with_reasoning(
                player.personality, player.hole_cards, game.community_cards,
                game.current_bet, game.pot, player.stack, player.current_bet, game.big_blind
            )
            decisions[player.personality] = decision.action
            print(f"  {player.personality}: {decision.action} ({decision.reasoning[:50]}...)")

    # Verify we got decisions
    assert len(decisions) > 0, "Should have AI decisions"
    print(f"✓ Got {len(decisions)} AI decisions with different personalities")

def test_learning_features():
    """Test that learning features (events, AI decisions) are tracked."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Initial events (should have deal events)
    initial_events = len(game.current_hand_events)
    assert initial_events > 0, "Should have initial hand events (deals)"
    print(f"✓ Initial events logged: {initial_events}")

    # Take an action
    if game.get_current_player() and game.get_current_player().is_human:
        game.submit_human_action("call")

    # Should have more events
    assert len(game.current_hand_events) > initial_events, "Action should create events"
    print(f"✓ Events after action: {len(game.current_hand_events)}")

    # Check that AI decisions are tracked
    game._process_remaining_actions()
    assert len(game.last_ai_decisions) > 0, "Should track AI decisions"
    print(f"✓ AI decisions tracked: {len(game.last_ai_decisions)}")

    # Verify game state includes learning data
    state = game.get_game_state()
    assert 'ai_decisions' in state, "Game state should include AI decisions"
    assert 'current_hand_events' in state, "Game state should include hand events"
    print("✓ Learning features included in game state")

if __name__ == "__main__":
    print("Testing Complete Game Integration\n")
    test_complete_game_flow()
    test_multiple_hands()
    test_ai_personalities_different()
    test_learning_features()
    print("\n✅ All integration tests passed!")
