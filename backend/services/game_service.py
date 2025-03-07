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
                    "stack": player.stack
                })
            
            # Return game creation response
            return {
                "game_id": game_id,
                "players": players_data,
                "dealer_position": poker_game.dealer_index,
                "small_blind": poker_game.small_blind,
                "big_blind": poker_game.big_blind
            }
            
        except Exception as e:
            self.logger.error(f"Error creating game: {e}")
            raise
    
    def get_game_state(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Get current game state from the PokerGame instance"""
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
        
        # Format players data, filtering hole cards as needed
        players_data = []
        for player in player_objects:
            # Only include hole cards for the requesting player
            hole_cards = player.hole_cards if player.player_id == player_id else None
            
            player_type = "human" if isinstance(player, HumanPlayer) else "ai"
            
            players_data.append({
                "player_id": player.player_id,
                "player_type": player_type,
                "personality": getattr(player, "personality", None) if player_type == "ai" else None,
                "stack": player.stack,
                "stack_formatted": format_money(player.stack),
                "current_bet": player.current_bet,
                "current_bet_formatted": format_money(player.current_bet),
                "is_active": player.is_active,
                "is_all_in": player.all_in,
                "hole_cards": hole_cards,
                "hole_cards_formatted": format_cards(hole_cards) if hole_cards else None,
                "position": poker_game.players.index(player)
            })
        
        # Determine available actions for current player
        available_actions = []
        if poker_game.current_state != GameState.SHOWDOWN:
            available_actions = ["fold", "call", "raise"]
        
        # Convert enum to string for the API
        current_state = poker_game.current_state.value if isinstance(poker_game.current_state, GameState) else str(poker_game.current_state)
        
        return {
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
            "current_player": player_id,  # We'll use the requesting player as current for now
            "available_actions": available_actions,
            "min_raise": poker_game.big_blind,
            "min_raise_formatted": format_money(poker_game.big_blind),
            "hand_number": poker_game.hand_count
        }
    
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
                
                # Check minimum raise (usually 2x big blind)
                min_raise = poker_game.big_blind * 2
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
            
            # Check if all players have acted (simplified logic)
            all_acted = True
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
                "pot_update": poker_game.pot
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
                # For simplicity, raise by 2x big blind above current bet
                raise_amount = poker_game.current_bet + (poker_game.big_blind * 2)
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
        
        try:
            # In the actual PokerGame implementation, this would be handled by calling:
            # poker_game.play_hand()
            
            # For our API integration, we need to do these steps:
            # 1. Reset player states
            for player in poker_game.players:
                player.reset_hand_state()
                
            # 2. Reset game state for new hand
            poker_game.current_state = GameState.PRE_FLOP
            poker_game.community_cards = []
            poker_game.pot = 0
            poker_game.current_bet = 0
            
            # 3. Increment hand count
            poker_game.hand_count += 1
            
            # 4. Deal new cards and post blinds
            poker_game.reset_deck()
            poker_game.post_blinds()  # This also deals hole cards
            
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