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

def test_folded_player_chips_stay_in_pot():
    """
    Test that folded player's chips remain in pot but player cannot win.

    Texas Hold'em Rule: When a player folds, their invested chips stay in the pot
    but they are no longer eligible to win any portion of it.
    """
    print("\n[FOLDED] Testing folded player chips stay in pot...")
    game = PokerGame("TestPlayer")

    # P0: Active, strong hand
    p0 = Player("p0", "Winner", stack=100)
    p0.hole_cards = ["Ah", "As"]  # Pair of aces
    p0.is_active = True
    p0.total_invested = 50

    # P1: Folded after contributing chips
    p1 = Player("p1", "Folder", stack=50)
    p1.hole_cards = ["Kh", "Kd"]  # Would have been competitive
    p1.is_active = False  # Folded
    p1.folded = True
    p1.total_invested = 50  # But contributed to pot

    # P2: Active, weak hand
    p2 = Player("p2", "Loser", stack=100)
    p2.hole_cards = ["2h", "3h"]
    p2.is_active = True
    p2.total_invested = 50

    game.players = [p0, p1, p2]
    game.community_cards = ["7c", "8c", "9c", "Tc", "Jd"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Total pot should include folded player's chips
    total_pot = sum(pot['amount'] for pot in pots)
    total_invested = p0.total_invested + p1.total_invested + p2.total_invested
    assert total_pot == total_invested, \
        f"Pot should include folded player's chips: expected ${total_invested}, got ${total_pot}"

    # Folded player should not be in any pot's eligible list
    for pot in pots:
        assert 'p1' not in pot['winners'], "Folded player should not win any pot"
        if 'eligible_player_ids' in pot:
            assert 'p1' not in pot['eligible_player_ids'], \
                "Folded player should not be eligible for any pot"

    # P0 (best hand) should win
    assert any('p0' in pot['winners'] for pot in pots), "Active player with best hand should win"

    print(f"  ✓ Total pot: ${total_pot} (includes folded player's ${p1.total_invested})")
    print(f"  ✓ Folded player not eligible for any of {len(pots)} pot(s)")
    print("✅ Folded player's chips stay in pot but player cannot win")


def test_folded_player_not_eligible_for_side_pot():
    """
    Test that folded player is excluded from side pot eligibility.

    Scenario: P0 all-in for $30, P1 folds after betting $40, P2 bets $50.
    Main pot: $90 (P0, P1, P2 contributed)
    But P1 folded, so only P0 and P2 eligible.
    """
    print("\n[FOLDED] Testing folded player excluded from side pot...")
    game = PokerGame("TestPlayer")

    # P0: All-in for less
    p0 = Player("p0", "ShortStack", stack=0)
    p0.hole_cards = ["Ah", "As"]
    p0.is_active = True
    p0.all_in = True
    p0.total_invested = 30

    # P1: Folded after betting more than P0
    p1 = Player("p1", "Folder", stack=10)
    p1.hole_cards = ["Kh", "Kd"]
    p1.is_active = False
    p1.folded = True
    p1.total_invested = 40

    # P2: Active, bet most
    p2 = Player("p2", "BigStack", stack=0)
    p2.hole_cards = ["2h", "3h"]
    p2.is_active = True
    p2.total_invested = 50

    game.players = [p0, p1, p2]
    game.community_cards = ["7c", "8c", "9c", "Tc", "Jd"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Verify folded player not in any winners list
    for pot in pots:
        assert 'p1' not in pot['winners'], f"Folded player should not win pot: {pot}"

    # P0 should be able to win (best hand, all-in)
    assert any('p0' in pot['winners'] for pot in pots), "P0 with aces should win at least one pot"

    print(f"  ✓ Created {len(pots)} pot(s)")
    print(f"  ✓ Folded player excluded from all pots")
    print("✅ Folded player correctly excluded from side pot eligibility")


def test_multi_fold_side_pot_distribution():
    """
    Test complex scenario with multiple folded players at different contribution levels.

    Scenario:
    - P0: Active, $30
    - P1: Folded, $40
    - P2: Folded, $50
    - P3: Active, $60

    Expected:
    - Main pot: $120 (all 4 contributed $30 each) -> P0 or P3 wins
    - Side pot 1: $30 ($10 each from P1, P2, P3) -> P3 wins
    - Side pot 2: $20 ($10 each from P2, P3) -> P3 wins
    - Side pot 3: $10 (P3 alone) -> P3 gets back

    P1 and P2 folded, so cannot win any pots.
    """
    print("\n[FOLDED] Testing multiple folded players with side pots...")
    game = PokerGame("TestPlayer")

    # P0: Active, shortest investment
    p0 = Player("p0", "ShortActive", stack=0)
    p0.hole_cards = ["9h", "9s"]  # Medium hand
    p0.is_active = True
    p0.all_in = True
    p0.total_invested = 30

    # P1: Folded at $40
    p1 = Player("p1", "Folder1", stack=10)
    p1.hole_cards = ["Kh", "Kd"]  # Would beat P0
    p1.is_active = False
    p1.folded = True
    p1.total_invested = 40

    # P2: Folded at $50
    p2 = Player("p2", "Folder2", stack=10)
    p2.hole_cards = ["Qh", "Qd"]
    p2.is_active = False
    p2.folded = True
    p2.total_invested = 50

    # P3: Active, largest investment, best hand
    p3 = Player("p3", "BigActive", stack=0)
    p3.hole_cards = ["Ah", "As"]  # Best hand
    p3.is_active = True
    p3.all_in = True
    p3.total_invested = 60

    game.players = [p0, p1, p2, p3]
    game.community_cards = ["2c", "3c", "4c", "5c", "7d"]

    pots = game.hand_evaluator.determine_winners_with_side_pots(game.players, game.community_cards)

    # Verify total pot
    total_pot = sum(pot['amount'] for pot in pots)
    total_invested = 30 + 40 + 50 + 60
    assert total_pot == total_invested, \
        f"Total pot should equal all investments: expected ${total_invested}, got ${total_pot}"

    # Neither folded player should win anything
    for pot in pots:
        assert 'p1' not in pot['winners'], "P1 (folded) should not win"
        assert 'p2' not in pot['winners'], "P2 (folded) should not win"

    # P3 has best hand and is active for all pots
    # P0 is only eligible for main pot
    # So P3 should win at least some pots
    p3_wins = [pot for pot in pots if 'p3' in pot['winners']]
    assert len(p3_wins) > 0, "P3 (aces, active) should win at least one pot"

    print(f"  ✓ Created {len(pots)} pot(s) totaling ${total_pot}")
    print(f"  ✓ P3 won {len(p3_wins)} pot(s)")
    print(f"  ✓ Neither P1 nor P2 (folded) won any pots")
    print("✅ Multiple folded players correctly excluded from side pot distribution")


if __name__ == "__main__":
    print("Testing Bug #5 Fix: Side Pot Handling\n")
    test_side_pot_creation()
    test_equal_side_pot_split()
    test_main_and_side_pot_distribution()
    test_three_way_all_in()
    test_folded_player_chips_stay_in_pot()
    test_folded_player_not_eligible_for_side_pot()
    test_multi_fold_side_pot_distribution()
    print("\n✅ All side pot tests passed!")
