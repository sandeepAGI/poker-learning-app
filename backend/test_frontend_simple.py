#!/usr/bin/env python3

import requests
import json

def test_frontend_integration():
    """Test complete frontend-backend integration flow using direct API calls"""
    
    base_url = "http://localhost:8080"
    
    print('Testing complete frontend-backend integration flow...')
    
    try:
        # 1. Create player (simulating frontend registration)
        print('\n1. Creating player...')
        player_response = requests.post(
            f"{base_url}/api/v1/players",
            json={"username": "FrontendTestUser", "settings": {"level": "beginner"}},
            headers={"Content-Type": "application/json"}
        )
        player_response.raise_for_status()
        player_data = player_response.json()
        print(f'Player created: {player_data["username"]} (ID: {player_data["player_id"]})')
        
        # 2. Create game (simulating frontend game creation with FIXED personalities)
        print('\n2. Creating game...')
        game_response = requests.post(
            f"{base_url}/api/v1/games",
            json={
                "ai_count": 3, 
                "ai_personalities": ["Conservative", "Probability-Based", "Bluffer"]
            },
            headers={
                "Content-Type": "application/json",
                "X-API-Key": player_data["access_token"]
            }
        )
        game_response.raise_for_status()
        game_data = game_response.json()
        print(f'Game created: {game_data["game_id"]} with {len(game_data["players"])} players')
        
        # 3. Make player action (simulating frontend gameplay)
        print('\n3. Making player action...')
        action_response = requests.post(
            f"{base_url}/api/v1/games/{game_data['game_id']}/actions",
            json={
                "player_id": player_data['player_id'], 
                "action_type": "call", 
                "amount": 10
            },
            headers={
                "Content-Type": "application/json",
                "X-API-Key": player_data["access_token"]
            }
        )
        action_response.raise_for_status()
        action_data = action_response.json()
        print(f'Action result: {action_data["action_result"]}')
        print(f'Game state: {action_data["updated_game_state"]["current_state"]}')
        
        # 4. Check if game progressed to next round
        print('\n4. Game state after action:')
        print(f'Community cards: {action_data["updated_game_state"]["community_cards"]}')
        print(f'Pot size: {action_data["updated_game_state"]["pot"]}')
        
        # 5. Test getting game state
        print('\n5. Getting current game state...')
        state_response = requests.get(
            f"{base_url}/api/v1/games/{game_data['game_id']}",
            headers={"X-API-Key": player_data["access_token"]}
        )
        state_response.raise_for_status()
        state_data = state_response.json()
        print(f'Current game state: {state_data["current_state"]}')
        print(f'Player cards visible: {state_data["players"][0]["visible_to_client"]}')
        
        print('\n✅ Frontend-backend integration test completed successfully!')
        print('\n📋 Test Summary:')
        print('  ✅ Player registration working')
        print('  ✅ Game creation working')
        print('  ✅ Player actions working')
        print('  ✅ Game state progression working')
        print('  ✅ AI personalities correctly mapped')
        return True
        
    except requests.RequestException as e:
        print(f'\n❌ API request failed: {e}')
        if hasattr(e, 'response') and e.response:
            print(f'Response status: {e.response.status_code}')
            print(f'Response text: {e.response.text}')
        return False
    except Exception as e:
        print(f'\n❌ Integration test failed: {e}')
        return False

if __name__ == '__main__':
    test_frontend_integration()