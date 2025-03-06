import os
import json
import time
from typing import Dict, List, Any, Optional
from enum import Enum, auto
import uuid

from learning_statistics import LearningStatistics
from logger import get_logger

# Create a logger for the statistics manager
logger = get_logger("statistics_manager")

class Position(Enum):
    """Poker table positions."""
    EARLY = "early"
    MIDDLE = "middle" 
    LATE = "late"
    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"

class PlayerStatistics:
    """Basic statistics about a player's performance."""
    
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.hands_played = 0
        self.hands_won = 0
        self.total_winnings = 0
        self.total_losses = 0
        self.vpip = 0.0  # Voluntarily Put Money In Pot
        self.pfr = 0.0   # Pre-Flop Raise
        self.aggression_factor = 0.0
        self.showdown_count = 0
        self.showdown_wins = 0
        self.position_hands = {pos.value: 0 for pos in Position}
        self.position_wins = {pos.value: 0 for pos in Position}
        
    @property
    def win_rate(self) -> float:
        """Returns the percentage of hands won."""
        if self.hands_played == 0:
            return 0.0
        return (self.hands_won / self.hands_played) * 100
        
    @property
    def showdown_success(self) -> float:
        """Returns the percentage of showdowns won."""
        if self.showdown_count == 0:
            return 0.0
        return (self.showdown_wins / self.showdown_count) * 100
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for serialization."""
        return {
            "player_id": self.player_id,
            "hands_played": self.hands_played,
            "hands_won": self.hands_won,
            "total_winnings": self.total_winnings,
            "total_losses": self.total_losses,
            "vpip": self.vpip,
            "pfr": self.pfr,
            "aggression_factor": self.aggression_factor,
            "showdown_count": self.showdown_count,
            "showdown_wins": self.showdown_wins,
            "position_hands": self.position_hands,
            "position_wins": self.position_wins
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerStatistics':
        """Create a PlayerStatistics object from dictionary data."""
        stats = cls(data["player_id"])
        
        stats.hands_played = data.get("hands_played", 0)
        stats.hands_won = data.get("hands_won", 0)
        stats.total_winnings = data.get("total_winnings", 0)
        stats.total_losses = data.get("total_losses", 0)
        stats.vpip = data.get("vpip", 0.0)
        stats.pfr = data.get("pfr", 0.0)
        stats.aggression_factor = data.get("aggression_factor", 0.0)
        stats.showdown_count = data.get("showdown_count", 0)
        stats.showdown_wins = data.get("showdown_wins", 0)
        stats.position_hands = data.get("position_hands", {})
        stats.position_wins = data.get("position_wins", {})
        
        return stats

class SessionStatistics:
    """Statistics for a single game session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = time.time()
        self.end_time = None
        self.hands_played = 0
        self.players = []
        self.starting_chips = 0
        self.final_chip_counts = {}
        self.elimination_order = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "hands_played": self.hands_played,
            "players": self.players,
            "starting_chips": self.starting_chips,
            "final_chip_counts": self.final_chip_counts,
            "elimination_order": self.elimination_order
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionStatistics':
        """Create a SessionStatistics object from dictionary data."""
        stats = cls(data["session_id"])
        
        stats.start_time = data.get("start_time", 0)
        stats.end_time = data.get("end_time")
        stats.hands_played = data.get("hands_played", 0)
        stats.players = data.get("players", [])
        stats.starting_chips = data.get("starting_chips", 0)
        stats.final_chip_counts = data.get("final_chip_counts", {})
        stats.elimination_order = data.get("elimination_order", [])
        
        return stats

class StatisticsManager:
    """
    Manages storage and retrieval of game statistics.
    Handles player statistics, session statistics, and learning statistics.
    """
    
    # Maximum number of sessions to keep detailed data for
    MAX_SESSIONS = 5
    
    # Base directory for storing statistics
    DATA_DIR = "game_data"
    
    def __init__(self):
        """Initialize the statistics manager."""
        self._player_stats: Dict[str, PlayerStatistics] = {}
        self._session_stats: Dict[str, SessionStatistics] = {}
        self._learning_stats: Dict[str, LearningStatistics] = {}
        self.current_session_id: Optional[str] = None
        
        # Ensure data directory exists
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, "players"), exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, "sessions"), exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, "learning"), exist_ok=True)
        
        logger.info("Statistics manager initialized")
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new game session.
        
        Args:
            session_id: Optional session ID, will generate one if not provided
            
        Returns:
            The session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        self.current_session_id = session_id
        
        # Create new session statistics
        session_stats = SessionStatistics(session_id)
        self._session_stats[session_id] = session_stats
        
        # Update learning statistics for all tracked players
        for player_id, learning_stats in self._learning_stats.items():
            learning_stats.current_session_id = session_id
            
        logger.info(f"Started new session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str) -> None:
        """
        End a game session and finalize statistics.
        
        Args:
            session_id: ID of the session to end
        """
        if session_id not in self._session_stats:
            logger.warning(f"Cannot end unknown session: {session_id}")
            return
            
        session_stats = self._session_stats[session_id]
        session_stats.end_time = time.time()
        
        # Save session statistics
        self._save_session_statistics(session_id)
        
        # Prune old session data
        self._prune_old_sessions()
        
        if self.current_session_id == session_id:
            self.current_session_id = None
            
        logger.info(f"Ended session: {session_id}")
    
    def get_player_statistics(self, player_id: str) -> Optional[PlayerStatistics]:
        """
        Get statistics for a specific player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            PlayerStatistics object or None if not found
        """
        if player_id not in self._player_stats:
            # Try to load from disk
            self._load_player_statistics(player_id)
            
        return self._player_stats.get(player_id)
    
    def get_session_statistics(self, session_id: str) -> Optional[SessionStatistics]:
        """
        Get statistics for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            SessionStatistics object or None if not found
        """
        if session_id not in self._session_stats:
            # Try to load from disk
            self._load_session_statistics(session_id)
            
        return self._session_stats.get(session_id)
    
    def get_learning_statistics(self, player_id: str) -> LearningStatistics:
        """
        Get learning statistics for a player, creating if needed.
        
        Args:
            player_id: ID of the player
            
        Returns:
            LearningStatistics object
        """
        if player_id not in self._learning_stats:
            # Try to load from disk
            self._load_learning_statistics(player_id)
            
            # If still not found, create new
            if player_id not in self._learning_stats:
                self._learning_stats[player_id] = LearningStatistics(player_id)
                
        return self._learning_stats[player_id]
    
    def record_decision(self, player_id: str, decision_data: Dict[str, Any]) -> None:
        """
        Record a player's decision with context and classification.
        
        Args:
            player_id: ID of the player who made the decision
            decision_data: Dictionary containing decision context and analysis
        """
        # Add metadata
        decision_data["timestamp"] = time.time()
        decision_data["session_id"] = self.current_session_id
        
        # Get learning statistics and add decision
        learning_stats = self.get_learning_statistics(player_id)
        learning_stats.add_decision(decision_data)
        
        # Save learning statistics
        self._save_learning_statistics(player_id)
        
        logger.debug(f"Recorded decision for player {player_id}: {decision_data['decision']}")
    
    def _load_player_statistics(self, player_id: str) -> None:
        """Load player statistics from disk."""
        file_path = os.path.join(self.DATA_DIR, "players", f"{player_id}.json")
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self._player_stats[player_id] = PlayerStatistics.from_dict(data)
                    logger.debug(f"Loaded statistics for player: {player_id}")
        except Exception as e:
            logger.error(f"Error loading player statistics for {player_id}: {e}")
    
    def _save_player_statistics(self, player_id: str) -> None:
        """Save player statistics to disk."""
        if player_id not in self._player_stats:
            return
            
        file_path = os.path.join(self.DATA_DIR, "players", f"{player_id}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self._player_stats[player_id].to_dict(), f, indent=2)
                logger.debug(f"Saved statistics for player: {player_id}")
        except Exception as e:
            logger.error(f"Error saving player statistics for {player_id}: {e}")
    
    def _load_session_statistics(self, session_id: str) -> None:
        """Load session statistics from disk."""
        file_path = os.path.join(self.DATA_DIR, "sessions", f"{session_id}.json")
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self._session_stats[session_id] = SessionStatistics.from_dict(data)
                    logger.debug(f"Loaded statistics for session: {session_id}")
        except Exception as e:
            logger.error(f"Error loading session statistics for {session_id}: {e}")
    
    def _save_session_statistics(self, session_id: str) -> None:
        """Save session statistics to disk."""
        if session_id not in self._session_stats:
            return
            
        file_path = os.path.join(self.DATA_DIR, "sessions", f"{session_id}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self._session_stats[session_id].to_dict(), f, indent=2)
                logger.debug(f"Saved statistics for session: {session_id}")
        except Exception as e:
            logger.error(f"Error saving session statistics for {session_id}: {e}")
    
    def _load_learning_statistics(self, player_id: str) -> None:
        """Load learning statistics from disk."""
        file_path = os.path.join(self.DATA_DIR, "learning", f"{player_id}.json")
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self._learning_stats[player_id] = LearningStatistics.from_dict(data)
                    logger.debug(f"Loaded learning statistics for player: {player_id}")
        except Exception as e:
            logger.error(f"Error loading learning statistics for {player_id}: {e}")
    
    def _save_learning_statistics(self, player_id: str) -> None:
        """Save learning statistics to disk."""
        if player_id not in self._learning_stats:
            return
            
        file_path = os.path.join(self.DATA_DIR, "learning", f"{player_id}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self._learning_stats[player_id].to_dict(), f, indent=2)
                logger.debug(f"Saved learning statistics for player: {player_id}")
        except Exception as e:
            logger.error(f"Error saving learning statistics for {player_id}: {e}")
    
    def _prune_old_sessions(self) -> None:
        """
        Remove detailed data for sessions beyond the retention policy.
        Keeps aggregate statistics for all sessions.
        """
        # Get list of session files
        sessions_dir = os.path.join(self.DATA_DIR, "sessions")
        session_files = [f for f in os.listdir(sessions_dir) if f.endswith(".json")]
        
        # If we have more than MAX_SESSIONS, prune the oldest ones
        if len(session_files) > self.MAX_SESSIONS:
            # Sort by modification time (oldest first)
            session_files.sort(key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)))
            
            # Determine how many to prune
            to_prune = len(session_files) - self.MAX_SESSIONS
            
            for i in range(to_prune):
                file_to_prune = session_files[i]
                session_id = file_to_prune.replace(".json", "")
                
                # Remove detailed decision data for this session from all learning statistics
                for player_id, learning_stats in self._learning_stats.items():
                    # Filter out decisions from this session
                    learning_stats.decision_history = [
                        decision for decision in learning_stats.decision_history
                        if decision.get("session_id") != session_id
                    ]
                    # Save the updated learning statistics
                    self._save_learning_statistics(player_id)
                
                logger.info(f"Pruned detailed data for session: {session_id}")

# Create a singleton instance
_statistics_manager = None

def get_statistics_manager() -> StatisticsManager:
    """
    Get the singleton instance of the statistics manager.
    
    Returns:
        StatisticsManager instance
    """
    global _statistics_manager
    if _statistics_manager is None:
        _statistics_manager = StatisticsManager()
    return _statistics_manager