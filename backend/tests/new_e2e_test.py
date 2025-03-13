import requests
import json
import time

BASE_URL = "http://localhost:8080/api/v1"
ACCESS_TOKEN = None
PLAYER_ID = None
GAME_ID = None

# Helper function to pause execution and wait for user input
def pause_for_review(message="Press Enter to continue..."):
    input(f"\n{message}")

# Helper function to pretty print JSON responses
def print_json_response(title, data):
    print(f"\n==== {title} ====")
    print(json.dumps(data, indent=2))
    print("=" * (len(title) + 10))

# Step 1: Create a human player
def create_player():
    global ACCESS_TOKEN, PLAYER_ID
    
    print("\nCreating player...")
    response = requests.post(
        f"{BASE_URL}/players",
        json={"username": "TestPlayer1"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        PLAYER_ID = data["player_id"]
        print_json_response("Player Created", data)
        return True
    else:
        print(f"Failed to create player: {response.text}")
        return False

# Step 2: Initialize a game with 4 AI players with different personalities
def create_game():
    global GAME_ID
    
    print("\nCreating game with 4 AI players...")
    headers = {"X-API-Key": ACCESS_TOKEN}
    response = requests.post(
        f"{BASE_URL}/games",
        headers=headers,
        json={
            "player_id": PLAYER_ID,
            "ai_count": 4,
            "ai_personalities": ["Conservative", "Bluffer", "Risk Taker", "Probability-Based"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        GAME_ID = data["game_id"]
        print_json_response("Game Created", data)
        return True
    else:
        print(f"Failed to create game: {response.text}")
        return False

# Get current game state
def get_game_state(show_all_cards=False, show_response=True):
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    # Add query parameter to request all cards if in showdown
    url = f"{BASE_URL}/games/{GAME_ID}"
    if show_all_cards:
        url += "?show_all_cards=true"
    
    response = requests.get(
        url,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if show_response:
            print_json_response("Current Game State", data)
        return data
    else:
        print(f"Failed to get game state: {response.text}")
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
    
    print(f"\nMaking action: {action_type}" + (f" with amount {amount}" if amount else ""))
    print(f"Request payload: {json.dumps(action_data, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/games/{GAME_ID}/actions",
        headers=headers,
        json=action_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print_json_response("Action Result", data)
        return data
    else:
        print(f"Failed to make player action: {response.text}")
        return None

# Start next hand
def start_next_hand():
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    print("\nStarting next hand...")
    response = requests.post(
        f"{BASE_URL}/games/{GAME_ID}/next-hand",
        headers=headers,
        json={"player_id": PLAYER_ID}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_json_response("Next Hand Started", data)
        return data
    else:
        print(f"Failed to start next hand: {response.text}")
        return None

# Format currency value for display
def format_currency(value):
    if value is None:
        return "$0"
    return f"${value}"

# Helper function to get hand details
def get_player_hand(player_id):
    headers = {"X-API-Key": ACCESS_TOKEN}
    
    print(f"\nGetting cards for player {player_id}...")
    try:
        response = requests.get(
            f"{BASE_URL}/games/{GAME_ID}/players/{player_id}/cards",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_json_response(f"Player {player_id} Cards", data)
            return data.get("hole_cards", [])
        else:
            print(f"Error getting player hand: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting player hand: {str(e)}")
        return []

# Display user-friendly game state summary
def display_game_summary(game_state):
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
        
        # Show hole cards if available
        hole_cards = player.get('hole_cards', [])
        if hole_cards:
            print(f"    Hole cards: {hole_cards}")
    
    # Available actions (only relevant for human player's turn)
    if game_state.get('current_player') == PLAYER_ID:
        available_actions = game_state.get("available_actions", ["fold", "call", "raise"])
        print(f"\nAvailable actions: {available_actions}")
    
    print("================================")

# Enhanced decision function with user input for player actions
def player_decision(game_state):
    display_game_summary(game_state)
    
    # If it's not player's turn, just provide summary
    if game_state.get('current_player') != PLAYER_ID:
        return None, None
    
    # Get available actions
    available_actions = game_state.get("available_actions", ["fold", "call", "raise"])
    
    # Get my player data for context
    my_player_data = None
    for player in game_state.get('players', []):
        if player.get('player_id') == PLAYER_ID:
            my_player_data = player
            break
    
    # Show hole cards for decision
    if my_player_data:
        hole_cards = my_player_data.get('hole_cards', [])
        print(f"\nYOUR HOLE CARDS: {hole_cards}")
    
    # Ask for action
    print("\nChoose your action:")
    for i, action in enumerate(available_actions):
        print(f"{i+1}. {action.upper()}")
    
    print("a. Auto-play (will call/check)")
    
    # Get user choice
    choice = input("\nEnter choice (number, or 'a' for auto): ").strip().lower()
    
    # Handle auto-play
    if choice == 'a':
        if "call" in available_actions:
            return "call", None
        elif "check" in available_actions:
            return "check", None
        else:
            return "fold", None
    
    # Process numeric choice
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(available_actions):
            action = available_actions[idx]
            
            # If raising, ask for amount
            if action == "raise":
                amount_str = input("Enter raise amount: $")
                try:
                    amount = int(amount_str)
                    return action, amount
                except ValueError:
                    print("Invalid amount, defaulting to minimum raise")
                    return action, None
            else:
                return action, None
        else:
            print("Invalid choice, auto-calling")
            if "call" in available_actions:
                return "call", None
            elif "check" in available_actions:
                return "check", None
            else:
                return "fold", None
    except ValueError:
        print("Invalid choice, auto-calling")
        if "call" in available_actions:
            return "call", None
        elif "check" in available_actions:
            return "check", None
        else:
            return "fold", None

# Main test flow with pauses and more detailed feedback
def run_test():
    print("\n====== POKER E2E TEST ======")
    print("This test will step through a poker hand with pauses")
    print("Press Enter at each step to continue")
    pause_for_review()
    
    # Initialize player and game
    if not create_player():
        return False
    pause_for_review()
    
    if not create_game():
        return False
    pause_for_review()
    
    print("\nStarting a hand...")
    
    # Track hand progression
    hand_completed = False
    max_actions = 30
    action_count = 0
    
    while not hand_completed and action_count < max_actions:
        action_count += 1
        print(f"\n====== ACTION {action_count} ======")
        
        # Get current game state
        game_state = get_game_state(show_response=False)
        if not game_state:
            print("Couldn't get game state")
            return False
        
        # Check if hand is complete
        if game_state.get('current_state') == "showdown":
            print("Hand reached showdown!")
            hand_completed = True
            break
        
        # Check whose turn it is
        current_player = game_state.get('current_player')
        
        if current_player == PLAYER_ID:
            # Human player's turn
            print("It's your turn to act")
            action, amount = player_decision(game_state)
            
            # Make the action
            result = make_player_action(action, amount)
            if not result:
                print("Failed to make action")
                return False
            
            pause_for_review()
            
            # Check updated state
            updated_state = result.get('updated_game_state', {})
            new_state = updated_state.get('current_state')
            
            if new_state == "showdown":
                print("Hand complete!")
                hand_completed = True
        else:
            # AI player's turn
            print(f"Waiting for AI player {current_player} to act...")
            display_game_summary(game_state)
            
            # Option to wait or force AI action immediately
            choice = input("\nPress Enter to wait for AI action, or type 'f' to force immediate action: ").strip().lower()
            
            if choice == 'f':
                print("Forcing immediate AI action...")
                # We'll just poll once and continue
                time.sleep(2)
                updated_state = get_game_state(show_response=False)
                
                if not updated_state:
                    print("Couldn't get updated state")
                    continue
                
                display_game_summary(updated_state)
                pause_for_review()
                
                # Check if it's now our turn or the hand is complete
                current_player_now = updated_state.get('current_player')
                new_state = updated_state.get('current_state')
                
                if current_player_now == PLAYER_ID:
                    print("AI has acted, now it's your turn")
                
                if new_state == "showdown":
                    print("Hand complete after AI action!")
                    hand_completed = True
            else:
                # Poll with multiple updates and a timeout
                max_polls = 10
                poll_count = 0
                ai_acted = False
                
                while poll_count < max_polls and not ai_acted:
                    poll_count += 1
                    time.sleep(1)
                    
                    print(f"Polling for AI action... (attempt {poll_count}/{max_polls})")
                    updated_state = get_game_state(show_response=False)
                    if not updated_state:
                        print("Couldn't get updated state")
                        continue
                    
                    current_player_now = updated_state.get('current_player')
                    
                    if current_player_now != current_player:
                        print("AI has acted!")
                        display_game_summary(updated_state)
                        pause_for_review()
                        ai_acted = True
                    
                    new_state = updated_state.get('current_state')
                    if new_state == "showdown":
                        print("Hand complete after AI action!")
                        display_game_summary(updated_state)
                        pause_for_review()
                        hand_completed = True
                        ai_acted = True
                
                if not ai_acted:
                    print("AI didn't act within the expected time")
                    choice = input("Continue waiting? (y/n): ").strip().lower()
                    if choice != 'y':
                        return False
    
    # After hand completes
    if hand_completed:
        print("\n=====================")
        print("HAND COMPLETED")
        print("=====================")
        
        # Get final state with all cards shown
        final_state = get_game_state(show_all_cards=True)
        
        if final_state:
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
                    
                    print(f"  {player_name} won {format_currency(amount)} with {hand_name}")
                    print(f"  Winning hand: {hand}")
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
        
        # Ask if user wants to play another hand
        choice = input("\nPlay another hand? (y/n): ").strip().lower()
        if choice == 'y':
            next_hand_result = start_next_hand()
            if next_hand_result:
                print("New hand started! Run the test again to play it.")
        
        return True
    else:
        print("Hand did not complete within expected number of actions")
        return False

# Run the test
if __name__ == "__main__":
    success = run_test()
    print(f"\nTest {'succeeded' if success else 'failed'}")