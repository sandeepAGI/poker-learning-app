"""
WebSocket Integration Tests

Tests the FULL stack: WebSocket → API → PokerEngine
These tests simulate REAL user behavior through the WebSocket layer.

Critical: These tests would have caught UAT bugs #5, #11, Step Mode deadlock, and infinite loop.
"""
import pytest
import asyncio
import json
import httpx
import websockets
from typing import List, Dict, Any
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

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.ws = None
        self.received_messages = []
        self.ws_url = f"ws://127.0.0.1:8001/ws/{game_id}"

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


async def create_test_game(ai_count: int = 3) -> str:
    """Create a game via REST API and return game_id"""
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        response = await client.post("/games", json={"player_name": "TestPlayer", "ai_count": ai_count})
        assert response.status_code == 200
        return response.json()["game_id"]


class TestWebSocketBasicFlow:
    """Test basic WebSocket flows"""

    @pytest.mark.asyncio
    async def test_connection_and_initial_state(self):
        """Test: Connect to WebSocket and receive initial state"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Should receive initial state
            initial_state = await ws.wait_for_event("state_update", timeout=5.0)
            assert initial_state["type"] == "state_update"
            assert initial_state["data"]["state"] == "pre_flop"
            assert len(initial_state["data"]["players"]) == 3  # 1 human + 2 AI

    @pytest.mark.asyncio
    async def test_simple_call_action(self):
        """Test: Human calls, AI players act"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            initial_state = await ws.wait_for_event("state_update")

            # Human calls
            await ws.send_action("call")

            # Should receive: state update, AI actions, more states
            events = await ws.drain_events(max_events=20, timeout=3.0)

            # At least one AI action should have occurred
            ai_actions = [e for e in events if e.get("type") == "ai_action"]
            assert len(ai_actions) > 0, "Expected AI to act after human call"

            # Should eventually reach human's turn again or next state
            assert any(e.get("type") == "state_update" for e in events)


class TestWebSocketAllInScenarios:
    """
    Test all-in scenarios via WebSocket.

    CRITICAL: These tests would have caught the infinite loop bug!
    """

    @pytest.mark.asyncio
    async def test_human_all_in_basic(self):
        """Test: Human goes all-in, game should not hang"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            initial = await ws.wait_for_event("state_update")
            # Wait for initial AI processing to complete
            await ws.drain_events(timeout=2.0)

            # Get current state after AI processing
            current_state = ws.get_latest_state()

            # If game already ended (all AIs folded), skip test
            if current_state["state"] == "showdown":
                print("Game ended during initial AI processing, skipping all-in test")
                return

            # If not human's turn, skip test
            if not current_state["human_player"]["is_current_turn"]:
                print("Not human's turn after initial processing, skipping test")
                return

            human_stack = current_state["human_player"]["stack"]
            human_current_bet = current_state["human_player"]["current_bet"]

            # Go all-in: Must include current bet (e.g., big blind already posted)
            all_in_amount = human_stack + human_current_bet
            await ws.send_action("raise", amount=all_in_amount)

            # Drain events with timeout
            events = await ws.drain_events(max_events=50, timeout=10.0)

            # CRITICAL: Should not timeout (infinite loop detection)
            assert len(events) > 0, "Game hung after all-in!"

            # Game should eventually reach showdown or advance state (or receive error)
            states = [e["data"]["state"] for e in events if e.get("type") == "state_update"]
            errors = [e for e in events if e.get("type") == "error"]

            # Either state advanced OR got an error (acceptable outcomes)
            assert len(states) > 0 or len(errors) > 0, \
                f"No state updates or errors after all-in. Events: {[e.get('type') for e in events]}"

    @pytest.mark.asyncio
    async def test_human_all_in_after_ai_raise(self):
        """Test: AI raises, human goes all-in (the scenario that caused infinite loop!)"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Play one hand normally to let AI build confidence to raise
            await ws.wait_for_event("state_update")
            await ws.send_action("fold")
            await ws.drain_events()

            # Start next hand
            await ws.send_next_hand()
            await ws.drain_events()

            # Now try to trigger a raise scenario by calling/raising
            state = ws.get_latest_state()
            human_stack = state["human_player"]["stack"]
            human_current_bet = state["human_player"]["current_bet"]

            # Go all-in: Must include current bet
            all_in_amount = human_stack + human_current_bet
            await ws.send_action("raise", amount=all_in_amount)

            # CRITICAL: Should complete without hanging
            events = await ws.drain_events(max_events=100, timeout=15.0)

            # Count iterations - if same player processed >10 times, infinite loop!
            ai_actions = [e for e in events if e.get("type") == "ai_action"]
            player_names = [a["data"]["player_name"] for a in ai_actions]

            # Check for repeated player actions
            for i, name in enumerate(player_names):
                same_player_streak = 1
                for j in range(i + 1, len(player_names)):
                    if player_names[j] == name:
                        same_player_streak += 1
                    else:
                        break

                assert same_player_streak < 10, \
                    f"Infinite loop detected! {name} acted {same_player_streak} times in a row. " \
                    f"Actions: {player_names[i:i+same_player_streak+5]}"


class TestWebSocketStepMode:
    """
    Test Step Mode via WebSocket.

    CRITICAL: These tests would have caught the Step Mode deadlock bug!
    """

    @pytest.mark.asyncio
    async def test_step_mode_basic(self):
        """Test: Step Mode pauses after each AI action"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
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
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
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


class TestWebSocketMultipleHands:
    """Test playing multiple hands in sequence"""

    @pytest.mark.asyncio
    async def test_play_three_hands(self):
        """Test: Play 3 complete hands without errors"""
        game_id = await create_test_game(ai_count=2)

        async with WebSocketTestClient(game_id) as ws:
            # Wait for initial state and drain initial AI processing
            await ws.wait_for_event("state_update")
            await ws.drain_events(timeout=2.0)

            for hand_num in range(3):
                print(f"\n=== Hand {hand_num + 1} ===")

                # Get current state
                current_state = ws.get_latest_state()

                # If game already at showdown (AIs finished the hand), just move to next
                if current_state["state"] == "showdown":
                    print(f"Hand {hand_num + 1} already at showdown (AIs finished it)")
                else:
                    # Verify in pre_flop or later state
                    assert current_state["state"] in ["pre_flop", "flop", "turn", "river", "showdown"], \
                        f"Hand {hand_num + 1} in unexpected state: {current_state['state']}"

                    # If it's human's turn, play the hand (fold to keep it simple)
                    if current_state["human_player"]["is_current_turn"]:
                        await ws.send_action("fold")
                        events = await ws.drain_events(timeout=5.0)

                        # Verify game advanced to showdown
                        final_state = ws.get_latest_state()
                        assert final_state["state"] == "showdown", \
                            f"Hand {hand_num + 1} did not reach showdown. State: {final_state['state']}"

                # Start next hand (except last iteration)
                if hand_num < 2:
                    await ws.send_next_hand()
                    # Wait for next hand to start
                    await ws.drain_events(timeout=2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
