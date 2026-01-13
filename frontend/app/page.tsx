'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, getUsername, logout, login, register } from '@/lib/auth';
import Link from 'next/link';

export default function HomePage() {
  const router = useRouter();
  const username = getUsername();
  const authenticated = isAuthenticated();

  // Login/Register state
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loginUsername, setLoginUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate
    if (!loginUsername || !password) {
      setError('Username and password are required');
      return;
    }

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }
    }

    setLoading(true);

    try {
      if (mode === 'login') {
        await login(loginUsername, password);
      } else {
        await register(loginUsername, password);
      }

      // Force page refresh to update authentication state
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setConfirmPassword('');
  };

  const handleLogout = () => {
    logout();
    window.location.reload();
  };

  // If not authenticated, show login/register form
  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
        <div className="bg-gray-800 p-8 rounded-lg shadow-xl w-full max-w-md">
          <h1 className="text-3xl font-bold text-white mb-6 text-center">
            {mode === 'login' ? 'Login' : 'Register'}
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                autoComplete="username"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                disabled={loading}
              />
            </div>

            {mode === 'register' && (
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-2 rounded bg-gray-700 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
                  autoComplete="new-password"
                  disabled={loading}
                />
              </div>
            )}

            {error && (
              <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded transition"
            >
              {loading ? 'Loading...' : (mode === 'login' ? 'Login' : 'Register')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={switchMode}
              className="text-blue-400 hover:text-blue-300 text-sm"
              disabled={loading}
            >
              {mode === 'login' ? "Don't have an account? Create one" : 'Already have an account? Login'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // If authenticated, show landing page with navigation
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Welcome, {username}!</h1>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition"
          >
            Logout
          </button>
        </div>

        <div className="space-y-4">
          <Link
            href="/game/new"
            className="block bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            Start New Game
          </Link>

          <Link
            href="/history"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center font-bold py-3 px-4 rounded transition"
          >
            View Game History
          </Link>

          <Link
            href="/tutorial"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Tutorial
          </Link>

          <Link
            href="/guide"
            className="block bg-gray-700 hover:bg-gray-600 text-white text-center py-3 px-4 rounded transition"
          >
            Hand Rankings Guide
          </Link>
        </div>
      </div>
    </div>
  );
}
