'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PokerTable } from '../../../components/PokerTable';
import { AISidebar } from '../../../components/AISidebar';
import { useGameStore } from '../../../lib/store';
import { motion } from 'framer-motion';
import { useAIDecisionHistory } from '../../../lib/hooks/useAIDecisionHistory';

/**
 * Dynamic Game Page - Phase 7+ Browser Refresh Recovery
 *
 * This page handles:
 * 1. Direct navigation to /game/[gameId]
 * 2. Browser refresh during active game
 * 3. Invalid game ID handling
 * 4. Automatic reconnection to existing games
 */

export default function GamePage({ params }: { params: Promise<{ gameId: string }> }) {
  const router = useRouter();
  const { gameState, loading, error, reconnectToGame, showAiThinking } = useGameStore();
  const [gameId, setGameId] = useState<string>('');

  // Await params in Next.js 15
  useEffect(() => {
    params.then(p => setGameId(p.gameId));
  }, [params]);

  useEffect(() => {
    // Only attempt reconnection if gameId is set
    if (!gameId) return;

    // Attempt to reconnect to the game
    const attemptReconnect = async () => {
      const success = await reconnectToGame(gameId);

      if (!success) {
        // Reconnection failed, redirect to home after 3 seconds
        setTimeout(() => {
          router.push('/');
        }, 3000);
      }
    };

    // Only attempt reconnection if we don't already have the game state
    if (!gameState) {
      attemptReconnect();
    }
  }, [gameId, gameState, reconnectToGame, router]);

  // Phase 2: Use custom hook for AI decision history tracking
  const decisionHistory = useAIDecisionHistory(gameState);

  // Show error state if reconnection failed
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-700 to-red-900">
        <motion.div
          className="bg-white p-8 rounded-2xl shadow-2xl max-w-md w-full text-center"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-4">
            Unable to Reconnect
          </h1>
          <p className="text-gray-600 mb-6">
            {error}
          </p>
          <p className="text-sm text-gray-500">
            Redirecting to home in 3 seconds...
          </p>
        </motion.div>
      </div>
    );
  }

  // Show loading state while reconnecting
  if (loading || !gameState) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-700 to-green-900">
        <motion.div
          className="bg-white p-8 rounded-2xl shadow-2xl max-w-md w-full text-center"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            Reconnecting to Game
          </h1>
          <p className="text-gray-600">
            Game ID: <code className="bg-gray-100 px-2 py-1 rounded text-sm">{gameId}</code>
          </p>
        </motion.div>
      </div>
    );
  }

  // Render the poker table with AI sidebar once reconnected
  return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1 overflow-auto">
        <PokerTable />
      </div>
      <AISidebar isOpen={showAiThinking} decisions={decisionHistory} />
    </div>
  );
}
