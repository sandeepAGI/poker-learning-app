import { render, screen, waitFor } from '@testing-library/react';
import { useGameStore } from '@/lib/store';
import NewGamePage from '../page';

// Mock Zustand store
jest.mock('@/lib/store');
jest.mock('@/lib/auth', () => ({
  isAuthenticated: () => true,
  getUsername: () => 'test_user',
}));

describe('NewGamePage Navigation Recovery', () => {
  it('remounts PokerTable when gameState changes after navigation', async () => {
    const mockGameState = {
      current_hand: 1,
      players: [],
      pot: 10,
      community_cards: [],
      current_bet: 0,
      dealer_index: 0,
      current_player_index: 0,
      phase: 'pre_flop',
      winners: []
    };

    // Start with no game
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: jest.fn(),
      showAiThinking: false,
      decisionHistory: [],
      createGame: jest.fn(),
    });

    const { rerender } = render(<NewGamePage />);

    // Game creation form should show
    expect(screen.getByText('Your Name')).toBeInTheDocument();

    // Simulate game state loaded (e.g., after browser back)
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: mockGameState,
      loading: false,
      showAiThinking: false,
      decisionHistory: [],
      initializeFromStorage: jest.fn(),
      createGame: jest.fn(),
    });

    rerender(<NewGamePage />);

    // PokerTable should render (form should be gone)
    await waitFor(() => {
      expect(screen.queryByText('Your Name')).not.toBeInTheDocument();
    });
  });
});
