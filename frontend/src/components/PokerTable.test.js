import React from 'react';
import { render, screen } from '@testing-library/react';
import PokerTable from './PokerTable';
import { useGame } from '../store/gameStore';

// Mock the game store
jest.mock('../store/gameStore', () => ({
  useGame: jest.fn()
}));

describe('PokerTable', () => {
  const mockGameState = {
    players: [
      {
        id: 'player1',
        name: 'Human Player',
        chips: 1000,
        current_bet: 50,
        status: 'active',
        hole_cards: ['As', 'Kh']
      },
      {
        id: 'player2',
        name: 'AI Player 1',
        chips: 800,
        current_bet: 50,
        status: 'active',
        hole_cards: null
      },
      {
        id: 'player3',
        name: 'AI Player 2',
        chips: 1200,
        current_bet: 0,
        status: 'folded',
        hole_cards: null
      }
    ],
    playerId: 'player1',
    currentPlayerIndex: 0,
    dealerIndex: 1,
    communityCards: ['2h', '3d', '4s'],
    pot: 150,
    roundState: 'flop',
    gameState: 'active',
    currentBet: 50,
    handCount: 3
  };

  const mockComputed = {
    wsConnected: true
  };

  beforeEach(() => {
    useGame.mockReturnValue({
      state: mockGameState,
      computed: mockComputed
    });
  });

  test('renders poker table with community cards', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('Community Cards')).toBeInTheDocument();
    expect(screen.getByText('2h')).toBeInTheDocument();
    expect(screen.getByText('3d')).toBeInTheDocument();
    expect(screen.getByText('4s')).toBeInTheDocument();
  });

  test('displays pot amount correctly', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('Pot: $150')).toBeInTheDocument();
  });

  test('shows current round state', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('flop')).toBeInTheDocument();
  });

  test('clearly identifies human player with enhanced styling', () => {
    render(<PokerTable />);
    
    // Human player should have "(YOU)" label with proper styling
    expect(screen.getByText('Human Player (YOU)')).toBeInTheDocument();
    
    // Human player should have user icon
    const humanPlayerSection = screen.getByText('Human Player (YOU)').closest('div').closest('div').closest('div');
    expect(humanPlayerSection).toHaveClass('border-4', 'border-blue-400', 'bg-blue-900', 'shadow-lg', 'shadow-blue-500/50');
  });

  test('identifies AI players with robot icons', () => {
    render(<PokerTable />);
    
    // AI players should not have "(YOU)" label
    expect(screen.getByText('AI Player 1')).toBeInTheDocument();
    expect(screen.getByText('AI Player 2')).toBeInTheDocument();
    
    // Should not show "(YOU)" for AI players
    expect(screen.queryByText('AI Player 1 (YOU)')).not.toBeInTheDocument();
    expect(screen.queryByText('AI Player 2 (YOU)')).not.toBeInTheDocument();
  });

  test('displays player chips correctly', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('$1000')).toBeInTheDocument(); // Human player chips
    expect(screen.getByText('$800')).toBeInTheDocument();  // AI Player 1 chips
    expect(screen.getByText('$1200')).toBeInTheDocument(); // AI Player 2 chips
  });

  test('shows current bets for players who have bet', () => {
    render(<PokerTable />);
    
    // Players 1 and 2 have current bets
    const betElements = screen.getAllByText(/Bet: \$50/);
    expect(betElements).toHaveLength(2);
  });

  test('displays player status correctly with colors', () => {
    render(<PokerTable />);
    
    const activeStatus = screen.getAllByText('active');
    expect(activeStatus).toHaveLength(2);
    
    expect(screen.getByText('folded')).toBeInTheDocument();
  });

  test('shows hole cards only for human player', () => {
    render(<PokerTable />);
    
    // Human player's cards should be visible
    expect(screen.getByText('As')).toBeInTheDocument();
    expect(screen.getByText('Kh')).toBeInTheDocument();
  });

  test('marks dealer with fire emoji', () => {
    render(<PokerTable />);
    
    // AI Player 1 is the dealer (index 1)
    const dealerSection = screen.getByText('AI Player 1').closest('div');
    expect(dealerSection).toHaveTextContent('🔥');
  });

  test('highlights active player with yellow ring', () => {
    render(<PokerTable />);
    
    // Human player is active (index 0)
    const activePlayerSection = screen.getByText('Human Player (YOU)').closest('div').closest('div').closest('div');
    expect(activePlayerSection).toHaveClass('ring-2', 'ring-yellow-400');
  });

  test('shows WebSocket connection status', () => {
    render(<PokerTable />);
    
    const wsIndicator = document.querySelector('.bg-green-400');
    expect(wsIndicator).toBeInTheDocument();
  });

  test('displays game state and current bet info', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('active')).toBeInTheDocument(); // Game state
    expect(screen.getByText('Current Bet:')).toBeInTheDocument();
    expect(screen.getByText('$50')).toBeInTheDocument(); // Current bet amount
  });

  test('shows hand count', () => {
    render(<PokerTable />);
    
    expect(screen.getByText('Hand:')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  test('handles empty community cards', () => {
    const stateWithNoCards = {
      ...mockGameState,
      communityCards: []
    };

    useGame.mockReturnValue({
      state: stateWithNoCards,
      computed: mockComputed
    });

    render(<PokerTable />);
    
    expect(screen.getByText('No cards dealt')).toBeInTheDocument();
  });

  test('shows disconnected WebSocket status', () => {
    const disconnectedComputed = {
      wsConnected: false
    };

    useGame.mockReturnValue({
      state: mockGameState,
      computed: disconnectedComputed
    });

    render(<PokerTable />);
    
    const wsIndicator = document.querySelector('.bg-red-400');
    expect(wsIndicator).toBeInTheDocument();
  });
});