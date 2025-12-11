'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Player } from '../lib/types';

interface WinnerModalProps {
  isOpen: boolean;
  winner: Player | null;
  amount: number;
  onClose: () => void;
}

export function WinnerModal({ isOpen, winner, amount, onClose }: WinnerModalProps) {
  if (!winner) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
        >
          {/* Backdrop - inside container, allows clicks to pass through */}
          <div
            className="absolute inset-0 bg-black bg-opacity-75 pointer-events-none"
          />

          {/* Modal content */}
          <motion.div
            initial={{ scale: 0.8, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.8, y: 50 }}
            transition={{ type: 'spring', damping: 20 }}
            className="bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-2xl shadow-2xl p-8 max-w-md w-full border-4 border-yellow-300 pointer-events-auto relative z-10"
          >
              {/* Trophy icon */}
              <div className="text-center mb-6">
                <motion.div
                  initial={{ rotate: -10, scale: 0 }}
                  animate={{ rotate: 0, scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', damping: 10 }}
                  className="text-8xl"
                >
                  🏆
                </motion.div>
              </div>

              {/* Winner announcement */}
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-4xl font-bold text-gray-900 text-center mb-4"
              >
                {winner.name} Wins!
              </motion.h2>

              {/* Amount won */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-6 mb-6 text-center shadow-lg"
              >
                <div className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-2">
                  Amount Won
                </div>
                <div className="text-5xl font-bold text-green-600">
                  ${amount}
                </div>
              </motion.div>

              {/* AI Strategy reveal (only for AI players) */}
              {!winner.is_human && winner.personality && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="bg-gray-900 rounded-xl p-4 mb-6 text-white"
                >
                  <div className="text-yellow-400 text-xs font-bold uppercase tracking-wide mb-2">
                    🤖 AI Strategy Revealed
                  </div>
                  <div className="text-lg font-semibold">
                    {winner.personality} Player
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {winner.personality === 'Conservative' && 'Plays cautiously with premium hands'}
                    {winner.personality === 'Aggressive' && 'Bets and raises frequently'}
                    {winner.personality === 'Mathematical' && 'Uses pot odds and expected value'}
                  </div>
                </motion.div>
              )}

            {/* Close button */}
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              onClick={onClose}
              className="w-full bg-gray-900 hover:bg-gray-800 text-white font-bold py-4 px-6 rounded-lg text-lg transition-colors"
            >
              Next Hand
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
