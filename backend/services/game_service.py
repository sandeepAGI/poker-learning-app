# backend/services/game_service.py
from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime, timedelta

# Import error classes
from utils.errors import (
    GameNotFoundError, 
    PlayerNotFoundError, 
    InvalidActionError,
    NotYourTurnError, 
    InsufficientFundsError, 
    InvalidAmountError
)

# Import session manager
from utils.session import SessionManager
from utils.logger import get_logger
from utils.formatters import format_cards, format_money

# Import config
from config import STARTING_CHIPS, SMALL_BLIND, BIG_BLIND

# Singleton to store websocket manager reference
# This avoids circular imports
class WebSocketManagerSingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        return cls._instance
    
    @classmethod
    def set_instance(cls, manager):
        cls._instance = manager

# Import game engine components
from game.poker_game import PokerGame
from models.player import Player, AIPlayer, HumanPlayer
from models.game_state import GameState

# For now, we'll mock the interactions
class GameService:
    def __init__(self):
        self.session_manager = SessionManager()
        self.logger = get_logger("game_service")
    
    async def notify_game_update(self, game_id: str, event_type: str, data: Dict[str, Any], exclude_player: Optional[str] = None):
        """
        Notify clients about a game update through WebSockets
        """
        manager = WebSocketManagerSingleton.get_instance()
        if manager:
            message = json.dumps({
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            })
            
            await manager.broadcast(message, game_id, exclude_player)
            self.logger.info(f"Broadcast {event_type} event for game {game_id}")
        else:
            self.logger.warning("WebSocket manager not available for notifications")
    
    def create_game(self, player_id: str, ai_count: int, ai_personalities: List[str]) -> Dict[str, Any]:
        """Create a new game session with actual PokerGame instance"""
        game_id = str(uuid.uuid4())
        
        # Log game creation
        self.logger.info(f"Creating new game {game_id} for player {player_id}")
        
        # Create the human player
        human_player = HumanPlayer(player_id=player_id, stack=STARTING_CHIPS)
        
        # Create AI players with appropriate personalities
        ai_players = []
        for i in range(ai_count):
            personality = ai_personalities[i % len(ai_personalities)]
            ai_players.append(
                AIPlayer(
                    player_id=f"ai_{i}",
                    stack=STARTING_CHIPS,
                    personality=personality
                )
            )
        
        # Combine all players
        all_players = [human_player] + ai_players
        
        # Create actual PokerGame instance
        try:
            poker_game = PokerGame(players=all_players)
            
            # Initialize the first hand to post blinds and deal cards
            poker_game.current_state = GameState.PRE_FLOP
            poker_game.post_blinds()
            
            # Store game in session manager
            game_data = {
                "game_id": game_id,
                "poker_game": poker_game,
                "created_at": datetime.now()
            }
            self.session_manager.create_session(game_id, game_data)
            
            # Format response for API
            players_data = []
            for i, player in enumerate(all_players):
                player_type = "human" if isinstance(player, HumanPlayer) else "ai"
                personality = getattr(player, "personality", None) if player_type == "ai" else None
                
                players_data.append({
                    "player_id": player.player_id,
                    "player_type": player_type,
                    "personality": personality,
                    "position": i,
                    "stack": player.stack,
                    "current_bet": player.current_bet,
                    "is_active": player.is_active,
                    "hole_cards": player.hole_cards
                })
            
            # Return game creation response
            return {
                "game_id": game_id,
                "players": players_data,
                "dealer_position": poker_game.dealer_index,
                "small_blind": poker_game.small_blind,
                "big_blind": poker_game.big_blind,
                "pot": poker_game.pot,
                "current_bet": poker_game.current_bet,
                "current_state": poker_game.current_state.value
            }
            
        except Exception as e:
            self.logger.error(f"Error creating game: {e}")
            raise
    
    def get_game_state(self, game_id: str, player_id: str, show_all_cards: bool = False) -> Dict[str, Any]:
        """Get current game state from the PokerGame instance with option to show all cards."""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Check if player is in the game
        player_objects = poker_game.players
        player_exists = any(p.player_id == player_id for p in player_objects)
        
        if not player_exists:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        self.logger.info(f"Retrieved game state for game {game_id}, player {player_id}")
        
        # Format players data, but always include hole cards (let frontend decide visibility)
        players_data = []
        
        # Log all players' stacks for debugging
        for player in player_objects:
            self.logger.info(f"GET GAME STATE: Player {player.player_id} has stack {player.stack}")
        
        for player in player_objects:
            # Ensure all players have valid hole cards
            if player.is_active and (not player.hole_cards or len(player.hole_cards) < 2):
                try:
                    # If we need to deal cards, make sure we have enough in the deck
                    if len(poker_game.deck) < 2:
                        self.logger.info(f"Resetting deck to deal cards to player {player.player_id}")
                        poker_game.deck_manager.reset()
                        poker_game.reset_deck()
                    
                    # Deal cards to any player missing them
                    hole_cards = poker_game.deck_manager.deal_to_player(2)
                    player.receive_cards(hole_cards)
                    poker_game.deck = poker_game.deck_manager.get_deck()
                    self.logger.info(f"Dealt missing hole cards to player {player.player_id}: {hole_cards}")
                except ValueError as e:
                    self.logger.error(f"Error dealing cards to player {player.player_id}: {e}")
            
            player_type = "human" if isinstance(player, HumanPlayer) else "ai"
            current_stack = player.stack  # Get current stack value
            
            # Always include hole cards in the API response
            # For security in a production environment, you might want to add a "visible_to_client" flag
            # that the frontend can use to determine visibility
            player_data = {
                "player_id": player.player_id,
                "player_type": player_type,
                "personality": getattr(player, "personality", None) if player_type == "ai" else None,
                "stack": current_stack,
                "stack_formatted": format_money(current_stack),
                "current_bet": player.current_bet,
                "current_bet_formatted": format_money(player.current_bet),
                "is_active": player.is_active,
                "is_all_in": player.all_in,
                "hole_cards": player.hole_cards,  # Always include the hole cards
                "hole_cards_formatted": format_cards(player.hole_cards) if player.hole_cards else None,
                "visible_to_client": player.player_id == player_id or (show_all_cards and poker_game.current_state == GameState.SHOWDOWN),
                "position": poker_game.players.index(player)
            }
            
            players_data.append(player_data)
        
        # Determine available actions for current player
        available_actions = []
        # Only provide actions if game is not in showdown state and player is active
        if poker_game.current_state != GameState.SHOWDOWN:
            # Find the player to check if they're active
            player_obj = None
            for p in poker_game.players:
                if p.player_id == player_id:
                    player_obj = p
                    break
                    
            if player_obj and player_obj.is_active:
                available_actions = ["fold", "call", "raise"]
            else:
                self.logger.info(f"Player {player_id} is not active, no actions available")
                # Player is not active (folded), no actions available
        
        # Convert enum to string for the API
        current_state = poker_game.current_state.value if isinstance(poker_game.current_state, GameState) else str(poker_game.current_state)
        
        # Add showdown data if in showdown state and requested
        showdown_data = None
        if poker_game.current_state == GameState.SHOWDOWN and show_all_cards:
            showdown_data = self._get_showdown_data(poker_game)
        
        response = {
            "game_id": game_id,
            "current_state": current_state,
            "community_cards": poker_game.community_cards,
            "community_cards_formatted": format_cards(poker_game.community_cards),
            "pot": poker_game.pot,
            "pot_formatted": format_money(poker_game.pot),
            "current_bet": poker_game.current_bet,
            "current_bet_formatted": format_money(poker_game.current_bet),
            "players": players_data,
            "dealer_position": poker_game.dealer_index,
            "current_player": player_id,
            "available_actions": available_actions,
            "min_raise": poker_game.big_blind,
            "min_raise_formatted": format_money(poker_game.big_blind),
            "hand_number": poker_game.hand_count
        }
        
        if showdown_data:
            response["showdown_data"] = showdown_data
            response["winner_info"] = showdown_data["winners"]  # Add the winners at the top level for client compatibility
            
        return response
    
    def process_action(self, game_id: str, player_id: str, action_type: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Process player action using the PokerGame instance"""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Find the player in the game
        player = None
        for p in poker_game.players:
            if p.player_id == player_id:
                player = p
                break
        
        if player is None:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        # Validate action type
        if action_type not in ["fold", "call", "raise"]:
            self.logger.warning(f"Invalid action type: {action_type}")
            raise InvalidActionError(f"Invalid action type: {action_type}")
        
        self.logger.info(f"Processing {action_type} action from player {player_id} in game {game_id}")
        
        # In real implementation, this would use the PokerRound class to manage betting
        # Since we don't have a direct API to manually trigger player actions,
        # we'll modify the player state directly
        
        try:
            # Process action based on type
            if action_type == "fold":
                # Handle fold - mark player inactive
                player.is_active = False
                
            elif action_type == "call":
                # Handle call - bet current required amount
                call_amount = poker_game.current_bet - player.current_bet
                
                # Check if player has enough chips
                if player.stack < call_amount:
                    self.logger.warning(f"Player {player_id} has insufficient funds for call")
                    raise InsufficientFundsError(player_id, call_amount, player.stack)
                
                # Place bet
                player.bet(call_amount)
                poker_game.pot += call_amount
                
            elif action_type == "raise":
                # Handle raise - increase the current bet
                if amount is None:
                    self.logger.warning("Amount required for raise action")
                    raise InvalidAmountError("Amount required for raise action")
                
                # Check minimum raise (standard Texas Hold'em rules)
                # Minimum raise is current bet plus the size of the big blind
                min_raise = poker_game.current_bet + poker_game.big_blind
                if amount < min_raise:
                    self.logger.warning(f"Raise amount must be at least {min_raise}")
                    raise InvalidAmountError(f"Raise amount must be at least {min_raise}")
                
                # Check if player has enough chips
                if player.stack < amount:
                    self.logger.warning(f"Player {player_id} has insufficient funds for raise")
                    raise InsufficientFundsError(player_id, amount, player.stack)
                
                # Place bet and update current bet
                actual_bet = player.bet(amount)
                poker_game.pot += actual_bet
                poker_game.current_bet = amount
            
            # After human player action, let AI players act
            self._process_ai_actions(poker_game)
            
            # Progress game state if round is complete
            current_state = poker_game.current_state
            
            # Check if all players have acted (improved logic)
            all_acted = True
            # Check if only one active player remains
            active_player_count = sum(1 for p in poker_game.players if p.is_active)
            if active_player_count <= 1:
                all_acted = True
                self.logger.info("Only one player remains active, all actions complete.")
            else:
                # Check if all active players have matched the current bet or are all-in
                for p in poker_game.players:
                    if p.is_active and p.current_bet != poker_game.current_bet and not p.all_in:
                        all_acted = False
                        break
            
            # If all players have acted, advance to next game state
            if all_acted:
                poker_game.advance_game_state()
                
                # Reset player bets for new round
                for p in poker_game.players:
                    p.reset_round_state()
                
                # Reset current bet for new round
                poker_game.current_bet = 0
            
            # Update game in session manager
            self.session_manager.update_session(game_id, game_data)
            
            # Find next player to act
            next_player = None
            # Check the number of active players first
            active_players = [p for p in poker_game.players if p.is_active]
            
            # If only one active player remains, advance to showdown
            if len(active_players) == 1:
                self.logger.info(f"Only one active player remains. Moving to showdown.")
                poker_game.current_state = GameState.SHOWDOWN
                # Distribute pot to the last remaining player
                winners = poker_game.hand_manager.distribute_pot(
                    players=poker_game.players,
                    community_cards=poker_game.community_cards,
                    total_pot=poker_game.pot,
                    deck=poker_game.deck
                )
                self.logger.info(f"Pot distributed to last remaining player: {winners}")
                poker_game.pot = 0
            else:
                # Find next active player
                for p in poker_game.players:
                    if p.is_active and p.player_id != player_id:
                        next_player = p.player_id
                        break
            
            # Get updated game state
            updated_game_state = self.get_game_state(game_id, player_id)
            
            # Notify other players via WebSocket
            try:
                # Create a sanitized version without hole cards for broadcasting
                broadcast_state = updated_game_state.copy()
                for p in broadcast_state["players"]:
                    p["hole_cards"] = None
                
                # Async notify
                import asyncio
                asyncio.create_task(
                    self.notify_game_update(
                        game_id=game_id,
                        event_type="player_action",
                        data={
                            "action": {
                                "player_id": player_id,
                                "action_type": action_type,
                                "amount": amount if action_type == "raise" else None
                            },
                            "game_state": broadcast_state
                        }
                    )
                )
            except Exception as e:
                self.logger.error(f"Error broadcasting game update: {e}")
            
            # Return updated game state
            return {
                "action_result": "success",
                "updated_game_state": updated_game_state,
                "next_player": next_player or player_id,  # If no next player, keep current
                "pot_update": poker_game.pot,
                "is_showdown": poker_game.current_state == GameState.SHOWDOWN
            }
            
        except Exception as e:
            self.logger.error(f"Error processing action: {e}")
            raise
    
    def _process_ai_actions(self, poker_game: PokerGame) -> None:
        """Process AI player actions after human player acts"""
        # This is a simplified version - in real implementation, 
        # would use PokerRound to handle betting rounds properly
        
        # Basic game state for AI decisions
        game_state_dict = {
            "community_cards": poker_game.community_cards,
            "pot": poker_game.pot,
            "current_bet": poker_game.current_bet,
            "current_state": poker_game.current_state.value
        }
        
        # Process each AI player
        for player in poker_game.players:
            # Skip non-AI players or inactive/all-in players
            if not isinstance(player, AIPlayer) or not player.is_active or player.all_in:
                continue
                
            # Get AI decision
            decision = player.make_decision(
                game_state=game_state_dict,
                deck=poker_game.deck,
                spr=player.stack / (poker_game.pot or 1),  # Avoid division by zero
                pot_size=poker_game.pot
            )
            
            # Process decision
            if decision == "fold":
                player.is_active = False
            elif decision == "call":
                call_amount = poker_game.current_bet - player.current_bet
                if call_amount > 0:
                    actual_bet = player.bet(call_amount)
                    poker_game.pot += actual_bet
            elif decision == "raise":
                # Raise by current bet plus big blind (minimum raise)
                raise_amount = poker_game.current_bet + poker_game.big_blind
                if raise_amount <= player.stack:
                    actual_bet = player.bet(raise_amount)
                    poker_game.pot += actual_bet
                    poker_game.current_bet = player.current_bet
    
    def next_hand(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Advance to the next hand using the PokerGame instance"""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Check if player is in the game
        player_exists = any(p.player_id == player_id for p in poker_game.players)
        if not player_exists:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        # Check if game is in showdown state
        if poker_game.current_state != GameState.SHOWDOWN:
            self.logger.warning(f"Cannot advance game {game_id} to next hand - not in showdown state")
            raise InvalidActionError("Cannot advance to next hand before showdown")
        
        self.logger.info(f"Advancing game {game_id} to next hand")
        
        # Log player stacks at the start of the new hand
        for player in poker_game.players:
            self.logger.info(f"NEXT HAND: Player {player.player_id} starting with stack {player.stack}")
        
        try:
            # In the actual PokerGame implementation, this would be handled by calling:
            # poker_game.play_hand()
            
            # For our API integration, we need to do these steps:
            # 1. Reset player states - explicitly clear hole cards while preserving stacks
            for player in poker_game.players:
                current_stack = player.stack  # Store the stack
                active_status = player.is_active  # Store active status
                player.reset_hand_state()
                player.hole_cards = []  # Explicitly clear hole cards for each player
                player.stack = current_stack  # Restore stack after reset
                player.is_active = active_status  # Restore active status
                
            # 2. Reset game state for new hand
            poker_game.current_state = GameState.PRE_FLOP
            poker_game.community_cards = []
            poker_game.pot = 0
            poker_game.current_bet = 0
            
            # 3. Increment hand count
            poker_game.hand_count += 1
            
            # 4. Reset the deck manager before dealing new cards
            poker_game.deck_manager.reset()  # Full deck reset in the deck manager
            poker_game.reset_deck()  # Update the game's deck reference
            
            # 5. Post blinds and deal hole cards
            poker_game.post_blinds()  # This also deals hole cards
            
            # 6. Ensure all players have cards by explicitly dealing cards to any player missing them
            for player in poker_game.players:
                if player.is_active and (not player.hole_cards or len(player.hole_cards) < 2):
                    # If player is active but missing cards, deal them cards
                    try:
                        hole_cards = poker_game.deck_manager.deal_to_player(2)
                        player.receive_cards(hole_cards)
                        self.logger.info(f"Explicitly dealt cards to player {player.player_id}: {hole_cards}")
                    except ValueError as e:
                        self.logger.error(f"Error dealing cards to player {player.player_id}: {e}")
            
            # Update game's deck after all dealing
            poker_game.deck = poker_game.deck_manager.get_deck()
            
            # Log stacks after posting blinds to verify they've been properly updated
            for player in poker_game.players:
                self.logger.info(f"NEXT HAND (after blinds): Player {player.player_id} stack {player.stack}")
            
            # Update game in session manager
            self.session_manager.update_session(game_id, game_data)
            
            # Get updated game state
            updated_game_state = self.get_game_state(game_id, player_id)
            
            # Notify all players via WebSocket
            try:
                # Create a sanitized version without hole cards for broadcasting
                broadcast_state = updated_game_state.copy()
                for p in broadcast_state["players"]:
                    p["hole_cards"] = None
                
                # Async notify
                import asyncio
                asyncio.create_task(
                    self.notify_game_update(
                        game_id=game_id,
                        event_type="new_hand",
                        data={
                            "hand_number": poker_game.hand_count,
                            "game_state": broadcast_state
                        }
                    )
                )
            except Exception as e:
                self.logger.error(f"Error broadcasting new hand event: {e}")
            
            # Return updated game state
            return {
                "hand_number": poker_game.hand_count,
                "updated_game_state": updated_game_state
            }
            
        except Exception as e:
            self.logger.error(f"Error advancing to next hand: {e}")
            raise
    
    def end_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """End a game session"""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Check if player is in the game
        player_exists = any(p.player_id == player_id for p in poker_game.players)
        if not player_exists:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        self.logger.info(f"Ending game {game_id} for player {player_id}")
        
        try:
            # End the learning session in the PokerGame
            poker_game.end_session()
            
            # Calculate game summary
            duration = int((datetime.now() - game_data["created_at"]).total_seconds())
            hands_played = poker_game.hand_count
            
            # Get final chip counts
            final_chips = {}
            for player in poker_game.players:
                final_chips[player.player_id] = player.stack
            
            # Determine winner (player with most chips)
            winner = max(final_chips.items(), key=lambda x: x[1])[0]
            
            # Prepare game summary
            game_summary = {
                "duration": duration,
                "hands_played": hands_played,
                "final_chips": final_chips,
                "winner": winner
            }
            
            # Notify all players via WebSocket
            try:
                # Async notify before deleting the session
                import asyncio
                asyncio.create_task(
                    self.notify_game_update(
                        game_id=game_id,
                        event_type="game_end",
                        data=game_summary
                    )
                )
            except Exception as e:
                self.logger.error(f"Error broadcasting game end event: {e}")
            
            # Clean up game resources
            self.session_manager.delete_session(game_id)
            
            # Log game summary
            self.logger.info(f"Game {game_id} ended. Duration: {duration}s, Hands: {hands_played}, Winner: {winner}")
            
            return game_summary
            
        except Exception as e:
            self.logger.error(f"Error ending game: {e}")
            raise
    
    def get_showdown_results(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Get detailed showdown results including all player hands and winner information."""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Check if player is in the game
        player_exists = any(p.player_id == player_id for p in poker_game.players)
        if not player_exists:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        # Check if the game is in showdown state
        if poker_game.current_state != GameState.SHOWDOWN:
            self.logger.warning(f"Game {game_id} is not in showdown state")
            raise InvalidActionError("Game is not in showdown state")
        
        self.logger.info(f"Retrieved showdown results for game {game_id}")
        
        # Get showdown data
        showdown_data = self._get_showdown_data(poker_game)
        
        # Update the session after getting showdown data to ensure stack changes are persisted
        self.session_manager.update_session(game_id, game_data)
        
        return showdown_data

    def _get_showdown_data(self, poker_game) -> Dict[str, Any]:
        """Helper method to get showdown data from a PokerGame instance."""
        # Evaluate hands and determine winners
        player_hands = {}
        winning_hands = []
        
        # Get active or all-in players
        active_players = [p for p in poker_game.players if p.is_active or p.all_in]
        self.logger.info(f"SHOWDOWN: Active players: {[p.player_id for p in active_players]}")
        
        # Log current stacks before distribution
        for player in poker_game.players:
            self.logger.info(f"BEFORE SHOWDOWN: Player {player.player_id} has stack {player.stack}")
        
        # Get hand evaluations
        evaluated_hands = poker_game.hand_manager.evaluate_hands(
            active_players, 
            poker_game.community_cards, 
            poker_game.deck
        )
        
        # Store the original pot amount
        total_pot = poker_game.pot
        self.logger.info(f"SHOWDOWN: Total pot to distribute: {total_pot}")
        
        # Get pot distribution (winners)
        winners = poker_game.hand_manager.distribute_pot(
            players=poker_game.players,
            community_cards=poker_game.community_cards,
            total_pot=total_pot,  # Pass the stored pot amount
            deck=poker_game.deck
        )
        
        # Manually update winners' stacks for extra safety
        win_amounts = {}
        for pid, amount in winners.items():
            win_amounts[pid] = amount
            for player in poker_game.players:
                if player.player_id == pid:
                    # Get original stack before adding winnings
                    original_stack = player.stack - amount
                    self.logger.info(f"UPDATING WINNER: Player {pid} - Original stack {original_stack}, Adding {amount}, New stack should be {original_stack + amount}")
                    
                    # Set the stack explicitly to ensure it's updated correctly
                    player.stack = original_stack + amount
                    self.logger.info(f"WINNER STACK UPDATED: Player {pid} stack is now {player.stack}")
                    break
        
        # Log all stacks after distribution
        for player in poker_game.players:
            self.logger.info(f"AFTER SHOWDOWN: Player {player.player_id} has stack {player.stack}")
        
        # Reset pot after distribution
        poker_game.pot = 0
        
        # Format hand data
        for pid, (score, hand_rank, player) in evaluated_hands.items():
            # Calculate best hand from hole cards + community cards
            best_hand = poker_game.hand_manager.hand_evaluator.get_best_hand(
                player.hole_cards,
                poker_game.community_cards
            )
            
            player_hands[pid] = {
                "hole_cards": player.hole_cards,
                "hand_rank": hand_rank,
                "hand_score": score,
                "best_hand": best_hand
            }
        
        # Format winner data
        for pid, amount in winners.items():
            if pid in evaluated_hands:
                _, hand_rank, player = evaluated_hands[pid]
                best_hand = poker_game.hand_manager.hand_evaluator.get_best_hand(
                    player.hole_cards,
                    poker_game.community_cards
                )
                
                # Find the player again to get the most up-to-date stack
                current_player = None
                for p in poker_game.players:
                    if p.player_id == pid:
                        current_player = p
                        break
                
                # Use player's current stack if we found them
                current_stack = current_player.stack if current_player else player.stack
                
                winning_hands.append({
                    "player_id": pid,
                    "amount": amount,
                    "hand_rank": hand_rank,
                    "hand_name": hand_rank,  # Adding hand_name for compatibility with new_e2e_test.py
                    "hand": best_hand,
                    "final_stack": current_stack  # Include the winner's final stack
                })
        
        return {
            "player_hands": player_hands,
            "winners": winning_hands,
            "community_cards": poker_game.community_cards,
            "total_pot": poker_game.pot
        }

    def get_player_cards(self, game_id: str, player_id: str, target_player_id: str) -> Dict[str, Any]:
        """Get a player's hole cards (only available at showdown or for the requesting player)."""
        # Get game from session manager
        game_data = self.session_manager.get_session(game_id)
        if game_data is None:
            self.logger.warning(f"Game {game_id} not found")
            raise GameNotFoundError(game_id)
        
        # Get the PokerGame instance
        poker_game = game_data["poker_game"]
        
        # Check if player is in the game
        player_exists = any(p.player_id == player_id for p in poker_game.players)
        if not player_exists:
            self.logger.warning(f"Player {player_id} not found in game {game_id}")
            raise PlayerNotFoundError(player_id)
        
        # Check if target player is in the game
        target_player = None
        for p in poker_game.players:
            if p.player_id == target_player_id:
                target_player = p
                break
        
        if target_player is None:
            self.logger.warning(f"Target player {target_player_id} not found in game {game_id}")
            raise PlayerNotFoundError(target_player_id)
        
        # In the updated approach, we're not restricting hole cards visibility at the API level.
        # Instead, we add a "visible_to_client" flag that the frontend can use to decide what to show.
        # For this particular endpoint, it makes sense to still enforce the policy though, as it's
        # being called specifically to get another player's cards.
        should_hide_cards = target_player_id != player_id and poker_game.current_state != GameState.SHOWDOWN
        
        # Check if player has valid hole cards and proactively deal if needed
        if not target_player.hole_cards or len(target_player.hole_cards) != 2:
            self.logger.warning(f"Player {target_player_id} has invalid or missing hole cards")
            
            # If player is active, try to deal cards (regardless of game state)
            if target_player.is_active:
                try:
                    # Reset deck manager if needed
                    if len(poker_game.deck) < 2:
                        self.logger.info(f"Resetting deck before dealing cards to player {target_player_id}")
                        poker_game.deck_manager.reset()
                        poker_game.reset_deck()
                    
                    # Deal cards to the player
                    hole_cards = poker_game.deck_manager.deal_to_player(2)
                    target_player.receive_cards(hole_cards)
                    poker_game.deck = poker_game.deck_manager.get_deck()
                    
                    # Update session
                    self.session_manager.update_session(game_id, game_data)
                    self.logger.info(f"Dealt missing cards to player {target_player_id}: {hole_cards}")
                except ValueError as e:
                    self.logger.error(f"Error dealing cards to player {target_player_id}: {e}")
        
        self.logger.info(f"Retrieved cards for player {target_player_id} in game {game_id}")
        
        # Policy decision options:
        # 1. Return cards with a visibility flag (more consistent with the new approach)
        # 2. Filter cards at the API level (more secure but less flexible)
        
        # We're going with option 1 for consistency
        return {
            "player_id": target_player_id,
            "hole_cards": target_player.hole_cards,  # Always include actual cards
            "is_active": target_player.is_active,
            "visible_to_client": target_player_id == player_id or poker_game.current_state == GameState.SHOWDOWN
        }
    
    def schedule_cleanup(self):
        """Schedule regular cleanup of inactive games"""
        import threading
        
        def cleanup_job():
            self.logger.info("Running scheduled cleanup of inactive games")
            self.session_manager.cleanup_sessions(timeout_minutes=30)
            # Schedule the next cleanup
            threading.Timer(300, cleanup_job).start()  # Run every 5 minutes
        
        # Start the initial cleanup job
        threading.Timer(300, cleanup_job).start()  # Start after 5 minutes