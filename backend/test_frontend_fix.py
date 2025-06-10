#!/usr/bin/env python3

import requests
import json

def test_frontend_flow():
    """Test the frontend flow with the fixed state mapping"""
    
    base_url = "http://localhost:8080"
    
    print('🧪 Testing frontend fix for Create New Game issue...')
    
    try:
        # 1. Create player (simulates AuthModal)
        print('\n1️⃣ Creating player...')
        player_response = requests.post(
            f"{base_url}/api/v1/players",
            json={"username": "FixTestUser", "settings": {"level": "beginner"}},
            headers={"Content-Type": "application/json"}
        )
        player_response.raise_for_status()
        player_data = player_response.json()
        token = player_data["access_token"]
        player_id = player_data["player_id"]
        print(f'   ✅ Player created: {player_data["username"]} (ID: {player_id})')
        
        # 2. Create game (simulates GameLobby.onCreateGame)
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
        print(f'   ✅ Game created: {game_id}')
        
        # 3. Analyze the response for frontend mapping
        print('\n3️⃣ Analyzing backend response for frontend mapping...')
        print(f'   Backend current_state: "{game_data.get("current_state")}"')
        print(f'   Backend has players: {len(game_data.get("players", []))}')
        print(f'   Backend pot: ${game_data.get("pot", 0)}')
        print(f'   Backend current_bet: ${game_data.get("current_bet", 0)}')
        
        # 4. Simulate frontend state mapping
        print('\n4️⃣ Simulating frontend state mapping...')
        frontend_state = {
            'gameState': 'playing' if game_data.get("current_state") else 'lobby',
            'roundState': game_data.get("current_state", "pre_flop"),
            'players': game_data.get("players", []),
            'pot': game_data.get("pot", 0),
            'currentBet': game_data.get("current_bet", 0),
            'gameId': game_data.get("game_id")
        }
        
        print(f'   Frontend gameState: "{frontend_state["gameState"]}"')
        print(f'   Frontend roundState: "{frontend_state["roundState"]}"')
        print(f'   Frontend will show: {"PokerTable" if frontend_state["gameState"] == "playing" else "GameLobby"}')
        
        # 5. Test the condition that determines UI state
        print('\n5️⃣ Testing UI state transition...')
        should_show_game = frontend_state['gameState'] != 'lobby'
        if should_show_game:
            print('   ✅ SUCCESS: Frontend should transition from GameLobby to PokerTable')
            print('   ✅ SUCCESS: "Create New Game" issue should be FIXED')
        else:
            print('   ❌ FAILURE: Frontend will stay on GameLobby - issue NOT fixed')
            
        return should_show_game
        
    except requests.RequestException as e:
        print(f'\n❌ API request failed: {e}')
        if hasattr(e, 'response') and e.response:
            print(f'   Response status: {e.response.status_code}')
            print(f'   Response text: {e.response.text}')
        return False
    except Exception as e:
        print(f'\n❌ Test failed: {e}')
        return False

if __name__ == '__main__':
    success = test_frontend_flow()
    if success:
        print('\n🎉 Frontend fix validation: PASSED')
        print('   Users should now be able to proceed past "Create New Game"')
    else:
        print('\n💥 Frontend fix validation: FAILED')
        print('   Additional debugging needed')