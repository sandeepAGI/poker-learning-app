"""
Test HandEvaluator.score_to_strength() - SINGLE SOURCE OF TRUTH for hand strength.

Tests the consolidated hand strength calculation that was previously duplicated
in 4 locations (2 of which were incomplete).

Phase 4 of refactoring plan.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import HandEvaluator


class TestScoreToStrength:
    """Test score_to_strength() static method."""

    def test_royal_flush_strength(self):
        """Royal/Straight flush (score 1-10) should return 0.95."""
        assert HandEvaluator.score_to_strength(1) == 0.95
        assert HandEvaluator.score_to_strength(5) == 0.95
        assert HandEvaluator.score_to_strength(10) == 0.95

    def test_four_of_a_kind_strength(self):
        """Four of a kind (score 11-166) should return 0.90."""
        assert HandEvaluator.score_to_strength(11) == 0.90
        assert HandEvaluator.score_to_strength(100) == 0.90
        assert HandEvaluator.score_to_strength(166) == 0.90

    def test_full_house_strength(self):
        """Full house (score 167-322) should return 0.85."""
        assert HandEvaluator.score_to_strength(167) == 0.85
        assert HandEvaluator.score_to_strength(250) == 0.85
        assert HandEvaluator.score_to_strength(322) == 0.85

    def test_flush_strength(self):
        """Flush (score 323-1599) should return 0.75."""
        assert HandEvaluator.score_to_strength(323) == 0.75
        assert HandEvaluator.score_to_strength(1000) == 0.75
        assert HandEvaluator.score_to_strength(1599) == 0.75

    def test_straight_strength(self):
        """Straight (score 1600-1609) should return 0.65."""
        assert HandEvaluator.score_to_strength(1600) == 0.65
        assert HandEvaluator.score_to_strength(1605) == 0.65
        assert HandEvaluator.score_to_strength(1609) == 0.65

    def test_three_of_a_kind_strength(self):
        """Three of a kind (score 1610-2467) should return 0.55."""
        assert HandEvaluator.score_to_strength(1610) == 0.55
        assert HandEvaluator.score_to_strength(2000) == 0.55
        assert HandEvaluator.score_to_strength(2467) == 0.55

    def test_two_pair_strength(self):
        """Two pair (score 2468-3325) should return 0.45."""
        assert HandEvaluator.score_to_strength(2468) == 0.45
        assert HandEvaluator.score_to_strength(3000) == 0.45
        assert HandEvaluator.score_to_strength(3325) == 0.45

    def test_one_pair_strength(self):
        """One pair (score 3326-6185) should return 0.25."""
        assert HandEvaluator.score_to_strength(3326) == 0.25
        assert HandEvaluator.score_to_strength(5000) == 0.25
        assert HandEvaluator.score_to_strength(6185) == 0.25

    def test_high_card_strength(self):
        """High card (score 6186+) should return 0.05."""
        assert HandEvaluator.score_to_strength(6186) == 0.05
        assert HandEvaluator.score_to_strength(7000) == 0.05
        assert HandEvaluator.score_to_strength(7462) == 0.05


class TestScoreToStrengthBoundaries:
    """Test boundary conditions for score_to_strength()."""

    def test_boundary_four_of_kind_full_house(self):
        """Test boundary between four of a kind and full house."""
        assert HandEvaluator.score_to_strength(166) == 0.90  # Four of a kind
        assert HandEvaluator.score_to_strength(167) == 0.85  # Full house

    def test_boundary_full_house_flush(self):
        """Test boundary between full house and flush."""
        assert HandEvaluator.score_to_strength(322) == 0.85  # Full house
        assert HandEvaluator.score_to_strength(323) == 0.75  # Flush

    def test_boundary_flush_straight(self):
        """Test boundary between flush and straight."""
        assert HandEvaluator.score_to_strength(1599) == 0.75  # Flush
        assert HandEvaluator.score_to_strength(1600) == 0.65  # Straight

    def test_boundary_straight_three_of_kind(self):
        """Test boundary between straight and three of a kind."""
        assert HandEvaluator.score_to_strength(1609) == 0.65  # Straight
        assert HandEvaluator.score_to_strength(1610) == 0.55  # Three of a kind

    def test_boundary_three_of_kind_two_pair(self):
        """Test boundary between three of a kind and two pair."""
        assert HandEvaluator.score_to_strength(2467) == 0.55  # Three of a kind
        assert HandEvaluator.score_to_strength(2468) == 0.45  # Two pair

    def test_boundary_two_pair_one_pair(self):
        """Test boundary between two pair and one pair."""
        assert HandEvaluator.score_to_strength(3325) == 0.45  # Two pair
        assert HandEvaluator.score_to_strength(3326) == 0.25  # One pair

    def test_boundary_one_pair_high_card(self):
        """Test boundary between one pair and high card."""
        assert HandEvaluator.score_to_strength(6185) == 0.25  # One pair
        assert HandEvaluator.score_to_strength(6186) == 0.05  # High card


class TestScoreToStrengthOrdering:
    """Test that strength values are properly ordered."""

    def test_strength_decreases_with_score(self):
        """Higher scores (worse hands) should have lower strength."""
        # Sample scores for each hand type
        royal_flush = 5
        four_kind = 100
        full_house = 250
        flush = 1000
        straight = 1605
        three_kind = 2000
        two_pair = 3000
        one_pair = 5000
        high_card = 7000

        strengths = [
            HandEvaluator.score_to_strength(royal_flush),
            HandEvaluator.score_to_strength(four_kind),
            HandEvaluator.score_to_strength(full_house),
            HandEvaluator.score_to_strength(flush),
            HandEvaluator.score_to_strength(straight),
            HandEvaluator.score_to_strength(three_kind),
            HandEvaluator.score_to_strength(two_pair),
            HandEvaluator.score_to_strength(one_pair),
            HandEvaluator.score_to_strength(high_card),
        ]

        # Each strength should be >= next strength
        for i in range(len(strengths) - 1):
            assert strengths[i] >= strengths[i + 1], \
                f"Strength ordering violated: {strengths[i]} should be >= {strengths[i + 1]}"


class TestScoreToStrengthReturnType:
    """Test return type of score_to_strength()."""

    def test_returns_float(self):
        """Should return a float."""
        result = HandEvaluator.score_to_strength(1000)
        assert isinstance(result, float)

    def test_returns_value_in_range(self):
        """Should return value between 0.0 and 1.0."""
        for score in [1, 100, 500, 1000, 2000, 3000, 5000, 7000]:
            strength = HandEvaluator.score_to_strength(score)
            assert 0.0 <= strength <= 1.0, f"Strength {strength} out of range for score {score}"


class TestHandEvaluatorIntegration:
    """Test score_to_strength() with actual hand evaluation."""

    def test_pair_actual(self):
        """Test actual pair hand."""
        evaluator = HandEvaluator()

        # A pair of aces (no straight possible)
        hole_cards = ["As", "Ah"]
        community = ["2c", "7d", "9h", "Js", "Kc"]

        score, rank = evaluator.evaluate_hand(hole_cards, community)
        strength = HandEvaluator.score_to_strength(int(score))

        # Pair of aces should be a pair (0.25 strength)
        assert strength == 0.25, f"Pair of aces got strength {strength}, expected 0.25"

    def test_straight_actual(self):
        """Test actual straight hand."""
        evaluator = HandEvaluator()

        # Broadway straight
        hole_cards = ["Ts", "Jh"]
        community = ["Qc", "Kd", "Ah", "2s", "3c"]

        score, rank = evaluator.evaluate_hand(hole_cards, community)
        strength = HandEvaluator.score_to_strength(int(score))

        # Should be straight (0.65)
        assert strength == 0.65, f"Straight got strength {strength}, expected 0.65"

    def test_full_house_actual(self):
        """Test actual full house hand."""
        evaluator = HandEvaluator()

        # Full house: AAA-22
        hole_cards = ["As", "Ah"]
        community = ["Ac", "2d", "2h", "5s", "9c"]

        score, rank = evaluator.evaluate_hand(hole_cards, community)
        strength = HandEvaluator.score_to_strength(int(score))

        # Should be full house (0.85)
        assert strength == 0.85, f"Full house got strength {strength}, expected 0.85"

    def test_wheel_straight_actual(self):
        """Test wheel straight (A-2-3-4-5)."""
        evaluator = HandEvaluator()

        # Wheel straight
        hole_cards = ["As", "2h"]
        community = ["3c", "4d", "5h", "Js", "Kc"]

        score, rank = evaluator.evaluate_hand(hole_cards, community)
        strength = HandEvaluator.score_to_strength(int(score))

        # Should be straight (0.65)
        assert strength == 0.65, f"Wheel straight got strength {strength}, expected 0.65"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
