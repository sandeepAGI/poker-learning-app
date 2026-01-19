/**
 * Frontend Auth Library
 * Handles user authentication with localStorage token management
 * Phase 2.1: Frontend Auth Library
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuthResponse {
  user_id: string;
  username: string;
  token: string;
}

/**
 * Register a new user
 * @param username - Username for new account
 * @param password - Password for new account
 * @returns Auth response with token
 * @throws Error if registration fails
 */
export async function register(username: string, password: string): Promise<AuthResponse> {
  console.log('[Auth] Starting registration for:', username);
  console.log('[Auth] API URL:', `${API_BASE_URL}/auth/register`);

  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  console.log('[Auth] Registration response status:', response.status);

  if (!response.ok) {
    const error = await response.json();
    console.error('[Auth] Registration failed:', error);
    throw new Error(error.detail || 'Registration failed');
  }

  const data: AuthResponse = await response.json();
  console.log('[Auth] Registration successful, got data:', { ...data, token: '***' });

  // Store auth data in localStorage
  console.log('[Auth] Setting localStorage...');
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.setItem('username', data.username);
  console.log('[Auth] localStorage set successfully');

  return data;
}

/**
 * Login existing user
 * @param username - Username
 * @param password - Password
 * @returns Auth response with token
 * @throws Error if login fails
 */
export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data: AuthResponse = await response.json();

  // Store auth data in localStorage
  localStorage.setItem('auth_token', data.token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.setItem('username', data.username);

  return data;
}

/**
 * Logout current user
 * Clears all auth data from localStorage
 */
export function logout(): void {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_id');
  localStorage.removeItem('username');
}

/**
 * Get current auth token
 * @returns Auth token or null if not authenticated
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/**
 * Get stored username
 * @returns Username or null if not authenticated
 */
export function getUsername(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('username');
}

/**
 * Check if user is authenticated
 * @returns true if user has valid token, false otherwise
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  return token !== null && token !== '';
}
