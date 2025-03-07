# backend/routers/players.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional

from schemas.player import PlayerCreate, PlayerResponse, PlayerStatistics
from services.player_service import PlayerService
from utils.auth import get_current_player, create_access_token
from datetime import timedelta

router = APIRouter(tags=["players"])
player_service = PlayerService()

@router.post("/players", response_model=PlayerResponse)
async def create_player(player_data: PlayerCreate):
    """Create a new player profile"""
    # This is the only endpoint that doesn't require authentication
    player = player_service.create_player(
        username=player_data.username,
        settings=player_data.settings
    )
    
    # Generate token for the new player
    access_token = create_access_token(
        data={"sub": player["player_id"]},
        expires_delta=timedelta(days=30)  # Longer expiry for better UX
    )
    
    # Add token to response
    player["access_token"] = access_token
    return player

@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: str = Path(..., description="The ID of the player"),
    authenticated_player_id: str = Depends(get_current_player)
):
    """Get player information"""
    # Security check: ensure players can only access their own info
    if player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own player information"
        )
    
    return player_service.get_player(player_id)

@router.get("/players/{player_id}/statistics", response_model=PlayerStatistics)
async def get_player_statistics(
    player_id: str = Path(..., description="The ID of the player"),
    timeframe: Optional[str] = Query(None, description="Optional timeframe filter"),
    metric_type: Optional[str] = Query(None, description="Optional metric type filter"),
    authenticated_player_id: str = Depends(get_current_player)
):
    """Get detailed player statistics"""
    # Security check: ensure players can only access their own info
    if player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own statistics"
        )
    
    return player_service.get_player_statistics(
        player_id=player_id,
        timeframe=timeframe,
        metric_type=metric_type
    )