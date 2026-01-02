"""Validate community cards are dealt in 3-1-1 order without duplication."""
from game.poker_engine import PokerGame


def test_community_cards_dealt_in_order():
    game = PokerGame("Human", ai_count=3)
    game.start_new_hand(process_ai=False)

    # Capture deck state after hole cards dealt
    deck_snapshot = list(game.deck_manager.deck)

    # Force advance logic to think betting rounds are complete
    game._betting_round_complete = lambda: True  # type: ignore

    # Advance to flop/turn/river
    game._advance_state_core(process_ai=False)  # → FLOP
    assert game.community_cards == deck_snapshot[:3]

    game._advance_state_core(process_ai=False)  # → TURN
    assert game.community_cards[3] == deck_snapshot[3]

    game._advance_state_core(process_ai=False)  # → RIVER
    assert game.community_cards[4] == deck_snapshot[4]

    # Ensure no duplicates among hole cards + community cards
    seen = set()
    for player in game.players:
        for card in player.hole_cards:
            assert card not in seen, "Hole cards should be unique"
            seen.add(card)
    for card in game.community_cards:
        assert card not in seen, "Community cards should not duplicate hole cards"
        seen.add(card)
