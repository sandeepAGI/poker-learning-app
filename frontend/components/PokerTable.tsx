'use client';

import { motion } from 'framer-motion';
import { Card } from './Card';
import { PlayerSeat } from './PlayerSeat';
import { WinnerModal } from './WinnerModal';
import { AnalysisModal } from './AnalysisModal';
import { useGameStore } from '../lib/store';
import { useState, useEffect } from 'react';

export function PokerTable() {
  const {
    gameState,
    showAiThinking,
    handAnalysis,
    submitAction,
    nextHand,
    toggleShowAiThinking,
    getHandAnalysis,
    quitGame,
    loading,
    error
  } = useGameStore();

  if (!gameState) return null;

  // Fix: Don't show actions if player has no chips (all-in or busted)
  const isMyTurn = gameState.human_player.is_current_turn &&
                   gameState.human_player.is_active &&
                   gameState.human_player.stack > 0;
  const isShowdown = gameState.state === 'showdown';

  // Bug Fix #1: Proper call amount calculation (prevent negative)
  const callAmount = Math.max(0, gameState.current_bet - gameState.human_player.current_bet);
  const canCall = gameState.human_player.stack >= callAmount;

  // Bug Fix #1: Proper raise amount validation
  const minRaise = gameState.current_bet + (gameState.big_blind || 10);
  const maxRaise = gameState.human_player.stack;
  const canRaise = maxRaise >= minRaise && gameState.human_player.stack > callAmount;

  const [raiseAmount, setRaiseAmount] = useState(minRaise);
  const [showWinnerModal, setShowWinnerModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);

  // Check if player is all-in (has chips invested but stack = 0)
  const isAllIn = gameState.human_player.current_bet > 0 && gameState.human_player.stack === 0;

  // Bug Fix #3: Check if player is busted (not in game anymore)
  const isBusted = gameState.human_player.stack === 0 && !gameState.human_player.is_active;

  // Update raise amount when minRaise changes (new betting round, someone raises, etc.)
  useEffect(() => {
    setRaiseAmount(minRaise);
  }, [minRaise]);

  // Issue #5 fix: Validate and cap raise amount
  const handleRaiseAmountChange = (value: number) => {
    // Cap between minRaise and maxRaise
    const capped = Math.max(minRaise, Math.min(value, maxRaise));
    setRaiseAmount(capped);
  };

  // Issue #3 fix: All-in button handler
  const handleAllIn = () => {
    setRaiseAmount(maxRaise);
    submitAction('raise', maxRaise);
  };

  // Show winner modal when winner_info is available
  useEffect(() => {
    if (gameState.winner_info) {
      setShowWinnerModal(true);
    }
  }, [gameState.winner_info]);

  // Handle winner modal close - advance to next hand
  const handleWinnerModalClose = () => {
    setShowWinnerModal(false);
    nextHand();
  };

  // UX Phase 2: Handle analysis button click
  const handleAnalysisClick = async () => {
    await getHandAnalysis();
    // Only show modal if analysis was successfully fetched (checked in next useEffect)
  };

  // Show analysis modal when analysis is available (and not null)
  useEffect(() => {
    if (handAnalysis && !showAnalysisModal) {
      setShowAnalysisModal(true);
    }
  }, [handAnalysis]);

  return (
    <div className="flex flex-col h-screen bg-green-800 p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4 text-white">
        <div>
          <h1 className="text-2xl font-bold">Poker Learning App</h1>
          <div className="text-sm opacity-80">Game State: {gameState.state.toUpperCase()}</div>
          {/* Issue #1 fix: Display blind levels and hand count */}
          <div className="text-sm opacity-80 mt-1">
            Hand #{gameState.hand_count || 1} | Blinds: ${gameState.small_blind || 5}/${gameState.big_blind || 10}
          </div>
        </div>

        {/* UX Controls */}
        <div className="flex gap-2">
          {/* UX Phase 2: Analyze Last Hand button */}
          <button
            onClick={handleAnalysisClick}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-50"
            title="Analyze your last hand to learn from your decisions"
          >
            📊 Analyze Hand
          </button>

          {/* UX Phase 1: Toggle AI Thinking */}
          <button
            onClick={toggleShowAiThinking}
            className={`px-4 py-2 rounded-lg font-semibold ${
              showAiThinking
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-white text-green-800 hover:bg-gray-100'
            }`}
            title="Toggle AI reasoning visibility"
          >
            {showAiThinking ? '🤖 Hide AI Thinking' : '🤖 Show AI Thinking'}
          </button>

          {/* Bug Fix #2: Quit Game button */}
          <button
            onClick={quitGame}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold"
            title="Quit game and return to lobby"
          >
            ❌ Quit
          </button>
        </div>
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
                showAiThinking={showAiThinking}
                isShowdown={isShowdown}
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
            showAiThinking={showAiThinking}
            isShowdown={isShowdown}
          />
        </div>

        {/* Action buttons */}
        <div className="bg-gray-900 p-4 rounded-lg">
          {/* Bug Fix #3: Show game state to busted players */}
          {isBusted ? (
            <div className="text-center py-4">
              <div className="text-red-400 font-bold text-xl mb-2">💀 You're Out!</div>
              <div className="text-white text-sm mb-4">
                You've been eliminated from the game. Watch the remaining players compete!
              </div>
              {isShowdown && (
                <button
                  onClick={() => nextHand()}
                  disabled={loading}
                  className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Next Hand'}
                </button>
              )}
            </div>
          ) : isShowdown ? (
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

              {/* Call - Bug Fix #1: Use validated callAmount */}
              <button
                onClick={() => submitAction('call')}
                disabled={loading || !canCall}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-lg disabled:opacity-50"
                title={!canCall ? 'Not enough chips to call' : ''}
              >
                Call ${callAmount}
              </button>

              {/* Raise - Bug Fix #1: Better validation */}
              {canRaise ? (
                <div className="flex-1 flex flex-col gap-2">
                  <div className="flex gap-2">
                    <div className="flex-1 flex flex-col">
                      <label className="text-white text-sm mb-1 font-semibold">Raise Amount:</label>
                      <input
                        type="number"
                        value={raiseAmount}
                        onChange={(e) => handleRaiseAmountChange(parseInt(e.target.value) || minRaise)}
                        min={minRaise}
                        max={maxRaise}
                        disabled={loading}
                        className="w-full px-4 py-4 rounded-lg bg-gray-900 text-white text-xl font-bold border-4 border-green-400 focus:border-green-300 focus:outline-none text-center placeholder-gray-400 disabled:opacity-50"
                        placeholder={`Min $${minRaise}`}
                      />
                      <div className="text-white text-xs mt-1">
                        Min: ${minRaise} | Max: ${maxRaise}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2">
                      {/* All-In button */}
                      <button
                        onClick={handleAllIn}
                        disabled={loading}
                        className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-2 px-6 rounded-lg disabled:opacity-50 whitespace-nowrap"
                        title="Go all-in with your entire stack"
                      >
                        All-In (${maxRaise})
                      </button>
                      <button
                        onClick={() => submitAction('raise', raiseAmount)}
                        disabled={loading || raiseAmount < minRaise || raiseAmount > maxRaise}
                        className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-6 rounded-lg disabled:opacity-50"
                      >
                        Raise
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 bg-gray-800 rounded-lg flex items-center justify-center text-gray-400 text-sm">
                  {gameState.human_player.stack <= callAmount
                    ? 'Call or fold only (not enough chips to raise)'
                    : 'Raise not available'}
                </div>
              )}
            </div>
          ) : (
            <div className="text-white text-center py-4">
              {loading ? 'Processing...' : isAllIn ? "All-In! Waiting for hand to complete..." : "Waiting for other players..."}
            </div>
          )}
        </div>
      </div>

      {/* Winner announcement modal */}
      {gameState.winner_info && (
        <WinnerModal
          isOpen={showWinnerModal}
          winner={gameState.players.find(p => p.player_id === gameState.winner_info?.player_id) || null}
          amount={gameState.winner_info.amount}
          onClose={handleWinnerModalClose}
        />
      )}

      {/* UX Phase 2: Hand analysis modal */}
      <AnalysisModal
        isOpen={showAnalysisModal}
        analysis={handAnalysis}
        onClose={() => setShowAnalysisModal(false)}
      />
    </div>
  );
}
