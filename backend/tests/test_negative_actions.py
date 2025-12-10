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
