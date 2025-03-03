import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from enum import Enum
import config
from treys import Evaluator, Card
from ai.ai_manager import AIDecisionMaker
from ai.base_ai import BaseAI

class GameState(Enum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

@dataclass
class Player:
    player_id: str
    stack: int = config.STARTING_CHIPS
    hole_cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0
    all_in: bool = False

    def bet(self, amount: int) -> int:
        """Places a bet, reducing stack size.
        
        Args:
            amount (int): Amount to bet
            
        Returns:
            int: Actual amount bet (may be less if stack is insufficient)
        """
        if amount > self.stack:
            amount = self.stack
            self.all_in = True
        self.stack -= amount
        self.current_bet += amount
        return amount

    def receive_cards(self, cards: List[str]) -> None:
        """Assigns hole cards to the player.
        
        Args:
            cards (List[str]): List of card codes to assign
        """
        if self.hole_cards:
            return
        self.hole_cards = cards

    def eliminate(self) -> None:
        """Marks player as eliminated if they have less than 5 chips."""
        if self.stack < 5:
            self.is_active = False

    def reset_round_state(self) -> None:
        """Resets player state for new betting round."""
        self.current_bet = 0

@dataclass
class AIPlayer(Player):
    personality: str = ""

    def make_decision(self, game_state: dict, deck: List[str], spr: float, pot_size: int) -> str:
        """Delegates AI decision-making to ai_manager.py
        
        Args:
            game_state (dict): Current game state information including community cards,
                             current bet, and game state
            deck (List[str]): Current deck state
            spr (float): Stack-to-pot ratio
            pot_size (int): Current pot size

        Returns:
            str: Decision ('call', 'raise', or 'fold')
        """
        return AIDecisionMaker.make_decision(
            personality=self.personality,
            hole_cards=self.hole_cards,
            game_state=game_state,
            deck=deck,
            pot_size=pot_size,
            spr=spr
        )

@dataclass
class PotInfo:
    """Represents a pot and eligible players."""
    amount: int
    eligible_players: List[Player]

@dataclass
class HandResult:
    """Holds hand evaluation results for showdown."""
    player: Player
    score: float
    hand_rank: str



@dataclass
class PokerGame:
    players: List[Player]
    deck: List[str] = field(default_factory=list)
    community_cards: List[str] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    small_blind: int = config.SMALL_BLIND
    big_blind: int = config.BIG_BLIND
    dealer_index: int = -1
    hand_count: int = 0
    evaluator: Evaluator = field(default_factory=Evaluator)
    current_state: GameState = GameState.PRE_FLOP
    last_hand_dealt: int = -1
    last_community_cards: Dict[GameState, int] = field(
        default_factory=lambda: {
            GameState.FLOP: -1,
            GameState.TURN: -1,
            GameState.RIVER: -1
        }
    )

    def reset_deck(self) -> None:
        """Ensures a new shuffled deck at the start of each hand."""
        self.deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(self.deck)

    def deal_hole_cards(self) -> None:
        """Deals 2 hole cards to each active player."""
        for player in self.players:
            if player.is_active and not player.hole_cards:
                hole_cards = self.deck[:2]
                player.receive_cards(hole_cards)
                self.deck = self.deck[2:]
        self.last_hand_dealt = self.hand_count

    def deal_community_cards(self) -> None:
        """Deals community cards based on current game state."""
        current_hand = self.hand_count

        if self.current_state == GameState.FLOP:
            if self.last_community_cards[GameState.FLOP] == current_hand:
                return
            self.deck = self.deck[1:]  # Burn card
            flop_cards = self.deck[:3]
            self.community_cards.extend(flop_cards)
            self.deck = self.deck[3:]
            self.last_community_cards[GameState.FLOP] = current_hand

        elif self.current_state == GameState.TURN:
            if self.last_community_cards[GameState.TURN] == current_hand:
                return
            self.deck = self.deck[1:]  # Burn card
            turn_card = [self.deck[0]]
            self.community_cards.extend(turn_card)
            self.deck = self.deck[1:]
            self.last_community_cards[GameState.TURN] = current_hand

        elif self.current_state == GameState.RIVER:
            if self.last_community_cards[GameState.RIVER] == current_hand:
                return
            self.deck = self.deck[1:]  # Burn card
            river_card = [self.deck[0]]
            self.community_cards.extend(river_card)
            self.deck = self.deck[1:]
            self.last_community_cards[GameState.RIVER] = current_hand

    def post_blinds(self) -> None:
        """Assigns small and big blinds at the start of each hand."""
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        sb_index = (self.dealer_index + 1) % len(self.players)

        if self.hand_count > 1:
            previous_sb = (self.dealer_index) % len(self.players)
            bb_index = previous_sb
        else:
            bb_index = (sb_index + 1) % len(self.players)

        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]

        sb_player.bet(self.small_blind)
        bb_player.bet(self.big_blind)

        self.pot += self.small_blind + self.big_blind
        self.current_bet = self.big_blind

        if self.hand_count % 2 == 0:
            self.small_blind += config.BLIND_INCREASE
            self.big_blind = self.small_blind * 2

        if self.hand_count > self.last_hand_dealt:
            self.deal_hole_cards()

    def betting_round(self) -> None:
        """Handles betting rounds with position-based action order."""
        max_bet: int = self.big_blind if self.current_state == GameState.PRE_FLOP else 0
        betting_done: bool = False

        # Determine starting position based on game state
        start_pos: int = (
            (self.dealer_index + 3) % len(self.players) 
            if self.current_state == GameState.PRE_FLOP
            else (self.dealer_index + 1) % len(self.players)
        )

        while not betting_done:
            betting_done = True
            current_pos = start_pos

            for _ in range(len(self.players)):
                player = self.players[current_pos]
                
                if isinstance(player, AIPlayer) and player.is_active and player.stack > 0:
                    effective_stack = min(
                        player.stack,
                        max(p.stack for p in self.players if p != player and p.is_active)
                    )
                    spr = effective_stack / self.pot if self.pot > 0 else float('inf')
                    
                    game_state_info = {
                        "community_cards": self.community_cards,
                        "current_bet": max_bet,
                        "pot_size": self.pot,
                        "game_state": self.current_state.value
                    }

                    decision = player.make_decision(
                        game_state=game_state_info,
                        deck=self.deck,
                        spr=spr,
                        pot_size=self.pot
                    )

                    if decision == "call":
                        bet_amount = min(max_bet - player.current_bet, player.stack)
                    elif decision == "raise":
                        bet_amount = max(min(max_bet * 2, player.stack), self.big_blind)
                        max_bet = player.current_bet + bet_amount
                        betting_done = False
                    else:  # fold
                        bet_amount = 0
                        player.is_active = False

                    if bet_amount > 0:
                        player.bet(bet_amount)
                        self.pot += bet_amount

                current_pos = (current_pos + 1) % len(self.players)

        # Reset player bet amounts for next round
        for player in self.players:
            player.reset_round_state()

    def advance_game_state(self) -> None:
        """Advances the game to the next state and handles necessary actions."""
        state_order = [
            GameState.PRE_FLOP,
            GameState.FLOP,
            GameState.TURN,
            GameState.RIVER,
            GameState.SHOWDOWN
        ]
        
        current_index = state_order.index(self.current_state)
        
        if current_index < len(state_order) - 1:
            self.current_state = state_order[current_index + 1]
            if self.current_state in [GameState.FLOP, GameState.TURN, GameState.RIVER]:
                self.deal_community_cards()

    def play_hand(self) -> None:
        """Manages the complete flow of a poker hand."""
        self.current_state = GameState.PRE_FLOP
        self.community_cards = []
        self.post_blinds()

        while self.current_state != GameState.SHOWDOWN:
            active_players = sum(1 for p in self.players if p.is_active)
            if active_players <= 1:
                self.distribute_pot(self.deck)
                break

            self.betting_round()
            self.advance_game_state()

        if self.current_state == GameState.SHOWDOWN:
            self.distribute_pot(self.deck)

        self.hand_count += 1
        self.community_cards = []
        for player in self.players:
            player.hole_cards = []
            player.current_bet = 0
            player.all_in = False

    def calculate_pots(self) -> List[PotInfo]:
        """Calculate main pot and side pots based on player bets.
    
        Returns:
            List[PotInfo]: List of pots with their eligible players
        """
        all_pots = []
        remaining_players = [p for p in self.players if p.is_active]
    
        while remaining_players:
            # Find smallest bet amount among remaining players
            min_bet = min(p.current_bet for p in remaining_players)
            if min_bet == 0:
                break
            
            # Calculate pot amount and eligible players
            eligible = [p for p in self.players if p.is_active and p.current_bet >= min_bet]
            pot_amount = min_bet * len(eligible)
            all_pots.append(PotInfo(pot_amount, eligible))
        
            # Subtract processed bet amount from all players
            for player in self.players:
                if player.current_bet >= min_bet:
                    player.current_bet -= min_bet
                
            # Update remaining players
            remaining_players = [p for p in self.players 
                               if p.is_active and p.current_bet > 0]
    
        # Add any remaining amount to the first pot
        remaining_total = sum(p.current_bet for p in self.players)
        if remaining_total > 0 and all_pots:
            all_pots[0].amount += remaining_total
        
        return all_pots
    
    def distribute_pot(self, deck: List[str]) -> None:
        """Determines winners and distributes main and side pots.
    
        Args:
            deck (List[str]): Current deck state for hand evaluation
        """
        active_players = [p for p in self.players if p.is_active]
    
        # Single player remaining - award pot directly
        if len(active_players) == 1:
            active_players[0].stack += self.pot
            self.pot = 0
            return
        
        # Calculate all pots (main and side pots)
        pots = self.calculate_pots()
    
        # Process each pot
        for pot in pots:
            # Get hand results for all eligible players
            results = []
            for player in pot.eligible_players:
                if player.hole_cards:
                    score, rank = BaseAI().evaluate_hand(
                        hole_cards=player.hole_cards,
                        community_cards=self.community_cards,
                        deck=deck
                    )
                    results.append(HandResult(player, score, rank))
        
            if not results:
                continue
            
            # Find best hand(s)
            best_score = min(r.score for r in results)
            winners = [r for r in results if r.score == best_score]
        
            # Split pot among winners
            amount_per_player = pot.amount // len(winners)
            remainder = pot.amount % len(winners)
        
            for result in winners:
                result.player.stack += amount_per_player
                if remainder > 0:
                    result.player.stack += 1
                    remainder -= 1

        # Reset pot
        self.pot = 0
    
        # Check for eliminations
        for player in self.players:
            player.eliminate()