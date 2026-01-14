import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PokerTable } from '../PokerTable';
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/lib/store';

jest.mock('next/navigation');
jest.mock('@/lib/store');

describe('PokerTable Quit Functionality', () => {
  it('calls router.push when quit button clicked', async () => {
    const mockPush = jest.fn();
    const mockQuitGame = jest.fn();

    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useGameStore as jest.Mock).mockReturnValue({
      gameState: {
        current_hand: 1,
        players: [
          { player_id: 0, name: 'Player', stack: 1000, current_bet: 0, is_active: true, hole_cards: [], all_in: false }
        ],
        pot: 10,
        community_cards: [],
        current_bet: 0,
        dealer_index: 0,
        current_player_index: 0,
        phase: 'pre_flop',
        winners: [],
        hand_count: 1,
      },
      quitGame: mockQuitGame,
      submitAction: jest.fn(),
      nextHand: jest.fn(),
      sendContinue: jest.fn(),
      getHandAnalysis: jest.fn(),
      clearHandAnalysis: jest.fn(),
      loading: false,
      error: null,
      connectionState: 'CONNECTED',
      awaitingContinue: false,
      stepMode: false,
    });

    render(<PokerTable />);

    const quitButton = screen.getByTestId('quit-button');
    fireEvent.click(quitButton);

    // Should call quitGame (clears state)
    await waitFor(() => {
      expect(mockQuitGame).toHaveBeenCalled();
    });

    // Should use Next.js router (not window.history)
    expect(mockPush).toHaveBeenCalledWith('/');
  });
});
