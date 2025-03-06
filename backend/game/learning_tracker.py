from typing import Dict, List, Optional, Any
import uuid
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.statistics_manager import get_statistics_manager
from stats.ai_decision_analyzer import get_decision_analyzer
from utils.logger import get_logger
from hooks.game_engine_hooks import get_game_engine_hooks

logger = get_logger("game.learning_tracker")

class LearningTracker:
    """
    Responsible for tracking and analyzing learning-related statistics
    during poker gameplay. This class serves as a facade to the statistics
    and decision analysis components.
    """
    
    def __init__(self):
        """Initialize the learning tracker."""
        try:
            self.stats_manager = get_statistics_manager()
            self.decision_analyzer = get_decision_analyzer()
            self.hooks = get_game_engine_hooks()
            self.session_id = None
            self.current_hand_id = None
            self.enabled = True
            logger.info("Learning tracker initialized")
        except ImportError:
            self.enabled = False
            logger.warning("Learning statistics components not available")
    
    def start_session(self) -> Optional[str]:
        """
        Start a new game session for tracking.
        
        Returns:
            str: Session ID or None if tracking is disabled
        """
        if not self.enabled:
            return None
            
        try:
            self.session_id = self.hooks.start_session()
            logger.info(f"Started learning session: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Error starting learning session: {e}")
            self.enabled = False
            return None
    
    def end_session(self) -> None:
        """End the current game session."""
        if not self.enabled or not self.session_id:
            return
            
        try:
            self.hooks.end_session(self.session_id)
            logger.info(f"Ended learning session: {self.session_id}")
            self.session_id = None
        except Exception as e:
            logger.error(f"Error ending learning session: {e}")
    
    def start_hand(self) -> Optional[str]:
        """
        Start tracking a new hand.
        
        Returns:
            str: Hand ID or None if tracking is disabled
        """
        if not self.enabled:
            return None
            
        try:
            self.current_hand_id = self.hooks.start_hand()
            logger.info(f"Started tracking hand: {self.current_hand_id}")
            return self.current_hand_id
        except Exception as e:
            logger.error(f"Error starting hand tracking: {e}")
            return None
    
    def end_hand(self, winners: Dict[str, int]) -> None:
        """
        End tracking for the current hand.
        
        Args:
            winners: Dictionary mapping player IDs to winnings
        """
        if not self.enabled or not self.current_hand_id:
            return
            
        try:
            self.hooks.end_hand(winners)
            logger.info(f"Ended tracking for hand with winners: {winners}")
            self.current_hand_id = None
        except Exception as e:
            logger.error(f"Error ending hand tracking: {e}")
    
    def track_decision(self, player_id: str, decision: str, 
                      hole_cards: List[str], game_state: Dict[str, Any],
                      deck: List[str], pot_size: int, spr: float) -> None:
        """
        Track and analyze a player's decision.
        
        Args:
            player_id: ID of the player
            decision: The decision made
            hole_cards: Player's hole cards
            game_state: Current game state
            deck: Current deck state
            pot_size: Current pot size
            spr: Stack-to-pot ratio
        """
        if not self.enabled:
            return
            
        # Ensure hand_id is included in game state
        if self.current_hand_id and "hand_id" not in game_state:
            game_state["hand_id"] = self.current_hand_id
            
        try:
            self.hooks.track_human_decision(
                player_id=player_id,
                decision=decision,
                hole_cards=hole_cards,
                game_state=game_state,
                deck=deck,
                pot_size=pot_size,
                spr=spr
            )
        except Exception as e:
            logger.error(f"Error tracking decision: {e}")
    
    def get_learning_feedback(self, player_id: str, num_decisions: int = 1) -> List[str]:
        """
        Get learning feedback for a player.
        
        Args:
            player_id: ID of the player
            num_decisions: Number of recent decisions to analyze
            
        Returns:
            List of feedback messages
        """
        if not self.enabled:
            return ["Learning statistics not enabled"]
            
        try:
            return self.hooks.get_learning_feedback(player_id, num_decisions)
        except Exception as e:
            logger.error(f"Error getting learning feedback: {e}")
            return [f"Error generating feedback: {str(e)}"]
    
    def get_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """
        Get a player's strategy profile.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Strategy profile information
        """
        if not self.enabled:
            return {"error": "Learning statistics not enabled"}
            
        try:
            return self.hooks.get_strategy_profile(player_id)
        except Exception as e:
            logger.error(f"Error getting strategy profile: {e}")
            return {"error": str(e)}