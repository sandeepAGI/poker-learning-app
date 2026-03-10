"""
Poker Learning App - Enhanced FastAPI with WebSockets
Phase 2: Minimal API layer with REST endpoints
Phase 3: WebSocket support for real-time AI turn visibility
Phase 4: LLM-powered hand analysis with Claude AI
"""
# Load environment variables from .env file (Phase 4: for ANTHROPIC_API_KEY)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import logging
import os

from game.poker_engine import GameState
from websocket_manager import manager, thread_safe_manager, process_ai_turns_with_events, serialize_game_state
from auth import verify_token_string
from database import save_completed_hand

import app_state
from routes.auth import router as auth_router
from routes.game import router as game_router
from routes.analysis import router as analysis_router

# Phase 4: LLM Analysis imports
try:
    from llm_analyzer import LLMHandAnalyzer
    app_state.llm_analyzer = LLMHandAnalyzer()
    app_state.LLM_ENABLED = True
except Exception as e:
    _logger = logging.getLogger(__name__)
    _logger.warning(f"LLM analysis disabled: {e}")

# FastAPI app
app = FastAPI(title="Poker Learning App API", version="2.0")

# CORS middleware - allow both local development and Azure production
# Environment variable FRONTEND_URLS can override (comma-separated list)
allowed_origins = os.getenv(
    "FRONTEND_URLS",
    "http://localhost:3000,http://127.0.0.1:3000,https://poker-learning-app.azurewebsites.net"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test mode flag - ONLY enable in test environments
TEST_MODE = os.getenv("TEST_MODE") == "1"

# Setup logging
logger = logging.getLogger(__name__)

if TEST_MODE:
    logger.warning("⚠️  TEST_MODE is ENABLED - Test endpoints are active")
    logger.warning("⚠️  NEVER deploy to production with TEST_MODE=1")

# Include routers
app.include_router(auth_router)
app.include_router(game_router)
app.include_router(analysis_router)


# Health check endpoint for monitoring and deployment verification
@app.get("/health")
async def health_check():
    """Health check endpoint for Azure App Service and monitoring"""
    return {
        "status": "healthy",
        "version": "2.0",
        "environment": "production" if not TEST_MODE else "test",
        "llm_enabled": app_state.LLM_ENABLED
    }


# Periodic cleanup task
@app.on_event("startup")
async def startup_event():
    """Start periodic cleanup of old games."""
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(app_state.GAME_CLEANUP_INTERVAL_SECONDS)
            removed = app_state.cleanup_old_games()
            if removed > 0:
                print(f"[Cleanup] Removed {removed} idle game(s)")

    asyncio.create_task(periodic_cleanup())
    print(f"[Startup] Periodic game cleanup enabled (every {app_state.GAME_CLEANUP_INTERVAL_SECONDS}s, max idle {app_state.GAME_MAX_IDLE_SECONDS}s)")


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time game updates (requires authentication).
    Phase 3: Enables smooth AI turn-by-turn visibility.

    Args:
        websocket: WebSocket connection
        game_id: Game ID
        token: JWT token as query parameter (?token=xxx)

    Flow:
    1. Client connects with auth token
    2. Client sends action: {"action": "fold/call/raise", "amount": 100}
    3. Server processes human action
    4. Server processes AI turns ONE AT A TIME, emitting events for each
    5. Client receives events and animates each action
    """
    from fastapi import HTTPException

    games = app_state.games

    # Validate token
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        user_id = verify_token_string(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Validate game exists
    if game_id not in games:
        await websocket.close(code=1008, reason="Game not found")
        return

    # Validate game ownership
    game, _ = games[game_id]
    if not hasattr(game, 'user_id') or game.user_id != user_id:
        await websocket.close(code=1008, reason="Unauthorized")
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
            task = asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking=False, step_mode=False))
            app_state.game_tasks[game_id] = task

        print(f"[WebSocket] Client connected to game {game_id}, awaiting actions...")

        # Listen for client messages
        while True:
            # Receive action from client
            data = await websocket.receive_json()
            print(f"[WebSocket] Received: {data}")

            # Update game access time (guard against re-inserting deleted games)
            if game_id not in app_state.deleted_games:
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
                    task = asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking, step_mode))
                    app_state.game_tasks[game_id] = task
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

                # Save previous hand before starting new one
                if game.last_hand_summary and hasattr(game, 'user_id'):
                    save_completed_hand(game_id, game.last_hand_summary, game.user_id)

                # Start new hand (process_ai=False: let WebSocket handle AI turns async)
                game.start_new_hand(process_ai=False)
                show_ai_thinking = data.get("show_ai_thinking", False)
                step_mode = data.get("step_mode", False)  # Phase 4: Step Mode
                await manager.broadcast_state(game_id, game, show_ai_thinking)

                # Process AI turns if game starts with AI (background task)
                current = game.get_current_player()
                if current and not current.is_human:
                    task = asyncio.create_task(process_ai_turns_with_events(game, game_id, show_ai_thinking, step_mode))
                    app_state.game_tasks[game_id] = task

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


# ============================================================================
# TEST ENDPOINTS (Only available when TEST_MODE=1)
# ============================================================================

if TEST_MODE:
    @app.post("/test/set_game_state")
    async def set_game_state_for_testing(request: dict):
        """
        Manipulate game state for E2E testing.

        WARNING: Only available when TEST_MODE=1 env var set.
        NEVER deploy to production with TEST_MODE enabled.
        """
        from fastapi import HTTPException

        games = app_state.games
        game_id = request.get("game_id")

        if not game_id:
            raise HTTPException(status_code=400, detail="game_id required")

        if game_id not in games:
            raise HTTPException(status_code=404, detail="Game not found")

        game, _ = games[game_id]

        # Apply state modifications with validation
        if "player_stacks" in request:
            for player_name, stack in request["player_stacks"].items():
                # Validate stack is non-negative
                if stack < 0:
                    raise HTTPException(status_code=400, detail=f"Invalid stack: {stack}")

                # Find player by name (case-insensitive)
                player = next(
                    (p for p in game.players if p.name.lower() == player_name.lower()),
                    None
                )
                if player:
                    player.stack = stack
                    logger.info(f"[TEST] Set {player.name} stack to ${stack}")
                else:
                    logger.warning(f"[TEST] Player not found: {player_name}")

        if "dealer_position" in request:
            game.dealer_index = request["dealer_position"]
            logger.info(f"[TEST] Set dealer position to {game.dealer_index}")

        if "current_bet" in request:
            game.current_bet = request["current_bet"]
            logger.info(f"[TEST] Set current bet to ${game.current_bet}")

        if "pot" in request:
            game.pot = request["pot"]
            logger.info(f"[TEST] Set pot to ${game.pot}")

        if "state" in request:
            game.current_state = GameState(request["state"])
            logger.info(f"[TEST] Set game state to {game.current_state}")

        if "community_cards" in request:
            import re
            cards = request["community_cards"]

            # Validate card format (e.g., "Ah", "Kd", "2c")
            for card in cards:
                if not re.match(r'^[2-9TJQKA][hdsc]$', card):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid card format: {card}. Expected format: rank[2-9TJQKA] + suit[hdsc]"
                    )

            game.community_cards = cards
            logger.info(f"[TEST] Set community cards to {game.community_cards}")

        if "current_player_index" in request:
            game.current_player_index = request["current_player_index"]
            logger.info(f"[TEST] Set current player index to {game.current_player_index}")

        # Recalculate total chips for conservation check
        game.total_chips = sum(p.stack for p in game.players) + game.pot

        # Disable chip conservation for test scenarios
        game.qc_enabled = False

        # Update access time (guard against re-inserting deleted games)
        if game_id not in app_state.deleted_games:
            games[game_id] = (game, time.time())

        # Serialize and return new state
        state = serialize_game_state(game, show_ai_thinking=False)

        # Broadcast state update to all connected WebSocket clients
        await manager.broadcast_state(game_id, game)

        return {
            "success": True,
            "game_id": game_id,
            "game_state": state
        }

    @app.get("/test/health")
    async def test_health():
        """Health check for E2E tests"""
        return {
            "status": "ok",
            "test_mode": True,
            "message": "Test endpoints are active"
        }

    @app.get("/test/games/{game_id}")
    async def test_get_game_state(game_id: str):
        """Get full game state (for debugging E2E tests)"""
        from fastapi import HTTPException

        games = app_state.games
        if game_id not in games:
            raise HTTPException(status_code=404, detail="Game not found")

        game, _ = games[game_id]
        games[game_id] = (game, time.time())

        state = serialize_game_state(game, show_ai_thinking=True)

        return {
            "game_id": game_id,
            "game_state": state
        }


# Health check endpoint
@app.get("/")
def root_health_check():
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
