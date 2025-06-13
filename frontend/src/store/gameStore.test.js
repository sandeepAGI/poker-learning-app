import React from 'react';
import { render, act } from '@testing-library/react';
import { GameProvider, useGame, GAME_STATES, ROUND_STATES } from './gameStore';

// Mock the API client
jest.mock('../services/apiClient', () => ({
  gameApi: {
    createGame: jest.fn(),
    submitAction: jest.fn(),
    getGameState: jest.fn(),
    nextHand: jest.fn()
  }
}));

// Mock WebSocket manager
jest.mock('../services/websocketManager', () => ({
  default: {
    sendPlayerAction: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn()
  },
  EVENT_TYPES: {
    GAME_UPDATE: 'game_update',
    PLAYER_ACTION: 'player_action'
  },
  CONNECTION_STATES: {
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    RECONNECTING: 'reconnecting',
    ERROR: 'error'
  }
}));

describe('GameStore', () => {
  let TestComponent;
  let gameActions;
  let gameState;

  beforeEach(() => {
    TestComponent = () => {
      const { state, actions } = useGame();
      gameActions = actions;
      gameState = state;
      return <div data-testid="test-component">Test</div>;
    };
  });

  const renderWithProvider = () => {
    return render(
      <GameProvider>
        <TestComponent />
      </GameProvider>
    );
  };

  describe('Initial State', () => {
    test('should have correct initial state', () => {
      renderWithProvider();
      
      expect(gameState.gameId).toBeNull();
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
      expect(gameState.roundState).toBe(ROUND_STATES.PRE_FLOP);
      expect(gameState.playerId).toBeNull();
      expect(gameState.playerName).toBeNull();
      expect(gameState.isAuthenticated).toBe(false);
      expect(gameState.players).toEqual([]);
      expect(gameState.pot).toBe(0);
      expect(gameState.loading).toBe(false);
      expect(gameState.error).toBeNull();
    });
  });

  describe('Player Actions', () => {
    test('setPlayer should authenticate user and set player data', () => {
      renderWithProvider();
      
      act(() => {
        gameActions.setPlayer('player123', 'TestPlayer');
      });
      
      expect(gameState.playerId).toBe('player123');
      expect(gameState.playerName).toBe('TestPlayer');
      expect(gameState.isAuthenticated).toBe(true);
      expect(gameState.error).toBeNull();
    });

    test('clearPlayer should reset authentication', () => {
      renderWithProvider();
      
      // First set a player
      act(() => {
        gameActions.setPlayer('player123', 'TestPlayer');
      });
      
      // Then clear
      act(() => {
        gameActions.clearPlayer();
      });
      
      expect(gameState.playerId).toBeNull();
      expect(gameState.playerName).toBeNull();
      expect(gameState.isAuthenticated).toBe(false);
      expect(gameState.gameId).toBeNull();
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Game State Updates - CRITICAL AREA', () => {
    test('UPDATE_GAME_STATE should preserve gameId when not provided', () => {
      renderWithProvider();
      
      // Set initial game ID
      act(() => {
        gameActions.setGameId('game123');
      });
      
      // Update state without gameId in payload
      act(() => {
        gameActions.updateGameState({
          pot: 100,
          players: [{ id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      expect(gameState.gameId).toBe('game123'); // Should preserve existing gameId
      expect(gameState.pot).toBe(100);
    });

    test('UPDATE_GAME_STATE should prevent lobby redirect when game is active', () => {
      renderWithProvider();
      
      // Start with playing state and players
      act(() => {
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [
            { id: 'p1', name: 'Player1', chips: 1000 },
            { id: 'p2', name: 'Player2', chips: 1000 }
          ]
        });
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      
      // Try to update with LOBBY state but still have players
      act(() => {
        gameActions.updateGameState({
          gameState: GAME_STATES.LOBBY, // This should be prevented
          players: [
            { id: 'p1', name: 'Player1', chips: 900 },
            { id: 'p2', name: 'Player2', chips: 1100 }
          ],
          pot: 200
        });
      });
      
      // Should stay in PLAYING state despite payload saying LOBBY
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.pot).toBe(200); // Other data should update
    });

    test('UPDATE_GAME_STATE should allow lobby redirect when no players', () => {
      renderWithProvider();
      
      // Start with playing state
      act(() => {
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      // Update with no players - should allow lobby
      act(() => {
        gameActions.updateGameState({
          gameState: GAME_STATES.LOBBY,
          players: []
        });
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Backend Response Mapping - CRITICAL AREA', () => {
    // We need to test the mapBackendResponse function with real backend responses
    
    test('mapBackendResponse should stay PLAYING with active players', () => {
      // Mock a typical backend response after an action
      const backendResponse = {
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
      
      renderWithProvider();
      
      act(() => {
        gameActions.updateGameStateFromBackend(backendResponse);
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.players).toHaveLength(2);
      expect(gameState.pot).toBe(100);
    });

    test('mapBackendResponse should go to LOBBY when game finished', () => {
      const finishedGameResponse = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 0, status: 'eliminated' }
        ],
        current_state: 'finished',
        pot: 0
      };
      
      renderWithProvider();
      
      act(() => {
        gameActions.updateGameStateFromBackend(finishedGameResponse);
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('mapBackendResponse should go to LOBBY when no players', () => {
      const noPlayersResponse = {
        players: [],
        pot: 0,
        current_state: 'pre_flop'
      };
      
      renderWithProvider();
      
      act(() => {
        gameActions.updateGameStateFromBackend(noPlayersResponse);
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Action Submission Flow - CRITICAL AREA', () => {
    const { gameApi } = require('../services/apiClient');
    
    beforeEach(() => {
      jest.clearAllMocks();
    });

    test('submitAction should maintain PLAYING state after successful action', async () => {
      // Mock successful API response
      const mockActionResponse = {
        players: [
          { player_id: 'p1', name: 'Human', chips: 900, current_bet: 100, status: 'active' },
          { player_id: 'p2', name: 'AI1', chips: 950, current_bet: 50, status: 'active' }
        ],
        pot: 150,
        current_bet: 100,
        current_state: 'pre_flop',
        current_player: 'p2'
      };
      
      gameApi.submitAction.mockResolvedValue(mockActionResponse);
      
      renderWithProvider();
      
      // Set up initial game state
      act(() => {
        gameActions.setPlayer('p1', 'Human');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [
            { player_id: 'p1', name: 'Human', chips: 1000 },
            { player_id: 'p2', name: 'AI1', chips: 1000 }
          ]
        });
      });
      
      // Submit raise action
      await act(async () => {
        await gameActions.submitAction('raise', 100);
      });
      
      // Should stay in PLAYING state
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.pot).toBe(150);
      expect(gameApi.submitAction).toHaveBeenCalledWith('game123', 'p1', {
        action_type: 'raise',
        amount: 100
      });
    });

    test('submitAction should handle errors gracefully', async () => {
      gameApi.submitAction.mockRejectedValue(new Error('Network error'));
      
      renderWithProvider();
      
      // Set up initial state
      act(() => {
        gameActions.setPlayer('p1', 'Human');
        gameActions.setGameId('game123');
      });
      
      // Submit action that fails
      await act(async () => {
        try {
          await gameActions.submitAction('fold');
        } catch (error) {
          // Expected to throw
        }
      });
      
      expect(gameState.error).toBe('Network error');
      expect(gameState.loading).toBe(false);
    });

    test('submitAction should fail if game or player not initialized', async () => {
      renderWithProvider();
      
      // Try to submit action without game/player setup
      await act(async () => {
        try {
          await gameActions.submitAction('fold');
          fail('Should have thrown error');
        } catch (error) {
          expect(error.message).toBe('Game or player not initialized');
        }
      });
    });
  });

  describe('Game Creation Flow', () => {
    const { gameApi } = require('../services/apiClient');
    
    test('createGame should transition from LOBBY to PLAYING', async () => {
      const mockGameResponse = {
        game_id: 'new-game-123',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' },
          { player_id: 'ai1', name: 'AI1', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop',
        pot: 15,
        current_bet: 10
      };
      
      gameApi.createGame.mockResolvedValue(mockGameResponse);
      
      renderWithProvider();
      
      // Set up authenticated player
      act(() => {
        gameActions.setPlayer('p1', 'Human');
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
      
      // Create game
      await act(async () => {
        await gameActions.createGame({ ai_count: 1, ai_personalities: ['Conservative'] });
      });
      
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.gameId).toBe('new-game-123');
      expect(gameState.players).toHaveLength(2);
    });
  });

  describe('Error Handling', () => {
    test('should set error state when actions fail', () => {
      renderWithProvider();
      
      act(() => {
        gameActions.setError('Test error message');
      });
      
      expect(gameState.error).toBe('Test error message');
    });

    test('should clear error state', () => {
      renderWithProvider();
      
      act(() => {
        gameActions.setError('Test error');
      });
      
      expect(gameState.error).toBe('Test error');
      
      act(() => {
        gameActions.clearError();
      });
      
      expect(gameState.error).toBeNull();
    });
  });
});

// Helper function to test mapBackendResponse directly
describe('mapBackendResponse function', () => {
  // We need to extract and test this function directly
  // This would require exporting it from gameStore.js or testing it indirectly
  
  test('should map backend response correctly', () => {
    // TODO: Extract mapBackendResponse function and test directly
    // This is critical for debugging the lobby redirect issue
  });
});