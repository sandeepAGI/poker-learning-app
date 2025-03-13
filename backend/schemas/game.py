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
    hole_cards_formatted: Optional[Any] = None  # Can be a string or a list of dictionaries
    visible_to_client: Optional[bool] = False  # Indicates if these cards should be visible on the frontend

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
    pot: Optional[int] = 0
    current_bet: Optional[int] = 0
    current_state: Optional[str] = None

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

# NEW SCHEMA CLASSES

# Response model for getting a player's cards
class PlayerCardsResponse(BaseModel):
    hole_cards: Optional[List[str]] = None
    is_active: bool
    player_id: str
    visible_to_client: Optional[bool] = False  # Indicates if cards should be visible to the client

# Information about a winner in a showdown
class WinnerInfo(BaseModel):
    player_id: str
    amount: int
    hand_rank: str
    hand_name: Optional[str] = None  # Added for compatibility with new_e2e_test.py
    hand: List[str]

# Information about a player's hand in showdown
class PlayerHandInfo(BaseModel):
    hole_cards: List[str]
    hand_rank: str
    hand_score: int
    best_hand: List[str]

# Response model for showdown results
class ShowdownResponse(BaseModel):
    player_hands: Dict[str, PlayerHandInfo]
    winners: List[WinnerInfo]
    community_cards: List[str]
    total_pot: int