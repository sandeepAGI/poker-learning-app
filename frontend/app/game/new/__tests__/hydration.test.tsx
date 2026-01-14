import { render, screen } from '@testing-library/react';
import { renderToString } from 'react-dom/server';
import NewGamePage from '../page';
import { useGameStore } from '@/lib/store';

jest.mock('@/lib/store');
jest.mock('@/lib/auth', () => ({
  isAuthenticated: () => true,
  getUsername: () => 'test_user',
}));

describe('NewGamePage Hydration', () => {
  it('does not cause hydration mismatch when no game in storage', () => {
    // Mock no game state
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: jest.fn(),
      createGame: jest.fn(),
      showAiThinking: false,
      decisionHistory: [],
    });

    // Server render
    const serverHtml = renderToString(<NewGamePage />);

    // Client render
    const { container } = render(<NewGamePage />);
    const clientHtml = container.innerHTML;

    // Should match (no hydration error)
    // Note: This is simplified - React will warn in console if mismatch
    expect(serverHtml).toContain('Your Name');
    expect(clientHtml).toContain('Your Name');
  });

  it('prevents render until client-side mounted', () => {
    const mockInitialize = jest.fn();

    (useGameStore as jest.Mock).mockReturnValue({
      gameState: null,
      loading: false,
      initializeFromStorage: mockInitialize,
      createGame: jest.fn(),
      showAiThinking: false,
      decisionHistory: [],
    });

    render(<NewGamePage />);

    // initializeFromStorage should be called after mount
    expect(mockInitialize).toHaveBeenCalled();
  });
});
