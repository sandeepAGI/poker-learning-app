import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { auth } from './services/apiClient';

// Mock the API client auth
jest.mock('./services/apiClient', () => ({
  auth: {
    isAuthenticated: jest.fn(),
    setToken: jest.fn(),
    clearToken: jest.fn()
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

// Mock components to avoid complex nested dependencies
jest.mock('./components/PokerGameContainer', () => {
  return function MockPokerGameContainer({ onLogout }) {
    return (
      <div data-testid="poker-game-container">
        <button onClick={onLogout}>Test Logout</button>
      </div>
    );
  };
});

jest.mock('./components/AuthModal', () => {
  return function MockAuthModal({ onLogin }) {
    return (
      <div data-testid="auth-modal">
        <button onClick={() => onLogin('test-token', { username: 'Test' })}>
          Test Login
        </button>
      </div>
    );
  };
});

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
  });

  test('shows AuthModal when not authenticated', () => {
    auth.isAuthenticated.mockReturnValue(false);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    expect(screen.getByTestId('auth-modal')).toBeInTheDocument();
    expect(screen.queryByTestId('poker-game-container')).not.toBeInTheDocument();
  });

  test('shows PokerGameContainer when authenticated', () => {
    auth.isAuthenticated.mockReturnValue(true);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    expect(screen.getByTestId('poker-game-container')).toBeInTheDocument();
    expect(screen.queryByTestId('auth-modal')).not.toBeInTheDocument();
  });

  test('handles ask_for_name_on_startup flag correctly', () => {
    auth.isAuthenticated.mockReturnValue(true);
    localStorageMock.getItem.mockReturnValue('true'); // ask_for_name_on_startup = true
    
    render(<App />);
    
    // Should show auth modal even when authenticated due to the flag
    expect(screen.getByTestId('auth-modal')).toBeInTheDocument();
    expect(screen.queryByTestId('poker-game-container')).not.toBeInTheDocument();
    
    // Should remove the flag from localStorage
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('ask_for_name_on_startup');
  });

  test('handles authentication properly when not authenticated and no flag', () => {
    auth.isAuthenticated.mockReturnValue(false);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    expect(screen.getByTestId('auth-modal')).toBeInTheDocument();
    expect(localStorageMock.removeItem).not.toHaveBeenCalled();
  });

  test('stores player data on login', () => {
    auth.isAuthenticated.mockReturnValue(false);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    const loginButton = screen.getByText('Test Login');
    loginButton.click();
    
    expect(auth.setToken).toHaveBeenCalledWith('test-token');
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'player_data',
      JSON.stringify({ username: 'Test' })
    );
  });

  test('clears data on logout', () => {
    auth.isAuthenticated.mockReturnValue(true);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    const logoutButton = screen.getByText('Test Logout');
    logoutButton.click();
    
    expect(auth.clearToken).toHaveBeenCalled();
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('player_data');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('game_data');
  });

  test('shows debug button in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';
    
    auth.isAuthenticated.mockReturnValue(true);
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    expect(screen.getByText('Debug')).toBeInTheDocument();
    
    process.env.NODE_ENV = originalEnv;
  });
});