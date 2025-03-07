# backend/services/game_service.py
from typing import Dict, List, Optional, Any
import uuid
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

# This would be your actual game engine import
# from game.poker_game import PokerGame

# For now, we'll mock the interactions
class GameService:
    # Mock storage
    _games = {}
    
    def create_game(self, player_id: str, ai_count: int, ai_personalities: List[str]) -> Dict[str, Any]:
        """Create a new game session"""
        # In a real implementation, this would initialize a PokerGame instance
        game_id = str(uuid.uuid4())
        
        # Mock game creation
        players = [
            {
                "player_id": player_id,
                "player_type": "human",
                "personality": None,
                "position": 0,
                "stack": 1000
            }
        ]
        
        # Add AI players
        for i in range(ai_count):
            players.append({
                "player_id": f"ai_{i}",
                "player_type": "ai",
                "personality": ai_personalities[i % len(ai_personalities)],
                "position": i + 1,
                "stack": 1000
            })
        
        # Store game
        self._games[game_id] = {
            "game_id": game_id,
            "players": players,
            "dealer_position": 0,
            "small_blind": 5,
            "big_blind": 10,
            "current_state": "pre_flop",
            "community_cards": [],
            "pot": 0,
            "current_bet": 0,
            "hand_number": 1,
            "created_at": datetime.now(),
            "last_active": datetime.now()
        }
        
        return {
            "game_id": game_id,
            "players": players,
            "dealer_position": 0,
            "small_blind": 5,
            "big_blind": 10
        }
    
    def get_game_state(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Get current game state"""
        if game_id not in self._games:
            raise GameNotFoundError(game_id)
        
        # Update last activity time
        self._games[game_id]["last_active"] = datetime.now()
        
        # Get game state
        game = self._games[game_id]
        
        # Check if player is in the game
        player_exists = any(p["player_id"] == player_id for p in game["players"])
        if not player_exists:
            raise PlayerNotFoundError(player_id)
        
        # Filter sensitive data (only show current player's hole cards)
        players = []
        for player in game["players"]:
            player_copy = player.copy()
            if player_copy["player_id"] != player_id:
                player_copy["hole_cards"] = None
            players.append(player_copy)
        
        # Determine available actions for current player
        available_actions = ["fold", "call", "raise"] if game["current_state"] != "showdown" else []
        
        return {
            "game_id": game["game_id"],
            "current_state": game["current_state"],
            "community_cards": game["community_cards"],
            "pot": game["pot"],
            "current_bet": game["current_bet"],
            "players": players,
            "dealer_position": game["dealer_position"],
            "current_player": player_id,  # In real impl, this would be the actual current player
            "available_actions": available_actions,
            "min_raise": game["big_blind"],
            "hand_number": game["hand_number"]
        }
    
    def process_action(self, game_id: str, player_id: str, action_type: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Process player action (fold, call, raise)"""
        if game_id not in self._games:
            raise GameNotFoundError(game_id)
        
        # Update last activity time
        self._games[game_id]["last_active"] = datetime.now()
        
        # Get game
        game = self._games[game_id]
        
        # Check if player is in the game
        player = None
        for p in game["players"]:
            if p["player_id"] == player_id:
                player = p
                break
        
        if player is None:
            raise PlayerNotFoundError(player_id)
        
        # Check if it's player's turn
        # In a real implementation, this would check the actual current player
        # For now, we'll assume it's the player's turn
        
        # Validate action type
        if action_type not in ["fold", "call", "raise"]:
            raise InvalidActionError(f"Invalid action type: {action_type}")
        
        # Process action
        if action_type == "fold":
            # Player folds
            player["is_active"] = False
        elif action_type == "call":
            # Player calls
            call_amount = game["current_bet"]
            
            # Check if player has enough chips
            if player["stack"] < call_amount:
                raise InsufficientFundsError(player_id, call_amount, player["stack"])
            
            # Update player stack and pot
            player["stack"] -= call_amount
            game["pot"] += call_amount
            player["current_bet"] = call_amount
        elif action_type == "raise":
            # Validate raise amount
            if amount is None:
                raise InvalidAmountError("Amount required for raise action")
            
            # Check minimum raise
            if amount < game["big_blind"] * 2:
                raise InvalidAmountError(f"Raise amount must be at least {game['big_blind'] * 2}")
            
            # Check if player has enough chips
            if player["stack"] < amount:
                raise InsufficientFundsError(player_id, amount, player["stack"])
            
            # Update player stack, current bet, and pot
            player["stack"] -= amount
            game["current_bet"] = amount
            game["pot"] += amount
            player["current_bet"] = amount
        
        # Move game to next state for demo purposes
        if game["current_state"] == "pre_flop":
            game["current_state"] = "flop"
            game["community_cards"] = ["Ah", "Kd", "Qc"]
        elif game["current_state"] == "flop":
            game["current_state"] = "turn"
            game["community_cards"].append("Jh")
        elif game["current_state"] == "turn":
            game["current_state"] = "river"
            game["community_cards"].append("Ts")
        elif game["current_state"] == "river":
            game["current_state"] = "showdown"
        
        # Return updated game state
        return {
            "action_result": "success",
            "updated_game_state": self.get_game_state(game_id, player_id),
            "next_player": "ai_0",  # In real impl, this would be the next player
            "pot_update": game["pot"]
        }
    
    def next_hand(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Advance to the next hand"""
        if game_id not in self._games:
            raise GameNotFoundError(game_id)
        
        # Update last activity time
        self._games[game_id]["last_active"] = datetime.now()
        
        # Get game
        game = self._games[game_id]
        
        # Check if player is in the game
        player_exists = any(p["player_id"] == player_id for p in game["players"])
        if not player_exists:
            raise PlayerNotFoundError(player_id)
        
        # Check if game is in showdown state
        if game["current_state"] != "showdown":
            raise InvalidActionError("Cannot advance to next hand before showdown")
        
        # Increment hand number
        game["hand_number"] += 1
        
        # Reset game state for new hand
        game["current_state"] = "pre_flop"
        game["community_cards"] = []
        game["pot"] = 0
        game["current_bet"] = 0
        
        # Reset player states
        for player in game["players"]:
            player["is_active"] = True
            player["current_bet"] = 0
        
        # Move dealer button
        game["dealer_position"] = (game["dealer_position"] + 1) % len(game["players"])
        
        # Return updated game state
        return {
            "hand_number": game["hand_number"],
            "updated_game_state": self.get_game_state(game_id, player_id)
        }
    
    def end_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """End a game session"""
        if game_id not in self._games:
            raise GameNotFoundError(game_id)
        
        # Get game
        game = self._games[game_id]
        
        # Check if player is in the game
        player_exists = any(p["player_id"] == player_id for p in game["players"])
        if not player_exists:
            raise PlayerNotFoundError(player_id)
        
        # Calculate game summary
        duration = int((datetime.now() - game["created_at"]).total_seconds())
        hands_played = game["hand_number"]
        
        # Get final chip counts
        final_chips = {}
        for player in game["players"]:
            final_chips[player["player_id"]] = player["stack"]
        
        # Determine winner (player with most chips)
        winner = max(final_chips.items(), key=lambda x: x[1])[0]
        
        # Clean up game resources
        del self._games[game_id]
        
        return {
            "duration": duration,
            "hands_played": hands_played,
            "final_chips": final_chips,
            "winner": winner
        }
    
    def cleanup_inactive_games(self, timeout_minutes: int = 30):
        """Clean up inactive game sessions"""
        now = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        for game_id in list(self._games.keys()):
            if now - self._games[game_id]["last_active"] > timeout:
                del self._games[game_id]