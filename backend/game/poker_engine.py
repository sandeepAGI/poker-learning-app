# Poker Game Engine - Bug Fixes Applied
# Fixed: Turn order, fold resolution, raise validation, raise accounting, side pots
import random
import json
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
        """Place a bet, reducing stack. Fixed: proper accounting."""
        if amount > self.stack:
            amount = self.stack
            self.all_in = True

        self.stack -= amount
        self.current_bet += amount
        self.total_invested += amount
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

    def determine_winners_with_side_pots(self, players: List[Player], community_cards: List[str]) -> List[Dict]:
        """
        Determine winners with proper side pot handling.
        Returns list of pots with winners and amounts.
        Fixed: Bug #5 - Side pot implementation
        """
        # Players who can win pots
        eligible_winners = [p for p in players if p.is_active or p.all_in]

        # Include ALL players (even folded) when calculating pot amounts
        # because their chips are in the pot
        all_players_with_investment = [p for p in players if p.total_invested > 0]

        if len(eligible_winners) <= 1:
            winner = eligible_winners[0] if eligible_winners else None
            if not winner:
                return []
            # Pot amount is sum of ALL investments, not just winner's
            total_pot = sum(p.total_invested for p in all_players_with_investment)
            return [{
                'winners': [winner.player_id],
                'amount': total_pot,
                'type': 'main',
                'eligible_player_ids': [p.player_id for p in eligible_winners]
            }]

        # Build side pots
        pots = []
        remaining_players = all_players_with_investment.copy()

        while remaining_players:
            # Find minimum investment among remaining players
            min_investment = min(p.total_invested for p in remaining_players if p.total_invested > 0)
            if min_investment == 0:
                break

            # Create pot at this level - include ALL players' contributions
            pot_amount = 0
            pot_contributors = []  # All who contribute to this pot
            eligible_for_pot = []  # Only active/all-in can win

            for player in remaining_players:
                contribution = min(player.total_invested, min_investment)
                pot_amount += contribution
                player.total_invested -= contribution
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
            remaining_players = [p for p in remaining_players if p.total_invested > 0]

        return pots

class AIStrategy:
    """AI strategies with decision reasoning for learning."""

    @staticmethod
    def make_decision_with_reasoning(personality: str, hole_cards: List[str], community_cards: List[str],
                                   current_bet: int, pot_size: int, player_stack: int, player_bet: int = 0,
                                   big_blind: int = 10) -> AIDecision:
        """
        Make AI decision with full reasoning for transparency.
        Fixed: Uses big_blind for minimum raise calculation
        """

        # Hand strength calculation
        evaluator = HandEvaluator()
        hand_score, hand_rank = evaluator.evaluate_hand(hole_cards, community_cards)

        # Proper hand strength based on poker hand rankings
        if hand_score <= 10:  # Straight flush or better
            hand_strength = 0.95
        elif hand_score <= 166:  # Four of a kind
            hand_strength = 0.90
        elif hand_score <= 322:  # Full house
            hand_strength = 0.85
        elif hand_score <= 1599:  # Flush
            hand_strength = 0.75
        elif hand_score <= 1609:  # Straight
            hand_strength = 0.65
        elif hand_score <= 2467:  # Three of a kind
            hand_strength = 0.55
        elif hand_score <= 3325:  # Two pair
            hand_strength = 0.45
        elif hand_score <= 6185:  # One pair
            hand_strength = 0.25
        else:  # High card
            hand_strength = 0.05

        # Pot odds calculation
        call_amount = current_bet - player_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0

        # SPR (Stack-to-Pot Ratio) calculation - key poker metric for pot-relative decisions
        spr = player_stack / pot_size if pot_size > 0 else float('inf')

        if personality == "Conservative":
            # SPR-aware Conservative: Tighter with deep stacks, more committed with shallow stacks
            if spr < 3 and hand_strength >= 0.45:  # Low SPR - pot-committed with two pair+
                action = "raise" if random.random() > 0.3 else "call"
                amount = max(current_bet + big_blind, player_stack) if action == "raise" else call_amount
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
                amount = max(current_bet + big_blind, current_bet * 2) if action == "raise" else call_amount
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
                    amount = max(current_bet + big_blind, current_bet * 2)
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
                amount = max(current_bet + big_blind, current_bet * 3) if action == "raise" else call_amount
                amount = min(amount, player_stack)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Aggressive value betting."
                confidence = 0.8
            elif hand_strength >= 0.25:  # Any pair
                if random.random() > 0.4:
                    action = "raise" if random.random() > 0.6 else "call"
                    amount = max(current_bet + big_blind, current_bet * 2) if action == "raise" else call_amount
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
                    amount = max(current_bet + big_blind, current_bet * 2)
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
            implied_odds_factor = min(spr * pot_odds, 1.0) if spr != float('inf') else pot_odds

            if spr < 3 and hand_strength >= 0.25:  # Low SPR - committed with any pair
                action = "call" if call_amount < player_stack else "raise"
                amount = call_amount if action == "call" else player_stack
                reasoning = f"Low SPR ({spr:.1f}) - pot committed with {hand_rank}. Positive EV."
                confidence = 0.85
            elif hand_strength >= 0.65:  # Straight or better
                action = "raise"
                amount = max(current_bet + big_blind, current_bet * 2)
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
            spr=spr
        )

class PokerGame:
    """Main poker game class with bug fixes applied."""

    def __init__(self, human_player_name: str, ai_count: int = 3):
        """
        Create a new poker game.

        Args:
            human_player_name: Name of the human player
            ai_count: Number of AI opponents (1-3, default 3)
        """
        if ai_count < 1 or ai_count > 3:
            raise ValueError("AI count must be between 1 and 3")

        self.deck_manager = DeckManager()
        self.hand_evaluator = HandEvaluator()

        # Create human player
        self.players = [Player("human", human_player_name, is_human=True)]

        # Add AI players dynamically with creative AI pun names
        personalities = ["Conservative", "Aggressive", "Mathematical"]
        ai_names = ["AI-ce", "AI-ron", "AI-nstein"]  # Fun AI puns
        for i in range(ai_count):
            self.players.append(
                Player(
                    player_id=f"ai{i+1}",
                    name=ai_names[i],
                    personality=personalities[i]
                )
            )

        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        self.dealer_index = 0
        self.hand_count = 0
        self.big_blind = 10
        self.small_blind = 5

        # Fixed: Bug #1 - Turn order tracking
        self.current_player_index = 0
        self.last_raiser_index = None

        # Learning features
        self.hand_events: List[HandEvent] = []
        self.current_hand_events: List[HandEvent] = []
        self.last_ai_decisions: Dict[str, AIDecision] = {}

        # QC: Enable runtime assertions for poker rule validation
        self.qc_enabled = True  # Set to False to disable for performance

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
        if total != 4000:
            # Build detailed error message
            stacks_info = ", ".join([f"{p.name}=${p.stack}" for p in self.players])
            raise RuntimeError(
                f"🚨 CHIP CONSERVATION VIOLATED {context}\n"
                f"   Total: ${total} (Expected: $4000)\n"
                f"   Missing: ${4000 - total}\n"
                f"   Pot: ${self.pot}\n"
                f"   Stacks: {stacks_info}\n"
                f"   State: {self.current_state.value}\n"
                f"   This is a CRITICAL BUG - chips disappeared or were created!"
            )

    def _assert_valid_game_state(self, context: str = ""):
        """
        Assert that game state is valid.
        Checks multiple invariants that should always be true.
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

        # 5. Active players should have non-negative stacks or be all-in
        for p in self.players:
            if p.is_active and p.stack < 0:
                errors.append(f"Active player {p.name} has negative stack: ${p.stack}")

        # 6. At showdown, pot should be 0 (already awarded)
        if self.current_state == GameState.SHOWDOWN and self.pot > 0:
            errors.append(f"At SHOWDOWN but pot not awarded: ${self.pot}")

        # 7. If only 0-1 active players, should be at SHOWDOWN
        active_count = sum(1 for p in self.players if p.is_active)
        if active_count <= 1 and self.current_state != GameState.SHOWDOWN:
            errors.append(f"Only {active_count} active players but not at SHOWDOWN (state: {self.current_state.value})")

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
        """Check if betting round is complete. Fixed: Bug #1."""
        active_players = [p for p in self.players if p.is_active and not p.all_in]

        # If only 0-1 active players, round is complete
        if len(active_players) <= 1:
            return True

        # All active players must have acted and matched the current bet
        for player in active_players:
            if not player.has_acted:
                return False
            if player.current_bet != self.current_bet:
                return False

        return True

    def start_new_hand(self):
        """Start a new poker hand."""
        # Save previous hand events to history
        if self.current_hand_events:
            self.hand_events.extend(self.current_hand_events)

            # Cap hand_events to prevent unbounded growth
            if len(self.hand_events) > MAX_HAND_EVENTS_HISTORY:
                self.hand_events = self.hand_events[-MAX_HAND_EVENTS_HISTORY:]

        self.hand_count += 1
        self.current_hand_events = []
        self.last_ai_decisions = {}

        # Reset for new hand
        for player in self.players:
            player.reset_for_new_hand()

        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        self.last_raiser_index = None

        # Reset deck
        self.deck_manager.reset()

        # Deal hole cards
        for player in self.players:
            if player.is_active:
                player.hole_cards = self.deck_manager.deal_cards(2)
                self._log_hand_event("deal", player.player_id, "hole_cards", 0, 0.0,
                                   f"Dealt {len(player.hole_cards)} hole cards")

        # Post blinds
        self._post_blinds()

        # Set first player to act (after big blind)
        bb_index = (self.dealer_index + 2) % len(self.players)
        self.current_player_index = self._get_next_active_player_index(bb_index + 1)

        # Process AI actions if AI player is first to act
        self._process_remaining_actions()

        # QC: Verify chip conservation and game state after starting new hand
        self._assert_chip_conservation("after start_new_hand()")
        self._assert_valid_game_state("after start_new_hand()")

    def _post_blinds(self):
        """Post small and big blinds."""
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)

        # Post blinds
        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]

        sb_amount = sb_player.bet(self.small_blind)
        bb_amount = bb_player.bet(self.big_blind)

        # Blinds will mark themselves as acted during the natural betting round
        # This ensures BB gets their option to raise when everyone calls

        self.pot += sb_amount + bb_amount
        self.current_bet = self.big_blind
        self.last_raiser_index = bb_index  # BB is last raiser pre-flop

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is. Fixed: Bug #1."""
        if self.current_player_index is None:
            return None
        return self.players[self.current_player_index]

    def submit_human_action(self, action: str, amount: int = None) -> bool:
        """
        Process human player action.
        Fixed: Bug #1 (turn order), Bug #2 (fold resolution), Bug #3 (raise validation)
        """
        human_player = next(p for p in self.players if p.is_human)
        human_index = next(i for i, p in enumerate(self.players) if p.is_human)

        # Fixed Bug #1: Check if it's human's turn
        if self.current_player_index != human_index:
            return False

        # Fixed Bug #2: Allow action even if not active (for fold case)
        if not human_player.is_active and action != "fold":
            return False

        # Calculate hand strength
        hand_strength = 0.0
        if human_player.hole_cards:
            hand_score, _ = self.hand_evaluator.evaluate_hand(human_player.hole_cards, self.community_cards)
            if hand_score <= 10:
                hand_strength = 0.95
            elif hand_score <= 166:
                hand_strength = 0.90
            elif hand_score <= 322:
                hand_strength = 0.85
            elif hand_score <= 1599:
                hand_strength = 0.75
            elif hand_score <= 1609:
                hand_strength = 0.65
            elif hand_score <= 2467:
                hand_strength = 0.55
            elif hand_score <= 3325:
                hand_strength = 0.45
            elif hand_score <= 6185:
                hand_strength = 0.25
            else:
                hand_strength = 0.05

        if action == "fold":
            human_player.is_active = False
            human_player.has_acted = True
            self._log_hand_event("action", human_player.player_id, "fold", 0,
                               hand_strength, f"Human player folded with {hand_strength:.1%} hand strength")

        elif action == "call":
            call_amount = self.current_bet - human_player.current_bet
            bet_amount = human_player.bet(call_amount)
            self.pot += bet_amount
            human_player.has_acted = True
            self._log_hand_event("action", human_player.player_id, "call", bet_amount,
                               hand_strength, f"Human called ${call_amount}")

        elif action == "raise" and amount:
            # Fixed Bug #3: Validate raise
            call_amount = self.current_bet - human_player.current_bet
            min_raise = self.current_bet + self.big_blind

            if amount < min_raise and amount < human_player.stack:
                # Invalid raise amount
                return False

            # Fixed Bug #4: Proper raise accounting - amount is total bet, not increment
            total_bet = amount
            bet_increment = total_bet - human_player.current_bet

            if bet_increment > human_player.stack:
                bet_increment = human_player.stack

            bet_amount = human_player.bet(bet_increment)
            self.pot += bet_amount
            self.current_bet = total_bet  # Fixed: use total_bet, not player.current_bet
            self.last_raiser_index = human_index
            human_player.has_acted = True

            # Reset has_acted for other players who need to respond to raise
            for i, p in enumerate(self.players):
                if i != human_index and p.is_active and not p.all_in:
                    p.has_acted = False

            self._log_hand_event("action", human_player.player_id, "raise", bet_amount,
                               hand_strength, f"Human raised to ${self.current_bet}")
        else:
            return False

        # Move to next player
        self.current_player_index = self._get_next_active_player_index(human_index + 1)

        # Fixed Bug #2: Process AI actions even after human folds
        self._process_remaining_actions()

        # Advance game if betting round complete
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
            if current_player.is_human and not current_player.has_acted:
                break

            # Skip human player who has already acted
            if current_player.is_human and current_player.has_acted:
                self.current_player_index = self._get_next_active_player_index(self.current_player_index + 1)
                continue

            # Process AI action
            if current_player.is_active and not current_player.all_in:
                self._process_single_ai_action(current_player, self.current_player_index)

            # Move to next player
            self.current_player_index = self._get_next_active_player_index(self.current_player_index + 1)

    def _process_single_ai_action(self, player: Player, player_index: int):
        """Process a single AI player action. Fixed: Bug #4 - raise accounting."""
        ai_decision = AIStrategy.make_decision_with_reasoning(
            player.personality, player.hole_cards, self.community_cards,
            self.current_bet, self.pot, player.stack, player.current_bet, self.big_blind
        )

        # Store decision for frontend
        self.last_ai_decisions[player.player_id] = ai_decision

        if ai_decision.action == "fold":
            player.is_active = False
            player.has_acted = True
            self._log_hand_event("action", player.player_id, "fold", 0,
                               ai_decision.hand_strength, ai_decision.reasoning)

        elif ai_decision.action == "call":
            call_amount = self.current_bet - player.current_bet
            bet_amount = player.bet(call_amount)
            self.pot += bet_amount
            player.has_acted = True
            self._log_hand_event("action", player.player_id, "call", bet_amount,
                               ai_decision.hand_strength, ai_decision.reasoning)

        elif ai_decision.action == "raise":
            # Fixed Bug #4: Proper raise accounting
            raise_total = ai_decision.amount
            bet_increment = raise_total - player.current_bet

            if bet_increment > player.stack:
                bet_increment = player.stack

            bet_amount = player.bet(bet_increment)
            self.pot += bet_amount
            self.current_bet = raise_total  # Fixed: use raise_total, not player.current_bet
            self.last_raiser_index = player_index
            player.has_acted = True

            # Reset has_acted for players who need to respond
            for i, p in enumerate(self.players):
                if i != player_index and p.is_active and not p.all_in:
                    p.has_acted = False

            self._log_hand_event("action", player.player_id, "raise", bet_amount,
                               ai_decision.hand_strength, ai_decision.reasoning)

        # QC: Verify chip conservation after each AI action
        self._assert_chip_conservation(f"after AI {player.name} action: {ai_decision.action}")

    def _maybe_advance_state(self):
        """Advance game state if betting round is complete."""
        active_count = sum(1 for p in self.players if p.is_active)

        if active_count == 0:
            # All players folded - award pot to last player who acted
            # This is rare but maintains chip conservation
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

                    self._log_hand_event("pot_award", winner.player_id, "win", self.pot, 0.0,
                                       f"All players folded - {winner.name} wins ${self.pot} by default")
                    self.pot = 0

            self.current_state = GameState.SHOWDOWN
            self.current_player_index = None  # No one left to act
            return

        if active_count == 1:
            # Exactly one player remaining - award pot immediately
            winner = next((p for p in self.players if p.is_active), None)
            if winner and self.pot > 0:
                winner.stack += self.pot
                self._log_hand_event("pot_award", winner.player_id, "win", self.pot, 0.0,
                                   f"{winner.name} wins ${self.pot} (all others folded)")
                self.pot = 0
            self.current_state = GameState.SHOWDOWN
            self.current_player_index = None  # No one left to act
            return

        if not self._betting_round_complete():
            return

        # Advance to next state
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
            # Award pot at showdown with proper side pot handling
            self._award_pot_at_showdown()
            return

        # Reset for new betting round
        for player in self.players:
            player.reset_for_new_round()
        self.current_bet = 0
        self.last_raiser_index = None

        # First to act is after dealer
        first_to_act = self._get_next_active_player_index(self.dealer_index + 1)
        self.current_player_index = first_to_act

        # Process actions if no human or human not first
        self._process_remaining_actions()

        # Check if hand should end after processing actions
        self._maybe_advance_state()

    def _award_pot_at_showdown(self):
        """Award pot to winners at showdown. Called automatically when reaching SHOWDOWN."""
        if self.pot == 0:
            return  # No pot to award

        pots = self.hand_evaluator.determine_winners_with_side_pots(self.players, self.community_cards)

        # Distribute winnings with proper remainder handling
        for pot_info in pots:
            num_winners = len(pot_info['winners'])
            split_amount = pot_info['amount'] // num_winners
            remainder = pot_info['amount'] % num_winners

            for i, winner_id in enumerate(pot_info['winners']):
                winner = next(p for p in self.players if p.player_id == winner_id)
                award_amount = split_amount + (1 if i < remainder else 0)
                winner.stack += award_amount

                # Log pot award event for winner_info
                self._log_hand_event("pot_award", winner.player_id, "win", award_amount, 0.0,
                                   f"{winner.name} wins ${award_amount} at showdown")

        self.pot = 0

        # QC: Verify chip conservation after pot award
        self._assert_chip_conservation("after _award_pot_at_showdown()")
        self._assert_valid_game_state("after _award_pot_at_showdown()")

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
