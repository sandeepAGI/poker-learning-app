"""
Poker Learning App - Enhanced FastAPI with WebSockets
Phase 2: Minimal API layer with REST endpoints
Phase 3: WebSocket support for real-time AI turn visibility
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple
import uuid
import time
import asyncio
import json

from game.poker_engine import PokerGame, GameState
from websocket_manager import manager, thread_safe_manager, process_ai_turns_with_events, serialize_game_state

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
    winner_info: Optional[dict] = None  # Winner information at showdown
    small_blind: int  # Issue #1 fix: Expose blind levels
    big_blind: int
    hand_count: int  # Current hand number


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
    # Bug Fix #9: Use process_ai=False so hand doesn't complete before WebSocket connects
    # WebSocket handler will process AI turns when client connects
    game.start_new_hand(process_ai=False)

    # Store in memory with timestamp
    games[game_id] = (game, time.time())

    return {"game_id": game_id}


@app.get("/games/{game_id}", response_model=GameResponse)
def get_game_state(game_id: str, show_ai_thinking: bool = False):
    """
    Get current game state

    Args:
        game_id: Game identifier
        show_ai_thinking: If True, include AI reasoning (default: False for cleaner UX)

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

    # Convert last_ai_decisions to serializable format (UX Phase 1: hide by default)
    ai_decisions_data = {}
    if show_ai_thinking:
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount,
                "reasoning": decision.reasoning,
                "beginner_reasoning": decision.reasoning,  # TODO: Add beginner-friendly version
                "hand_strength": decision.hand_strength,
                "pot_odds": decision.pot_odds,
                "confidence": decision.confidence,
                "spr": decision.spr
            }
    else:
        # Only show action, not reasoning (cleaner UX by default)
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount
            }

    # Find winner information if at showdown
    winner_info = None
    if game.current_state == GameState.SHOWDOWN:
        # Look for pot_award event in current hand events
        for event in reversed(game.current_hand_events):
            if event.event_type == "pot_award":
                winner = next((p for p in game.players if p.player_id == event.player_id), None)
                if winner:
                    winner_info = {
                        "player_id": winner.player_id,
                        "name": winner.name,
                        "amount": event.amount,
                        "is_human": winner.is_human,
                        "personality": winner.personality if not winner.is_human else None
                    }
                break

    return GameResponse(
        game_id=game_id,
        state=game.current_state.value,
        pot=game.pot,
        current_bet=game.current_bet,
        players=players_data,
        community_cards=game.community_cards,
        current_player_index=game.current_player_index,
        human_player=human_data,
        last_ai_decisions=ai_decisions_data,
        winner_info=winner_info,
        small_blind=game.small_blind,
        big_blind=game.big_blind,
        hand_count=game.hand_count
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


@app.get("/games/{game_id}/analysis")
def get_hand_analysis(game_id: str):
    """
    Get rule-based analysis of the last completed hand.
    UX Phase 2 - Learning feature.

    Returns insights, tips, and AI reasoning for the last hand.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())  # Update access time

    analysis = game.analyze_last_hand()

    if not analysis:
        raise HTTPException(status_code=404, detail="No completed hands to analyze yet")

    return analysis


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for real-time game updates.
    Phase 3: Enables smooth AI turn-by-turn visibility.

    Flow:
    1. Client connects
    2. Client sends action: {"action": "fold/call/raise", "amount": 100}
    3. Server processes human action
    4. Server processes AI turns ONE AT A TIME, emitting events for each
    5. Client receives events and animates each action
    """
    # Validate game exists
    if game_id not in games:
        await websocket.close(code=1008, reason="Game not found")
        return

    # Connect to WebSocket manager
    await manager.connect(game_id, websocket)

    try:
        # Send initial game state
        game, _ = games[game_id]
        await manager.broadcast_state(game_id, game, show_ai_thinking=False)

        # Process AI turns if AI player acts first (e.g., heads-up where AI is SB/dealer)
        # Note: Initial connection always starts without step mode - user can enable it later
        current = game.get_current_player()
        if current and not current.is_human:
            asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking=False, step_mode=False))

        print(f"[WebSocket] Client connected to game {game_id}, awaiting actions...")

        # Listen for client messages
        while True:
            # Receive action from client
            data = await websocket.receive_json()
            print(f"[WebSocket] Received: {data}")

            # Update game access time
            games[game_id] = (game, time.time())

            # Handle different message types
            message_type = data.get("type", "action")

            if message_type == "action":
                # Human player action
                action = data.get("action")
                amount = data.get("amount")
                show_ai_thinking = data.get("show_ai_thinking", False)
                step_mode = data.get("step_mode", False)  # Phase 4: Step Mode (UAT-1 fix)

                # Validate action
                if action not in ["fold", "call", "raise"]:
                    await manager.send_event(game_id, {
                        "type": "error",
                        "data": {"message": "Invalid action"}
                    })
                    continue

                # Phase 8: Thread-safe action processing
                # Wrap action in lock to prevent race conditions
                async def execute_human_action():
                    # Submit human action (process_ai=False: let WebSocket handle AI turns)
                    success = game.submit_human_action(action, amount, process_ai=False)

                    if not success:
                        await manager.send_event(game_id, {
                            "type": "error",
                            "data": {"message": "Invalid action or not your turn"}
                        })
                        return False

                    # Broadcast state after human action
                    await manager.broadcast_state(game_id, game, show_ai_thinking)

                    # Process AI turns in background task (so we can continue receiving messages)
                    asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking, step_mode))
                    return True

                # Execute action with lock (only one action per game at a time)
                success = await thread_safe_manager.execute_action(game_id, execute_human_action)

                if not success:
                    continue

            elif message_type == "next_hand":
                # Start next hand
                if game.current_state != GameState.SHOWDOWN:
                    await manager.send_event(game_id, {
                        "type": "error",
                        "data": {"message": "Current hand not finished"}
                    })
                    continue

                # Check if game is over
                active_players = [p for p in game.players if p.stack > 0]
                if len(active_players) <= 1:
                    await manager.send_event(game_id, {
                        "type": "game_over",
                        "data": {"message": "Game over"}
                    })
                    continue

                # Start new hand (process_ai=False: let WebSocket handle AI turns async)
                game.start_new_hand(process_ai=False)
                show_ai_thinking = data.get("show_ai_thinking", False)
                step_mode = data.get("step_mode", False)  # Phase 4: Step Mode
                await manager.broadcast_state(game_id, game, show_ai_thinking)

                # Process AI turns if game starts with AI (background task)
                current = game.get_current_player()
                if current and not current.is_human:
                    asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking, step_mode))

            elif message_type == "continue":
                # Phase 4: User clicked "Continue" button in step mode
                print(f"[WebSocket] Received continue message for game {game_id}")
                manager.signal_continue(game_id)
                print(f"[WebSocket] Continue signal sent to manager")

            elif message_type == "get_state":
                # Client requesting current state
                show_ai_thinking = data.get("show_ai_thinking", False)
                await manager.broadcast_state(game_id, game, show_ai_thinking)

            else:
                await manager.send_event(game_id, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"}
                })

    except WebSocketDisconnect:
        # Phase 8: Pass specific websocket to disconnect
        manager.disconnect(game_id, websocket)
        print(f"[WebSocket] Client disconnected from game {game_id}")
    except Exception as e:
        print(f"[WebSocket] Error in game {game_id}: {e}")
        # Phase 8: Pass specific websocket to disconnect
        manager.disconnect(game_id, websocket)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


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
