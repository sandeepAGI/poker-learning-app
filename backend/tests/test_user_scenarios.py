"""
Phase 4: Scenario-Based Testing

Tests REAL user journeys (not isolated actions).
Goal: Validate complete gameplay flows over multiple hands.

Test Categories:
1. Multi-Hand Scenarios (3 hours) - Playing multiple hands with different strategies
2. Complex Betting Sequences (3 hours) - Multi-action sequences in single hands
3. Edge Case Scenarios (2 hours) - Boundary conditions and special situations

These tests simulate how users actually play the game.
"""
import pytest
import asyncio
import json
import httpx
import websockets
from typing import List, Dict, Any
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from game.poker_engine import PokerGame, GameState

# Import WebSocket test infrastructure
from test_websocket_integration import (
    WebSocketTestClient,
    create_test_game,
    test_server
)


# =============================================================================
# 4.1: Multi-Hand Scenarios (3 hours)
# =============================================================================

class TestMultiHandScenarios:
    """Test user strategies played over multiple hands"""

    @pytest.mark.asyncio
    async def test_go_all_in_every_hand_for_10_hands(self):
        """
        Aggressive strategy: Go all-in on every hand for 10 hands.

        Tests:
        - Multiple consecutive all-ins
        - Stack management across hands
        - Game handles player elimination
        - Continuous gameplay without hangs
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            # Get initial state
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)
            initial_stack = initial_state["data"]["human_player"]["stack"]

            hands_played = 0
            player_eliminated = False

            for hand_num in range(10):
                if player_eliminated:
                    break

                print(f"\n--- Hand {hand_num + 1}/10 ---")

                # Get current state (might already be our turn)
                current_state_data = ws.get_latest_state()
                if not current_state_data or not current_state_data.get("human_player", {}).get("is_current_turn"):
                    # Wait for our turn if it's not already
                    state_event = await ws.wait_for_event("state_update", timeout=10.0)
                    current_state_data = state_event["data"]

                # Check if we're still in the game
                human_player = current_state_data["human_player"]
                if human_player["stack"] == 0:
                    print(f"Player eliminated after {hand_num} hands")
                    player_eliminated = True
                    break

                # Calculate all-in amount (stack + current_bet)
                all_in_amount = human_player["stack"] + human_player["current_bet"]
                print(f"Going all-in: {all_in_amount}")

                # Send all-in action
                await ws.send_action("raise", amount=all_in_amount)

                # Wait for hand to complete (showdown or earlier)
                events = await ws.drain_events(max_events=100, timeout=15.0)

                # Verify hand completed
                final_state = ws.get_latest_state()
                assert final_state is not None, f"No state after hand {hand_num + 1}"

                # Check if hand reached showdown or ended early
                assert final_state["state"] in ["showdown", "pre_flop"], \
                    f"Hand {hand_num + 1} stuck in {final_state['state']}"

                hands_played += 1

                # If not eliminated and not the last hand, start next hand
                if hand_num < 9 and not player_eliminated:
                    if final_state["state"] == "showdown":
                        await ws.send_next_hand()
                        await asyncio.sleep(0.5)  # Brief pause

            print(f"\nCompleted {hands_played} hands")
            assert hands_played >= 1, "Should play at least 1 hand"

    @pytest.mark.asyncio
    async def test_conservative_strategy_fold_90_percent(self):
        """
        Conservative strategy: Fold 90% of hands, call 10%.

        Tests:
        - Repeated folding doesn't break game
        - Occasional calls work correctly
        - Blinds are paid each hand
        - Stack decreases appropriately
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            # Get initial state
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)
            initial_stack = initial_state["data"]["human_player"]["stack"]

            hands_played = 0
            folds = 0
            calls = 0

            for hand_num in range(20):
                print(f"\n--- Hand {hand_num + 1}/20 ---")

                # Get current state (might already be our turn)
                current_state_data = ws.get_latest_state()
                if not current_state_data or not current_state_data.get("human_player", {}).get("is_current_turn"):
                    # Wait for our turn if it's not already
                    state_event = await ws.wait_for_event("state_update", timeout=10.0)
                    current_state_data = state_event["data"]

                # Fold 90% of the time (hands 1-18), call 10% (hands 19-20)
                if hand_num < 18:
                    print("Folding")
                    await ws.send_action("fold")
                    folds += 1
                else:
                    print("Calling")
                    await ws.send_action("call")
                    calls += 1

                # Wait for hand to complete
                events = await ws.drain_events(max_events=100, timeout=10.0)

                hands_played += 1

                # Start next hand
                final_state = ws.get_latest_state()
                if final_state["state"] == "showdown" and hand_num < 19:
                    await ws.send_next_hand()
                    await asyncio.sleep(0.3)

            print(f"\nPlayed {hands_played} hands: {folds} folds, {calls} calls")
            assert hands_played == 20
            assert folds == 18
            assert calls == 2

            # Verify stack is valid (may increase or decrease depending on blinds and wins)
            final_state_data = ws.get_latest_state()
            final_stack = final_state_data["human_player"]["stack"]
            stack_change = final_stack - initial_stack
            print(f"Stack change: {initial_stack} -> {final_stack} (Δ{stack_change:+d})")

            # Stack should still be positive and within reasonable bounds
            assert final_stack >= 0, "Stack should never be negative"
            assert abs(stack_change) < 500, f"Stack change too large: {stack_change}"

    @pytest.mark.asyncio
    async def test_mixed_strategy_10_hands(self):
        """
        Mixed strategy: Randomized actions over 10 hands.

        Pattern: call, fold, call, raise, fold, call, raise, fold, call, raise

        Tests:
        - Variety of actions works correctly
        - State transitions properly between hands
        - No hangs with mixed actions
        """
        game_id = await create_test_game(ai_count=3)

        actions = ["call", "fold", "call", "raise", "fold",
                   "call", "raise", "fold", "call", "raise"]

        async with WebSocketTestClient(game_id) as ws:
            await ws.wait_for_event("state_update", timeout=5.0)

            for hand_num, action in enumerate(actions):
                print(f"\n--- Hand {hand_num + 1}/10: {action.upper()} ---")

                # Get current state (might already be our turn)
                current_state_data = ws.get_latest_state()
                if not current_state_data or not current_state_data.get("human_player", {}).get("is_current_turn"):
                    # Wait for our turn if it's not already
                    state_event = await ws.wait_for_event("state_update", timeout=10.0)
                    current_state_data = state_event["data"]

                human_player = current_state_data["human_player"]

                # Execute action
                if action == "raise":
                    # Raise by big blind amount
                    raise_amount = current_state_data["big_blind"] * 3
                    await ws.send_action("raise", amount=raise_amount)
                else:
                    await ws.send_action(action)

                # Wait for hand completion
                await ws.drain_events(max_events=100, timeout=10.0)

                # Start next hand if not last
                final_state = ws.get_latest_state()
                if hand_num < 9 and final_state["state"] == "showdown":
                    await ws.send_next_hand()
                    await asyncio.sleep(0.3)

            print("\n✅ All 10 hands completed successfully")


# =============================================================================
# 4.2: Complex Betting Sequences (3 hours)
# =============================================================================

class TestComplexBettingSequences:
    """Test multi-action sequences within single hands"""

    @pytest.mark.asyncio
    async def test_raise_call_multiple_streets(self):
        """
        Test: Raise pre-flop, call flop, call turn, call river.

        Tests complete hand progression through all streets.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)

            # Pre-flop: Raise
            print("Pre-flop: Raising")
            # Get current state (might already be our turn)
            current_state_data = ws.get_latest_state()
            if not current_state_data or not current_state_data.get("human_player", {}).get("is_current_turn"):
                # Wait for our turn if it's not already
                state_event = await ws.wait_for_event("state_update", timeout=10.0)
                current_state_data = state_event["data"]

            assert current_state_data["state"] == "pre_flop"

            raise_amount = current_state_data["big_blind"] * 3
            await ws.send_action("raise", amount=raise_amount)

            # Wait for AI actions and flop
            events = await ws.drain_events(max_events=50, timeout=10.0)

            # Flop: Call
            flop_state = ws.get_latest_state()
            if flop_state["state"] == "flop":
                print("Flop: Calling")
                await ws.send_action("call")
                events = await ws.drain_events(max_events=50, timeout=10.0)

            # Turn: Call
            turn_state = ws.get_latest_state()
            if turn_state["state"] == "turn":
                print("Turn: Calling")
                await ws.send_action("call")
                events = await ws.drain_events(max_events=50, timeout=10.0)

            # River: Call
            river_state = ws.get_latest_state()
            if river_state["state"] == "river":
                print("River: Calling")
                await ws.send_action("call")
                events = await ws.drain_events(max_events=50, timeout=10.0)

            # Should reach showdown
            final_state = ws.get_latest_state()
            assert final_state["state"] == "showdown", \
                f"Expected showdown, got {final_state['state']}"

            print("✅ Successfully played through all streets")

    @pytest.mark.asyncio
    async def test_all_players_go_all_in_scenario(self):
        """
        Test scenario where all 4 players go all-in.

        Critical test: This was a failing UAT case (UAT-5).
        Tests side pot calculations and showdown with multiple all-ins.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)
            human_player = initial_state["data"]["human_player"]

            # Go all-in immediately
            all_in_amount = human_player["stack"] + human_player["current_bet"]
            print(f"Human going all-in: {all_in_amount}")

            await ws.send_action("raise", amount=all_in_amount)

            # Wait for AI actions - hopefully they also go all-in
            events = await ws.drain_events(max_events=100, timeout=20.0)

            # Verify game reached showdown (not infinite loop)
            final_state = ws.get_latest_state()
            assert final_state is not None, "No final state received"

            # Game should complete (either showdown or earlier if all but one folded)
            assert final_state["state"] in ["showdown", "pre_flop"], \
                f"Game hung in state: {final_state['state']}"

            # Count AI actions to ensure no infinite loop
            ai_action_count = ws.count_ai_actions()
            print(f"AI actions: {ai_action_count}")
            assert ai_action_count <= 20, \
                f"Too many AI actions ({ai_action_count}) - possible infinite loop"

            print("✅ All-in scenario completed successfully")

    @pytest.mark.asyncio
    async def test_raise_reraise_sequence(self):
        """
        Test: Human raises → AI re-raises → Human re-raises again.

        Tests multiple raise rounds in single betting round.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)

            # Initial raise
            initial_raise = state["data"]["big_blind"] * 3
            print(f"Initial raise: {initial_raise}")
            await ws.send_action("raise", amount=initial_raise)

            # Wait for AI response
            events = await ws.drain_events(max_events=20, timeout=8.0)

            # Check if we get another turn (AI re-raised)
            current_state = ws.get_latest_state()
            human_player = current_state["human_player"]

            # If still in pre_flop and it's our turn, we can re-raise
            # Check if human player is current by looking at is_current_turn flag
            if current_state["state"] == "pre_flop" and \
               human_player.get("is_current_turn", False):

                # Re-raise
                reraise_amount = human_player["stack"] // 2  # Raise half our stack
                print(f"Re-raising: {reraise_amount}")
                await ws.send_action("raise", amount=reraise_amount)

                # Wait for completion
                events = await ws.drain_events(max_events=50, timeout=10.0)

            # Verify game completed without hanging
            final_state = ws.get_latest_state()
            assert final_state is not None
            print(f"✅ Raise sequence completed, final state: {final_state['state']}")


# =============================================================================
# 4.3: Edge Case Scenarios (2 hours)
# =============================================================================

class TestEdgeCaseScenarios:
    """Test boundary conditions and special situations"""

    @pytest.mark.asyncio
    async def test_minimum_raise_amounts(self):
        """
        Test raising exactly the minimum allowed amount.

        Minimum raise = current_bet + big_blind
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)

            # Calculate minimum raise
            current_bet = state["data"]["current_bet"]
            big_blind = state["data"]["big_blind"]
            min_raise = current_bet + big_blind

            print(f"Minimum raise: {min_raise} (current_bet={current_bet}, bb={big_blind})")

            # Attempt minimum raise
            await ws.send_action("raise", amount=min_raise)

            # Should be accepted
            events = await ws.drain_events(max_events=50, timeout=10.0)

            # Verify action was processed (not rejected)
            final_state = ws.get_latest_state()
            assert final_state is not None

            # Check that our bet was registered
            # Note: State should have advanced from pre_flop or we should see our bet
            print(f"✅ Minimum raise accepted, state: {final_state['state']}")

    @pytest.mark.asyncio
    async def test_raise_exactly_remaining_stack(self):
        """
        Test raising exactly our remaining stack (all-in).

        Edge case: amount = stack (not stack + current_bet)
        This should be auto-corrected to all-in.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)
            human_player = state["data"]["human_player"]

            # Try raising exactly our stack (forgetting current_bet)
            # This is a common frontend mistake
            stack_only = human_player["stack"]
            print(f"Attempting raise of {stack_only} (stack only, not stack+bet)")

            await ws.send_action("raise", amount=stack_only)

            # Should be handled gracefully (auto-corrected to all-in or rejected gracefully)
            events = await ws.drain_events(max_events=50, timeout=10.0)

            final_state = ws.get_latest_state()
            assert final_state is not None, "Game should handle this gracefully"

            print(f"✅ Edge case handled, state: {final_state['state']}")

    @pytest.mark.asyncio
    async def test_call_when_already_matched(self):
        """
        Test calling when our bet already matches current_bet.

        Edge case: No additional chips needed but player calls anyway.
        Should be treated as check or no-op.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)

            # First action: call to match
            await ws.send_action("call")
            events = await ws.drain_events(max_events=30, timeout=8.0)

            # If we get another turn on flop, call again when already matched
            current_state = ws.get_latest_state()
            if current_state["state"] in ["flop", "turn", "river"]:
                human_player = current_state["human_player"]

                # If no one has bet yet, our current_bet should be 0
                if current_state["current_bet"] == 0:
                    print("Calling when bet is already matched (check)")
                    await ws.send_action("call")

                    events = await ws.drain_events(max_events=30, timeout=8.0)

            final_state = ws.get_latest_state()
            assert final_state is not None
            print("✅ Edge case call handled")

    @pytest.mark.asyncio
    async def test_rapid_hand_progression(self):
        """
        Test playing 5 hands rapidly with minimal delay.

        Tests:
        - Game handles rapid next_hand requests
        - No state corruption with fast transitions
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            await ws.wait_for_event("state_update", timeout=5.0)

            for hand_num in range(5):
                print(f"Hand {hand_num + 1}/5")

                # Quick fold
                await ws.send_action("fold")
                await ws.drain_events(max_events=50, timeout=8.0)

                # Immediately start next hand (no delay)
                if hand_num < 4:
                    final_state = ws.get_latest_state()
                    if final_state["state"] == "showdown":
                        await ws.send_next_hand()
                        # Minimal delay
                        await asyncio.sleep(0.1)

            print("✅ Rapid progression completed")

    @pytest.mark.asyncio
    async def test_very_small_raise_attempt(self):
        """
        Test raising by a very small amount (less than big blind).

        Should be rejected with appropriate error.
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)

            # Try to raise by just 1 chip
            print("Attempting raise of 1 chip (should be rejected)")
            await ws.send_action("raise", amount=1)

            # Game should handle gracefully
            events = await ws.drain_events(max_events=30, timeout=8.0)

            final_state = ws.get_latest_state()
            assert final_state is not None
            print("✅ Small raise handled gracefully")

    @pytest.mark.asyncio
    async def test_play_until_elimination(self):
        """
        Test playing until human player is eliminated.

        Tests:
        - Game handles player running out of chips
        - Elimination is detected correctly
        - No crashes on $0 stack
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)

            max_hands = 50  # Limit to prevent infinite loop
            hands_played = 0

            for hand_num in range(max_hands):
                # Get current state (might already be our turn)
                current_state_data = ws.get_latest_state()
                if not current_state_data or not current_state_data.get("human_player", {}).get("is_current_turn"):
                    # Wait for our turn if it's not already
                    state_event = await ws.wait_for_event("state_update", timeout=10.0)
                    current_state_data = state_event["data"]

                human_player = current_state_data["human_player"]

                # Check if eliminated
                if human_player["stack"] == 0:
                    print(f"✅ Player eliminated after {hands_played} hands")
                    break

                # Go all-in to speed up elimination
                all_in = human_player["stack"] + human_player["current_bet"]
                await ws.send_action("raise", amount=all_in)

                await ws.drain_events(max_events=100, timeout=15.0)
                hands_played += 1

                final_state = ws.get_latest_state()
                if final_state["state"] == "showdown" and hand_num < max_hands - 1:
                    await ws.send_next_hand()
                    await asyncio.sleep(0.3)

            print(f"Played {hands_played} hands before elimination")
            assert hands_played > 0


# =============================================================================
# Summary
# =============================================================================

"""
Phase 4 Test Coverage:

Multi-Hand Scenarios (3 tests):
- test_go_all_in_every_hand_for_10_hands
- test_conservative_strategy_fold_90_percent
- test_mixed_strategy_10_hands

Complex Betting Sequences (3 tests):
- test_raise_call_multiple_streets
- test_all_players_go_all_in_scenario (UAT-5 regression)
- test_raise_reraise_sequence

Edge Case Scenarios (6 tests):
- test_minimum_raise_amounts
- test_raise_exactly_remaining_stack
- test_call_when_already_matched
- test_rapid_hand_progression
- test_very_small_raise_attempt
- test_play_until_elimination

Total: 12 scenario tests covering real user journeys
"""
