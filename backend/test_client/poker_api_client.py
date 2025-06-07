"""
Dedicated API Test Client for Poker Learning App
Follows proper game flow and respects rate limits.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GameState(Enum):
    """Mirror of the game state enum for client tracking."""
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


@dataclass
class PlayerInfo:
    """Information about a player."""
    player_id: str
    username: str
    is_human: bool = False


class PokerAPIClient:
    """
    State-aware API client for testing poker game flows.
    Respects rate limits and follows proper game progression.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", delay: float = 0.5):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the poker API
            delay: Delay between API calls to prevent rate limiting
        """
        self.base_url = base_url.rstrip('/')
        self.delay = delay
        self.session = requests.Session()
        
        # Add authentication header for testing
        self.session.headers.update({
            'X-API-Key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZGYwODc5Yy1kODNiLTQ2MzYtYmI0Ni0zOWY1MjM5NjRhZmQiLCJleHAiOjE3NTExNDIwMDN9.XUTVy8yQKDDBpXXpHNykZfT_azbPIzDzYKAiAC-4rDA'
        })
        
        # Game state tracking
        self.game_id: Optional[str] = None
        self.current_state: Optional[GameState] = None
        self.players: List[PlayerInfo] = []
        self.human_player_id: Optional[str] = None
        
        # Request tracking for debugging
        self.request_count = 0
        self.errors: List[Dict[str, Any]] = []
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an API request with error handling and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON data
            
        Raises:
            Exception: If request fails after retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self.request_count += 1
        
        logger.debug(f"REQUEST {self.request_count}: {method} {url}")
        
        # Add delay to prevent rate limiting
        if self.request_count > 1:
            time.sleep(self.delay)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 429:  # Rate limited
                logger.warning(f"Rate limited on request {self.request_count}, waiting longer...")
                time.sleep(self.delay * 3)
                response = self.session.request(method, url, **kwargs)
            
            if not response.ok:
                error_info = {
                    "request_count": self.request_count,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "response_text": response.text
                }
                self.errors.append(error_info)
                logger.error(f"Request failed: {error_info}")
                response.raise_for_status()
            
            data = response.json()
            logger.debug(f"RESPONSE {self.request_count}: Success")
            return data
            
        except Exception as e:
            logger.error(f"Request {self.request_count} failed: {e}")
            raise
    
    def create_player(self, username: str, is_human: bool = False) -> str:
        """
        Create a new player (simplified for testing - just return a test ID).
        
        Args:
            username: Player's username
            is_human: Whether this is a human player
            
        Returns:
            Player ID
        """
        # For this implementation, we'll use the authenticated player from token
        player_id = "4df0879c-d83b-4636-bb46-39f523964afd"
        
        player_info = PlayerInfo(player_id=player_id, username=username, is_human=is_human)
        self.players.append(player_info)
        
        if is_human:
            self.human_player_id = player_id
        
        logger.info(f"Using test player: {username} ({player_id})")
        return player_id
    
    def create_game(self, creator_player_id: str, ai_count: int = 3) -> str:
        """
        Create a new game.
        
        Args:
            creator_player_id: ID of the player creating the game
            ai_count: Number of AI players to add
            
        Returns:
            Game ID
        """
        game_data = {
            "player_id": creator_player_id,
            "ai_count": ai_count,
            "ai_personalities": ["Conservative", "Risk Taker", "Probability-Based"][:ai_count]
        }
        
        response = self._make_request("POST", "/api/v1/games", json=game_data)
        
        self.game_id = response["game_id"]
        self.current_state = GameState.PRE_FLOP
        
        logger.info(f"Created game: {self.game_id}")
        return self.game_id
    
    def join_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Join an existing game.
        
        Args:
            game_id: Game to join
            player_id: Player joining the game
            
        Returns:
            Response data
        """
        response = self._make_request(
            "POST", 
            f"/api/v1/games/{game_id}/join", 
            params={"player_id": player_id}
        )
        
        logger.info(f"Player {player_id} joined game {game_id}")
        return response
    
    def start_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Start a game.
        
        Args:
            game_id: Game to start
            player_id: Player starting the game
            
        Returns:
            Response data
        """
        response = self._make_request(
            "POST", 
            f"/api/v1/games/{game_id}/start", 
            params={"player_id": player_id}
        )
        
        logger.info(f"Started game {game_id}")
        return response
    
    def get_game_state(self, game_id: str, player_id: str, 
                      show_all_cards: bool = False) -> Dict[str, Any]:
        """
        Get current game state.
        
        Args:
            game_id: Game ID
            player_id: Player requesting state
            show_all_cards: Whether to show all cards (for showdown)
            
        Returns:
            Game state data
        """
        params = {}
        if show_all_cards:
            params["show_all_cards"] = "true"
        
        response = self._make_request(
            "GET", 
            f"/api/v1/games/{game_id}", 
            params=params
        )
        
        # Update tracked state
        if "current_state" in response:
            try:
                self.current_state = GameState(response["current_state"])
            except ValueError:
                logger.warning(f"Unknown game state: {response['current_state']}")
        
        return response
    
    def place_bet(self, game_id: str, player_id: str, action: str, 
                  amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Place a bet or take an action.
        
        Args:
            game_id: Game ID
            player_id: Player taking action
            action: Action to take (call, raise, fold)
            amount: Bet amount (for raise)
            
        Returns:
            Response data
        """
        action_data = {"action": action}
        if amount is not None:
            action_data["amount"] = amount
        
        response = self._make_request(
            "POST", 
            f"/api/v1/games/{game_id}/action", 
            json=action_data,
            params={"player_id": player_id}
        )
        
        logger.info(f"Player {player_id} action: {action}" + 
                   (f" ({amount})" if amount else ""))
        return response
    
    def next_hand(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Advance to the next hand.
        
        Args:
            game_id: Game ID
            player_id: Player requesting next hand
            
        Returns:
            Response data
        """
        response = self._make_request(
            "POST", 
            f"/api/v1/games/{game_id}/next-hand", 
            json={"player_id": player_id}
        )
        
        # Reset state tracking for new hand
        self.current_state = GameState.PRE_FLOP
        
        logger.info(f"Advanced to next hand in game {game_id}")
        return response
    
    def get_showdown_results(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Get showdown results.
        
        Args:
            game_id: Game ID
            player_id: Player requesting results
            
        Returns:
            Showdown results
        """
        response = self._make_request(
            "GET", 
            f"/api/v1/games/{game_id}/showdown", 
            params={"player_id": player_id}
        )
        
        logger.info(f"Retrieved showdown results for game {game_id}")
        return response
    
    def play_complete_hand(self, game_id: str) -> Dict[str, Any]:
        """
        Play a complete hand from pre-flop to showdown.
        
        Args:
            game_id: Game ID
            
        Returns:
            Final game state
        """
        if not self.human_player_id:
            raise ValueError("No human player found to play hand")
        
        logger.info(f"Starting complete hand for game {game_id}")
        
        # Get initial state
        state = self.get_game_state(game_id, self.human_player_id)
        
        # Play through betting rounds
        betting_rounds = 0
        max_betting_rounds = 10  # Safety limit
        
        while (state.get("current_state") != "showdown" and 
               betting_rounds < max_betting_rounds):
            
            # Check if it's the human player's turn
            if (state.get("next_player") == self.human_player_id and 
                state.get("current_state") != "showdown"):
                
                # Make a simple decision (call or fold based on stack)
                current_bet = state.get("current_bet", 0)
                player_stack = None
                
                for player in state.get("players", []):
                    if player["player_id"] == self.human_player_id:
                        player_stack = player["stack"]
                        break
                
                if player_stack and current_bet <= player_stack // 4:
                    # Call if bet is reasonable
                    self.place_bet(game_id, self.human_player_id, "call")
                else:
                    # Fold if bet is too high
                    self.place_bet(game_id, self.human_player_id, "fold")
            
            # Get updated state
            state = self.get_game_state(game_id, self.human_player_id)
            betting_rounds += 1
            
            # Small delay between state checks
            time.sleep(self.delay * 0.5)
        
        # If we reached showdown, get results
        if state.get("current_state") == "showdown":
            showdown_results = self.get_showdown_results(game_id, self.human_player_id)
            logger.info(f"Hand completed, reached showdown")
            return showdown_results
        
        logger.warning(f"Hand completed without reaching showdown (betting rounds: {betting_rounds})")
        return state
    
    def run_complete_game_test(self, num_hands: int = 3) -> Dict[str, Any]:
        """
        Run a complete game test with multiple hands.
        
        Args:
            num_hands: Number of hands to play
            
        Returns:
            Test results summary
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting complete game test with {num_hands} hands")
            
            # Create human player
            human_player_id = self.create_player("TestHuman", is_human=True)
            
            # Create game with AI players (games start automatically)
            game_id = self.create_game(human_player_id, ai_count=3)
            
            # Play multiple hands
            hand_results = []
            for hand_num in range(num_hands):
                logger.info(f"Playing hand {hand_num + 1}/{num_hands}")
                
                try:
                    result = self.play_complete_hand(game_id)
                    hand_results.append({
                        "hand_number": hand_num + 1,
                        "success": True,
                        "result": result
                    })
                    
                    # Advance to next hand if not the last one
                    if hand_num < num_hands - 1:
                        self.next_hand(game_id, human_player_id)
                        
                except Exception as e:
                    logger.error(f"Error in hand {hand_num + 1}: {e}")
                    hand_results.append({
                        "hand_number": hand_num + 1,
                        "success": False,
                        "error": str(e)
                    })
            
            # Get final game state
            final_state = self.get_game_state(game_id, human_player_id)
            
            test_results = {
                "success": True,
                "game_id": game_id,
                "hands_played": len(hand_results),
                "successful_hands": sum(1 for h in hand_results if h["success"]),
                "hand_results": hand_results,
                "final_state": final_state,
                "total_requests": self.request_count,
                "total_errors": len(self.errors),
                "duration_seconds": time.time() - start_time
            }
            
            logger.info(f"Game test completed: {test_results['successful_hands']}/{test_results['hands_played']} hands successful")
            return test_results
            
        except Exception as e:
            logger.error(f"Game test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_requests": self.request_count,
                "total_errors": len(self.errors),
                "duration_seconds": time.time() - start_time
            }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get a summary of test execution."""
        return {
            "total_requests": self.request_count,
            "total_errors": len(self.errors),
            "error_details": self.errors[-5:] if self.errors else [],  # Last 5 errors
            "players_created": len(self.players),
            "current_game_id": self.game_id,
            "current_state": self.current_state.value if self.current_state else None
        }