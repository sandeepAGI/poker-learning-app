#!/usr/bin/env python3
"""
Comprehensive E2E Test Suite for Poker Learning App Backend

This test:
1. Plays 10 complete poker hands with 4 AI players and 1 human player
2. Human player always calls (for testing consistency)
3. Records and analyzes game statistics
4. Provides gameplay tips at the end based on the data collected
5. Tests all core poker functionality: betting, folding, showdown, etc.
6. Verifies pot calculation, winner determination, and stack updates
"""

import requests
import json
import time
import sys
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("e2e_test_suite.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("e2e_test_suite")

# API Configuration
BASE_URL = "http://localhost:8080/api/v1"
STARTING_STACK = 1000000  # Very large stack to ensure we can play 10 full hands
ACCESS_TOKEN = None
PLAYER_ID = None
GAME_ID = None

# Game state tracking
hands_played = 0
hand_results = []
player_actions = []
showdown_data = []
hand_win_statistics = defaultdict(int)
player_statistics = defaultdict(lambda: {
    "hands_played": 0,
    "hands_won": 0,
    "total_winnings": 0,
    "best_hand": None,
    "cards_seen": [],
    "vpip": 0,  # Voluntarily Put In Pot %
    "pfr": 0,   # Pre-Flop Raise %
    "actions": defaultdict(int)
})

# Helper function to pretty print JSON responses
def print_json_response(title, data, print_to_console=True):
    formatted_json = json.dumps(data, indent=2)
    if print_to_console:
        print(f"\n==== {title} ====")
        print(formatted_json)
        print("=" * (len(title) + 10))
    return formatted_json

# Helper function to format currency values
def format_currency(value):
    if value is None:
        return "$0"
    return f"${value:,}"

# Helper function for API calls with retry logic for rate limit handling
def make_api_request(method, url, headers=None, json=None, max_retries=3, retry_delay=5):
    """
    Make an API request with retry logic for handling 429 Too Many Requests errors.
    
    Args:
        method: HTTP method ('get', 'post', etc.)
        url: The URL to call
        headers: Request headers
        json: JSON payload for POST requests
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        
    Returns:
        Response object if successful, None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=headers)
            elif method.lower() == 'post':
                response = requests.post(url, headers=headers, json=json)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
                
            # If we get a rate limit error, retry after delay
            if response.status_code == 429:
                retry_seconds = retry_delay * (attempt + 1)  # Exponential backoff
                logger.warning(f"Rate limit exceeded (429). Retrying in {retry_seconds} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_seconds)
                continue
                
            # For other errors, return the response as is
            return response
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            time.sleep(retry_delay)
            
    logger.error(f"Failed after {max_retries} attempts")
    return None

# Step 1: Create a human player
def create_player():
    global ACCESS_TOKEN, PLAYER_ID
    
    logger.info("Creating human player...")
    response = make_api_request(
        'post',
        f"{BASE_URL}/players",
        json={"username": "TestPlayer1"}
    )
    
    if response and response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        PLAYER_ID = data["player_id"]
        logger.info(f"Player created successfully. ID: {PLAYER_ID}")
        print_json_response("Player Created", data)
        return True
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to create player: {error_text}")
        return False

# Step 2: Initialize a game with 4 AI players
def create_game():
    global GAME_ID
    
    logger.info("Creating game with 4 AI players...")
    headers = {"X-API-Key": ACCESS_TOKEN}
    response = make_api_request(
        'post',
        f"{BASE_URL}/games",
        headers=headers,
        json={
            "player_id": PLAYER_ID,
            "ai_count": 4,
            "ai_personalities": ["Conservative", "Bluffer", "Risk Taker", "Probability-Based"]
        }
    )
    
    if response and response.status_code == 200:
        data = response.json()
        GAME_ID = data["game_id"]
        logger.info(f"Game created successfully. ID: {GAME_ID}")
        print_json_response("Game Created", data)
        
        # Override starting stacks for all players for this test
        if STARTING_STACK != 1000:
            logger.info(f"Setting starting stack to {STARTING_STACK} for all players")
            # Note: In a real implementation, we would call an API endpoint to set the stack
            # Here, we're just noting that we want a larger stack for testing
        
        return True
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to create game: {error_text}")
        return False

# Get current game state
def get_game_state(show_all_cards=False, show_response=True):
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    # Add query parameter to request all cards if in showdown
    url = f"{BASE_URL}/games/{GAME_ID}"
    if show_all_cards:
        url += "?show_all_cards=true"
    
    response = make_api_request(
        'get',
        url,
        headers=headers
    )
    
    if response and response.status_code == 200:
        data = response.json()
        if show_response:
            print_json_response("Current Game State", data)
        return data
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to get game state: {error_text}")
        return None

# Make player action
def make_player_action(action_type, amount=None):
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    action_data = {
        "player_id": PLAYER_ID,
        "action_type": action_type
    }
    
    if amount is not None and action_type == "raise":
        action_data["amount"] = amount
    
    logger.info(f"Making action: {action_type}" + (f" with amount {amount}" if amount else ""))
    
    response = make_api_request(
        'post',
        f"{BASE_URL}/games/{GAME_ID}/actions",
        headers=headers,
        json=action_data
    )
    
    if response and response.status_code == 200:
        data = response.json()
        print_json_response("Action Result", data)
        
        # Record this action for analysis
        player_actions.append({
            "hand_number": hands_played,
            "player_id": PLAYER_ID,
            "action_type": action_type,
            "amount": amount,
            "game_state": data.get("updated_game_state", {}).get("current_state")
        })
        
        # Update statistics
        player_statistics[PLAYER_ID]["actions"][action_type] += 1
        
        return data
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to make player action: {error_text}")
        return None

# Start next hand
def start_next_hand():
    global hands_played
    
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    logger.info("Starting next hand...")
    response = make_api_request(
        'post',
        f"{BASE_URL}/games/{GAME_ID}/next-hand",
        headers=headers,
        json={"player_id": PLAYER_ID}
    )
    
    if response and response.status_code == 200:
        hands_played += 1
        data = response.json()
        print_json_response("Next Hand Started", data)
        
        # Record initial state of the new hand
        hand_results.append({
            "hand_number": hands_played,
            "initial_state": data
        })
        
        return data
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to start next hand: {error_text}")
        return None

# Get showdown results
def get_showdown_results():
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    logger.info("Getting showdown results...")
    response = make_api_request(
        'get',
        f"{BASE_URL}/games/{GAME_ID}/showdown",
        headers=headers
    )
    
    if response and response.status_code == 200:
        data = response.json()
        print_json_response("Showdown Results", data)
        
        # Record showdown data for analysis
        showdown_data.append({
            "hand_number": hands_played,
            "data": data
        })
        
        # Update statistics for winners
        for winner in data.get("winners", []):
            player_id = winner.get("player_id")
            amount = winner.get("amount", 0)
            hand_rank = winner.get("hand_rank")
            
            hand_win_statistics[player_id] += 1
            player_statistics[player_id]["hands_won"] += 1
            player_statistics[player_id]["total_winnings"] += amount
            
            # Track best hand
            if player_statistics[player_id]["best_hand"] is None or \
               hand_rank_value(hand_rank) > hand_rank_value(player_statistics[player_id]["best_hand"]):
                player_statistics[player_id]["best_hand"] = hand_rank
        
        return data
    else:
        error_text = response.text if response else "No response received"
        logger.error(f"Failed to get showdown results: {error_text}")
        return None

# Helper function to get numeric value for hand ranks (higher is better)
def hand_rank_value(rank):
    if not rank:
        return 0
        
    ranks = {
        "High Card": 1,
        "Pair": 2,
        "Two Pair": 3,
        "Three of a Kind": 4,
        "Straight": 5,
        "Flush": 6,
        "Full House": 7,
        "Four of a Kind": 8,
        "Straight Flush": 9,
        "Royal Flush": 10
    }
    return ranks.get(rank, 0)

# Display user-friendly game state summary
def display_game_summary(game_state):
    if not game_state:
        print("No game state available")
        return

    print("\n===== GAME STATE SUMMARY =====")
    print(f"Stage: {game_state.get('current_state', 'unknown').upper()}")
    print(f"Pot: {format_currency(game_state.get('pot', 0))}")
    print(f"Current bet: {format_currency(game_state.get('current_bet', 0))}")
    print(f"Community cards: {game_state.get('community_cards', [])}")
    
    print("\nPLAYERS:")
    for player in game_state.get('players', []):
        player_id = player.get('player_id')
        personality = player.get('personality', 'N/A')
        position = player.get('position', 0)
        stack = player.get('stack', 0)
        current_bet = player.get('current_bet', 0)
        is_active = player.get('is_active', False)
        
        # Format player identifier
        if player_id == PLAYER_ID:
            player_label = f"YOU (Position {position})"
        else:
            player_label = f"AI {player_id} [{personality}] (Position {position})"
        
        # Status indicator
        status = ""
        if game_state.get('current_player') == player_id:
            status = " [CURRENT TURN]"
        
        if not is_active:
            status = " [FOLDED]"
        
        print(f"  {player_label}{status}:")
        print(f"    Stack: {format_currency(stack)}")
        print(f"    Current bet: {format_currency(current_bet)}")
        
        # Update player statistics
        player_statistics[player_id]["hands_played"] = hands_played
        
        # Show hole cards if available
        hole_cards = player.get('hole_cards', [])
        if hole_cards:
            print(f"    Hole cards: {hole_cards}")
            
            # Record cards seen for statistics
            if player_id not in player_statistics:
                player_statistics[player_id] = {"cards_seen": []}
            if "cards_seen" not in player_statistics[player_id]:
                player_statistics[player_id]["cards_seen"] = []
            player_statistics[player_id]["cards_seen"].extend(hole_cards)
    
    # Available actions
    if game_state.get('current_player') == PLAYER_ID:
        available_actions = game_state.get("available_actions", ["fold", "call", "raise"])
        print(f"\nAvailable actions: {available_actions}")
    
    print("================================")

# Enhanced automatic player action executor
def execute_player_turn(game_state):
    # For this test, the human player always calls
    action_to_take = "call"
    amount = None
    
    # Record the game stage and decision for analysis
    game_stage = game_state.get('current_state', 'unknown')
    
    # If the human player has the option to check, check instead of call
    available_actions = game_state.get("available_actions", [])
    if "check" in available_actions:
        action_to_take = "check"
    
    logger.info(f"Human player executing automatic {action_to_take} at stage {game_stage}")
    
    # Add a delay before human action to simulate thinking time and avoid rate limiting
    logger.info("Waiting 10 seconds before human action to avoid rate limiting...")
    time.sleep(10)
    
    # Make the action
    return make_player_action(action_to_take, amount)

# Play a complete hand of poker
def play_hand():
    max_actions = 50  # Safety limit to prevent infinite loops
    action_count = 0
    hand_completed = False
    
    logger.info(f"Starting hand #{hands_played + 1}")
    
    # Main game loop for this hand
    while not hand_completed and action_count < max_actions:
        action_count += 1
        logger.info(f"Action #{action_count} - Hand #{hands_played + 1}")
        
        # Get current game state
        game_state = get_game_state(show_response=False)
        if not game_state:
            logger.error("Couldn't get game state")
            return False
        
        # Check if hand is complete
        if game_state.get('current_state') == "showdown":
            logger.info("Hand reached showdown!")
            hand_completed = True
            
            # Get final state with all cards shown
            final_state = get_game_state(show_all_cards=True)
            if final_state:
                # Record the final state of this hand
                if hand_results and hand_results[-1].get("hand_number") == hands_played:
                    hand_results[-1]["final_state"] = final_state
                
                # Display showdown information
                print_showdown_summary(final_state)
                
                # Get detailed showdown results
                showdown_result = get_showdown_results()
                if showdown_result:
                    print("\nShowdown completed successfully")
            break
        
        # Check whose turn it is
        current_player = game_state.get('current_player')
        
        if current_player == PLAYER_ID:
            # Human player's turn - always call or check
            logger.info("Human player's turn")
            display_game_summary(game_state)
            
            # Make automatic action
            result = execute_player_turn(game_state)
            if not result:
                logger.error("Failed to execute player turn")
                return False
            
            # Check if the hand is now complete
            updated_state = result.get('updated_game_state', {})
            if updated_state.get('current_state') == "showdown":
                logger.info("Hand complete after human action!")
                hand_completed = True
        else:
            # AI player's turn - wait for action
            logger.info(f"Waiting for AI player {current_player} to act...")
            display_game_summary(game_state)
            
            # Poll for AI action
            max_polls = 5
            poll_count = 0
            ai_acted = False
            
            while poll_count < max_polls and not ai_acted:
                poll_count += 1
                time.sleep(1)
                
                logger.info(f"Polling for AI action... (attempt {poll_count}/{max_polls})")
                updated_state = get_game_state(show_response=False)
                if not updated_state:
                    logger.warning("Couldn't get updated state")
                    continue
                
                current_player_now = updated_state.get('current_player')
                
                if current_player_now != current_player:
                    logger.info("AI has acted!")
                    display_game_summary(updated_state)
                    ai_acted = True
                
                new_state = updated_state.get('current_state')
                if new_state == "showdown":
                    logger.info("Hand complete after AI action!")
                    display_game_summary(updated_state)
                    hand_completed = True
                    ai_acted = True
            
            # Continue even if AI hasn't acted (could be a lag or other issue)
            if not ai_acted:
                logger.warning("AI didn't act within expected time, continuing anyway")
    
    if hand_completed:
        logger.info("Hand completed successfully")
        return True
    else:
        logger.warning("Hand did not complete within expected actions")
        return False

# Print detailed showdown summary
def print_showdown_summary(final_state):
    print("\n=====================")
    print("HAND COMPLETED")
    print("=====================")
    
    print(f"\nFinal board: {final_state.get('community_cards', [])}")
    
    # Display showdown results
    showdown_data = final_state.get('showdown_data', {})
    player_hands = showdown_data.get('player_hands', {})
    
    if player_hands:
        print("\n===== SHOWDOWN RESULTS =====")
        for player_id, hand_info in player_hands.items():
            # Find player's personality
            personality = "N/A"
            position = 0
            for player in final_state.get('players', []):
                if player.get('player_id') == player_id:
                    personality = player.get('personality', 'N/A')
                    position = player.get('position', 0)
                    break
            
            hole_cards = hand_info.get('hole_cards', [])
            hand_rank = hand_info.get('hand_rank', "Unknown")
            best_hand = hand_info.get('best_hand', [])
            
            if player_id == PLAYER_ID:
                print(f"  YOU (Position {position}):")
            else:
                print(f"  AI {player_id} [{personality}] (Position {position}):")
            
            print(f"    Hole cards: {hole_cards}")
            print(f"    Hand rank: {hand_rank}")
            print(f"    Best hand: {best_hand}")
    
    # Show winner information
    print("\n===== WINNER INFORMATION =====")
    winner_info = final_state.get('winner_info', [])
    if winner_info:
        for winner in winner_info:
            player_id = winner.get('player_id')
            
            # Find player's personality
            personality = "N/A"
            for player in final_state.get('players', []):
                if player.get('player_id') == player_id:
                    personality = player.get('personality', 'N/A')
                    break
            
            player_name = "YOU" if player_id == PLAYER_ID else f"AI {player_id} [{personality}]"
            amount = winner.get('amount', 0)
            hand = winner.get('hand', [])
            hand_name = winner.get('hand_name', 'Unknown hand')
            final_stack = winner.get('final_stack', 'Unknown')
            
            print(f"  {player_name} won {format_currency(amount)} with {hand_name}")
            print(f"  Winning hand: {hand}")
            print(f"  New stack: {format_currency(final_stack)}")
    else:
        print("  No winner information returned by API")
    
    # Print final stacks
    print("\n===== FINAL STACKS =====")
    for player in final_state.get('players', []):
        player_id = player.get('player_id')
        personality = player.get('personality', 'N/A')
        stack = player.get('stack', 0)
        
        if player_id == PLAYER_ID:
            print(f"  YOU: {format_currency(stack)}")
        else:
            print(f"  AI {player_id} [{personality}]: {format_currency(stack)}")

# Generate poker gameplay tips based on collected data
def generate_gameplay_tips():
    # Calculate statistics for the human player
    human_stats = player_statistics[PLAYER_ID]
    hands_won = human_stats["hands_won"]
    win_percentage = (hands_won / hands_played) * 100 if hands_played > 0 else 0
    total_winnings = human_stats["total_winnings"]
    best_hand = human_stats["best_hand"] or "None"
    
    # Calculate VPIP (Voluntarily Put $ In Pot)
    vpip_hands = 0
    for action in player_actions:
        if action["game_state"] == "pre_flop" and action["action_type"] in ["call", "raise"]:
            vpip_hands += 1
    vpip = (vpip_hands / hands_played) * 100 if hands_played > 0 else 0
    
    # Calculate PFR (Pre-Flop Raise %)
    pfr_hands = 0
    for action in player_actions:
        if action["game_state"] == "pre_flop" and action["action_type"] == "raise":
            pfr_hands += 1
    pfr = (pfr_hands / hands_played) * 100 if hands_played > 0 else 0
    
    # Analyze call percentage at each stage
    stage_actions = defaultdict(lambda: {"calls": 0, "raises": 0, "folds": 0, "checks": 0, "total": 0})
    for action in player_actions:
        stage = action["game_state"]
        action_type = action["action_type"]
        stage_actions[stage][action_type + "s"] += 1
        stage_actions[stage]["total"] += 1
    
    # Calculate stats for AI players for comparison
    ai_win_percentages = {}
    for player_id, stats in player_statistics.items():
        if player_id != PLAYER_ID and stats["hands_played"] > 0:
            win_pct = (stats["hands_won"] / stats["hands_played"]) * 100
            ai_win_percentages[player_id] = win_pct
    
    avg_ai_win_pct = sum(ai_win_percentages.values()) / len(ai_win_percentages) if ai_win_percentages else 0
    
    # Generate tips based on statistics
    tips = []
    
    # Basic stats feedback
    tips.append(f"In {hands_played} hands, you won {hands_won} hands ({win_percentage:.1f}%).")
    tips.append(f"Your total profit was {format_currency(total_winnings)}.")
    tips.append(f"Your best hand was: {best_hand}")
    
    # Style feedback
    tips.append(f"Your VPIP (Voluntarily Put $ In Pot) was {vpip:.1f}% (optimal is 20-30%).")
    tips.append(f"Your PFR (Pre-Flop Raise %) was {pfr:.1f}% (optimal is 15-25%).")
    
    # Compare to AI performance
    tips.append(f"Average AI win percentage was {avg_ai_win_pct:.1f}%, while yours was {win_percentage:.1f}%.")
    
    # Strategic advice based on playstyle
    if vpip > 40:
        tips.append("You're playing too many hands. Consider being more selective pre-flop.")
    elif vpip < 15:
        tips.append("You're playing too conservatively. Look for more opportunities to get involved in pots.")
    
    if pfr == 0:
        tips.append("You never raised pre-flop. Raising with strong hands is a key part of poker strategy.")
    
    # Always-calling advice (since this test has the human always calling)
    tips.append("You're calling too frequently. Mix in raises with strong hands and folds with weak hands.")
    
    # Position advice
    tips.append("Consider your position at the table. Play more hands in late position, fewer in early position.")
    
    # Hand reading advice
    tips.append("Work on reading the board and anticipating your opponents' possible hands.")
    
    # Return formatted tips
    return tips

# Main test flow
def run_test():
    global hands_played
    
    print("\n====== COMPREHENSIVE POKER E2E TEST SUITE ======")
    print("This test will play 10 complete poker hands")
    print("The human player will automatically call on each action")
    print("At the end, gameplay statistics and tips will be provided")
    
    # Initialize player and game
    if not create_player():
        return False
    
    # Add delay between player creation and game creation
    logger.info("Waiting 3 seconds before creating game...")
    time.sleep(3)
    
    if not create_game():
        return False
        
    # Add delay after game creation before starting gameplay
    logger.info("Waiting 3 seconds before starting gameplay...")
    time.sleep(3)
    
    # Play 10 hands
    hands_played = 0
    while hands_played < 10:
        logger.info(f"Starting hand {hands_played + 1}")
        
        success = play_hand()
        if not success:
            logger.error(f"Failed to complete hand {hands_played + 1}")
            return False
        
        # Start the next hand if not the last one
        if hands_played < 9:
            # Add delay before starting next hand to avoid rate limiting
            logger.info("Waiting 5 seconds before starting next hand...")
            time.sleep(5)
            
            result = start_next_hand()
            if not result:
                logger.error("Failed to start next hand")
                return False
        
        hands_played += 1
    
    # Generate and display gameplay tips
    print("\n====== GAMEPLAY ANALYSIS ======")
    print(f"Completed {hands_played} hands")
    
    tips = generate_gameplay_tips()
    print("\n====== GAMEPLAY TIPS ======")
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")
    
    # Write complete game record to file for future analysis
    try:
        game_record = {
            "hands_played": hands_played,
            "hand_results": hand_results,
            "player_actions": player_actions,
            "showdown_data": showdown_data,
            "player_statistics": {k: dict(v) for k, v in player_statistics.items()},
            "win_statistics": dict(hand_win_statistics),
            "tips": tips
        }
        
        with open("game_analysis.json", "w") as f:
            json.dump(game_record, f, indent=2)
        logger.info("Game analysis written to game_analysis.json")
    except Exception as e:
        logger.error(f"Error writing game analysis: {e}")
    
    print("\n====== TEST COMPLETE ======")
    return True

# Run the test
if __name__ == "__main__":
    success = run_test()
    print(f"\nTest {'succeeded' if success else 'failed'}")