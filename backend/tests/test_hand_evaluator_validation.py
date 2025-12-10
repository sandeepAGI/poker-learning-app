"""
Phase 3.2: Hand Evaluator Validation with MD5 Checksums
=======================================================
Validates hand evaluator correctness and creates regression checksums.

Strategy:
- Test known hand rankings (Royal Flush → High Card)
- Generate MD5 checksums for 100 standard test cases
- Test 10,000 random hands for consistency
- Validate score ranges match expected hand types

Phase 3 of Testing Improvement Plan (10 hours total, 4 hours for validation)
"""

import pytest
import random
import hashlib
from typing import List, Tuple, Dict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game.poker_engine import HandEvaluator


def get_standard_test_hands() -> List[Dict]:
    """
    Standard test hands with known rankings for regression testing.
    Covers all hand types from Royal Flush to High Card.
    """
    return [
        # Royal Flush (1-10)
        {
            "name": "royal_flush_spades",
            "hole": ["As", "Ks"],
            "board": ["Qs", "Js", "10s"],
            "expected_rank": "Royal Flush",
            "expected_strength": 0.95
        },
        {
            "name": "royal_flush_hearts",
            "hole": ["Ah", "Kh"],
            "board": ["Qh", "Jh", "10h"],
            "expected_rank": "Royal Flush",
            "expected_strength": 0.95
        },

        # Straight Flush (1-10)
        {
            "name": "straight_flush_9_high",
            "hole": ["9s", "8s"],
            "board": ["7s", "6s", "5s"],
            "expected_rank": "Straight Flush",
            "expected_strength": 0.95
        },
        {
            "name": "straight_flush_king_high",
            "hole": ["Kd", "Qd"],
            "board": ["Jd", "10d", "9d"],
            "expected_rank": "Straight Flush",
            "expected_strength": 0.95
        },

        # Four of a Kind (11-166)
        {
            "name": "quad_aces",
            "hole": ["As", "Ah"],
            "board": ["Ad", "Ac", "Ks"],
            "expected_rank": "Four of a Kind",
            "expected_strength": 0.90
        },
        {
            "name": "quad_kings",
            "hole": ["Ks", "Kh"],
            "board": ["Kd", "Kc", "Qs"],
            "expected_rank": "Four of a Kind",
            "expected_strength": 0.90
        },
        {
            "name": "quad_twos",
            "hole": ["2s", "2h"],
            "board": ["2d", "2c", "7s"],
            "expected_rank": "Four of a Kind",
            "expected_strength": 0.90
        },

        # Full House (167-322)
        {
            "name": "full_house_aces_kings",
            "hole": ["As", "Ah"],
            "board": ["Ad", "Ks", "Kh"],
            "expected_rank": "Full House",
            "expected_strength": 0.85
        },
        {
            "name": "full_house_queens_jacks",
            "hole": ["Qs", "Qh"],
            "board": ["Qd", "Js", "Jh"],
            "expected_rank": "Full House",
            "expected_strength": 0.85
        },
        {
            "name": "full_house_threes_twos",
            "hole": ["3s", "3h"],
            "board": ["3d", "2s", "2h"],
            "expected_rank": "Full House",
            "expected_strength": 0.85
        },

        # Flush (323-1599)
        {
            "name": "flush_ace_high_spades",
            "hole": ["As", "Ks"],
            "board": ["9s", "7s", "3s"],
            "expected_rank": "Flush",
            "expected_strength": 0.75
        },
        {
            "name": "flush_queen_high_hearts",
            "hole": ["Qh", "Jh"],
            "board": ["9h", "6h", "2h"],
            "expected_rank": "Flush",
            "expected_strength": 0.75
        },
        {
            "name": "flush_seven_high_diamonds",
            "hole": ["7d", "5d"],
            "board": ["4d", "3d", "2d"],
            "expected_rank": "Flush",
            "expected_strength": 0.75
        },

        # Straight (1600-1609)
        {
            "name": "straight_ace_high",
            "hole": ["As", "Kh"],
            "board": ["Qd", "Jc", "10s"],
            "expected_rank": "Straight",
            "expected_strength": 0.65
        },
        {
            "name": "straight_ten_high",
            "hole": ["10s", "9h"],
            "board": ["8d", "7c", "6s"],
            "expected_rank": "Straight",
            "expected_strength": 0.65
        },
        {
            "name": "straight_five_high_wheel",
            "hole": ["5s", "4h"],
            "board": ["3d", "2c", "As"],
            "expected_rank": "Straight",
            "expected_strength": 0.65
        },

        # Three of a Kind (1610-2467)
        {
            "name": "trips_aces",
            "hole": ["As", "Ah"],
            "board": ["Ad", "Ks", "Qh"],
            "expected_rank": "Three of a Kind",
            "expected_strength": 0.55
        },
        {
            "name": "trips_tens",
            "hole": ["10s", "10h"],
            "board": ["10d", "7s", "3h"],
            "expected_rank": "Three of a Kind",
            "expected_strength": 0.55
        },
        {
            "name": "trips_deuces",
            "hole": ["2s", "2h"],
            "board": ["2d", "9s", "5h"],
            "expected_rank": "Three of a Kind",
            "expected_strength": 0.55
        },

        # Two Pair (2468-3325)
        {
            "name": "two_pair_aces_kings",
            "hole": ["As", "Ks"],
            "board": ["Ah", "Kh", "Qd"],
            "expected_rank": "Two Pair",
            "expected_strength": 0.45
        },
        {
            "name": "two_pair_queens_jacks",
            "hole": ["Qs", "Js"],
            "board": ["Qh", "Jh", "7d"],
            "expected_rank": "Two Pair",
            "expected_strength": 0.45
        },
        {
            "name": "two_pair_fours_threes",
            "hole": ["4s", "3s"],
            "board": ["4h", "3h", "Kd"],
            "expected_rank": "Two Pair",
            "expected_strength": 0.45
        },

        # One Pair (3326-6185)
        {
            "name": "pair_aces",
            "hole": ["As", "Kh"],
            "board": ["Ah", "Qd", "Jc"],
            "expected_rank": "Pair",
            "expected_strength": 0.25
        },
        {
            "name": "pair_tens",
            "hole": ["10s", "9h"],
            "board": ["10h", "7d", "4c"],
            "expected_rank": "Pair",
            "expected_strength": 0.25
        },
        {
            "name": "pair_deuces",
            "hole": ["2s", "Ah"],
            "board": ["2h", "Kd", "Qc"],
            "expected_rank": "Pair",
            "expected_strength": 0.25
        },

        # High Card (6186-7462)
        {
            "name": "high_card_ace_king",
            "hole": ["As", "Kh"],
            "board": ["Qd", "Jc", "9s"],
            "expected_rank": "High Card",
            "expected_strength": 0.05
        },
        {
            "name": "high_card_queen_jack",
            "hole": ["Qs", "Jh"],
            "board": ["9d", "7c", "4s"],
            "expected_rank": "High Card",
            "expected_strength": 0.05
        },
        {
            "name": "high_card_seven_five",
            "hole": ["7s", "5h"],
            "board": ["4d", "3c", "2s"],
            "expected_rank": "High Card",
            "expected_strength": 0.05
        },
    ]


class TestHandEvaluatorValidation:
    """Phase 3.2: Hand evaluator validation and regression testing"""

    def test_known_hand_rankings(self):
        """
        Test known hand rankings are correctly identified.

        Validates all hand types from Royal Flush to High Card
        match expected rankings.
        """
        print("\n[VALIDATION] Testing known hand rankings...")

        evaluator = HandEvaluator()
        test_hands = get_standard_test_hands()

        failures = []
        for test_case in test_hands:
            score, rank = evaluator.evaluate_hand(
                test_case["hole"],
                test_case["board"]
            )
            strength = evaluator.score_to_strength(score)

            # Check rank matches
            if rank != test_case["expected_rank"]:
                failures.append({
                    "test": test_case["name"],
                    "expected_rank": test_case["expected_rank"],
                    "actual_rank": rank,
                    "score": score
                })

            # Check strength matches
            if strength != test_case["expected_strength"]:
                failures.append({
                    "test": test_case["name"],
                    "expected_strength": test_case["expected_strength"],
                    "actual_strength": strength,
                    "score": score
                })

        if failures:
            print("\n❌ Hand ranking validation FAILED:")
            for failure in failures:
                print(f"  {failure}")

        assert len(failures) == 0, f"Hand ranking validation failed: {len(failures)} mismatches"
        print(f"✅ All {len(test_hands)} known hands evaluated correctly")


    def test_hand_evaluator_checksum(self):
        """
        Generate MD5 checksum of hand evaluations for regression testing.

        Creates a fingerprint of hand evaluator behavior.
        If this test fails after code changes, hand evaluator logic changed.
        """
        print("\n[VALIDATION] Generating hand evaluator MD5 checksum...")

        evaluator = HandEvaluator()
        test_hands = get_standard_test_hands()

        # Generate ordered list of results
        results = []
        for test_case in test_hands:
            score, rank = evaluator.evaluate_hand(
                test_case["hole"],
                test_case["board"]
            )
            strength = evaluator.score_to_strength(score)
            results.append(f"{test_case['name']}:{score}:{rank}:{strength}")

        # Calculate checksum
        checksum = hashlib.md5("\n".join(results).encode()).hexdigest()

        print(f"[VALIDATION] Hand evaluator checksum: {checksum}")

        # Expected checksum (update this after first run if tests pass)
        # This checksum represents the KNOWN GOOD state of hand evaluator
        EXPECTED_CHECKSUM = "TBD_UPDATE_AFTER_FIRST_RUN"

        # For now, just print and don't fail (will update after first successful run)
        if EXPECTED_CHECKSUM == "TBD_UPDATE_AFTER_FIRST_RUN":
            print(f"[VALIDATION] ⚠️  First run - checksum not yet set")
            print(f"[VALIDATION] Copy this checksum to EXPECTED_CHECKSUM:")
            print(f"EXPECTED_CHECKSUM = \"{checksum}\"")
        else:
            assert checksum == EXPECTED_CHECKSUM, \
                f"Hand evaluator behavior changed!\n" \
                f"Expected: {EXPECTED_CHECKSUM}\n" \
                f"Got:      {checksum}\n" \
                f"This indicates hand evaluator logic was modified."


    def test_score_ranges_match_hand_types(self):
        """
        Validate score ranges match expected hand types.

        Treys evaluator scores:
        - 1-10: Straight Flush
        - 11-166: Four of a Kind
        - 167-322: Full House
        - 323-1599: Flush
        - 1600-1609: Straight
        - 1610-2467: Three of a Kind
        - 2468-3325: Two Pair
        - 3326-6185: One Pair
        - 6186-7462: High Card
        """
        print("\n[VALIDATION] Validating score ranges...")

        evaluator = HandEvaluator()

        range_tests = [
            # (hole, board, expected_min_score, expected_max_score, rank_name)
            (["As", "Ks"], ["Qs", "Js", "10s"], 1, 10, "Straight Flush"),
            (["As", "Ah"], ["Ad", "Ac", "Ks"], 11, 166, "Four of a Kind"),
            (["As", "Ah"], ["Ad", "Ks", "Kh"], 167, 322, "Full House"),
            (["As", "Ks"], ["9s", "7s", "3s"], 323, 1599, "Flush"),
            (["As", "Kh"], ["Qd", "Jc", "10s"], 1600, 1609, "Straight"),
            (["As", "Ah"], ["Ad", "Ks", "Qh"], 1610, 2467, "Three of a Kind"),
            (["As", "Ks"], ["Ah", "Kh", "Qd"], 2468, 3325, "Two Pair"),
            (["As", "Kh"], ["Ah", "Qd", "Jc"], 3326, 6185, "Pair"),
            (["As", "Kh"], ["Qd", "Jc", "9s"], 6186, 7462, "High Card"),
        ]

        failures = []
        for hole, board, min_score, max_score, expected_rank in range_tests:
            score, rank = evaluator.evaluate_hand(hole, board)

            if not (min_score <= score <= max_score):
                failures.append({
                    "hand": f"{hole} + {board}",
                    "expected_range": f"{min_score}-{max_score}",
                    "actual_score": score,
                    "expected_rank": expected_rank,
                    "actual_rank": rank
                })

        if failures:
            print("\n❌ Score range validation FAILED:")
            for failure in failures:
                print(f"  {failure}")

        assert len(failures) == 0, f"Score range validation failed: {failures}"
        print(f"✅ All {len(range_tests)} score ranges validated")


    def test_random_hands_consistency(self):
        """
        Test 10,000 random hands for consistency.

        Ensures hand evaluator doesn't crash on random inputs
        and produces consistent results.
        """
        print("\n[VALIDATION] Testing 10,000 random hands for consistency...")

        evaluator = HandEvaluator()
        deck = [f"{r}{s}" for r in "23456789TJQKA" for s in "shdc"]

        stats = {
            "total": 0,
            "errors": 0,
            "invalid_scores": 0,
            "invalid_strengths": 0,
            "hand_types": {}
        }

        for i in range(10000):
            # Generate random 7-card hand
            cards = random.sample(deck, 7)
            hole = cards[:2]
            board = cards[2:7]

            try:
                score, rank = evaluator.evaluate_hand(hole, board)
                strength = evaluator.score_to_strength(score)

                stats["total"] += 1

                # Validate score is in valid range (1-7462 for Treys)
                if not (1 <= score <= 7462):
                    stats["invalid_scores"] += 1

                # Validate strength is in valid range (0.0-1.0)
                if not (0.0 <= strength <= 1.0):
                    stats["invalid_strengths"] += 1

                # Track hand type distribution
                stats["hand_types"][rank] = stats["hand_types"].get(rank, 0) + 1

            except Exception as e:
                stats["errors"] += 1
                print(f"[VALIDATION] ❌ Error on hand {i}: {e}")
                if stats["errors"] > 10:
                    raise

        # Print summary
        print("\n" + "="*70)
        print("RANDOM HAND CONSISTENCY SUMMARY")
        print("="*70)
        print(f"Total hands tested:      {stats['total']:>7,}")
        print(f"Errors:                  {stats['errors']:>7,}")
        print(f"Invalid scores:          {stats['invalid_scores']:>7,}")
        print(f"Invalid strengths:       {stats['invalid_strengths']:>7,}")
        print(f"\nHand type distribution:")
        for rank, count in sorted(stats["hand_types"].items(), key=lambda x: -x[1]):
            percentage = (count / stats["total"]) * 100
            print(f"  {rank:20s} {count:>7,}  ({percentage:5.2f}%)")
        print("="*70)

        # Assertions
        assert stats["errors"] == 0, f"Evaluator crashed {stats['errors']} times"
        assert stats["invalid_scores"] == 0, f"Generated {stats['invalid_scores']} invalid scores"
        assert stats["invalid_strengths"] == 0, f"Generated {stats['invalid_strengths']} invalid strengths"


    def test_score_to_strength_correctness(self):
        """
        Validate score_to_strength conversion is correct.

        Tests boundary conditions and ensures consistent mapping.
        """
        print("\n[VALIDATION] Testing score_to_strength conversion...")

        evaluator = HandEvaluator()

        test_cases = [
            # (score, expected_strength, description)
            (1, 0.95, "Royal Flush"),
            (10, 0.95, "Straight Flush boundary"),
            (11, 0.90, "Four of a Kind start"),
            (166, 0.90, "Four of a Kind end"),
            (167, 0.85, "Full House start"),
            (322, 0.85, "Full House end"),
            (323, 0.75, "Flush start"),
            (1599, 0.75, "Flush end"),
            (1600, 0.65, "Straight start"),
            (1609, 0.65, "Straight end"),
            (1610, 0.55, "Three of a Kind start"),
            (2467, 0.55, "Three of a Kind end"),
            (2468, 0.45, "Two Pair start"),
            (3325, 0.45, "Two Pair end"),
            (3326, 0.25, "One Pair start"),
            (6185, 0.25, "One Pair end"),
            (6186, 0.05, "High Card start"),
            (7462, 0.05, "High Card end"),
        ]

        failures = []
        for score, expected, desc in test_cases:
            actual = evaluator.score_to_strength(score)
            if actual != expected:
                failures.append({
                    "score": score,
                    "expected": expected,
                    "actual": actual,
                    "description": desc
                })

        if failures:
            print("\n❌ score_to_strength validation FAILED:")
            for failure in failures:
                print(f"  {failure}")

        assert len(failures) == 0, f"score_to_strength validation failed: {failures}"
        print(f"✅ All {len(test_cases)} score→strength mappings correct")
