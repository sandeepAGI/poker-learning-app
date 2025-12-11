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
}

export function PlayerSeat({ player, isCurrentTurn, aiDecision, showAiThinking, isShowdown = false }: PlayerSeatProps) {
  return (
    <motion.div
      className={`relative p-4 rounded-lg ${
        isCurrentTurn ? 'bg-yellow-100 border-4 border-yellow-400' : 'bg-gray-100 border-2 border-gray-300'
      } ${!player.is_active ? 'opacity-50' : ''}`}
      animate={{
        scale: isCurrentTurn ? 1.05 : 1,
      }}
      transition={{ duration: 0.2 }}
    >
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
      <div className="flex gap-2 mb-3">
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
