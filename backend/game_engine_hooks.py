from typing import Dict, List, Any, Optional
import uuid

from ai_decision_analyzer import get_decision_analyzer
from statistics_manager import get_statistics_manager
from logger import get_logger

# Create a logger for the game engine hooks
logger = get_logger("game_engine_hooks")

class GameEngineHooks:
    """
    Hooks into the game engine to collect data for learning statistics.
    This is a non-intrusive way to add learning statistics functionality
    without heavily modifying the game engine itself.
    """
    
    def __init__(self):
        """Initialize the game engine hooks."""
        self.decision_analyzer = get_decision_analyzer()
        self.stats_manager = get_statistics_manager()
        self.current_hand_id = None
        self.hand_data = {}
        logger.info("Game engine hooks initialized")
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new game session.
        
        Args:
            session_id: Optional session ID, will generate one if not provided
            
        Returns:
            The session ID
        """
        return self.stats_manager.start_session(session_id)
    
    def end_session(self, session_id: str) -> None:
        """
        End a game session.
        
        Args:
            session_id: ID of the session to end
        """
        self.stats_manager.end_session(session_id)
    
    def start_hand(self, hand_id: Optional[str] = None) -> str:
        """
        Start tracking a new hand.
        
        Args:
            hand_id: Optional hand ID, will generate one if not provided
            
        Returns:
            The hand ID
        """
        if hand_id is None:
            hand_id = str(uuid.uuid4())
            
        self.current_hand_id = hand_id
        self.hand_data = {
            "hand_id": hand_id,
            "players": {},
            "community_cards": [],
            "pot_size": 0,
            "current_bet": 0
        }
        
        logger.info(f"Started tracking hand: {hand_id}")
        return hand_id
    
    def end_hand(self, winners: Dict[str, int]) -> None:
        """
        End tracking for the current hand.
        
        Args:
            winners: Dictionary mapping player IDs to winnings
        """
        if not self.current_hand_id:
            return
            
        self.hand_data["winners"] = winners
        
        # Additional end-of-hand processing could go here
        
        self.current_hand_id = None
        self.hand_data = {}
        
        logger.info(f"Ended tracking for hand with winners: {winners}")
    
    def track_human_decision(self, player_id: str, decision: str, 
                           hole_cards: List[str], game_state: Dict[str, Any],
                           deck: List[str], pot_size: int, spr: float) -> Dict[str, Any]:
        """
        Track and analyze a human player's decision.
        
        Args:
            player_id: ID of the player
            decision: The decision made ("fold", "call", or "raise")
            hole_cards: Player's hole cards
            game_state: Current game state
            deck: Current deck state
            pot_size: Current pot size
            spr: Stack-to-pot ratio
            
        Returns:
            Dictionary containing decision analysis
        """
        # Ensure hand_id is included in game state
        if self.current_hand_id and "hand_id" not in game_state:
            game_state["hand_id"] = self.current_hand_id
            
        # Analyze the decision
        decision_data = self.decision_analyzer.analyze_decision(
            player_id=player_id,
            player_decision=decision,
            hole_cards=hole_cards,
            game_state=game_state,
            deck=deck,
            pot_size=pot_size,
            spr=spr
        )
        
        # Store the decision in hand data for later analysis
        if self.current_hand_id:
            if player_id not in self.hand_data["players"]:
                self.hand_data["players"][player_id] = []
                
            self.hand_data["players"][player_id].append(decision_data)
        
        logger.info(f"Tracked decision for player {player_id}: {decision}")
        return decision_data
    
    def get_learning_feedback(self, player_id: str, num_decisions: int = 1) -> List[str]:
        """
        Get learning feedback for a player based on recent decisions.
        
        Args:
            player_id: ID of the player
            num_decisions: Number of recent decisions to generate feedback for
            
        Returns:
            List of feedback messages
        """
        learning_stats = self.stats_manager.get_learning_statistics(player_id)
        recent_decisions = learning_stats.get_recent_decisions(num_decisions)
        
        feedback = []
        for decision_data in recent_decisions:
            feedback.append(self.decision_analyzer.generate_feedback(decision_data))
            
        return feedback
    
    def get_strategy_profile(self, player_id: str) -> Dict[str, Any]:
        """
        Get a player's strategy profile.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Strategy profile information
        """
        return self.decision_analyzer.get_player_strategy_profile(player_id)

# Create a singleton instance
_game_engine_hooks = None

def get_game_engine_hooks() -> GameEngineHooks:
    """
    Get the singleton instance of the game engine hooks.
    
    Returns:
        GameEngineHooks instance
    """
    global _game_engine_hooks
    if _game_engine_hooks is None:
        _game_engine_hooks = GameEngineHooks()
    return _game_engine_hooks