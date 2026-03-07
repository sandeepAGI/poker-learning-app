import random
from typing import List, Dict, Tuple, TYPE_CHECKING

from treys import Evaluator, Card

if TYPE_CHECKING:
    from game.poker_engine import Player


class HandEvaluator:
    """Hand evaluation using Treys library."""

    def __init__(self):
        self.evaluator = Evaluator()

    def evaluate_hand(self, hole_cards: List[str], community_cards: List[str]) -> Tuple[int, str]:
        """Evaluate hand strength."""
        # Convert to Treys format
        hole = [Card.new(card.replace("10", "T")) for card in hole_cards]
        board = [Card.new(card.replace("10", "T")) for card in community_cards]

        if len(board) + len(hole) >= 5:
            score = self.evaluator.evaluate(board, hole)
            rank = self.evaluator.get_rank_class(score)
            rank_str = self.evaluator.class_to_string(rank)
            return score, rank_str

        # Simple Monte Carlo for incomplete hands
        if len(board) < 5:
            remaining_deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
            # Remove known cards (player's perspective: only their cards + community)
            for card in hole_cards + community_cards:
                if card in remaining_deck:
                    remaining_deck.remove(card)

            scores = []
            for _ in range(100):  # Monte Carlo simulation (increased from 20 to 100 for accuracy)
                sim_deck = remaining_deck.copy()
                random.shuffle(sim_deck)
                sim_board = board + [Card.new(c.replace("10", "T")) for c in sim_deck[:5-len(board)]]
                scores.append(self.evaluator.evaluate(sim_board, hole))

            avg_score = sum(scores) / len(scores)
            rank = self.evaluator.get_rank_class(int(avg_score))
            rank_str = self.evaluator.class_to_string(rank)
            return avg_score, rank_str

        return 7500, "High Card"  # Default

    @staticmethod
    def score_to_strength(score: int) -> float:
        """
        Convert hand evaluator score to 0-1 strength value.
        SINGLE SOURCE OF TRUTH for hand strength calculation.

        Score ranges (lower is better, based on Treys evaluator):
        - 1-10: Royal Flush / Straight Flush
        - 11-166: Four of a Kind
        - 167-322: Full House
        - 323-1599: Flush
        - 1600-1609: Straight
        - 1610-2467: Three of a Kind
        - 2468-3325: Two Pair
        - 3326-6185: One Pair
        - 6186-7462: High Card

        Returns: float between 0.0 (worst) and 1.0 (best)
        """
        if score <= 10:
            return 0.95  # Royal Flush / Straight Flush
        elif score <= 166:
            return 0.90  # Four of a Kind
        elif score <= 322:
            return 0.85  # Full House
        elif score <= 1599:
            return 0.75  # Flush
        elif score <= 1609:
            return 0.65  # Straight
        elif score <= 2467:
            return 0.55  # Three of a Kind
        elif score <= 3325:
            return 0.45  # Two Pair
        elif score <= 6185:
            return 0.25  # One Pair
        else:
            return 0.05  # High Card

    def determine_winners_with_side_pots(
        self, players: List["Player"], community_cards: List[str]
    ) -> List[Dict]:
        """
        Determine winners with proper side pot handling.
        Returns list of pots with winners and amounts.
        Fixed: Bug #5 - Side pot implementation
        Fixed: Bug #3 - Optimization for simple cases (no side pots needed)
        """
        # Players who can win pots
        eligible_winners = [p for p in players if p.is_active or p.all_in]

        # Include ALL players (even folded) when calculating pot amounts
        all_players_with_investment = [p for p in players if p.total_invested > 0]
        total_pot = sum(p.total_invested for p in all_players_with_investment)

        if len(eligible_winners) <= 1:
            winner = eligible_winners[0] if eligible_winners else None
            if not winner:
                return []
            return [{
                'winners': [winner.player_id],
                'amount': total_pot,
                'type': 'main',
                'eligible_player_ids': [p.player_id for p in eligible_winners]
            }]

        # OPTIMIZATION (Bug #3): Simple pot when all eligible invested same
        eligible_investments = [p.total_invested for p in eligible_winners]
        if len(set(eligible_investments)) == 1:
            # All eligible players invested same amount - simple single pot
            hands = {}
            for player in eligible_winners:
                if player.hole_cards:
                    score, rank = self.evaluate_hand(
                        player.hole_cards, community_cards
                    )
                    hands[player.player_id] = (score, rank, player)

            if hands:
                best_score = min(hand[0] for hand in hands.values())
                winners = [
                    pid for pid, (score, rank, p) in hands.items()
                    if score == best_score
                ]
                return [{
                    'winners': winners,
                    'amount': total_pot,
                    'type': 'main',
                    'eligible_player_ids': [p.player_id for p in eligible_winners]
                }]

        # Build side pots (only when players have different investments)
        # CRITICAL FIX: Don't mutate player.total_invested - make a copy!
        # Bug: Function was called multiple times, each time reducing total_invested
        # causing chips to disappear
        investments = {p.player_id: p.total_invested for p in all_players_with_investment}
        pots = []

        while investments:
            # Find minimum investment among remaining players
            min_investment = min(inv for inv in investments.values() if inv > 0)
            if min_investment == 0:
                break

            # Create pot at this level - include ALL players' contributions
            pot_amount = 0
            pot_contributors = []  # All who contribute to this pot
            eligible_for_pot = []  # Only active/all-in can win

            for player in all_players_with_investment:
                if player.player_id not in investments:
                    continue

                contribution = min(investments[player.player_id], min_investment)
                pot_amount += contribution
                investments[player.player_id] -= contribution
                if contribution > 0:
                    pot_contributors.append(player)
                    # Only eligible winners can actually win this pot
                    if player in eligible_winners:
                        eligible_for_pot.append(player)

            # Evaluate hands for this pot (only among eligible winners)
            if eligible_for_pot:
                hands = {}
                for player in eligible_for_pot:
                    if player.hole_cards:
                        score, rank = self.evaluate_hand(player.hole_cards, community_cards)
                        hands[player.player_id] = (score, rank, player)

                if hands:
                    best_score = min(hand[0] for hand in hands.values())
                    winners = [pid for pid, (score, rank, player) in hands.items() if score == best_score]

                    pots.append({
                        'winners': winners,
                        'amount': pot_amount,
                        'type': 'main' if len(pots) == 0 else f'side_{len(pots)}',
                        'eligible_player_ids': [p.player_id for p in eligible_for_pot]
                    })

            # Remove players with zero investment
            investments = {pid: inv for pid, inv in investments.items() if inv > 0}

        return pots
