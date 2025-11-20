"""
WebSocket Manager for Real-Time Game Updates
Phase 1: WebSocket infrastructure for smooth AI turn visibility
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import asyncio
from game.poker_engine import PokerGame, GameState, Player, AIStrategy


class ConnectionManager:
    """Manages WebSocket connections for active games"""

    def __init__(self):
        # Store active connections: {game_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a game"""
        await websocket.accept()
        self.active_connections[game_id] = websocket
        print(f"[WebSocket] Client connected to game {game_id}")

    def disconnect(self, game_id: str):
        """Remove a WebSocket connection"""
        if game_id in self.active_connections:
            del self.active_connections[game_id]
            print(f"[WebSocket] Client disconnected from game {game_id}")

    async def send_event(self, game_id: str, event: Dict[str, Any]):
        """Send an event to a specific game's WebSocket"""
        if game_id in self.active_connections:
            try:
                await self.active_connections[game_id].send_json(event)
            except Exception as e:
                print(f"[WebSocket] Error sending to game {game_id}: {e}")
                self.disconnect(game_id)

    async def broadcast_state(self, game_id: str, game: PokerGame, show_ai_thinking: bool = False):
        """Broadcast current game state to connected client"""
        state_data = serialize_game_state(game, show_ai_thinking)
        await self.send_event(game_id, {
            "type": "state_update",
            "data": state_data
        })


# Global connection manager instance
manager = ConnectionManager()


def serialize_game_state(game: PokerGame, show_ai_thinking: bool = False) -> Dict[str, Any]:
    """Convert PokerGame to serializable dictionary"""

    # Find human player
    human_player = next((p for p in game.players if p.is_human), None)
    if not human_player:
        raise ValueError("No human player found")

    # Build player list
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

    # AI decisions data
    ai_decisions_data = {}
    if show_ai_thinking:
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount,
                "reasoning": decision.reasoning,
                "hand_strength": decision.hand_strength,
                "pot_odds": decision.pot_odds,
                "confidence": decision.confidence,
                "spr": decision.spr
            }
    else:
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount
            }

    # Winner information at showdown
    winner_info = None
    if game.current_state == GameState.SHOWDOWN:
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

    return {
        "state": game.current_state.value,
        "pot": game.pot,
        "current_bet": game.current_bet,
        "players": players_data,
        "community_cards": game.community_cards,
        "current_player_index": game.current_player_index,
        "human_player": human_data,
        "last_ai_decisions": ai_decisions_data,
        "winner_info": winner_info,
        "small_blind": game.small_blind,
        "big_blind": game.big_blind,
        "hand_count": game.hand_count
    }


async def process_ai_turns_with_events(game: PokerGame, game_id: str, show_ai_thinking: bool = False):
    """
    Process AI turns one-by-one and emit events for each action.
    This is the key function that enables smooth turn-by-turn gameplay!
    """
    print(f"[WebSocket] Processing AI turns for game {game_id}")

    while game.current_player_index is not None:
        current_player = game.players[game.current_player_index]

        # Stop if we reach a human player (wait for their action)
        if current_player.is_human and not current_player.all_in:
            print(f"[WebSocket] Reached human player, waiting for action")
            break

        # Skip inactive or all-in players
        if not current_player.is_active or current_player.all_in:
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )
            continue

        print(f"[WebSocket] Processing AI turn: {current_player.name}")

        # Get AI decision
        decision = AIStrategy.make_decision_with_reasoning(
            current_player.personality,
            current_player.hole_cards,
            game.community_cards,
            game.current_bet,
            game.pot,
            current_player.stack,
            current_player.current_bet,
            game.big_blind
        )

        # Store decision
        game.last_ai_decisions[current_player.player_id] = decision

        # Apply action to game state
        if decision.action == "fold":
            current_player.is_active = False
        elif decision.action == "call":
            call_amount = game.current_bet - current_player.current_bet
            current_player.bet(call_amount)
            game.pot += call_amount
        elif decision.action == "raise":
            current_player.bet(decision.amount)
            game.current_bet = current_player.current_bet
            game.pot += decision.amount

        current_player.has_acted = True

        # Emit AI action event
        await manager.send_event(game_id, {
            "type": "ai_action",
            "data": {
                "player_id": current_player.player_id,
                "player_name": current_player.name,
                "action": decision.action,
                "amount": decision.amount,
                "reasoning": decision.reasoning if show_ai_thinking else None,
                "stack_after": current_player.stack,
                "pot_after": game.pot
            }
        })

        # Small delay for UX (frontend can also add delay)
        await asyncio.sleep(0.5)

        # Broadcast updated state
        await manager.broadcast_state(game_id, game, show_ai_thinking)

        # Move to next player
        game.current_player_index = game._get_next_active_player_index(
            game.current_player_index + 1
        )

        # Check if betting round is complete
        if game._betting_round_complete():
            break

    # Check if we should advance game state
    if game._betting_round_complete():
        print(f"[WebSocket] Betting round complete, advancing state")
        advanced = game._advance_state_for_websocket()

        if advanced:
            await manager.broadcast_state(game_id, game, show_ai_thinking)

            # If still AI turns remaining (next betting round), continue
            current = game.get_current_player()
            if current and not current.is_human:
                await process_ai_turns_with_events(game, game_id, show_ai_thinking)

    print(f"[WebSocket] AI turn processing complete for game {game_id}")
