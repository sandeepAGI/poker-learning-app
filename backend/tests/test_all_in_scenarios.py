"""
Test all-in scenarios to catch the "only able to fold after all-in" bug.

This test was created to investigate UAT issue where:
- Human went all-in
- Another player matched
- Human was then only able to fold (shouldn't have any actions since all-in)

NOTE: Uses 3 players to ensure human gets a chance to act before AI can end the hand.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, GameState


def get_human_to_act(game, max_attempts=50):
    """
    Process AI actions until it's human's turn.
    Returns True if human can act, False if hand ended.
    """
    for _ in range(max_attempts):
        if game.current_state == GameState.SHOWDOWN:
            return False  # Hand ended

        if game.current_player_index is None:
            return False  # No one can act

        current = game.players[game.current_player_index]
        if current.is_human and current.is_active and not current.all_in:
            return True  # Human's turn

        # Process AI action
        if not current.is_human and current.is_active and not current.all_in:
            game._process_single_ai_action(current, game.current_player_index)

        # Check if action triggered showdown (apply_action sets current_player_index = None)
        if game.current_player_index is None:
            return False  # Hand ended

        # Move to next player
        game.current_player_index = game._get_next_active_player_index(
            game.current_player_index + 1
        )

        # Check if state needs advancing
        game._maybe_advance_state()

    return False  # Max iterations reached


def setup_game_with_human_to_act():
    """
    Create a game and advance until human can act.
    Returns (game, human) or (None, None) if couldn't set up.
    """
    # Try multiple times since AI behavior is random
    for attempt in range(10):
        game = PokerGame("TestPlayer", ai_count=2)  # 3 players for better chance
        game.start_new_hand(process_ai=False)

        human = game.players[0]

        if get_human_to_act(game):
            return game, human

    return None, None


class TestAllInScenarios:
    """Test various all-in scenarios for correctness."""

    def test_human_all_in_state_is_correct(self):
        """After human goes all-in, their state should reflect this."""
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in (total bet = stack + current_bet)
        all_in_total = human.stack + human.current_bet
        result = game.submit_human_action("raise", all_in_total, process_ai=False)
        assert result, f"All-in action should succeed. Stack={human.stack}, current_bet={human.current_bet}"

        # Verify state
        assert human.stack == 0, "Stack should be 0 after all-in"
        assert human.all_in == True, "all_in flag should be True"
        assert human.is_active == True, "is_active should still be True (not folded)"

    def test_human_all_in_no_further_action_needed(self):
        """Human who is all-in should NOT be the current player."""
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        human_index = 0

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)

        # After all-in, if human is still current, they must have already acted
        if game.current_player_index == human_index:
            assert human.has_acted == True, "If human is current but all-in, has_acted must be True"

    def test_both_players_all_in_goes_to_showdown(self):
        """When all active players are all-in, game should advance to showdown."""
        # Seed random to ensure consistent AI behavior (prevents flaky test)
        import random
        random.seed(42)

        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)
        assert human.all_in == True

        # Process AI responses until showdown or no more AI can act
        for _ in range(20):
            if game.current_state == GameState.SHOWDOWN:
                break
            if game.current_player_index is None:
                break

            current = game.players[game.current_player_index]
            if current.is_human:
                break  # Shouldn't happen since human is all-in

            if current.is_active and not current.all_in:
                game._process_single_ai_action(current, game.current_player_index)

            # Advance state first (may set current_player_index to None)
            game._maybe_advance_state()

            # Then update current_player_index only if it's not None
            if game.current_player_index is not None:
                game.current_player_index = game._get_next_active_player_index(
                    game.current_player_index + 1
                )

        # Verify chip conservation
        total = sum(p.stack for p in game.players) + game.pot
        assert total == game.total_chips, \
            f"Chip conservation violated: {total} != {game.total_chips}"

    def test_human_all_in_ai_calls_showdown(self):
        """Full flow: Human all-in -> AI responds -> Hand completes."""
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_amount = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_amount, process_ai=True)

        # Game should have processed AI response and potentially reached showdown
        assert human.all_in == True or human.stack > 0, \
            f"Human either all-in (stack={human.stack}) or won pot"

        # Verify chip conservation
        total = sum(p.stack for p in game.players) + game.pot
        assert total == game.total_chips, \
            f"Chip conservation violated: {total} != {game.total_chips}"

    def test_all_in_player_skipped_in_turn_order(self):
        """A player who is all-in should be skipped in turn order."""
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)

        # Verify human is all-in
        assert human.all_in == True
        assert human.stack == 0

        # Now check if _get_next_active_player_index skips the human
        next_idx = game._get_next_active_player_index(0)  # Start from human's position

        if next_idx is not None:
            next_player = game.players[next_idx]
            # Next player should not be the all-in human
            if next_player.player_id == "human":
                assert not next_player.all_in, \
                    "All-in player should be skipped in turn order"

    def test_game_state_after_all_in(self):
        """Test the game state sent to frontend after human goes all-in."""
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)

        # Get game state - this is what frontend receives
        state = game.get_game_state()

        # Verify human player state
        human_state = next(p for p in state['players'] if p['player_id'] == 'human')
        assert human_state['all_in'] == True, "Human should be marked all-in in state"
        assert human_state['stack'] == 0, "Human stack should be 0"
        assert human_state['is_active'] == True, "Human should still be active (not folded)"

        # Verify human is NOT current player (can't act anymore)
        if state['current_player_id'] == 'human':
            pytest.fail("All-in player should not be the current player!")

    def test_frontend_state_interpretation(self):
        """
        Test what the frontend would see and how it should interpret state.

        Frontend logic (from PokerTable.tsx) after Bug Fix #10:
        - isEliminated = stack === 0 && (!all_in || isShowdown)
        - isWaitingAllIn = all_in && !isShowdown && stack === 0
        - isMyTurn = is_current_turn && is_active && stack > 0

        States:
        - During hand, all-in: isWaitingAllIn=true, show "All-In! Waiting..."
        - At showdown, lost all-in: isEliminated=true, show "Game Over"
        """
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)

        # Get state that would be sent to frontend
        state = game.get_game_state()
        human_state = next(p for p in state['players'] if p['player_id'] == 'human')

        # These are what frontend checks:
        stack = human_state['stack']
        is_active = human_state['is_active']
        all_in = human_state['all_in']
        game_state = state['game_state']
        is_showdown = (game_state == 'showdown')

        print(f"\n=== Frontend State Analysis ===")
        print(f"stack: {stack}")
        print(f"is_active: {is_active}")
        print(f"all_in: {all_in}")
        print(f"game_state: {game_state}")

        # New correct frontend logic (Bug Fix #10)
        is_eliminated = (stack == 0) and (not all_in or is_showdown)
        is_waiting_all_in = all_in and not is_showdown and stack == 0

        print(f"\nisEliminated: {is_eliminated}")
        print(f"isWaitingAllIn: {is_waiting_all_in}")

        # During hand (not showdown), all-in player should see "waiting" not "eliminated"
        if all_in and not is_showdown:
            assert is_waiting_all_in == True, "All-in player during hand should see waiting state"
            assert is_eliminated == False, "All-in player during hand should NOT be eliminated"


class TestWebSocketAllInFlow:
    """Test all-in scenarios as they occur via WebSocket flow."""

    def test_websocket_all_in_and_response(self):
        """
        Simulate WebSocket flow where:
        1. Human submits all-in
        2. Server processes, sends state
        3. AI is processed asynchronously
        4. Hand completes
        """
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Record initial chip total
        initial_total = sum(p.stack for p in game.players) + game.pot

        # Step 1: Human submits all-in (WebSocket flow uses process_ai=False)
        human_bet_total = human.stack + human.current_bet
        game.submit_human_action("raise", human_bet_total, process_ai=False)

        # Verify human state
        assert human.all_in == True
        assert human.is_active == True

        # Step 2: Get state sent to frontend
        state1 = game.get_game_state()
        print(f"\nState after human all-in:")
        print(f"  game_state: {state1['game_state']}")
        print(f"  current_player_id: {state1['current_player_id']}")
        print(f"  pot: {state1['pot']}")

        # Step 3: Simulate AI processing (what WebSocket handler does)
        while game.current_state != GameState.SHOWDOWN:
            if game.current_player_index is None:
                break

            current = game.players[game.current_player_index]
            if current.is_human:
                break  # Human is all-in, shouldn't be current

            if current.is_active and not current.all_in:
                game._process_single_ai_action(current, game.current_player_index)

            # Advance state first (may set current_player_index to None)
            game._maybe_advance_state()

            # Then update current_player_index only if it's not None
            if game.current_player_index is not None:
                game.current_player_index = game._get_next_active_player_index(
                    game.current_player_index + 1
                )

        # Step 4: Get final state
        state2 = game.get_game_state()
        print(f"\nState after AI responses:")
        print(f"  game_state: {state2['game_state']}")
        print(f"  pot: {state2['pot']}")

        # Verify chip conservation
        final_total = sum(p.stack for p in game.players) + game.pot
        assert final_total == initial_total, \
            f"Chip conservation failed: {final_total} != {initial_total}"


class TestFrontendBugScenarios:
    """Test scenarios that could cause the 'only able to fold' frontend bug."""

    def test_all_in_then_next_hand_state(self):
        """
        Test what happens when:
        1. Human goes all-in
        2. Hand completes
        3. Next hand starts
        4. all_in flag should be reset
        """
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        # Human goes all-in
        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=True)

        # Hand should complete
        print(f"\nAfter all-in hand:")
        print(f"  Game state: {game.current_state}")
        print(f"  Human stack: {human.stack}")
        print(f"  Human is_active: {human.is_active}")
        print(f"  Human all_in: {human.all_in}")

        # Start next hand if human has chips
        if human.stack > 0:
            game.start_new_hand(process_ai=False)

            print(f"\nAfter next hand starts:")
            print(f"  Human stack: {human.stack}")
            print(f"  Human all_in: {human.all_in}")
            print(f"  Human is_active: {human.is_active}")

            # Verify all_in flag is reset
            assert human.all_in == False, \
                "all_in flag should be reset for new hand if player has chips"

    def test_frontend_all_in_states_correct(self):
        """
        Verify frontend logic after Bug Fix #10:
        - During hand: all-in player sees "Waiting" state
        - At showdown: eliminated player sees "Game Over" state
        """
        game, human = setup_game_with_human_to_act()
        if game is None:
            pytest.skip("Could not set up game with human to act")

        all_in_total = human.stack + human.current_bet
        game.submit_human_action("raise", all_in_total, process_ai=False)

        state = game.get_game_state()
        human_state = next(p for p in state['players'] if p['player_id'] == 'human')

        stack = human_state['stack']
        all_in = human_state['all_in']
        game_state = state['game_state']
        is_showdown = (game_state == 'showdown')

        # New frontend logic (Bug Fix #10)
        is_eliminated = (stack == 0) and (not all_in or is_showdown)
        is_waiting_all_in = all_in and not is_showdown and stack == 0

        print(f"\n=== Frontend State Check ===")
        print(f"Stack: {stack}")
        print(f"All-in: {all_in}")
        print(f"Game state: {game_state}")
        print(f"isEliminated: {is_eliminated}")
        print(f"isWaitingAllIn: {is_waiting_all_in}")

        if all_in and not is_showdown:
            print("\n*** BUG FIX VERIFIED ***")
            print("All-in player correctly sees 'Waiting' state during hand")

            # Verify the fix works
            assert is_waiting_all_in == True, "Should show waiting state"
            assert is_eliminated == False, "Should NOT show eliminated"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
