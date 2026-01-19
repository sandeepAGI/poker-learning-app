'use client';

import { motion } from 'framer-motion';

interface CardProps {
  card: string; // e.g., "Ah", "Kd", "Qc", "Js"
  hidden?: boolean;
  'data-testid'?: string;
}

export function Card({ card, hidden = false, 'data-testid': testId }: CardProps) {
  // Parse card value and suit
  const getSuitSymbol = (suit: string) => {
    switch (suit) {
      case 'h': return '♥';
      case 'd': return '♦';
      case 'c': return '♣';
      case 's': return '♠';
      default: return '';
    }
  };

  const getSuitColor = (suit: string) => {
    return suit === 'h' || suit === 'd' ? 'text-red-600' : 'text-gray-900';
  };

  // Professional card back design (30% smaller for better table proportions)
  if (hidden) {
    return (
      <motion.div
        data-testid={testId || 'hidden-card'}
        className="w-8 h-12 sm:w-10 sm:h-15 md:w-11 md:h-17 bg-gradient-to-br from-blue-800 to-blue-900 border-2 border-blue-700 rounded-lg shadow-xl flex items-center justify-center relative overflow-hidden"
        initial={{ rotateY: 180 }}
        animate={{ rotateY: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* Card back pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="w-full h-full bg-gradient-to-br from-blue-400 to-transparent" />
        </div>
        {/* Center design */}
        <div className="text-white text-4xl opacity-40">♠</div>
      </motion.div>
    );
  }

  const value = card.slice(0, -1);
  const suit = card.slice(-1);
  const suitSymbol = getSuitSymbol(suit);
  const suitColor = getSuitColor(suit);

  return (
    <motion.div
      data-testid={testId || `card-${suit}${value}`}
      className="w-8 h-12 sm:w-10 sm:h-15 md:w-11 md:h-17 bg-white border-2 border-gray-300 rounded-lg shadow-xl relative"
      initial={{ scale: 0, rotateY: 180 }}
      animate={{ scale: 1, rotateY: 0 }}
      whileHover={{ scale: 1.05, y: -4 }}
      transition={{ duration: 0.3 }}
    >
      {/* Top-left corner: Rank + Suit */}
      <div className={`absolute top-0.5 left-0.5 sm:top-0.5 sm:left-1 ${suitColor}`}>
        <div className="text-xs sm:text-sm md:text-base font-bold leading-none">{value}</div>
        <div className="text-sm sm:text-base md:text-lg leading-none -mt-0.5">{suitSymbol}</div>
      </div>

      {/* Center: Large suit symbol (subtle) */}
      <div className={`absolute inset-0 flex items-center justify-center ${suitColor}`}>
        <div className="text-2xl sm:text-3xl md:text-4xl opacity-15">{suitSymbol}</div>
      </div>

      {/* Bottom-right corner: Rank + Suit (rotated 180°) */}
      <div className={`absolute bottom-0.5 right-0.5 sm:bottom-0.5 sm:right-1 ${suitColor} transform rotate-180`}>
        <div className="text-xs sm:text-sm md:text-base font-bold leading-none">{value}</div>
        <div className="text-sm sm:text-base md:text-lg leading-none -mt-0.5">{suitSymbol}</div>
      </div>
    </motion.div>
  );
}
