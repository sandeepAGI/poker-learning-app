'use client';

import { useState, useEffect } from 'react';
import { PokerTable } from '../components/PokerTable';
import { AISidebar } from '../components/AISidebar';
import { useGameStore } from '../lib/store';
import { motion } from 'framer-motion';
import { useAIDecisionHistory } from '../lib/hooks/useAIDecisionHistory';

export default function Home() {
  const { gameState, createGame, loading, initializeFromStorage, showAiThinking } = useGameStore();
  const [playerName, setPlayerName] = useState('Player');
  const [aiCount, setAiCount] = useState(3);

  // Phase 7+: Check for existing game on mount (browser refresh recovery)
  useEffect(() => {
    initializeFromStorage();
  }, [initializeFromStorage]);

  // Phase 2: Use custom hook for AI decision history tracking
  const decisionHistory = useAIDecisionHistory(gameState);

  if (!gameState) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-700 to-green-900">
        <motion.div
          className="bg-white p-8 rounded-2xl shadow-2xl max-w-md w-full"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">
            Poker Learning App
          </h1>
          <p className="text-gray-600 text-center mb-6">
            Learn poker by playing against AI opponents with different strategies
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Name
              </label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Enter your name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of AI Opponents
              </label>
              <select
                value={aiCount}
                onChange={(e) => setAiCount(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value={1}>1 (Conservative)</option>
                <option value={2}>2 (Conservative + Aggressive)</option>
                <option value={3}>3 (All Personalities)</option>
              </select>
            </div>

            <button
              onClick={() => createGame(playerName || 'Player', aiCount)}
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating Game...' : 'Start Game'}
            </button>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-sm text-gray-700 mb-2">AI Personalities:</h3>
            <ul className="text-xs text-gray-600 space-y-1">
              <li><strong>Conservative:</strong> Plays tight, folds weak hands</li>
              <li><strong>Aggressive:</strong> Bluffs often, raises frequently</li>
              <li><strong>Mathematical:</strong> Uses pot odds and EV calculations</li>
            </ul>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 overflow-auto">
        <PokerTable />
      </div>
      <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
    </div>
  );
}
