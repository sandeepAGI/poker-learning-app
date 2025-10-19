'use client';

import { motion } from 'framer-motion';
import { Card } from './Card';
import { PlayerSeat } from './PlayerSeat';
import { useGameStore } from '../lib/store';
import { useState } from 'react';

export function PokerTable() {
  const { gameState, beginnerMode, submitAction, nextHand, toggleBeginnerMode, loading, error } = useGameStore();
  const [raiseAmount, setRaiseAmount] = useState(0);

  if (!gameState) return null;

  const isMyTurn = gameState.human_player.is_current_turn && gameState.human_player.is_active;
  const isShowdown = gameState.state === 'showdown';
  const minRaise = gameState.current_bet + 10; // Assuming 10 is big blind

  return (
    <div className="flex flex-col h-screen bg-green-800 p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4 text-white">
        <div>
          <h1 className="text-2xl font-bold">Poker Learning App</h1>
          <div className="text-sm opacity-80">Game State: {gameState.state.toUpperCase()}</div>
        </div>
        <button
          onClick={toggleBeginnerMode}
          className="bg-white text-green-800 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100"
        >
          {beginnerMode ? 'Beginner Mode' : 'Expert Mode'}
        </button>
      </div>

      {/* Error display */}
      {error && (
        <motion.div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {error}
        </motion.div>
      )}

      {/* Main table */}
      <div className="flex-1 flex flex-col">
        {/* AI Players (top row) */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          {gameState.players
            .filter((p) => !p.is_human)
            .map((player) => (
              <PlayerSeat
                key={player.player_id}
                player={player}
                isCurrentTurn={gameState.players[gameState.current_player_index]?.player_id === player.player_id}
                aiDecision={gameState.last_ai_decisions[player.player_id]}
                beginnerMode={beginnerMode}
              />
            ))}
        </div>

        {/* Community cards and pot (center) */}
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Pot */}
          <motion.div
            className="bg-yellow-500 text-white px-6 py-3 rounded-full text-2xl font-bold mb-4 shadow-lg"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 1, repeat: Infinity, repeatDelay: 2 }}
          >
            Pot: ${gameState.pot}
          </motion.div>

          {/* Community cards */}
          {gameState.community_cards.length > 0 && (
            <div className="flex gap-2 mb-4">
              {gameState.community_cards.map((card, i) => (
                <Card key={i} card={card} />
              ))}
            </div>
          )}

          {/* Current bet */}
          {gameState.current_bet > 0 && (
            <div className="text-white text-lg">
              Current Bet: <span className="font-bold">${gameState.current_bet}</span>
            </div>
          )}
        </div>

        {/* Human player (bottom) */}
        <div className="mb-4">
          <PlayerSeat
            player={gameState.human_player}
            isCurrentTurn={isMyTurn}
            beginnerMode={beginnerMode}
          />
        </div>

        {/* Action buttons */}
        <div className="bg-gray-900 p-4 rounded-lg">
          {isShowdown ? (
            <button
              onClick={() => nextHand()}
              disabled={loading}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-lg text-lg disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Next Hand'}
            </button>
          ) : isMyTurn ? (
            <div className="flex gap-4">
              {/* Fold */}
              <button
                onClick={() => submitAction('fold')}
                disabled={loading}
                className="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold py-4 px-6 rounded-lg disabled:opacity-50"
              >
                Fold
              </button>

              {/* Call */}
              <button
                onClick={() => submitAction('call')}
                disabled={loading}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-lg disabled:opacity-50"
              >
                Call ${gameState.current_bet - gameState.human_player.current_bet}
              </button>

              {/* Raise */}
              <div className="flex-1 flex gap-2">
                <input
                  type="number"
                  value={raiseAmount}
                  onChange={(e) => setRaiseAmount(parseInt(e.target.value) || 0)}
                  min={minRaise}
                  max={gameState.human_player.stack}
                  className="flex-1 px-4 py-2 rounded-lg text-black"
                  placeholder={`Min $${minRaise}`}
                />
                <button
                  onClick={() => submitAction('raise', raiseAmount)}
                  disabled={loading || raiseAmount < minRaise}
                  className="bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-lg disabled:opacity-50"
                >
                  Raise
                </button>
              </div>
            </div>
          ) : (
            <div className="text-white text-center py-4">
              {loading ? 'Processing...' : "Waiting for other players..."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
