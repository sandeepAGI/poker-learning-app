'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Player } from '../lib/types';
import { Card } from './Card';

interface ShowdownParticipant {
  player_id: string;
  name: string;
  hand_rank: string;
  hole_cards: string[];
  amount_won: number;
  is_human: boolean;
}

interface FoldedPlayer {
  player_id: string;
  name: string;
  is_human: boolean;
}

interface WinnerInfo {
  player_id: string;
  name: string;
  amount: number;
  is_human: boolean;
  personality?: string | null;
  won_by_fold?: boolean;
  hand_rank?: string | null;
  hole_cards?: string[];
  all_showdown_hands?: ShowdownParticipant[];
  folded_players?: FoldedPlayer[];
}

interface MultipleWinnersInfo {
  winners: WinnerInfo[];
  all_showdown_hands?: ShowdownParticipant[];
  folded_players?: FoldedPlayer[];
}

interface WinnerModalProps {
  isOpen: boolean;
  winnerInfo: WinnerInfo | MultipleWinnersInfo | null;
  players: Player[];
  communityCards?: string[];
  onClose: () => void;
}

export function WinnerModal({ isOpen, winnerInfo, players, communityCards, onClose }: WinnerModalProps) {
  if (!winnerInfo) return null;

  // Detect if it's MultipleWinnersInfo or single WinnerInfo
  const isMultipleWinnersObject = 'winners' in winnerInfo;

  // Extract winners array
  const winners: WinnerInfo[] = isMultipleWinnersObject
    ? (winnerInfo as MultipleWinnersInfo).winners
    : [winnerInfo as WinnerInfo];

  // Extract showdown and folded player data
  const showdownHands: ShowdownParticipant[] = isMultipleWinnersObject
    ? (winnerInfo as MultipleWinnersInfo).all_showdown_hands || []
    : (winnerInfo as WinnerInfo).all_showdown_hands || [];

  const foldedPlayers: FoldedPlayer[] = isMultipleWinnersObject
    ? (winnerInfo as MultipleWinnersInfo).folded_players || []
    : (winnerInfo as WinnerInfo).folded_players || [];

  const totalAmount = winners.reduce((sum, w) => sum + w.amount, 0);
  const isMultipleWinners = winners.length > 1;

  // Check if this was a fold win (no showdown)
  const wonByFold = winners[0]?.won_by_fold === true;
  const hasShowdown = showdownHands.length > 0;

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
            className="bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-2xl shadow-2xl p-5 max-w-md w-full max-h-[90vh] overflow-y-auto border-4 border-yellow-300 pointer-events-auto relative z-10"
            data-testid="winner-modal"
          >
            {/* Trophy icon */}
            <div className="text-center mb-3">
              <motion.div
                initial={{ rotate: -10, scale: 0 }}
                animate={{ rotate: 0, scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', damping: 10 }}
                className="text-6xl"
              >
                🏆
              </motion.div>
            </div>

            {/* Winner announcement */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-3xl font-bold text-gray-900 text-center mb-2"
              data-testid="winner-announcement"
            >
              {isMultipleWinners ? 'Split Pot!' : `${winners[0].name} Wins!`}
            </motion.h2>

            {/* Community Cards - Show the board */}
            {hasShowdown && communityCards && communityCards.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 }}
                className="mb-3"
              >
                <div className="text-center text-gray-800 text-xs font-semibold uppercase tracking-wide mb-1">
                  Board
                </div>
                <div className="flex gap-1 justify-center">
                  {communityCards.map((card, i) => (
                    <div key={i} className="scale-50 origin-center">
                      <Card card={card} />
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Winner details */}
            {isMultipleWinners ? (
              // Multiple winners
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-3 mb-3 text-center shadow-lg"
              >
                <div className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-3">
                  {winners.length} Players Split ${totalAmount}
                </div>

                <div className="space-y-3">
                  {winners.map((winner, index) => (
                    <div
                      key={winner.player_id}
                      className="bg-gray-50 rounded-lg p-3"
                      data-testid={`winner-${index}`}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-semibold text-gray-900">
                          {winner.name}
                        </span>
                        <span className="text-2xl font-bold text-green-600">
                          ${winner.amount}
                        </span>
                      </div>

                      {/* Show hand rank and cards if showdown */}
                      {hasShowdown && winner.hand_rank && winner.hole_cards && winner.hole_cards.length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-600 font-semibold mb-1">
                            {winner.hand_rank}
                          </div>
                          <div className="flex gap-1 justify-center">
                            {winner.hole_cards.map((card, i) => (
                              <div key={i} className="scale-60 origin-center">
                                <Card card={card} />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              // Single winner
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-4 mb-3 text-center shadow-lg"
              >
                <div className="text-gray-600 text-sm font-semibold uppercase tracking-wide mb-1">
                  Amount Won
                </div>
                <div className="text-4xl font-bold text-green-600 mb-2" data-testid="winner-amount">
                  ${winners[0].amount}
                </div>

                {/* Show hand rank and cards if showdown */}
                {hasShowdown && winners[0].hand_rank && winners[0].hole_cards && winners[0].hole_cards.length > 0 && (
                  <div className="mt-2">
                    <div className="text-sm text-gray-600 font-semibold mb-2">
                      {winners[0].hand_rank}
                    </div>
                    <div className="flex gap-1 justify-center">
                      {winners[0].hole_cards.map((card, i) => (
                        <div key={i} className="scale-60 origin-center">
                          <Card card={card} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Showdown Results - show all hands ranked */}
            {hasShowdown && showdownHands.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-gray-800 rounded-xl p-3 mb-2 text-white"
              >
                <div className="text-yellow-400 text-xs font-bold uppercase tracking-wide mb-2">
                  📊 Showdown Results (Best to Worst)
                </div>
                <div className="space-y-1.5">
                  {showdownHands.map((participant, index) => (
                    <div
                      key={participant.player_id}
                      className={`bg-gray-700 rounded-lg p-1.5 ${participant.amount_won > 0 ? 'border-2 border-green-500' : ''}`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <span className="font-semibold text-xs">
                            {index + 1}. {participant.name}
                          </span>
                          {participant.amount_won > 0 && (
                            <span className="ml-1 text-green-400 text-xs font-bold">
                              Won ${participant.amount_won}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-400">
                          {participant.hand_rank}
                        </span>
                      </div>
                      <div className="flex gap-0.5">
                        {participant.hole_cards.map((card, i) => (
                          <div key={i} className="scale-50 origin-left">
                            <Card card={card} />
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Folded Players - show who folded (no cards) */}
            {hasShowdown && foldedPlayers.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="bg-gray-200 rounded-xl p-2 mb-2"
              >
                <div className="text-gray-600 text-xs font-bold uppercase tracking-wide mb-1">
                  Folded Players
                </div>
                <div className="flex flex-wrap gap-1">
                  {foldedPlayers.map((player) => (
                    <span
                      key={player.player_id}
                      className="bg-gray-300 text-gray-700 px-2 py-0.5 rounded text-xs font-medium"
                    >
                      {player.name}
                    </span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* AI Strategy reveal (only for single AI winner who won by fold) */}
            {wonByFold && !isMultipleWinners && !winners[0].is_human && winners[0].personality && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-gray-900 rounded-xl p-3 mb-3 text-white"
              >
                <div className="text-yellow-400 text-xs font-bold uppercase tracking-wide mb-1">
                  🤖 AI Strategy Revealed
                </div>
                <div className="text-base font-semibold">
                  {winners[0].personality} Player
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
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
