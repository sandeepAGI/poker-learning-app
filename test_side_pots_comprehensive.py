#!/usr/bin/env python3
"""
Comprehensive side pot testing (Issue #6).
Tests various all-in scenarios to ensure side pots work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame, GameState

def test_scenario_1_simple_all_in():
    """
    Scenario 1: One player all-in, others have more chips
    - Player: $100 (all-in)
    - AI-1: $1000
    - AI-2: $1000
    - AI-3: $1000

    Expected: Main pot = $400 (4 players × $100), Side pot = remaining
    """
    print("\n" + "="*70)
    print("SCENARIO 1: Simple All-In")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    # Set up stacks
    game.players[0].stack = 100  # Player
    game.players[1].stack = 1000  # AI-ce
    game.players[2].stack = 1000  # AI-ron
    game.players[3].stack = 1000  # AI-nstein

    # Recalculate total_chips for QC
    game.total_chips = sum(p.stack for p in game.players)

    print(f"\nInitial stacks:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Total: ${game.total_chips}")

    # Start hand
    game.start_new_hand()

    # Force everyone to call to showdown (simulate)
    # For testing, manually set investments
    game.players[0].total_invested = 100  # Player all-in
    game.players[0].all_in = True
    game.players[0].is_active = True
    game.players[1].total_invested = 200  # AI-ce
    game.players[1].is_active = True
    game.players[2].total_invested = 200  # AI-ron
    game.players[2].is_active = True
    game.players[3].total_invested = 200  # AI-nstein
    game.players[3].is_active = True

    # Calculate side pots
    pots = game.hand_evaluator.determine_winners_with_side_pots(
        game.players, game.community_cards
    )

    print(f"\nSide pot calculation:")
    total_invested = sum(p.total_invested for p in game.players)
    print(f"Total invested: ${total_invested}")
    print(f"Number of pots: {len(pots)}")

    for i, pot in enumerate(pots):
        print(f"\nPot {i+1} ({pot['type']}):")
        print(f"  Amount: ${pot['amount']}")
        print(f"  Eligible players: {pot['eligible_player_ids']}")
        print(f"  Winners: {pot['winners']}")

    # Verify
    assert len(pots) == 2, f"Expected 2 pots (main + side), got {len(pots)}"
    main_pot = pots[0]
    side_pot = pots[1]

    assert main_pot['amount'] == 400, f"Main pot should be $400, got ${main_pot['amount']}"
    assert len(main_pot['eligible_player_ids']) == 4, "All 4 players eligible for main pot"

    assert side_pot['amount'] == 300, f"Side pot should be $300, got ${side_pot['amount']}"
    assert len(side_pot['eligible_player_ids']) == 3, "Only 3 players eligible for side pot"

    print(f"\n✅ Scenario 1 PASSED")
    return True

def test_scenario_2_multiple_all_ins():
    """
    Scenario 2: Multiple players all-in with different stack sizes
    - Player: $50 (all-in)
    - AI-1: $100 (all-in)
    - AI-2: $200 (all-in)
    - AI-3: $1000

    Expected: 3 pots
    - Pot 1: $200 (4 players × $50)
    - Pot 2: $150 (3 players × $50)
    - Pot 3: $850 (2 players × remaining)
    """
    print("\n" + "="*70)
    print("SCENARIO 2: Multiple All-Ins")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    # Set up stacks
    game.players[0].stack = 50   # Player
    game.players[1].stack = 100  # AI-ce
    game.players[2].stack = 200  # AI-ron
    game.players[3].stack = 1000 # AI-nstein

    # Recalculate total_chips for QC
    game.total_chips = sum(p.stack for p in game.players)

    print(f"\nInitial stacks:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Total: ${game.total_chips}")

    # Start hand and manually set all-ins
    game.start_new_hand()

    game.players[0].total_invested = 50
    game.players[0].all_in = True
    game.players[0].is_active = True
    game.players[1].total_invested = 100
    game.players[1].all_in = True
    game.players[1].is_active = True
    game.players[2].total_invested = 200
    game.players[2].all_in = True
    game.players[2].is_active = True
    game.players[3].total_invested = 200  # Calls AI-ron's all-in
    game.players[3].is_active = True

    # Calculate side pots
    pots = game.hand_evaluator.determine_winners_with_side_pots(
        game.players, game.community_cards
    )

    print(f"\nSide pot calculation:")
    total_invested = sum(p.total_invested for p in game.players)
    print(f"Total invested: ${total_invested}")
    print(f"Number of pots: {len(pots)}")

    for i, pot in enumerate(pots):
        print(f"\nPot {i+1} ({pot['type']}):")
        print(f"  Amount: ${pot['amount']}")
        print(f"  Eligible players: {pot['eligible_player_ids']}")
        print(f"  Winners: {pot['winners']}")

    # Verify
    assert len(pots) == 3, f"Expected 3 pots, got {len(pots)}"

    assert pots[0]['amount'] == 200, f"Pot 1 should be $200, got ${pots[0]['amount']}"
    assert len(pots[0]['eligible_player_ids']) == 4, "All 4 players eligible for pot 1"

    assert pots[1]['amount'] == 150, f"Pot 2 should be $150, got ${pots[1]['amount']}"
    assert len(pots[1]['eligible_player_ids']) == 3, "3 players eligible for pot 2"

    assert pots[2]['amount'] == 200, f"Pot 3 should be $200, got ${pots[2]['amount']}"
    assert len(pots[2]['eligible_player_ids']) == 2, "2 players eligible for pot 3"

    print(f"\n✅ Scenario 2 PASSED")
    return True

def test_scenario_3_all_in_with_fold():
    """
    Scenario 3: One all-in, one fold, two active
    - Player: $100 (folded)
    - AI-1: $50 (all-in)
    - AI-2: $1000 (active)
    - AI-3: $1000 (active)

    Expected: Main pot includes folded player's contribution
    """
    print("\n" + "="*70)
    print("SCENARIO 3: All-In With Fold")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    # Set up stacks
    game.players[0].stack = 100  # Player (will fold)
    game.players[1].stack = 50   # AI-ce (will go all-in)
    game.players[2].stack = 1000 # AI-ron
    game.players[3].stack = 1000 # AI-nstein

    # Recalculate total_chips for QC
    game.total_chips = sum(p.stack for p in game.players)

    print(f"\nInitial stacks:")
    for p in game.players:
        print(f"  {p.name}: ${p.stack}")
    print(f"Total: ${game.total_chips}")

    # Start hand
    game.start_new_hand()

    # Player folds after betting $20
    game.players[0].total_invested = 20
    game.players[0].is_active = False  # Folded

    # AI-ce goes all-in for $50
    game.players[1].total_invested = 50
    game.players[1].all_in = True
    game.players[1].is_active = True

    # Others call
    game.players[2].total_invested = 50
    game.players[2].is_active = True
    game.players[3].total_invested = 50
    game.players[3].is_active = True

    # Calculate total invested BEFORE calling side pot method (it modifies total_invested)
    total_invested_before = sum(p.total_invested for p in game.players)

    # Calculate side pots
    pots = game.hand_evaluator.determine_winners_with_side_pots(
        game.players, game.community_cards
    )

    print(f"\nSide pot calculation:")
    print(f"Total invested: ${total_invested_before}")
    print(f"Number of pots: {len(pots)}")

    for i, pot in enumerate(pots):
        print(f"\nPot {i+1} ({pot['type']}):")
        print(f"  Amount: ${pot['amount']}")
        print(f"  Eligible players: {pot['eligible_player_ids']}")
        print(f"  Winners: {pot['winners']}")

    # Verify: Folded player's chips ARE included, but distributed across pot levels
    # Pot 1 (at $20 level): 4 players × $20 = $80
    # Pot 2 (at $50 level): 3 players × $30 = $90
    # Total: $170 (all chips accounted for)
    assert len(pots) == 2, f"Expected 2 pots, got {len(pots)}"
    assert pots[0]['amount'] == 80, f"Main pot should be $80, got ${pots[0]['amount']}"
    assert pots[1]['amount'] == 90, f"Side pot should be $90, got ${pots[1]['amount']}"
    assert len(pots[0]['eligible_player_ids']) == 3, "Only 3 active/all-in players can win"

    # Verify total chips accounted for
    total_pot = sum(pot['amount'] for pot in pots)
    assert total_pot == total_invested_before, f"Total pot ${total_pot} != Total invested ${total_invested_before}"

    print(f"\n✅ Scenario 3 PASSED - Folded player's chips correctly included")
    return True

if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE SIDE POT TESTS (Issue #6)")
    print("="*70)

    try:
        test_scenario_1_simple_all_in()
        test_scenario_2_multiple_all_ins()
        test_scenario_3_all_in_with_fold()

        print("\n" + "="*70)
        print("✅ ALL SIDE POT TESTS PASSED!")
        print("="*70)
        print("\nConclusion: Side pots are working correctly.")
        print("Issue #6 is already fixed in the backend.")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
