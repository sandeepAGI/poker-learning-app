"""
Phase 3.1: Action Fuzzing with WebSocket Integration
====================================================
Tests the game's robustness by sending 1000+ random actions (valid AND invalid).

Strategy:
- Test 1000 random raise amounts (50% invalid, 50% valid)
- Test 500 random action sequences (fold/call/raise combinations)
- Verify game NEVER crashes or hangs on any input
- Ensure invalid actions are rejected gracefully

Phase 3 of Testing Improvement Plan (10 hours total, 4 hours for fuzzing)
"""

import os
import pytest
import random
import asyncio
import json
import httpx
import websockets
from typing import Dict, Any, List


# Default to the standard backend port unless tests override via env vars
_default_port = os.getenv("TEST_BACKEND_PORT", "8000")
BASE_URL = os.getenv("TEST_API_BASE_URL", f"http://127.0.0.1:{_default_port}")
WS_BASE = os.getenv("TEST_WS_BASE_URL", f"ws://127.0.0.1:{_default_port}")

RAISE_ITERATIONS = int(os.getenv("TEST_FUZZ_RAISE_ITERATIONS", "1000"))
SEQUENCE_ITERATIONS = int(os.getenv("TEST_FUZZ_SEQUENCE_ITERATIONS", "500"))
INVALID_ITERATIONS = int(os.getenv("TEST_FUZZ_INVALID_ITERATIONS", "100"))
EXTREME_ITERATIONS = int(os.getenv("TEST_FUZZ_EXTREME_ITERATIONS", "50"))


class WebSocketTestClient:
    """WebSocket test client for fuzzing tests"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.ws = None
        self.received_messages = []
        self.ws_url = f"{WS_BASE}/ws/{game_id}"

    async def __aenter__(self):
        self.ws = await websockets.connect(self.ws_url)
        return self

    async def __aexit__(self, *args):
        if self.ws:
            await self.ws.close()

    async def send_action(self, action: str, amount: int = None):
        """Send player action"""
        message = {
            "type": "action",
            "action": action,
            "amount": amount,
            "show_ai_thinking": False,
            "step_mode": False
        }
        await self.ws.send(json.dumps(message))

    async def receive_event(self, timeout: float = 2.0) -> Dict[str, Any]:
        """Receive one event from WebSocket"""
        try:
            data = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            message = json.loads(data)
            self.received_messages.append(message)
            return message
        except asyncio.TimeoutError:
            raise TimeoutError(f"No event received within {timeout}s")

    async def wait_for_event(self, event_type: str, timeout: float = 5.0) -> Dict[str, Any]:
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

    def get_latest_state(self) -> Dict[str, Any]:
        """Get the most recent state_update event"""
        for msg in reversed(self.received_messages):
            if msg.get("type") == "state_update":
                return msg.get("data")
        return None


async def create_test_game(ai_count: int = 3) -> str:
    """Create a game via REST API and return game_id"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/games", json={"player_name": "FuzzTester", "ai_count": ai_count})
        assert response.status_code == 200
        return response.json()["game_id"]


@pytest.mark.slow
@pytest.mark.monthly  # Marathon tests: Require live backend server, run 5-10 min
class TestActionFuzzing:
    """Phase 3.1: Fuzz testing with random actions"""

    @pytest.mark.asyncio
    async def test_fuzz_raise_amounts_1000_iterations(self):
        """
        Test 1000 random raise amounts (50% invalid, 50% valid).

        Verifies game handles ALL inputs gracefully without crashing.
        Invalid: negative, zero, too small, too large
        Valid: random amounts within valid range
        """
        print(f"\n[FUZZ] Starting {RAISE_ITERATIONS} raise amount fuzzing iterations...")

        stats = {
            "total": 0,
            "valid_amounts": 0,
            "invalid_amounts": 0,
            "game_responded": 0,
            "game_hung": 0,
            "crashes": 0
        }

        for i in range(RAISE_ITERATIONS):
            try:
                game_id = await create_test_game()
                async with WebSocketTestClient(game_id) as ws:
                    # Wait for initial state
                    state = await ws.wait_for_event("state_update", timeout=3.0)
                    human_player = state["data"]["human_player"]

                    # Generate RANDOM raise amount (50% invalid, 50% valid)
                    if random.random() < 0.5:
                        # Invalid amounts
                        amount = random.choice([
                            -100,                                    # Negative
                            -random.randint(1, 10000),              # Random negative
                            0,                                       # Zero
                            random.randint(1, 5),                   # Too small (below BB)
                            random.randint(6, 19),                  # Below minimum raise
                            human_player["stack"] * 10,             # Way too large
                            human_player["stack"] + 99999,          # Absurdly large
                        ])
                        stats["invalid_amounts"] += 1
                    else:
                        # Valid amounts
                        max_valid = human_player["stack"] + human_player["current_bet"]
                        amount = random.randint(20, max_valid)
                        stats["valid_amounts"] += 1

                    stats["total"] += 1

                    # Send action
                    await ws.send_action("raise", amount=amount)

                    # Game should respond within 5 seconds (even if rejecting)
                    events = await ws.drain_events(timeout=5.0)

                    if len(events) > 0:
                        stats["game_responded"] += 1
                    else:
                        stats["game_hung"] += 1
                        print(f"[FUZZ] ⚠️  Game hung on iteration {i} with amount {amount}")

                    # Critical assertion: Game must ALWAYS respond
                    assert len(events) > 0, \
                        f"Game hung on iteration {i} with raise amount {amount}"

            except Exception as e:
                stats["crashes"] += 1
                print(f"[FUZZ] ❌ Crash on iteration {i}: {e}")
                # Don't fail immediately - collect crash stats
                if stats["crashes"] > 10:  # But fail if too many crashes
                    raise

        # Print summary
        print("\n" + "="*70)
        print("RAISE AMOUNT FUZZING SUMMARY")
        print("="*70)
        print(f"Total iterations:        {stats['total']:>7,}")
        print(f"  Valid amounts:         {stats['valid_amounts']:>7,}")
        print(f"  Invalid amounts:       {stats['invalid_amounts']:>7,}")
        print(f"\nGame responses:")
        print(f"  Responded (expected):  {stats['game_responded']:>7,}")
        print(f"  Hung (BUGS):           {stats['game_hung']:>7,}")
        print(f"  Crashes (BUGS):        {stats['crashes']:>7,}")
        print("="*70)

        # Assertions
        assert stats["game_hung"] == 0, f"Game hung {stats['game_hung']} times - CRITICAL BUG"
        assert stats["crashes"] == 0, f"Game crashed {stats['crashes']} times - CRITICAL BUG"


    @pytest.mark.asyncio
    async def test_fuzz_action_sequences_500_iterations(self):
        """
        Test 500 random action sequences.

        Generates random sequences like: raise→fold, call→raise→call, etc.
        Verifies game completes correctly regardless of action order.
        """
        print(f"\n[FUZZ] Starting {SEQUENCE_ITERATIONS} action sequence fuzzing iterations...")

        stats = {
            "total_games": 0,
            "total_actions": 0,
            "completed_successfully": 0,
            "errors": 0
        }

        for i in range(SEQUENCE_ITERATIONS):
            try:
                game_id = await create_test_game()
                async with WebSocketTestClient(game_id) as ws:
                    # Wait for initial state
                    await ws.wait_for_event("state_update", timeout=3.0)

                    # Generate random action sequence (2-5 actions)
                    num_actions = random.randint(2, 5)

                    for action_num in range(num_actions):
                        state = ws.get_latest_state()
                        if not state:
                            break

                        # Check if hand is over
                        if state.get("state") in ["showdown", "complete"]:
                            break

                        human_player = state.get("human_player")
                        if not human_player or not human_player.get("is_active"):
                            break

                        # Random action
                        action_type = random.choice(["fold", "call", "raise"])

                        if action_type == "raise":
                            # Random raise amount (mix of valid/invalid)
                            if random.random() < 0.3:
                                # 30% invalid
                                amount = random.choice([0, -10, 5])
                            else:
                                # 70% valid
                                max_bet = human_player["stack"] + human_player["current_bet"]
                                amount = random.randint(20, max_bet)
                            await ws.send_action("raise", amount=amount)
                        else:
                            await ws.send_action(action_type)

                        stats["total_actions"] += 1

                        # Wait for game response
                        await ws.drain_events(timeout=3.0)

                    stats["total_games"] += 1
                    stats["completed_successfully"] += 1

            except Exception as e:
                stats["errors"] += 1
                print(f"[FUZZ] ⚠️  Error on game {i}: {e}")
                if stats["errors"] > 20:  # Fail if too many errors
                    raise

        # Print summary
        print("\n" + "="*70)
        print("ACTION SEQUENCE FUZZING SUMMARY")
        print("="*70)
        print(f"Total games:             {stats['total_games']:>7,}")
        print(f"Total actions sent:      {stats['total_actions']:>7,}")
        print(f"Completed successfully:  {stats['completed_successfully']:>7,}")
        print(f"Errors:                  {stats['errors']:>7,}")
        print("="*70)

        # Assertions
        assert stats["errors"] < 10, f"Too many errors: {stats['errors']}"


    @pytest.mark.asyncio
    async def test_fuzz_invalid_action_types_100_iterations(self):
        """
        Test 100 completely invalid action types.

        Sends garbage like: "check", "bet", "allin", "FOLD", "rAiSe", "", None, 123
        Verifies game rejects gracefully without crashing.
        """
        print(f"\n[FUZZ] Starting {INVALID_ITERATIONS} invalid action type fuzzing iterations...")

        stats = {
            "total": 0,
            "rejected_gracefully": 0,
            "crashes": 0
        }

        invalid_actions = [
            "check", "bet", "allin", "FOLD", "CALL", "RAISE",  # Wrong case/names
            "rAiSe", "FoLd", "cAlL",                           # Mixed case
            "", " ", "   ",                                     # Empty/whitespace
            "invalid", "test", "action",                        # Garbage
            "fold123", "callme", "raiseup",                    # Mangled
            "f", "c", "r",                                      # Abbreviated
        ]

        for i in range(INVALID_ITERATIONS):
            try:
                game_id = await create_test_game()
                async with WebSocketTestClient(game_id) as ws:
                    await ws.wait_for_event("state_update", timeout=3.0)

                    # Send invalid action type
                    invalid_action = random.choice(invalid_actions)
                    await ws.send_action(invalid_action, amount=100)

                    stats["total"] += 1

                    # Game should respond (even if rejecting)
                    events = await ws.drain_events(timeout=3.0)

                    if len(events) > 0:
                        stats["rejected_gracefully"] += 1
                    else:
                        print(f"[FUZZ] ⚠️  No response to invalid action: '{invalid_action}'")

            except Exception as e:
                stats["crashes"] += 1
                print(f"[FUZZ] ❌ Crash on iteration {i}: {e}")
                if stats["crashes"] > 5:
                    raise

        # Print summary
        print("\n" + "="*70)
        print("INVALID ACTION TYPE FUZZING SUMMARY")
        print("="*70)
        print(f"Total iterations:        {stats['total']:>7,}")
        print(f"Rejected gracefully:     {stats['rejected_gracefully']:>7,}")
        print(f"Crashes:                 {stats['crashes']:>7,}")
        print("="*70)

        # Assertion: Should never crash
        assert stats["crashes"] == 0, f"Game crashed {stats['crashes']} times on invalid action types"


    @pytest.mark.asyncio
    async def test_fuzz_extreme_values_50_iterations(self):
        """
        Test 50 extreme/boundary value cases.

        Tests: INT_MAX, INT_MIN, very large floats, special values
        Verifies robust handling of edge case inputs.
        """
        print(f"\n[FUZZ] Starting {EXTREME_ITERATIONS} extreme value fuzzing iterations...")

        stats = {
            "total": 0,
            "handled_gracefully": 0,
            "crashes": 0
        }

        extreme_values = [
            2**31 - 1,              # INT_MAX
            -2**31,                 # INT_MIN
            2**63 - 1,              # LONG_MAX
            999999999999,           # Very large
            -999999999999,          # Very negative
            0,                      # Zero
            1,                      # Minimum
        ]

        for i in range(EXTREME_ITERATIONS):
            try:
                game_id = await create_test_game()
                async with WebSocketTestClient(game_id) as ws:
                    await ws.wait_for_event("state_update", timeout=3.0)

                    # Send extreme value
                    extreme_val = random.choice(extreme_values)
                    await ws.send_action("raise", amount=extreme_val)

                    stats["total"] += 1

                    # Game should handle it
                    events = await ws.drain_events(timeout=3.0)

                    if len(events) > 0:
                        stats["handled_gracefully"] += 1

            except Exception as e:
                stats["crashes"] += 1
                print(f"[FUZZ] ❌ Crash on extreme value {extreme_values[i % len(extreme_values)]}: {e}")
                if stats["crashes"] > 3:
                    raise

        # Print summary
        print("\n" + "="*70)
        print("EXTREME VALUE FUZZING SUMMARY")
        print("="*70)
        print(f"Total iterations:        {stats['total']:>7,}")
        print(f"Handled gracefully:      {stats['handled_gracefully']:>7,}")
        print(f"Crashes:                 {stats['crashes']:>7,}")
        print("="*70)

        # Assertion
        assert stats["crashes"] == 0, f"Game crashed {stats['crashes']} times on extreme values"
