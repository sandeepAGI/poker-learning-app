import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PokerGameContainer from './PokerGameContainer';
import { GameProvider, GAME_STATES } from '../store/gameStore';

// Mock all child components to isolate the conditional rendering logic
jest.mock('./GameLobby', () => {
  return function MockGameLobby({ onCreateGame }) {
    return (
      <div data-testid="game-lobby">
        <h1>Create New Game</h1>
        <button onClick={() => onCreateGame({ ai_count: 1 })}>Create Game</button>
      </div>
    );
  };
});

jest.mock('./PokerTable', () => {
  return function MockPokerTable() {
    return <div data-testid="poker-table">Poker Table</div>;
  };
});

jest.mock('./GameControls', () => {
  return function MockGameControls({ onAction }) {
    return (
      <div data-testid="game-controls">
        <button onClick={() => onAction('raise', 50)}>Raise</button>
        <button onClick={() => onAction('fold')}>Fold</button>
      </div>
    );
  };
});

jest.mock('./PlayerStats', () => {
  return function MockPlayerStats() {
    return <div data-testid="player-stats">Player Stats</div>;
  };
});

// Mock API client
jest.mock('../services/apiClient', () => ({
  gameApi: {
    createGame: jest.fn(),
    submitAction: jest.fn(),
    getGameState: jest.fn(),
    nextHand: jest.fn()
  }
}));

// Mock WebSocket
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

describe('PokerGameContainer - Conditional Rendering Logic', () => {
  const mockOnLogout = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithGameState = (initialGameState = {}) => {
    const TestWrapper = () => {
      const [mounted, setMounted] = React.useState(false);
      
      React.useEffect(() => {
        setMounted(true);
      }, []);

      if (!mounted) return null;
      
      return (
        <GameProvider>
          <PokerGameContainer onLogout={mockOnLogout} />
        </GameProvider>
      );
    };

    return render(<TestWrapper />);
  };

  describe('CRITICAL: Game State Conditional Rendering', () => {
    test('should show GameLobby when gameState is LOBBY', async () => {
      renderWithGameState();
      
      // Should start in LOBBY state by default
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
        expect(screen.getByText('Create New Game')).toBeInTheDocument();
      });
      
      expect(screen.queryByTestId('poker-table')).not.toBeInTheDocument();
    });

    test('should show poker game components when gameState is PLAYING', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock game creation response
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' },
          { player_id: 'ai1', name: 'AI1', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop',
        pot: 15,
        current_bet: 10
      });

      renderWithGameState();
      
      // Start by clicking create game
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      // Click create game button
      fireEvent.click(screen.getByText('Create Game'));
      
      // Should transition to playing state and show poker components
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
        expect(screen.getByTestId('player-stats')).toBeInTheDocument();
      });
      
      expect(screen.queryByTestId('game-lobby')).not.toBeInTheDocument();
    });

    test('CRITICAL: should NOT redirect to lobby after successful action', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock successful game creation
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' },
          { player_id: 'ai1', name: 'AI1', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop',
        pot: 15
      });

      // Mock successful action response - THIS IS THE CRITICAL TEST
      gameApi.submitAction.mockResolvedValue({
        players: [
          { player_id: 'p1', name: 'Human', chips: 950, current_bet: 50, status: 'active' },
          { player_id: 'ai1', name: 'AI1', chips: 1000, current_bet: 0, status: 'active' }
        ],
        pot: 65,
        current_bet: 50,
        current_state: 'pre_flop', // Still in pre_flop, game continues
        current_player: 'ai1'
      });

      renderWithGameState();
      
      // Create game first
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      // Wait for game to start
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
      });
      
      // Submit an action (this is where the bug occurs)
      fireEvent.click(screen.getByText('Raise'));
      
      // CRITICAL: Should stay in poker game, NOT redirect to lobby
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
        expect(screen.queryByTestId('game-lobby')).not.toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Verify action was submitted
      expect(gameApi.submitAction).toHaveBeenCalledWith('test-game', 'p1', {
        action_type: 'raise',
        amount: 50
      });
    });

    test('should redirect to lobby when game is finished', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock game creation
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop'
      });

      // Mock action that finishes the game
      gameApi.submitAction.mockResolvedValue({
        players: [
          { player_id: 'p1', name: 'Human', chips: 2000, status: 'active' }
        ],
        pot: 0,
        current_state: 'finished' // Game is finished
      });

      renderWithGameState();
      
      // Create and start game
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
      });
      
      // Submit action that finishes game
      fireEvent.click(screen.getByText('Fold'));
      
      // Should redirect back to lobby when game is finished
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
        expect(screen.queryByTestId('poker-table')).not.toBeInTheDocument();
      });
    });
  });

  describe('Player Authentication Display', () => {
    test('should show player name in header when authenticated', async () => {
      renderWithGameState();
      
      await waitFor(() => {
        // Should show welcome message (this requires the game state to have playerName)
        // This test might need adjustment based on actual header implementation
        expect(screen.getByText('Change Player')).toBeInTheDocument();
        expect(screen.getByText('Logout')).toBeInTheDocument();
      });
    });

    test('should handle logout correctly', async () => {
      renderWithGameState();
      
      await waitFor(() => {
        expect(screen.getByText('Logout')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Logout'));
      
      expect(mockOnLogout).toHaveBeenCalled();
    });

    test('should handle change player correctly', async () => {
      renderWithGameState();
      
      await waitFor(() => {
        expect(screen.getByText('Change Player')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Change Player'));
      
      // Should set flag and call logout
      expect(mockOnLogout).toHaveBeenCalled();
    });
  });

  describe('Game Controls Visibility', () => {
    test('should show game controls when player can act', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock game where it's the human player's turn
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop',
        current_player: 'p1' // Human player's turn
      });

      renderWithGameState();
      
      // Create game
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      // Should show game controls when it's player's turn
      await waitFor(() => {
        expect(screen.getByTestId('game-controls')).toBeInTheDocument();
      });
    });

    test('should hide game controls when not player turn', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock game where it's NOT the human player's turn
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [
          { player_id: 'p1', name: 'Human', chips: 1000, status: 'active' },
          { player_id: 'ai1', name: 'AI1', chips: 1000, status: 'active' }
        ],
        current_state: 'pre_flop',
        current_player: 'ai1' // AI player's turn
      });

      renderWithGameState();
      
      // Create game
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      // Should NOT show game controls when it's not player's turn
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
        expect(screen.queryByTestId('game-controls')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('should handle game creation errors', async () => {
      const { gameApi } = require('../services/apiClient');
      
      gameApi.createGame.mockRejectedValue(new Error('Failed to create game'));
      
      renderWithGameState();
      
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      // Should stay in lobby on error
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
    });

    test('should handle action submission errors', async () => {
      const { gameApi } = require('../services/apiClient');
      
      // Mock successful game creation
      gameApi.createGame.mockResolvedValue({
        game_id: 'test-game',
        players: [{ player_id: 'p1', name: 'Human', chips: 1000, status: 'active' }],
        current_state: 'pre_flop',
        current_player: 'p1'
      });

      // Mock failed action
      gameApi.submitAction.mockRejectedValue(new Error('Action failed'));

      renderWithGameState();
      
      // Create game
      await waitFor(() => {
        expect(screen.getByTestId('game-lobby')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Create Game'));
      
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
      });
      
      // Submit action that fails
      fireEvent.click(screen.getByText('Fold'));
      
      // Should stay in poker game even after action error
      await waitFor(() => {
        expect(screen.getByTestId('poker-table')).toBeInTheDocument();
        expect(screen.queryByTestId('game-lobby')).not.toBeInTheDocument();
      });
    });
  });
});