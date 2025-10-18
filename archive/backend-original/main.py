# Simple FastAPI Poker Server - 4 Essential Endpoints
import json
import uuid
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from poker_engine import PokerGame, GameState

# FastAPI app
app = FastAPI(title="Simple Poker API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory game storage (use Redis/DB in production)
games: Dict[str, PokerGame] = {}

# Request/Response models
class CreateGameRequest(BaseModel):
    player_name: str

class PlayerActionRequest(BaseModel):
    action: str  # "fold", "call", "raise"
    amount: Optional[int] = None

class GameResponse(BaseModel):
    game_id: str
    game_state: dict

# API Endpoints

@app.post("/api/create-game", response_model=GameResponse)
async def create_game(request: CreateGameRequest):
    """Create a new poker game."""
    game_id = str(uuid.uuid4())
    game = PokerGame(request.player_name)
    game.start_new_hand()
    
    games[game_id] = game
    
    return GameResponse(
        game_id=game_id,
        game_state=game.get_game_state()
    )

@app.get("/api/game-state/{game_id}", response_model=GameResponse)
async def get_game_state(game_id: str):
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    return GameResponse(
        game_id=game_id,
        game_state=game.get_game_state()
    )

@app.post("/api/player-action/{game_id}", response_model=GameResponse)
async def submit_action(game_id: str, request: PlayerActionRequest):
    """Submit player action."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Validate action
    if request.action not in ["fold", "call", "raise"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if request.action == "raise" and not request.amount:
        raise HTTPException(status_code=400, detail="Amount required for raise")
    
    # Process action
    success = game.submit_human_action(request.action, request.amount)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid action for current state")
    
    return GameResponse(
        game_id=game_id,
        game_state=game.get_game_state()
    )

@app.post("/api/next-hand/{game_id}", response_model=GameResponse)
async def next_hand(game_id: str):
    """Start next hand after showdown."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.current_state != GameState.SHOWDOWN:
        raise HTTPException(status_code=400, detail="Not in showdown state")
    
    game.start_new_hand()
    
    return GameResponse(
        game_id=game_id,
        game_state=game.get_game_state()
    )

@app.get("/api/showdown/{game_id}")
async def get_showdown_results(game_id: str):
    """Get showdown results."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    results = game.get_showdown_results()
    
    if not results:
        raise HTTPException(status_code=400, detail="Not in showdown state")
    
    return results

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "games_active": len(games)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)