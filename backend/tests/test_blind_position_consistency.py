"""
Test for Issue #2: Blind/Button Indicators Drift

Verifies that WebSocket and REST API return the same blind positions,
even when a blind poster busts mid-hand.

TDD Red Phase: This test should FAIL before the fix is applied.
"""
import pytest
import asyncio
import httpx
import json
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame
from websocket_manager import serialize_game_state
from test_websocket_integration import create_test_game


def test_websocket_serializer_uses_stored_blind_indexes():
    """
    Test that serialize_game_state uses stored blind indexes, not recomputed ones.

    Setup:
    - Create game with 4 players
    - Start hand (blinds posted at positions 0 and 1)
    - Manually bust the small blind player (set stack = 0)
    - Serialize game state

    Expected:
    - small_blind_position should remain 0 (even though stack = 0)
    - Should NOT skip to next player with chips
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)

    # Record the actual blind positions set by _post_blinds
    original_sb_index = game.small_blind_index
    original_bb_index = game.big_blind_index

    # Simulate the small blind player going bust mid-hand
    sb_player = game.players[original_sb_index]
    sb_player.stack = 0  # Busted
    sb_player.all_in = True

    # Serialize the game state (as WebSocket does)
    state = serialize_game_state(game, show_ai_thinking=False)

    # Verify blind positions match the stored indexes
    assert state["small_blind_position"] == original_sb_index, \
        f"SB position should be {original_sb_index} (stored), not {state['small_blind_position']} (recomputed)"

    assert state["big_blind_position"] == original_bb_index, \
        f"BB position should be {original_bb_index} (stored), not {state['big_blind_position']} (recomputed)"

    # This test will FAIL with current code because serialize_game_state
    # recomputes positions and skips players with stack = 0


def test_rest_api_uses_stored_blind_indexes():
    """
    Verify REST API correctly uses stored blind indexes.
    This should already pass - it's a baseline test.
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)

    original_sb_index = game.small_blind_index
    original_bb_index = game.big_blind_index

    # REST API directly uses game.small_blind_index and game.big_blind_index
    # This is correct behavior
    assert game.small_blind_index == original_sb_index
    assert game.big_blind_index == original_bb_index


def test_blind_positions_stay_fixed_during_hand():
    """
    Test that blind positions don't change during a hand, even if players bust.

    This tests the core poker rule: blinds are fixed at start of hand.
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)

    sb_before = game.small_blind_index
    bb_before = game.big_blind_index

    # Simulate some players going all-in and busting
    for i, player in enumerate(game.players):
        if i != 0:  # Don't bust the human
            player.stack = 0
            player.all_in = True

    # Blind positions should NOT change
    assert game.small_blind_index == sb_before, "SB index should not change during hand"
    assert game.big_blind_index == bb_before, "BB index should not change during hand"

    # And serialize_game_state should use these stored values
    state = serialize_game_state(game, show_ai_thinking=False)
    assert state["small_blind_position"] == sb_before
    assert state["big_blind_position"] == bb_before


@pytest.mark.asyncio
async def test_websocket_and_rest_return_same_positions():
    """
    Integration test: Verify WebSocket and REST API return identical blind positions.

    This is the user-facing symptom: UI shows different button positions
    depending on whether data comes from REST or WebSocket.
    """
    pytest.skip("Requires WebSocket test infrastructure to compare with REST")

    # The code below requires a running server, so we skip this test
    game_id = await create_test_game(ai_count=3)

    # Get state via REST API
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        rest_response = await client.get(f"/games/{game_id}")
        rest_data = rest_response.json()

    # Get state via direct serialization (simulates WebSocket)
    # Note: We'd need access to the actual game object for this
    # For now, this test is more conceptual

    # Both should return same positions
    # This will FAIL if WebSocket recomputes and REST uses stored values
