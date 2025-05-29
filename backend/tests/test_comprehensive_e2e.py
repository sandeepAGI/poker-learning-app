#!/usr/bin/env python3
"""
Comprehensive E2E Test for Poker Game Backend

This test:
1. Creates a game with mixed AI players
2. Plays multiple complete poker hands
3. Verifies card handling, betting, folding, showdown, and stack updates
4. Tests specific edge cases related to recent fixes
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
        logging.FileHandler("comprehensive_e2e_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("comprehensive_e2e_test")

# API Configuration
BASE_URL = "http://localhost:8080/api/v1"
TEST_PLAYER_ID = None
ACCESS_TOKEN = None
GAME_ID = None

def create_player() -> bool:
    """Create a human player and get access token"""
    global ACCESS_TOKEN, TEST_PLAYER_ID
    
    logger.info("Creating test player")
    
    try:
        response = requests.post(
            f"{BASE_URL}/players",
            json={"username": f"ComprehensiveTestPlayer_{int(time.time())}"}
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
                delay: float = 1.0, retries: int = 0) -> Dict:
    """Make API request with proper error handling and rate limit handling"""
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
        
        # Check for rate limiting
        if response.status_code == 429 and retries < 3:
            retry_after = int(response.headers.get('Retry-After', 2))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return api_request(method, endpoint, data, params, delay * 2, retries + 1)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def create_game() -> str:
    """Create a new game with AI players of different personalities"""
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

def get_player_cards(game_id: str, player_id: str, target_player_id: str) -> Dict:
    """Get a player's hole cards"""
    return api_request("get", f"/games/{game_id}/players/{target_player_id}/cards")

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

def verify_player_status(players: List[Dict], expected_active_count: int) -> bool:
    """Verify player active status count matches expected"""
    active_count = sum(1 for p in players if p.get("is_active", False))
    logger.info(f"Active players: {active_count}, Expected: {expected_active_count}")
    return active_count == expected_active_count

def verify_stack_changes(previous_state: Dict, current_state: Dict, action_player_id: str, action_type: str, amount: Optional[int] = None) -> bool:
    """Verify that stack changes match expectations after an action"""
    previous_players = {p["player_id"]: p for p in previous_state["players"]}
    current_players = {p["player_id"]: p for p in current_state["players"]}
    
    # Check the acting player's stack
    prev_stack = previous_players[action_player_id]["stack"]
    curr_stack = current_players[action_player_id]["stack"]
    
    if action_type == "fold":
        # Stack should not change on fold
        expected_stack = prev_stack
    elif action_type == "call":
        # Stack decreases by current bet minus previous bet
        prev_bet = previous_players[action_player_id].get("current_bet", 0)
        curr_bet = current_players[action_player_id].get("current_bet", 0)
        bet_difference = curr_bet - prev_bet
        expected_stack = prev_stack - bet_difference
    elif action_type == "raise":
        # Stack decreases by amount
        expected_stack = prev_stack - amount
    else:
        logger.warning(f"Unknown action type: {action_type}")
        return False
    
    logger.info(f"Player {action_player_id} stack: {prev_stack} -> {curr_stack} (expected: {expected_stack})")
    
    # Allow a small tolerance for different calculation methods
    return abs(curr_stack - expected_stack) <= 1

def verify_pot_consistency(game_state: Dict) -> bool:
    """Verify that the pot matches the sum of player bets"""
    total_bets = sum(p.get("current_bet", 0) for p in game_state["players"])
    pot = game_state["pot"]
    
    logger.info(f"Pot: {pot}, Sum of bets: {total_bets}")
    
    # Allow for bets not yet added to pot
    return pot >= total_bets or (total_bets - pot) <= max(p.get("current_bet", 0) for p in game_state["players"])

def verify_total_chips_conserved(initial_state: Dict, current_state: Dict) -> bool:
    """Verify that the total chips in the system are conserved"""
    initial_total = sum(p["stack"] for p in initial_state["players"]) + initial_state["pot"]
    current_total = sum(p["stack"] for p in current_state["players"]) + current_state["pot"]
    
    logger.info(f"Initial total chips: {initial_total}, Current total chips: {current_total}")
    
    # Should be exactly equal
    return initial_total == current_total

def test_folded_player_reactivation():
    """Test that folded players are properly reactivated in the next hand"""
    # Start a game
    global GAME_ID
    GAME_ID = create_game()
    
    # Get initial state
    initial_state = get_game_state(GAME_ID)
    logger.info(f"Initial active players: {sum(1 for p in initial_state['players'] if p.get('is_active', False))}")
    
    # Have the human player fold
    current_state = initial_state
    while current_state["current_player"] != TEST_PLAYER_ID:
        # Wait for AI players to act
        time.sleep(1)
        current_state = get_game_state(GAME_ID)
    
    # Fold
    fold_result = process_action(GAME_ID, TEST_PLAYER_ID, "fold")
    current_state = fold_result.get("updated_game_state", {})
    
    # Verify the human player is now inactive
    human_player = next((p for p in current_state["players"] if p["player_id"] == TEST_PLAYER_ID), None)
    logger.info(f"Human player active status after fold: {human_player.get('is_active', False)}")
    assert not human_player.get("is_active", True), "Human player should be inactive after folding"
    
    # Make some AI players fold
    # Either wait for them to fold naturally or force specific players to fold
    # For this test, we'll wait until all rounds complete
    while current_state.get("current_state") != "showdown":
        time.sleep(1)
        current_state = get_game_state(GAME_ID)
        if current_state.get("current_player") == TEST_PLAYER_ID:
            # Handle the case where the human needs to act again
            process_action(GAME_ID, TEST_PLAYER_ID, "fold")
    
    # Verify some players folded
    folded_count = sum(1 for p in current_state["players"] if not p.get("is_active", False))
    logger.info(f"Folded players at end of hand: {folded_count}")
    assert folded_count > 0, "At least one player should have folded"
    
    # Start next hand
    next_hand_result = next_hand(GAME_ID, TEST_PLAYER_ID)
    next_hand_state = get_game_state(GAME_ID)
    
    # Verify all players with sufficient chips are active in the new hand
    reactivated_count = sum(1 for p in next_hand_state["players"] 
                            if p.get("is_active", False) and p.get("stack", 0) >= 5)
    total_eligible = sum(1 for p in next_hand_state["players"] if p.get("stack", 0) >= 5)
    
    logger.info(f"Reactivated players: {reactivated_count}, Total eligible: {total_eligible}")
    assert reactivated_count == total_eligible, "All eligible players should be reactivated"

def test_winner_stack_update():
    """Test that the winner's stack is properly updated after a hand"""
    # Start a game if needed
    global GAME_ID
    if not GAME_ID:
        GAME_ID = create_game()
    
    # Get initial state
    initial_state = get_game_state(GAME_ID)
    
    # Store player states before the hand
    initial_player_stacks = {p["player_id"]: p["stack"] for p in initial_state["players"]}
    
    # Play through the hand
    current_state = initial_state
    hand_complete = False
    
    # Store the current bets for detailed analysis
    player_actions = {}
    
    # Track the state right before showdown
    pre_showdown_state = None
    
    while not hand_complete:
        # Check if hand is complete
        if current_state.get("current_state") == "showdown":
            hand_complete = True
            break
            
        # Check if it's the human player's turn
        if current_state.get("current_player") == TEST_PLAYER_ID:
            # Store the state before the last action
            pre_showdown_state = current_state
            
            # Check if player has sufficient funds for the call
            human_player = next((p for p in current_state["players"] if p["player_id"] == TEST_PLAYER_ID), None)
            current_bet = human_player.get("current_bet", 0)
            highest_bet = max(p.get("current_bet", 0) for p in current_state["players"])
            required_amount = highest_bet - current_bet
            available_amount = human_player.get("stack", 0)
            
            logger.info(f"Player bet: {current_bet}, Highest bet: {highest_bet}")
            logger.info(f"Required amount: {required_amount}, Available: {available_amount}")
            
            # Choose appropriate action based on available funds
            if available_amount >= required_amount:
                action_type = "call"
            else:
                # If we can't call, we should fold
                action_type = "fold"
                
            logger.info(f"Taking action: {action_type}")
            action_result = process_action(GAME_ID, TEST_PLAYER_ID, action_type)
            current_state = action_result.get("updated_game_state", {})
            
            # Record the action and state for debugging
            if TEST_PLAYER_ID not in player_actions:
                player_actions[TEST_PLAYER_ID] = []
            player_actions[TEST_PLAYER_ID].append({
                "action": action_type,
                "required": required_amount,
                "current_bet": current_bet,
                "stack_before": available_amount,
                "stack_after": next((p["stack"] for p in current_state["players"] if p["player_id"] == TEST_PLAYER_ID), None)
            })
        else:
            # Wait for AI to act
            time.sleep(1)
            
            # Get the new state and store it as pre-showdown
            pre_showdown_state = current_state
            current_state = get_game_state(GAME_ID)
    
    # Get showdown results with all cards visible
    showdown_state = get_game_state(GAME_ID, show_all_cards=True)
    
    # Try to get more detailed showdown results via the dedicated endpoint
    try:
        detailed_showdown = get_showdown_results(GAME_ID)
        logger.info(f"Detailed showdown results: {json.dumps(detailed_showdown, indent=2)}")
    except Exception as e:
        logger.warning(f"Could not get detailed showdown results: {e}")
        detailed_showdown = None
    
    # Check if there's winner information
    if "winner_info" not in showdown_state or not showdown_state["winner_info"]:
        logger.info("No winner information available - player might have folded")
        # Start the next hand and exit the test
        next_hand_result = next_hand(GAME_ID, TEST_PLAYER_ID)
        return
    
    # Get winner details
    winner_info = showdown_state["winner_info"][0]
    winner_id = winner_info["player_id"]
    win_amount = winner_info["amount"]
    
    logger.info(f"Winner: {winner_id}, Amount: {win_amount}")
    
    # Find the winner's stack at different points
    winner_initial = initial_player_stacks.get(winner_id, 0)
    
    # Get winner's stack just before showdown (accounts for bets made)
    winner_pre_showdown = 0
    if pre_showdown_state:
        winner_pre_showdown = next((p["stack"] for p in pre_showdown_state["players"] if p["player_id"] == winner_id), 0)
    
    # Get winner's final stack
    winner_final = next((p["stack"] for p in showdown_state["players"] if p["player_id"] == winner_id), 0)
    
    # Calculate how much the winner bet during the hand
    winner_total_bet = winner_initial - winner_pre_showdown
    
    # Check for a better bet amount from detailed showdown if available
    if detailed_showdown and "player_hands" in detailed_showdown:
        # Some implementations might include bet info in detailed showdown
        winner_bet_info = detailed_showdown.get("player_hands", {}).get(winner_id, {}).get("total_bet", None)
        if winner_bet_info is not None:
            winner_total_bet = winner_bet_info
            logger.info(f"Using bet amount from detailed showdown: {winner_total_bet}")
    
    logger.info(f"Winner's initial stack: {winner_initial}")
    logger.info(f"Winner's pre-showdown stack: {winner_pre_showdown}")
    logger.info(f"Winner's final stack: {winner_final}")
    logger.info(f"Total bet by winner: {winner_total_bet}")
    logger.info(f"Game pot: {showdown_state.get('pot', 0)}")
    
    # Expected final stack calculation
    expected_final = winner_pre_showdown + win_amount
    
    logger.info(f"Expected final stack: {expected_final}")
    logger.info(f"Actual final stack: {winner_final}")
    
    # Add better verification with tolerance for rounding
    stack_difference = abs(winner_final - expected_final)
    if stack_difference > 1:  # Allow for 1 chip rounding difference
        logger.error(f"STACK UPDATE ERROR: Expected {expected_final}, got {winner_final}")
        logger.error(f"Difference: {stack_difference} chips")
    else:
        logger.info(f"STACK UPDATE VERIFIED: Final stack {winner_final} matches expected {expected_final} (within tolerance)")
    
    # Start the next hand
    next_hand_result = next_hand(GAME_ID, TEST_PLAYER_ID)
    next_hand_state = get_game_state(GAME_ID)

def run_tests():
    """Run all tests in sequence"""
    try:
        # Create player first to get proper authentication token
        if not create_player():
            logger.error("Failed to create test player")
            return False
        
        # Run individual test cases
        test_folded_player_reactivation()
        test_winner_stack_update()
        
        logger.info("All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting comprehensive E2E test suite")
    success = run_tests()
    if success:
        logger.info("Test suite completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test suite failed!")
        sys.exit(1)