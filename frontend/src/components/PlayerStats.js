import React from 'react';
import { useGame } from '../store/gameStore';

const PlayerStats = () => {
  const { state, computed } = useGame();

  const currentPlayer = state.players.find(p => p.id === state.playerId);

  if (!currentPlayer) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Player Stats</h3>
        <p className="text-gray-400">No player data available</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-4">Your Stats</h3>
      
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400">Chips:</span>
          <span className="text-green-400 font-semibold">${currentPlayer.chips}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Position:</span>
          <span className="text-white">{currentPlayer.position || 'N/A'}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Status:</span>
          <span className={`capitalize ${
            currentPlayer.status === 'active' ? 'text-green-400' : 
            currentPlayer.status === 'folded' ? 'text-red-400' : 'text-gray-400'
          }`}>
            {currentPlayer.status}
          </span>
        </div>

        {currentPlayer.hole_cards && (
          <div>
            <span className="text-gray-400 block mb-2">Your Cards:</span>
            <div className="flex space-x-1">
              {currentPlayer.hole_cards.map((card, index) => (
                <div key={index} className="bg-white text-black text-xs px-2 py-1 rounded font-mono">
                  {card}
                </div>
              ))}
            </div>
          </div>
        )}

        {currentPlayer.current_bet > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-400">Current Bet:</span>
            <span className="text-yellow-400">${currentPlayer.current_bet}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlayerStats;