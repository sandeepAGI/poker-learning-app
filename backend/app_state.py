"""
Shared application state - accessed by routes and main.py.

Contains in-memory game storage, analysis caching, and LLM configuration.
"""
import asyncio
import time
import logging
from typing import Dict, Tuple, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel

from game.poker_engine import PokerGame

logger = logging.getLogger(__name__)

# In-memory game storage with TTL (Time To Live)
# Format: {game_id: (PokerGame, last_access_timestamp)}
games: Dict[str, Tuple[PokerGame, float]] = {}

# Track deleted game IDs to prevent re-insertion by background tasks
deleted_games: Set[str] = set()

# Track asyncio tasks per game for cancellation on game deletion
game_tasks: Dict[str, asyncio.Task] = {}

# Memory management constants
GAME_MAX_IDLE_SECONDS = 3600  # Remove games idle > 1 hour
GAME_CLEANUP_INTERVAL_SECONDS = 300  # Clean up every 5 minutes

# Phase 4: LLM Analysis - Caching and Metrics
# Cache key format: "{game_id}_hand_{hand_number}_{depth}"
analysis_cache: Dict[str, Dict] = {}

# Rate limiting: track last analysis time per game
last_analysis_time: Dict[str, float] = {}


@dataclass
class AnalysisMetrics:
    timestamp: str
    game_id: str
    model_used: str
    cost: float
    analysis_count: int
    success: bool


analysis_metrics: List[AnalysisMetrics] = []


# LLM Analyzer (initialized in main.py)
llm_analyzer = None
LLM_ENABLED = False


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


def track_analysis_metrics(game_id: str, model: str, cost: float, count: int, success: bool = True):
    """Track analysis metrics for cost monitoring."""
    metrics = AnalysisMetrics(
        timestamp=datetime.utcnow().isoformat(),
        game_id=game_id,
        model_used=model,
        cost=cost,
        analysis_count=count,
        success=success
    )
    analysis_metrics.append(metrics)

    # Keep last 1000 metrics
    if len(analysis_metrics) > 1000:
        analysis_metrics[:] = analysis_metrics[-1000:]


# Request/Response Models (shared across routes)
class CreateGameRequest(BaseModel):
    """Request to create a new game"""
    player_name: str = "Player"
    ai_count: int = 3  # Number of AI opponents (1-5, default 3)


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
    winner_info: Optional[Any] = None  # Winner(s) - dict for single winner, list for multiple (split/side pots)
    small_blind: int  # Issue #1 fix: Expose blind levels
    big_blind: int
    hand_count: int  # Current hand number
    dealer_position: Optional[int] = None  # FIX-01: Which player index is dealer
    small_blind_position: Optional[int] = None  # FIX-01: Which player index is SB
    big_blind_position: Optional[int] = None  # FIX-01: Which player index is BB
    last_raise_amount: Optional[int] = None  # Issue #2: Minimum raise tracking


class RegisterRequest(BaseModel):
    """Register new user request."""
    username: str
    password: str


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class AuthResponse(BaseModel):
    """Authentication response."""
    token: str
    user_id: str
    username: str
