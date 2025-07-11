from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import sys
import os

# Add the parent directory to sys.path to allow imports from the backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ai.ai_manager import AIDecisionMaker

# Import tracking components conditionally
try:
    from stats.ai_decision_analyzer import get_decision_analyzer
    LEARNING_STATS_ENABLED = True
except ImportError:
    LEARNING_STATS_ENABLED = False

from utils.logger import get_logger

# Create a logger for the player models
logger = get_logger("models.player")

@dataclass
class Player:
    player_id: str
    stack: int = config.STARTING_CHIPS
    hole_cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0
    all_in: bool = False
    total_bet: int = 0  # Tracks total contribution to current hand's pot

    def bet(self, amount: int) -> int:
        """Places a bet, reducing stack size.
        
        Args:
            amount (int): Amount to bet
            
        Returns:
            int: Actual amount bet (may be less if stack is insufficient)
        """
        if amount <= 0:
            logger.warning(f"Player {self.player_id} attempted to bet {amount}, which is <= 0")
            return 0
            
        old_stack = self.stack  # For logging
        
        if amount > self.stack:
            amount = self.stack
            self.all_in = True
            logger.info(f"Player {self.player_id} going all-in with {amount}")
            
        self.stack -= amount
        self.current_bet += amount
        self.total_bet += amount  # Update total contribution to the pot
        
        logger.debug(f"Player {self.player_id} bet {amount}, stack: {old_stack} -> {self.stack}")
        
        # Verify consistency
        if self.stack != old_stack - amount:
            logger.error(f"STACK ERROR: Player {self.player_id} stack ({self.stack}) does not match expected value ({old_stack - amount})")
            # Fix the stack
            self.stack = old_stack - amount
            logger.info(f"STACK CORRECTED: Fixed {self.player_id} stack to {self.stack}")
            
        return amount

    def add_to_stack(self, amount: int) -> int:
        """Adds chips to player's stack (used for winnings).
        
        Args:
            amount (int): Amount to add to stack
            
        Returns:
            int: New stack size
        """
        if amount <= 0:
            logger.warning(f"Player {self.player_id} attempted to add {amount} to stack, which is <= 0")
            return self.stack
            
        old_stack = self.stack
        self.stack += amount
        
        logger.debug(f"Player {self.player_id} stack increased by {amount}: {old_stack} -> {self.stack}")
        
        # Verify consistency
        if self.stack != old_stack + amount:
            logger.error(f"STACK ERROR: Player {self.player_id} stack ({self.stack}) does not match expected value ({old_stack + amount})")
            # Fix the stack
            self.stack = old_stack + amount
            logger.info(f"STACK CORRECTED: Fixed {self.player_id} stack to {self.stack}")
            
        return self.stack

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
            logger.info(f"Player {self.player_id} eliminated (stack: {self.stack})")

    def reset_round_state(self) -> None:
        """Resets player state for new betting round."""
        self.current_bet = 0
        
    def reset_hand_state(self) -> None:
        """Resets player state for a new hand."""
        # Store current stack to preserve it
        current_stack = self.stack
        
        # Reset betting state
        self.current_bet = 0
        self.total_bet = 0
        self.all_in = False
        self.hole_cards = []
        
        # Restore stack
        self.stack = current_stack
        
        # IMPORTANT: Always set players to active at the start of a new hand
        # unless they were eliminated due to insufficient chips
        if not self.is_active and current_stack >= 5:
            logger.info(f"Reactivating player {self.player_id} for new hand (stack: {current_stack})")
        
        self.is_active = current_stack >= 5
        
        logger.debug(f"Reset hand state for player {self.player_id}, stack: {self.stack}, active: {self.is_active}")
        
    def make_decision(self, game_state: Dict[str, Any], deck: List[str], 
                     spr: float, pot_size: int) -> str:
        """Base method for player decisions, to be overridden by subclasses.
        
        Args:
            game_state (dict): Current game state information
            deck (List[str]): Current deck state
            spr (float): Stack-to-pot ratio
            pot_size (int): Current pot size
            
        Returns:
            str: Decision ('call', 'raise', or 'fold')
        """
        # Base implementation just folds
        return "fold"

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
class HumanPlayer(Player):
    """Human player extension with decision tracking for learning."""
    
    def make_decision(self, game_state: dict, deck: List[str], spr: float, pot_size: int) -> str:
        """Gets player decision and tracks it for learning.
        
        Args:
            game_state (dict): Current game state information
            deck (List[str]): Current deck state
            spr (float): Stack-to-pot ratio
            pot_size (int): Current pot size
            
        Returns:
            str: Decision ('call', 'raise', or 'fold')
        """
        # In a real implementation, this would get input from the UI
        # For this example, we'll return a default
        decision = "call"  # Replace with actual player input
        
        # Track decision for learning statistics if enabled
        if LEARNING_STATS_ENABLED:
            try:
                decision_analyzer = get_decision_analyzer()
                decision_data = decision_analyzer.analyze_decision(
                    player_id=self.player_id,
                    player_decision=decision,
                    hole_cards=self.hole_cards,
                    game_state=game_state,
                    deck=deck,
                    pot_size=pot_size,
                    spr=spr
                )
                logger.debug(f"Decision analyzed: {decision_data['matching_strategy']} - Optimal: {decision_data['was_optimal']}")
            except Exception as e:
                logger.error(f"Error analyzing decision: {e}")
        
        return decision