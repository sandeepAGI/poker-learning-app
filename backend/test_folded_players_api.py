#!/usr/bin/env python3
"""
API Test to Verify Fix for Folded AI Players Issue

This test:
1. Connects to the running API server
2. Creates a game with AI players
3. Plays multiple rounds with deliberate folding
4. Verifies that folded players do not continue to act after folding
"""

import requests
import json
import time
import sys
import logging
import jwt
import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_folded_players_api.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_folded_players_api")

# API Configuration
BASE_URL = "http://localhost:8080/api/v1"
TEST_PLAYER_ID = "test_player_1"
GAME_ID = None
NUM_HANDS = 3
DELAY_SECONDS = 2.0  # Delay between API calls

# Auth configuration (must match config.py values)
SECRET_KEY = "development-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_auth_token() -> str:
    """Create a proper JWT token for authentication"""
    payload = {
        "sub": TEST_PLAYER_ID,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def api_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
    """Make API request with proper error handling and logging"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-API-Key": create_auth_token()}
    
    try:
        response = None
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=params)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if response:
            logger.error(f"Response content: {response.text}")
        raise

def create_game() -> str:
    """Create a new game with AI players"""
    logger.info("Creating new game with 4 AI players")
    game_data = {
        "player_id": TEST_PLAYER_ID,
        "ai_count": 4,
        "ai_personalities": ["Conservative", "Risk Taker", "Probability-Based", "Bluffer"]
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
        "action_type": action_type,
        "amount": amount
    }
    return api_request("post", f"/games/{game_id}/actions", data=action_data)

def next_hand(game_id: str, player_id: str) -> Dict:
    """Advance to the next hand"""
    next_hand_data = {"player_id": player_id}
    return api_request("post", f"/games/{game_id}/next-hand", data=next_hand_data)

def end_game(game_id: str) -> Dict:
    """End the game session"""
    return api_request("delete", f"/games/{game_id}")

def count_active_players(game_state: Dict) -> int:
    """Count the number of active players in the game state"""
    return sum(1 for p in game_state["players"] if p["is_active"])

def check_fold_behavior(game_id: str) -> bool:
    """
    Check if folded players remain folded throughout a hand
    Returns True if behavior is correct, False otherwise
    """
    # First, let's get the current game state
    game_state = get_game_state(game_id)
    logger.info(f"Game state: {game_state['current_state']}, active players: {count_active_players(game_state)}")
    
    # Keep track of which players have folded
    folded_players = set()
    
    # Let's play through the hand, having the human player fold
    action_result = process_action(game_id, TEST_PLAYER_ID, "fold")
    logger.info(f"Player {TEST_PLAYER_ID} folded")
    time.sleep(DELAY_SECONDS)
    
    # Get updated game state
    updated_state = get_game_state(game_id)
    
    # Verify the human player is now marked as inactive
    human_player = next((p for p in updated_state["players"] if p["player_id"] == TEST_PLAYER_ID), None)
    if human_player and human_player["is_active"]:
        logger.error(f"Player {TEST_PLAYER_ID} folded but is still marked as active")
        return False
    
    # Add the human player to our tracked folded players
    folded_players.add(TEST_PLAYER_ID)
    
    # Keep track of which AI players fold
    initial_active_count = count_active_players(updated_state)
    logger.info(f"Initial active players after human fold: {initial_active_count}")
    
    # Now let's observe subsequent betting rounds
    prev_state = updated_state["current_state"]
    
    # Keep playing until showdown or all but one have folded
    while updated_state["current_state"] != "showdown" and count_active_players(updated_state) > 1:
        # Track which players have folded in this round
        newly_folded = []
        for player in updated_state["players"]:
            if player["player_id"] not in folded_players and not player["is_active"]:
                folded_players.add(player["player_id"])
                newly_folded.append(player["player_id"])
        
        if newly_folded:
            logger.info(f"Players folded in this round: {newly_folded}")
        
        # If we're in a new betting round, check that previously folded players stayed folded
        if updated_state["current_state"] != prev_state:
            logger.info(f"Advanced to new state: {updated_state['current_state']}")
            prev_state = updated_state["current_state"]
            
            # Verify all previously folded players are still marked inactive
            for player in updated_state["players"]:
                if player["player_id"] in folded_players and player["is_active"]:
                    logger.error(f"Player {player['player_id']} had folded but is now active again")
                    return False
        
        # Continue playing by checking the state (human already folded)
        time.sleep(DELAY_SECONDS)
        updated_state = get_game_state(game_id)
    
    # Check if we reached showdown
    final_active_count = count_active_players(updated_state)
    logger.info(f"Final state: {updated_state['current_state']}, active players: {final_active_count}")
    
    # Verify one last time that all folded players remained folded
    for player_id in folded_players:
        player = next((p for p in updated_state["players"] if p["player_id"] == player_id), None)
        if player and player["is_active"]:
            logger.error(f"Player {player_id} had folded but was somehow reactivated in the same hand")
            return False
    
    logger.info("All folded players properly remained inactive throughout the hand")
    return True

def verify_reactivation_after_hand(game_id: str) -> bool:
    """
    Verify that folded players are properly reactivated for the next hand
    Returns True if behavior is correct, False otherwise
    """
    # First, get current game state (which should be at showdown)
    game_state = get_game_state(game_id, show_all_cards=True)
    
    # Note which players are currently inactive due to folding
    folded_players = [p["player_id"] for p in game_state["players"] if not p["is_active"]]
    logger.info(f"Folded players at end of hand: {folded_players}")
    
    # Move to the next hand
    next_hand_result = next_hand(game_id, TEST_PLAYER_ID)
    time.sleep(DELAY_SECONDS)
    
    # Get new game state
    new_game_state = get_game_state(game_id)
    
    # Check that all players with sufficient chips are now active
    reactivated_correctly = True
    for player in new_game_state["players"]:
        # Players with sufficient chips should be active
        if player["stack"] >= 5 and not player["is_active"]:
            logger.error(f"Player {player['player_id']} has sufficient chips but was not reactivated")
            reactivated_correctly = False
    
    if reactivated_correctly:
        logger.info("All players with sufficient chips were properly reactivated for the new hand")
    
    return reactivated_correctly

def run_test():
    """Run the complete test sequence"""
    try:
        # Create game
        global GAME_ID
        GAME_ID = create_game()
        time.sleep(DELAY_SECONDS)
        
        all_tests_passed = True
        
        # Run test for multiple hands
        for hand_num in range(1, NUM_HANDS + 1):
            logger.info(f"\n{'='*50}\nTesting hand #{hand_num}\n{'='*50}")
            
            # Test folding behavior for this hand
            fold_behavior_ok = check_fold_behavior(GAME_ID)
            if not fold_behavior_ok:
                logger.error(f"Fold behavior test failed in hand {hand_num}")
                all_tests_passed = False
            
            # Test reactivation behavior for next hand
            reactivation_ok = verify_reactivation_after_hand(GAME_ID)
            if not reactivation_ok:
                logger.error(f"Reactivation test failed after hand {hand_num}")
                all_tests_passed = False
            
            time.sleep(DELAY_SECONDS)
        
        # End game
        logger.info("Test complete, ending game")
        summary = end_game(GAME_ID)
        logger.info(f"Game summary: {json.dumps(summary, indent=2)}")
        
        if all_tests_passed:
            logger.info("SUCCESS: All tests passed!")
        else:
            logger.error("FAILURE: Some tests failed")
        
        return all_tests_passed
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if GAME_ID:
            try:
                end_game(GAME_ID)
            except:
                pass
        return False

if __name__ == "__main__":
    logger.info("Starting API test to verify fix for folded AI players issue")
    success = run_test()
    if success:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("One or more tests failed")
        sys.exit(1)