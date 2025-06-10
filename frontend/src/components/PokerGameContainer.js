import React, { useState, useEffect } from 'react';
import { useGame, GAME_STATES } from '../store/gameStore';
import GameLobby from './GameLobby';
import PokerTable from './PokerTable';
import GameControls from './GameControls';
import PlayerStats from './PlayerStats';
import LoadingSpinner from './LoadingSpinner';
import Toast from './Toast';

const PokerGameContainer = ({ onLogout }) => {
  const { state, actions, computed } = useGame();
  const [toast, setToast] = useState(null);

  // Initialize player data from localStorage
  useEffect(() => {
    const playerData = localStorage.getItem('player_data');
    if (playerData && !state.playerId) {
      try {
        const parsed = JSON.parse(playerData);
        actions.setPlayer(parsed.player_id, parsed.username);
      } catch (error) {
        console.error('Failed to parse player data:', error);
      }
    }
  }, [state.playerId, actions]);

  // Show toast notifications for errors
  useEffect(() => {
    if (state.error) {
      setToast({
        type: 'error',
        message: state.error,
        duration: 5000
      });
    }
  }, [state.error]);

  const handleCreateGame = async (gameConfig) => {
    try {
      await actions.createGame(gameConfig);
      setToast({
        type: 'success',
        message: 'Game created successfully!',
        duration: 3000
      });
    } catch (error) {
      // Error is already handled in the store
    }
  };

  const handlePlayerAction = async (action, amount = null) => {
    try {
      await actions.submitAction(action, amount);
      setToast({
        type: 'success',
        message: `Action: ${action}${amount ? ` $${amount}` : ''}`,
        duration: 2000
      });
    } catch (error) {
      // Error is already handled in the store
    }
  };

  const handleNextHand = async () => {
    try {
      await actions.nextHand();
      setToast({
        type: 'info',
        message: 'Starting next hand...',
        duration: 2000
      });
    } catch (error) {
      // Error is already handled in the store
    }
  };

  const handleToastClose = () => {
    setToast(null);
    actions.clearError();
  };

  // Render loading state
  if (state.loading && !state.gameId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner message="Loading game..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-blue-400">🃏 Poker Learning</h1>
            {state.gameId && (
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <span>Game:</span>
                <code className="bg-gray-700 px-2 py-1 rounded text-xs">
                  {state.gameId.slice(-8)}
                </code>
                <span className={`px-2 py-1 rounded text-xs ${
                  computed.wsConnected 
                    ? 'bg-green-900 text-green-300' 
                    : 'bg-red-900 text-red-300'
                }`}>
                  {computed.wsConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {state.playerName && (
              <span className="text-gray-300">Welcome, {state.playerName}</span>
            )}
            <button
              onClick={onLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto p-4">
        {state.gameState === GAME_STATES.LOBBY ? (
          <GameLobby onCreateGame={handleCreateGame} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main game area */}
            <div className="lg:col-span-3">
              <PokerTable />
              
              {/* Game controls */}
              {computed.canAct && (
                <div className="mt-6">
                  <GameControls
                    onAction={handlePlayerAction}
                    gameState={state}
                    currentPlayer={computed.currentPlayer}
                  />
                </div>
              )}

              {/* Next hand button */}
              {state.roundState === 'showdown' && computed.isCurrentPlayer && (
                <div className="mt-4 text-center">
                  <button
                    onClick={handleNextHand}
                    disabled={state.loading}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                  >
                    {state.loading ? 'Starting...' : 'Next Hand'}
                  </button>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <PlayerStats />
              
              {/* Action history */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4">Recent Actions</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {state.actionHistory.slice(0, 10).map((action, index) => (
                    <div key={index} className="text-sm text-gray-300">
                      <span className="text-blue-400">{action.playerId}</span>
                      {' '}
                      <span className="text-white">{action.action}</span>
                      {action.amount && (
                        <span className="text-green-400"> ${action.amount}</span>
                      )}
                      <div className="text-xs text-gray-500">
                        {new Date(action.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Game info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4">Game Info</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Hand:</span>
                    <span className="text-white">{state.handCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Players:</span>
                    <span className="text-white">{computed.activePlayers.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Small Blind:</span>
                    <span className="text-white">${state.smallBlind}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Big Blind:</span>
                    <span className="text-white">${state.bigBlind}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Toast notifications */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onClose={handleToastClose}
        />
      )}

      {/* Loading overlay */}
      {state.loading && state.gameId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <LoadingSpinner message="Processing..." />
        </div>
      )}
    </div>
  );
};

export default PokerGameContainer;