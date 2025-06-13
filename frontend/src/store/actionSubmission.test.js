import React from 'react';
import { render, act, waitFor } from '@testing-library/react';
import { GameProvider, useGame, GAME_STATES } from './gameStore';
import { gameApi } from '../services/apiClient';

// Mock the entire API client
jest.mock('../services/apiClient', () => ({
  gameApi: {
    submitAction: jest.fn(),
    createGame: jest.fn(),
    getGameState: jest.fn(),
    nextHand: jest.fn()
  }
}));

// Mock WebSocket manager
jest.mock('../services/websocketManager', () => ({
  default: {
    sendPlayerAction: jest.fn()
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

describe('Action Submission Flow - Root Cause Analysis', () => {
  let TestComponent;
  let gameActions;
  let gameState;

  beforeEach(() => {
    jest.clearAllMocks();
    
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

  describe('CRITICAL: Raise Action Flow', () => {
    test('should stay in PLAYING state after successful raise', async () => {
      // This is the exact scenario that's failing in the real app
      
      // Mock backend response after a raise action - based on real backend logs
      const raiseActionResponse = {
        players: [
          { 
            player_id: 'de799935-0c0f-481b-ace2-318ba3f9d14f', 
            name: 'Sandeep', 
            chips: 950, 
            current_bet: 50, 
            status: 'active',
            hole_cards: ['7d', 'Kc']
          },
          { 
            player_id: 'ai_0', 
            name: 'AI Probability-Based', 
            chips: 995, 
            current_bet: 5, 
            status: 'active' 
          },
          { 
            player_id: 'ai_1', 
            name: 'AI Bluffer', 
            chips: 990, 
            current_bet: 10, 
            status: 'active' 
          },
          { 
            player_id: 'ai_2', 
            name: 'AI Conservative', 
            chips: 970, 
            current_bet: 30, 
            status: 'active' 
          }
        ],
        pot: 95,
        current_bet: 50,
        current_state: 'pre_flop',
        current_player: 'ai_0',
        community_cards: [],
        hand_number: 1,
        dealer_position: 1
      };
      
      gameApi.submitAction.mockResolvedValue(raiseActionResponse);
      
      renderWithProvider();
      
      // Setup initial game state (user is authenticated and in active game)
      await act(async () => {
        gameActions.setPlayer('de799935-0c0f-481b-ace2-318ba3f9d14f', 'Sandeep');
        gameActions.setGameId('3088a947-2b9b-43d2-8ea4-35ded7cfe765');
        
        // Simulate being in an active game before the raise
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [
            { 
              player_id: 'de799935-0c0f-481b-ace2-318ba3f9d14f', 
              name: 'Sandeep', 
              chips: 1000, 
              current_bet: 0, 
              status: 'active' 
            },
            { 
              player_id: 'ai_0', 
              name: 'AI Probability-Based', 
              chips: 1000, 
              current_bet: 0, 
              status: 'active' 
            }
          ],
          pot: 15,
          currentBet: 10,
          roundState: 'pre_flop'
        });
      });
      
      // Verify we start in PLAYING state
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.players).toHaveLength(2);
      
      // Submit the raise action that's causing the problem
      await act(async () => {
        await gameActions.submitAction('raise', 50);
      });
      
      // CRITICAL: This should stay PLAYING, but it's going to LOBBY in real app
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.pot).toBe(95);
      expect(gameState.players).toHaveLength(4); // AI players were added by backend
      
      // Verify API was called correctly
      expect(gameApi.submitAction).toHaveBeenCalledWith(
        '3088a947-2b9b-43d2-8ea4-35ded7cfe765',
        'de799935-0c0f-481b-ace2-318ba3f9d14f',
        {
          action_type: 'raise',
          amount: 50
        }
      );
    });

    test('should handle backend response with missing gameState field', async () => {
      // Test edge case: backend doesn't explicitly set game_status or current_state
      const ambiguousResponse = {
        players: [
          { player_id: 'p1', name: 'Player1', chips: 950, status: 'active' }
        ],
        pot: 100,
        current_bet: 50
        // Note: no current_state or game_status field
      };
      
      gameApi.submitAction.mockResolvedValue(ambiguousResponse);
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      await act(async () => {
        await gameActions.submitAction('call');
      });
      
      // Should default to PLAYING since we have players and no explicit finish
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
    });

    test('should handle backend response with finished game', async () => {
      const finishedGameResponse = {
        players: [
          { player_id: 'p1', name: 'Player1', chips: 2000, status: 'active' }
        ],
        pot: 0,
        current_state: 'finished',
        game_status: 'finished'
      };
      
      gameApi.submitAction.mockResolvedValue(finishedGameResponse);
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      await act(async () => {
        await gameActions.submitAction('fold');
      });
      
      // Should go to LOBBY when game is finished
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Backend Response Mapping Edge Cases', () => {
    test('should handle response with empty players array', async () => {
      const emptyPlayersResponse = {
        players: [],
        pot: 0,
        current_state: 'pre_flop'
      };
      
      gameApi.submitAction.mockResolvedValue(emptyPlayersResponse);
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      await act(async () => {
        await gameActions.submitAction('fold');
      });
      
      // Should go to LOBBY when no players
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });

    test('should handle response with null/undefined players', async () => {
      const nullPlayersResponse = {
        players: null,
        pot: 0,
        current_state: 'pre_flop'
      };
      
      gameApi.submitAction.mockResolvedValue(nullPlayersResponse);
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      await act(async () => {
        await gameActions.submitAction('fold');
      });
      
      // Should go to LOBBY when players is null/undefined
      expect(gameState.gameState).toBe(GAME_STATES.LOBBY);
    });
  });

  describe('Error Scenarios', () => {
    test('should handle API errors gracefully', async () => {
      gameApi.submitAction.mockRejectedValue(new Error('Backend error'));
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      // Submit action that will fail
      await act(async () => {
        try {
          await gameActions.submitAction('raise', 100);
        } catch (error) {
          // Expected to fail
        }
      });
      
      // Should maintain PLAYING state even after error
      expect(gameState.gameState).toBe(GAME_STATES.PLAYING);
      expect(gameState.error).toBe('Backend error');
      expect(gameState.loading).toBe(false);
    });

    test('should prevent action submission when game not initialized', async () => {
      renderWithProvider();
      
      // Don't set up game - should fail validation
      await act(async () => {
        try {
          await gameActions.submitAction('fold');
          fail('Should have thrown error');
        } catch (error) {
          expect(error.message).toBe('Game or player not initialized');
        }
      });
      
      expect(gameApi.submitAction).not.toHaveBeenCalled();
    });
  });

  describe('Action History', () => {
    test('should add action to history after successful submission', async () => {
      const successResponse = {
        players: [{ player_id: 'p1', name: 'Player1', chips: 950, status: 'active' }],
        pot: 50,
        current_state: 'pre_flop'
      };
      
      gameApi.submitAction.mockResolvedValue(successResponse);
      
      renderWithProvider();
      
      await act(async () => {
        gameActions.setPlayer('p1', 'Player1');
        gameActions.setGameId('game123');
        gameActions.updateGameState({
          gameState: GAME_STATES.PLAYING,
          players: [{ player_id: 'p1', name: 'Player1', chips: 1000 }]
        });
      });
      
      await act(async () => {
        await gameActions.submitAction('raise', 50);
      });
      
      // Should add action to history
      expect(gameState.actionHistory).toHaveLength(1);
      expect(gameState.actionHistory[0]).toMatchObject({
        playerId: 'p1',
        action: 'raise',
        amount: 50
      });
    });
  });
});