#!/usr/bin/env python
"""
Manual End-to-End Testing Script for Poker Learning App API
This script provides a command-line interface to test various API endpoints.
"""

import requests
import json
import sys
import os
import time
import threading
import uuid
from datetime import datetime

# Global variables to store state during testing
game_id = None
player_ids = {}
auth_tokens = {}

# Base URL for API
BASE_URL = "http://localhost:8080/api/v1"

def pretty_print_response(response):
    """Pretty print a response object"""
    print("\n=== Response ===")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("===============\n")

def test_root():
    """Test the root endpoint"""
    print("\n🔍 Testing root endpoint (/)")
    response = requests.get("http://localhost:8080/")
    pretty_print_response(response)
    return response.ok

def test_api_docs():
    """Test the API documentation endpoint"""
    print("\n🔍 Testing API docs endpoint (/api/docs)")
    response = requests.get("http://localhost:8080/api/docs")
    print(f"Status Code: {response.status_code}")
    print(f"Length of HTML response: {len(response.text)}")
    return response.ok

def test_create_player(name=None, strategy=None):
    """Test creating a new player"""
    if name is None:
        name = f"Player_{uuid.uuid4().hex[:8]}"
    
    if strategy is None:
        strategy = "probability_based"
    
    print(f"\n🔍 Creating player: {name} with strategy: {strategy}")
    
    data = {
        "name": name,
        "strategy": strategy
    }
    
    response = requests.post(f"{BASE_URL}/players", json=data)
    pretty_print_response(response)
    
    if response.ok:
        player_data = response.json()
        player_id = player_data.get("id")
        player_ids[name] = player_id
        auth_tokens[name] = player_data.get("auth_token")
        print(f"Player created with ID: {player_id}")
        return player_id
    return None

def test_get_players():
    """Test getting all players"""
    print("\n🔍 Getting all players")
    response = requests.get(f"{BASE_URL}/players")
    pretty_print_response(response)
    return response.ok

def test_get_player(player_id):
    """Test getting a specific player"""
    print(f"\n🔍 Getting player with ID: {player_id}")
    response = requests.get(f"{BASE_URL}/players/{player_id}")
    pretty_print_response(response)
    return response.ok

def test_create_game(player_id, name=None):
    """Test creating a new game"""
    global game_id
    
    if name is None:
        name = f"Game_{uuid.uuid4().hex[:8]}"
    
    print(f"\n🔍 Creating game: {name} with host player ID: {player_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return None
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return None
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    data = {
        "name": name,
        "max_players": 4,
        "initial_stack": 1000,
        "small_blind": 10,
        "big_blind": 20
    }
    
    response = requests.post(f"{BASE_URL}/games", json=data, headers=headers)
    pretty_print_response(response)
    
    if response.ok:
        game_data = response.json()
        game_id = game_data.get("id")
        print(f"Game created with ID: {game_id}")
        return game_id
    return None

def test_get_games():
    """Test getting all games"""
    print("\n🔍 Getting all games")
    response = requests.get(f"{BASE_URL}/games")
    pretty_print_response(response)
    return response.ok

def test_get_game(game_id):
    """Test getting a specific game"""
    print(f"\n🔍 Getting game with ID: {game_id}")
    response = requests.get(f"{BASE_URL}/games/{game_id}")
    pretty_print_response(response)
    return response.ok

def test_join_game(game_id, player_id):
    """Test joining a game"""
    print(f"\n🔍 Player {player_id} joining game {game_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return False
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/join", headers=headers)
    pretty_print_response(response)
    return response.ok

def test_start_game(game_id, player_id):
    """Test starting a game"""
    print(f"\n🔍 Starting game {game_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return False
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/start", headers=headers)
    pretty_print_response(response)
    return response.ok

def test_game_state(game_id, player_id):
    """Test getting the game state"""
    print(f"\n🔍 Getting game state for game {game_id} as player {player_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return False
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{BASE_URL}/games/{game_id}/state", headers=headers)
    pretty_print_response(response)
    return response.ok

def test_player_action(game_id, player_id, action, amount=None):
    """Test performing a player action (check, fold, call, raise)"""
    print(f"\n🔍 Player {player_id} performing action: {action} in game {game_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return False
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    data = {"action": action}
    if amount is not None and action in ["raise", "bet"]:
        data["amount"] = amount
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/action", json=data, headers=headers)
    pretty_print_response(response)
    return response.ok

def test_learning_progress(player_id):
    """Test getting a player's learning progress"""
    print(f"\n🔍 Getting learning progress for player {player_id}")
    
    # Find the player name for this ID to get auth token
    player_name = None
    for name, pid in player_ids.items():
        if pid == player_id:
            player_name = name
            break
    
    if player_name is None:
        print("❌ Cannot find player name for the given ID")
        return False
    
    auth_token = auth_tokens.get(player_name)
    if auth_token is None:
        print("❌ No auth token available for this player")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{BASE_URL}/learning/progress/{player_id}", headers=headers)
    pretty_print_response(response)
    return response.ok

def test_websocket_connection(game_id, player_id):
    """Test WebSocket connection for real-time game updates"""
    print(f"\n🔍 Testing WebSocket connection for game {game_id} as player {player_id}")
    
    try:
        # Import websocket library if available
        import websocket
        
        def on_message(ws, message):
            print(f"\n=== WebSocket Message ===")
            try:
                print(json.dumps(json.loads(message), indent=2))
            except:
                print(message)
            print("========================\n")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            print("WebSocket connection established")
            
            # Send a test message
            test_msg = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            ws.send(json.dumps(test_msg))
        
        websocket_url = f"ws://localhost:8080/api/ws/games/{game_id}?player_id={player_id}"
        ws = websocket.WebSocketApp(websocket_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Run the WebSocket connection in a separate thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Keep the connection open for a few seconds to receive messages
        print("WebSocket connection opened, waiting for messages...")
        time.sleep(5)
        ws.close()
        
        return True
    except ImportError:
        print("❌ websocket-client library not installed. Run 'pip install websocket-client' to test WebSocket functionality.")
        return False

def display_menu():
    """Display the main menu"""
    print("\n==== Poker Learning App API Testing Menu ====")
    print("1. Test root endpoint")
    print("2. Test API docs")
    print("3. Create new player")
    print("4. Get all players")
    print("5. Get specific player")
    print("6. Create new game")
    print("7. Get all games")
    print("8. Get specific game")
    print("9. Join game")
    print("10. Start game")
    print("11. Get game state")
    print("12. Perform player action")
    print("13. Get learning progress")
    print("14. Test WebSocket connection")
    print("15. Run full end-to-end test")
    print("0. Exit")
    print("==========================================")

def main():
    """Main function to run the testing script"""
    while True:
        display_menu()
        choice = input("Enter your choice (0-15): ")
        
        try:
            choice = int(choice)
        except ValueError:
            print("❌ Please enter a valid number")
            continue
        
        if choice == 0:
            print("Exiting...")
            sys.exit(0)
        
        elif choice == 1:
            test_root()
        
        elif choice == 2:
            test_api_docs()
        
        elif choice == 3:
            name = input("Enter player name (leave blank for random): ")
            if not name:
                name = None
            
            print("Available strategies: probability_based, conservative, risk_taker, bluffer")
            strategy = input("Enter strategy (leave blank for probability_based): ")
            if not strategy:
                strategy = None
            
            test_create_player(name, strategy)
        
        elif choice == 4:
            test_get_players()
        
        elif choice == 5:
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID: ")
            test_get_player(player_id)
        
        elif choice == 6:
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter host player ID: ")
            name = input("Enter game name (leave blank for random): ")
            if not name:
                name = None
            
            test_create_game(player_id, name)
        
        elif choice == 7:
            test_get_games()
        
        elif choice == 8:
            if game_id is None:
                game_id_input = input("Enter game ID: ")
                test_get_game(game_id_input)
            else:
                print(f"Using current game ID: {game_id}")
                test_get_game(game_id)
        
        elif choice == 9:
            if game_id is None:
                print("❌ No game created yet. Create a game first.")
                continue
            
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID to join the game: ")
            test_join_game(game_id, player_id)
        
        elif choice == 10:
            if game_id is None:
                print("❌ No game created yet. Create a game first.")
                continue
            
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter host player ID to start the game: ")
            test_start_game(game_id, player_id)
        
        elif choice == 11:
            if game_id is None:
                print("❌ No game created yet. Create a game first.")
                continue
            
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID to view game state: ")
            test_game_state(game_id, player_id)
        
        elif choice == 12:
            if game_id is None:
                print("❌ No game created yet. Create a game first.")
                continue
            
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID to perform action: ")
            
            print("Available actions: check, fold, call, raise, bet")
            action = input("Enter action: ")
            
            amount = None
            if action.lower() in ["raise", "bet"]:
                amount = int(input("Enter amount: "))
            
            test_player_action(game_id, player_id, action, amount)
        
        elif choice == 13:
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID to view learning progress: ")
            test_learning_progress(player_id)
        
        elif choice == 14:
            if game_id is None:
                print("❌ No game created yet. Create a game first.")
                continue
            
            if not player_ids:
                print("❌ No players created yet. Create a player first.")
                continue
            
            print("Available players:")
            for name, pid in player_ids.items():
                print(f"- {name}: {pid}")
            
            player_id = input("Enter player ID to establish WebSocket connection: ")
            test_websocket_connection(game_id, player_id)
        
        elif choice == 15:
            print("\n🔍 Running full end-to-end test")
            
            # Test root
            test_root()
            
            # Test API docs
            test_api_docs()
            
            # Create host player
            host_id = test_create_player("Host_Player", "probability_based")
            
            # Create AI players
            ai1_id = test_create_player("AI_Player_1", "conservative")
            ai2_id = test_create_player("AI_Player_2", "risk_taker")
            ai3_id = test_create_player("AI_Player_3", "bluffer")
            
            # List all players
            test_get_players()
            
            # Create a game
            game_id = test_create_game(host_id, "Test Game")
            
            # List all games
            test_get_games()
            
            # Get game details
            test_get_game(game_id)
            
            # Join game with AI players
            test_join_game(game_id, ai1_id)
            test_join_game(game_id, ai2_id)
            test_join_game(game_id, ai3_id)
            
            # Start game
            test_start_game(game_id, host_id)
            
            # Get game state
            test_game_state(game_id, host_id)
            
            # Test WebSocket connection
            test_websocket_connection(game_id, host_id)
            
            print("\n✅ Full end-to-end test completed")
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)