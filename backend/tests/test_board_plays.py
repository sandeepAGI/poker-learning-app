"""
Test scenarios where board plays (hole cards don't improve hand).

Edge cases where the best 5-card hand is entirely on the board,
making hole cards irrelevant. Critical for split pot scenarios.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import HandEvaluator


class TestBoardPlays:
    """Test board plays scenarios."""

    def test_board_plays_split_pot_straight(self):
        """When best 5 cards are all on board, pot splits."""
        print("\n[BOARD PLAYS] Testing board straight split pot...")
        evaluator = HandEvaluator()

        # Board: A-K-Q-J-10 (Broadway straight)
        board = ["Ah", "Kh", "Qh", "Jh", "10h"]

        # Player 1: 2-3 (doesn't play)
        p1_hole = ["2c", "3c"]
        p1_score, p1_rank = evaluator.evaluate_hand(p1_hole, board)

        # Player 2: 4-5 (doesn't play)
        p2_hole = ["4d", "5d"]
        p2_score, p2_rank = evaluator.evaluate_hand(p2_hole, board)

        # Both should have same hand (royal flush)
        assert p1_score == p2_score, f"Scores should be identical: {p1_score} vs {p2_score}"
        assert p1_rank == p2_rank, f"Ranks should match: {p1_rank} vs {p2_rank}"
        print(f"  ✅ Both players have {p1_rank} (score: {p1_score})")
        print(f"  ✅ Hole cards irrelevant, pot splits")

    def test_board_plays_split_pot_quads(self):
        """Board with quads, split pot."""
        print("\n[BOARD PLAYS] Testing board quads split pot...")
        evaluator = HandEvaluator()

        # Board: A-A-A-A-K (Quad aces)
        board = ["Ah", "Ac", "Ad", "As", "Kh"]

        # Player 1: 2-3
        p1_hole = ["2c", "3c"]
        p1_score, p1_rank = evaluator.evaluate_hand(p1_hole, board)

        # Player 2: 4-5
        p2_hole = ["4d", "5d"]
        p2_score, p2_rank = evaluator.evaluate_hand(p2_hole, board)

        # Both should have quad aces with King kicker
        assert p1_score == p2_score, "Scores should be identical"
        assert "Four of a Kind" in p1_rank or "Quads" in p1_rank.lower() or p1_rank == "Four of a Kind"
        print(f"  ✅ Both players have {p1_rank} (score: {p1_score})")
        print(f"  ✅ Pot splits evenly")

    def test_board_flush_kicker_matters(self):
        """When board has 4 cards same suit, hole card kicker wins."""
        print("\n[BOARD PLAYS] Testing board flush with kicker...")
        evaluator = HandEvaluator()

        # Board: K-Q-9-7-2 (four spades + one other)
        board = ["Ks", "Qs", "9s", "7s", "2c"]

        # Player 1: As-3c (has Ace of spades → A-K-Q-9-7 flush)
        p1_hole = ["As", "3c"]
        p1_score, p1_rank = evaluator.evaluate_hand(p1_hole, board)

        # Player 2: 8s-3d (has Eight of spades → K-Q-9-8-7 flush)
        p2_hole = ["8s", "3d"]
        p2_score, p2_rank = evaluator.evaluate_hand(p2_hole, board)

        # Both should have flush
        assert "Flush" in p1_rank
        assert "Flush" in p2_rank

        # P1 should win (A-K-Q-9-7 flush vs K-Q-9-8-7 flush)
        assert p1_score < p2_score, f"P1 (Ace kicker) should beat P2 (8 kicker): {p1_score} < {p2_score}"
        print(f"  ✅ P1 has better flush (Ace kicker)")
        print(f"  ✅ P1 score: {p1_score}, P2 score: {p2_score}")

    def test_board_full_house_kicker_matters(self):
        """Board with trips, kicker in hand determines winner."""
        print("\n[BOARD PLAYS] Testing board trips with kicker...")
        evaluator = HandEvaluator()

        # Board: K-K-K-9-7 (Trip Kings)
        board = ["Kh", "Kc", "Kd", "9s", "7h"]

        # Player 1: A-Q (makes full house K-K-K-A-Q, but only K-K-K-A-A if pairs Ace)
        # Actually with K-K-K on board and A-Q in hand, best is K-K-K-A-Q (trips with A-Q kickers)
        p1_hole = ["Ah", "Qc"]
        p1_score, p1_rank = evaluator.evaluate_hand(p1_hole, board)

        # Player 2: 8-6 (makes K-K-K-9-8)
        p2_hole = ["8d", "6s"]
        p2_score, p2_rank = evaluator.evaluate_hand(p2_hole, board)

        # P1 should win (better kickers)
        assert p1_score < p2_score, f"P1 (A-Q kickers) should beat P2 (9-8 kickers): {p1_score} < {p2_score}"
        print(f"  ✅ P1 has {p1_rank} (score: {p1_score})")
        print(f"  ✅ P2 has {p2_rank} (score: {p2_score})")
        print(f"  ✅ Kicker matters when board has trips")

    def test_board_pair_multiple_kickers(self):
        """Board with pair, hole cards don't improve - split pot."""
        print("\n[BOARD PLAYS] Testing board pair with no improvement...")
        evaluator = HandEvaluator()

        # Board: A-A-K-Q-9 (Pair of Aces, no straight possible)
        board = ["Ah", "Ac", "Kd", "Qh", "9s"]

        # Player 1: 8-7 (makes A-A-K-Q-9, 8 doesn't play)
        p1_hole = ["8h", "7c"]
        p1_score, p1_rank = evaluator.evaluate_hand(p1_hole, board)

        # Player 2: 6-5 (makes A-A-K-Q-9, 6 doesn't play)
        p2_hole = ["6d", "5s"]
        p2_score, p2_rank = evaluator.evaluate_hand(p2_hole, board)

        # Should be identical (board plays completely)
        assert p1_score == p2_score, f"Scores should be identical when board plays: {p1_score} vs {p2_score}"
        print(f"  ✅ Both have {p1_rank} (score: {p1_score})")
        print(f"  ✅ Hole cards don't improve hand, pot splits")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
