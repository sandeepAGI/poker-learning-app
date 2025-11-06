"""
Poker Learning App - Simple FastAPI wrapper
Phase 2: Minimal API layer with 4 core endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple
import uuid
import time
import asyncio

from game.poker_engine import PokerGame, GameState

# FastAPI app
app = FastAPI(title="Poker Learning App API", version="2.0")

# CORS middleware for Next.js development (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory game storage with TTL (Time To Live)
# Format: {game_id: (PokerGame, last_access_timestamp)}
games: Dict[str, Tuple[PokerGame, float]] = {}

# Memory management constants
GAME_MAX_IDLE_SECONDS = 3600  # Remove games idle > 1 hour
GAME_CLEANUP_INTERVAL_SECONDS = 300  # Clean up every 5 minutes


def cleanup_old_games(max_age_seconds: int = GAME_MAX_IDLE_SECONDS) -> int:
    """Remove games inactive for > max_age_seconds. Returns number removed."""
    current_time = time.time()
    to_remove = [
        game_id for game_id, (game, last_access) in games.items()
        if current_time - last_access > max_age_seconds
    ]
    for game_id in to_remove:
        del games[game_id]
    return len(to_remove)


# Periodic cleanup task
@app.on_event("startup")
async def startup_event():
    """Start periodic cleanup of old games."""
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(GAME_CLEANUP_INTERVAL_SECONDS)
            removed = cleanup_old_games()
            if removed > 0:
                print(f"[Cleanup] Removed {removed} idle game(s)")

    asyncio.create_task(periodic_cleanup())
    print(f"[Startup] Periodic game cleanup enabled (every {GAME_CLEANUP_INTERVAL_SECONDS}s, max idle {GAME_MAX_IDLE_SECONDS}s)")


# Request/Response Models
class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player_name: str = "Player"
    ai_count: int = 3  # Number of AI opponents (1-3)


class GameActionRequest(BaseModel):
    """Request to submit a player action"""
    action: str  # "fold", "call", "raise"
    amount: Optional[int] = None  # Required for raise


class GameResponse(BaseModel):
    """Game state response"""
    game_id: str
    state: str
    pot: int
    current_bet: int
    players: list
    community_cards: list
    current_player_index: Optional[int]  # None when all players all-in or folded
    human_player: dict
    last_ai_decisions: dict


# API Endpoints

@app.post("/games", response_model=Dict[str, str])
def create_game(request: CreateGameRequest):
    """
    Create a new poker game
    Returns: {"game_id": "uuid"}
    """
    # Validate AI count
    if request.ai_count < 1 or request.ai_count > 3:
        raise HTTPException(status_code=400, detail="AI count must be between 1 and 3")

    # Create game
    game_id = str(uuid.uuid4())
    game = PokerGame(request.player_name, request.ai_count)

    # Start first hand
    game.start_new_hand()

    # Store in memory with timestamp
    games[game_id] = (game, time.time())

    return {"game_id": game_id}


@app.get("/games/{game_id}", response_model=GameResponse)
def get_game_state(game_id: str):
    """
    Get current game state
    Returns: Complete game state including players, cards, pot, etc.
    """
    # Validate game exists
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get game and update last access time
    game, _ = games[game_id]
    games[game_id] = (game, time.time())

    # Find human player
    human_player = next((p for p in game.players if p.is_human), None)
    if not human_player:
        raise HTTPException(status_code=500, detail="No human player found")

    # Build player list (hide other players' cards)
    players_data = []
    for player in game.players:
        player_data = {
            "player_id": player.player_id,
            "name": player.name,
            "stack": player.stack,
            "current_bet": player.current_bet,
            "is_active": player.is_active,
            "all_in": player.all_in,
            "is_human": player.is_human,
            "personality": player.personality if not player.is_human else None,
            # Only show hole cards for human player or if showdown
            "hole_cards": player.hole_cards if (player.is_human or game.current_state == GameState.SHOWDOWN) else []
        }
        players_data.append(player_data)

    # Build human player data
    human_data = {
        "player_id": human_player.player_id,
        "name": human_player.name,
        "stack": human_player.stack,
        "current_bet": human_player.current_bet,
        "hole_cards": human_player.hole_cards,
        "is_active": human_player.is_active,
        "is_current_turn": game.get_current_player() == human_player if game.get_current_player() else False
    }

    # Convert last_ai_decisions to serializable format
    ai_decisions_data = {}
    for player_id, decision in game.last_ai_decisions.items():
        ai_decisions_data[player_id] = {
            "action": decision.action,
            "amount": decision.amount,
            "reasoning": decision.reasoning,
            "beginner_reasoning": decision.reasoning,  # TODO: Add in Phase 3
            "hand_strength": decision.hand_strength,
            "pot_odds": decision.pot_odds,
            "confidence": decision.confidence,
            "spr": decision.spr
        }

    return GameResponse(
        game_id=game_id,
        state=game.current_state.value,
        pot=game.pot,
        current_bet=game.current_bet,
        players=players_data,
        community_cards=game.community_cards,
        current_player_index=game.current_player_index,
        human_player=human_data,
        last_ai_decisions=ai_decisions_data
    )


@app.post("/games/{game_id}/actions")
def submit_action(game_id: str, request: GameActionRequest):
    """
    Submit a player action (fold/call/raise)
    Returns: Updated game state
    """
    # Validate game exists
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get game and update last access time
    game, _ = games[game_id]
    games[game_id] = (game, time.time())

    # Validate action
    if request.action not in ["fold", "call", "raise"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'fold', 'call', or 'raise'")

    # Validate raise has amount
    if request.action == "raise" and request.amount is None:
        raise HTTPException(status_code=400, detail="Raise action requires amount")

    # Submit action to game engine
    success = game.submit_human_action(request.action, request.amount)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid action. Check if it's your turn or the action is valid.")

    # Return updated game state
    return get_game_state(game_id)


@app.post("/games/{game_id}/next")
def next_hand(game_id: str):
    """
    Start next hand in the game
    Returns: Updated game state
    """
    # Validate game exists
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get game and update last access time
    game, _ = games[game_id]
    games[game_id] = (game, time.time())

    # Check if current hand is finished
    if game.current_state != GameState.SHOWDOWN:
        raise HTTPException(status_code=400, detail="Current hand not finished. Complete showdown first.")

    # Check if any players are eliminated
    active_players = [p for p in game.players if p.stack > 0]
    if len(active_players) <= 1:
        raise HTTPException(status_code=400, detail="Game over. Only one player remaining.")

    # Start new hand
    game.start_new_hand()

    # Return updated game state
    return get_game_state(game_id)


# Health check endpoint
@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Poker Learning App API",
        "version": "2.0",
        "phase": "Phase 2 - Simple API Layer"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
