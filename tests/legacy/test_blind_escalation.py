#!/usr/bin/env python3
"""
Test blind escalation (Issue #1 fix).
Blinds should increase every N hands.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame

def test_blind_escalation():
    """Test that blinds increase correctly over time."""
    print("="*70)
    print("TEST: Blind Escalation (Issue #1)")
    print("="*70)

    game = PokerGame("Player", ai_count=3)

    # Disable QC for this test (we're only testing blind logic, not hand completion)
    game.qc_enabled = False

    # Default settings: increase every 10 hands by 1.5x
    assert game.blind_escalation_enabled == True
    assert game.hands_per_blind_level == 10
    assert game.blind_multiplier == 1.5

    print(f"\nInitial blinds: ${game.small_blind}/${game.big_blind}")
    assert game.small_blind == 5
    assert game.big_blind == 10

    # Play 10 hands
    print(f"\nPlaying hands 1-10...")
    for hand_num in range(10):
        game.pot = 0  # Reset pot (simulate hand completion)
        game.start_new_hand()
        print(f"  Hand #{game.hand_count}: Blinds ${game.small_blind}/${game.big_blind}")

        # Blinds should not change yet
        assert game.small_blind == 5, f"SB changed early at hand {game.hand_count}"
        assert game.big_blind == 10, f"BB changed early at hand {game.hand_count}"

    # Hand 11 should trigger blind increase
    print(f"\nStarting hand 11 (should trigger blind increase)...")
    game.pot = 0
    game.start_new_hand()
    print(f"  Hand #{game.hand_count}: Blinds ${game.small_blind}/${game.big_blind}")

    # Blinds should increase by 1.5x (5 → 7, 10 → 15)
    assert game.small_blind == 7, f"SB should be 7, got {game.small_blind}"
    assert game.big_blind == 15, f"BB should be 15, got {game.big_blind}"

    # Play 9 more hands (hands 12-20)
    print(f"\nPlaying hands 12-20...")
    for hand_num in range(9):
        game.pot = 0
        game.start_new_hand()
        print(f"  Hand #{game.hand_count}: Blinds ${game.small_blind}/${game.big_blind}")

        # Blinds should stay at new level
        assert game.small_blind == 7, f"SB changed mid-level at hand {game.hand_count}"
        assert game.big_blind == 15, f"BB changed mid-level at hand {game.hand_count}"

    # Hand 21 should trigger another blind increase
    print(f"\nStarting hand 21 (should trigger second blind increase)...")
    game.pot = 0
    game.start_new_hand()
    print(f"  Hand #{game.hand_count}: Blinds ${game.small_blind}/${game.big_blind}")

    # Blinds should increase again (7 → 10, 15 → 22)
    assert game.small_blind == 10, f"SB should be 10, got {game.small_blind}"
    assert game.big_blind == 22, f"BB should be 22, got {game.big_blind}"

    print("\n✅ Blind escalation working correctly!")
    print(f"   Level 1 (hands 1-10): $5/$10")
    print(f"   Level 2 (hands 11-20): $7/$15")
    print(f"   Level 3 (hands 21+): $10/$22")

    return True

def test_blind_escalation_disabled():
    """Test that blinds don't increase when escalation is disabled."""
    print("\n" + "="*70)
    print("TEST: Blind Escalation Disabled")
    print("="*70)

    game = PokerGame("Player", ai_count=3)
    game.qc_enabled = False  # Disable QC for this test
    game.blind_escalation_enabled = False

    print(f"\nBlind escalation disabled")
    print(f"Initial blinds: ${game.small_blind}/${game.big_blind}")

    # Play 25 hands
    print(f"\nPlaying 25 hands...")
    for hand_num in range(25):
        game.pot = 0  # Reset pot (simulate hand completion)
        game.start_new_hand()

    print(f"After 25 hands: Blinds ${game.small_blind}/${game.big_blind}")

    # Blinds should never change
    assert game.small_blind == 5, f"SB changed when disabled: {game.small_blind}"
    assert game.big_blind == 10, f"BB changed when disabled: {game.big_blind}"

    print("✅ Blinds stayed constant when escalation disabled!")

    return True

if __name__ == "__main__":
    try:
        test_blind_escalation()
        test_blind_escalation_disabled()

        print("\n" + "="*70)
        print("✅ ALL BLIND ESCALATION TESTS PASSED!")
        print("="*70)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
