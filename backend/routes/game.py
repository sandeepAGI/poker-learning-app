"""Game routes - CRUD, actions, history endpoints."""
import uuid
import time
from typing import Dict, Optional
from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from game.poker_engine import PokerGame, GameState, HandEvaluator
from auth import verify_token
from models import Game, Hand
from database import get_db, save_completed_hand
from app_state import (
    games, CreateGameRequest, GameActionRequest, GameResponse,
)

router = APIRouter(tags=["game"])


def _build_game_response(game_id: str, game: PokerGame, show_ai_thinking: bool = False) -> GameResponse:
    """Build GameResponse from a PokerGame instance."""
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


@router.post("/games", response_model=Dict[str, str])
def create_game(
    request: CreateGameRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
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

    # Store user_id in game for later access
    game.user_id = user_id

    # Start first hand
    # MVP: Use process_ai=True for REST API flow (WebSocket support comes later)
    game.start_new_hand(process_ai=True)

    # Save game to database (must happen before save_completed_hand for FK)
    db_game = Game(
        game_id=game_id,
        user_id=user_id,
        num_ai_players=request.ai_count,
        starting_stack=game.players[0].stack,
        status="active"
    )
    db.add(db_game)
    db.commit()

    # Store in memory with timestamp
    games[game_id] = (game, time.time())

    # If hand completed during start_new_hand (e.g., heads-up AI fold), save it
    if game.last_hand_summary:
        save_completed_hand(game_id, game.last_hand_summary, user_id, db)

    return {"game_id": game_id}


@router.get("/games/{game_id}", response_model=GameResponse)
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

    return _build_game_response(game_id, game, show_ai_thinking)


@router.post("/games/{game_id}/actions")
def submit_action(
    game_id: str,
    request: GameActionRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
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

    # Save hand if completed (deduplication handled in save_completed_hand)
    if game.last_hand_summary and hasattr(game, 'user_id'):
        save_completed_hand(game_id, game.last_hand_summary, game.user_id, db)

    # Return updated game state
    return get_game_state(game_id)


@router.post("/games/{game_id}/next")
def next_hand(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
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

    # Save previous hand before starting new one
    if game.last_hand_summary and hasattr(game, 'user_id'):
        save_completed_hand(game_id, game.last_hand_summary, game.user_id, db)

    # Check if any players are eliminated
    active_players = [p for p in game.players if p.stack > 0]
    if len(active_players) <= 1:
        # Mark game as completed
        db_game = db.query(Game).filter(Game.game_id == game_id).first()
        if db_game:
            db_game.status = "completed"
            db_game.completed_at = datetime.utcnow()
            human_player = next((p for p in game.players if p.is_human), None)
            if human_player:
                db_game.final_stack = human_player.stack
                db_game.profit_loss = human_player.stack - db_game.starting_stack
            db.commit()

        raise HTTPException(status_code=400, detail="Game over. Only one player remaining.")

    # Start new hand
    game.start_new_hand()

    # Return updated game state
    return get_game_state(game_id)


@router.post("/games/{game_id}/quit")
async def quit_game(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Quit an active game and mark it as completed.

    Called when player manually quits (closes browser, clicks quit button, etc.)
    Saves current game state to history instead of losing it.
    """
    # Verify game exists and belongs to user
    db_game = db.query(Game).filter(
        Game.game_id == game_id,
        Game.user_id == user_id
    ).first()

    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    if db_game.status == "completed":
        # Already completed, just return success
        return {"message": "Game already completed"}

    # Get in-memory game state to save final stack and hand history
    game_tuple = games.get(game_id)
    if game_tuple:
        game, _ = game_tuple  # Extract PokerGame from tuple

        # Save the last completed hand if it exists
        if game.last_hand_summary and hasattr(game, 'user_id'):
            save_completed_hand(game_id, game.last_hand_summary, game.user_id, db)

        # Save final stack
        human_player = next((p for p in game.players if p.is_human), None)
        if human_player:
            db_game.final_stack = human_player.stack
            db_game.profit_loss = human_player.stack - db_game.starting_stack

    # Mark as completed
    db_game.status = "completed"
    db_game.completed_at = datetime.utcnow()
    db.commit()

    # Clean up in-memory state
    if game_id in games:
        del games[game_id]

    return {"message": "Game quit successfully", "game_id": game_id}


@router.get("/users/me/games")
async def get_my_games(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get user's completed games.

    Returns most recent games ordered by started_at descending.
    Only returns completed games (not active).
    """
    games_list = db.query(Game).filter(
        Game.user_id == user_id,
        Game.status == "completed"
    ).order_by(Game.started_at.desc()).limit(limit).all()

    return {
        "games": [
            {
                "game_id": g.game_id,
                "started_at": g.started_at.isoformat() if g.started_at else None,
                "completed_at": g.completed_at.isoformat() if g.completed_at else None,
                "total_hands": g.total_hands,
                "starting_stack": g.starting_stack,
                "final_stack": g.final_stack,
                "profit_loss": g.profit_loss,
                "num_ai_players": g.num_ai_players
            }
            for g in games_list
        ]
    }


@router.get("/games/{game_id}/hands")
async def get_game_hands(
    game_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get all hands for a game.

    Verifies game belongs to user before returning hands.
    Returns hands ordered by hand_number.
    """
    # Verify game ownership
    game = db.query(Game).filter(
        Game.game_id == game_id,
        Game.user_id == user_id
    ).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get hands
    hands = db.query(Hand).filter(
        Hand.game_id == game_id
    ).order_by(Hand.hand_number).all()

    return {
        "hands": [
            {
                "hand_id": str(h.hand_id),
                "hand_number": h.hand_number,
                "hand_data": h.hand_data,
                "user_hole_cards": h.user_hole_cards,
                "user_won": h.user_won,
                "pot": h.pot,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in hands
        ]
    }


@router.get("/games/{game_id}/history")
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
    hands_data = [asdict(hand) for hand in hands]

    return {
        "session_id": game.session_id,
        "total_hands": len(game.hand_history),
        "returned_hands": len(hands_data),
        "hands": hands_data
    }
