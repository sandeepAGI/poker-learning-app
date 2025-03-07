# backend/services/player_service.py
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

# Import error classes
from utils.errors import (
    PlayerNotFoundError
)

class PlayerService:
    # Mock storage
    _players = {}
    
    def create_player(self, username: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new player profile"""
        player_id = str(uuid.uuid4())
        
        # Initialize player record
        player = {
            "player_id": player_id,
            "username": username,
            "settings": settings or {},
            "created_at": datetime.now(),
            "statistics": {
                "hands_played": 0,
                "hands_won": 0,
                "win_rate": 0.0
            }
        }
        
        # Store player
        self._players[player_id] = player
        
        return player
    
    def get_player(self, player_id: str) -> Dict[str, Any]:
        """Get player information"""
        if player_id not in self._players:
            raise PlayerNotFoundError(player_id)
        
        return self._players[player_id]
    
    def get_player_statistics(self, player_id: str, timeframe: Optional[str] = None, metric_type: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed player statistics"""
        if player_id not in self._players:
            raise PlayerNotFoundError(player_id)
        
        # In a real implementation, this would fetch detailed statistics from StatisticsManager
        # For now, we'll return mock statistics
        
        return {
            "player_id": player_id,
            "basic_stats": {
                "hands_played": 42,
                "hands_won": 15,
                "win_rate": 35.7,
                "showdown_success": 60.0
            },
            "position_stats": {
                "early": {"win_rate": 20.0, "hands_played": 10},
                "middle": {"win_rate": 33.3, "hands_played": 12},
                "late": {"win_rate": 50.0, "hands_played": 14},
                "blinds": {"win_rate": 16.7, "hands_played": 6}
            },
            "strategy_metrics": {
                "vpip": 22.5,
                "pfr": 18.2,
                "aggression_factor": 2.3
            }
        }