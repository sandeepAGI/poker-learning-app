import { mapBackendResponse, GAME_STATES, ROUND_STATES } from './gameStore';

describe('mapBackendResponse - Critical Function Analysis', () => {
  
  describe('PLAYING State Scenarios', () => {
    test('should return PLAYING state for normal game with active players', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 950, current_bet: 50, status: 'active' },
          { player_id: 'p2', name: 'AI1', chips: 950, current_bet: 50, status: 'active' }
        ],
        pot: 100,
        current_bet: 50,
        current_state: 'pre_flop',
        current_player: 'p2',
        community_cards: [],
        hand_number: 1
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.players).toHaveLength(2);
      expect(result.pot).toBe(100);
      expect(result.roundState).toBe('pre_flop');
    });

    test('should return PLAYING state even with no current_state field', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' }
        ],
        pot: 50
        // Note: no current_state field
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.roundState).toBe(ROUND_STATES.PRE_FLOP); // default
    });

    test('should return PLAYING state for game in progress (flop)', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 900, current_bet: 0, status: 'active' },
          { player_id: 'p2', name: 'AI1', chips: 900, current_bet: 0, status: 'active' }
        ],
        pot: 200,
        current_bet: 0,
        current_state: 'flop',
        community_cards: ['As', 'Kh', '2d']
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.roundState).toBe('flop');
      expect(result.communityCards).toEqual(['As', 'Kh', '2d']);
    });

    test('should return PLAYING state for showdown', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 800, status: 'active' },
          { player_id: 'p2', name: 'AI1', chips: 1200, status: 'active' }
        ],
        pot: 0,
        current_state: 'showdown',
        community_cards: ['As', 'Kh', '2d', 'Qc', 'Jh']
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.roundState).toBe('showdown');
    });
  });

  describe('LOBBY State Scenarios', () => {
    test('should return LOBBY state when current_state is finished', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 2000, status: 'active' }
        ],
        pot: 0,
        current_state: 'finished'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('should return LOBBY state when game_status is finished', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 2000, status: 'active' }
        ],
        pot: 0,
        game_status: 'finished'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('should return LOBBY state when no players', () => {
      const response = {
        players: [],
        pot: 0,
        current_state: 'pre_flop'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('should return LOBBY state when players is null', () => {
      const response = {
        players: null,
        pot: 0,
        current_state: 'pre_flop'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('should return LOBBY state when players is undefined', () => {
      const response = {
        pot: 0,
        current_state: 'pre_flop'
        // players is undefined
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Real Backend Response Scenarios', () => {
    test('should handle actual backend response from successful raise action', () => {
      // This is based on the actual backend logs from the user's issue
      const realBackendResponse = {
        players: [
          { 
            player_id: 'de799935-0c0f-481b-ace2-318ba3f9d14f', 
            name: 'Sandeep', 
            chips: 980, 
            current_bet: 20, 
            status: 'active',
            hole_cards: ['7d', 'Kc'],
            is_active: true
          },
          { 
            player_id: 'ai_0', 
            name: 'Probability-Based', 
            chips: 995, 
            current_bet: 5, 
            status: 'active',
            is_active: true
          },
          { 
            player_id: 'ai_1', 
            name: 'Bluffer', 
            chips: 990, 
            current_bet: 10, 
            status: 'active',
            is_active: true
          },
          { 
            player_id: 'ai_2', 
            name: 'Conservative', 
            chips: 970, 
            current_bet: 30, 
            status: 'active',
            is_active: true
          }
        ],
        pot: 65,
        current_bet: 30,
        current_state: 'pre_flop',
        current_player: 'de799935-0c0f-481b-ace2-318ba3f9d14f',
        community_cards: [],
        hand_number: 1,
        small_blind: 5,
        big_blind: 10,
        dealer_position: 1
      };
      
      const result = mapBackendResponse(realBackendResponse);
      
      // This should be PLAYING, not LOBBY
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.players).toHaveLength(4);
      expect(result.pot).toBe(65);
      expect(result.currentBet).toBe(30);
      expect(result.roundState).toBe('pre_flop');
      expect(result.dealerIndex).toBe(1);
      
      // Verify current player index calculation
      const expectedCurrentPlayerIndex = result.players.findIndex(
        p => p.player_id === 'de799935-0c0f-481b-ace2-318ba3f9d14f'
      );
      expect(result.currentPlayerIndex).toBe(expectedCurrentPlayerIndex);
    });

    test('should handle backend response with minimal fields', () => {
      const minimalResponse = {
        players: [{ player_id: 'p1', name: 'Player1' }]
      };
      
      const result = mapBackendResponse(minimalResponse);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.pot).toBe(0); // default
      expect(result.currentBet).toBe(0); // default
      expect(result.smallBlind).toBe(5); // default
      expect(result.bigBlind).toBe(10); // default
      expect(result.communityCards).toEqual([]); // default
      expect(result.handCount).toBe(1); // default
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle empty response object', () => {
      const result = mapBackendResponse({});
      
      expect(result.gameState).toBe(GAME_STATES.LOBBY); // no players
      expect(result.players).toEqual([]);
      expect(result.pot).toBe(0);
    });

    test('should handle null response', () => {
      const result = mapBackendResponse(null);
      
      // Should not crash
      expect(result.gameState).toBe(GAME_STATES.LOBBY);
      expect(result.players).toEqual([]);
    });

    test('should handle response with mixed player field names', () => {
      const response = {
        players: [
          { id: 'p1', name: 'Player1', chips: 1000 }, // uses 'id'
          { player_id: 'p2', name: 'Player2', chips: 1000 } // uses 'player_id'
        ],
        current_player: 'p1'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      
      // Should find current player by either id or player_id
      const currentPlayerIndex = result.currentPlayerIndex;
      expect(currentPlayerIndex).toBeGreaterThanOrEqual(0);
    });

    test('should handle response with invalid current_player', () => {
      const response = {
        players: [
          { player_id: 'p1', name: 'Player1', chips: 1000 },
          { player_id: 'p2', name: 'Player2', chips: 1000 }
        ],
        current_player: 'nonexistent_player'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      expect(result.currentPlayerIndex).toBe(0); // defaults to 0 when not found
    });
  });

  describe('Field Mapping Verification', () => {
    test('should map all backend fields correctly', () => {
      const response = {
        players: [{ player_id: 'p1', name: 'Player1' }],
        pot: 150,
        current_bet: 50,
        small_blind: 5,
        big_blind: 10,
        dealer_position: 2,
        community_cards: ['As', 'Kh'],
        hand_number: 5,
        current_state: 'turn',
        current_player: 'p1'
      };
      
      const result = mapBackendResponse(response);
      
      expect(result.pot).toBe(150);
      expect(result.currentBet).toBe(50);
      expect(result.smallBlind).toBe(5);
      expect(result.bigBlind).toBe(10);
      expect(result.dealerIndex).toBe(2);
      expect(result.communityCards).toEqual(['As', 'Kh']);
      expect(result.handCount).toBe(5);
      expect(result.roundState).toBe('turn');
      expect(result.currentPlayerIndex).toBe(0); // p1 is at index 0
    });
  });

  describe('CRITICAL: The Lobby Redirect Bug Investigation', () => {
    test('should NOT return LOBBY for typical action response', () => {
      // This tests the exact scenario causing the bug
      const typicalActionResponse = {
        players: [
          { player_id: 'human', name: 'Human Player', chips: 950, status: 'active' },
          { player_id: 'ai1', name: 'AI Player', chips: 1050, status: 'active' }
        ],
        pot: 100,
        current_bet: 50,
        current_state: 'pre_flop' // This is NOT 'finished'
        // game_status is not set
      };
      
      const result = mapBackendResponse(typicalActionResponse);
      
      // THIS IS THE CRITICAL TEST - should be PLAYING, not LOBBY
      expect(result.gameState).toBe(GAME_STATES.PLAYING);
      
      // If this test fails, we found the bug in mapBackendResponse
      // If this test passes, the bug is elsewhere (likely in the reducer)
    });

    test('should identify what makes a response trigger LOBBY state', () => {
      // Test each condition that could cause LOBBY state
      
      // Case 1: No players
      expect(mapBackendResponse({ players: [] }).gameState).toBe(GAME_STATES.LOBBY);
      expect(mapBackendResponse({ players: null }).gameState).toBe(GAME_STATES.LOBBY);
      expect(mapBackendResponse({}).gameState).toBe(GAME_STATES.LOBBY);
      
      // Case 2: Game finished
      expect(mapBackendResponse({ 
        players: [{ player_id: 'p1' }], 
        current_state: 'finished' 
      }).gameState).toBe(GAME_STATES.LOBBY);
      
      expect(mapBackendResponse({ 
        players: [{ player_id: 'p1' }], 
        game_status: 'finished' 
      }).gameState).toBe(GAME_STATES.LOBBY);
      
      // Case 3: Valid game should be PLAYING
      expect(mapBackendResponse({ 
        players: [{ player_id: 'p1' }], 
        current_state: 'pre_flop' 
      }).gameState).toBe(GAME_STATES.PLAYING);
      
      expect(mapBackendResponse({ 
        players: [{ player_id: 'p1' }] 
        // no current_state - should default to PLAYING
      }).gameState).toBe(GAME_STATES.PLAYING);
    });
  });
});