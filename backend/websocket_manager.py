"""
WebSocket Manager for Real-Time Game Updates
Phase 1: WebSocket infrastructure for smooth AI turn visibility
Phase 8: Thread-safe game action processing (concurrency & race conditions)
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Callable, Awaitable
import json
import asyncio
from game.poker_engine import PokerGame, GameState, Player, AIStrategy, HandEvaluator


class ThreadSafeGameManager:
    """
    Thread-safe game action manager using asyncio.Lock.

    Prevents race conditions when multiple WebSocket connections
    send actions simultaneously to the same game.

    Phase 8.3: Critical for production reliability.
    """

    def __init__(self):
        # Store locks per game: {game_id: asyncio.Lock}
        self.locks: Dict[str, asyncio.Lock] = {}

    async def execute_action(self, game_id: str, action_fn: Callable[[], Awaitable[Any]]) -> Any:
        """
        Execute action with exclusive lock for this game.

        Only one action per game can execute at a time.
        This prevents race conditions from simultaneous actions.

        Args:
            game_id: Game identifier
            action_fn: Async function to execute (action logic)

        Returns:
            Result from action_fn
        """
        # Create lock for this game if doesn't exist
        if game_id not in self.locks:
            self.locks[game_id] = asyncio.Lock()

        print(f"[ThreadSafe] Waiting for lock: game={game_id[:8]}")

        # Acquire lock and execute action
        async with self.locks[game_id]:
            print(f"[ThreadSafe] Lock acquired: game={game_id[:8]}")
            # Only one concurrent action per game allowed
            result = await action_fn()
            print(f"[ThreadSafe] Lock released: game={game_id[:8]}")
            return result

    def cleanup_lock(self, game_id: str):
        """Remove lock for game (call when game is deleted)"""
        if game_id in self.locks:
            del self.locks[game_id]
            print(f"[ThreadSafe] Cleaned up lock for game {game_id}")


class ConnectionManager:
    """Manages WebSocket connections for active games"""

    def __init__(self):
        # Store active connections: {game_id: List[WebSocket]} - Phase 8: Support multiple connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store step mode state: {game_id: continue_event}
        self.step_mode_events: Dict[str, asyncio.Event] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a game"""
        await websocket.accept()

        # Phase 8: Support multiple WebSocket connections per game
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []

        self.active_connections[game_id].append(websocket)
        connection_count = len(self.active_connections[game_id])
        print(f"[WebSocket] Client connected to game {game_id} (total connections: {connection_count})")

    def disconnect(self, game_id: str, websocket: WebSocket = None):
        """Remove a WebSocket connection"""
        if game_id in self.active_connections:
            if websocket:
                # Phase 8: Remove specific websocket from list
                try:
                    self.active_connections[game_id].remove(websocket)
                    remaining = len(self.active_connections[game_id])
                    print(f"[WebSocket] Client disconnected from game {game_id} (remaining: {remaining})")

                    # Clean up empty list
                    if remaining == 0:
                        del self.active_connections[game_id]
                except ValueError:
                    pass  # WebSocket not in list
            else:
                # Legacy behavior: remove all connections
                del self.active_connections[game_id]
                print(f"[WebSocket] All clients disconnected from game {game_id}")

        # Clean up step mode event if exists and no more connections
        if game_id not in self.active_connections and game_id in self.step_mode_events:
            del self.step_mode_events[game_id]

    def signal_continue(self, game_id: str):
        """Signal that user wants to continue to next AI action"""
        if game_id in self.step_mode_events:
            self.step_mode_events[game_id].set()
            print(f"[WebSocket] Continue signal received for game {game_id}")

    async def send_event(self, game_id: str, event: Dict[str, Any]):
        """Send an event to all WebSocket connections for a game"""
        if game_id in self.active_connections:
            # Phase 8: Send to ALL connections for this game
            dead_connections = []
            for ws in self.active_connections[game_id]:
                try:
                    await ws.send_json(event)
                except Exception as e:
                    print(f"[WebSocket] Error sending to game {game_id}: {e}")
                    dead_connections.append(ws)

            # Clean up dead connections
            for ws in dead_connections:
                self.disconnect(game_id, ws)

    async def broadcast_state(self, game_id: str, game: PokerGame, show_ai_thinking: bool = False):
        """Broadcast current game state to connected client"""
        state_data = serialize_game_state(game, show_ai_thinking)
        await self.send_event(game_id, {
            "type": "state_update",
            "data": state_data
        })


# Global connection manager instance
manager = ConnectionManager()

# Global thread-safe game manager (Phase 8: Concurrency)
thread_safe_manager = ThreadSafeGameManager()


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

    # FIX Issue #3: AI decisions data - always include decision_id for deduplication
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
                "spr": decision.spr,
                "decision_id": decision.decision_id  # Always include for deduplication
            }
    else:
        # Even with thinking hidden, include decision_id for reliable deduplication
        for player_id, decision in game.last_ai_decisions.items():
            ai_decisions_data[player_id] = {
                "action": decision.action,
                "amount": decision.amount,
                "decision_id": decision.decision_id  # Critical for deduplication
            }

    # FIX-09: Enhanced winner info with poker-accurate hand reveals (same as main.py)
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

    # FIX Issue #2: Use stored blind positions (don't recompute)
    # Blind positions are set at the start of the hand and should not change
    # even if a blind poster busts mid-hand. This matches REST API behavior.
    dealer_position = game.dealer_index
    sb_position = game.small_blind_index
    bb_position = game.big_blind_index

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
        "hand_count": game.hand_count,
        "dealer_position": dealer_position,
        "small_blind_position": sb_position,
        "big_blind_position": bb_position,
        "last_raise_amount": game.last_raise_amount  # Issue #2: Minimum raise tracking
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

        # CRITICAL: Check if action succeeded
        # Bug fix: If action fails validation, force fold to prevent infinite loop
        if not result["success"]:
            print(f"[WebSocket] ⚠️  AI action FAILED for {current_player.name}: {result.get('error', 'Unknown error')}")
            print(f"[WebSocket] Applying fallback: force fold to prevent infinite loop")

            # Force fold as fallback
            fallback_result = game.apply_action(
                player_index=game.current_player_index,
                action="fold",
                amount=0,
                hand_strength=decision.hand_strength,
                reasoning=f"[FORCED FOLD] Original {decision.action} failed: {result.get('error')}"
            )

            # Emit fallback action event
            await manager.send_event(game_id, {
                "type": "ai_action",
                "data": {
                    "player_id": current_player.player_id,
                    "player_name": current_player.name,
                    "action": "fold",
                    "amount": 0,
                    "reasoning": f"[FORCED FOLD] {decision.action} failed validation" if show_ai_thinking else None,
                    "stack_after": current_player.stack,
                    "pot_after": game.pot,
                    "bet_amount": 0
                }
            })

            # Broadcast updated state
            await manager.broadcast_state(game_id, game, show_ai_thinking)

            # Check if fallback fold triggered showdown
            if game.current_player_index is None or fallback_result["triggers_showdown"]:
                break

            # Move to next player
            game.current_player_index = game._get_next_active_player_index(
                game.current_player_index + 1
            )

            # Continue to next iteration (skip normal action processing)
            continue

        # Emit AI action event (only if action succeeded)
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
                # Issue #4: Notify frontend that we auto-resumed after timeout
                await manager.send_event(game_id, {
                    "type": "auto_resumed",
                    "data": {
                        "reason": "timeout",
                        "timeout_seconds": 60
                    }
                })
                print(f"[WebSocket] 📤 Sent 'auto_resumed' event after timeout")
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
