'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Card } from './Card';
import { PlayerSeat } from './PlayerSeat';
import { CommunityCards } from './CommunityCards';
import { WinnerModal } from './WinnerModal';
import { AnalysisModal } from './AnalysisModal';
import { GameOverModal } from './GameOverModal';
import { useGameStore } from '../lib/store';
import { useState, useEffect } from 'react';

export function PokerTable() {
  const {
    gameState,
    showAiThinking,
    handAnalysis,
    stepMode,
    awaitingContinue,
    submitAction,
    nextHand,
    toggleShowAiThinking,
    toggleStepMode,
    sendContinue,
    getHandAnalysis,
    quitGame,
    loading,
    error,
    connectionState
  } = useGameStore();

  if (!gameState) return null;

  // Fix: Don't show actions if player has no chips (all-in or busted)
  const isMyTurn = !!(gameState.human_player.is_current_turn &&
                   gameState.human_player.is_active &&
                   gameState.human_player.stack > 0);
  const isShowdown = gameState.state === 'showdown';

  // Bug Fix #1: Proper call amount calculation (prevent negative)
  const callAmount = Math.max(0, gameState.current_bet - gameState.human_player.current_bet);
  const canCall = gameState.human_player.stack >= callAmount;

  // Bug Fix #1: Proper raise amount validation
  const minRaise = gameState.current_bet + (gameState.big_blind || 10);
  // Bug Fix: All-in must include current bet (e.g., big blind already posted)
  const maxRaise = gameState.human_player.stack + gameState.human_player.current_bet;
  const canRaise = maxRaise >= minRaise && gameState.human_player.stack > callAmount;

  const [raiseAmount, setRaiseAmount] = useState(minRaise);
  const [showWinnerModal, setShowWinnerModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [showGameOverModal, setShowGameOverModal] = useState(false);
  const [showRaisePanel, setShowRaisePanel] = useState(false);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);

  // Check if player is all-in (has chips invested but stack = 0)
  const isAllIn = gameState.human_player.all_in ||
                  (gameState.human_player.current_bet > 0 && gameState.human_player.stack === 0);

  // Bug Fix #3: Check if player is busted (not in game anymore)
  const isBusted = gameState.human_player.stack === 0 && !gameState.human_player.is_active;

  // Feature: Detect when human player is eliminated (game over)
  // Bug Fix #10: Properly detect elimination:
  // - stack=0 and NOT all-in → eliminated (busted out without going all-in)
  // - stack=0 and all-in and at showdown → eliminated (lost the all-in)
  // - stack=0 and all-in and NOT showdown → NOT eliminated (waiting for hand to complete)
  const isEliminated = gameState.human_player.stack === 0 &&
                       (!gameState.human_player.all_in || isShowdown);

  // Player is all-in and waiting for hand to complete
  const isWaitingAllIn = gameState.human_player.all_in && !isShowdown && gameState.human_player.stack === 0;

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
    try {
      await getHandAnalysis();
      // Only show modal if analysis was successfully fetched (checked in next useEffect)
    } catch (error) {
      // Error is already handled in store.ts (sets error state)
      // This catch prevents Next.js error overlay in development mode
      console.log('Analysis fetch handled by store');
    }
  };

  // Show analysis modal when analysis is available (and not null)
  useEffect(() => {
    if (handAnalysis && !showAnalysisModal) {
      setShowAnalysisModal(true);
    }
  }, [handAnalysis]);

  // Show game over modal when human player is eliminated
  useEffect(() => {
    if (isEliminated && isShowdown && !showGameOverModal) {
      // Wait a moment to let the last showdown complete
      const timer = setTimeout(() => {
        setShowGameOverModal(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isEliminated, isShowdown, showGameOverModal]);

  // Handle new game after elimination
  const handleNewGame = () => {
    setShowGameOverModal(false);
    quitGame(); // Return to lobby to start fresh game
  };

  // Phase 4: Debug - Log when awaitingContinue changes
  useEffect(() => {
    console.log('[PokerTable] awaitingContinue changed to:', awaitingContinue);
    if (awaitingContinue) {
      console.log('[PokerTable] Continue button SHOULD BE VISIBLE NOW');
    }
  }, [awaitingContinue]);

  // Phase 4: Debug - Log when stepMode changes
  useEffect(() => {
    console.log('[PokerTable] stepMode changed to:', stepMode);
  }, [stepMode]);

  // Phase 2C: Close settings menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showSettingsMenu) {
        const target = event.target as HTMLElement;
        if (!target.closest('.settings-menu-container')) {
          setShowSettingsMenu(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSettingsMenu]);

  return (
    <div className="flex flex-col h-screen bg-[#0D5F2F] p-2 sm:p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-2 sm:mb-4 text-white">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold">Poker Learning App</h1>
          <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm opacity-80">
            <span className="hidden sm:inline">Game State: {gameState.state.toUpperCase()}</span>
            {/* WebSocket connection status */}
            <span className="flex items-center gap-1">
              {connectionState === 'connected' && <span className="text-green-400">● Connected</span>}
              {connectionState === 'connecting' && <span className="text-yellow-400">⟳ Connecting...</span>}
              {connectionState === 'reconnecting' && <span className="text-orange-400">⟳ Reconnecting...</span>}
              {connectionState === 'disconnected' && <span className="text-gray-400">○ Disconnected</span>}
              {connectionState === 'failed' && <span className="text-red-400">✗ Connection Failed</span>}
            </span>
          </div>
          {/* Issue #1 fix: Display blind levels and hand count */}
          <div className="text-sm opacity-80 mt-1">
            Hand #{gameState.hand_count || 1} | Blinds: ${gameState.small_blind || 5}/${gameState.big_blind || 10}
            {/* Debug: Show step mode state */}
            {stepMode && <span className="ml-2 text-yellow-300">| Step Mode: ON</span>}
            {awaitingContinue && <span className="ml-2 text-green-300 font-bold">| WAITING FOR CONTINUE</span>}
          </div>
        </div>

        {/* Header Controls - Consolidated */}
        <div className="flex gap-3 items-center relative settings-menu-container">
          {/* Phase 4: Continue button (shown only in Step Mode when waiting) */}
          {awaitingContinue && (
            <motion.button
              onClick={() => {
                console.log('[PokerTable] Continue button clicked!');
                sendContinue();
              }}
              className="bg-[#10B981] hover:bg-[#059669] text-white px-6 py-2 rounded-lg font-bold shadow-lg border-2 border-white"
              title="Continue to next AI action"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              ▶️ Continue
            </motion.button>
          )}

          {/* Settings Menu Button */}
          <button
            onClick={() => setShowSettingsMenu(!showSettingsMenu)}
            className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2"
            title="Game settings and options"
          >
            ⚙️ Settings
          </button>

          {/* Settings Dropdown Menu */}
          {showSettingsMenu && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute top-12 right-20 bg-[#0A4D26]/95 backdrop-blur-sm border-2 border-[#1F7A47] rounded-lg shadow-2xl p-2 min-w-[250px] z-50"
            >
              {/* Analyze Hand */}
              <button
                onClick={() => {
                  handleAnalysisClick();
                  setShowSettingsMenu(false);
                }}
                disabled={loading}
                className="w-full text-left px-4 py-3 hover:bg-[#1F7A47] rounded-lg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                📊 Analyze Hand
              </button>

              {/* Toggle AI Thinking */}
              <button
                onClick={() => {
                  toggleShowAiThinking();
                  setShowSettingsMenu(false);
                }}
                className="w-full text-left px-4 py-3 hover:bg-[#1F7A47] rounded-lg text-white font-medium flex items-center gap-2"
              >
                <span className={showAiThinking ? 'text-[#FCD34D]' : 'text-gray-400'}>
                  {showAiThinking ? '✓' : '○'}
                </span>
                🤖 Show AI Thinking
              </button>

              {/* Toggle Step Mode */}
              <button
                onClick={() => {
                  toggleStepMode();
                  setShowSettingsMenu(false);
                }}
                className="w-full text-left px-4 py-3 hover:bg-[#1F7A47] rounded-lg text-white font-medium flex items-center gap-2"
              >
                <span className={stepMode ? 'text-[#FCD34D]' : 'text-gray-400'}>
                  {stepMode ? '✓' : '○'}
                </span>
                {stepMode ? '⏸️ Step Mode (ON)' : '▶️ Step Mode (OFF)'}
              </button>
            </motion.div>
          )}

          {/* Quit Game button */}
          <button
            onClick={quitGame}
            className="bg-[#DC2626] hover:bg-[#B91C1C] text-white px-4 py-2 rounded-lg font-semibold"
            title="Quit game and return to lobby"
          >
            ❌ Quit
          </button>
        </div>
      </div>

      {/* Phase 4: Step Mode - Awaiting Continue Banner */}
      {awaitingContinue && (
        <motion.div
          className="bg-yellow-100 border-2 border-yellow-600 text-yellow-900 px-4 py-3 rounded mb-4 text-center font-bold"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          ⏸️ PAUSED - Click the green "Continue" button to see the next AI action
        </motion.div>
      )}

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

      {/* Main table - Circular Layout */}
      <div className="flex-1 relative">
        {/* Extract opponents into array for easier positioning */}
        {(() => {
          const opponents = gameState.players.filter((p) => !p.is_human);

          return (
            <>
              {/* Opponent 1 - Left Side (clockwise from human) */}
              {opponents[0] && (
                <div className="absolute top-1/3 left-8">
                  <PlayerSeat
                    key={opponents[0].player_id}
                    player={opponents[0]}
                    isCurrentTurn={gameState.current_player_index !== null && gameState.players[gameState.current_player_index]?.player_id === opponents[0].player_id}
                    aiDecision={gameState.last_ai_decisions[opponents[0].player_id]}
                    showAiThinking={showAiThinking}
                    isShowdown={isShowdown}
                  />
                </div>
              )}

              {/* Opponent 2 - Top Center (clockwise from opponent 1) */}
              {opponents[1] && (
                <div className="absolute top-8 left-1/2 -translate-x-1/2">
                  <PlayerSeat
                    key={opponents[1].player_id}
                    player={opponents[1]}
                    isCurrentTurn={gameState.current_player_index !== null && gameState.players[gameState.current_player_index]?.player_id === opponents[1].player_id}
                    aiDecision={gameState.last_ai_decisions[opponents[1].player_id]}
                    showAiThinking={showAiThinking}
                    isShowdown={isShowdown}
                  />
                </div>
              )}

              {/* Opponent 3 - Right Side (clockwise from opponent 2) */}
              {opponents[2] && (
                <div className="absolute top-1/3 right-8">
                  <PlayerSeat
                    key={opponents[2].player_id}
                    player={opponents[2]}
                    isCurrentTurn={gameState.current_player_index !== null && gameState.players[gameState.current_player_index]?.player_id === opponents[2].player_id}
                    aiDecision={gameState.last_ai_decisions[opponents[2].player_id]}
                    showAiThinking={showAiThinking}
                    isShowdown={isShowdown}
                  />
                </div>
              )}
            </>
          );
        })()}

        {/* Center Area - Community Cards and Pot */}
        <div className="absolute top-[40%] left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-6">
          {/* Pot */}
          <motion.div
            className="bg-[#D97706] text-white px-6 py-3 rounded-full text-3xl font-bold shadow-2xl"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 1, repeat: Infinity, repeatDelay: 2 }}
          >
            Pot: ${gameState.pot}
          </motion.div>

          {/* Community cards - Using new dedicated component */}
          <CommunityCards
            cards={gameState.community_cards}
            gameState={gameState.state}
          />

          {/* Current bet */}
          {gameState.current_bet > 0 && (
            <div className="text-white text-lg font-semibold">
              Current Bet: <span className="font-bold text-[#FCD34D]">${gameState.current_bet}</span>
            </div>
          )}
        </div>

        {/* Human Player - Bottom (moved lower to avoid overlap) */}
        <div className="absolute bottom-44 left-1/2 -translate-x-1/2">
          <PlayerSeat
            player={gameState.human_player}
            isCurrentTurn={isMyTurn}
            showAiThinking={showAiThinking}
            isShowdown={isShowdown}
          />
        </div>

        {/* Action buttons - Absolute positioned at bottom */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4">
          <div className="bg-[#0A4D26]/90 backdrop-blur-sm border-2 border-[#1F7A47] p-4 rounded-lg">
          {/* Feature: Game over when eliminated - don't show controls */}
          {isEliminated ? (
            <div className="text-center py-4">
              <div className="text-red-400 font-bold text-xl mb-2">💀 Game Over</div>
              <div className="text-white text-sm">
                You've been eliminated. Game ending...
              </div>
            </div>
          ) : isWaitingAllIn ? (
            /* Bug Fix #10: Show waiting message when all-in */
            <div className="text-center py-4">
              <div className="text-yellow-400 font-bold text-xl mb-2">🎲 All-In!</div>
              <div className="text-white text-sm">
                Waiting for hand to complete...
              </div>
            </div>
          ) : isShowdown ? (
            <button
              onClick={() => nextHand()}
              disabled={loading}
              className="w-full bg-[#10B981] hover:bg-[#059669] text-white font-bold py-4 px-6 rounded-lg text-lg disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Next Hand'}
            </button>
          ) : isMyTurn ? (
            <div className="flex flex-col gap-3">
              {/* Primary Action Buttons - Simplified 3-button layout */}
              <div className="flex gap-4">
                {/* Fold */}
                <button
                  onClick={() => submitAction('fold')}
                  disabled={loading}
                  className="flex-1 bg-[#DC2626] hover:bg-[#B91C1C] text-white font-bold py-4 sm:py-5 px-4 sm:px-6 rounded-lg text-xl sm:text-2xl disabled:opacity-50 transition-colors min-h-[44px]"
                >
                  Fold
                </button>

                {/* Call */}
                <button
                  onClick={() => submitAction('call')}
                  disabled={loading || !canCall}
                  className="flex-1 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-bold py-4 sm:py-5 px-4 sm:px-6 rounded-lg text-xl sm:text-2xl disabled:opacity-50 transition-colors min-h-[44px]"
                  title={!canCall ? 'Not enough chips to call' : ''}
                >
                  Call ${callAmount}
                </button>

                {/* Raise - Opens expandable panel */}
                {canRaise ? (
                  <button
                    onClick={() => setShowRaisePanel(!showRaisePanel)}
                    disabled={loading}
                    className={`flex-1 ${showRaisePanel ? 'bg-[#059669]' : 'bg-[#10B981]'} hover:bg-[#059669] text-white font-bold py-4 sm:py-5 px-4 sm:px-6 rounded-lg text-xl sm:text-2xl disabled:opacity-50 transition-colors min-h-[44px]`}
                  >
                    Raise {showRaisePanel ? '▲' : '▼'}
                  </button>
                ) : (
                  <button
                    disabled
                    className="flex-1 bg-[#1F7A47]/50 text-gray-400 font-bold py-4 sm:py-5 px-4 sm:px-6 rounded-lg text-xl sm:text-2xl opacity-50 cursor-not-allowed min-h-[44px]"
                    title={gameState.human_player.stack <= callAmount ? 'Not enough chips to raise' : 'Raise not available'}
                  >
                    Raise
                  </button>
                )}
              </div>

              {/* Expandable Raise Panel */}
              <AnimatePresence>
                {showRaisePanel && canRaise && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-[#0A4D26]/95 backdrop-blur-sm border-2 border-[#1F7A47] rounded-lg p-4 space-y-4">
                      {/* Quick bet buttons */}
                      <div className="flex gap-2 justify-center flex-wrap">
                        <button
                          onClick={() => handleRaiseAmountChange(minRaise)}
                          className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white font-semibold py-2 px-4 rounded"
                        >
                          Min ${minRaise}
                        </button>
                        <button
                          onClick={() => handleRaiseAmountChange(Math.floor(gameState.pot * 0.5))}
                          className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white font-semibold py-2 px-4 rounded"
                        >
                          ½ Pot ${Math.floor(gameState.pot * 0.5)}
                        </button>
                        <button
                          onClick={() => handleRaiseAmountChange(gameState.pot)}
                          className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white font-semibold py-2 px-4 rounded"
                        >
                          Pot ${gameState.pot}
                        </button>
                        <button
                          onClick={() => handleRaiseAmountChange(gameState.pot * 2)}
                          className="bg-[#1F7A47] hover:bg-[#0A4D26] text-white font-semibold py-2 px-4 rounded"
                        >
                          2x Pot ${gameState.pot * 2}
                        </button>
                        <button
                          onClick={handleAllIn}
                          className="bg-[#F59E0B] hover:bg-[#D97706] text-black font-bold py-2 px-4 rounded"
                        >
                          All-In ${maxRaise}
                        </button>
                      </div>

                      {/* Slider */}
                      <div>
                        <label className="text-white text-sm font-semibold mb-2 block">
                          Raise Amount: ${raiseAmount}
                        </label>
                        <input
                          type="range"
                          value={raiseAmount}
                          onChange={(e) => handleRaiseAmountChange(parseInt(e.target.value))}
                          min={minRaise}
                          max={maxRaise}
                          step={gameState.big_blind || 10}
                          disabled={loading}
                          className="w-full h-3 bg-[#1F7A47] rounded-lg appearance-none cursor-pointer accent-[#10B981]"
                        />
                        <div className="flex justify-between text-white text-xs mt-1">
                          <span>Min: ${minRaise}</span>
                          <span>Max: ${maxRaise}</span>
                        </div>
                      </div>

                      {/* Confirm Raise Button */}
                      <button
                        onClick={() => {
                          submitAction('raise', raiseAmount);
                          setShowRaisePanel(false);
                        }}
                        disabled={loading || raiseAmount < minRaise || raiseAmount > maxRaise}
                        className="w-full bg-[#10B981] hover:bg-[#059669] text-white font-bold py-4 px-6 rounded-lg text-lg disabled:opacity-50"
                      >
                        Confirm Raise ${raiseAmount}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <div className="text-white text-center py-4">
              {loading ? 'Processing...' : isAllIn ? "All-In! Waiting for hand to complete..." : "Waiting for other players..."}
            </div>
          )}
          </div>
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

      {/* Game Over modal - shown when human player is eliminated */}
      <GameOverModal
        isOpen={showGameOverModal}
        handsPlayed={gameState.hand_count || 0}
        onNewGame={handleNewGame}
      />
    </div>
  );
}
