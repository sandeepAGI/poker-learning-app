from typing import List, Dict, Any
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.game_state import GameState
from utils.logger import get_logger

logger = get_logger("game.poker_round")

class PokerRound:
    """Manages a single round of betting in poker."""
    
    def __init__(self, players, dealer_index: int, current_state: GameState, 
                pot: int, current_bet: int, big_blind: int, hand_id: str = None):
        """
        Initialize a poker betting round.
        
        Args:
            players: List of Player objects
            dealer_index: Index of the dealer in the players list
            current_state: Current game state
            pot: Current pot size
            current_bet: Current bet amount
            big_blind: Big blind amount
            hand_id: Optional hand identifier for tracking
        """
        self.players = players
        self.dealer_index = dealer_index
        self.current_state = current_state
        self.pot = pot
        self.current_bet = current_bet
        self.big_blind = big_blind
        self.hand_id = hand_id
    
    def execute_betting_round(self) -> Dict[str, Any]:
        """
        Handles a complete betting round with position-based action order.
        
        Returns:
            Dict containing:
                - pot: Updated pot amount after the betting round
                - active_players: Number of active players at end of round
        """
        max_bet: int = self.big_blind if self.current_state == GameState.PRE_FLOP else 0
        betting_done: bool = False
        active_players_count = sum(1 for p in self.players if p.is_active)

        # Determine starting position based on game state
        start_pos: int = (
            (self.dealer_index + 3) % len(self.players) 
            if self.current_state == GameState.PRE_FLOP
            else (self.dealer_index + 1) % len(self.players)
        )

        # Early exit if only one player is active
        if active_players_count <= 1:
            logger.info(f"Only {active_players_count} active player(s) at start of round, skipping betting")
            return {
                "pot": self.pot,
                "active_players": active_players_count
            }

        while not betting_done:
            betting_done = True
            current_pos = start_pos
            
            # Check active players before each cycle
            active_players_count = sum(1 for p in self.players if p.is_active)
            if active_players_count <= 1:
                logger.info(f"Only {active_players_count} active player(s) remaining, ending betting round")
                break

            for _ in range(len(self.players)):
                player = self.players[current_pos]
                
                if player.is_active and player.stack > 0:
                    # Calculate effective stack and SPR
                    other_active_stacks = [p.stack for p in self.players if p != player and p.is_active]
                    effective_stack = player.stack
                    if other_active_stacks:
                        effective_stack = min(player.stack, max(other_active_stacks))
                    spr = effective_stack / self.pot if self.pot > 0 else float('inf')
                    
                    # Prepare game state information
                    game_state_info = {
                        "hand_id": self.hand_id,
                        "community_cards": [], # This will be set by the PokerGame class
                        "current_bet": max_bet,
                        "pot_size": self.pot,
                        "game_state": self.current_state.value
                    }

                    # Get player decision
                    decision = player.make_decision(
                        game_state=game_state_info,
                        deck=[], # This will be set by the PokerGame class
                        spr=spr,
                        pot_size=self.pot
                    )

                    # Process decision
                    if decision == "call":
                        bet_amount = min(max_bet - player.current_bet, player.stack)
                        logger.debug(f"Player {player.player_id} calls with {bet_amount}")
                    elif decision == "raise":
                        min_raise = max(min(max_bet * 2, player.stack), self.big_blind)
                        bet_amount = min_raise - player.current_bet
                        max_bet = player.current_bet + bet_amount
                        betting_done = False
                        logger.debug(f"Player {player.player_id} raises to {max_bet}")
                    else:  # fold
                        bet_amount = 0
                        player.is_active = False
                        logger.debug(f"Player {player.player_id} folds")
                        
                        # Check for remaining active players after fold
                        active_players_count = sum(1 for p in self.players if p.is_active)
                        if active_players_count <= 1:
                            logger.info(f"Only {active_players_count} active player(s) remaining after fold")
                            # Don't break here - just track the count for PokerGame to handle

                    if bet_amount > 0:
                        player.bet(bet_amount)
                        self.pot += bet_amount

                current_pos = (current_pos + 1) % len(self.players)

        # Reset player bet amounts for next round
        for player in self.players:
            player.reset_round_state()
            
        # Update active player count before returning
        active_players_count = sum(1 for p in self.players if p.is_active)
        
        logger.info(f"Betting round complete for {self.current_state.value}, pot: {self.pot}, active players: {active_players_count}")
        
        return {
            "pot": self.pot,
            "active_players": active_players_count
        }