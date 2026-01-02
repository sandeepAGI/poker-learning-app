"""Integration-style tests that award pots after multi-way all-ins."""
from game.poker_engine import PokerGame, GameState


def test_side_pot_awarding_three_players():
    game = PokerGame("Human", ai_count=2)
    game.start_new_hand(process_ai=False)
    game.qc_enabled = False

    human, ai1, ai2 = game.players

    # Force known hole cards and board
    human.hole_cards = ["Kc", "Ks"]
    ai1.hole_cards = ["3c", "4c"]
    ai2.hole_cards = ["Ad", "Jd"]
    game.community_cards = ["Kh", "Qd", "Qs", "2s", "7h"]

    # Simulate investments: ai1 all-in 40, human 100, ai2 150
    human.stack = 0
    human.current_bet = human.total_invested = 100
    human.all_in = True

    ai1.stack = 0
    ai1.current_bet = ai1.total_invested = 40
    ai1.all_in = True

    ai2.stack = 50  # 200 starting - 150 invested
    ai2.current_bet = ai2.total_invested = 150
    ai2.all_in = True

    game.pot = human.total_invested + ai1.total_invested + ai2.total_invested
    game.current_state = GameState.SHOWDOWN

    game._award_pot_at_showdown()

    # Main pot (120) + first side pot (120) should both go to human, last 50 to ai2
    assert human.stack == 240, f"Human should win 240, got {human.stack}"
    assert ai2.stack == 100, f"AI2 should get remaining 50 back, got {ai2.stack}"
    assert ai1.stack == 0, "Shortest stack lost and stays at zero"
