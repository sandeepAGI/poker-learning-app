# Poker Game Engine - Simplified from your excellent implementation
import random
import json
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from treys import Evaluator, Card

class GameState(Enum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

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
    """Simple AI strategies extracted from your implementation."""
    
    @staticmethod
    def make_decision(personality: str, hole_cards: List[str], community_cards: List[str], 
                     current_bet: int, pot_size: int, player_stack: int) -> str:
        """Make AI decision based on personality."""
        
        # Quick hand strength estimation
        evaluator = HandEvaluator()
        hand_score, hand_rank = evaluator.evaluate_hand(hole_cards, community_cards)
        
        # Normalize score (lower is better, so invert for strength)
        hand_strength = max(0, (7500 - hand_score) / 7500)
        
        if personality == "Conservative":
            if hand_strength > 0.7:
                return "raise" if random.random() > 0.5 else "call"
            elif hand_strength > 0.4:
                return "call"
            else:
                return "fold"
                
        elif personality == "Aggressive":
            if hand_strength > 0.3:
                return "raise" if random.random() > 0.3 else "call"
            elif hand_strength > 0.1:
                return "call" if random.random() > 0.4 else "fold"
            else:
                return "fold" if random.random() > 0.2 else "call"  # Bluff sometimes
                
        elif personality == "Mathematical":
            # Pot odds based decisions
            pot_odds = current_bet / (pot_size + current_bet) if pot_size > 0 else 0
            if hand_strength > pot_odds + 0.1:
                return "call"
            elif hand_strength > 0.6:
                return "raise"
            else:
                return "fold"
        
        # Default Conservative
        return "call" if hand_strength > 0.4 else "fold"

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
        
    def start_new_hand(self):
        """Start a new poker hand."""
        self.hand_count += 1
        
        # Reset for new hand
        for player in self.players:
            player.reset_for_new_hand()
        
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_state = GameState.PRE_FLOP
        
        # Reset deck
        self.deck_manager.reset()
        
        # Deal hole cards
        for player in self.players:
            if player.is_active:
                player.hole_cards = self.deck_manager.deal_cards(2)
        
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
        """Process human player action."""
        human_player = next(p for p in self.players if p.is_human)
        
        if not human_player.is_active:
            return False
        
        if action == "fold":
            human_player.is_active = False
        elif action == "call":
            call_amount = self.current_bet - human_player.current_bet
            bet_amount = human_player.bet(call_amount)
            self.pot += bet_amount
        elif action == "raise" and amount:
            bet_amount = human_player.bet(amount)
            self.pot += bet_amount
            self.current_bet = amount
        
        # Process AI actions
        self._process_ai_actions()
        
        # Advance game if betting round complete
        self._maybe_advance_state()
        
        return True
    
    def _process_ai_actions(self):
        """Process AI player actions."""
        for player in self.players:
            if not player.is_human and player.is_active and not player.all_in:
                decision = AIStrategy.make_decision(
                    player.personality, player.hole_cards, self.community_cards,
                    self.current_bet, self.pot, player.stack
                )
                
                if decision == "fold":
                    player.is_active = False
                elif decision == "call":
                    call_amount = self.current_bet - player.current_bet
                    bet_amount = player.bet(call_amount)
                    self.pot += bet_amount
                elif decision == "raise":
                    raise_amount = self.current_bet + 20  # Simple raise
                    bet_amount = player.bet(raise_amount)
                    self.pot += bet_amount
                    self.current_bet = raise_amount
    
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
        """Get current game state."""
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
            "hand_count": self.hand_count
        }