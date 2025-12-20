'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Player } from '../lib/types';

interface WinnerInfo {
  player_id: string;
  name: string;
  amount: number;
  is_human: boolean;
  personality?: string | null;
}

interface WinnerModalProps {
  isOpen: boolean;
  winnerInfo: WinnerInfo | WinnerInfo[];  // Can be single winner or array
  players: Player[];
  onClose: () => void;
}

export function WinnerModal({ isOpen, winnerInfo, players, onClose }: WinnerModalProps) {
  if (!winnerInfo) return null;

  // Normalize to array for consistent handling
  const winners = Array.isArray(winnerInfo) ? winnerInfo : [winnerInfo];
  const totalAmount = winners.reduce((sum, w) => sum + w.amount, 0);
  const isMultipleWinners = winners.length > 1;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black bg-opacity-75 pointer-events-none" />

          {/* Modal content */}
          <motion.div
            initial={{ scale: 0.8, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.8, y: 50 }}
            transition={{ type: 'spring', damping: 20 }}
            className="bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-2xl shadow-2xl p-8 max-w-md w-full border-4 border-yellow-300 pointer-events-auto relative z-10"
            data-testid="winner-modal"
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
              data-testid="winner-announcement"
            >
              {isMultipleWinners ? 'Split Pot!' : `${winners[0].name} Wins!`}
            </motion.h2>

            {/* Winner details */}
            {isMultipleWinners ? (
              // Multiple winners
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-4 mb-6 text-center shadow-lg"
              >
                <div className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-3">
                  {winners.length} Players Split ${totalAmount}
                </div>

                <div className="space-y-2">
                  {winners.map((winner, index) => {
                    const player = players.find(p => p.player_id === winner.player_id);
                    return (
                      <div
                        key={winner.player_id}
                        className="flex justify-between items-center bg-gray-50 rounded-lg p-3"
                        data-testid={`winner-${index}`}
                      >
                        <span className="font-semibold text-gray-900">
                          {winner.name}
                        </span>
                        <span className="text-2xl font-bold text-green-600">
                          ${winner.amount}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            ) : (
              // Single winner
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-6 mb-6 text-center shadow-lg"
              >
                <div className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-2">
                  Amount Won
                </div>
                <div className="text-5xl font-bold text-green-600" data-testid="winner-amount">
                  ${winners[0].amount}
                </div>
              </motion.div>
            )}

            {/* AI Strategy reveal (only for single AI winner) */}
            {!isMultipleWinners && !winners[0].is_human && winners[0].personality && (
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
                  {winners[0].personality} Player
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  {winners[0].personality === 'Conservative' && 'Plays cautiously with premium hands'}
                  {winners[0].personality === 'Aggressive' && 'Bets and raises frequently'}
                  {winners[0].personality === 'Mathematical' && 'Uses pot odds and expected value'}
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
