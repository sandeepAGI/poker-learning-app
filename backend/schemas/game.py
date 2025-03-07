# backend/schemas/game.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Player in a game
class PlayerInfo(BaseModel):
    player_id: str
    player_type: str
    personality: Optional[str] = None
    position: int
    stack: int
    current_bet: Optional[int] = 0
    is_active: Optional[bool] = True
    is_all_in: Optional[bool] = False
    hole_cards: Optional[List[str]] = None

# Create game request
class GameCreate(BaseModel):
    player_id: str
    ai_count: int
    ai_personalities: List[str]

# Create game response
class GameCreateResponse(BaseModel):
    game_id: str
    players: List[PlayerInfo]
    dealer_position: int
    small_blind: int
    big_blind: int

# Game state response
class GameState(BaseModel):
    game_id: str
    current_state: str
    community_cards: List[str]
    pot: int
    current_bet: int
    players: List[PlayerInfo]
    dealer_position: int
    current_player: Optional[str] = None
    available_actions: List[str]
    min_raise: Optional[int] = None
    hand_number: int

# Player action request
class PlayerAction(BaseModel):
    player_id: str
    action_type: str
    amount: Optional[int] = None

# Player action response
class ActionResponse(BaseModel):
    action_result: str
    updated_game_state: GameState
    next_player: Optional[str] = None
    pot_update: int

# Next hand request
class NextHandRequest(BaseModel):
    player_id: str

# Next hand response
class NextHandResponse(BaseModel):
    hand_number: int
    updated_game_state: GameState

# End game response
class GameSummary(BaseModel):
    duration: int
    hands_played: int
    final_chips: Dict[str, int]
    winner: str