import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AuthModal from './AuthModal';
import { gameApi } from '../services/apiClient';

// Mock the API client
jest.mock('../services/apiClient', () => ({
  gameApi: {
    createPlayer: jest.fn()
  }
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

describe('AuthModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear.mockClear();
    localStorageMock.setItem.mockClear();
  });

  test('renders auth modal correctly', () => {
    render(<AuthModal onLogin={() => {}} />);
    
    expect(screen.getByText('Poker Learning App')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your name...')).toBeInTheDocument();
    expect(screen.getByText('Start Playing')).toBeInTheDocument();
  });

  test('shows user options for managing cached data', () => {
    render(<AuthModal onLogin={() => {}} />);
    
    expect(screen.getByText('Clear All Data & Restart')).toBeInTheDocument();
    expect(screen.getByText('Ask for Name Next Time')).toBeInTheDocument();
    expect(screen.getByText('Want to start fresh? Clear your saved data to enter a different name next time.')).toBeInTheDocument();
  });

  test('clears localStorage when Clear All Data & Restart is clicked', () => {
    render(<AuthModal onLogin={() => {}} />);
    
    const clearButton = screen.getByText('Clear All Data & Restart');
    fireEvent.click(clearButton);
    
    expect(localStorageMock.clear).toHaveBeenCalled();
    expect(window.location.reload).toHaveBeenCalled();
  });

  test('sets ask_for_name_on_startup flag when Ask for Name Next Time is clicked', () => {
    render(<AuthModal onLogin={() => {}} />);
    
    const askButton = screen.getByText('Ask for Name Next Time');
    fireEvent.click(askButton);
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith('ask_for_name_on_startup', 'true');
  });

  test('validates empty player name', () => {
    render(<AuthModal onLogin={() => {}} />);
    
    const submitButton = screen.getByText('Start Playing');
    fireEvent.click(submitButton);
    
    expect(screen.getByText('Please enter a player name')).toBeInTheDocument();
  });

  test('creates player successfully', async () => {
    const mockOnLogin = jest.fn();
    const mockResponse = {
      access_token: 'test-token',
      player_id: 'test-player-id',
      username: 'TestPlayer'
    };
    
    gameApi.createPlayer.mockResolvedValue(mockResponse);
    
    render(<AuthModal onLogin={mockOnLogin} />);
    
    const nameInput = screen.getByPlaceholderText('Enter your name...');
    const submitButton = screen.getByText('Start Playing');
    
    fireEvent.change(nameInput, { target: { value: 'TestPlayer' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(gameApi.createPlayer).toHaveBeenCalledWith({
        username: 'TestPlayer',
        settings: {}
      });
      expect(mockOnLogin).toHaveBeenCalledWith('test-token', mockResponse);
    });
  });

  test('handles API error gracefully', async () => {
    const mockOnLogin = jest.fn();
    gameApi.createPlayer.mockRejectedValue(new Error('API Error'));
    
    render(<AuthModal onLogin={mockOnLogin} />);
    
    const nameInput = screen.getByPlaceholderText('Enter your name...');
    const submitButton = screen.getByText('Start Playing');
    
    fireEvent.change(nameInput, { target: { value: 'TestPlayer' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
      expect(mockOnLogin).not.toHaveBeenCalled();
    });
  });
});