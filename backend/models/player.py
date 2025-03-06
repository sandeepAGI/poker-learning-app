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
        if amount > self.stack:
            amount = self.stack
            self.all_in = True
        self.stack -= amount
        self.current_bet += amount
        self.total_bet += amount  # Update total contribution to the pot
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
        
    def reset_hand_state(self) -> None:
        """Resets player state for a new hand."""
        self.current_bet = 0
        self.total_bet = 0
        self.all_in = False
        self.hole_cards = []
        
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