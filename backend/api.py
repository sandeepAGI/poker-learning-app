# backend/api.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from typing import Dict, List, Optional, Any
import uvicorn
import os

# Import routers
from routers import games, players, learning, debug

# Import error handlers
from utils.errors import (
    PokerAppError, 
    poker_app_exception_handler, 
    validation_exception_handler,
    generic_exception_handler
)

# Import services
from services.game_service import GameService

# Import logger
from utils.logger import (
    get_logger, 
    set_correlation_id, 
    set_request_context, 
    clear_context,
    get_correlation_id
)

# Setup logger
logger = get_logger("api")

# Create FastAPI app instance
app = FastAPI(
    title="Poker Learning App API",
    description="API for the Poker Learning App",
    version="1.0.0",
    docs_url="/api/docs",  # Custom docs URL
    redoc_url="/api/redoc",  # Custom redoc URL
)

# Configure CORS
origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
logger.info(f"Configuring CORS with origins: {origins}")

# Create rate limiting middleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute=60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.reset_interval = 60  # 1 minute in seconds
        self.clients = defaultdict(lambda: {"calls": 0, "reset_time": time.time() + self.reset_interval})
        self.logger = get_logger("rate_limiter")
    
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/"):
            # Get client identifier (IP or JWT subject if authenticated)
            client_id = request.client.host
            
            # Reset counter if needed
            if time.time() > self.clients[client_id]["reset_time"]:
                self.clients[client_id] = {
                    "calls": 0, 
                    "reset_time": time.time() + self.reset_interval
                }
            
            # Check rate limit
            self.clients[client_id]["calls"] += 1
            if self.clients[client_id]["calls"] > self.calls_per_minute:
                self.logger.warning(f"Rate limit exceeded for client {client_id}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": True,
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "details": {"retry_after": int(self.clients[client_id]["reset_time"] - time.time())}
                    }
                )
        
        # Process the request
        return await call_next(request)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
rate_limit = int(os.environ.get("RATE_LIMIT", "60"))  # 60 requests per minute by default
app.add_middleware(RateLimitMiddleware, calls_per_minute=rate_limit)
logger.info(f"Added rate limiting middleware: {rate_limit} requests per minute")

# Correlation ID and Request Context Middleware
class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Generate or use existing correlation ID
        corr_id = request.headers.get("X-Correlation-ID")
        if not corr_id:
            corr_id = set_correlation_id()
        else:
            set_correlation_id(corr_id)
        
        # Set request context
        context = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        set_request_context(context)
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = corr_id
            
            # Log request completion
            logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
            
            return response
        except Exception as e:
            # Log error with context
            logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}", exc_info=True)
            raise
        finally:
            # Clear context
            clear_context()

# Add correlation middleware
app.add_middleware(CorrelationMiddleware)
logger.info("Added correlation ID middleware")

# Add HTTPS redirect in production
if os.environ.get("ENVIRONMENT") == "production":
    logger.info("Adding HTTPS redirect middleware for production")
    app.add_middleware(HTTPSRedirectMiddleware)

# Add exception handlers
app.add_exception_handler(PokerAppError, poker_app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Import websocket
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime

# Include routers
app.include_router(games.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")
app.include_router(debug.router)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.logger = get_logger("websocket")
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        
        self.active_connections[game_id][player_id] = websocket
        self.logger.info(f"WebSocket connection established for player {player_id} in game {game_id}")
    
    def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections and player_id in self.active_connections[game_id]:
            del self.active_connections[game_id][player_id]
            self.logger.info(f"WebSocket connection removed for player {player_id} in game {game_id}")
            
            # Clean up empty games
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
    
    async def send_personal_message(self, message: str, game_id: str, player_id: str):
        if game_id in self.active_connections and player_id in self.active_connections[game_id]:
            await self.active_connections[game_id][player_id].send_text(message)
    
    async def broadcast(self, message: str, game_id: str, exclude_player: str = None):
        if game_id in self.active_connections:
            for player_id, connection in self.active_connections[game_id].items():
                if exclude_player is None or player_id != exclude_player:
                    await connection.send_text(message)

# Create connection manager instance
manager = ConnectionManager()

# WebSocket endpoint for game updates
@app.websocket("/api/ws/games/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    # Get player_id from query parameters
    player_id = websocket.query_params.get("player_id")
    
    if not player_id:
        logger.error("WebSocket connection rejected: No player_id provided")
        await websocket.close(code=1008)  # Policy violation
        return
        
    # Validate player access to this game (in a real implementation, use JWT validation)
    game_service = GameService()
    try:
        # Try to get game state to validate player's access
        game_service.get_game_state(game_id, player_id)
        
        # Accept connection if validation passes
        await manager.connect(websocket, game_id, player_id)
        
        # Notify other players
        await manager.broadcast(
            json.dumps({
                "event_type": "player_connected",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "player_id": player_id
                }
            }),
            game_id,
            exclude_player=player_id
        )
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Here you would process any client-sent messages
                # Most game actions will be through REST endpoints, but you can
                # handle client-specific events here
                
                # Echo back for demonstration
                await manager.send_personal_message(
                    json.dumps({
                        "event_type": "echo",
                        "timestamp": datetime.now().isoformat(),
                        "data": message
                    }),
                    game_id,
                    player_id
                )
                
        except WebSocketDisconnect:
            manager.disconnect(game_id, player_id)
            await manager.broadcast(
                json.dumps({
                    "event_type": "player_disconnected",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "player_id": player_id
                    }
                }),
                game_id
            )
    except Exception as e:
        # Log error and reject connection
        logger.error(f"WebSocket connection rejected: {str(e)}")
        await websocket.close(code=1008)  # Policy violation

# Custom OpenAPI docs have been removed
# Using built-in FastAPI docs at /api/docs and /api/redoc instead

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Poker Learning App API"}

# Import WebSocketManagerSingleton
from services.game_service import WebSocketManagerSingleton

# Lifespan events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting the Poker Learning App API")
    
    # Initialize WebSocket manager singleton
    WebSocketManagerSingleton.set_instance(manager)
    logger.info("Initialized WebSocket manager")
    
    # Schedule cleanup of inactive games
    game_service = GameService()
    game_service.schedule_cleanup()
    logger.info("Scheduled inactive game cleanup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the Poker Learning App API")

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)