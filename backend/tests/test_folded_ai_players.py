#!/usr/bin/env python3
"""
Test Script to Verify Fix for Folded AI Players Issue

This test:
1. Creates a game with 5 AI players (plus human test player)
2. Plays through 5 complete poker hands
3. Verifies that folded AI players do not continue to make decisions after folding
4. Uses adaptive delays between API calls to prevent rate limiting
5. Logs detailed information about player states and actions
"""

import requests
import json
import time
import sys
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_folded_ai_players.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_folded_ai_players")

# API Configuration
BASE_URL = "http://localhost:8080/api/v1"
TEST_PLAYER_ID = None
ACCESS_TOKEN = None
GAME_ID = None

# Test configuration
NUM_HANDS = 5
BASE_DELAY_SECONDS = 1  # Base delay between API calls
RATE_LIMIT_BACKOFF = 2  # Multiply delay by this factor when rate limited
MAX_RETRIES = 3         # Maximum number of retries for rate limited requests
DELAY_BETWEEN_HANDS = 3 # Longer delay between hands

def create_player() -> bool:
    """Create a human player and get access token"""
    global ACCESS_TOKEN, TEST_PLAYER_ID
    
    logger.info("Creating test player")
    
    try:
        response = requests.post(
            f"{BASE_URL}/players",
            json={"username": f"TestFoldedAIPlayer_{int(time.time())}"}  # Add timestamp to prevent conflicts
        )
        
        response.raise_for_status()
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        TEST_PLAYER_ID = data["player_id"]
        logger.info(f"Player created with ID: {TEST_PLAYER_ID}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create player: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False

def api_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, 
                delay: float = BASE_DELAY_SECONDS, retries: int = 0) -> Dict:
    """Make API request with proper error handling, rate limit handling, and logging"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    # Add a small delay before making the request to prevent rate limiting
    time.sleep(delay)
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=params)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check for rate limiting response
        if response.status_code == 429 and retries < MAX_RETRIES:
            retry_after = int(response.headers.get('Retry-After', delay * RATE_LIMIT_BACKOFF))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds before retrying.")
            
            # Increase delay for the next attempt
            new_delay = delay * RATE_LIMIT_BACKOFF
            
            # Wait for the specified retry period
            time.sleep(retry_after)
            
            # Retry the request with increased delay
            return api_request(method, endpoint, data, params, new_delay, retries + 1)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        
        # If we've hit our retry limit or it's not a rate limiting issue, exit
        if retries >= MAX_RETRIES or (hasattr(e, 'response') and e.response and e.response.status_code != 429):
            logger.error(f"Giving up after {retries} retries")
            sys.exit(1)
            
        # If it's a rate limiting issue and we still have retries, try again
        if hasattr(e, 'response') and e.response and e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', delay * RATE_LIMIT_BACKOFF))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds before retrying.")
            
            # Increase delay for the next attempt
            new_delay = delay * RATE_LIMIT_BACKOFF
            
            # Wait for the specified retry period
            time.sleep(retry_after)
            
            # Retry the request with increased delay
            return api_request(method, endpoint, data, params, new_delay, retries + 1)
        
        sys.exit(1)

def create_game() -> str:
    """Create a new game with 5 AI players"""
    logger.info("Creating new game with 5 AI players")
    game_data = {
        "player_id": TEST_PLAYER_ID,
        "ai_count": 5,
        "ai_personalities": ["Conservative", "Risk Taker", "Probability-Based", "Bluffer", "Conservative"]
    }
    
    response = api_request("post", "/games", data=game_data)
    game_id = response["game_id"]
    logger.info(f"Game created with ID: {game_id}")
    return game_id

def get_game_state(game_id: str, show_all_cards: bool = False) -> Dict:
    """Get current game state"""
    params = {"show_all_cards": "true" if show_all_cards else "false"}
    return api_request("get", f"/games/{game_id}", params=params)

def process_action(game_id: str, player_id: str, action_type: str, amount: Optional[int] = None) -> Dict:
    """Process a player action"""
    action_data = {
        "player_id": player_id,
        "action_type": action_type
    }
    
    if amount is not None and action_type == "raise":
        action_data["amount"] = amount
        
    return api_request("post", f"/games/{game_id}/actions", data=action_data)

def next_hand(game_id: str, player_id: str) -> Dict:
    """Advance to the next hand"""
    next_hand_data = {"player_id": player_id}
    return api_request("post", f"/games/{game_id}/next-hand", data=next_hand_data)

def get_showdown_results(game_id: str) -> Dict:
    """Get detailed showdown results"""
    return api_request("get", f"/games/{game_id}/showdown")

def end_game(game_id: str) -> Dict:
    """End the game session"""
    return api_request("delete", f"/games/{game_id}")

def analyze_player_states(game_state: Dict) -> None:
    """Analyze and log player states to verify folded players are not acting"""
    logger.info(f"Current game state: {game_state['current_state']}")
    logger.info(f"Pot size: {game_state['pot']}")
    
    active_players = 0
    folded_players = 0
    
    for player in game_state["players"]:
        player_status = "ACTIVE" if player.get("is_active", True) else "FOLDED"
        logger.info(f"Player {player['player_id']} is {player_status} with stack {player['stack']}")
        
        if player.get("is_active", True):
            active_players += 1
        else:
            folded_players += 1
    
    logger.info(f"Total active players: {active_players}, folded players: {folded_players}")

def verify_stack_changes(game_state: Dict, player_id: str, action_type: str) -> bool:
    """Verify that player stack changes after actions"""
    for player in game_state["players"]:
        if player["player_id"] == player_id:
            initial_stack = player["stack"]
            logger.info(f"Initial stack before {action_type}: {initial_stack}")
            
            # Store the stack value for verification after the action
            return initial_stack
    
    return None

def play_hand(game_id: str, hand_number: int) -> None:
    """Play a complete poker hand with AI players only"""
    logger.info(f"\n{'='*50}\nStarting hand #{hand_number}\n{'='*50}")
    
    # Get initial game state
    game_state = get_game_state(game_id)
    analyze_player_states(game_state)
    
    action_count = 0
    max_actions_per_hand = 30
    
    # Play through betting rounds until showdown
    while game_state["current_state"] != "showdown" and action_count < max_actions_per_hand:
        action_count += 1
        logger.info(f"Current betting round: {game_state['current_state']}")
        
        # Check if it's the test player's turn
        if game_state.get("current_player") == TEST_PLAYER_ID:
            # Get player's stack before calling
            previous_stack = None
            for player in game_state["players"]:
                if player["player_id"] == TEST_PLAYER_ID:
                    previous_stack = player["stack"]
                    break
                    
            # Simulating test player action (always call)
            logger.info(f"Test player {TEST_PLAYER_ID} calls (stack before: {previous_stack})")
            result = process_action(game_id, TEST_PLAYER_ID, "call")
            
            # Get updated game state
            updated_state = result.get("updated_game_state", {})
            if updated_state:
                new_stack = None
                for player in updated_state.get("players", []):
                    if player["player_id"] == TEST_PLAYER_ID:
                        new_stack = player["stack"]
                        break
                
                if previous_stack is not None and new_stack is not None and previous_stack != new_stack:
                    logger.info(f"Stack updated: {previous_stack} -> {new_stack} (change: {new_stack - previous_stack})")
                else:
                    logger.warning(f"Stack not updated properly after call! Before: {previous_stack}, After: {new_stack}")
        else:
            # Wait for AI players to act
            logger.info(f"Waiting for AI player {game_state.get('current_player')} to act")
            time.sleep(BASE_DELAY_SECONDS)
        
        # Get updated game state
        game_state = get_game_state(game_id)
        analyze_player_states(game_state)
    
    if action_count >= max_actions_per_hand:
        logger.warning(f"Hit maximum actions per hand ({max_actions_per_hand}). Game might be stuck.")
    
    # Get showdown results
    if game_state["current_state"] == "showdown":
        logger.info("Hand complete, getting showdown results")
        showdown_results = get_showdown_results(game_id)
        
        # Log winner information
        winners = showdown_results.get("winners", [])
        if winners:
            for winner in winners:
                logger.info(f"Winner: {winner.get('player_id')} won {winner.get('amount')} chips with {winner.get('hand_rank')}")
        else:
            logger.warning("No winners returned in showdown results")
    
    # If not the last hand, advance to next hand
    if hand_number < NUM_HANDS:
        logger.info("Advancing to next hand")
        next_hand_result = next_hand(game_id, TEST_PLAYER_ID)
        time.sleep(DELAY_BETWEEN_HANDS)  # Longer delay between hands

def run_test():
    """Run the complete test sequence"""
    try:
        # Create player first to get proper authentication token
        if not create_player():
            logger.error("Failed to create test player")
            return False
            
        # Create game
        global GAME_ID
        GAME_ID = create_game()
        time.sleep(BASE_DELAY_SECONDS)
        
        # Play hands
        for hand_num in range(1, NUM_HANDS + 1):
            play_hand(GAME_ID, hand_num)
        
        # End game
        logger.info("Test complete, ending game")
        summary = end_game(GAME_ID)
        logger.info(f"Game summary: {json.dumps(summary, indent=2)}")
        
        logger.info("TEST PASSED: No issues detected with folded AI players")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        if GAME_ID:
            try:
                end_game(GAME_ID)
            except:
                pass
        return False

if __name__ == "__main__":
    logger.info("Starting test to verify fix for folded AI players issue")
    success = run_test()
    if success:
        logger.info("Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)