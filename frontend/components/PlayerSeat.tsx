'use client';

import { motion } from 'framer-motion';
import { Card } from './Card';
import type { Player, AIDecision } from '../lib/types';

interface PlayerSeatProps {
  player: Player;
  isCurrentTurn: boolean;
  aiDecision?: AIDecision;
  beginnerMode: boolean;
}

export function PlayerSeat({ player, isCurrentTurn, aiDecision, beginnerMode }: PlayerSeatProps) {
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
        <div className="font-bold text-sm">{player.name}</div>
        {player.personality && (
          <div className="text-xs bg-blue-200 px-2 py-0.5 rounded">{player.personality}</div>
        )}
        {player.all_in && <div className="text-xs bg-red-200 px-2 py-0.5 rounded">ALL-IN</div>}
      </div>

      {/* Cards */}
      <div className="flex gap-1 mb-2">
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
      <div className="text-sm space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-600">Stack:</span>
          <span className="font-semibold">${player.stack}</span>
        </div>
        {player.current_bet > 0 && (
          <motion.div
            className="flex justify-between text-green-700"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring' }}
          >
            <span>Bet:</span>
            <span className="font-semibold">${player.current_bet}</span>
          </motion.div>
        )}
      </div>

      {/* AI Decision reasoning */}
      {aiDecision && (
        <motion.div
          className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.3 }}
        >
          <div className="font-semibold mb-1">
            Action: {aiDecision.action.toUpperCase()}{' '}
            {aiDecision.amount > 0 && `$${aiDecision.amount}`}
          </div>
          <div className="text-gray-700">
            {beginnerMode ? aiDecision.beginner_reasoning : aiDecision.reasoning}
          </div>
          <div className="mt-1 text-gray-500 text-[10px]">
            SPR: {aiDecision.spr.toFixed(1)} | Pot Odds: {(aiDecision.pot_odds * 100).toFixed(0)}% |
            Hand: {(aiDecision.hand_strength * 100).toFixed(0)}%
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
