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
        # Store step mode state: {game_id: continue_event}
        self.step_mode_events: Dict[str, asyncio.Event] = {}

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
        # Clean up step mode event if exists
        if game_id in self.step_mode_events:
            del self.step_mode_events[game_id]

    def signal_continue(self, game_id: str):
        """Signal that user wants to continue to next AI action"""
        if game_id in self.step_mode_events:
            self.step_mode_events[game_id].set()
            print(f"[WebSocket] Continue signal received for game {game_id}")

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


async def process_ai_turns_with_events(game: PokerGame, game_id: str, show_ai_thinking: bool = False, step_mode: bool = False):
    """
    Process AI turns one-by-one and emit events for each action.
    This is the key function that enables smooth turn-by-turn gameplay!

    Args:
        game: The PokerGame instance
        game_id: Game identifier
        show_ai_thinking: Whether to include AI reasoning in events
        step_mode: If True, pause after each AI action and wait for user to continue (UAT-1 fix)
    """
    import time
    start_time = time.time()
    print(f"[WebSocket] ====== Processing AI turns for game {game_id} (step_mode={step_mode}, state={game.current_state.value}) ======")

    # CRITICAL: Infinite loop protection
    max_iterations = 50  # Safety limit (4 players * 4 betting rounds * 3 raises per round)
    iteration_count = 0
    last_player_index = None
    same_player_count = 0

    while game.current_player_index is not None:
        iteration_count += 1

        # SAFETY: Detect infinite loop
        if iteration_count > max_iterations:
            print(f"[WebSocket] ⚠️  INFINITE LOOP DETECTED! Stopping after {iteration_count} iterations")
            print(f"[WebSocket] Game state: {game.current_state.value}, current_player_index={game.current_player_index}")
            print(f"[WebSocket] Active players: {[(p.name, p.is_active, p.all_in, p.has_acted) for p in game.players]}")
            break

        # SAFETY: Detect same player looping
        if game.current_player_index == last_player_index:
            same_player_count += 1
            if same_player_count > 5:
                print(f"[WebSocket] ⚠️  STUCK ON SAME PLAYER! Player index {game.current_player_index} ({game.players[game.current_player_index].name}) has been processed {same_player_count} times in a row")
                print(f"[WebSocket] Player state: is_active={game.players[game.current_player_index].is_active}, all_in={game.players[game.current_player_index].all_in}, has_acted={game.players[game.current_player_index].has_acted}")
                break
        else:
            same_player_count = 0
        last_player_index = game.current_player_index
        # CRITICAL: Check if betting round is complete FIRST (prevents infinite loop)
        if game._betting_round_complete():
            print(f"[WebSocket] Betting round complete (checked at loop start)")
            break

        current_player = game.players[game.current_player_index]

        # Stop if we reach a human player who hasn't acted yet (wait for their action)
        if current_player.is_human and not current_player.all_in and not current_player.has_acted:
            print(f"[WebSocket] Reached human player, waiting for action")
            break

        # Skip inactive, all-in, or already-acted players
        if not current_player.is_active or current_player.all_in or current_player.has_acted:
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )
            continue

        action_start = time.time()
        print(f"[WebSocket] >>> AI turn #{len([p for p in game.players if not p.is_human and not p.is_active]) + 1}: {current_player.name} (player_index={game.current_player_index})")

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

        # Use apply_action() - SINGLE SOURCE OF TRUTH for action processing
        # This fixes all the divergence bugs (raise accounting, last_raiser_index, has_acted)
        result = game.apply_action(
            player_index=game.current_player_index,
            action=decision.action,
            amount=decision.amount,
            hand_strength=decision.hand_strength,
            reasoning=decision.reasoning
        )

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
                "pot_after": game.pot,
                "bet_amount": result["bet_amount"]
            }
        })

        # Broadcast updated state
        await manager.broadcast_state(game_id, game, show_ai_thinking)

        # STEP MODE: Pause IMMEDIATELY after AI action (no delay first!)
        if step_mode:
            print(f"[WebSocket] 🎮 STEP MODE: Pausing after {current_player.name}'s {decision.action}")
            # Create a new event for this game if not exists
            if game_id not in manager.step_mode_events:
                manager.step_mode_events[game_id] = asyncio.Event()

            # Clear any previous continue signal
            manager.step_mode_events[game_id].clear()

            # Send "awaiting_continue" event to frontend
            await manager.send_event(game_id, {
                "type": "awaiting_continue",
                "data": {
                    "player_name": current_player.name,
                    "action": decision.action
                }
            })
            print(f"[WebSocket] 📤 Sent 'awaiting_continue' event for {current_player.name}")

            wait_start = time.time()
            print(f"[WebSocket] ⏸️  PAUSED - Waiting for continue signal... (t={wait_start - start_time:.2f}s)")
            # Wait for user to click "Continue" button (with 60 second timeout for safety)
            try:
                await asyncio.wait_for(manager.step_mode_events[game_id].wait(), timeout=60.0)
                continue_received = time.time()
                print(f"[WebSocket] ▶️  Continue signal received (waited {continue_received - wait_start:.2f}s, total t={continue_received - start_time:.2f}s)")
                # Small delay after continue to let user see the action before next one
                await asyncio.sleep(0.3)
                after_delay = time.time()
                print(f"[WebSocket] Post-continue delay done (0.3s), continuing loop (t={after_delay - start_time:.2f}s)")
            except asyncio.TimeoutError:
                print(f"[WebSocket] Step mode: Timeout waiting for continue (proceeding anyway)")
        else:
            # Non-step mode: Small delay for better UX visibility
            await asyncio.sleep(0.5)

        # Check if action triggered showdown (e.g., all others folded)
        # apply_action() sets current_player_index = None when hand is complete
        if game.current_player_index is None or result["triggers_showdown"]:
            break

        # Move to next player
        game.current_player_index = game._get_next_active_player_index(
            game.current_player_index + 1
        )

        # Check if betting round is complete
        if game._betting_round_complete():
            break

    # Check if we should advance game state
    if game._betting_round_complete():
        advance_start = time.time()
        print(f"[WebSocket] 🔄 Betting round complete, advancing state (t={advance_start - start_time:.2f}s)")
        advanced = game._advance_state_for_websocket()
        advance_done = time.time()
        print(f"[WebSocket] State advanced: {advanced}, new state={game.current_state.value if advanced else 'N/A'} (took {advance_done - advance_start:.3f}s)")

        if advanced:
            await manager.broadcast_state(game_id, game, show_ai_thinking)
            broadcast_done = time.time()
            print(f"[WebSocket] State broadcast done (took {broadcast_done - advance_done:.3f}s, total t={broadcast_done - start_time:.2f}s)")

            # If still AI turns remaining (next betting round), continue
            current = game.get_current_player()
            if current and not current.is_human:
                print(f"[WebSocket] 🔁 Next player is AI ({current.name}), recursively processing AI turns...")
                await process_ai_turns_with_events(game, game_id, show_ai_thinking, step_mode)
            else:
                print(f"[WebSocket] Next player is human or None, stopping AI processing")
    else:
        # Betting round not complete - send final state update so frontend knows it's human's turn
        # This is critical: the loop may have broken because we reached a human player,
        # but the last state broadcast was BEFORE current_player_index was updated
        final_broadcast_start = time.time()
        print(f"[WebSocket] Betting round NOT complete, sending final state broadcast (t={final_broadcast_start - start_time:.2f}s)")
        await manager.broadcast_state(game_id, game, show_ai_thinking)
        final_broadcast_done = time.time()
        print(f"[WebSocket] Final broadcast done (took {final_broadcast_done - final_broadcast_start:.3f}s)")

    end_time = time.time()
    print(f"[WebSocket] ====== AI turn processing complete for game {game_id} (total time: {end_time - start_time:.2f}s) ======")
