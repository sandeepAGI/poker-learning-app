"""Analysis routes - rule-based and LLM-powered hand/session analysis."""
import time
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from game.poker_engine import CompletedHand, GameState
from auth import verify_token
from models import Game, Hand
from database import get_db
from app_state import (
    games, analysis_cache, analysis_metrics, last_analysis_time,
    llm_analyzer, LLM_ENABLED, track_analysis_metrics,
)

router = APIRouter(tags=["analysis"])

logger = logging.getLogger(__name__)


@router.get("/games/{game_id}/analysis")
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


@router.get("/games/{game_id}/analysis-llm")
async def get_llm_hand_analysis(
    game_id: str,
    hand_number: Optional[int] = None,
    use_cache: bool = True,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get LLM-powered hand analysis using Claude AI (Haiku 4.5 only).
    Phase 4: LLM-Powered Hand Analysis (Quick Analysis)

    Supports both active games (in-memory) and completed games (from database).

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

    # Check if game is in active games (in-memory)
    game = None
    is_active_game = game_id in games

    if is_active_game:
        game, _ = games[game_id]
        games[game_id] = (game, time.time())  # Update access time
    else:
        # Query database for completed game
        game_record = db.query(Game).filter(
            Game.game_id == game_id,
            Game.user_id == user_id
        ).first()

        if not game_record:
            raise HTTPException(status_code=404, detail="Game not found")

    # Rate limiting: 1 analysis per 30 seconds per game
    now = time.time()
    last_time = last_analysis_time.get(game_id, 0)
    if use_cache and now - last_time < 30:
        wait_time = int(30 - (now - last_time))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: Wait {wait_time}s before next analysis"
        )

    # Get target hand and hand history
    if is_active_game:
        # Active game: use in-memory data
        if hand_number is not None and hasattr(game, 'hand_history'):
            target_hand = next(
                (h for h in game.hand_history if h.hand_number == hand_number),
                None
            )
        else:
            target_hand = game.last_hand_summary

        if not target_hand:
            raise HTTPException(status_code=404, detail="No hand to analyze")

        hand_history = game.hand_history if hasattr(game, 'hand_history') else []
        analysis_count = getattr(game, 'analysis_count', 0)
        game.analysis_count = analysis_count + 1
    else:
        # Completed game: reconstruct from database
        # Get the specific hand or latest hand
        if hand_number is not None:
            hand_record = db.query(Hand).filter(
                Hand.game_id == game_id,
                Hand.hand_number == hand_number
            ).first()
        else:
            # Get latest hand
            hand_record = db.query(Hand).filter(
                Hand.game_id == game_id
            ).order_by(Hand.hand_number.desc()).first()

        if not hand_record:
            raise HTTPException(status_code=404, detail="No hand to analyze")

        # Reconstruct CompletedHand from database JSONB
        hand_data = hand_record.hand_data
        target_hand = CompletedHand(**hand_data)

        # Get all hands for context (hand history)
        all_hands = db.query(Hand).filter(
            Hand.game_id == game_id
        ).order_by(Hand.hand_number).all()

        hand_history = [CompletedHand(**h.hand_data) for h in all_hands]
        analysis_count = 0  # No persistent analysis count for completed games

    # Check cache (always use "quick" for single hands)
    cache_key = f"{game_id}_hand_{target_hand.hand_number}_quick"
    if use_cache and cache_key in analysis_cache:
        cached_result = analysis_cache[cache_key]
        return {
            **cached_result,
            "cached": True
        }

    try:

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
        track_analysis_metrics(game_id, model, cost, analysis_count + 1, success=True)

        return result

    except Exception as e:
        logger.error(f"LLM analysis failed for game {game_id}: {e}")

        # Track failed attempt
        track_analysis_metrics(game_id, "error", 0.0, analysis_count + 1, success=False)

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


@router.get("/games/{game_id}/analysis-session")
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
        track_analysis_metrics(game_id, f"{model}_session", cost, hands_to_analyze, success=True)

        return result

    except Exception as e:
        logger.error(f"Session analysis failed for game {game_id}: {e}")

        # Track failed attempt
        track_analysis_metrics(game_id, "error_session", 0.0, hands_to_analyze, success=False)

        return {
            "analysis": {"error": "Session analysis not available", "details": str(e)},
            "model_used": "error",
            "cost": 0.0,
            "cached": False,
            "error": str(e),
            "hands_analyzed": hands_to_analyze
        }


@router.get("/admin/analysis-metrics")
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
