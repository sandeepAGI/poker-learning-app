#!/usr/bin/env python3

import requests
import json
import time

def simulate_full_game():
    """Simulate a complete poker game from start to finish"""
    
    base_url = "http://localhost:8080"
    
    print('🎮 Starting complete poker game simulation...')
    
    try:
        # 1. Create player
        print('\n1️⃣ Creating player...')
        player_response = requests.post(
            f"{base_url}/api/v1/players",
            json={"username": "GameSimulator", "settings": {"level": "beginner"}},
            headers={"Content-Type": "application/json"}
        )
        player_response.raise_for_status()
        player_data = player_response.json()
        token = player_data["access_token"]
        player_id = player_data["player_id"]
        print(f'   Player created: {player_data["username"]} (ID: {player_id})')
        
        # 2. Create game
        print('\n2️⃣ Creating game...')
        game_response = requests.post(
            f"{base_url}/api/v1/games",
            json={
                "ai_count": 3, 
                "ai_personalities": ["Conservative", "Probability-Based", "Bluffer"]
            },
            headers={
                "Content-Type": "application/json",
                "X-API-Key": token
            }
        )
        game_response.raise_for_status()
        game_data = game_response.json()
        game_id = game_data["game_id"]
        print(f'   Game created: {game_id}')
        print(f'   Players: {len(game_data["players"])} (1 human + {len(game_data["players"])-1} AI)')
        
        # 3. Play through the hand
        print('\n3️⃣ Playing poker hand...')
        hand_count = 0
        max_hands = 5  # Limit to prevent infinite loops
        
        while hand_count < max_hands:
            hand_count += 1
            print(f'\n   🃏 Hand #{hand_count}')
            
            # Get current game state
            state_response = requests.get(
                f"{base_url}/api/v1/games/{game_id}",
                headers={"X-API-Key": token}
            )
            state_response.raise_for_status()
            game_state = state_response.json()
            
            print(f'   State: {game_state["current_state"]}')
            print(f'   Community cards: {game_state.get("community_cards", [])}')
            print(f'   Pot: ${game_state["pot"]}')
            
            # Check if it's our turn and we have available actions
            current_player = game_state.get("current_player")
            if current_player == player_id:
                available_actions = game_state.get("available_actions", [])
                print(f'   Your turn! Available actions: {available_actions}')
                
                # Choose action (simple strategy: call if possible, otherwise fold)
                if "call" in available_actions:
                    action = "call"
                    amount = game_state.get("current_bet", 0)
                elif "check" in available_actions:
                    action = "check"
                    amount = 0
                else:
                    action = "fold"
                    amount = 0
                
                print(f'   Taking action: {action} (amount: {amount})')
                
                # Make the action
                action_response = requests.post(
                    f"{base_url}/api/v1/games/{game_id}/actions",
                    json={
                        "player_id": player_id, 
                        "action_type": action, 
                        "amount": amount
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": token
                    }
                )
                action_response.raise_for_status()
                action_data = action_response.json()
                print(f'   Action result: {action_data["action_result"]}')
                
                # Check if showdown
                if action_data.get("is_showdown"):
                    print('   🏆 Showdown reached!')
                    break
                    
            else:
                print(f'   Waiting for {current_player or "AI"} to act...')
                time.sleep(1)  # Give AI time to act
                
            # Check if hand is over
            if game_state["current_state"] == "showdown":
                print('   🏆 Hand completed - showdown!')
                
                # Try to advance to next hand
                print('   🔄 Advancing to next hand...')
                next_hand_response = requests.post(
                    f"{base_url}/api/v1/games/{game_id}/next-hand",
                    json={"player_id": player_id},
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": token
                    }
                )
                
                if next_hand_response.status_code == 200:
                    next_hand_data = next_hand_response.json()
                    print(f'   Next hand started: #{next_hand_data["hand_number"]}')
                else:
                    print(f'   Could not start next hand: {next_hand_response.status_code}')
                    break
            
            # Small delay to prevent hammering the API
            time.sleep(0.5)
        
        print(f'\n✅ Game simulation completed successfully!')
        print(f'   Hands played: {hand_count}')
        return True
        
    except requests.RequestException as e:
        print(f'\n❌ API request failed: {e}')
        if hasattr(e, 'response') and e.response:
            print(f'   Response status: {e.response.status_code}')
            print(f'   Response text: {e.response.text}')
        return False
    except Exception as e:
        print(f'\n❌ Game simulation failed: {e}')
        return False

if __name__ == '__main__':
    simulate_full_game()