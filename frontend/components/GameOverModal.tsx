'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface GameOverModalProps {
  isOpen: boolean;
  handsPlayed: number;
  onNewGame: () => void;
}

export function GameOverModal({ isOpen, handsPlayed, onNewGame }: GameOverModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black bg-opacity-80" />

          {/* Modal */}
          <motion.div
            className="relative bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-8"
            initial={{ scale: 0.5, y: 100 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.5, y: 100 }}
            transition={{ type: 'spring', damping: 15 }}
          >
            {/* Bust emoji */}
            <div className="text-center mb-6">
              <div className="text-8xl mb-4">💀</div>
              <h2 className="text-4xl font-bold mb-2">Game Over!</h2>
              <p className="text-xl text-gray-300">You've been eliminated</p>
            </div>

            {/* Stats */}
            <div className="bg-gray-800 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold mb-3 text-center">Your Stats</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Hands Played:</span>
                  <span className="font-bold text-xl">{handsPlayed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Final Stack:</span>
                  <span className="font-bold text-xl text-red-400">$0</span>
                </div>
              </div>
            </div>

            {/* Message */}
            <div className="text-center text-gray-300 mb-6">
              <p className="text-sm">
                Thanks for playing! Every hand is a learning opportunity.
              </p>
              <p className="text-sm mt-2">
                Try using the analysis feature to learn from your decisions.
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={onNewGame}
                className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-bold py-4 px-6 rounded-lg text-lg transition-all"
              >
                🎮 New Game
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
