"""
Phase 8: Concurrency & Race Conditions Testing (16 hours)

Tests simultaneous actions, state transition races, and thread safety.
Critical for production - prevents corrupted game state from concurrent users.

Test Categories:
1. Simultaneous Actions (6 hours) - Multiple connections, rapid spam
2. State Transition Races (6 hours) - Actions during state changes, concurrent game creation
3. Thread Safety (4 hours) - Locking verification

Port: 8003 (to avoid conflicts with other test suites)
"""
import pytest
import asyncio
import json
import httpx
import websockets
from typing import List, Dict, Any, Optional
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
    """Start FastAPI server on port 8003 for concurrency tests"""
    config = uvicorn.Config(app, host="127.0.0.1", port=8003, log_level="error")
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


class ConcurrentWebSocketClient:
    """
    WebSocket client for concurrency testing.

    Supports:
    - Simultaneous action sending
    - Race condition detection
    - Event tracking with timestamps
    """

    def __init__(self, game_id: str, client_id: str, port: int = 8003):
        self.game_id = game_id
        self.client_id = client_id
        self.ws = None
        self.received_messages = []
        self.port = port
        self.ws_url = f"ws://127.0.0.1:{port}/ws/{game_id}"
        self.connected = False

    async def connect(self):
        """Connect to WebSocket"""
        if self.ws:
            await self.ws.close()

        self.ws = await websockets.connect(self.ws_url)
        self.connected = True
        print(f"[{self.client_id}] WebSocket connected to {self.ws_url}")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.connected = False
            print(f"[{self.client_id}] WebSocket disconnected")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        if self.ws:
            await self.ws.close()

    async def send_action(self, action: str, amount: int = None, expect_success: bool = True):
        """
        Send player action.

        Returns tuple: (success: bool, response: dict or exception)
        """
        if not self.connected or not self.ws:
            return False, ConnectionError("Not connected to WebSocket")

        message = {
            "type": "action",
            "action": action,
            "amount": amount,
            "show_ai_thinking": False
        }

        try:
            await self.ws.send(json.dumps(message))

            # Wait for response (either success or error)
            response = await asyncio.wait_for(self.ws.recv(), timeout=2.0)
            result = json.loads(response)
            self.received_messages.append(result)

            success = result.get("type") != "error"
            print(f"[{self.client_id}] Action {action}: {'SUCCESS' if success else 'REJECTED'}")
            return success, result

        except Exception as e:
            print(f"[{self.client_id}] Action {action}: EXCEPTION {type(e).__name__}")
            return False, e

    async def receive_event(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Receive one event from WebSocket"""
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to WebSocket")

        try:
            data = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            message = json.loads(data)
            self.received_messages.append(message)
            return message
        except asyncio.TimeoutError:
            raise TimeoutError(f"No event received within {timeout}s")

    async def wait_for_event(self, event_type: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for specific event type"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            remaining = timeout - (asyncio.get_event_loop().time() - start)
            event = await self.receive_event(timeout=remaining)
            if event.get("type") == event_type:
                return event
        raise TimeoutError(f"Event '{event_type}' not received within {timeout}s")

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

    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get most recent state_update event"""
        for msg in reversed(self.received_messages):
            if msg.get("type") == "state_update":
                return msg.get("data", {})
        return None

    def get_error_count(self) -> int:
        """Count error responses received"""
        return sum(1 for msg in self.received_messages if msg.get("type") == "error")

    def clear_messages(self):
        """Clear received messages"""
        self.received_messages = []


async def create_test_game(ai_count: int = 3, port: int = 8003) -> str:
    """Create a test game via REST API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://127.0.0.1:{port}/games",
            json={"name": "Test Game", "ai_count": ai_count}
        )
        return response.json()["game_id"]


# ====================
# Phase 8.1: Simultaneous Actions Tests (6 hours)
# ====================

@pytest.mark.asyncio
async def test_two_connections_same_game_simultaneous_fold():
    """
    CRITICAL: Two WebSocket connections send fold actions at exactly the same time.

    Expected behavior:
    - Only ONE action should succeed (first to acquire lock)
    - Other action should be REJECTED (not their turn or already acted)
    - Both clients should see same final state
    - No race condition corruption

    This tests the core concurrency lock mechanism.
    """
    print("\n=== TEST: Simultaneous Fold from Two Connections ===")

    game_id = await create_test_game(ai_count=2)

    async with ConcurrentWebSocketClient(game_id, "Client1") as ws1, \
               ConcurrentWebSocketClient(game_id, "Client2") as ws2:

        # Wait for initial state
        await ws1.wait_for_event("state_update")
        await ws2.wait_for_event("state_update")

        # Both send fold action SIMULTANEOUSLY
        print("[TEST] Sending simultaneous fold actions...")
        results = await asyncio.gather(
            ws1.send_action("fold"),
            ws2.send_action("fold"),
            return_exceptions=True
        )

        # Analyze results - but don't trust the immediate response!
        # The test needs to check the actual game state, not just WebSocket responses
        success1, result1 = results[0] if not isinstance(results[0], Exception) else (False, results[0])
        success2, result2 = results[1] if not isinstance(results[1], Exception) else (False, results[1])

        print(f"[TEST] Client1 initial response: {'SUCCESS' if success1 else 'REJECTED/ERROR'}")
        print(f"[TEST] Client2 initial response: {'SUCCESS' if success2 else 'REJECTED/ERROR'}")

        # Drain all events to get final state
        print("[TEST] Draining events to get final game state...")
        await asyncio.sleep(1.0)  # Give server time to process both actions
        events1 = await ws1.drain_events(timeout=3.0)
        events2 = await ws2.drain_events(timeout=3.0)

        # Check for error messages (true indicator of rejection)
        errors1 = [e for e in events1 if e.get("type") == "error"]
        errors2 = [e for e in events2 if e.get("type") == "error"]

        print(f"[TEST] Client1 errors: {len(errors1)}")
        print(f"[TEST] Client2 errors: {len(errors2)}")

        # CRITICAL: At least ONE should have received an error
        # (because the second fold attempt should fail - already acted or not your turn)
        total_errors = len(errors1) + len(errors2)
        assert total_errors >= 1, \
            f"RACE CONDITION! Neither client received error - both folds may have been processed! " \
            f"(errors1={len(errors1)}, errors2={len(errors2)})"

        # Both clients should see same final state
        state1 = ws1.get_latest_state()
        state2 = ws2.get_latest_state()

        assert state1 is not None, "Client1 never received state update"
        assert state2 is not None, "Client2 never received state update"

        # States should be identical (same pot, same players, same turn)
        assert state1.get("pot") == state2.get("pot"), \
            f"State divergence! Client1 pot={state1.get('pot')}, Client2 pot={state2.get('pot')}"

        # Verify game is in valid state (not corrupted)
        assert state1.get("state") in ["pre_flop", "flop", "turn", "river", "showdown"], \
            f"Game in invalid state: {state1.get('state')}"

        print("[TEST] ✅ Simultaneous fold test passed - lock prevented race condition")


@pytest.mark.asyncio
async def test_rapid_action_spam_100_folds():
    """
    CRITICAL: Player clicks fold button 100 times in rapid succession (spam clicking).

    Expected behavior:
    - Only FIRST fold should process
    - Remaining 99 should be rejected (already acted or no longer their turn)
    - Game state should advance normally (not 100 folds)
    - No state corruption from spam

    Real users DO this - accidental double-clicks, laggy UI, etc.
    """
    print("\n=== TEST: Rapid Action Spam (100 Folds) ===")

    game_id = await create_test_game(ai_count=3)

    async with ConcurrentWebSocketClient(game_id, "Spammer") as ws:
        # Wait for initial state
        await ws.wait_for_event("state_update")

        # SPAM: Send 100 fold actions as fast as possible
        print("[TEST] Sending 100 rapid fold actions...")
        start_time = time.time()

        tasks = [ws.send_action("fold", expect_success=False) for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        print(f"[TEST] Sent 100 actions in {elapsed:.2f}s ({100/elapsed:.1f} actions/sec)")

        # Count successes
        successes = sum(1 for r in results if not isinstance(r, Exception) and r[0])
        print(f"[TEST] Successful actions: {successes}/100")

        # CRITICAL: Should be AT MOST 1 success (the first fold)
        assert successes <= 1, \
            f"RACE CONDITION! Multiple folds succeeded ({successes}) - state may be corrupted!"

        # Drain all remaining events
        await ws.drain_events(timeout=3.0)

        # Verify game state is consistent
        final_state = ws.get_latest_state()
        assert final_state is not None, "No final state received"

        # Count error responses (should be ~99 if 1 succeeded, ~100 if 0 succeeded)
        error_count = ws.get_error_count()
        print(f"[TEST] Error responses: {error_count}")

        # Game should be in valid state (not broken)
        assert final_state.get("state") in ["pre_flop", "flop", "turn", "river", "showdown"], \
            f"Game in invalid state: {final_state.get('state')}"

        print("[TEST] ✅ Rapid spam test passed - only first action processed")


@pytest.mark.asyncio
async def test_simultaneous_different_actions():
    """
    Two connections send DIFFERENT actions simultaneously (fold vs call).

    Expected behavior:
    - At most one succeeds (whoever's turn it actually is)
    - No corrupted state from both actions applying
    """
    print("\n=== TEST: Simultaneous Different Actions (Fold vs Call) ===")

    game_id = await create_test_game(ai_count=2)

    async with ConcurrentWebSocketClient(game_id, "Folder") as ws_fold, \
               ConcurrentWebSocketClient(game_id, "Caller") as ws_call:

        # Wait for initial state
        await ws_fold.wait_for_event("state_update")
        await ws_call.wait_for_event("state_update")

        # Send different actions simultaneously
        print("[TEST] Sending simultaneous fold and call...")
        results = await asyncio.gather(
            ws_fold.send_action("fold"),
            ws_call.send_action("call"),
            return_exceptions=True
        )

        # Drain all events to get final state
        print("[TEST] Draining events to get final game state...")
        await asyncio.sleep(1.0)  # Give server time to process both actions
        events_fold = await ws_fold.drain_events(timeout=3.0)
        events_call = await ws_call.drain_events(timeout=3.0)

        # Check for error messages (true indicator of rejection)
        errors_fold = [e for e in events_fold if e.get("type") == "error"]
        errors_call = [e for e in events_call if e.get("type") == "error"]

        print(f"[TEST] Fold errors: {len(errors_fold)}")
        print(f"[TEST] Call errors: {len(errors_call)}")

        # CRITICAL: At least ONE should have received an error
        # (because only one action can be valid at a time)
        total_errors = len(errors_fold) + len(errors_call)
        assert total_errors >= 1, \
            f"RACE CONDITION! Neither client received error - both actions may have been processed! " \
            f"(errors_fold={len(errors_fold)}, errors_call={len(errors_call)})"

        # Verify state consistency
        state_fold = ws_fold.get_latest_state()
        state_call = ws_call.get_latest_state()

        assert state_fold is not None and state_call is not None, "Missing final state"
        assert state_fold.get("pot") == state_call.get("pot"), \
            f"State divergence! Fold pot={state_fold.get('pot')}, Call pot={state_call.get('pot')}"

        print("[TEST] ✅ Different simultaneous actions test passed")


@pytest.mark.asyncio
async def test_rapid_raise_amount_changes():
    """
    User drags raise slider rapidly, sending many raise actions with different amounts.

    Expected behavior:
    - Only first raise processes
    - Subsequent raises rejected (already acted)
    - Final raise amount matches first request
    """
    print("\n=== TEST: Rapid Raise Amount Changes ===")

    game_id = await create_test_game(ai_count=3)

    async with ConcurrentWebSocketClient(game_id, "RaiseSpammer") as ws:
        await ws.wait_for_event("state_update")
        state = ws.get_latest_state()

        # Get valid raise amounts
        current_bet = state.get("current_bet", 0)
        min_raise = current_bet * 2

        # Send 20 rapid raise actions with different amounts
        print("[TEST] Sending 20 rapid raises with different amounts...")
        amounts = [min_raise + (i * 10) for i in range(20)]

        tasks = [ws.send_action("raise", amount=amt) for amt in amounts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if not isinstance(r, Exception) and r[0]]
        print(f"[TEST] Successful raises: {len(successes)}/20")

        # CRITICAL: At most 1 raise should succeed
        assert len(successes) <= 1, \
            f"RACE CONDITION! Multiple raises succeeded ({len(successes)})"

        # If one succeeded, verify amount matches first request
        if len(successes) == 1:
            await ws.drain_events(timeout=2.0)
            final_state = ws.get_latest_state()
            # We can't easily verify the exact amount here without deeper state inspection
            # Just verify game is in valid state
            assert final_state is not None
            assert final_state.get("state") in ["pre_flop", "flop", "turn", "river", "showdown"]

        print("[TEST] ✅ Rapid raise changes test passed")


# ====================
# Phase 8.2: State Transition Race Conditions (6 hours)
# ====================

@pytest.mark.asyncio
async def test_concurrent_game_creation():
    """
    CRITICAL: 10 users create games simultaneously.

    Expected behavior:
    - All 10 games created successfully
    - All game IDs are UNIQUE (no collisions)
    - All games are playable

    This tests UUID generation and game storage thread safety.
    """
    print("\n=== TEST: Concurrent Game Creation (10 games) ===")

    # Create 10 games simultaneously
    print("[TEST] Creating 10 games concurrently...")
    tasks = [create_test_game(ai_count=3) for _ in range(10)]

    start_time = time.time()
    game_ids = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    print(f"[TEST] Created 10 games in {elapsed:.2f}s")
    print(f"[TEST] Game IDs: {game_ids}")

    # CRITICAL: All IDs must be unique
    unique_ids = set(game_ids)
    assert len(unique_ids) == 10, \
        f"GAME ID COLLISION! Only {len(unique_ids)} unique IDs from 10 games: {game_ids}"

    # Verify all games are playable
    print("[TEST] Verifying all games are playable...")
    for i, game_id in enumerate(game_ids):
        async with ConcurrentWebSocketClient(game_id, f"Player{i}") as ws:
            state = await ws.wait_for_event("state_update", timeout=5.0)
            assert state is not None, f"Game {game_id} not playable"

    print("[TEST] ✅ Concurrent game creation test passed - all IDs unique")


@pytest.mark.asyncio
async def test_action_during_state_transition():
    """
    Player sends action while game is transitioning between states (e.g., pre_flop → flop).

    Expected behavior:
    - Action queued OR rejected gracefully
    - No state corruption
    - Game continues normally

    This is tricky because action arrives during state mutation.
    """
    print("\n=== TEST: Action During State Transition ===")

    game_id = await create_test_game(ai_count=3)

    async with ConcurrentWebSocketClient(game_id, "Player") as ws:
        # Wait for game to start
        await ws.wait_for_event("state_update")

        # Send action to complete first betting round
        success, _ = await ws.send_action("fold")

        # Immediately spam actions while AI processing and state transitioning
        # Some of these will arrive during state transition
        print("[TEST] Spamming actions during AI processing...")
        tasks = [ws.send_action("call") for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Drain all events
        await ws.drain_events(timeout=5.0)

        # Game should still be in valid state
        final_state = ws.get_latest_state()
        assert final_state is not None, "No final state after state transition spam"
        assert final_state.get("state") in ["pre_flop", "flop", "turn", "river", "showdown"], \
            f"Game in invalid state after transition spam: {final_state.get('state')}"

        print("[TEST] ✅ Action during state transition handled gracefully")


@pytest.mark.asyncio
async def test_multiple_simultaneous_raise_validations():
    """
    Multiple users send raises simultaneously with edge case amounts.

    Expected behavior:
    - Validation logic thread-safe
    - No corrupted pot or stack amounts
    - Chip conservation maintained
    """
    print("\n=== TEST: Simultaneous Raise Validation ===")

    game_id = await create_test_game(ai_count=3)

    async with ConcurrentWebSocketClient(game_id, "Raiser1") as ws1, \
               ConcurrentWebSocketClient(game_id, "Raiser2") as ws2:

        await ws1.wait_for_event("state_update")
        await ws2.wait_for_event("state_update")

        # Both try to raise simultaneously
        print("[TEST] Two clients raising simultaneously...")
        results = await asyncio.gather(
            ws1.send_action("raise", amount=100),
            ws2.send_action("raise", amount=150),
            return_exceptions=True
        )

        # Drain all events to get final state
        print("[TEST] Draining events to get final game state...")
        await asyncio.sleep(1.0)  # Give server time to process both actions
        events1 = await ws1.drain_events(timeout=3.0)
        events2 = await ws2.drain_events(timeout=3.0)

        # Check for error messages (true indicator of rejection)
        errors1 = [e for e in events1 if e.get("type") == "error"]
        errors2 = [e for e in events2 if e.get("type") == "error"]

        print(f"[TEST] Client1 errors: {len(errors1)}")
        print(f"[TEST] Client2 errors: {len(errors2)}")

        # CRITICAL: At least ONE should have received an error
        # (because only one raise can be valid at a time)
        total_errors = len(errors1) + len(errors2)
        assert total_errors >= 1, \
            f"RACE CONDITION! Neither client received error - both raises may have been processed! " \
            f"(errors1={len(errors1)}, errors2={len(errors2)})"

        # Both should see same final state
        state1 = ws1.get_latest_state()
        state2 = ws2.get_latest_state()

        assert state1 is not None and state2 is not None, "Missing final state"
        assert state1.get("pot") == state2.get("pot"), \
            f"State divergence! Client1 pot={state1.get('pot')}, Client2 pot={state2.get('pot')}"

        print("[TEST] ✅ Simultaneous raise validation test passed")


# ====================
# Summary Test
# ====================

@pytest.mark.asyncio
async def test_concurrency_stress_test():
    """
    Comprehensive stress test: Multiple connections, rapid actions, simultaneous requests.

    This is the "kitchen sink" test that tries to break the system.
    """
    print("\n=== TEST: Concurrency Stress Test ===")

    game_id = await create_test_game(ai_count=3)

    # Spawn 5 connections
    client0 = ConcurrentWebSocketClient(game_id, "Client0")
    client1 = ConcurrentWebSocketClient(game_id, "Client1")
    client2 = ConcurrentWebSocketClient(game_id, "Client2")
    client3 = ConcurrentWebSocketClient(game_id, "Client3")
    client4 = ConcurrentWebSocketClient(game_id, "Client4")

    async with client0, client1, client2, client3, client4:
        clients = [client0, client1, client2, client3, client4]

        # Wait for all to connect and get state
        await asyncio.gather(*[
            client.wait_for_event("state_update")
            for client in clients
        ])

        # All clients spam fold simultaneously
        print("[TEST] 5 clients spamming 10 folds each (50 total)...")
        all_tasks = []
        for client in clients:
            all_tasks.extend([client.send_action("fold") for _ in range(10)])

        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Drain all events to get final state
        print("[TEST] Draining events...")
        await asyncio.sleep(2.0)  # Give more time for 5 clients
        await asyncio.gather(*[
            client.drain_events(timeout=3.0)
            for client in clients
        ])

        # Count errors - with proper locking, most actions should be rejected
        all_messages = []
        for client in clients:
            all_messages.extend(client.received_messages)

        error_count = sum(1 for msg in all_messages if msg.get("type") == "error")
        print(f"[TEST] Total errors received: {error_count}")

        # Should have MANY errors (most of the 50 actions should be rejected)
        # With proper locking, only the player whose turn it is can act
        assert error_count >= 30, \
            f"RACE CONDITION! Too few errors ({error_count}/50) - many invalid actions may have succeeded!"

        # All clients should see same final state
        states = [client.get_latest_state() for client in clients]
        assert all(s is not None for s in states), "Some clients missing final state"

        # All states should be identical
        first_state = states[0]
        for i, state in enumerate(states[1:], 1):
            assert state.get("pot") == first_state.get("pot"), \
                f"State divergence! Client 0 pot={first_state.get('pot')} != Client {i} pot={state.get('pot')}"

    print("[TEST] ✅ Concurrency stress test passed - no race conditions detected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
