# backend/schemas/learning.py
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Game context for feedback
class GameContext(BaseModel):
    game_state: str
    hole_cards: List[str]
    community_cards: List[str]
    pot_size: int
    spr: float

# Learning feedback item
class FeedbackItem(BaseModel):
    decision_id: str
    game_context: GameContext
    decision: str
    feedback_text: str
    optimal_decision: str
    improvement_areas: List[str]
    timestamp: datetime

# Learning feedback response
class FeedbackResponse(BaseModel):
    feedback: List[FeedbackItem]

# Strategy profile response
class StrategyProfile(BaseModel):
    dominant_strategy: str
    strategy_distribution: Dict[str, float]
    recommended_strategy: str
    decision_accuracy: float
    total_decisions: int
    improvement_areas: List[Dict[str, str]]
    learning_recommendations: List[Dict[str, str]]
    decision_trend: Dict[str, Any]

# Decision details response
class DecisionDetails(BaseModel):
    decision_id: str
    timestamp: datetime
    game_context: GameContext
    player_decision: str
    matching_strategy: str
    optimal_strategy: str
    was_optimal: bool
    strategy_decisions: Dict[str, str]
    expected_value: float
    detailed_analysis: str