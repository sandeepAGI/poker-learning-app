#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from test_client.poker_api_client import PokerAPIClient
import json

def test_frontend_integration():
    """Test complete frontend-backend integration flow"""
    
    client = PokerAPIClient()
    
    print('Testing complete frontend-backend integration flow...')
    
    try:
        # 1. Create player (simulating frontend registration)
        print('\n1. Creating player...')
        player_data = client.create_player('TestUser123', {'level': 'beginner'})
        print(f'Player created: {player_data["username"]} (ID: {player_data["player_id"]})')
        
        # 2. Create game (simulating frontend game creation)
        print('\n2. Creating game...')
        game_data = client.create_game(3, ['Conservative', 'Probability-Based', 'Bluffer'])
        print(f'Game created: {game_data["game_id"]} with {len(game_data["players"])} players')
        
        # 3. Make player action (simulating frontend gameplay)
        print('\n3. Making player action...')
        action_data = client.make_action(
            game_data['game_id'], 
            player_data['player_id'], 
            'call', 
            10
        )
        print(f'Action result: {action_data["action_result"]}')
        print(f'Game state: {action_data["updated_game_state"]["current_state"]}')
        print(f'Current player: {action_data["updated_game_state"]["current_player"]}')
        
        # 4. Check if game progressed to next round
        print('\n4. Game state after action:')
        print(f'Community cards: {action_data["updated_game_state"]["community_cards"]}')
        print(f'Pot size: {action_data["updated_game_state"]["pot"]}')
        
        # 5. Test getting game state
        print('\n5. Getting current game state...')
        game_state = client.get_game_state(game_data['game_id'])
        print(f'Current game state: {game_state["current_state"]}')
        print(f'Player cards visible: {game_state["players"][0]["visible_to_client"]}')
        
        print('\n✅ Frontend-backend integration test completed successfully!')
        return True
        
    except Exception as e:
        print(f'\n❌ Integration test failed: {e}')
        return False

if __name__ == '__main__':
    test_frontend_integration()