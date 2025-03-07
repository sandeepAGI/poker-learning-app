# backend/schemas/player.py
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Create player request
class PlayerCreate(BaseModel):
    username: str
    settings: Optional[Dict[str, Any]] = None

# Player response
class PlayerResponse(BaseModel):
    player_id: str
    username: str
    created_at: datetime
    statistics: Dict[str, Any]
    access_token: Optional[str] = None  # Only included when creating a new player

# Player statistics response
class PlayerStatistics(BaseModel):
    player_id: str
    basic_stats: Dict[str, Any]
    position_stats: Dict[str, Dict[str, Any]]
    strategy_metrics: Dict[str, float]