import React, { useState } from 'react';
import { PLAYER_ACTIONS } from '../store/gameStore';

const GameControls = ({ onAction, gameState, currentPlayer }) => {
  const [betAmount, setBetAmount] = useState(gameState.bigBlind);
  const [selectedAction, setSelectedAction] = useState(null);

  const handleAction = (action, amount = null) => {
    onAction(action, amount);
    setSelectedAction(null);
  };

  const canCheck = gameState.currentBet === 0 || (currentPlayer && currentPlayer.current_bet === gameState.currentBet);
  const canCall = gameState.currentBet > 0 && currentPlayer && currentPlayer.current_bet < gameState.currentBet;
  const callAmount = gameState.currentBet - (currentPlayer ? currentPlayer.current_bet : 0);
  const minRaise = gameState.currentBet + gameState.bigBlind;
  const maxBet = currentPlayer ? currentPlayer.chips : 0;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Your Turn</h3>
      
      {/* Action buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {/* Fold */}
        <button
          onClick={() => handleAction(PLAYER_ACTIONS.FOLD)}
          className="bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
        >
          Fold
        </button>

        {/* Check/Call */}
        {canCheck ? (
          <button
            onClick={() => handleAction(PLAYER_ACTIONS.CHECK)}
            className="bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
          >
            Check
          </button>
        ) : canCall ? (
          <button
            onClick={() => handleAction(PLAYER_ACTIONS.CALL)}
            className="bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
          >
            Call ${callAmount}
          </button>
        ) : (
          <button
            disabled
            className="bg-gray-600 text-gray-400 py-3 px-4 rounded-lg font-semibold cursor-not-allowed"
          >
            Call
          </button>
        )}

        {/* Bet/Raise */}
        <button
          onClick={() => setSelectedAction(selectedAction === 'bet' ? null : 'bet')}
          className={`py-3 px-4 rounded-lg font-semibold transition-colors ${
            selectedAction === 'bet'
              ? 'bg-yellow-600 text-white'
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {gameState.currentBet === 0 ? 'Bet' : 'Raise'}
        </button>

        {/* All-in */}
        <button
          onClick={() => handleAction(PLAYER_ACTIONS.ALL_IN)}
          className="bg-purple-600 hover:bg-purple-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors"
        >
          All-In
        </button>
      </div>

      {/* Bet amount controls */}
      {selectedAction === 'bet' && (
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {gameState.currentBet === 0 ? 'Bet Amount' : 'Raise To'}
            </label>
            <div className="flex items-center space-x-2">
              <span className="text-white">$</span>
              <input
                type="number"
                value={betAmount}
                onChange={(e) => setBetAmount(Math.max(minRaise, parseInt(e.target.value) || 0))}
                min={minRaise}
                max={maxBet}
                className="flex-1 px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white"
              />
              <span className="text-gray-400 text-sm">Max: ${maxBet}</span>
            </div>
          </div>

          {/* Quick bet buttons */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            <button
              onClick={() => setBetAmount(minRaise)}
              className="bg-gray-600 hover:bg-gray-500 text-white py-2 px-3 rounded text-sm"
            >
              Min
            </button>
            <button
              onClick={() => setBetAmount(Math.floor(gameState.pot / 2))}
              className="bg-gray-600 hover:bg-gray-500 text-white py-2 px-3 rounded text-sm"
            >
              1/2 Pot
            </button>
            <button
              onClick={() => setBetAmount(gameState.pot)}
              className="bg-gray-600 hover:bg-gray-500 text-white py-2 px-3 rounded text-sm"
            >
              Pot
            </button>
            <button
              onClick={() => setBetAmount(maxBet)}
              className="bg-gray-600 hover:bg-gray-500 text-white py-2 px-3 rounded text-sm"
            >
              All-In
            </button>
          </div>

          {/* Confirm bet */}
          <div className="flex space-x-2">
            <button
              onClick={() => handleAction(gameState.currentBet === 0 ? PLAYER_ACTIONS.BET : PLAYER_ACTIONS.RAISE, betAmount)}
              disabled={betAmount < minRaise || betAmount > maxBet}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white py-2 px-4 rounded font-semibold transition-colors"
            >
              {gameState.currentBet === 0 ? 'Bet' : 'Raise'} ${betAmount}
            </button>
            <button
              onClick={() => setSelectedAction(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Player info */}
      <div className="mt-4 text-sm text-gray-400">
        <div className="flex justify-between">
          <span>Your chips:</span>
          <span className="text-green-400">${currentPlayer ? currentPlayer.chips : 0}</span>
        </div>
        {gameState.currentBet > 0 && (
          <div className="flex justify-between">
            <span>Current bet:</span>
            <span className="text-yellow-400">${gameState.currentBet}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Pot:</span>
          <span className="text-white">${gameState.pot}</span>
        </div>
      </div>
    </div>
  );
};

export default GameControls;
  