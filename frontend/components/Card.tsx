'use client';

import { motion } from 'framer-motion';

interface CardProps {
  card: string; // e.g., "Ah", "Kd", "Qc", "Js"
  hidden?: boolean;
}

export function Card({ card, hidden = false }: CardProps) {
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

  if (hidden) {
    return (
      <motion.div
        className="w-14 h-20 bg-blue-600 border-2 border-blue-700 rounded-lg shadow-lg flex items-center justify-center"
        initial={{ rotateY: 180 }}
        animate={{ rotateY: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="text-white text-2xl">🂠</div>
      </motion.div>
    );
  }

  const value = card.slice(0, -1);
  const suit = card.slice(-1);
  const suitSymbol = getSuitSymbol(suit);
  const suitColor = getSuitColor(suit);

  return (
    <motion.div
      className="w-14 h-20 bg-white border-2 border-gray-300 rounded-lg shadow-lg p-1 flex flex-col items-center justify-between"
      initial={{ scale: 0, rotateY: 180 }}
      animate={{ scale: 1, rotateY: 0 }}
      whileHover={{ scale: 1.05, y: -2 }}
      transition={{ duration: 0.3 }}
    >
      <div className={`${suitColor} font-bold text-lg`}>{value}</div>
      <div className={`${suitColor} text-2xl`}>{suitSymbol}</div>
      <div className={`${suitColor} font-bold text-lg`}>{value}</div>
    </motion.div>
  );
}
