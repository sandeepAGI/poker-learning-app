"""
Tests for AI personality expansion (Phase 5).

Validates that all 6 AI personalities work correctly and that random
assignment produces variety across different games.
"""

import pytest
from game.poker_engine import PokerGame, AIStrategy


def test_all_six_personalities_work():
    """Verify all 6 personalities make valid decisions."""
    personalities = [
        "Conservative",
        "Aggressive",
        "Mathematical",
        "Loose-Passive",
        "Tight-Aggressive",
        "Maniac"
    ]

    for personality in personalities:
        decision = AIStrategy.make_decision_with_reasoning(
            personality=personality,
            hole_cards=["Ah", "Kh"],
            community_cards=[],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )

        # Verify decision is valid
        assert decision.action in ["fold", "call", "raise"], \
            f"{personality} returned invalid action: {decision.action}"
        assert len(decision.reasoning) > 0, \
            f"{personality} provided no reasoning"
        assert 0 <= decision.confidence <= 1, \
            f"{personality} confidence out of range: {decision.confidence}"
        assert decision.hand_strength >= 0, \
            f"{personality} hand_strength is negative"


def test_random_personality_assignment_no_duplicates():
    """Verify random assignment doesn't create duplicates."""
    game = PokerGame(human_player_name="Test", ai_count=5)

    # Get AI personalities
    ai_personalities = [p.personality for p in game.players if not p.is_human]

    assert len(ai_personalities) == 5, \
        f"Expected 5 AI players, got {len(ai_personalities)}"
    assert len(set(ai_personalities)) == 5, \
        f"Duplicate personalities found: {ai_personalities}"


def test_personality_variety_across_games():
    """Verify different games get different personality mixes."""
    personalities_sets = []

    for _ in range(10):
        game = PokerGame(human_player_name="Test", ai_count=3)
        ai_personalities = tuple(sorted([p.personality for p in game.players if not p.is_human]))
        personalities_sets.append(ai_personalities)

    # At least 3 different combinations in 10 games
    unique_combinations = len(set(personalities_sets))
    assert unique_combinations >= 3, \
        f"Only {unique_combinations} unique personality combinations in 10 games (expected >= 3)"


def test_loose_passive_personality():
    """Verify Loose-Passive calls frequently and rarely raises."""
    # Test with marginal hand
    decision = AIStrategy.make_decision_with_reasoning(
        personality="Loose-Passive",
        hole_cards=["9h", "8h"],  # Marginal hand
        community_cards=["Kd", "7c", "2s"],
        current_bet=20,
        pot_size=50,
        player_stack=1000,
        player_bet=0,
        big_blind=10
    )

    # Loose-Passive should call or fold (rarely raise)
    assert decision.action in ["call", "fold"], \
        f"Loose-Passive should rarely raise, got: {decision.action}"

    # Most likely call with this situation
    # (may fold if bet is too expensive, which is fine)


def test_tight_aggressive_personality():
    """Verify Tight-Aggressive folds marginal hands but raises premium hands."""
    # Test 1: Marginal hand - should fold
    decision1 = AIStrategy.make_decision_with_reasoning(
        personality="Tight-Aggressive",
        hole_cards=["9h", "8h"],  # Marginal hand
        community_cards=["Kd", "7c", "2s"],
        current_bet=20,
        pot_size=50,
        player_stack=1000,
        player_bet=0,
        big_blind=10
    )

    assert decision1.action == "fold", \
        f"TAG should fold marginal hands, got: {decision1.action}"

    # Test 2: Premium hand - should raise
    decision2 = AIStrategy.make_decision_with_reasoning(
        personality="Tight-Aggressive",
        hole_cards=["Ah", "As"],  # Premium hand
        community_cards=["Ad", "Kh", "Ks"],  # Full house
        current_bet=20,
        pot_size=50,
        player_stack=1000,
        player_bet=0,
        big_blind=10
    )

    assert decision2.action == "raise", \
        f"TAG should raise premium hands, got: {decision2.action}"


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_maniac_personality():
    """Verify Maniac is hyper-aggressive and bluffs frequently.

    FLAKY: This test checks probabilistic behavior (70% raise rate) with only 10 trials.
    Statistical probability of false negative: ~4.7% (binomial: P(X<=4 | n=10, p=0.7)).
    Will retry up to 2 times if it fails due to randomness.
    """
    # Run 10 decisions with weak hands
    raise_count = 0

    for _ in range(10):
        decision = AIStrategy.make_decision_with_reasoning(
            personality="Maniac",
            hole_cards=["7h", "2d"],  # Weak hand
            community_cards=["Kd", "Qc", "Js"],
            current_bet=20,
            pot_size=50,
            player_stack=1000,
            player_bet=0,
            big_blind=10
        )

        if decision.action == "raise":
            raise_count += 1

    # Maniac should raise at least 50% of the time even with weak hands (70% bluff rate)
    assert raise_count >= 5, \
        f"Maniac should be hyper-aggressive, only raised {raise_count}/10 times"


def test_ai_name_pool_supports_five_players():
    """Verify AI name pool has enough names for 5 AI opponents."""
    game = PokerGame(human_player_name="Test", ai_count=5)

    ai_names = [p.name for p in game.players if not p.is_human]

    assert len(ai_names) == 5, \
        f"Expected 5 AI names, got {len(ai_names)}"
    assert len(set(ai_names)) == 5, \
        f"Duplicate AI names found: {ai_names}"


def test_all_personalities_with_different_scenarios():
    """Verify all personalities handle different game scenarios."""
    scenarios = [
        # (hole_cards, community_cards, current_bet, pot_size, description)
        (["Ah", "As"], ["Ad", "Kh", "Ks"], 20, 50, "premium_hand"),
        (["9h", "8h"], ["Kd", "7c", "2s"], 20, 50, "marginal_hand"),
        (["2h", "7d"], ["Kd", "Qc", "Js"], 20, 50, "weak_hand"),
        (["Th", "9h"], ["Jh", "Qh", "Kh"], 20, 50, "strong_draw"),
    ]

    personalities = [
        "Conservative", "Aggressive", "Mathematical",
        "Loose-Passive", "Tight-Aggressive", "Maniac"
    ]

    for personality in personalities:
        for hole_cards, community_cards, bet, pot, desc in scenarios:
            decision = AIStrategy.make_decision_with_reasoning(
                personality=personality,
                hole_cards=hole_cards,
                community_cards=community_cards,
                current_bet=bet,
                pot_size=pot,
                player_stack=1000,
                player_bet=0,
                big_blind=10
            )

            # Verify basic validity
            assert decision.action in ["fold", "call", "raise"], \
                f"{personality} with {desc}: invalid action {decision.action}"
            assert decision.amount >= 0, \
                f"{personality} with {desc}: negative amount {decision.amount}"
            assert len(decision.reasoning) > 0, \
                f"{personality} with {desc}: no reasoning provided"
