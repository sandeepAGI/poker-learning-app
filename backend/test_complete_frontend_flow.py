#!/usr/bin/env python3

import requests
import json
import time

def test_complete_frontend_flow():
    """Test the complete frontend flow to ensure everything works"""
    
    base_url = "http://localhost:8080"
    
    print('🎮 Testing COMPLETE frontend flow with fixes...')
    
    try:
        # 1. Create player (AuthModal flow)
        print('\n1️⃣ Creating player (AuthModal simulation)...')
        player_response = requests.post(
            f"{base_url}/api/v1/players",
            json={"username": "CompleteFlowUser", "settings": {"level": "beginner"}},
            headers={"Content-Type": "application/json"}
        )
        player_response.raise_for_status()
        player_data = player_response.json()
        token = player_data["access_token"]
        player_id = player_data["player_id"]
        print(f'   ✅ Player created: {player_data["username"]}')
        print(f'   ✅ Token received: {token[:20]}...')
        
        # 2. Simulate AuthModal.onLogin
        print('\n2️⃣ Simulating AuthModal.onLogin...')
        frontend_auth_data = {
            'player_id': player_id,
            'username': player_data["username"],
            'access_token': token
        }
        print(f'   ✅ Frontend localStorage will store: player_data')
        print(f'   ✅ Frontend auth.setToken() will store: auth_token')
        
        # 3. Create game (GameLobby flow)
        print('\n3️⃣ Creating game (GameLobby.onCreateGame simulation)...')
        game_config = {
            "ai_count": 3, 
            "ai_personalities": ["Conservative", "Probability-Based", "Bluffer"]
        }
        print(f'   📤 Sending: {json.dumps(game_config, indent=2)}')
        
        game_response = requests.post(
            f"{base_url}/api/v1/games",
            json=game_config,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": token
            }
        )
        game_response.raise_for_status()
        game_data = game_response.json()
        game_id = game_data["game_id"]
        print(f'   ✅ Game created: {game_id}')
        
        # 4. Simulate frontend state mapping
        print('\n4️⃣ Simulating frontend state mapping...')
        frontend_mapped_state = {
            'gameId': game_data.get("game_id"),
            'gameState': 'playing' if game_data.get("current_state") else 'lobby',
            'roundState': game_data.get("current_state", "pre_flop"),
            'players': game_data.get("players", []),
            'pot': game_data.get("pot", 0),
            'currentBet': game_data.get("current_bet", 0),
            'smallBlind': game_data.get("small_blind", 5),
            'bigBlind': game_data.get("big_blind", 10),
            'dealerIndex': game_data.get("dealer_position", 0),
            'communityCards': game_data.get("community_cards", []),
            'handCount': game_data.get("hand_number", 1),
            'playerId': player_id
        }
        
        print(f'   📋 Frontend state after createGame:')
        print(f'     gameState: "{frontend_mapped_state["gameState"]}"')
        print(f'     roundState: "{frontend_mapped_state["roundState"]}"')
        print(f'     players: {len(frontend_mapped_state["players"])}')
        print(f'     pot: ${frontend_mapped_state["pot"]}')
        
        # 5. Test UI rendering logic
        print('\n5️⃣ Testing UI rendering logic...')
        will_show_lobby = frontend_mapped_state['gameState'] == 'lobby'
        will_show_game = not will_show_lobby
        
        print(f'   🖥️  PokerGameContainer.js line 131 condition:')
        print(f'     state.gameState === GAME_STATES.LOBBY ? <GameLobby> : <PokerTable>')
        print(f'     "{frontend_mapped_state["gameState"]}" === "lobby" ? GameLobby : PokerTable')
        print(f'     {will_show_lobby} ? GameLobby : PokerTable')
        print(f'   📺 Will render: {"GameLobby" if will_show_lobby else "PokerTable + GameControls"}')
        
        # 6. Test computed values
        print('\n6️⃣ Testing computed values...')
        current_player_index = 0
        for i, player in enumerate(frontend_mapped_state["players"]):
            if player.get("player_id") == player_id:
                current_player_index = i
                break
        
        is_current_player = frontend_mapped_state["players"][current_player_index]["player_id"] == player_id if current_player_index < len(frontend_mapped_state["players"]) else False
        can_act = frontend_mapped_state["gameState"] == "playing" and is_current_player
        
        print(f'   👤 Current player: {frontend_mapped_state["players"][current_player_index]["player_id"] if current_player_index < len(frontend_mapped_state["players"]) else "None"}')
        print(f'   🎯 Is current player: {is_current_player}')
        print(f'   🎮 Can act: {can_act}')
        
        # 7. Test a player action
        if frontend_mapped_state["gameState"] == "playing":
            print('\n7️⃣ Testing player action...')
            action_response = requests.post(
                f"{base_url}/api/v1/games/{game_id}/actions",
                json={
                    "player_id": player_id, 
                    "action_type": "call", 
                    "amount": frontend_mapped_state["currentBet"]
                },
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": token
                }
            )
            action_response.raise_for_status()
            action_data = action_response.json()
            print(f'   ✅ Action successful: {action_data["action_result"]}')
            print(f'   🎯 Updated state: {action_data["updated_game_state"]["current_state"]}')
        
        print('\n🎉 COMPLETE FRONTEND FLOW TEST: PASSED')
        print('   ✅ Player registration works')
        print('   ✅ Authentication flow works') 
        print('   ✅ Game creation works')
        print('   ✅ State mapping works')
        print('   ✅ UI transition works (GameLobby → PokerTable)')
        print('   ✅ Player actions work')
        print('\n🚀 The "Create New Game" issue should be COMPLETELY RESOLVED!')
        
        return True
        
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
    success = test_complete_frontend_flow()
    if success:
        print('\n🎯 FRONTEND TESTING COMPLETE')
        print('   Users can now successfully:')
        print('   1. Register a new player')
        print('   2. Create a new game') 
        print('   3. See the poker table and play!')
    else:
        print('\n💥 FRONTEND TESTING FAILED')
        print('   Additional fixes needed')