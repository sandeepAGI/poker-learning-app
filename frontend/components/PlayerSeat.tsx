'use client';

import { motion } from 'framer-motion';
import { Card } from './Card';
import type { Player, AIDecision } from '../lib/types';

interface PlayerSeatProps {
  player: Player;
  isCurrentTurn: boolean;
  aiDecision?: AIDecision;
  showAiThinking: boolean; // UX Phase 1: Control AI reasoning visibility
  isShowdown?: boolean;
  isDealer?: boolean;         // Phase 0.5: Dealer button indicator
  isSmallBlind?: boolean;     // Phase 0.5: Small blind indicator
  isBigBlind?: boolean;       // Phase 0.5: Big blind indicator
}

export function PlayerSeat({
  player,
  isCurrentTurn,
  aiDecision,
  showAiThinking,
  isShowdown = false,
  isDealer = false,
  isSmallBlind = false,
  isBigBlind = false
}: PlayerSeatProps) {
  return (
    <motion.div
      className={`relative p-2 sm:p-3 md:p-4 rounded-lg ${
        isCurrentTurn ? 'bg-yellow-100 border-4 border-yellow-400' : 'bg-gray-100 border-2 border-gray-300'
      } ${!player.is_active ? 'opacity-50' : ''}`}
      animate={{
        scale: isCurrentTurn ? 1.05 : 1,
      }}
      transition={{ duration: 0.2 }}
    >
      {/* Phase 0.5: Button Indicators */}
      {isDealer && (
        <div className="absolute -top-3 -right-3 w-10 h-10 bg-white rounded-full border-4 border-amber-500 flex items-center justify-center text-sm font-bold shadow-lg z-10">
          D
        </div>
      )}

      {isSmallBlind && (
        <div className="absolute -top-3 -left-3 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-lg z-10">
          SB
        </div>
      )}

      {isBigBlind && (
        <div className="absolute -top-3 left-8 w-10 h-10 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-lg z-10">
          BB
        </div>
      )}

      {/* Player name and personality */}
      <div className="flex items-center gap-2 mb-2">
        <div className="font-semibold text-sm">{player.name}</div>
        {/* Only reveal AI strategy at showdown */}
        {player.personality && isShowdown && (
          <div className="text-xs bg-blue-200 px-2 py-0.5 rounded">{player.personality}</div>
        )}
        {player.all_in && <div className="text-xs bg-red-200 px-2 py-0.5 rounded">ALL-IN</div>}
      </div>

      {/* Cards */}
      <div className="flex gap-1 sm:gap-1.5 md:gap-2 mb-2 sm:mb-2.5 md:mb-3">
        {player.hole_cards.length > 0 ? (
          player.hole_cards.map((card, i) => <Card key={i} card={card} />)
        ) : (
          <>
            <Card card="" hidden />
            <Card card="" hidden />
          </>
        )}
      </div>

      {/* Stack and bet */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Stack:</span>
          <span className="text-lg font-bold">${player.stack}</span>
        </div>
        {player.current_bet > 0 && (
          <motion.div
            className="flex justify-between items-center text-green-700"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring' }}
          >
            <span className="text-sm">Bet:</span>
            <span className="text-base font-medium">${player.current_bet}</span>
          </motion.div>
        )}
      </div>

      {/* UX Phase 4: AI reasoning now shown in sidebar instead of inline */}
    </motion.div>
  );
}
