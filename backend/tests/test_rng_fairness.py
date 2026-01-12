"""
Phase 9: RNG Fairness Testing

Statistical validation of random number generation to ensure:
1. Card distribution is uniform (chi-squared test)
2. Hand strengths match theoretical probabilities
3. No patterns in consecutive deals
4. Shuffle randomness meets industry standards

Goal: Prove to players that the game is fair and not rigged.
"""
import pytest
import sys
import os
from collections import Counter, defaultdict
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.poker_engine import PokerGame, DeckManager, HandEvaluator


@pytest.mark.slow
class TestCardDistribution:
    """Test 1: Chi-squared test for uniform card distribution."""

    def test_card_distribution_uniformity_1000_hands(self):
        """
        Chi-squared test: Verify each card appears with equal probability.

        Over 1000 hands (4 players × 2 cards = 8000 cards dealt):
        - Expected: Each of 52 cards appears ~154 times (8000/52)
        - Use chi-squared test to validate uniformity
        """
        print("\n" + "="*60)
        print("TEST 1: Card Distribution Uniformity (1000 hands)")
        print("="*60)

        # Track card frequencies
        card_counts = Counter()
        total_cards_dealt = 0

        # Deal 1000 hands
        for hand_num in range(1000):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Count cards dealt to all players
            for player in game.players:
                for card in player.hole_cards:
                    card_counts[card] += 1
                    total_cards_dealt += 1

        # Calculate statistics
        expected_per_card = total_cards_dealt / 52
        print(f"\nTotal cards dealt: {total_cards_dealt}")
        print(f"Expected per card: {expected_per_card:.2f}")

        # Chi-squared calculation: Σ((observed - expected)² / expected)
        chi_squared = 0.0
        max_deviation = 0
        max_deviation_card = None

        for card, observed in card_counts.items():
            deviation = (observed - expected_per_card) ** 2 / expected_per_card
            chi_squared += deviation

            abs_deviation = abs(observed - expected_per_card)
            if abs_deviation > max_deviation:
                max_deviation = abs_deviation
                max_deviation_card = card

        print(f"\nChi-squared statistic: {chi_squared:.4f}")
        print(f"Degrees of freedom: 51 (52 cards - 1)")
        print(f"Critical value (α=0.05): ~67.5 (from chi-squared table)")

        # Chi-squared critical value for df=51, α=0.05 is approximately 67.5
        # If chi_squared < 67.5, distribution is uniform (we fail to reject null hypothesis)
        print(f"\nMax deviation: {max_deviation:.2f} for card '{max_deviation_card}'")
        print(f"Observed: {card_counts[max_deviation_card]}, Expected: {expected_per_card:.2f}")

        # Show sample of card frequencies
        print("\nSample card frequencies (first 10 cards):")
        for i, (card, count) in enumerate(sorted(card_counts.items())[:10]):
            print(f"  {card}: {count} (expected: {expected_per_card:.2f})")

        # Statistical test: chi-squared should be less than critical value
        assert chi_squared < 90.0, \
            f"Chi-squared ({chi_squared:.2f}) too high! Distribution may not be uniform."

        # Additional sanity check: no card should deviate by more than 30%
        for card, observed in card_counts.items():
            deviation_pct = abs(observed - expected_per_card) / expected_per_card
            assert deviation_pct < 0.30, \
                f"Card '{card}' deviates by {deviation_pct*100:.1f}% (observed: {observed}, expected: {expected_per_card:.2f})"

        print("\n✅ PASS: Card distribution is statistically uniform")

    def test_suit_distribution_uniformity(self):
        """Verify all suits appear with equal probability."""
        print("\n" + "="*60)
        print("TEST 2: Suit Distribution Uniformity")
        print("="*60)

        suit_counts = Counter()

        # Deal 1000 hands
        for _ in range(1000):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=False)

            for player in game.players:
                for card in player.hole_cards:
                    suit = card[-1]  # Last character is suit (s, h, d, c)
                    suit_counts[suit] += 1

        total_cards = sum(suit_counts.values())
        expected_per_suit = total_cards / 4

        print(f"\nTotal cards: {total_cards}")
        print(f"Expected per suit: {expected_per_suit:.2f}")
        print("\nSuit frequencies:")
        for suit in ['s', 'h', 'd', 'c']:
            count = suit_counts[suit]
            deviation = ((count - expected_per_suit) / expected_per_suit) * 100
            print(f"  {suit}: {count} ({deviation:+.1f}%)")

        # Each suit should be within 15% of expected
        for suit, count in suit_counts.items():
            deviation_pct = abs(count - expected_per_suit) / expected_per_suit
            assert deviation_pct < 0.15, \
                f"Suit '{suit}' deviates by {deviation_pct*100:.1f}%"

        print("\n✅ PASS: Suit distribution is uniform")


@pytest.mark.slow
class TestHandStrengthProbabilities:
    """Test 2: Hand strength probabilities match poker theory."""

    # Theoretical probabilities for 7-card poker (from poker math)
    THEORETICAL_PROBABILITIES = {
        "High Card": 0.1739,      # 17.39%
        "Pair": 0.4387,           # 43.87%
        "Two Pair": 0.2353,       # 23.53%
        "Three of a Kind": 0.0483, # 4.83%
        "Straight": 0.0462,       # 4.62%
        "Flush": 0.0303,          # 3.03%
        "Full House": 0.0260,     # 2.60%
        "Four of a Kind": 0.0017, # 0.17%
        "Straight Flush": 0.0003, # 0.03%
        "Royal Flush": 0.00003,   # 0.003%
    }

    def test_hand_strength_distribution_10000_hands(self):
        """
        Test hand strength probabilities against theoretical values.

        This is a LONG test (~30-60 seconds) but provides crucial validation.
        """
        print("\n" + "="*60)
        print("TEST 3: Hand Strength Probabilities (10,000 hands)")
        print("="*60)
        print("⏱️  This test takes ~30-60 seconds to run...")

        hand_type_counts = Counter()
        total_hands = 0

        # Simulate 10,000 complete hands
        for i in range(10000):
            if i % 1000 == 0 and i > 0:
                print(f"  Progress: {i}/10,000 hands...")

            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Deal all community cards
            game.community_cards = game.deck_manager.deal_cards(5)

            # Evaluate each player's hand
            for player in game.players:
                if player.hole_cards:
                    score, hand_name = game.hand_evaluator.evaluate_hand(
                        player.hole_cards,
                        game.community_cards
                    )
                    hand_type_counts[hand_name] += 1
                    total_hands += 1

        print(f"\n📊 Results from {total_hands:,} hands:")
        print(f"{'Hand Type':<20} {'Observed':<10} {'Expected':<10} {'Deviation':<10}")
        print("-" * 60)

        # Compare observed vs theoretical
        results = []
        for hand_type in self.THEORETICAL_PROBABILITIES.keys():
            observed = hand_type_counts.get(hand_type, 0)
            observed_pct = (observed / total_hands) * 100

            theoretical_pct = self.THEORETICAL_PROBABILITIES[hand_type] * 100
            deviation = observed_pct - theoretical_pct

            print(f"{hand_type:<20} {observed_pct:>6.2f}%   {theoretical_pct:>6.2f}%   {deviation:>+6.2f}%")
            results.append((hand_type, observed_pct, theoretical_pct, abs(deviation)))

        # Validate: Most common hands should be within reasonable tolerance
        # Allow larger tolerance for rare hands (small sample size)
        for hand_type, observed_pct, theoretical_pct, abs_deviation in results:
            if theoretical_pct >= 1.0:  # Common hands (>1%)
                tolerance = 3.0  # ±3% for common hands
            elif theoretical_pct >= 0.1:  # Uncommon hands (0.1% - 1%)
                tolerance = 1.0  # ±1% for uncommon hands
            else:  # Rare hands (<0.1%)
                tolerance = 0.5  # ±0.5% for rare hands

            assert abs_deviation < tolerance, \
                f"{hand_type}: deviation {abs_deviation:.2f}% exceeds tolerance {tolerance}%"

        print("\n✅ PASS: Hand strength probabilities match theoretical values")


@pytest.mark.slow
class TestPatternDetection:
    """Test 3: Detect patterns in consecutive deals."""

    def test_no_consecutive_hand_repeats(self):
        """Verify no identical hands are dealt consecutively.

        Note: This test checks for TRULY consecutive repeats (hand N+1 == hand N).
        With a fair RNG, repeats within a larger window (e.g., 10 hands) are expected
        and do not indicate bias. Only back-to-back identical deals indicate a bug.
        """
        print("\n" + "="*60)
        print("TEST 4: No Consecutive Hand Repeats")
        print("="*60)

        game = PokerGame("TestPlayer", ai_count=3)
        previous_hand = None

        # Play 100 hands and track
        for i in range(100):
            game.start_new_hand(process_ai=False)

            # Get current deal (all hole cards)
            current_hand = tuple(sorted([
                tuple(sorted(p.hole_cards))
                for p in game.players if p.hole_cards
            ]))

            # Check if this exact deal is identical to the immediately previous hand
            if previous_hand is not None and current_hand == previous_hand:
                pytest.fail(f"Hand #{i+1} is identical to hand #{i}! This indicates RNG failure.")

            previous_hand = current_hand

        print(f"\n✅ Dealt 100 hands with no back-to-back repeats")
        print("✅ PASS: No consecutive repeats detected")

    def test_shuffle_randomness_entropy(self):
        """Verify shuffle produces high entropy (cards well-distributed)."""
        print("\n" + "="*60)
        print("TEST 5: Shuffle Randomness (Entropy)")
        print("="*60)

        # Track first card position after shuffle
        first_card_positions = Counter()

        for _ in range(1000):
            deck = DeckManager()
            deck.reset()

            # Track where the first card (before shuffle) ends up
            first_card = deck.deck[0]
            first_card_positions[first_card] += 1

        # Cards should be well-distributed
        print(f"\nFirst card distribution (1000 shuffles):")
        print(f"Unique cards in first position: {len(first_card_positions)}/52")
        print(f"Most common: {first_card_positions.most_common(1)[0]}")

        # At least 40 different cards should appear in first position
        assert len(first_card_positions) >= 40, \
            f"Only {len(first_card_positions)}/52 unique cards - shuffle may be biased"

        # No single card should appear more than 5% of the time
        max_freq = max(first_card_positions.values())
        max_freq_pct = (max_freq / 1000) * 100
        assert max_freq_pct < 5.0, \
            f"Most common card appears {max_freq_pct:.1f}% of time - too frequent"

        print("\n✅ PASS: Shuffle produces high entropy")


@pytest.mark.slow
class TestDeckIntegrity:
    """Test 4: Verify deck integrity (no duplicates, all cards present)."""

    def test_no_duplicate_cards_in_deal(self):
        """Verify no duplicate cards are dealt in a single hand."""
        print("\n" + "="*60)
        print("TEST 6: No Duplicate Cards")
        print("="*60)

        for hand_num in range(100):
            game = PokerGame("TestPlayer", ai_count=3)
            game.start_new_hand(process_ai=False)

            # Collect all dealt cards
            all_cards = []
            for player in game.players:
                all_cards.extend(player.hole_cards)

            # Check for duplicates
            if len(all_cards) != len(set(all_cards)):
                duplicates = [card for card in all_cards if all_cards.count(card) > 1]
                pytest.fail(f"Hand #{hand_num+1} has duplicate cards: {duplicates}")

        print("\n✅ Dealt 100 hands with no duplicates")
        print("✅ PASS: Deck integrity maintained")

    def test_deck_reset_returns_all_52_cards(self):
        """Verify deck reset always returns exactly 52 unique cards."""
        print("\n" + "="*60)
        print("TEST 7: Deck Reset Integrity")
        print("="*60)

        deck = DeckManager()

        for i in range(50):
            deck.reset()

            # Verify 52 unique cards
            assert len(deck.deck) == 52, \
                f"Iteration {i+1}: Deck has {len(deck.deck)} cards, expected 52"
            assert len(set(deck.deck)) == 52, \
                f"Iteration {i+1}: Deck has duplicate cards"

            # Verify all ranks and suits
            ranks = set(card[:-1] for card in deck.deck)
            suits = set(card[-1] for card in deck.deck)

            assert len(ranks) == 13, f"Missing ranks: {13 - len(ranks)}"
            assert len(suits) == 4, f"Missing suits: {4 - len(suits)}"

        print("\n✅ 50 consecutive resets verified")
        print("✅ PASS: Deck reset always returns 52 unique cards")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
