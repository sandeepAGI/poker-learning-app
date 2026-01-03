# Poker Game Engine - Bug Fixes Applied
# Fixed: Turn order, fold resolution, raise validation, raise accounting, side pots
import random
import json
import uuid  # FIX Issue #3: Generate unique IDs for AI decisions
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from treys import Evaluator, Card

# Memory management constants
MAX_HAND_EVENTS_HISTORY = 1000  # Keep last ~10-20 hands worth of events

class GameState(Enum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

@dataclass
class HandEvent:
    """Track events that happen during a hand for learning."""
    timestamp: str
    event_type: str  # "deal", "bet", "fold", "call", "raise", "showdown"
    player_id: str
    action: str
    amount: int = 0
    hand_strength: float = 0.0
    reasoning: str = ""
    pot_size: int = 0
    current_bet: int = 0

@dataclass
class AIDecision:
    """AI decision with reasoning for transparency."""
    action: str
    amount: int
    reasoning: str
    hand_strength: float
    pot_odds: float
    confidence: float
    spr: float = 0.0  # Stack-to-Pot Ratio for pot-relative decision making
    decision_id: str = ""  # FIX Issue #3: Unique ID for deduplication (generated on creation)

@dataclass
class ActionRecord:
    """Single action in a betting round - Phase 3."""
    player_id: str
    player_name: str
    action: str  # fold, call, raise, check, all-in
    amount: int
    stack_before: int
    stack_after: int
    pot_before: int
    pot_after: int
    reasoning: str = ""  # AI reasoning if available

@dataclass
class BettingRound:
    """All actions in a single betting round - Phase 3."""
    round_name: str  # pre_flop, flop, turn, river
    community_cards: List[str]  # Cards visible at this stage
    actions: List[ActionRecord] = field(default_factory=list)
    pot_at_start: int = 0
    pot_at_end: int = 0

@dataclass
class CompletedHand:
    """Store completed hand for analysis."""
    hand_number: int
    community_cards: List[str]
    pot_size: int
    winner_ids: List[str]
    winner_names: List[str]
    human_action: str  # fold, call, raise, all-in
    human_cards: List[str]
    human_final_stack: int
    human_hand_strength: float
    human_pot_odds: float  # When they made their final decision
    ai_decisions: Dict[str, AIDecision]  # player_id -> their decision
    events: List[HandEvent]  # All events in the hand
    analysis_available: bool = True

    # Phase 3: Session tracking and detailed history
    session_id: str = ""  # UUID for the play session
    timestamp: str = ""  # When hand was played (ISO format)
    betting_rounds: List[BettingRound] = field(default_factory=list)  # Round-by-round actions
    showdown_hands: Dict[str, List[str]] = field(default_factory=dict)  # player_id -> cards revealed
    hand_rankings: Dict[str, str] = field(default_factory=dict)  # player_id -> hand rank (pair, flush, etc.)

@dataclass
class Player:
    player_id: str
    name: str
    stack: int = 1000
    hole_cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0  # Bet in current betting round
    total_invested: int = 0  # Total invested in hand (for side pots)
    all_in: bool = False
    is_human: bool = False
    personality: str = ""
    has_acted: bool = False  # Track if player has acted this round

    def bet(self, amount: int) -> int:
        """Place a bet, reducing stack. Fixed: proper accounting + all-in handling."""
        if amount >= self.stack:
            # Betting entire stack or more - mark as all-in
            amount = self.stack
            self.all_in = True

        self.stack -= amount
        self.current_bet += amount
        self.total_invested += amount

        # Double-check: if stack is now 0, definitely all-in
        if self.stack == 0 and self.current_bet > 0:
            self.all_in = True

        return amount

    def reset_for_new_hand(self):
        """Reset player for new hand."""
        self.current_bet = 0
        self.total_invested = 0
        self.all_in = False
        self.hole_cards = []
        self.has_acted = False
        self.is_active = self.stack >= 5  # Reactivate if they have chips

    def reset_for_new_round(self):
        """Reset for new betting round."""
        self.current_bet = 0
        self.has_acted = False

class DeckManager:
    """Simple deck management."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Create and shuffle a new deck."""
        self.deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(self.deck)

    def deal_cards(self, num_cards: int) -> List[str]:
        """Deal specified number of cards."""
        if num_cards > len(self.deck):
            raise ValueError(f"Not enough cards: need {num_cards}, have {len(self.deck)}")

        cards = self.deck[:num_cards]
        self.deck = self.deck[num_cards:]
        return cards

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
        self, players: List[Player], community_cards: List[str]
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

class AIStrategy:
    """AI strategies with decision reasoning for learning."""

    @staticmethod
    def make_decision_with_reasoning(personality: str, hole_cards: List[str], community_cards: List[str],
                                   current_bet: int, pot_size: int, player_stack: int, player_bet: int = 0,
                                   big_blind: int = 10, last_raise_amount: Optional[int] = None) -> AIDecision:
        """
        Make AI decision with full reasoning for transparency.
        Fixed: Uses last_raise_amount for correct minimum raise calculation per Texas Hold'em rules
        """

        # Calculate minimum raise increment (Texas Hold'em rule)
        min_raise_increment = last_raise_amount if last_raise_amount is not None else big_blind

        # Hand strength calculation
        evaluator = HandEvaluator()
        hand_score, hand_rank = evaluator.evaluate_hand(hole_cards, community_cards)

        # Use consolidated hand strength calculation
        hand_strength = HandEvaluator.score_to_strength(hand_score)

        # Pot odds calculation
        call_amount = current_bet - player_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0

        # SPR (Stack-to-Pot Ratio) calculation - key poker metric for pot-relative decisions
        # Use 999.0 instead of infinity for JSON compatibility
        spr = player_stack / pot_size if pot_size > 0 else 999.0

        if personality == "Conservative":
            # SPR-aware Conservative: Tighter with deep stacks, more committed with shallow stacks
            if spr < 3 and hand_strength >= 0.45:  # Low SPR - pot-committed with two pair+
                action = "raise" if random.random() > 0.3 else "call"
                # FIX: Don't use max with player_stack, just calculate min raise and cap it
                amount = (current_bet + min_raise_increment) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Low SPR ({spr:.1f}) - pot committed with {hand_rank} ({hand_strength:.1%})"
                confidence = 0.85
            elif spr > 10 and hand_strength < 0.65:  # High SPR - need premium hands
                action = "fold"
                amount = 0
                reasoning = f"High SPR ({spr:.1f}) - need premium hand, folding {hand_rank} ({hand_strength:.1%})"
                confidence = 0.8
            elif hand_strength >= 0.75:  # Flush or better
                action = "raise" if random.random() > 0.3 else "call"
                amount = max(current_bet + min_raise_increment, current_bet * 2) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Premium hand ({hand_rank}, {hand_strength:.1%}). Conservative value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, {hand_strength:.1%}). Conservative call."
                confidence = 0.7
            elif hand_strength >= 0.25 and call_amount <= player_stack // 20:
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, {hand_strength:.1%}). Small bet, worth a call."
                confidence = 0.5
            else:
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}, {hand_strength:.1%}). Conservative fold."
                confidence = 0.9

        elif personality == "Aggressive":
            # SPR-aware Aggressive: Push/fold with low SPR, bluff more with high SPR
            if spr < 3 and hand_strength >= 0.25:  # Low SPR - any pair, push/fold
                action = "raise"
                amount = player_stack  # All-in or near all-in
                reasoning = f"Low SPR ({spr:.1f}) - aggressive push with {hand_rank} ({hand_strength:.1%})"
                confidence = 0.75
            elif spr > 7 and hand_strength < 0.25:  # High SPR - more bluffs
                bluff_chance = 0.4 if call_amount <= player_stack // 20 else 0.2
                if random.random() < bluff_chance:
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"High SPR ({spr:.1f}) - applying pressure with weak {hand_rank}. Bluff play."
                    confidence = 0.4
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"High SPR ({spr:.1f}) - weak hand ({hand_rank}), conserving chips for better spots."
                    confidence = 0.7
            elif hand_strength >= 0.55:  # Three of a kind or better
                action = "raise" if random.random() > 0.2 else "call"
                amount = max(current_bet + min_raise_increment, current_bet * 3) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Aggressive value betting."
                confidence = 0.8
            elif hand_strength >= 0.25:  # Any pair
                if random.random() > 0.4:
                    action = "raise" if random.random() > 0.6 else "call"
                    amount = max(current_bet + min_raise_increment, current_bet * 2) if action == "raise" else call_amount
                    amount = min(amount, player_stack)
                    reasoning = f"Playable hand ({hand_rank}, {hand_strength:.1%}). Aggressive play to build pot."
                    confidence = 0.6
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Marginal hand ({hand_rank}). Aggressive fold to control pot size."
                    confidence = 0.5
            else:  # High card
                if random.random() > 0.7 and call_amount <= player_stack // 40:
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"Weak hand ({hand_rank}) but bluffing for fold equity. Aggressive move."
                    confidence = 0.3
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Too weak to continue ({hand_rank}, {hand_strength:.1%}). Smart aggression."
                    confidence = 0.8

        elif personality == "Mathematical":
            # SPR + pot odds combined for optimal EV decisions
            implied_odds_factor = min(spr * pot_odds, 1.0) if spr < 999.0 else pot_odds

            if spr < 3 and hand_strength >= 0.25:  # Low SPR - committed with any pair
                action = "call" if call_amount < player_stack else "raise"
                amount = call_amount if action == "call" else player_stack
                reasoning = f"Low SPR ({spr:.1f}) - pot committed with {hand_rank}. Positive EV."
                confidence = 0.85
            elif hand_strength >= 0.65:  # Straight or better
                action = "raise"
                amount = max(current_bet + min_raise_increment, current_bet * 2)
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Mathematical value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, {hand_strength:.1%}). Positive expectation call."
                confidence = 0.8
            elif hand_strength >= 0.25 and (pot_odds <= 0.33 or spr < 5):
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, {hand_strength:.1%}). Pot odds {pot_odds:.1%}, SPR {spr:.1f} - positive EV."
                confidence = 0.6
            elif hand_strength >= 0.25:
                action = "fold"
                amount = 0
                reasoning = f"Pair ({hand_rank}). Pot odds {pot_odds:.1%}, SPR {spr:.1f} - negative EV fold."
                confidence = 0.8
            else:
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}, {hand_strength:.1%}). Clear mathematical fold."
                confidence = 0.95

        elif personality == "Loose-Passive":
            # Calling station - calls too much, rarely raises or bluffs
            if hand_strength >= 0.20:  # Any pair or better
                if spr < 3:  # Low SPR - call to see showdown
                    action = "call"
                    amount = call_amount
                    reasoning = f"Low SPR ({spr:.1f}) - calling with {hand_rank}. Loose-passive play."
                    confidence = 0.6
                elif current_bet > player_stack // 3:  # Too expensive
                    action = "fold"
                    amount = 0
                    reasoning = f"Too expensive ({hand_rank}). Even calling stations fold sometimes."
                    confidence = 0.7
                else:  # Default: call almost everything
                    action = "call"
                    amount = call_amount
                    reasoning = f"Calling with {hand_rank} ({hand_strength:.1%}). Loose-passive style."
                    confidence = 0.5
            else:  # Even calling stations fold high card sometimes
                if call_amount <= player_stack // 40:  # Very small bet
                    action = "call"
                    amount = call_amount
                    reasoning = f"Small bet, worth a call with {hand_rank}. Loose play."
                    confidence = 0.4
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Weak hand ({hand_rank}). Fold."
                    confidence = 0.8

        elif personality == "Tight-Aggressive":
            # TAG - premium hands only, but aggressive when playing
            if hand_strength >= 0.75:  # Flush or better - premium
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size)
                amount = min(amount, player_stack)
                reasoning = f"Premium hand ({hand_rank}, {hand_strength:.1%}). TAG value betting."
                confidence = 0.95
            elif hand_strength >= 0.55:  # Three of a kind - solid
                if spr < 5:  # Low SPR - go all-in
                    action = "raise"
                    amount = player_stack
                    reasoning = f"Low SPR ({spr:.1f}), strong hand ({hand_rank}). TAG push."
                    confidence = 0.9
                else:  # Raise for value
                    action = "raise"
                    amount = max(current_bet + min_raise_increment, current_bet * 2)
                    amount = min(amount, player_stack)
                    reasoning = f"Strong hand ({hand_rank}). TAG value raise."
                    confidence = 0.85
            elif hand_strength >= 0.35:  # Marginal hands - fold
                action = "fold"
                amount = 0
                reasoning = f"Below TAG threshold ({hand_rank}, {hand_strength:.1%}). Fold."
                confidence = 0.8
            else:  # Weak hands - always fold
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}). TAG disciplined fold."
                confidence = 0.95

        elif personality == "Maniac":
            # Hyper-aggressive - raises almost always
            if hand_strength >= 0.45:  # Two pair or better
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size * 2)
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}). Maniac value aggression!"
                confidence = 0.7
            elif random.random() < 0.70:  # 70% bluff frequency
                action = "raise"
                amount = max(current_bet + min_raise_increment, pot_size)
                amount = min(amount, player_stack)
                reasoning = f"Bluffing with {hand_rank}. Maniac pressure play!"
                confidence = 0.3
            else:  # Occasionally calls to vary play
                if call_amount < player_stack // 2:
                    action = "call"
                    amount = call_amount
                    reasoning = f"Calling with {hand_rank} to vary play. Maniac style."
                    confidence = 0.4
                else:  # Too expensive even for maniac
                    action = "fold"
                    amount = 0
                    reasoning = f"Too expensive. Even maniacs fold sometimes."
                    confidence = 0.6

        else:
            # Default Conservative
            action = "call" if hand_strength > 0.4 else "fold"
            amount = call_amount if action == "call" else 0
            reasoning = f"Default strategy: {action} with {hand_strength:.1%} hand strength."
            confidence = 0.5

        return AIDecision(
            action=action,
            amount=amount,
            reasoning=reasoning,
            hand_strength=hand_strength,
            pot_odds=pot_odds,
            confidence=confidence,
            spr=spr,
            decision_id=str(uuid.uuid4())  # FIX Issue #3: Unique ID for reliable deduplication
        )

class PokerGame:
    """Main poker game class with bug fixes applied."""

    def __init__(self, human_player_name: str, ai_count: int = 3):
        """
        Create a new poker game.

        Args:
            human_player_name: Name of the human player
            ai_count: Number of AI opponents (1-5, default 3 for 4-player table)
        """
        if ai_count < 1 or ai_count > 5:
            raise ValueError("AI count must be between 1 and 5")

        self.deck_manager = DeckManager()
        self.hand_evaluator = HandEvaluator()

        # Create human player
        self.players = [Player("human", human_player_name, is_human=True)]

        # Add AI players dynamically with creative AI pun names (30 names for 5-AI support)
        ai_name_pool = [
            # Classic AI puns
            "AI-ce", "AI-ron", "AI-nstein",
            # Tech/Science themed
            "Chip Checker", "The Algorithm", "Beta Bluffer", "Neural Net",
            "Deep Blue", "Data Dealer", "Binary Bob", "Quantum Quinn",
            # Poker themed
            "All-In Annie", "Fold Franklin", "Raise Rachel", "Call Carl",
            "Bluff Master", "The Calculator", "Lady Luck", "Card Shark",
            # Personality themed
            "Cool Hand Luke", "The Professor", "Wild Card", "Stone Face",
            "The Grinder", "Risk Taker", "The Rock", "Loose Lucy",
            # Phase 5: Added 2 more names for 30 total (supports 5 AI opponents)
            "The Oracle", "Monte Carlo"
        ]

        # Randomly select unique names for AI players
        import random
        selected_names = random.sample(ai_name_pool, min(ai_count, len(ai_name_pool)))

        # Phase 5: Random personality assignment from expanded pool (6 personalities)
        all_personalities = [
            "Conservative",
            "Aggressive",
            "Mathematical",
            "Loose-Passive",
            "Tight-Aggressive",
            "Maniac"
        ]
        # Randomly assign personalities (no duplicates in same game)
        selected_personalities = random.sample(all_personalities, min(ai_count, len(all_personalities)))

        for i in range(ai_count):
            self.players.append(
                Player(
                    player_id=f"ai{i+1}",
                    name=selected_names[i],
                    personality=selected_personalities[i]  # Random unique personality
                )
            )

        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        self.dealer_index = 0
        self.small_blind_index: Optional[int] = None  # FIX-01: Track SB position for frontend
        self.big_blind_index: Optional[int] = None    # FIX-01: Track BB position for frontend
        self.hand_count = 0
        self.big_blind = 10
        self.small_blind = 5

        # Blind escalation (Issue #1 fix)
        self.blind_escalation_enabled = True  # Enable/disable blind increases
        self.hands_per_blind_level = 10  # Increase blinds every 10 hands
        self.blind_multiplier = 2.0  # Double blinds each level (5/10 → 10/20 → 20/40)

        # Fixed: Bug #1 - Turn order tracking
        self.current_player_index = 0
        self.last_raiser_index = None
        self.last_raise_amount = None  # Track size of last raise for minimum raise calculation

        # Learning features
        self.hand_events: List[HandEvent] = []
        self.current_hand_events: List[HandEvent] = []
        self.last_ai_decisions: Dict[str, AIDecision] = {}

        # Hand history for analysis (UX Phase 2)
        self.completed_hands: List[CompletedHand] = []
        self.last_hand_summary: Optional[CompletedHand] = None

        # Phase 3: Hand history infrastructure
        import uuid
        from datetime import datetime
        self.session_id = str(uuid.uuid4())  # Generate unique session ID
        self.hand_history: List[CompletedHand] = []  # Store all hands (max 100)

        # Phase 3: Current hand tracking for detailed history
        self._current_round_actions: List[ActionRecord] = []
        self._hand_betting_rounds: List[BettingRound] = []
        self._pot_at_round_start = 0

        # QC: Enable runtime assertions for poker rule validation
        self.qc_enabled = True  # Set to False to disable for performance
        self.total_chips = sum(p.stack for p in self.players) + self.pot  # Track expected total

    # ========================================================================
    # QC RUNTIME ASSERTIONS - Phase 1: Catch bugs immediately
    # ========================================================================

    def _assert_chip_conservation(self, context: str = ""):
        """
        Assert that total chips always equal $4000.
        This is THE fundamental invariant of poker - chips cannot be created or destroyed.

        If this fails, a critical bug has occurred and the game is corrupt.
        """
        if not self.qc_enabled:
            return

        total = sum(p.stack for p in self.players) + self.pot
        if total != self.total_chips:
            # Build detailed error message
            stacks_info = ", ".join([f"{p.name}=${p.stack}" for p in self.players])
            raise RuntimeError(
                f"🚨 CHIP CONSERVATION VIOLATED {context}\n"
                f"   Total: ${total} (Expected: ${self.total_chips})\n"
                f"   Missing: ${self.total_chips - total}\n"
                f"   Pot: ${self.pot}\n"
                f"   Stacks: {stacks_info}\n"
                f"   State: {self.current_state.value}\n"
                f"   This is a CRITICAL BUG - chips disappeared or were created!"
            )

    def _assert_valid_game_state(self, context: str = ""):
        """
        Assert that game state is valid.
        Checks multiple invariants that should always be true.
        ENHANCED: Now checks all-in logic, current player validity, and more.
        """
        if not self.qc_enabled:
            return

        errors = []

        # 1. Pot should never be negative
        if self.pot < 0:
            errors.append(f"Pot is negative: ${self.pot}")

        # 2. Current bet should never be negative
        if self.current_bet < 0:
            errors.append(f"Current bet is negative: ${self.current_bet}")

        # 3. Player stacks should never be negative
        for p in self.players:
            if p.stack < 0:
                errors.append(f"{p.name} has negative stack: ${p.stack}")

        # 4. Player current_bet should never be negative
        for p in self.players:
            if p.current_bet < 0:
                errors.append(f"{p.name} has negative current_bet: ${p.current_bet}")

        # 5. Player total_invested should never be negative (NEW)
        for p in self.players:
            if p.total_invested < 0:
                errors.append(f"{p.name} has negative total_invested: ${p.total_invested}")

        # 6. Active players should have non-negative stacks or be all-in
        for p in self.players:
            if p.is_active and p.stack < 0:
                errors.append(f"Active player {p.name} has negative stack: ${p.stack}")

        # 7. All-in consistency checks (NEW - would have caught the all-in bug!)
        for p in self.players:
            # If marked all-in, stack must be 0
            if p.all_in and p.stack > 0:
                errors.append(f"{p.name} marked all-in but has ${p.stack} remaining")

            # If stack is 0 and player is active with a bet, must be all-in
            if p.stack == 0 and p.is_active and p.total_invested > 0 and not p.all_in:
                errors.append(f"{p.name} has $0 stack and active with bet ${p.total_invested} but NOT marked all-in")

        # 8. Current player validation (NEW - critical for turn order)
        if self.current_state not in [GameState.SHOWDOWN]:
            if self.current_player_index is not None:
                current = self.players[self.current_player_index]

                # Current player must be active
                if not current.is_active:
                    errors.append(f"Current player {current.name} is not active (index={self.current_player_index})")

                # Current player cannot be all-in (NEW - would have caught the bug!)
                if current.all_in:
                    errors.append(f"Current player {current.name} is all-in but marked as current (index={self.current_player_index})")

                # Current player must have chips if not all-in
                if current.stack == 0 and not current.all_in:
                    errors.append(f"Current player {current.name} has $0 but not all-in (index={self.current_player_index})")

        # 9. At showdown, pot should be 0 (already awarded)
        if self.current_state == GameState.SHOWDOWN and self.pot > 0:
            errors.append(f"At SHOWDOWN but pot not awarded: ${self.pot}")

        # 10. If only 0-1 active players during hand play (not at start), should be at SHOWDOWN
        # NOTE: At PRE_FLOP start, busted players from previous hands are inactive - this is valid
        active_count = sum(1 for p in self.players if p.is_active)
        if active_count <= 1 and self.current_state != GameState.SHOWDOWN and self.current_state != GameState.PRE_FLOP:
            errors.append(f"Only {active_count} active players but not at SHOWDOWN (state: {self.current_state.value})")

        # 11. Betting round consistency (NEW)
        if self.current_state in [GameState.PRE_FLOP, GameState.FLOP, GameState.TURN, GameState.RIVER]:
            active_not_all_in = [p for p in self.players if p.is_active and not p.all_in]

            # If multiple players can act, must have a current player
            if len(active_not_all_in) > 1 and self.current_player_index is None:
                errors.append(f"{len(active_not_all_in)} active players can act but no current player set")

        if errors:
            error_msg = "\n   ".join(errors)
            raise RuntimeError(
                f"🚨 INVALID GAME STATE {context}\n"
                f"   {error_msg}\n"
                f"   This is a CRITICAL BUG - game rules violated!"
            )

    # ========================================================================
    # End QC Assertions
    # ========================================================================

    def _log_hand_event(self, event_type: str, player_id: str, action: str,
                       amount: int = 0, hand_strength: float = 0.0, reasoning: str = ""):
        """Log a hand event for learning analysis."""
        event = HandEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            player_id=player_id,
            action=action,
            amount=amount,
            hand_strength=hand_strength,
            reasoning=reasoning,
            pot_size=self.pot,
            current_bet=self.current_bet
        )
        self.current_hand_events.append(event)

    def _get_next_active_player_index(self, start_index: int) -> Optional[int]:
        """Get next active player index who can act. Fixed: Bug #1."""
        for i in range(len(self.players)):
            idx = (start_index + i) % len(self.players)
            player = self.players[idx]
            if player.is_active and not player.all_in:
                return idx
        return None

    def _betting_round_complete(self) -> bool:
        """Check if betting round is complete. Fixed: Bug #1 + BB option."""
        active_players = [p for p in self.players if p.is_active and not p.all_in]
        all_active_players = [p for p in self.players if p.is_active]  # Including all-in

        # If 0 active non-all-in players (everyone folded or all-in), round is complete
        if len(active_players) == 0:
            return True

        # If only 1 non-all-in player remains:
        # - If others are all-in (len(all_active_players) > 1), this player needs to act
        # - If others have folded (len(all_active_players) == 1), pot goes to winner - complete
        if len(active_players) == 1:
            if len(all_active_players) > 1:
                # Others are all-in, this player still needs to act
                return active_players[0].has_acted
            else:
                # All others folded, this player wins - round is complete
                return True

        # All active players must have acted and matched the current bet
        for player in active_players:
            if not player.has_acted:
                return False
            if player.current_bet != self.current_bet:
                return False

        # BB OPTION: Pre-flop, BB gets option to raise even if everyone just called
        if self.current_state == GameState.PRE_FLOP and self.last_raiser_index is not None:
            bb_player = self.players[self.last_raiser_index]
            # BB gets option if: active, not all-in, and hasn't made an action beyond posting blind
            if bb_player.is_active and not bb_player.all_in:
                # Count BB's actual actions (not blind posting)
                bb_action_count = sum(1 for e in self.current_hand_events
                                     if e.player_id == bb_player.player_id
                                     and e.event_type == "action"
                                     and e.action in ["check", "call", "raise", "fold"])
                # If BB hasn't acted yet (only posted blind), round is not complete
                if bb_action_count == 0:
                    return False

        return True

    def _maybe_increase_blinds(self):
        """Increase blinds if blind escalation is enabled and threshold reached (Issue #1 fix)."""
        if not self.blind_escalation_enabled:
            return

        # Check if we should increase blinds (every N hands, starting after the first N hands)
        # hand_count is incremented before this is called
        # Increase at hand 11, 21, 31, etc. (after 10, 20, 30 hands complete)
        if self.hand_count > self.hands_per_blind_level and (self.hand_count - 1) % self.hands_per_blind_level == 0:
            old_sb = self.small_blind
            old_bb = self.big_blind

            # Increase blinds
            self.small_blind = int(self.small_blind * self.blind_multiplier)
            self.big_blind = int(self.big_blind * self.blind_multiplier)

            # Log blind increase event
            self._log_hand_event("blind_increase", "system", "increase", 0, 0.0,
                               f"Blinds increased from ${old_sb}/${old_bb} to ${self.small_blind}/${self.big_blind}")

    def start_new_hand(self, process_ai: bool = True):
        """
        Start a new poker hand.

        Args:
            process_ai: If True (default), process AI turns synchronously.
                       If False, skip AI processing (WebSocket handles it async).
        """
        # DEFENSIVE: If pot > 0, award to last active player to prevent chip loss
        # This handles edge cases where pot wasn't distributed properly
        if self.pot > 0:
            active_players = [p for p in self.players if p.is_active]
            if active_players:
                # Award to first active player (usually the winner by default)
                winner = active_players[0]
                winner.stack += self.pot
                # Clear all-in flag if winner now has chips
                if winner.stack > 0 and winner.all_in:
                    winner.all_in = False
                self._log_hand_event(
                    "pot_award", winner.player_id, "defensive_award",
                    self.pot, 0.0,
                    f"Defensive pot award: {winner.name} receives ${self.pot}"
                )
                self.pot = 0
            elif self.players:
                # No active players, award to any player with chips
                for p in self.players:
                    if p.stack >= 0:  # Any player still in game
                        p.stack += self.pot
                        # Clear all-in flag if winner now has chips
                        if p.stack > 0 and p.all_in:
                            p.all_in = False
                        self._log_hand_event(
                            "pot_award", p.player_id, "defensive_award",
                            self.pot, 0.0,
                            f"Defensive pot award: {p.name} receives ${self.pot}"
                        )
                        self.pot = 0
                        break

        # Save previous hand events to history
        if self.current_hand_events:
            self.hand_events.extend(self.current_hand_events)

            # Cap hand_events to prevent unbounded growth
            if len(self.hand_events) > MAX_HAND_EVENTS_HISTORY:
                self.hand_events = self.hand_events[-MAX_HAND_EVENTS_HISTORY:]

        self.hand_count += 1

        # Issue #1 fix: Increase blinds if needed (tournament mode)
        self._maybe_increase_blinds()

        self.current_hand_events = []
        self.last_ai_decisions = {}

        # Phase 3: Reset hand history tracking for new hand
        self._current_round_actions = []
        self._hand_betting_rounds = []
        self._pot_at_round_start = 0

        # Reset for new hand
        for player in self.players:
            player.reset_for_new_hand()

        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        self.last_raiser_index = None
        self.last_raise_amount = None

        # Reset deck
        self.deck_manager.reset()

        # Deal hole cards
        for player in self.players:
            if player.is_active:
                player.hole_cards = self.deck_manager.deal_cards(2)
                self._log_hand_event("deal", player.player_id, "hole_cards", 0, 0.0,
                                   f"Dealt {len(player.hole_cards)} hole cards")

        # Post blinds and get actual blind positions (important when players are busted)
        sb_index, bb_index = self._post_blinds()

        # QC: Verify chip conservation immediately after blind posting
        self._assert_chip_conservation("immediately after _post_blinds()")

        # Set first player to act (after big blind)
        # Use actual BB index, not dealer+2 (handles busted players correctly)
        if bb_index is not None:
            self.current_player_index = self._get_next_active_player_index(bb_index + 1)
        else:
            # Not enough players with chips
            self.current_player_index = None

        # Process AI actions if requested (synchronous flow for REST API and tests)
        # WebSocket flow passes process_ai=False and handles AI turns asynchronously
        if process_ai:
            self._process_remaining_actions()

        # Check if game should advance (e.g., all players all-in)
        self._maybe_advance_state()

        # QC: Verify chip conservation and game state after starting new hand
        self._assert_chip_conservation("after start_new_hand()")
        self._assert_valid_game_state("after start_new_hand()")

    def _post_blinds(self) -> tuple:
        """
        Post small and big blinds. Fixed: Handle busted players, partial blinds, and heads-up.
        Returns (sb_index, bb_index) for correct turn order calculation.
        """
        # DEBUG (set to True to enable logging)
        debug = False
        if debug:
            print(f"\n>>> _post_blinds() START:")
            for i, p in enumerate(self.players):
                print(f"    [{i}] {p.name}: ${p.stack}, invested=${p.total_invested}")
            print(f"    Pot: ${self.pot}")
            print(f"    Dealer index (before move): {self.dealer_index}")

        # Count players with chips
        players_with_chips_count = sum(1 for p in self.players if p.stack > 0)
        if players_with_chips_count < 2:
            # Not enough players to post blinds - game should end
            # But for now, just don't post blinds
            self.pot = 0
            self.current_bet = 0
            return (None, None)

        # Move dealer button (skip completely busted players with stack=0)
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        for _ in range(len(self.players)):
            if self.players[self.dealer_index].stack > 0:
                break
            self.dealer_index = (self.dealer_index + 1) % len(self.players)

        # Special case: Heads-up (exactly 2 players with chips)
        # In heads-up, dealer posts SB and other player posts BB
        if players_with_chips_count == 2:
            sb_index = self.dealer_index
            # Find the other player with chips (BB)
            bb_index = (self.dealer_index + 1) % len(self.players)
            for _ in range(len(self.players)):
                if self.players[bb_index].stack > 0 and bb_index != sb_index:
                    break
                bb_index = (bb_index + 1) % len(self.players)
        else:
            # Normal case: 3+ players with chips
            # Find SB (next player with chips after dealer)
            sb_index = (self.dealer_index + 1) % len(self.players)
            for _ in range(len(self.players)):
                if self.players[sb_index].stack > 0:
                    break
                sb_index = (sb_index + 1) % len(self.players)

            # Find BB (next player with chips after SB)
            bb_index = (sb_index + 1) % len(self.players)
            for _ in range(len(self.players)):
                if self.players[bb_index].stack > 0:
                    break
                bb_index = (bb_index + 1) % len(self.players)

        # Sanity check: SB and BB must be different players
        if sb_index == bb_index:
            raise RuntimeError(f"🚨 BLIND POSTING BUG: SB and BB are same player (index={sb_index})")

        # Post blinds (players will auto-go all-in if they don't have enough)
        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]

        if debug:
            print(f"    Dealer index (after move): {self.dealer_index}")
            print(f"    SB index: {sb_index} ({sb_player.name})")
            print(f"    BB index: {bb_index} ({bb_player.name})")

        sb_amount = sb_player.bet(self.small_blind)
        bb_amount = bb_player.bet(self.big_blind)

        if debug:
            print(f"    SB amount posted: ${sb_amount}")
            print(f"    BB amount posted: ${bb_amount}")

        # Blinds will mark themselves as acted during the natural betting round
        # This ensures BB gets their option to raise when everyone calls

        self.pot += sb_amount + bb_amount

        if debug:
            print(f"    Pot after blinds: ${self.pot}")
            print(f">>> _post_blinds() END\n")

        # Current bet is the actual BB amount (might be less if BB went all-in)
        self.current_bet = bb_amount
        self.last_raiser_index = bb_index  # BB is last raiser pre-flop
        # For pre-flop, the first raise must be at least big_blind (from bb_amount to bb_amount + big_blind)
        self.last_raise_amount = self.big_blind

        # FIX-01: Store blind positions for frontend display
        self.small_blind_index = sb_index
        self.big_blind_index = bb_index

        return (sb_index, bb_index)

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is. Fixed: Bug #1."""
        if self.current_player_index is None:
            return None
        return self.players[self.current_player_index]

    def apply_action(self, player_index: int, action: str, amount: int = 0,
                     hand_strength: float = 0.0, reasoning: str = "") -> dict:
        """
        Apply a player action to the game state. SINGLE SOURCE OF TRUTH for action processing.

        This method consolidates all action processing logic that was previously duplicated in:
        - submit_human_action()
        - _process_single_ai_action()
        - websocket_manager.process_ai_turns_with_events()

        Args:
            player_index: Index of the player taking the action
            action: 'fold', 'call', or 'raise'
            amount: For raise, the TOTAL bet amount (not increment). Ignored for fold/call.
            hand_strength: Optional hand strength for logging (0.0-1.0)
            reasoning: Optional reasoning text for logging

        Returns:
            dict with keys:
                - success: bool - whether action was applied
                - bet_amount: int - actual chips added to pot (0 for fold)
                - triggers_showdown: bool - whether this action ends the hand
                - error: str - error message if success=False
        """
        if action not in ["fold", "call", "raise"]:
            return {"success": False, "bet_amount": 0, "triggers_showdown": False,
                    "error": f"Invalid action: {action}"}

        if player_index < 0 or player_index >= len(self.players):
            return {"success": False, "bet_amount": 0, "triggers_showdown": False,
                    "error": f"Invalid player_index: {player_index}"}

        player = self.players[player_index]
        bet_amount = 0
        triggers_showdown = False

        if action == "fold":
            player.is_active = False
            player.has_acted = True
            self._log_hand_event("action", player.player_id, "fold", 0,
                               hand_strength, reasoning or f"{player.name} folded")

            # Check if <= 1 player remains after fold - triggers immediate showdown
            active_players = [p for p in self.players if p.is_active]
            if len(active_players) <= 1:
                triggers_showdown = True
                pot_awarded = 0
                winner_id = None
                if len(active_players) == 1:
                    winner = active_players[0]
                    winner_id = winner.player_id
                    pot_awarded = self.pot
                    winner.stack += self.pot
                    # Clear all-in flag if winner now has chips
                    if winner.stack > 0 and winner.all_in:
                        winner.all_in = False
                    self._log_hand_event("pot_award", winner.player_id, "win_by_fold",
                                       self.pot, 0.0, f"{winner.name} wins ${self.pot} (all others folded)")
                    self.pot = 0

                # Save hand for analysis (early end - fold in apply_action)
                self._save_hand_on_early_end(winner_id, pot_awarded)

                # Advance to showdown
                self.current_state = GameState.SHOWDOWN
                self.current_player_index = None

        elif action == "call":
            call_amount = self.current_bet - player.current_bet
            bet_amount = player.bet(call_amount)
            self.pot += bet_amount
            player.has_acted = True
            self._log_hand_event("action", player.player_id, "call", bet_amount,
                               hand_strength, reasoning or f"{player.name} called ${call_amount}")

        elif action == "raise":
            # SPECIAL CASE: If "raise" amount is below minimum BUT player is going all-in,
            # treat it as a call instead (correct poker behavior)
            # Texas Hold'em rule: Min raise = current_bet + (size of previous raise)
            # First raise in a round uses big_blind as the minimum increment
            min_raise_increment = self.last_raise_amount if self.last_raise_amount is not None else self.big_blind
            min_raise = self.current_bet + min_raise_increment
            if amount < min_raise:
                # Check if this is an all-in attempt
                max_possible_bet = player.stack + player.current_bet
                if amount >= player.stack or amount >= max_possible_bet:
                    # Player is going all-in but can't meet minimum raise
                    # Convert to call (put in all remaining chips)
                    call_amount = self.current_bet - player.current_bet
                    bet_amount = player.bet(call_amount)
                    self.pot += bet_amount
                    player.has_acted = True
                    self._log_hand_event("action", player.player_id, "call", bet_amount,
                                       hand_strength, reasoning or f"{player.name} called all-in ${call_amount}")
                else:
                    # Not an all-in, and below minimum - invalid
                    return {"success": False, "bet_amount": 0, "triggers_showdown": False,
                            "error": f"Raise amount {amount} below minimum {min_raise}"}
            else:
                # Valid raise amount - process normally
                # Calculate bet increment (amount is TOTAL bet, not increment)
                raise_total = amount
                bet_increment = raise_total - player.current_bet

                # Cap at player's stack (all-in for less)
                if bet_increment > player.stack:
                    bet_increment = player.stack

                bet_amount = player.bet(bet_increment)
                self.pot += bet_amount

                # Track the raise amount for next player's minimum raise calculation
                previous_bet = self.current_bet
                self.current_bet = raise_total  # CRITICAL: Use raise_total, not player.current_bet
                self.last_raise_amount = raise_total - previous_bet  # Store size of this raise
                self.last_raiser_index = player_index
                player.has_acted = True

                # Reset has_acted for other players who need to respond to raise
                for i, p in enumerate(self.players):
                    if i != player_index and p.is_active and not p.all_in:
                        p.has_acted = False

                self._log_hand_event("action", player.player_id, "raise", bet_amount,
                                   hand_strength, reasoning or f"{player.name} raised to ${self.current_bet}")

        # Phase 3: Track action for detailed hand history
        if action != "fold":  # Track successful actions (fold already tracked separately)
            action_record = ActionRecord(
                player_id=player.player_id,
                player_name=player.name,
                action=action,
                amount=bet_amount,
                stack_before=player.stack + bet_amount,  # Stack before action
                stack_after=player.stack,
                pot_before=self.pot - bet_amount,
                pot_after=self.pot,
                reasoning=reasoning
            )
            self._current_round_actions.append(action_record)

        return {"success": True, "bet_amount": bet_amount, "triggers_showdown": triggers_showdown, "error": ""}

    def submit_human_action(self, action: str, amount: int = None, process_ai: bool = True) -> bool:
        """
        Process human player action.
        Refactored to use apply_action() as single source of truth.

        Args:
            action: 'fold', 'call', or 'raise'
            amount: Required for raise action
            process_ai: If True, process AI turns synchronously (REST API).
                       If False, skip AI processing (WebSocket handles it).
        """
        # CRITICAL: Validate input types (fuzzing found this bug!)
        if action not in ["fold", "call", "raise"]:
            return False  # Invalid action type

        if amount is not None and not isinstance(amount, int):
            # Reject non-integer amounts (prevents rounding errors creating/destroying chips)
            return False

        human_player = next(p for p in self.players if p.is_human)
        human_index = next(i for i, p in enumerate(self.players) if p.is_human)

        # Check if it's human's turn
        if self.current_player_index != human_index:
            return False

        # Allow action even if not active (for fold case)
        if not human_player.is_active and action != "fold":
            return False

        # Calculate hand strength for logging using consolidated method
        hand_strength = 0.0
        if human_player.hole_cards:
            hand_score, _ = self.hand_evaluator.evaluate_hand(human_player.hole_cards, self.community_cards)
            hand_strength = HandEvaluator.score_to_strength(hand_score)

        # Use apply_action() - SINGLE SOURCE OF TRUTH for action processing
        result = self.apply_action(
            player_index=human_index,
            action=action,
            amount=amount or 0,
            hand_strength=hand_strength,
            reasoning=f"Human player {action}"
        )

        if not result["success"]:
            return False

        # If fold triggered showdown, we're done (apply_action handled it)
        if result["triggers_showdown"]:
            return True

        # Move to next player
        self.current_player_index = self._get_next_active_player_index(human_index + 1)

        # Fixed Bug #2: Process AI actions even after human folds
        # Only process synchronously for REST API; WebSocket handles AI turns async
        if process_ai:
            self._process_remaining_actions()

        # Advance game if betting round complete (only when processing AI synchronously)
        if process_ai:
            self._maybe_advance_state()

        # QC: Verify chip conservation and game state after human action
        self._assert_chip_conservation("after submit_human_action()")
        self._assert_valid_game_state("after submit_human_action()")

        return True

    def _process_remaining_actions(self):
        """Process remaining player actions in turn order. Fixed: Bugs #1, #2."""
        max_iterations = 100  # Prevent infinite loops
        iterations = 0

        while not self._betting_round_complete() and iterations < max_iterations:
            iterations += 1

            if self.current_player_index is None:
                break

            current_player = self.players[self.current_player_index]

            # Stop at human player if they haven't acted yet (wait for API call)
            # BUT: If human is all-in, they can't act, so don't wait for them
            if current_player.is_human and not current_player.has_acted and not current_player.all_in:
                break

            # Skip human player who has already acted OR is all-in
            if current_player.is_human and (current_player.has_acted or current_player.all_in):
                self.current_player_index = self._get_next_active_player_index(self.current_player_index + 1)
                continue

            # Process AI action
            if current_player.is_active and not current_player.all_in:
                self._process_single_ai_action(current_player, self.current_player_index)

            # Check if action triggered showdown (e.g., all others folded)
            # apply_action() sets current_player_index = None when hand is complete
            if self.current_player_index is None:
                break

            # Move to next player
            self.current_player_index = self._get_next_active_player_index(self.current_player_index + 1)

    def _process_single_ai_action(self, player: Player, player_index: int):
        """
        Process a single AI player action.
        Refactored to use apply_action() as single source of truth.
        """
        ai_decision = AIStrategy.make_decision_with_reasoning(
            player.personality, player.hole_cards, self.community_cards,
            self.current_bet, self.pot, player.stack, player.current_bet, self.big_blind,
            self.last_raise_amount
        )

        # Store decision for frontend
        self.last_ai_decisions[player.player_id] = ai_decision

        # Use apply_action() - SINGLE SOURCE OF TRUTH for action processing
        self.apply_action(
            player_index=player_index,
            action=ai_decision.action,
            amount=ai_decision.amount,
            hand_strength=ai_decision.hand_strength,
            reasoning=ai_decision.reasoning
        )

        # QC: Verify chip conservation after each AI action
        self._assert_chip_conservation(f"after AI {player.name} action: {ai_decision.action}")

    def _advance_state_core(self, process_ai: bool = True) -> bool:
        """
        Core state advancement logic. SINGLE SOURCE OF TRUTH for state transitions.

        This method consolidates all state advancement logic that was previously
        duplicated (and diverging) between:
        - _maybe_advance_state() (used by REST path)
        - _advance_state_for_websocket() (used by WebSocket path)

        Args:
            process_ai: If True, process remaining AI actions after state change.
                       Set False for WebSocket path (AI handled externally).

        Returns:
            True if state changed, False otherwise.

        Handles all edge cases:
        - Already at SHOWDOWN (no-op)
        - No current player but not at SHOWDOWN (safety fallback)
        - 0 active players (award pot to last actor)
        - 1 active player (award pot, fold victory)
        - All players all-in (fast-forward to showdown) <- Fixes UAT-5!
        - Normal state advancement (PRE_FLOP -> FLOP -> TURN -> RIVER -> SHOWDOWN)
        """
        # EARLY RETURN: Already at SHOWDOWN, nothing to advance
        if self.current_state == GameState.SHOWDOWN:
            return False

        active_count = sum(1 for p in self.players if p.is_active)

        # SAFETY CHECK: If no current player and not at showdown, force resolution
        # This handles edge cases where betting can't continue but hand isn't over
        if self.current_player_index is None:
            if self.pot > 0:
                if active_count == 1:
                    # Award pot to sole active player
                    winner = next((p for p in self.players if p.is_active), None)
                    if winner:
                        winner.stack += self.pot
                        if winner.stack > 0 and winner.all_in:
                            winner.all_in = False
                        self._log_hand_event("pot_award", winner.player_id, "win", self.pot, 0.0,
                                           f"{winner.name} wins ${self.pot} (no other players can act)")
                        self.pot = 0
                elif active_count > 1:
                    # Multiple players still active but no one can act - go to showdown
                    self.current_state = GameState.SHOWDOWN
                    self._award_pot_at_showdown()
                    return True
            self.current_state = GameState.SHOWDOWN
            return True

        # Handle 0 active players (all folded - award to last actor)
        if active_count == 0:
            last_actor_id = None
            for event in reversed(self.current_hand_events):
                if event.event_type == "action":
                    last_actor_id = event.player_id
                    break

            if last_actor_id and self.pot > 0:
                winner = next((p for p in self.players if p.player_id == last_actor_id), None)
                if winner:
                    winner.stack += self.pot
                    winner.is_active = True  # Reactivate for pot award
                    if winner.stack > 0 and winner.all_in:
                        winner.all_in = False
                    self._log_hand_event("pot_award", winner.player_id, "win", self.pot, 0.0,
                                       f"All players folded - {winner.name} wins ${self.pot} by default")
                    self.pot = 0

            self.current_state = GameState.SHOWDOWN
            self.current_player_index = None
            return True

        # Handle 1 active player (everyone else folded - award pot)
        if active_count == 1:
            winner = next((p for p in self.players if p.is_active), None)
            pot_awarded = 0
            if winner and self.pot > 0:
                pot_awarded = self.pot
                winner.stack += self.pot
                if winner.stack > 0 and winner.all_in:
                    winner.all_in = False
                self._log_hand_event("pot_award", winner.player_id, "win", self.pot, 0.0,
                                   f"{winner.name} wins ${self.pot} (all others folded)")
                self.pot = 0

            # Save hand for analysis (early end - fold)
            self._save_hand_on_early_end(winner.player_id if winner else None, pot_awarded)

            self.current_state = GameState.SHOWDOWN
            self.current_player_index = None
            return True

        # ALL-IN FAST-FORWARD (UAT-5 fix): If all remaining active players are all-in
        # (or only 1 player can still act), no more betting is possible - go to showdown
        active_not_all_in = [p for p in self.players if p.is_active and not p.all_in]
        if len(active_not_all_in) <= 1:
            # Deal remaining community cards
            if self.current_state == GameState.PRE_FLOP:
                self.community_cards.extend(self.deck_manager.deal_cards(3))  # Flop
                self.community_cards.extend(self.deck_manager.deal_cards(1))  # Turn
                self.community_cards.extend(self.deck_manager.deal_cards(1))  # River
            elif self.current_state == GameState.FLOP:
                self.community_cards.extend(self.deck_manager.deal_cards(1))  # Turn
                self.community_cards.extend(self.deck_manager.deal_cards(1))  # River
            elif self.current_state == GameState.TURN:
                self.community_cards.extend(self.deck_manager.deal_cards(1))  # River
            # RIVER already has all cards

            # Go directly to showdown
            self.current_state = GameState.SHOWDOWN
            self._award_pot_at_showdown()
            self.current_player_index = None
            return True

        # Normal case: Check if betting round is complete before advancing
        if not self._betting_round_complete():
            return False  # Can't advance yet

        # Phase 3: Save current betting round before advancing
        if len(self._current_round_actions) > 0:
            betting_round = BettingRound(
                round_name=self.current_state.value,
                community_cards=self.community_cards.copy(),
                actions=self._current_round_actions.copy(),
                pot_at_start=self._pot_at_round_start,
                pot_at_end=self.pot
            )
            self._hand_betting_rounds.append(betting_round)
            self._current_round_actions = []  # Reset for next round

        # Advance to next state and deal cards
        if self.current_state == GameState.PRE_FLOP:
            self.current_state = GameState.FLOP
            self.community_cards.extend(self.deck_manager.deal_cards(3))
        elif self.current_state == GameState.FLOP:
            self.current_state = GameState.TURN
            self.community_cards.extend(self.deck_manager.deal_cards(1))
        elif self.current_state == GameState.TURN:
            self.current_state = GameState.RIVER
            self.community_cards.extend(self.deck_manager.deal_cards(1))
        elif self.current_state == GameState.RIVER:
            self.current_state = GameState.SHOWDOWN
            self._award_pot_at_showdown()
            return True

        # Reset for new betting round
        for player in self.players:
            player.reset_for_new_round()
        self.current_bet = 0
        self.last_raiser_index = None
        self.last_raise_amount = None  # Reset min raise to big_blind for new round

        # Phase 3: Track pot at start of new round
        self._pot_at_round_start = self.pot

        # First to act is after dealer
        first_to_act = self._get_next_active_player_index(self.dealer_index + 1)
        self.current_player_index = first_to_act

        # Optionally process AI actions (REST path does this, WebSocket path doesn't)
        if process_ai:
            self._process_remaining_actions()
            # Recursive check if hand should end after processing actions
            self._advance_state_core(process_ai=True)

        return True

    def _maybe_advance_state(self):
        """Advance game state if betting round is complete."""
        # Delegate to core method with AI processing enabled
        self._advance_state_core(process_ai=True)

    def _advance_state_for_websocket(self):
        """
        Advance game state without processing AI actions (for WebSocket flow).
        Used when AI actions are handled externally one-by-one.

        Delegates to _advance_state_core() with process_ai=False.
        This ensures WebSocket path has ALL the same edge case handling:
        - All-in fast-forward (UAT-5 fix)
        - 0 active players handling
        - Proper showdown triggering
        """
        return self._advance_state_core(process_ai=False)

    def _award_pot_at_showdown(self):
        """Award pot to winners at showdown. Called automatically when reaching SHOWDOWN."""
        if self.pot == 0:
            return  # No pot to award

        # Store original pot for verification
        original_pot = self.pot

        pots = self.hand_evaluator.determine_winners_with_side_pots(self.players, self.community_cards)

        # Calculate total pot from side pot calculation
        calculated_pot_total = sum(pot_info['amount'] for pot_info in pots)

        # CRITICAL FIX: The actual pot might differ from calculated pots due to
        # rounding or partial blind posts. Always award the ACTUAL pot, not calculated.
        # Distribute any difference to the first winner.
        pot_difference = original_pot - calculated_pot_total

        # Distribute winnings with proper remainder handling
        total_awarded = 0
        for pot_info in pots:
            num_winners = len(pot_info['winners'])
            split_amount = pot_info['amount'] // num_winners
            remainder = pot_info['amount'] % num_winners

            for i, winner_id in enumerate(pot_info['winners']):
                winner = next(p for p in self.players if p.player_id == winner_id)
                award_amount = split_amount + (1 if i < remainder else 0)

                # Add pot difference to first winner (handles rounding errors)
                if pot_difference > 0 and total_awarded == 0:
                    award_amount += pot_difference

                winner.stack += award_amount
                total_awarded += award_amount

                # Clear all-in flag if winner now has chips (Bug fix from marathon simulation)
                if winner.stack > 0 and winner.all_in:
                    winner.all_in = False

                # Log pot award event for winner_info
                self._log_hand_event("pot_award", winner.player_id, "win", award_amount, 0.0,
                                   f"{winner.name} wins ${award_amount} at showdown")

        self.pot = 0

        # Save completed hand for analysis (UX Phase 2)
        self._save_completed_hand(pots, original_pot)

        # QC: Verify chip conservation after pot award
        self._assert_chip_conservation("after _award_pot_at_showdown()")
        self._assert_valid_game_state("after _award_pot_at_showdown()")

    def _save_hand_on_early_end(self, winner_id: Optional[str], pot_size: int):
        """Save hand that ended early (before showdown). UX Phase 2."""
        try:
            # Skip saving if no human player (AI-only games)
            human = next((p for p in self.players if p.is_human), None)
            if human is None:
                return

            # Determine winner
            winner_ids = [winner_id] if winner_id else []
            winner_names = []
            if winner_id:
                winner = next((p for p in self.players if p.player_id == winner_id), None)
                if winner:
                    winner_names = [winner.name]

            # Determine human's final action
            human_action = "unknown"
            if not human.is_active:
                human_action = "fold"
            elif human.all_in:
                human_action = "all-in"
            else:
                # Check last action from events
                for event in reversed(self.current_hand_events):
                    if event.player_id == human.player_id and event.event_type == "action":
                        human_action = event.action
                        break

            # Get human's hand strength if cards were dealt (using consolidated method)
            human_hand_strength = 0.0
            if human.hole_cards and self.community_cards:
                score, _ = self.hand_evaluator.evaluate_hand(human.hole_cards, self.community_cards)
                human_hand_strength = HandEvaluator.score_to_strength(score)

            # Calculate pot odds
            human_pot_odds = 0.0
            for event in reversed(self.current_hand_events):
                if event.player_id == human.player_id and event.pot_size > 0:
                    call_amount = event.current_bet
                    if call_amount > 0:
                        human_pot_odds = call_amount / (event.pot_size + call_amount)
                    break

            # Phase 3: Add session tracking and detailed history
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + 'Z'

            # Create completed hand record
            completed_hand = CompletedHand(
                hand_number=self.hand_count,
                community_cards=self.community_cards.copy(),
                pot_size=pot_size,
                winner_ids=winner_ids,
                winner_names=winner_names,
                human_action=human_action,
                human_cards=human.hole_cards.copy() if human.hole_cards else [],
                human_final_stack=human.stack,
                human_hand_strength=human_hand_strength,
                human_pot_odds=human_pot_odds,
                ai_decisions=self.last_ai_decisions.copy(),
                events=self.current_hand_events.copy(),
                # Phase 3 fields
                session_id=self.session_id,
                timestamp=timestamp,
                betting_rounds=self._hand_betting_rounds.copy(),
                showdown_hands={},  # Early end - no showdown
                hand_rankings={}  # Early end - no rankings
            )

            # Store
            self.last_hand_summary = completed_hand
            self.completed_hands.append(completed_hand)

            # Phase 3: Also store in hand_history with 100-hand limit
            self.hand_history.append(completed_hand)
            if len(self.hand_history) > 100:
                self.hand_history = self.hand_history[-100:]

            # Keep only last 50 hands in completed_hands (legacy)
            if len(self.completed_hands) > 50:
                self.completed_hands = self.completed_hands[-50:]

        except Exception as e:
            print(f"Warning: Failed to save early-end hand for analysis: {e}")
            import traceback
            traceback.print_exc()

    def _save_completed_hand(self, pots: List[Dict], pot_size: int):
        """Save completed hand for later analysis. UX Phase 2."""
        try:
            # Skip saving if no human player (AI-only games)
            human = next((p for p in self.players if p.is_human), None)
            if human is None:
                return

            # Collect all winners from all pots
            all_winner_ids = set()
            for pot_info in pots:
                all_winner_ids.update(pot_info.get('winners', []))

            winner_names = [p.name for p in self.players if p.player_id in all_winner_ids]

            # Determine human's final action
            human_action = "unknown"
            if not human.is_active:
                human_action = "fold"
            elif human.all_in:
                human_action = "all-in"
            else:
                # Check last action from events
                for event in reversed(self.current_hand_events):
                    if event.player_id == human.player_id and event.event_type == "action":
                        human_action = event.action
                        break

            # Get human's hand strength at showdown (using consolidated method)
            human_hand_strength = 0.0
            if human.hole_cards and self.community_cards:
                score, _ = self.hand_evaluator.evaluate_hand(human.hole_cards, self.community_cards)
                human_hand_strength = HandEvaluator.score_to_strength(score)

            # Calculate pot odds for human's last decision
            human_pot_odds = 0.0
            for event in reversed(self.current_hand_events):
                if event.player_id == human.player_id and event.pot_size > 0:
                    call_amount = event.current_bet
                    if call_amount > 0:
                        human_pot_odds = call_amount / (event.pot_size + call_amount)
                    break

            # Phase 3: Collect showdown hands and rankings
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + 'Z'
            showdown_hands = {}
            hand_rankings = {}

            for player in self.players:
                if player.hole_cards and len(player.hole_cards) == 2:
                    # All players who reached showdown
                    if player.is_active or player.all_in:
                        showdown_hands[player.player_id] = player.hole_cards.copy()
                        _, rank = self.hand_evaluator.evaluate_hand(player.hole_cards, self.community_cards)
                        hand_rankings[player.player_id] = rank

            # Create completed hand record
            completed_hand = CompletedHand(
                hand_number=self.hand_count,
                community_cards=self.community_cards.copy(),
                pot_size=pot_size,
                winner_ids=list(all_winner_ids),
                winner_names=winner_names,
                human_action=human_action,
                human_cards=human.hole_cards.copy() if human.hole_cards else [],
                human_final_stack=human.stack,
                human_hand_strength=human_hand_strength,
                human_pot_odds=human_pot_odds,
                ai_decisions=self.last_ai_decisions.copy(),
                events=self.current_hand_events.copy(),
                # Phase 3 fields
                session_id=self.session_id,
                timestamp=timestamp,
                betting_rounds=self._hand_betting_rounds.copy(),
                showdown_hands=showdown_hands,
                hand_rankings=hand_rankings
            )

            # Store as last hand and in history
            self.last_hand_summary = completed_hand
            self.completed_hands.append(completed_hand)

            # Phase 3: Also store in hand_history with 100-hand limit
            self.hand_history.append(completed_hand)
            if len(self.hand_history) > 100:
                self.hand_history = self.hand_history[-100:]

            # Keep only last 50 hands to avoid memory issues (legacy)
            if len(self.completed_hands) > 50:
                self.completed_hands = self.completed_hands[-50:]

        except Exception as e:
            # Don't fail the game if hand saving fails
            print(f"Warning: Failed to save hand for analysis: {e}")
            import traceback
            traceback.print_exc()

    def analyze_last_hand(self) -> Optional[Dict]:
        """
        Analyze the last completed hand and provide rule-based insights.
        UX Phase 2 - Learning feature.
        """
        if not self.last_hand_summary:
            return None

        hand = self.last_hand_summary
        insights = []
        tips = []

        # Determine if human won
        human_won = "human" in hand.winner_ids
        human = next(p for p in self.players if p.is_human)

        # Analysis 1: Pot Odds vs Decision
        if hand.human_action in ["fold", "call", "raise"]:
            if hand.human_pot_odds > 0:
                pot_odds_pct = hand.human_pot_odds * 100
                hand_strength_pct = hand.human_hand_strength * 100

                if hand.human_action == "fold" and hand.human_hand_strength >= 0.4 and hand.human_pot_odds < 0.33:
                    insights.append(f"✓ Good fold! You had a decent hand ({hand_strength_pct:.0f}%) but pot odds ({pot_odds_pct:.0f}%) weren't favorable.")
                elif hand.human_action == "fold" and hand.human_hand_strength >= 0.5:
                    insights.append(f"⚠️ You folded a strong hand ({hand_strength_pct:.0f}%). With pot odds of {pot_odds_pct:.0f}%, calling might have been better.")
                    tips.append("Tip: With strong hands (>50%), you should call unless facing a very large bet.")

                elif hand.human_action == "call" and hand.human_hand_strength < 0.25 and hand.human_pot_odds > 0.5:
                    insights.append(f"⚠️ You called with a weak hand ({hand_strength_pct:.0f}%) and poor pot odds ({pot_odds_pct:.0f}%).")
                    tips.append("Tip: Calling with weak hands and bad pot odds usually loses money. Consider folding.")
                elif hand.human_action == "call" and hand.human_hand_strength > 0.4:
                    insights.append(f"✓ Reasonable call with {hand_strength_pct:.0f}% hand strength.")

        # Analysis 2: Outcome
        if human_won:
            insights.append(f"🎉 You won ${hand.pot_size}!")
            if hand.human_action == "fold":
                insights.append("(You won by default - all others folded)")
        else:
            if hand.human_action != "fold":
                insights.append(f"You lost to {', '.join(hand.winner_names)}")
                if hand.human_hand_strength >= 0.6:
                    insights.append("Tough beat - you had a strong hand but got outdrawn.")

        # Analysis 3: AI Decisions (what were they thinking?)
        ai_thinking = []
        for player_id, decision in hand.ai_decisions.items():
            ai_player = next((p for p in self.players if p.player_id == player_id), None)
            if ai_player:
                ai_thinking.append({
                    'name': ai_player.name,
                    'personality': ai_player.personality,
                    'action': decision.action,
                    'reasoning': decision.reasoning,
                    'hand_strength': decision.hand_strength,
                    'confidence': decision.confidence
                })

        # Analysis 4: Hand Strength Comparison
        if hand.community_cards and human_won is False:
            insights.append(f"Your final hand strength: {hand.human_hand_strength*100:.0f}%")

        # Analysis 5: Strategic Tips
        if hand.human_action == "raise" and not human_won:
            tips.append("Tip: Raising is powerful but risky. Make sure you have a strong hand or good bluffing opportunity.")

        if hand.human_action == "all-in":
            if human_won:
                insights.append("✓ All-in paid off!")
            else:
                insights.append("All-in didn't work out this time. Make sure you're all-in with strong hands or as a calculated bluff.")

        # Build final analysis
        return {
            'hand_number': hand.hand_number,
            'your_action': hand.human_action,
            'your_cards': hand.human_cards,
            'community_cards': hand.community_cards,
            'pot_size': hand.pot_size,
            'you_won': human_won,
            'winners': hand.winner_names,
            'your_hand_strength': f"{hand.human_hand_strength*100:.0f}%",
            'insights': insights,
            'tips': tips,
            'ai_thinking': ai_thinking,
            'detailed_events': len(hand.events),  # Number of actions in hand
        }

    def get_showdown_results(self) -> Optional[Dict]:
        """Get showdown results with side pots. Fixed: Bug #5."""
        if self.current_state != GameState.SHOWDOWN:
            return None

        # Award pot if not already awarded
        self._award_pot_at_showdown()

        # Return results (pot is already 0 after awarding)
        pots = self.hand_evaluator.determine_winners_with_side_pots(self.players, self.community_cards)

        return {
            "pots": pots,
            "community_cards": self.community_cards,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "hole_cards": p.hole_cards,
                    "stack": p.stack
                } for p in self.players
            ]
        }

    def get_game_state(self) -> Dict:
        """Get current game state with learning data."""
        current_player = self.get_current_player()

        return {
            "game_state": self.current_state.value,
            "current_player_id": current_player.player_id if current_player else None,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "stack": p.stack,
                    "current_bet": p.current_bet,
                    "is_active": p.is_active,
                    "all_in": p.all_in,
                    "hole_cards": p.hole_cards if p.is_human else ["hidden", "hidden"],
                    "is_current": self.players.index(p) == self.current_player_index
                } for p in self.players
            ],
            "community_cards": self.community_cards,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "hand_count": self.hand_count,
            # Learning features
            "ai_decisions": {
                player_id: {
                    "action": decision.action,
                    "reasoning": decision.reasoning,
                    "hand_strength": decision.hand_strength,
                    "pot_odds": decision.pot_odds,
                    "confidence": decision.confidence
                } for player_id, decision in self.last_ai_decisions.items()
            },
            "current_hand_events": [
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "player_id": event.player_id,
                    "action": event.action,
                    "amount": event.amount,
                    "reasoning": event.reasoning,
                    "hand_strength": event.hand_strength
                } for event in self.current_hand_events[-5:]
            ]
        }
