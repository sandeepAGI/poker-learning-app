"""
Test for Issue #3: AI Reasoning Sidebar Data Loss

Verifies that AI decisions are uniquely identifiable even when reasoning is stripped,
and that full decision data is always available server-side.

TDD Red Phase: These tests should FAIL before the fix is applied.
"""
import pytest
from game.poker_engine import PokerGame, AIDecision
from websocket_manager import serialize_game_state


def test_ai_decisions_have_unique_identifiers():
    """
    Test that AIDecision dataclass has decision_id field.

    This allows deduplication without relying on reasoning text.
    """
    # Test that the dataclass has the field
    from dataclasses import fields
    from game.poker_engine import AIDecision

    field_names = [f.name for f in fields(AIDecision)]
    assert 'decision_id' in field_names, "AIDecision should have decision_id field"

    # Test that decisions created programmatically get unique IDs
    # (actual AI decisions are tested in other test functions)
    import uuid
    decision1 = AIDecision(
        action="call", amount=10, reasoning="Test", hand_strength=0.6,
        pot_odds=0.3, confidence=0.8, spr=5.0, decision_id=str(uuid.uuid4())
    )
    decision2 = AIDecision(
        action="fold", amount=0, reasoning="Test", hand_strength=0.2,
        pot_odds=0.1, confidence=0.9, spr=3.0, decision_id=str(uuid.uuid4())
    )

    assert decision1.decision_id != decision2.decision_id, "Decision IDs should be unique"
    assert decision1.decision_id != "", "Decision ID should not be empty"
    assert decision2.decision_id != "", "Decision ID should not be empty"


def test_serialize_always_includes_decision_ids():
    """
    Test that serialized decisions always include decision IDs,
    even when show_ai_thinking=False.

    This allows frontend to deduplicate reliably.
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=True)  # Let AI make some decisions

    # Serialize with AI thinking OFF
    state_hidden = serialize_game_state(game, show_ai_thinking=False)

    # Even with thinking hidden, decision IDs should be present
    for player_id, decision_data in state_hidden["last_ai_decisions"].items():
        assert "decision_id" in decision_data, \
            f"Decision for {player_id} should have decision_id even when reasoning is hidden"
        assert decision_data["decision_id"] is not None, \
            f"Decision ID should not be None"


def test_full_decision_data_preserved_server_side():
    """
    Test that full AI decision data is preserved in game.last_ai_decisions,
    even when serialized output is filtered.

    This ensures data can be retrieved later when user toggles AI thinking on.
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=True)

    # Record full decisions stored server-side
    server_decisions = game.last_ai_decisions.copy()

    # Serialize with thinking OFF (strips reasoning)
    state_hidden = serialize_game_state(game, show_ai_thinking=False)

    # Server-side decisions should still have full data
    for player_id, decision in server_decisions.items():
        assert decision.reasoning is not None, \
            f"Server-side decision for {player_id} should have reasoning"
        assert decision.hand_strength is not None, \
            f"Server-side decision for {player_id} should have hand_strength"
        assert decision.pot_odds is not None, \
            f"Server-side decision for {player_id} should have pot_odds"

    # But serialized output should be filtered
    for player_id, decision_data in state_hidden["last_ai_decisions"].items():
        assert "reasoning" not in decision_data or decision_data["reasoning"] is None, \
            "Serialized decision should not have reasoning when show_ai_thinking=False"


def test_toggle_ai_thinking_preserves_data():
    """
    Integration test: Verify that toggling show_ai_thinking doesn't lose data.

    This simulates the user experience:
    1. Start with AI thinking hidden
    2. AI makes decisions (reasoning stripped from broadcasts)
    3. User toggles AI thinking ON
    4. Previously hidden data should now be visible
    """
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=True)

    # First broadcast: AI thinking OFF
    state1 = serialize_game_state(game, show_ai_thinking=False)
    decision_ids_hidden = []
    for player_id, decision_data in state1["last_ai_decisions"].items():
        if "decision_id" in decision_data:
            decision_ids_hidden.append(decision_data["decision_id"])

    # Second broadcast: AI thinking ON
    state2 = serialize_game_state(game, show_ai_thinking=True)
    decision_ids_shown = []
    for player_id, decision_data in state2["last_ai_decisions"].items():
        if "decision_id" in decision_data:
            decision_ids_shown.append(decision_data["decision_id"])
        # Data should now be present
        assert "reasoning" in decision_data, "Reasoning should be present when AI thinking is ON"
        assert decision_data["reasoning"] is not None, "Reasoning should not be None"

    # Same decisions should be present in both states
    assert set(decision_ids_hidden) == set(decision_ids_shown), \
        "Same decisions should be present regardless of show_ai_thinking flag"


def test_duplicate_decisions_have_different_ids():
    """
    Test that repeated actions from the same player get unique IDs.

    Example: Player folds twice in different hands - should have different decision IDs.
    """
    game = PokerGame("Human", ai_count=3)

    # Hand 1
    game.start_new_hand(process_ai=True)
    state1 = serialize_game_state(game, show_ai_thinking=True)
    decision_ids_hand1 = {
        pid: data.get("decision_id")
        for pid, data in state1["last_ai_decisions"].items()
    }

    # Hand 2
    game.start_new_hand(process_ai=True)
    state2 = serialize_game_state(game, show_ai_thinking=True)
    decision_ids_hand2 = {
        pid: data.get("decision_id")
        for pid, data in state2["last_ai_decisions"].items()
    }

    # Decision IDs should be different across hands
    for player_id in decision_ids_hand1.keys():
        if player_id in decision_ids_hand2:
            assert decision_ids_hand1[player_id] != decision_ids_hand2[player_id], \
                f"Decision IDs for {player_id} should differ across hands"
