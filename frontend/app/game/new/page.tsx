'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PokerTable } from '@/components/PokerTable';
import { AISidebar } from '@/components/AISidebar';
import { useGameStore } from '@/lib/store';
import { isAuthenticated, getUsername } from '@/lib/auth';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function NewGamePage() {
  const router = useRouter();
  const username = getUsername();
  const { gameState, createGame, loading, initializeFromStorage, showAiThinking, decisionHistory } = useGameStore();
  const [playerName, setPlayerName] = useState(username || 'Player');
  const [aiCount, setAiCount] = useState(3);
  const [mounted, setMounted] = useState(false);

  // Check authentication and initialize game state
  useEffect(() => {
    setMounted(true); // Mark as client-side mounted

    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Set player name from username if available
    if (username && !playerName) {
      setPlayerName(username);
    }

    // Only restore game after mounted (prevents hydration mismatch)
    initializeFromStorage();
  }, [router, username, playerName, initializeFromStorage]);

  // Redirect if not authenticated
  if (!isAuthenticated()) {
    return null;
  }

  // Prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  // Show game creation form if no active game
  if (!gameState) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-700 to-green-900">
        <motion.div
          className="bg-white p-8 rounded-2xl shadow-2xl max-w-md w-full"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {/* Back to Home Link */}
          <div className="mb-4">
            <Link
              href="/"
              className="text-sm text-gray-600 hover:text-gray-800 transition"
            >
              ← Back to Home
            </Link>
          </div>

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
                Table Size
              </label>
              <select
                value={aiCount}
                onChange={(e) => setAiCount(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value={3}>4 Players (You + 3 AI) - Recommended</option>
                <option value={5}>6 Players (You + 5 AI) - Full Table</option>
              </select>
              <div className="mt-2 text-xs text-gray-600 space-y-1">
                <p>🎯 <strong>4 Players:</strong> Faster hands, easier to learn</p>
                <p>🔥 <strong>6 Players:</strong> Full table experience, more challenging</p>
              </div>
            </div>

            <button
              onClick={() => createGame(playerName || username || 'Player', aiCount)}
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating Game...' : 'Start Game'}
            </button>
          </div>

          {/* Phase 2: Tutorial and Guide Links */}
          <div className="mt-4 flex gap-3 justify-center">
            <a
              href="/tutorial"
              className="text-sm text-green-600 hover:text-green-700 font-medium hover:underline"
            >
              📚 Learn Texas Hold'em
            </a>
            <span className="text-gray-400">•</span>
            <a
              href="/guide"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium hover:underline"
            >
              ❓ How to Use This App
            </a>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-sm text-gray-700 mb-2">AI Personalities:</h3>
            <p className="text-xs text-gray-600 mb-2">
              AI opponents use a mix of playing styles to challenge you:
            </p>
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

  // Show active game (PokerTable + AISidebar)
  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 overflow-auto">
        <PokerTable key={gameState?.hand_count || 'poker-table'} />
      </div>
      <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
    </div>
  );
}
