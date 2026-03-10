"""
WebSocket Integration Tests — Step Mode

Tests Step Mode behavior through the full stack: WebSocket -> API -> PokerEngine.
Validates that step mode pauses correctly and does not deadlock.

Other WebSocket flows (basic connect, all-in, multi-hand) are covered by:
  - test_websocket_simulation.py, test_action_processing.py (basic flow)
  - test_all_in_scenarios.py, test_property_based_enhanced.py (all-in)
  - test_complete_game.py, stress tests (multi-hand)
"""
import pytest
import asyncio
import json
import threading
import time
import sys
import os
from typing import List, Dict, Any

import uvicorn
import websockets

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from conftest import register_and_get_token, create_authed_game


# Global server thread and flag
server_thread = None
server_started = False


def start_test_server():
    """Start FastAPI server in background thread for WebSocket tests"""
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="error")
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

    # Server will be killed when test process ends (daemon thread)


class WebSocketTestClient:
    """
    WebSocket test client that simulates a real frontend.

    Provides:
    - Connect/disconnect to WebSocket
    - Send actions (fold, call, raise)
    - Receive events (state_update, ai_action, awaiting_continue)
    - Wait for specific events
    """

    def __init__(self, game_id: str, token: str):
        self.game_id = game_id
        self.token = token
        self.ws = None
        self.received_messages = []
        self.ws_url = f"ws://127.0.0.1:8001/ws/{game_id}?token={token}"

    async def __aenter__(self):
        self.ws = await websockets.connect(self.ws_url)
        return self

    async def __aexit__(self, *args):
        if self.ws:
            await self.ws.close()

    async def send_action(self, action: str, amount: int = None, show_ai_thinking: bool = False, step_mode: bool = False):
        """Send player action"""
        message = {
            "type": "action",
            "action": action,
            "amount": amount,
            "show_ai_thinking": show_ai_thinking,
            "step_mode": step_mode
        }
        await self.ws.send(json.dumps(message))

    async def send_continue(self):
        """Send continue signal (Step Mode)"""
        await self.ws.send(json.dumps({"type": "continue"}))

    async def send_next_hand(self, show_ai_thinking: bool = False, step_mode: bool = False):
        """Start next hand"""
        message = {
            "type": "next_hand",
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

    async def wait_for_event(self, event_type: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for specific event type"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            remaining = timeout - (asyncio.get_event_loop().time() - start)
            event = await self.receive_event(timeout=remaining)
            if event.get("type") == event_type:
                return event
        raise TimeoutError(f"Event '{event_type}' not received within {timeout}s")

    async def wait_for_state(self, state: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for game to reach specific state"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            remaining = timeout - (asyncio.get_event_loop().time() - start)
            event = await self.receive_event(timeout=remaining)
            if event.get("type") == "state_update" and event.get("data", {}).get("state") == state:
                return event
        raise TimeoutError(f"Game state '{state}' not reached within {timeout}s")

    async def drain_events(self, max_events: int = 100, timeout: float = 0.5) -> List[Dict[str, Any]]:
        """Drain all pending events (useful after AI actions)"""
        events = []
        for _ in range(max_events):
            try:
                event = await self.receive_event(timeout=timeout)
                events.append(event)
            except TimeoutError:
                break
        return events

    def count_ai_actions(self) -> int:
        """Count how many AI actions were received"""
        return sum(1 for msg in self.received_messages if msg.get("type") == "ai_action")

    def get_latest_state(self) -> Dict[str, Any]:
        """Get the most recent state_update event"""
        for msg in reversed(self.received_messages):
            if msg.get("type") == "state_update":
                return msg.get("data")
        return None


class TestWebSocketStepMode:
    """
    Test Step Mode via WebSocket.

    CRITICAL: These tests would have caught the Step Mode deadlock bug!
    """

    @pytest.mark.asyncio
    async def test_step_mode_basic(self):
        """Test: Step Mode pauses after each AI action"""
        token = await register_and_get_token(8001)
        game_id = await create_authed_game(8001, token, ai_count=2)

        async with WebSocketTestClient(game_id, token) as ws:
            # Wait for initial state and let initial AI processing complete
            await ws.wait_for_event("state_update")
            await ws.drain_events(timeout=1.0)  # Drain initial AI actions

            # Fold to complete first hand quickly
            await ws.send_action("fold")
            await ws.drain_events(timeout=2.0)

            # Start next hand with step_mode=True from the beginning
            await ws.send_next_hand(step_mode=True)

            # Should receive state update, then AI actions with awaiting_continue
            events = await ws.drain_events(max_events=20, timeout=3.0)

            # Find awaiting_continue events
            awaiting_events = [e for e in events if e.get("type") == "awaiting_continue"]
            assert len(awaiting_events) > 0, f"Step mode did not pause for AI action. Events: {[e.get('type') for e in events]}"

            # Send continue to unpause
            await ws.send_continue()

            # Should receive next AI action or state update
            next_events = await ws.drain_events(max_events=10, timeout=2.0)
            assert len(next_events) > 0, "Game did not continue after continue signal"

    @pytest.mark.asyncio
    async def test_step_mode_no_deadlock(self):
        """Test: Step Mode does not deadlock when receiving continue signal"""
        token = await register_and_get_token(8001)
        game_id = await create_authed_game(8001, token, ai_count=2)

        async with WebSocketTestClient(game_id, token) as ws:
            # Wait for initial state and drain initial AI processing
            await ws.wait_for_event("state_update")
            await ws.drain_events(timeout=1.0)

            # Fold first hand
            await ws.send_action("fold")
            await ws.drain_events(timeout=2.0)

            # Start next hand with step mode
            await ws.send_next_hand(step_mode=True)

            # Process all AI turns by clicking continue
            for i in range(10):  # Max 10 AI actions per betting round
                events = await ws.drain_events(max_events=5, timeout=1.0)

                # Check if waiting for continue
                if any(e.get("type") == "awaiting_continue" for e in events):
                    print(f"  Iteration {i+1}: Sending continue signal")
                    await ws.send_continue()
                else:
                    # No more AI actions, human's turn or round complete
                    print(f"  Iteration {i+1}: No awaiting_continue, stopping")
                    break

            # Game should reach a stable state (human's turn or next round)
            final_state = ws.get_latest_state()
            assert final_state is not None, "Game lost state after step mode"

            # Should be able to act normally
            await ws.send_action("fold", step_mode=False)
            events = await ws.drain_events()
            assert len(events) > 0, "Game did not respond after step mode sequence"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
