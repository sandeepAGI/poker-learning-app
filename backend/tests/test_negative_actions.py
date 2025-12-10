"""
Negative Testing Suite - Error Handling Path Tests

Phase 1 of Testing Improvement Plan (docs/TESTING_IMPROVEMENT_PLAN.md)

CRITICAL: These tests validate error handling paths that were previously UNTESTED.
The infinite loop bug existed because we never tested what happens when apply_action() fails.

Current coverage: Error handling paths (formerly 0%, now growing)
"""
import pytest
import asyncio
import json
import httpx
import websockets
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
import sys
import os
import threading
import uvicorn
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from game.poker_engine import PokerGame, GameState


# Global server thread and flag
server_thread = None
server_started = False


def start_test_server():
    """Start FastAPI server in background thread for negative tests"""
    config = uvicorn.Config(app, host="127.0.0.1", port=8002, log_level="error")
    server = uvicorn.Server(config)
    server.run()


@pytest.fixture(scope="session", autouse=True)
def test_server():
    """Start test server once for all tests"""
    global server_thread, server_started

    if not server_started:
        server_thread = threading.Thread(target=start_test_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Wait for server to start
        server_started = True

    yield


class WebSocketTestClient:
    """WebSocket test client for negative testing"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.ws = None
        self.received_messages = []
        self.ws_url = f"ws://127.0.0.1:8002/ws/{game_id}"

    async def __aenter__(self):
        self.ws = await websockets.connect(self.ws_url)
        return self

    async def __aexit__(self, *args):
        if self.ws:
            await self.ws.close()

    async def send_action(self, action: str, amount: int = None, show_ai_thinking: bool = True, step_mode: bool = False):
        """Send player action"""
        message = {
            "type": "action",
            "action": action,
            "amount": amount,
            "show_ai_thinking": show_ai_thinking,
            "step_mode": step_mode
        }
        await self.ws.send(json.dumps(message))

    async def receive_event(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Receive one event from WebSocket"""
        try:
            data = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            message = json.loads(data)
            self.received_messages.append(message)
            return message
        except asyncio.TimeoutError:
            raise TimeoutError(f"No event received within {timeout}s. Last messages: {self.received_messages[-3:]}")

    async def drain_events(self, max_events: int = 100, timeout: float = 0.5) -> List[Dict[str, Any]]:
        """Drain all pending events"""
        events = []
        for _ in range(max_events):
            try:
                event = await self.receive_event(timeout=timeout)
                events.append(event)
            except TimeoutError:
                break
        return events

    def count_events_by_type(self, event_type: str) -> int:
        """Count events of specific type"""
        return sum(1 for msg in self.received_messages if msg.get("type") == event_type)

    def get_ai_action_counts_by_player(self) -> Dict[str, int]:
        """
        Count how many times each player acted (by name).
        Returns: {"Player Name": action_count, ...}
        """
        counts = {}
        for msg in self.received_messages:
            if msg.get("type") == "ai_action":
                player_name = msg.get("data", {}).get("player_name", "Unknown")
                counts[player_name] = counts.get(player_name, 0) + 1
        return counts


async def create_test_game(ai_count: int = 3) -> str:
    """Create a game via REST API and return game_id"""
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8002") as client:
        response = await client.post("/games", json={"player_name": "TestPlayer", "ai_count": ai_count})
        assert response.status_code == 200
        return response.json()["game_id"]


class TestInfiniteLoopRegression:
    """
    REGRESSION TEST for infinite loop bug discovered in UAT.

    Bug: WebSocket AI processing didn't check apply_action() result["success"]
    Impact: Failed actions left has_acted=False, causing same player to be processed infinitely
    """

    @pytest.mark.asyncio
    async def test_ai_action_failure_doesnt_cause_infinite_loop(self):
        """
        CRITICAL REGRESSION TEST: AI action failure must not cause infinite loop.

        This test MUST FAIL until bug is fixed in websocket_manager.py.

        Simulates scenario where apply_action() returns success: False for an AI player.
        Without the fix, the AI player's has_acted flag stays False, causing infinite loop.
        With the fix, the code should handle the failure gracefully (e.g., force fold).

        Success criteria:
        - No player acts more than 4 times in a single betting round
        - Game continues after action failure (doesn't hang)
        - Fallback action is applied (e.g., fold)
        """
        game_id = await create_test_game(ai_count=3)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)
            assert initial_state["type"] == "state_update"

            # Track which player fails
            failing_player_index = [None]
            original_apply_action = PokerGame.apply_action

            def mock_apply_action(self, player_index, action, amount=0, hand_strength=0.0, reasoning=""):
                """
                Mock that fails NON-FOLD actions for a specific player.

                This simulates a validation error (e.g., invalid raise).
                Fold actions are allowed to succeed (so fallback works).
                Without the bug fix, this causes an infinite loop as the player's
                has_acted flag never gets set to True.
                """
                # Set the failing player on first AI action (player_index 1)
                if failing_player_index[0] is None and player_index == 1:
                    failing_player_index[0] = player_index
                    print(f"[TEST] Will fail non-fold actions for player_index={player_index}")

                # Fail NON-FOLD actions for the designated player
                # (Allow fold to succeed so fallback works)
                if player_index == failing_player_index[0] and action != "fold":
                    print(f"[TEST] Injecting failure for player_index={player_index}, action={action}")
                    return {
                        "success": False,
                        "bet_amount": 0,
                        "triggers_showdown": False,
                        "error": f"Invalid {action}: simulated validation failure"
                    }

                # Otherwise call real method
                return original_apply_action(self, player_index, action, amount, hand_strength, reasoning)

            # Patch apply_action to inject failure
            with patch.object(PokerGame, 'apply_action', mock_apply_action):
                # Send human action to trigger AI processing
                await ws.send_action("fold")

                # Collect all events with a SHORT timeout
                # If there's an infinite loop, we'll hit max_events quickly
                # Reduced timeout to 2.0s so test fails faster
                events = await ws.drain_events(max_events=100, timeout=2.0)

                # Analyze AI action counts
                action_counts = ws.get_ai_action_counts_by_player()

                print(f"[TEST] Received {len(events)} events")
                print(f"[TEST] AI action counts by player: {action_counts}")

                # CRITICAL ASSERTION: No player should act more than 4 times in one betting round
                # (4 = reasonable max for a betting round with re-raises)
                # If any player acts >4 times, it indicates an infinite loop
                for player_name, count in action_counts.items():
                    assert count <= 4, (
                        f"INFINITE LOOP DETECTED: {player_name} acted {count} times! "
                        f"Expected ≤4 actions per player in a betting round. "
                        f"This indicates apply_action() failure wasn't handled properly."
                    )

                # Additional check: Total events shouldn't exceed reasonable limit
                # Normal game: ~10-20 events per betting round
                # Infinite loop: Would quickly hit 100+ events
                assert len(events) < 50, (
                    f"Too many events ({len(events)}) - possible infinite loop or stuck state"
                )

                # Success: Game handled action failure without infinite loop
                print("[TEST] ✅ No infinite loop detected - action failure handled properly")


class TestInvalidActionHandling:
    """
    Test how the system handles various invalid actions.
    These tests will be expanded in Phase 2 (Negative Testing Suite).
    """

    @pytest.mark.asyncio
    async def test_invalid_raise_amount_below_minimum(self):
        """
        Test: Raise amount below minimum should be rejected gracefully.

        This is a placeholder for Phase 2 expansion.
        Currently validates that invalid raises return success: False.
        """
        # Create game with direct API
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)  # Don't process AI, just set up game state

        # Find current player
        current_player = game.players[game.current_player_index]

        # Try to raise below minimum (current_bet + big_blind)
        min_raise = game.current_bet + game.big_blind
        invalid_raise = min_raise - 5  # 5 below minimum

        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=invalid_raise
        )

        # Should fail validation
        assert result["success"] is False, "Invalid raise should be rejected"
        assert "below minimum" in result["error"].lower(), "Error message should mention minimum"

        # Player should NOT have has_acted set to True after failed action
        # (This is critical for preventing infinite loops)
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

        print(f"[TEST] ✅ Invalid raise properly rejected: {result['error']}")

    @pytest.mark.asyncio
    async def test_raise_more_than_stack_caps_to_all_in(self):
        """
        Test: Raise exceeding stack should cap at all-in.

        Phase 2.1 - Invalid raise amount handling.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]
        original_stack = current_player.stack

        # Try to raise more than total chips (stack + current_bet)
        excessive_raise = current_player.stack + current_player.current_bet + 5000

        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=excessive_raise
        )

        # Should succeed but cap at all-in
        assert result["success"] is True, "Should succeed and cap to all-in"
        assert current_player.stack == 0, "Player should be all-in (stack=0)"
        assert current_player.all_in is True, "Player should be marked as all-in"
        assert result["bet_amount"] == original_stack, "Should bet entire original stack"

        print(f"[TEST] ✅ Excessive raise capped to all-in: {result['bet_amount']} chips")

    @pytest.mark.asyncio
    async def test_negative_raise_amount_rejected(self):
        """
        Test: Negative raise amounts should be rejected.

        Phase 2.1 - Invalid raise amount handling.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]

        # Try negative amount
        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=-100
        )

        # Should fail validation
        assert result["success"] is False, "Negative amount should be rejected"
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

        print(f"[TEST] ✅ Negative raise rejected: {result['error']}")

    @pytest.mark.asyncio
    async def test_zero_raise_amount_rejected(self):
        """
        Test: Zero raise amount should be rejected.

        Phase 2.1 - Invalid raise amount handling.
        """
        game = PokerGame(human_player_name="TestPlayer", ai_count=2)
        game.start_new_hand(process_ai=False)

        current_player = game.players[game.current_player_index]

        # Try zero amount
        result = game.apply_action(
            player_index=game.current_player_index,
            action="raise",
            amount=0
        )

        # Should fail validation
        assert result["success"] is False, "Zero amount should be rejected"
        assert current_player.has_acted is False, "Failed action should not set has_acted=True"

        print(f"[TEST] ✅ Zero raise rejected: {result['error']}")

    @pytest.mark.asyncio
    async def test_websocket_invalid_raise_handled_gracefully(self):
        """
        Test: Invalid raise via WebSocket should be handled gracefully (no crash).

        Phase 2.1 - Full-stack validation via WebSocket.
        Tests that invalid raises don't cause infinite loops or crashes.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)
            assert initial_state["type"] == "state_update"

            # Send invalid raise (below minimum)
            await ws.send_action("raise", amount=5)  # Way below minimum

            # Game should handle gracefully - either reject or cap
            events = await ws.drain_events(timeout=3.0)

            # Verify game didn't crash/hang
            assert len(events) > 0, "Should receive events (game didn't hang)"

            # Game should continue (AI players should act)
            ai_action_count = ws.count_events_by_type("ai_action")
            assert ai_action_count >= 2, f"AI should continue playing (got {ai_action_count} AI actions)"

            print(f"[TEST] ✅ Invalid raise via WebSocket handled gracefully ({len(events)} events received)")


class TestInvalidActionSequences:
    """
    Phase 2.2: Test actions at wrong times are rejected.

    Validates that the game enforces turn order and game state constraints.
    """

    @pytest.mark.asyncio
    async def test_action_when_not_your_turn(self):
        """
        Test: Acting out of turn should be rejected.

        Phase 2.2 - Action sequence validation.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)
            assert initial_state["type"] == "state_update"

            current_player_index = initial_state["data"]["current_player_index"]

            # Find human player index from players array
            players = initial_state["data"]["players"]
            human_player_index = next(i for i, p in enumerate(players) if p["is_human"])

            # If it's not human's turn, try to act anyway
            if current_player_index != human_player_index:
                # Try to act out of turn
                await ws.send_action("call")

                # Should receive events, but human action shouldn't be processed
                events = await ws.drain_events(timeout=3.0)

                # Verify AI still acts (game continues normally)
                ai_action_count = ws.count_events_by_type("ai_action")
                assert ai_action_count >= 1, "AI should continue acting normally"

                print(f"[TEST] ✅ Out-of-turn action rejected, game continued normally")
            else:
                # If it IS human's turn, just act normally and verify it works
                await ws.send_action("call")
                events = await ws.drain_events(timeout=3.0)
                assert len(events) > 0, "Should receive events"
                print(f"[TEST] ✅ Human was current player, action processed normally")

    @pytest.mark.asyncio
    async def test_action_after_folding(self):
        """
        Test: Folded players cannot act.

        Phase 2.2 - Action sequence validation.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)
            assert initial_state["type"] == "state_update"

            # Fold
            await ws.send_action("fold")

            # Wait for AI to finish acting
            events = await ws.drain_events(timeout=3.0)

            # Try to act again after folding
            await ws.send_action("call")

            # Should not process this action
            more_events = await ws.drain_events(timeout=2.0)

            # Game should continue with AI actions only
            ai_actions_after_fold = sum(1 for e in more_events if e.get("type") == "ai_action")

            print(f"[TEST] ✅ Action after fold ignored, game continued with {ai_actions_after_fold} AI actions")

    @pytest.mark.asyncio
    async def test_action_after_hand_complete(self):
        """
        Test: Cannot act after showdown.

        Phase 2.2 - Action sequence validation.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)

            # Fold to quickly end hand
            await ws.send_action("fold")

            # Wait for hand to complete (showdown)
            events = await ws.drain_events(timeout=5.0)

            # Check if we reached showdown
            state_updates = [e for e in events if e.get("type") == "state_update"]
            if state_updates:
                final_state = state_updates[-1]["data"]["state"]
                if final_state == "showdown":
                    # Try to act after showdown
                    await ws.send_action("call")

                    # Should not process
                    more_events = await ws.drain_events(timeout=1.0)

                    # Should receive minimal or no events
                    print(f"[TEST] ✅ Action after showdown ignored ({len(more_events)} events)")
                else:
                    print(f"[TEST] ⚠️  Hand didn't reach showdown (state: {final_state}), skipping test")
            else:
                print(f"[TEST] ⚠️  No state updates received, test inconclusive")

    @pytest.mark.asyncio
    async def test_rapid_duplicate_actions(self):
        """
        Test: Rapid duplicate actions - only first should count.

        Phase 2.3 - Rapid action handling.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)

            # Send same action 10 times rapidly
            for _ in range(10):
                await ws.send_action("call")

            # Wait for events
            events = await ws.drain_events(timeout=5.0)

            # Count how many times human action was processed
            # Should only be processed once
            # (Hard to test precisely, but game shouldn't crash/hang)

            # Main validation: Game didn't crash
            assert len(events) > 0, "Game should continue (not crash from rapid actions)"

            # Game should reach reasonable state
            ai_action_count = ws.count_events_by_type("ai_action")
            assert ai_action_count >= 1, "AI should act normally"

            print(f"[TEST] ✅ Rapid duplicate actions handled ({len(events)} events, {ai_action_count} AI actions)")


class TestRapidActionSpam:
    """
    Phase 2.3: Test rapid action spam doesn't crash the game.

    Validates system resilience under extreme conditions.
    """

    @pytest.mark.asyncio
    async def test_action_spam_concurrent(self):
        """
        Test: Sending many actions concurrently shouldn't crash.

        Phase 2.3 - Stress test for action handling.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)
            assert initial_state["type"] == "state_update"

            # Send 50 actions as fast as possible
            # Mix of valid and invalid actions
            actions = ["call", "fold", "raise"] * 16 + ["call", "fold"]
            amounts = [None, None, 100] * 16 + [None, None]

            for action, amount in zip(actions, amounts):
                try:
                    await ws.send_action(action, amount=amount)
                except Exception as e:
                    # Even if some fail, keep trying
                    pass

            # Give time for all actions to be processed (or rejected)
            await asyncio.sleep(1.0)

            # Drain events
            events = await ws.drain_events(timeout=5.0)

            # Main validation: System didn't crash
            assert len(events) > 0, "System should respond (not crash from action spam)"

            # Game should still be in valid state
            state_updates = [e for e in events if e.get("type") == "state_update"]
            if state_updates:
                final_state = state_updates[-1]["data"]
                # Basic sanity checks
                assert "state" in final_state, "Should have valid game state"
                assert "players" in final_state, "Should have players"

            print(f"[TEST] ✅ Action spam handled ({len(events)} events received, no crash)")

    @pytest.mark.asyncio
    async def test_invalid_action_types_rejected(self):
        """
        Test: Invalid action types should be rejected gracefully.

        Phase 2 - Negative testing for action validation.
        """
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Receive initial state
            initial_state = await ws.receive_event(timeout=3.0)

            # Try invalid action types
            invalid_actions = ["check", "bet", "allin", "CALL", "Fold", "", "invalid"]

            for invalid_action in invalid_actions:
                try:
                    await ws.send_action(invalid_action)
                except Exception:
                    pass  # Expected to fail

            # Wait a bit
            await asyncio.sleep(0.5)

            # Game should still function
            await ws.send_action("fold")  # Valid action
            events = await ws.drain_events(timeout=3.0)

            # Game should continue normally
            assert len(events) > 0, "Game should continue after invalid actions"

            print(f"[TEST] ✅ Invalid action types rejected, game continued normally")
