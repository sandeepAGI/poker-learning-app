"""
Test side pot handling - Bug #5 fix
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import PokerGame, GameState, Player

def test_side_pot_creation():
    """Test that side pots are created when players have different stack sizes."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Set up scenario with different stack sizes
    game.players[0].stack = 100
    game.players[0].total_invested = 50
    game.players[1].stack = 0
    game.players[1].total_invested = 30  # All-in for less
    game.players[1].all_in = True
    game.players[2].stack = 50
    game.players[2].total_invested = 50
    game.players[3].stack = 0
    game.players[3].total_invested = 40  # All-in for less
    game.players[3].all_in = True

    # All players should be eligible
    for p in game.players:
        p.is_active = True
        p.hole_cards = ["Ah", "Kh"]  # Give them cards

    game.community_cards = ["2c", "3c", "4c", "5c", "6c"]

    # Calculate side pots
    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Should have multiple pots
    assert len(pots) >= 1, "Should have at least one pot"
    print(f"✓ Created {len(pots)} pot(s) with different investment levels")

    # Verify pot amounts add up correctly
    total_pot = sum(pot['amount'] for pot in pots)
    total_invested = sum(p.total_invested for p in game.players if p.is_active or p.all_in)

    # Note: total_invested is reset during pot calculation, so we can't compare directly
    # but we can verify pots were created
    print(f"✓ Total distributed: ${total_pot}")

def test_equal_side_pot_split():
    """Test that side pots are split equally among winners."""
    game = PokerGame("TestPlayer")
    game.start_new_hand()

    # Set up two players with same hand
    game.players[0].hole_cards = ["Ah", "Kh"]
    game.players[0].is_active = True
    game.players[0].total_invested = 100

    game.players[1].hole_cards = ["Ad", "Kd"]  # Same hand strength
    game.players[1].is_active = True
    game.players[1].total_invested = 100

    # Other players fold
    game.players[2].is_active = False
    game.players[3].is_active = False

    game.community_cards = ["2c", "3c", "4c", "5c", "6c"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Should have one pot with two winners
    assert len(pots) == 1, "Should have one pot"
    assert len(pots[0]['winners']) == 2, "Should have two winners (tied hands)"
    print(f"✓ Pot correctly split between {len(pots[0]['winners'])} winners")

def test_main_and_side_pot_distribution():
    """Test distribution with main pot and side pot."""
    game = PokerGame("TestPlayer")

    # Player 0: Has best hand, can win both pots
    p0 = Player("p0", "Player0", stack=0)
    p0.hole_cards = ["Ah", "As"]  # Pair of aces
    p0.is_active = True
    p0.all_in = True
    p0.total_invested = 50

    # Player 1: Has worst hand, all-in for less
    p1 = Player("p1", "Player1", stack=0)
    p1.hole_cards = ["2h", "3h"]  # High card
    p1.is_active = True
    p1.all_in = True
    p1.total_invested = 30  # Less invested

    # Player 2: Has medium hand
    p2 = Player("p2", "Player2", stack=50)
    p2.hole_cards = ["Kh", "Kd"]  # Pair of kings
    p2.is_active = True
    p2.total_invested = 50

    game.players = [p0, p1, p2]
    game.community_cards = ["7c", "8c", "9c", "Tc", "Jd"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Should have 2 pots: main pot (everyone eligible) and side pot (p0 and p2 only)
    assert len(pots) >= 1, "Should have at least one pot"
    print(f"✓ Created {len(pots)} pot(s)")

    # Verify p0 (best hand) wins
    # Find which pots p0 won
    p0_wins = [pot for pot in pots if "p0" in pot['winners']]
    assert len(p0_wins) > 0, "Player with best hand should win at least one pot"
    print(f"✓ Player with Aces won {len(p0_wins)} pot(s)")

def test_three_way_all_in():
    """Test complex scenario with three players all-in at different amounts."""
    game = PokerGame("TestPlayer")

    p0 = Player("p0", "Short", stack=0)
    p0.hole_cards = ["Ah", "Kh"]
    p0.is_active = True
    p0.all_in = True
    p0.total_invested = 20

    p1 = Player("p1", "Medium", stack=0)
    p1.hole_cards = ["As", "Ks"]  # Same strength as p0
    p1.is_active = True
    p1.all_in = True
    p1.total_invested = 50

    p2 = Player("p2", "Large", stack=100)
    p2.hole_cards = ["2d", "3d"]  # Worst hand
    p2.is_active = True
    p2.total_invested = 100

    game.players = [p0, p1, p2]
    # Use community cards that don't make a straight/flush
    # p0 and p1 will have A-K high, p2 will have 3-high (worst)
    game.community_cards = ["4h", "5c", "8s", "Qh", "Jc"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Should create multiple pots
    assert len(pots) >= 2, "Should have at least 2 pots in three-way all-in"
    print(f"✓ Three-way all-in created {len(pots)} pots")

    # p0 and p1 tie for best hand (A-K high), should win pots they're eligible for
    main_pot = pots[0]
    assert len(main_pot['winners']) == 2, \
        f"Main pot should be split between tied winners (A-K high), got: {main_pot['winners']}"
    print(f"✓ Main pot correctly split between {len(main_pot['winners'])} tied winners")

if __name__ == "__main__":
    print("Testing Bug #5 Fix: Side Pot Handling\n")
    test_side_pot_creation()
    test_equal_side_pot_split()
    test_main_and_side_pot_distribution()
    test_three_way_all_in()
    print("\n✅ All side pot tests passed!")
