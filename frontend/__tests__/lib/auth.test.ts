/**
 * Tests for auth library (localStorage + token management)
 * Phase 2.1: Frontend Auth Library
 */

import { register, login, logout, getToken, isAuthenticated } from '@/lib/auth';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Auth Library', () => {
  beforeEach(() => {
    // Clear localStorage and fetch mock before each test
    localStorageMock.clear();
    (global.fetch as jest.Mock).mockClear();
  });

  describe('register', () => {
    it('should register a new user and store token', async () => {
      const mockResponse = {
        user_id: 'user-123',
        username: 'testuser',
        token: 'mock-jwt-token',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await register('testuser', 'password123');

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: 'testuser', password: 'password123' }),
      });

      expect(result).toEqual(mockResponse);
      expect(localStorageMock.getItem('auth_token')).toBe('mock-jwt-token');
      expect(localStorageMock.getItem('user_id')).toBe('user-123');
      expect(localStorageMock.getItem('username')).toBe('testuser');
    });

    it('should throw error when registration fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Username already exists' }),
      });

      await expect(register('testuser', 'password123')).rejects.toThrow(
        'Username already exists'
      );

      expect(localStorageMock.getItem('auth_token')).toBeNull();
    });

    it('should throw generic error when response has no detail', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      });

      await expect(register('testuser', 'password123')).rejects.toThrow(
        'Registration failed'
      );
    });
  });

  describe('login', () => {
    it('should login user and store token', async () => {
      const mockResponse = {
        user_id: 'user-456',
        username: 'existinguser',
        token: 'mock-login-token',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await login('existinguser', 'password123');

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: 'existinguser', password: 'password123' }),
      });

      expect(result).toEqual(mockResponse);
      expect(localStorageMock.getItem('auth_token')).toBe('mock-login-token');
      expect(localStorageMock.getItem('user_id')).toBe('user-456');
      expect(localStorageMock.getItem('username')).toBe('existinguser');
    });

    it('should throw error when credentials are invalid', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      });

      await expect(login('wronguser', 'wrongpass')).rejects.toThrow(
        'Invalid credentials'
      );

      expect(localStorageMock.getItem('auth_token')).toBeNull();
    });

    it('should throw generic error when response has no detail', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      });

      await expect(login('testuser', 'password123')).rejects.toThrow('Login failed');
    });
  });

  describe('logout', () => {
    it('should clear all auth data from localStorage', () => {
      // Set some auth data
      localStorageMock.setItem('auth_token', 'some-token');
      localStorageMock.setItem('user_id', 'user-123');
      localStorageMock.setItem('username', 'testuser');

      logout();

      expect(localStorageMock.getItem('auth_token')).toBeNull();
      expect(localStorageMock.getItem('user_id')).toBeNull();
      expect(localStorageMock.getItem('username')).toBeNull();
    });

    it('should not throw error when no auth data exists', () => {
      expect(() => logout()).not.toThrow();
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      localStorageMock.setItem('auth_token', 'test-token-123');

      expect(getToken()).toBe('test-token-123');
    });

    it('should return null when no token exists', () => {
      expect(getToken()).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      localStorageMock.setItem('auth_token', 'valid-token');

      expect(isAuthenticated()).toBe(true);
    });

    it('should return false when no token exists', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('should return false when token is empty string', () => {
      localStorageMock.setItem('auth_token', '');

      expect(isAuthenticated()).toBe(false);
    });
  });
});
