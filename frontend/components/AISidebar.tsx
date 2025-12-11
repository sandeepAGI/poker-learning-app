'use client';

import { motion, AnimatePresence } from 'framer-motion';
import type { AIDecision } from '../lib/types';

interface AIDecisionEntry {
  playerName: string;
  playerId: string;
  decision: AIDecision;
  timestamp: number;
}

interface AISidebarProps {
  isOpen: boolean;
  decisions: AIDecisionEntry[];
}

export function AISidebar({ isOpen, decisions }: AISidebarProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 320, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="hidden md:flex bg-[#0A4D26]/95 backdrop-blur-sm border-l-2 border-[#1F7A47] overflow-hidden flex-col"
        >
          <div className="flex-1 overflow-y-auto p-4">
            {/* Header */}
            <div className="sticky top-0 bg-[#0A4D26] pb-3 mb-3 border-b border-[#1F7A47]">
              <h3 className="text-white font-bold text-lg">🤖 AI Reasoning Stream</h3>
              <p className="text-xs text-gray-400 mt-1">
                {decisions.length} decision{decisions.length !== 1 ? 's' : ''} this hand
              </p>
            </div>

            {/* Decision Stream */}
            <div className="space-y-3">
              {decisions.length === 0 ? (
                <div className="text-gray-400 text-sm text-center py-8">
                  No AI decisions yet this hand
                </div>
              ) : (
                decisions.map((entry, i) => (
                  <motion.div
                    key={`${entry.playerId}-${entry.timestamp}`}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="bg-[#1F7A47]/40 backdrop-blur-sm rounded-lg p-3 border border-[#1F7A47]"
                  >
                    {/* Player Name & Action */}
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-semibold text-sm">
                        {entry.playerName}
                      </span>
                      <span className={`text-xs font-bold px-2 py-1 rounded ${
                        entry.decision.action === 'fold'
                          ? 'bg-[#DC2626] text-white'
                          : entry.decision.action === 'call'
                          ? 'bg-[#2563EB] text-white'
                          : 'bg-[#10B981] text-white'
                      }`}>
                        {entry.decision.action.toUpperCase()}
                        {entry.decision.amount > 0 && ` $${entry.decision.amount}`}
                      </span>
                    </div>

                    {/* Reasoning */}
                    <div className="text-gray-200 text-xs italic mb-2 leading-relaxed">
                      "{entry.decision.reasoning}"
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-3 gap-2 text-[10px] text-gray-300">
                      <div className="bg-[#0A4D26]/60 rounded px-2 py-1">
                        <div className="text-gray-400">SPR</div>
                        <div className="font-bold text-[#FCD34D]">
                          {entry.decision.spr.toFixed(1)}
                        </div>
                      </div>
                      <div className="bg-[#0A4D26]/60 rounded px-2 py-1">
                        <div className="text-gray-400">Pot Odds</div>
                        <div className="font-bold text-[#FCD34D]">
                          {(entry.decision.pot_odds * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="bg-[#0A4D26]/60 rounded px-2 py-1">
                        <div className="text-gray-400">Hand</div>
                        <div className="font-bold text-[#FCD34D]">
                          {(entry.decision.hand_strength * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
