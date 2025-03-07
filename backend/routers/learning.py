# backend/routers/learning.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional

from schemas.learning import FeedbackResponse, StrategyProfile, DecisionDetails
from services.learning_service import LearningService

router = APIRouter(tags=["learning"])
learning_service = LearningService()

@router.get("/players/{player_id}/feedback", response_model=FeedbackResponse)
async def get_learning_feedback(
    player_id: str = Path(..., description="The ID of the player"),
    num_decisions: int = Query(1, description="Number of decisions to include in feedback")
):
    """Get learning feedback for a player"""
    return learning_service.get_learning_feedback(player_id, num_decisions)

@router.get("/players/{player_id}/strategy-profile", response_model=StrategyProfile)
async def get_strategy_profile(
    player_id: str = Path(..., description="The ID of the player")
):
    """Get player's strategic profile"""
    return learning_service.get_strategy_profile(player_id)

@router.get("/players/{player_id}/decisions/{decision_id}", response_model=DecisionDetails)
async def get_decision_details(
    player_id: str = Path(..., description="The ID of the player"),
    decision_id: str = Path(..., description="The ID of the decision")
):
    """Get detailed analysis of a specific decision"""
    return learning_service.get_decision_details(player_id, decision_id)