from ai.strategies.bluffer import BlufferStrategy
from ai.strategies.conservative import ConservativeStrategy
from ai.strategies.probability_based import ProbabilityBasedStrategy
from ai.strategies.risk_taker import RiskTakerStrategy

def test_ai_decisions(spr, hand_score):
    """Manually test AI decisions based on given SPR and hand score."""
    
    bluffer_ai = BlufferStrategy()
    conservative_ai = ConservativeStrategy()
    probability_ai = ProbabilityBasedStrategy()
    risk_taker_ai = RiskTakerStrategy()
    
    game_state = {"current_bet": 100, "community_cards": ["Ah", "Kd", "3c"]}
    deck = ["7s", "Jd", "2d", "9h", "Qh"] * 3
    pot_size = 500

    print(f"\n=== Manual Test for SPR={spr}, Hand Score={hand_score} ===")

    # Bluffer AI
    decision_bluffer = bluffer_ai.make_decision(["2c", "7d"], game_state, deck, pot_size, spr)
    print(f"Bluffer AI Decision: {decision_bluffer}")

    # Conservative AI
    decision_conservative = conservative_ai.make_decision(["As", "Ks"], game_state, deck, pot_size, spr)
    print(f"Conservative AI Decision: {decision_conservative}")

    # Probability-Based AI
    decision_probability = probability_ai.make_decision(["9h", "8h"], game_state, deck, pot_size, spr)
    print(f"Probability-Based AI Decision: {decision_probability}")

    # Risk-Taker AI
    decision_risk_taker = risk_taker_ai.make_decision(["3c", "7d"], game_state, deck, pot_size, spr)
    print(f"Risk-Taker AI Decision: {decision_risk_taker}")

# Example manual tests:
test_ai_decisions(0.0, 3000)  # All-in case
test_ai_decisions(2.0, 4000)  # Low SPR case
test_ai_decisions(4.0, 6000)  # Medium SPR case
test_ai_decisions(7.0, 4500)  # High SPR case

