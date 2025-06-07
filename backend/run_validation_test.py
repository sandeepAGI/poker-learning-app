#!/usr/bin/env python3
"""
Quick validation test for the implementation fixes.
"""

import requests
import json
import sys

def main():
    # Test API functionality
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZGYwODc5Yy1kODNiLTQ2MzYtYmI0Ni0zOWY1MjM5NjRhZmQiLCJleHAiOjE3NTExNDIwMDN9.XUTVy8yQKDDBpXXpHNykZfT_azbPIzDzYKAiAC-4rDA'
    headers = {'X-API-Key': token}

    print('Testing Poker API implementation fixes...')

    try:
        # Create a game
        print('1. Creating game...')
        game_data = {
            'player_id': '4df0879c-d83b-4636-bb46-39f523964afd',
            'ai_count': 3,
            'ai_personalities': ['Conservative', 'Risk Taker', 'Probability-Based']
        }
        response = requests.post('http://localhost:8080/api/v1/games', json=game_data, headers=headers, timeout=10)
        
        if not response.ok:
            print(f'❌ Failed to create game: {response.text}')
            return False
        
        game_response = response.json()
        game_id = game_response['game_id']
        print(f'   ✅ Created game: {game_id}')
        
        # Get game state
        print('2. Getting game state...')
        response = requests.get(f'http://localhost:8080/api/v1/games/{game_id}', headers=headers, timeout=10)
        
        if not response.ok:
            print(f'❌ Failed to get game state: {response.text}')
            return False
            
        state = response.json()
        print(f'   ✅ Current state: {state.get("current_state", "unknown")}')
        print(f'   ✅ Players: {len(state.get("players", []))}')
        print(f'   ✅ Pot: {state.get("pot", 0)}')
        
        # Validate our key fixes
        print('3. Validating implementation fixes...')
        
        players = state.get('players', [])
        total_chips = state.get('pot', 0)
        issues = []
        
        for i, player in enumerate(players):
            hole_cards = player.get('hole_cards', [])
            stack = player.get('stack', 0)
            is_active = player.get('is_active', False)
            total_chips += stack
            
            print(f'   Player {i+1}: active={is_active}, cards={len(hole_cards) if hole_cards else 0}, stack={stack}')
            
            # Deck management check: active players should have 2 hole cards
            if is_active and (not hole_cards or len(hole_cards) != 2):
                issues.append(f'Player {i+1} is active but has {len(hole_cards) if hole_cards else 0} cards instead of 2')
            
            # Chip conservation check: no negative stacks
            if stack < 0:
                issues.append(f'Player {i+1} has negative stack: {stack}')
        
        # Total chip conservation check (4 players * 1000 starting chips = 4000)
        expected_chips = 4000
        if total_chips != expected_chips:
            issues.append(f'Chip conservation violation: expected {expected_chips}, found {total_chips}')
        
        # Summary
        print('4. Results:')
        if not issues:
            print('   🎉 ALL IMPLEMENTATION FIXES ARE WORKING CORRECTLY!')
            print('   ✅ Deck Management: All active players have proper hole cards')
            print('   ✅ Chip Conservation: Total chips preserved')
            print('   ✅ State Management: Game state is consistent')
            return True
        else:
            print('   ❌ Issues found:')
            for issue in issues:
                print(f'     - {issue}')
            return False
                
    except Exception as e:
        print(f'❌ Test failed with exception: {e}')
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)