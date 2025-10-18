# Poker Game Engine - Simplified from your excellent implementation
import random
import json
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from treys import Evaluator, Card

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

@dataclass
class Player:
    player_id: str
    name: str
    stack: int = 1000
    hole_cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0
    all_in: bool = False
    is_human: bool = False
    personality: str = ""

    def bet(self, amount: int) -> int:
        """Place a bet, reducing stack."""
        if amount > self.stack:
            amount = self.stack
            self.all_in = True
        
        self.stack -= amount
        self.current_bet += amount
        return amount

    def reset_for_new_hand(self):
        """Reset player for new hand."""
        self.current_bet = 0
        self.all_in = False
        self.hole_cards = []
        self.is_active = self.stack >= 5  # Reactivate if they have chips

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
            # Remove known cards
            for card in hole_cards + community_cards:
                if card in remaining_deck:
                    remaining_deck.remove(card)
            
            scores = []
            for _ in range(20):  # Quick simulation
                sim_deck = remaining_deck.copy()
                random.shuffle(sim_deck)
                sim_board = board + [Card.new(c.replace("10", "T")) for c in sim_deck[:5-len(board)]]
                scores.append(self.evaluator.evaluate(sim_board, hole))
            
            avg_score = sum(scores) / len(scores)
            rank = self.evaluator.get_rank_class(int(avg_score))
            rank_str = self.evaluator.class_to_string(rank)
            return avg_score, rank_str
        
        return 7500, "High Card"  # Default

    def determine_winners(self, players: List[Player], community_cards: List[str]) -> Dict[str, int]:
        """Determine hand winners."""
        active_players = [p for p in players if p.is_active or p.all_in]
        
        if len(active_players) <= 1:
            winner = active_players[0] if active_players else None
            return {winner.player_id: 1} if winner else {}
        
        # Evaluate all hands
        hands = {}
        for player in active_players:
            if player.hole_cards:
                score, rank = self.evaluate_hand(player.hole_cards, community_cards)
                hands[player.player_id] = (score, rank, player)
        
        if not hands:
            return {}
        
        # Find best hand (lowest score in Treys)
        best_score = min(hand[0] for hand in hands.values())
        winners = [player_id for player_id, (score, rank, player) in hands.items() if score == best_score]
        
        return {winner_id: 1 for winner_id in winners}  # Equal split

class AIStrategy:
    """AI strategies with decision reasoning for learning."""
    
    @staticmethod
    def make_decision_with_reasoning(personality: str, hole_cards: List[str], community_cards: List[str], 
                                   current_bet: int, pot_size: int, player_stack: int, player_bet: int = 0) -> AIDecision:
        """Make AI decision with full reasoning for transparency."""
        
        # Hand strength calculation
        evaluator = HandEvaluator()
        hand_score, hand_rank = evaluator.evaluate_hand(hole_cards, community_cards)
        
        # Proper hand strength based on poker hand rankings
        # Treys scores: Royal Flush=1, Straight Flush=2-10, Four of a Kind=11-166, etc.
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
            hand_strength = 0.25  # Most pairs are weak
        else:  # High card
            hand_strength = 0.05  # Very weak
        
        # Pot odds calculation
        call_amount = current_bet - player_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0
        
        # Position and stack considerations
        effective_stack = min(player_stack, 1000)  # Simplified
        stack_pressure = player_stack / 1000  # Stack to starting ratio
        
        if personality == "Conservative":
            if hand_strength >= 0.75:  # Flush or better
                action = "raise" if random.random() > 0.3 else "call"
                amount = min(current_bet * 2, player_stack // 4) if action == "raise" else call_amount
                reasoning = f"Premium hand ({hand_rank}, strength: {hand_strength:.1%}). Conservative value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, strength: {hand_strength:.1%}). Conservative call."
                confidence = 0.7
            elif hand_strength >= 0.25 and call_amount <= player_stack // 20:  # Pairs, small bet only
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, strength: {hand_strength:.1%}). Small bet, worth a call."
                confidence = 0.5
            else:
                action = "fold"
                amount = 0
                reasoning = f"Weak hand ({hand_rank}, strength: {hand_strength:.1%}). Conservative fold."
                confidence = 0.9
                
        elif personality == "Aggressive":
            if hand_strength >= 0.55:  # Three of a kind or better
                action = "raise" if random.random() > 0.2 else "call"
                amount = min(current_bet * 3, player_stack // 3) if action == "raise" else call_amount
                reasoning = f"Strong hand ({hand_rank}, strength: {hand_strength:.1%}). Aggressive value betting."
                confidence = 0.8
            elif hand_strength >= 0.25:  # Any pair
                if random.random() > 0.4:  # 60% of time
                    action = "raise" if random.random() > 0.6 else "call"
                    amount = min(current_bet * 2, player_stack // 4) if action == "raise" else call_amount
                    reasoning = f"Playable hand ({hand_rank}, strength: {hand_strength:.1%}). Aggressive play to build pot."
                    confidence = 0.6
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Marginal hand ({hand_rank}). Aggressive fold to control pot size."
                    confidence = 0.5
            else:  # High card
                if random.random() > 0.7 and call_amount <= player_stack // 40:  # 30% bluff, tiny bets only
                    action = "raise"
                    amount = min(current_bet * 2, player_stack // 6)
                    reasoning = f"Weak hand ({hand_rank}) but bluffing for fold equity. Aggressive move."
                    confidence = 0.3
                else:
                    action = "fold"
                    amount = 0
                    reasoning = f"Too weak to continue ({hand_rank}, strength: {hand_strength:.1%}). Smart aggression."
                    confidence = 0.8
                    
        elif personality == "Mathematical":
            # Mathematical approach with proper poker thresholds
            if hand_strength >= 0.65:  # Straight or better
                action = "raise"
                amount = min(current_bet * 2, player_stack // 3)
                reasoning = f"Strong hand ({hand_rank}, {hand_strength:.1%}). Mathematical value betting."
                confidence = 0.9
            elif hand_strength >= 0.45:  # Two pair or better
                action = "call"
                amount = call_amount
                reasoning = f"Solid hand ({hand_rank}, {hand_strength:.1%}). Positive expectation call."
                confidence = 0.8
            elif hand_strength >= 0.25 and pot_odds <= 0.33:  # Pairs with good pot odds
                action = "call"
                amount = call_amount
                reasoning = f"Marginal hand ({hand_rank}, {hand_strength:.1%}) but pot odds ({pot_odds:.1%}) justify call."
                confidence = 0.6
            elif hand_strength >= 0.25:  # Pairs with poor pot odds
                action = "fold"
                amount = 0
                reasoning = f"Pair ({hand_rank}) but pot odds ({pot_odds:.1%}) too poor. Mathematical fold."
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
            confidence=confidence
        )
    
    @staticmethod
    def make_decision(personality: str, hole_cards: List[str], community_cards: List[str], 
                     current_bet: int, pot_size: int, player_stack: int) -> str:
        """Legacy method for backward compatibility."""
        decision = AIStrategy.make_decision_with_reasoning(
            personality, hole_cards, community_cards, current_bet, pot_size, player_stack
        )
        return decision.action

class PokerGame:
    """Main poker game class - simplified from your excellent implementation."""
    
    def __init__(self, human_player_name: str):
        self.deck_manager = DeckManager()
        self.hand_evaluator = HandEvaluator()
        
        # Create players
        self.players = [
            Player("human", human_player_name, is_human=True),
            Player("ai1", "AI Conservative", personality="Conservative"),
            Player("ai2", "AI Aggressive", personality="Aggressive"), 
            Player("ai3", "AI Mathematical", personality="Mathematical")
        ]
        
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        self.dealer_index = 0
        self.hand_count = 0
        
        # Learning features
        self.hand_events: List[HandEvent] = []
        self.current_hand_events: List[HandEvent] = []
        self.last_ai_decisions: Dict[str, AIDecision] = {}
    
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
        
    def start_new_hand(self):
        """Start a new poker hand."""
        # Save previous hand events to history
        if self.current_hand_events:
            self.hand_events.extend(self.current_hand_events)
        
        self.hand_count += 1
        self.current_hand_events = []  # Reset for new hand
        self.last_ai_decisions = {}
        
        # Reset for new hand
        for player in self.players:
            player.reset_for_new_hand()
        
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        
        # Reset deck
        self.deck_manager.reset()
        
        # Deal hole cards and log events
        for player in self.players:
            if player.is_active:
                player.hole_cards = self.deck_manager.deal_cards(2)
                self._log_hand_event("deal", player.player_id, "hole_cards", 0, 0.0, 
                                   f"Dealt {len(player.hole_cards)} hole cards")
        
        # Post blinds
        self._post_blinds()
    
    def _post_blinds(self):
        """Post small and big blinds."""
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)
        
        # Post blinds
        sb_amount = self.players[sb_index].bet(5)
        bb_amount = self.players[bb_index].bet(10)
        
        self.pot += sb_amount + bb_amount
        self.current_bet = 10
    
    def submit_human_action(self, action: str, amount: int = None) -> bool:
        """Process human player action with logging."""
        human_player = next(p for p in self.players if p.is_human)
        
        if not human_player.is_active:
            return False
        
        # Calculate hand strength for human player using same logic as AI
        hand_strength = 0.0
        if human_player.hole_cards:
            hand_score, _ = self.hand_evaluator.evaluate_hand(human_player.hole_cards, self.community_cards)
            # Use same proper hand strength calculation as AI
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
        
        if action == "fold":
            human_player.is_active = False
            self._log_hand_event("action", human_player.player_id, "fold", 0, 
                               hand_strength, f"Human player folded with {hand_strength:.1%} hand strength")
        elif action == "call":
            call_amount = self.current_bet - human_player.current_bet
            bet_amount = human_player.bet(call_amount)
            self.pot += bet_amount
            self._log_hand_event("action", human_player.player_id, "call", bet_amount,
                               hand_strength, f"Human called ${call_amount}")
        elif action == "raise" and amount:
            bet_amount = human_player.bet(amount)
            self.pot += bet_amount
            self.current_bet = amount
            self._log_hand_event("action", human_player.player_id, "raise", bet_amount,
                               hand_strength, f"Human raised to ${amount}")
        
        # Process AI actions
        self._process_ai_actions()
        
        # Advance game if betting round complete
        self._maybe_advance_state()
        
        return True
    
    def _process_ai_actions(self):
        """Process AI player actions with reasoning for learning."""
        for player in self.players:
            if not player.is_human and player.is_active and not player.all_in:
                # Get AI decision with full reasoning
                ai_decision = AIStrategy.make_decision_with_reasoning(
                    player.personality, player.hole_cards, self.community_cards,
                    self.current_bet, self.pot, player.stack, player.current_bet
                )
                
                # Store decision for frontend display
                self.last_ai_decisions[player.player_id] = ai_decision
                
                # Process the action
                if ai_decision.action == "fold":
                    player.is_active = False
                    self._log_hand_event("action", player.player_id, "fold", 0, 
                                       ai_decision.hand_strength, ai_decision.reasoning)
                elif ai_decision.action == "call":
                    call_amount = self.current_bet - player.current_bet
                    bet_amount = player.bet(call_amount)
                    self.pot += bet_amount
                    self._log_hand_event("action", player.player_id, "call", bet_amount,
                                       ai_decision.hand_strength, ai_decision.reasoning)
                elif ai_decision.action == "raise":
                    raise_amount = min(ai_decision.amount, player.stack)
                    total_bet = raise_amount + player.current_bet
                    bet_amount = player.bet(raise_amount)
                    self.pot += bet_amount
                    self.current_bet = max(self.current_bet, total_bet)
                    self._log_hand_event("action", player.player_id, "raise", bet_amount,
                                       ai_decision.hand_strength, ai_decision.reasoning)
    
    def _maybe_advance_state(self):
        """Advance game state if betting round is complete."""
        active_count = sum(1 for p in self.players if p.is_active)
        if active_count <= 1:
            self.current_state = GameState.SHOWDOWN
            return
        
        # Check if all active players have matched current bet
        all_matched = all(
            p.current_bet == self.current_bet or not p.is_active or p.all_in 
            for p in self.players
        )
        
        if all_matched:
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
            
            # Reset betting for new round
            for player in self.players:
                player.current_bet = 0
            self.current_bet = 0
    
    def get_showdown_results(self) -> Optional[Dict]:
        """Get showdown results if in showdown state."""
        if self.current_state != GameState.SHOWDOWN:
            return None
        
        winners = self.hand_evaluator.determine_winners(self.players, self.community_cards)
        
        # Distribute pot
        if winners:
            split_amount = self.pot // len(winners)
            for winner_id in winners:
                winner = next(p for p in self.players if p.player_id == winner_id)
                winner.stack += split_amount
        
        self.pot = 0
        return {
            "winners": winners,
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
        return {
            "game_state": self.current_state.value,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "stack": p.stack,
                    "current_bet": p.current_bet,
                    "is_active": p.is_active,
                    "all_in": p.all_in,
                    "hole_cards": p.hole_cards if p.is_human else ["hidden", "hidden"]
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
                } for event in self.current_hand_events[-5:]  # Last 5 events
            ]
        }