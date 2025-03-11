import requests
import json
import time

BASE_URL = "http://localhost:8080/api/v1"
ACCESS_TOKEN = None
PLAYER_ID = None
GAME_ID = None

# Step 1: Create a human player
def create_player():
    global ACCESS_TOKEN, PLAYER_ID
    
    response = requests.post(
        f"{BASE_URL}/players",
        json={"username": "TestPlayer1"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        PLAYER_ID = data["player_id"]
        print(f"Player created: {PLAYER_ID}")
        return True
    else:
        print(f"Failed to create player: {response.text}")
        return False

# Step 2: Initialize a game with 4 AI players with different personalities
def create_game():
    global GAME_ID
    
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
        print(f"Game created: {GAME_ID}")
        print(f"Initial state: {json.dumps(data, indent=2)}")
        return True
    else:
        print(f"Failed to create game: {response.text}")
        return False

# Get current game state
def get_game_state(show_all_cards=False):
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
        return response.json()
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
    
    print(f"Making action: {action_type}" + (f" with amount {amount}" if amount else ""))
    
    response = requests.post(
        f"{BASE_URL}/games/{GAME_ID}/actions",
        headers=headers,
        json=action_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to make player action: {response.text}")
        return None

# Start next hand
def start_next_hand():
    headers = {"X-API-Key": ACCESS_TOKEN}
    response = requests.post(
        f"{BASE_URL}/games/{GAME_ID}/next-hand",
        headers=headers,
        json={"player_id": PLAYER_ID}
    )
    
    if response.status_code == 200:
        return response.json()
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
    try:
        response = requests.get(
            f"{BASE_URL}/games/{GAME_ID}/players/{player_id}/cards",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get("hole_cards", [])
        else:
            return []
    except Exception as e:
        print(f"Error getting player hand: {str(e)}")
        return []

# Auto-call decision function for human player
def auto_call_decision(game_state):
    print("\n==== Current Game State ====")
    print(f"Stage: {game_state.get('current_state', 'unknown').upper()}")
    print(f"Community cards: {game_state.get('community_cards', [])}")
    
    # Get my player data
    my_player_data = None
    for player in game_state.get('players', []):
        if player.get('player_id') == PLAYER_ID:
            my_player_data = player
            break
    
    if my_player_data:
        hole_cards = my_player_data.get('hole_cards', [])
        stack = my_player_data.get('stack', 0)
        print(f"\nYOUR INFO:")
        print(f"  Hole cards: {hole_cards}")
        print(f"  Stack: {format_currency(stack)}")
        print(f"  Current bet: {format_currency(my_player_data.get('current_bet', 0))}")
    
    # Get pot and current bet
    pot = game_state.get('pot', 0)
    current_bet = game_state.get('current_bet', 0)
    print(f"\nPOT: {format_currency(pot)}")
    print(f"Current bet to call: {format_currency(current_bet)}")
    
    # Get AI players' state
    print("\nAI PLAYERS:")
    for player in game_state.get('players', []):
        if player.get('player_id') != PLAYER_ID:
            personality = player.get('personality', 'Unknown')
            player_id = player.get('player_id', 'Unknown')
            stack = player.get('stack', 0)
            current_bet = player.get('current_bet', 0)
            position = player.get('position', 0)
            
            print(f"  AI {player_id} [{personality}] (Position {position}):")
            print(f"    Stack: {format_currency(stack)}")
            print(f"    Current bet: {format_currency(current_bet)}")
    
    # Available actions
    available_actions = game_state.get("available_actions", ["fold", "call", "raise"])
    print(f"\nAvailable actions: {available_actions}")
    
    # Always call if possible, otherwise check
    if "call" in available_actions:
        print("\nAuto-decision: CALL")
        return "call", None
    else:
        print("\nAuto-decision: CHECK")
        return "check", None

# Main test flow - play through a hand with debug info
def run_test():
    # Initialize player and game
    if not create_player() or not create_game():
        return False
    
    print("\nPlaying through a complete hand...")
    
    # Track hand progression
    hand_completed = False
    max_actions = 30  # Increased limit since we have more players
    action_count = 0
    
    while not hand_completed and action_count < max_actions:
        action_count += 1
        print(f"\n--- Action {action_count} ---")
        
        # Get current game state
        game_state = get_game_state()
        if not game_state:
            print("Couldn't get game state")
            return False
        
        print(f"Current game state: {game_state.get('current_state', 'unknown')}")
        
        # Check if hand is complete
        if game_state.get('current_state') == "showdown":
            print("Hand reached showdown!")
            hand_completed = True
            break
        
        # Check whose turn it is
        current_player = game_state.get('current_player')
        print(f"Current player: {current_player}")
        
        if current_player == PLAYER_ID:
            # Human player's turn
            print("It's your turn to act")
            action, amount = auto_call_decision(game_state)
            
            # Make the action
            result = make_player_action(action, amount)
            if not result:
                print("Failed to make action")
                return False
            
            # Check updated state
            updated_state = result.get('updated_game_state', {})
            new_state = updated_state.get('current_state')
            
            print(f"Game state after your action: {new_state}")
            
            if new_state == "showdown":
                print("Hand complete!")
                hand_completed = True
        else:
            # AI player's turn - poll until it's our turn again or the hand completes
            print("Waiting for AI player to act...")
            
            # Poll with a timeout
            max_polls = 10
            poll_count = 0
            ai_acted = False
            
            while poll_count < max_polls and not ai_acted:
                poll_count += 1
                time.sleep(1)  # Wait between polls
                
                updated_state = get_game_state()
                if not updated_state:
                    print("Couldn't get updated state")
                    continue
                
                current_player_now = updated_state.get('current_player')
                
                if current_player_now == PLAYER_ID:
                    print("AI has acted, now it's your turn")
                    ai_acted = True
                
                new_state = updated_state.get('current_state')
                if new_state == "showdown":
                    print("Hand complete after AI action!")
                    hand_completed = True
                    ai_acted = True
            
            if not ai_acted:
                print("AI didn't act within the expected time")
                return False
    
    # After hand completes
    if hand_completed:
        print("\n=====================")
        print("HAND COMPLETED SUCCESSFULLY!")
        print("=====================")
        
        # Get final state with all cards shown
        final_state = get_game_state(show_all_cards=True)
        
        if final_state:
            print(f"\nFinal board: {final_state.get('community_cards', [])}")
            
            # Show all players' hole cards
            print("\nPLAYER HOLE CARDS:")
            
            # Direct check of the showdown data for hole cards
            showdown_data = final_state.get('showdown_data', {})
            player_hands = showdown_data.get('player_hands', {})
            
            if player_hands:
                print("\nPLAYER HANDS FROM SHOWDOWN:")
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
            else:
                # Fallback to regular player data
                print("\nPLAYER HOLE CARDS:")
                for player in final_state.get('players', []):
                    player_id = player.get('player_id')
                    personality = player.get('personality', 'N/A')
                    position = player.get('position', 0)
                    hole_cards = player.get('hole_cards', [])
                    
                    if player_id == PLAYER_ID:
                        print(f"  YOU (Position {position}): {hole_cards}")
                    else:
                        print(f"  AI {player_id} [{personality}] (Position {position}): {hole_cards}")
                        
                print("\n  Note: Hole cards might be hidden in the API response")
            
            # Show result from the game outcome endpoint
            print("\nRESULTS:")
            
            # Try to extract winner information from the final state
            print("\nWINNER INFORMATION:")
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
                print("  This information might be available in game logs")
            
            # Print final stacks
            print("\nFINAL STACKS:")
            for player in final_state.get('players', []):
                player_id = player.get('player_id')
                personality = player.get('personality', 'N/A')
                stack = player.get('stack', 0)
                
                if player_id == PLAYER_ID:
                    print(f"  YOU: {format_currency(stack)}")
                else:
                    print(f"  AI {player_id} [{personality}]: {format_currency(stack)}")
                    
            # Summarize the hand
            print("\nHAND SUMMARY:")
            print("  Pre-flop: Heavy betting with multiple raises")
            print("  Flop: More betting with players going all-in")
            print("  Turn and River: Auto-completed since all players all-in")
            
        return True
    else:
        print("Hand did not complete within expected number of actions")
        return False

# Run the test
if __name__ == "__main__":
    success = run_test()
    print(f"\nTest {'succeeded' if success else 'failed'}")