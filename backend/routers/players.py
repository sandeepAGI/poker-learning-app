# backend/routers/players.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional

from schemas.player import PlayerCreate, PlayerResponse, PlayerStatistics
from services.player_service import PlayerService

router = APIRouter(tags=["players"])
player_service = PlayerService()

@router.post("/players", response_model=PlayerResponse)
async def create_player(player_data: PlayerCreate):
    """Create a new player profile"""
    return player_service.create_player(
        username=player_data.username,
        settings=player_data.settings
    )

@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: str = Path(..., description="The ID of the player")
):
    """Get player information"""
    return player_service.get_player(player_id)

@router.get("/players/{player_id}/statistics", response_model=PlayerStatistics)
async def get_player_statistics(
    player_id: str = Path(..., description="The ID of the player"),
    timeframe: Optional[str] = Query(None, description="Optional timeframe filter"),
    metric_type: Optional[str] = Query(None, description="Optional metric type filter")
):
    """Get detailed player statistics"""
    return player_service.get_player_statistics(
        player_id=player_id,
        timeframe=timeframe,
        metric_type=metric_type
    )