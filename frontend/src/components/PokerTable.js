import React from 'react';
import { useGame } from '../store/gameStore';

const PokerTable = () => {
  const { state, computed } = useGame();

  const renderPlayerSeat = (player, index) => {
    const isCurrentPlayer = player.id === state.playerId;
    const isActivePlayer = index === state.currentPlayerIndex;
    const isDealer = index === state.dealerIndex;

    return (
      <div
        key={player.id}
        className={`absolute transform -translate-x-1/2 -translate-y-1/2 ${
          isCurrentPlayer ? 'border-2 border-blue-400' : 'border border-gray-600'
        } ${
          isActivePlayer ? 'bg-yellow-900' : 'bg-gray-800'
        } rounded-lg p-3 min-w-32`}
        style={{
          left: `${50 + 35 * Math.cos((index * 2 * Math.PI) / state.players.length)}%`,
          top: `${50 + 25 * Math.sin((index * 2 * Math.PI) / state.players.length)}%`
        }}
      >
        <div className="text-center">
          <div className="text-sm font-semibold text-white mb-1">
            {player.name}
            {isDealer && <span className="ml-1 text-yellow-400">D</span>}
          </div>
          <div className="text-xs text-green-400">${player.chips}</div>
          {player.current_bet > 0 && (
            <div className="text-xs text-yellow-400">Bet: ${player.current_bet}</div>
          )}
          <div className={`text-xs mt-1 ${
            player.status === 'active' ? 'text-green-400' : 
            player.status === 'folded' ? 'text-red-400' : 'text-gray-400'
          }`}>
            {player.status}
          </div>
          
          {/* Show cards for current player or if showCards is enabled */}
          {(isCurrentPlayer && player.hole_cards) && (
            <div className="mt-2 flex space-x-1 justify-center">
              {player.hole_cards.map((card, cardIndex) => (
                <div key={cardIndex} className="bg-white text-black text-xs px-1 py-1 rounded font-mono">
                  {card}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-green-700 rounded-xl p-8 relative" style={{ minHeight: '500px' }}>
      {/* Table border */}
      <div className="absolute inset-4 border-4 border-green-600 rounded-xl"></div>
      
      {/* Community cards */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <div className="text-center">
          <div className="text-white text-lg font-semibold mb-2">Community Cards</div>
          <div className="flex space-x-2 justify-center mb-4">
            {state.communityCards.length > 0 ? (
              state.communityCards.map((card, index) => (
                <div key={index} className="bg-white text-black px-3 py-4 rounded font-mono text-sm">
                  {card}
                </div>
              ))
            ) : (
              <div className="text-gray-400 text-sm">No cards dealt</div>
            )}
          </div>
          
          {/* Pot */}
          <div className="bg-yellow-600 text-black px-4 py-2 rounded-full font-bold">
            Pot: ${state.pot}
          </div>
          
          {/* Round state */}
          <div className="text-white text-sm mt-2 capitalize">
            {state.roundState.replace('_', ' ')}
          </div>
        </div>
      </div>

      {/* Player seats */}
      {state.players.map((player, index) => renderPlayerSeat(player, index))}

      {/* Game state indicator */}
      <div className="absolute top-4 left-4 bg-gray-800 px-3 py-1 rounded text-sm">
        <span className="text-gray-400">Game:</span>
        <span className="text-white ml-1 capitalize">{state.gameState}</span>
      </div>

      {/* Current bet indicator */}
      {state.currentBet > 0 && (
        <div className="absolute top-4 right-4 bg-blue-800 px-3 py-1 rounded text-sm">
          <span className="text-gray-400">Current Bet:</span>
          <span className="text-white ml-1">${state.currentBet}</span>
        </div>
      )}

      {/* Hand count */}
      <div className="absolute bottom-4 left-4 bg-gray-800 px-3 py-1 rounded text-sm">
        <span className="text-gray-400">Hand:</span>
        <span className="text-white ml-1">{state.handCount}</span>
      </div>

      {/* WebSocket status */}
      <div className="absolute bottom-4 right-4">
        <div className={`w-3 h-3 rounded-full ${
          computed.wsConnected ? 'bg-green-400' : 'bg-red-400'
        }`} title={computed.wsConnected ? 'Connected' : 'Disconnected'}></div>
      </div>
    </div>
  );
};

export default PokerTable;
