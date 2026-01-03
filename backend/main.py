"""
Poker Learning App - Enhanced FastAPI with WebSockets
Phase 2: Minimal API layer with REST endpoints
Phase 3: WebSocket support for real-time AI turn visibility
Phase 4: LLM-powered hand analysis with Claude AI
"""
# Load environment variables from .env file (Phase 4: for ANTHROPIC_API_KEY)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import time
import asyncio
import json
import logging

from game.poker_engine import PokerGame, GameState
from websocket_manager import manager, thread_safe_manager, process_ai_turns_with_events, serialize_game_state

# Phase 4: LLM Analysis imports
try:
    from llm_analyzer import LLMHandAnalyzer
    llm_analyzer = LLMHandAnalyzer()
    LLM_ENABLED = True
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"LLM analysis disabled: {e}")
    llm_analyzer = None
    LLM_ENABLED = False

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

# Phase 4: LLM Analysis - Caching and Metrics
# Cache key format: "{game_id}_hand_{hand_number}_{depth}"
analysis_cache: Dict[str, Dict] = {}

# Metrics for cost tracking
@dataclass
class AnalysisMetrics:
    timestamp: str
    game_id: str
    model_used: str
    cost: float
    analysis_count: int
    success: bool

analysis_metrics: List[AnalysisMetrics] = []

# Rate limiting: track last analysis time per game
last_analysis_time: Dict[str, float] = {}


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


# API Endpoints

@app.post("/games", response_model=Dict[str, str])
def create_game(request: CreateGameRequest):
    """
    Create a new poker game
    Returns: {"game_id": "uuid"}
    """
    # Phase 1: Validate AI count (updated to support 6-player tables)
    if request.ai_count < 1 or request.ai_count > 5:
        raise HTTPException(status_code=400, detail="AI count must be between 1 and 5")

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
                "spr": decision.spr,
                "decision_id": decision.decision_id  # Issue #5: Add for deduplication
            }
    else:
        # Only show action, not reasoning (cleaner UX by default)
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount,
                "decision_id": decision.decision_id  # Issue #5: Critical for deduplication after refresh
            }

    # Find ALL winners (handles showdown, fold wins, split pots, and side pots)
    # FIX-09: Enhanced winner info with poker-accurate hand reveals
    winner_info = None

    # Check if there are any pot_award events (showdown or fold wins)
    has_pot_award = any(event.event_type == "pot_award" for event in game.current_hand_events)

    if has_pot_award:
        # Determine if this is a showdown or fold win
        # Showdown happened if there are showdown_hands recorded (not just based on game state)
        is_showdown = (game.last_hand_summary is not None and
                      len(game.last_hand_summary.showdown_hands) > 0)

        # Collect ALL pot_award events (not just the first one!)
        winners = []
        for event in game.current_hand_events:
            if event.event_type == "pot_award":
                winner = next((p for p in game.players if p.player_id == event.player_id), None)
                if winner:
                    # Get hand rank and hole cards from last_hand_summary (only at showdown)
                    hand_rank = None
                    hole_cards = []
                    if is_showdown and game.last_hand_summary:
                        hand_rank = game.last_hand_summary.hand_rankings.get(winner.player_id)
                        hole_cards = game.last_hand_summary.showdown_hands.get(winner.player_id, [])

                    winners.append({
                        "player_id": winner.player_id,
                        "name": winner.name,
                        "amount": event.amount,
                        "is_human": winner.is_human,
                        "personality": winner.personality if not winner.is_human else None,
                        "won_by_fold": not is_showdown,  # True if won by fold, False if showdown
                        "hand_rank": hand_rank,
                        "hole_cards": hole_cards
                    })

        # Build all_showdown_hands list (all players who revealed cards, ranked by hand strength)
        # Only populate for showdown scenarios
        all_showdown_hands = []
        folded_players = []

        if is_showdown and game.last_hand_summary:
            # Get showdown participants (players who revealed cards)
            from game.poker_engine import HandEvaluator
            evaluator = HandEvaluator()
            showdown_participants = []

            for player in game.players:
                if player.player_id in game.last_hand_summary.showdown_hands:
                    # This player went to showdown
                    hole_cards = game.last_hand_summary.showdown_hands[player.player_id]
                    hand_rank = game.last_hand_summary.hand_rankings.get(player.player_id, "Unknown")

                    # Calculate score for ranking
                    score = 9999  # Default high score
                    if hole_cards and game.community_cards:
                        score, _ = evaluator.evaluate_hand(hole_cards, game.community_cards)

                    # Find amount won (if any)
                    amount_won = 0
                    for w in winners:
                        if w["player_id"] == player.player_id:
                            amount_won = w["amount"]
                            break

                    showdown_participants.append({
                        "player_id": player.player_id,
                        "name": player.name,
                        "hand_rank": hand_rank,
                        "hole_cards": hole_cards,
                        "amount_won": amount_won,
                        "is_human": player.is_human,
                        "score": score  # For sorting (lower is better in Treys)
                    })
                else:
                    # This player folded - don't show cards
                    folded_players.append({
                        "player_id": player.player_id,
                        "name": player.name,
                        "is_human": player.is_human
                    })

            # Sort by hand strength (lower score = better hand)
            showdown_participants.sort(key=lambda x: x["score"])

            # Remove score from final output (internal use only)
            for participant in showdown_participants:
                del participant["score"]

            all_showdown_hands = showdown_participants

        # Return as list if multiple winners, single dict if only one
        # Add showdown data to the response
        if len(winners) > 1:
            winner_info = {
                "winners": winners,
                "all_showdown_hands": all_showdown_hands,
                "folded_players": folded_players
            }
        elif len(winners) == 1:
            winner_info = winners[0]
            winner_info["all_showdown_hands"] = all_showdown_hands
            winner_info["folded_players"] = folded_players

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
        hand_count=game.hand_count,
        dealer_position=game.dealer_index,  # FIX-01: Expose dealer position
        small_blind_position=game.small_blind_index,  # FIX-01: Expose SB position
        big_blind_position=game.big_blind_index,  # FIX-01: Expose BB position
        last_raise_amount=game.last_raise_amount  # Issue #2: Minimum raise tracking
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
def get_hand_analysis(game_id: str, hand_number: Optional[int] = None):
    """
    Get rule-based analysis of a completed hand.
    UX Phase 2 - Learning feature.

    Args:
        game_id: Game ID
        hand_number: Optional hand number to analyze (defaults to last hand)

    Returns insights, tips, and AI reasoning for the specified hand.
    Phase 3: Support for historical hand analysis via hand_number parameter.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())  # Update access time

    # Phase 3: Support analyzing specific hand by number
    if hand_number is not None:
        # Find hand in history
        target_hand = None
        for hand in game.hand_history:
            if hand.hand_number == hand_number:
                target_hand = hand
                break

        if not target_hand:
            raise HTTPException(status_code=404, detail=f"Hand #{hand_number} not found in history")

        # Temporarily set as last_hand_summary for analysis
        original_last_hand = game.last_hand_summary
        game.last_hand_summary = target_hand
        analysis = game.analyze_last_hand()
        game.last_hand_summary = original_last_hand

        if not analysis:
            raise HTTPException(status_code=500, detail="Failed to analyze hand")
        return analysis
    else:
        # Default: analyze most recent hand
        analysis = game.analyze_last_hand()
        if not analysis:
            raise HTTPException(status_code=404, detail="No completed hands to analyze yet")
        return analysis


@app.get("/games/{game_id}/analysis-llm")
async def get_llm_hand_analysis(
    game_id: str,
    hand_number: Optional[int] = None,
    use_cache: bool = True
):
    """
    Get LLM-powered hand analysis using Claude AI (Haiku 4.5 only).
    Phase 4: LLM-Powered Hand Analysis (Quick Analysis)

    Args:
        game_id: Game ID
        hand_number: Optional hand number to analyze (defaults to last hand)
        use_cache: Whether to use cached analysis (default: True)

    Returns:
        {
            "analysis": {...},  # Full LLM analysis JSON
            "model_used": "haiku-4.5",
            "cost": float,      # Cost of this analysis (~$0.016)
            "cached": bool,     # Whether result was cached
            "analysis_count": int  # Total analyses for this game
        }
    """
    # Check if LLM is enabled
    if not LLM_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="LLM analysis not available. Set ANTHROPIC_API_KEY environment variable."
        )

    # Check game exists
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())  # Update access time

    # Rate limiting: 1 analysis per 30 seconds per game
    now = time.time()
    last_time = last_analysis_time.get(game_id, 0)
    if use_cache and now - last_time < 30:
        wait_time = int(30 - (now - last_time))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: Wait {wait_time}s before next analysis"
        )

    # Get target hand
    if hand_number is not None and hasattr(game, 'hand_history'):
        target_hand = next(
            (h for h in game.hand_history if h.hand_number == hand_number),
            None
        )
    else:
        target_hand = game.last_hand_summary

    if not target_hand:
        raise HTTPException(status_code=404, detail="No hand to analyze")

    # Check cache (always use "quick" for single hands)
    cache_key = f"{game_id}_hand_{target_hand.hand_number}_quick"
    if use_cache and cache_key in analysis_cache:
        cached_result = analysis_cache[cache_key]
        return {
            **cached_result,
            "cached": True
        }

    # Get analysis count for context management
    analysis_count = getattr(game, 'analysis_count', 0)
    game.analysis_count = analysis_count + 1

    try:
        # Get hand history
        hand_history = game.hand_history if hasattr(game, 'hand_history') else []

        # Call LLM analyzer (always use "quick" for single hands)
        analysis = llm_analyzer.analyze_hand(
            completed_hand=target_hand,
            hand_history=hand_history,
            analysis_count=analysis_count,
            depth="quick",
            skill_level="beginner"  # TODO: Track player skill
        )

        # Calculate cost (for monitoring) - always Haiku for single hands
        model = "haiku-4.5"
        cost = 0.016

        # Build response
        result = {
            "analysis": analysis,
            "model_used": model,
            "cost": cost,
            "cached": False,
            "analysis_count": analysis_count + 1
        }

        # Cache result
        analysis_cache[cache_key] = result

        # Update last analysis time
        last_analysis_time[game_id] = now

        # Track metrics (for cost monitoring)
        _track_analysis_metrics(game_id, model, cost, analysis_count + 1, success=True)

        return result

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"LLM analysis failed for game {game_id}: {e}")

        # Track failed attempt
        _track_analysis_metrics(game_id, "error", 0.0, analysis_count + 1, success=False)

        # Fallback to rule-based analysis
        fallback = game.analyze_last_hand() if hasattr(game, 'analyze_last_hand') else {
            "error": "Analysis not available",
            "details": str(e)
        }

        return {
            "analysis": fallback,
            "model_used": "rule-based-fallback",
            "cost": 0.0,
            "cached": False,
            "error": str(e),
            "analysis_count": analysis_count + 1
        }


@app.get("/games/{game_id}/analysis-session")
async def get_session_analysis(
    game_id: str,
    depth: str = Query("quick", regex="^(quick|deep)$"),
    hand_count: Optional[int] = None,
    use_cache: bool = True
):
    """
    Get LLM-powered session analysis across multiple hands.
    Phase 4.5: Session Analysis

    Args:
        game_id: Game ID
        depth: "quick" (Haiku, $0.018) or "deep" (Sonnet, $0.032)
        hand_count: Number of recent hands to analyze (default: all hands)
        use_cache: Whether to use cached analysis (default: True)

    Returns:
        {
            "analysis": {...},  # Full session analysis JSON
            "model_used": str,  # "haiku-4.5" or "sonnet-4.5"
            "cost": float,      # Cost of this analysis
            "cached": bool,     # Whether result was cached
            "hands_analyzed": int  # Number of hands analyzed
        }
    """
    # Check if LLM is enabled
    if not LLM_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="LLM analysis not available. Set ANTHROPIC_API_KEY environment variable."
        )

    # Check game exists
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())  # Update access time

    # Get hand history
    hand_history = game.hand_history if hasattr(game, 'hand_history') else []

    if not hand_history:
        raise HTTPException(status_code=404, detail="No hands to analyze")

    # FIX Issue #4: Slice hand_history BEFORE calling analyzer
    # Determine how many hands to analyze
    hands_to_analyze = hand_count if hand_count else len(hand_history)
    # Slice to only the requested number of hands (last N hands)
    sliced_history = hand_history[-hands_to_analyze:] if hands_to_analyze < len(hand_history) else hand_history

    # Check cache
    cache_key = f"{game_id}_session_{hands_to_analyze}_{depth}"
    if use_cache and cache_key in analysis_cache:
        cached_result = analysis_cache[cache_key]
        return {
            **cached_result,
            "cached": True
        }

    # FIX Issue #4: Rate limiting should apply regardless of use_cache flag
    # Rate limiting: 1 session analysis per 60 seconds per game
    now = time.time()
    last_time = last_analysis_time.get(f"{game_id}_session", 0)
    if now - last_time < 60:
        wait_time = int(60 - (now - last_time))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: Wait {wait_time}s before next session analysis"
        )

    try:
        # Get starting stack (from first hand or default)
        starting_stack = 1000  # Default starting stack
        # Note: We use a default since CompletedHand doesn't track starting stack per hand
        # The human_final_stack only shows ending stack for that hand

        # Get current stack - use the same pattern as rest of codebase
        human_player = next(p for p in game.players if p.is_human)
        ending_stack = human_player.stack

        # Call LLM analyzer with SLICED history (not full history)
        analysis = llm_analyzer.analyze_session(
            hand_history=sliced_history,
            starting_stack=starting_stack,
            ending_stack=ending_stack,
            depth=depth,
            skill_level="beginner",  # TODO: Track player skill
            hand_count=hand_count
        )

        # Calculate cost (for monitoring)
        model = "sonnet-4.5" if depth == "deep" else "haiku-4.5"
        # Session analysis uses more tokens than single hand
        cost = 0.032 if depth == "deep" else 0.018

        # Build response
        result = {
            "analysis": analysis,
            "model_used": model,
            "cost": cost,
            "cached": False,
            "hands_analyzed": hands_to_analyze
        }

        # Cache result
        analysis_cache[cache_key] = result

        # Update last analysis time
        last_analysis_time[f"{game_id}_session"] = now

        # Track metrics (for cost monitoring)
        _track_analysis_metrics(game_id, f"{model}_session", cost, hands_to_analyze, success=True)

        return result

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Session analysis failed for game {game_id}: {e}")

        # Track failed attempt
        _track_analysis_metrics(game_id, "error_session", 0.0, hands_to_analyze, success=False)

        return {
            "analysis": {"error": "Session analysis not available", "details": str(e)},
            "model_used": "error",
            "cost": 0.0,
            "cached": False,
            "error": str(e),
            "hands_analyzed": hands_to_analyze
        }


def _track_analysis_metrics(game_id: str, model: str, cost: float, count: int, success: bool = True):
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


@app.get("/admin/analysis-metrics")
async def get_analysis_metrics():
    """
    Get LLM analysis cost and usage metrics.
    Phase 4: Cost Monitoring

    Returns statistics about LLM analysis usage and costs.
    """
    if not analysis_metrics:
        return {
            "total_analyses": 0,
            "total_cost": 0.0,
            "haiku_analyses": 0,
            "sonnet_analyses": 0,
            "avg_cost": 0.0,
            "cost_today": 0.0,
            "alert": False
        }

    total_cost = sum(m.cost for m in analysis_metrics)
    haiku_count = sum(1 for m in analysis_metrics if "haiku" in m.model_used)
    sonnet_count = sum(1 for m in analysis_metrics if "sonnet" in m.model_used)
    error_count = sum(1 for m in analysis_metrics if not m.success)

    # Calculate daily cost
    today = datetime.utcnow().date()
    daily_metrics = [
        m for m in analysis_metrics
        if datetime.fromisoformat(m.timestamp).date() == today
    ]
    cost_today = sum(m.cost for m in daily_metrics)

    return {
        "total_analyses": len(analysis_metrics),
        "successful_analyses": len(analysis_metrics) - error_count,
        "failed_analyses": error_count,
        "total_cost": round(total_cost, 2),
        "haiku_analyses": haiku_count,
        "sonnet_analyses": sonnet_count,
        "avg_cost": round(total_cost / len(analysis_metrics), 4) if analysis_metrics else 0,
        "cost_today": round(cost_today, 2),
        "analyses_today": len(daily_metrics),
        "alert": cost_today > 100.0  # Alert if >$100 spent today
    }


@app.get("/games/{game_id}/history")
def get_hand_history(game_id: str, limit: Optional[int] = 10):
    """
    Get hand history for a game session.
    Phase 3: Hand History Infrastructure.

    Args:
        game_id: Game ID
        limit: Maximum number of hands to return (default 10, max 100)

    Returns:
        List of completed hands with detailed round-by-round actions.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game, _ = games[game_id]
    games[game_id] = (game, time.time())  # Update access time

    # Validate and cap limit
    if limit < 1:
        limit = 10
    elif limit > 100:
        limit = 100

    # Get most recent N hands
    hands = game.hand_history[-limit:] if len(game.hand_history) > limit else game.hand_history

    # Convert to JSON-serializable format
    from dataclasses import asdict
    hands_data = [asdict(hand) for hand in hands]

    return {
        "session_id": game.session_id,
        "total_hands": len(game.hand_history),
        "returned_hands": len(hands_data),
        "hands": hands_data
    }


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
