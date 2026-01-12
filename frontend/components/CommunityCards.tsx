'use client';

import { motion } from 'framer-motion';
import { Card } from './Card';

interface CommunityCardsProps {
  cards: string[];
  gameState: string;
}

export function CommunityCards({ cards, gameState }: CommunityCardsProps) {
  if (cards.length === 0) return null;

  // Determine stage label
  let stageLabel = '';
  if (cards.length === 3 && gameState === 'flop') {
    stageLabel = 'FLOP';
  } else if (cards.length === 4 && gameState === 'turn') {
    stageLabel = 'TURN';
  } else if (cards.length === 5 && gameState === 'river') {
    stageLabel = 'RIVER';
  }

  return (
    <div data-testid="community-cards-container" className="flex flex-col items-center">
      {/* Stage Label */}
      {stageLabel && (
        <motion.div
          data-testid="stage-label"
          className="text-[#FCD34D] font-bold text-base mb-2 tracking-wider"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {stageLabel}
        </motion.div>
      )}

      {/* Community Cards Container */}
      <motion.div
        className="bg-[#0A4D26]/80 backdrop-blur-sm px-2 py-2 sm:px-4 sm:py-3 md:px-6 md:py-4 rounded-xl border-2 border-[#1F7A47]/60 shadow-2xl"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div data-testid="community-cards-list" className="flex gap-1 sm:gap-2 md:gap-3">
          {cards.map((card, i) => (
            <motion.div
              key={i}
              initial={{ scale: 0, rotateY: 180 }}
              animate={{ scale: 1, rotateY: 0 }}
              transition={{
                delay: i * 0.15,
                type: 'spring',
                stiffness: 200,
                damping: 15
              }}
            >
              <Card card={card} data-testid={`community-card-${i}`} />
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
