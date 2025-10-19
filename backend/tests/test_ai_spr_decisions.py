"""
Test AI SPR (Stack-to-Pot Ratio) decision making - Phase 1.5
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import AIStrategy

def test_conservative_low_spr():
    """Conservative should be more willing to commit with low SPR."""
    print("\nTest: Conservative Low SPR")

    # Setup: pot=300, player_stack=200 (SPR = 0.67)
    # Hand: Two pair (hand_strength = 0.45)
    hole_cards = ["7h", "7d"]  # Pair (will map to hand_strength ~0.45 with community)
    community_cards = ["7c", "2h", "3s"]  # Gives three of a kind
    current_bet = 50
    pot_size = 300
    player_stack = 200
    player_bet = 0

    decision = AIStrategy.make_decision_with_reasoning(
        "Conservative", hole_cards, community_cards,
        current_bet, pot_size, player_stack, player_bet
    )

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")

    assert decision.spr < 1.0, f"Expected low SPR, got {decision.spr}"
    assert decision.action in ["raise", "call"], f"Expected raise/call with low SPR, got {decision.action}"
    assert "SPR" in decision.reasoning or decision.action == "raise", "Should mention SPR or raise"
    print("  ✓ Conservative commits with low SPR")

def test_conservative_high_spr():
    """Conservative should be tighter with high SPR."""
    print("\nTest: Conservative High SPR")

    # Setup: pot=50, player_stack=1000 (SPR = 20)
    # Hand: One pair (hand_strength = 0.25)
    hole_cards = ["8h", "8d"]  # Pair
    community_cards = ["2c", "3h", "4s"]  # No help
    current_bet = 10
    pot_size = 50
    player_stack = 1000
    player_bet = 0

    decision = AIStrategy.make_decision_with_reasoning(
        "Conservative", hole_cards, community_cards,
        current_bet, pot_size, player_stack, player_bet
    )

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")

    assert decision.spr > 10, f"Expected high SPR, got {decision.spr}"
    assert decision.action == "fold", f"Expected fold with high SPR + weak hand, got {decision.action}"
    assert "SPR" in decision.reasoning, "Should mention SPR in reasoning"
    print("  ✓ Conservative folds weak hands with high SPR")

def test_aggressive_low_spr():
    """Aggressive should push/fold with low SPR."""
    print("\nTest: Aggressive Low SPR")

    # Setup: pot=400, player_stack=300 (SPR = 0.75)
    # Hand: One pair (hand_strength = 0.25)
    hole_cards = ["9h", "9d"]  # Pair
    community_cards = ["2c", "3h", "4s"]
    current_bet = 100
    pot_size = 400
    player_stack = 300
    player_bet = 0

    decision = AIStrategy.make_decision_with_reasoning(
        "Aggressive", hole_cards, community_cards,
        current_bet, pot_size, player_stack, player_bet
    )

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")

    assert decision.spr < 1.0, f"Expected low SPR, got {decision.spr}"
    assert decision.action == "raise", f"Expected aggressive push with low SPR, got {decision.action}"
    assert decision.amount == player_stack, f"Expected all-in, got ${decision.amount}"
    assert "SPR" in decision.reasoning, "Should mention SPR in reasoning"
    print("  ✓ Aggressive pushes with low SPR")

def test_aggressive_high_spr_bluff():
    """Aggressive should bluff more with high SPR."""
    print("\nTest: Aggressive High SPR Bluffing")

    # Setup: pot=30, player_stack=900 (SPR = 30)
    # Hand: High card (hand_strength = 0.05)
    # Run multiple times to test bluff percentage
    hole_cards = ["2h", "3d"]  # High card
    community_cards = ["7c", "9h", "Ks"]
    current_bet = 5
    pot_size = 30
    player_stack = 900
    player_bet = 0

    actions = []
    for _ in range(20):  # Run 20 times to get distribution
        decision = AIStrategy.make_decision_with_reasoning(
            "Aggressive", hole_cards, community_cards,
            current_bet, pot_size, player_stack, player_bet
        )
        actions.append(decision.action)

    raises = actions.count("raise")
    folds = actions.count("fold")

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Actions over 20 trials: {raises} raises, {folds} folds")
    print(f"  Sample reasoning: {decision.reasoning}")

    assert decision.spr > 20, f"Expected high SPR, got {decision.spr}"
    assert raises > 0, "Expected some bluffs with high SPR"
    assert folds > 0, "Expected some folds too"
    print(f"  ✓ Aggressive bluffs {raises/20:.0%} of time with high SPR")

def test_mathematical_spr_pot_odds():
    """Mathematical should use both SPR and pot odds."""
    print("\nTest: Mathematical SPR + Pot Odds")

    # Setup: pot=100, player_stack=150 (SPR = 1.5)
    # Current bet=30, so call=30, pot odds = 30/(100+30) = 0.23
    # Hand: One pair (hand_strength = 0.25)
    hole_cards = ["Th", "Td"]  # Pair
    community_cards = ["2c", "5h", "8s"]
    current_bet = 30
    pot_size = 100
    player_stack = 150
    player_bet = 0

    decision = AIStrategy.make_decision_with_reasoning(
        "Mathematical", hole_cards, community_cards,
        current_bet, pot_size, player_stack, player_bet
    )

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Pot Odds: {decision.pot_odds:.2%}")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")

    assert decision.spr < 2.0, f"Expected low SPR, got {decision.spr}"
    assert decision.action == "call", f"Expected call with low SPR + decent odds, got {decision.action}"
    assert "SPR" in decision.reasoning or "EV" in decision.reasoning, "Should mention SPR or EV"
    print("  ✓ Mathematical uses SPR + pot odds for EV decision")

def test_mathematical_high_spr_fold():
    """Mathematical should fold marginal hands with high SPR + poor odds."""
    print("\nTest: Mathematical High SPR + Poor Odds")

    # Setup: pot=40, player_stack=800 (SPR = 20)
    # Current bet=25, so pot odds = 25/(40+25) = 0.38 (poor)
    # Hand: One pair (hand_strength = 0.25)
    hole_cards = ["Jh", "Jd"]  # Pair
    community_cards = ["2c", "5h", "8s"]
    current_bet = 25
    pot_size = 40
    player_stack = 800
    player_bet = 0

    decision = AIStrategy.make_decision_with_reasoning(
        "Mathematical", hole_cards, community_cards,
        current_bet, pot_size, player_stack, player_bet
    )

    print(f"  SPR: {decision.spr:.2f}")
    print(f"  Pot Odds: {decision.pot_odds:.2%}")
    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")

    assert decision.spr > 15, f"Expected high SPR, got {decision.spr}"
    assert decision.pot_odds > 0.35, f"Expected poor pot odds, got {decision.pot_odds}"
    assert decision.action == "fold", f"Expected fold with high SPR + poor odds, got {decision.action}"
    assert "SPR" in decision.reasoning or "EV" in decision.reasoning, "Should mention SPR or EV"
    print("  ✓ Mathematical folds with high SPR + poor pot odds")

def test_all_personalities_different_spr():
    """Verify different personalities make different SPR-based decisions."""
    print("\nTest: Personality Differences with SPR")

    # Same scenario for all: Medium SPR, marginal hand
    hole_cards = ["Qh", "Qd"]  # Pair
    community_cards = ["2c", "5h", "8s", "Kd"]  # Paired with overcard on board
    current_bet = 40
    pot_size = 120
    player_stack = 400  # SPR = 3.33
    player_bet = 0

    decisions = {}
    for personality in ["Conservative", "Aggressive", "Mathematical"]:
        decision = AIStrategy.make_decision_with_reasoning(
            personality, hole_cards, community_cards,
            current_bet, pot_size, player_stack, player_bet
        )
        decisions[personality] = decision
        print(f"  {personality}: {decision.action} - {decision.reasoning[:60]}...")

    # Check that SPR is calculated consistently
    sprs = [d.spr for d in decisions.values()]
    assert all(abs(spr - sprs[0]) < 0.1 for spr in sprs), "SPR should be consistent"

    # Check that at least one personality differs in action
    actions = [d.action for d in decisions.values()]
    assert len(set(actions)) >= 2 or any("SPR" in d.reasoning for d in decisions.values()), \
        "Personalities should differ in actions or mention SPR"

    print(f"  ✓ All personalities calculate SPR: {sprs[0]:.2f}")
    print(f"  ✓ Actions: {set(actions)}")

if __name__ == "__main__":
    print("="*60)
    print("PHASE 1.5 SPR TEST SUITE")
    print("="*60)

    test_conservative_low_spr()
    test_conservative_high_spr()
    test_aggressive_low_spr()
    test_aggressive_high_spr_bluff()
    test_mathematical_spr_pot_odds()
    test_mathematical_high_spr_fold()
    test_all_personalities_different_spr()

    print("\n" + "="*60)
    print("✅ ALL SPR TESTS PASSED!")
    print("="*60)
