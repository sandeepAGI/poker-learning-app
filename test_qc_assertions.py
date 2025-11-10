#!/usr/bin/env python3
"""
Test QC assertions - verify they catch bugs immediately
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from game.poker_engine import PokerGame

def test_qc_catches_chip_loss():
    """Test that QC catches chip conservation violations."""
    print("=" * 70)
    print("TEST: QC Assertions Catch Chip Loss")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print("\n✓ Game started with QC enabled")
    print(f"  QC enabled: {game.qc_enabled}")

    # Artificially violate chip conservation
    print("\n→ Simulating chip loss bug (removing $100 from pot)...")
    game.pot -= 100

    # Try to call submit_human_action - should trigger QC assertion
    try:
        game.submit_human_action("call")
        print("\n❌ FAIL: QC did not catch chip loss!")
        return False
    except RuntimeError as e:
        print(f"\n✅ PASS: QC caught chip loss!")
        print(f"  Error message:")
        print(f"  {str(e)}")
        if "CHIP CONSERVATION VIOLATED" in str(e):
            print(f"\n✅ PASS: Error message is clear and helpful")
            return True
        else:
            print(f"\n❌ FAIL: Error message not clear")
            return False

def test_qc_catches_negative_pot():
    """Test that QC catches invalid game state (negative pot)."""
    print("\n" + "=" * 70)
    print("TEST: QC Assertions Catch Negative Pot")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    print("\n→ Simulating bug (setting pot to -50)...")
    game.pot = -50

    # Try to call start_new_hand - should trigger QC assertion
    try:
        game.start_new_hand()
        print("\n❌ FAIL: QC did not catch negative pot!")
        return False
    except RuntimeError as e:
        print(f"\n✅ PASS: QC caught negative pot!")
        print(f"  Error message:")
        print(f"  {str(e)}")
        if "INVALID GAME STATE" in str(e) and "negative" in str(e).lower():
            print(f"\n✅ PASS: Error message is clear and helpful")
            return True
        else:
            print(f"\n❌ FAIL: Error message not clear")
            return False

def test_qc_can_be_disabled():
    """Test that QC can be disabled for performance."""
    print("\n" + "=" * 70)
    print("TEST: QC Can Be Disabled")
    print("=" * 70)

    game = PokerGame("TestPlayer", ai_count=3)
    game.start_new_hand()

    # Disable QC
    game.qc_enabled = False
    print("\n✓ QC disabled")

    # Violate chip conservation
    print("→ Violating chip conservation with QC disabled...")
    game.pot -= 100

    # Should NOT raise exception
    try:
        # Just call the assertion directly
        game._assert_chip_conservation("test")
        print("\n✅ PASS: QC disabled, no exception raised")
        return True
    except RuntimeError:
        print("\n❌ FAIL: QC raised exception even when disabled!")
        return False

if __name__ == "__main__":
    print("\n🚨 PHASE 1: QC RUNTIME ASSERTIONS TEST SUITE 🚨\n")

    results = []

    # Test 1
    results.append(("Chip Loss Detection", test_qc_catches_chip_loss()))

    # Test 2
    results.append(("Negative Pot Detection", test_qc_catches_negative_pot()))

    # Test 3
    results.append(("QC Disable Feature", test_qc_can_be_disabled()))

    # Summary
    print("\n" + "=" * 70)
    print("QC ASSERTIONS TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL QC ASSERTION TESTS PASSED!")
        print("Phase 1 complete - QC guards are working correctly")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
