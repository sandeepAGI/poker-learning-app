import React, { useState } from 'react';
import { gameApi } from '../services/apiClient';

const AuthModal = ({ onLogin }) => {
  const [playerName, setPlayerName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!playerName.trim()) {
      setError('Please enter a player name');
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Create player and get authentication token
      const response = await gameApi.createPlayer({
        username: playerName.trim(),
        settings: {}
      });

      // Call the login handler with token and player data
      onLogin(response.access_token, response);
      
    } catch (err) {
      setError(err.message || 'Failed to create player');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="bg-gray-800 rounded-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-400 mb-2">🃏</h1>
          <h2 className="text-2xl font-bold text-white mb-2">Poker Learning App</h2>
          <p className="text-gray-400">Enter your name to start playing</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label htmlFor="playerName" className="block text-sm font-medium text-gray-300 mb-2">
              Player Name
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your name..."
              maxLength={50}
              disabled={loading}
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded-md">
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !playerName.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-md transition-colors"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Creating Player...
              </div>
            ) : (
              'Start Playing'
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-400 text-sm">
            New to poker? This app will help you learn optimal strategies through AI-powered feedback.
          </p>
        </div>

        {/* Development information */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 p-3 bg-gray-700 rounded-md">
            <p className="text-gray-300 text-xs">
              <strong>Development Mode:</strong> Authentication is simplified for testing.
              In production, this would include proper user registration and login.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;