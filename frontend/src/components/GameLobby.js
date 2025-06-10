import React, { useState } from 'react';

const GameLobby = ({ onCreateGame }) => {
  const [aiCount, setAiCount] = useState(3);
  const [loading, setLoading] = useState(false);

  const handleCreateGame = async () => {
    setLoading(true);
    try {
      await onCreateGame({
        ai_count: aiCount,
        ai_personalities: ['Conservative', 'Probability-Based', 'Bluffer'].slice(0, aiCount)
      });
    } catch (error) {
      console.error('Failed to create game:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="text-center py-12">
      <h2 className="text-3xl font-bold mb-8">Create New Game</h2>
      
      <div className="bg-gray-800 rounded-lg p-8 max-w-md mx-auto">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Number of AI Opponents
          </label>
          <select
            value={aiCount}
            onChange={(e) => setAiCount(parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value={1}>1 AI Player</option>
            <option value={2}>2 AI Players</option>
            <option value={3}>3 AI Players</option>
            <option value={4}>4 AI Players</option>
          </select>
        </div>

        <button
          onClick={handleCreateGame}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-3 px-4 rounded transition-colors"
        >
          {loading ? 'Creating Game...' : 'Create Game'}
        </button>
      </div>
    </div>
  );
};

export default GameLobby;