# backend/routers/games.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional

from schemas.game import (
    GameCreate, GameCreateResponse, GameState, PlayerAction, 
    ActionResponse, NextHandRequest, NextHandResponse, GameSummary
)
from services.game_service import GameService
from utils.auth import get_current_player

router = APIRouter(tags=["games"])
game_service = GameService()

@router.post("/games", response_model=GameCreateResponse)
async def create_game(
    game_data: GameCreate,
    player_id: str = Depends(get_current_player)
):
    """Create a new game session"""
    # Override player_id from token for security
    return game_service.create_game(
        player_id=player_id,
        ai_count=game_data.ai_count,
        ai_personalities=game_data.ai_personalities
    )

@router.get("/games/{game_id}", response_model=GameState)
async def get_game_state(
    game_id: str = Path(..., description="The ID of the game"),
    player_id: str = Depends(get_current_player)
):
    """Get current game state"""
    return game_service.get_game_state(game_id, player_id)

@router.post("/games/{game_id}/actions", response_model=ActionResponse)
async def player_action(
    action: PlayerAction,
    game_id: str = Path(..., description="The ID of the game"),
    authenticated_player_id: str = Depends(get_current_player)
):
    """Process player action (fold, call, raise)"""
    # Security check: ensure the player can only submit actions for themselves
    if action.player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="You can only submit actions for your own player"
        )
        
    return game_service.process_action(
        game_id=game_id,
        player_id=action.player_id,
        action_type=action.action_type,
        amount=action.amount
    )

@router.post("/games/{game_id}/next-hand", response_model=NextHandResponse)
async def next_hand(
    request: NextHandRequest,
    game_id: str = Path(..., description="The ID of the game"),
    authenticated_player_id: str = Depends(get_current_player)
):
    """Advance to the next hand"""
    # Security check: ensure the player can only submit for themselves
    if request.player_id != authenticated_player_id:
        raise HTTPException(
            status_code=403,
            detail="You can only advance the game for your own player"
        )
        
    return game_service.next_hand(game_id, request.player_id)

@router.delete("/games/{game_id}", response_model=GameSummary)
async def end_game(
    game_id: str = Path(..., description="The ID of the game"),
    player_id: str = Depends(get_current_player)
):
    """End a game session"""
    return game_service.end_game(game_id, player_id)