// Simple Poker Frontend - Basic React with useState
import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8080/api';

function App() {
  const [gameId, setGameId] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const createGame = async () => {
    if (!playerName.trim()) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/create-game`, {
        player_name: playerName
      });
      
      setGameId(response.data.game_id);
      setGameState(response.data.game_state);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create game');
    } finally {
      setLoading(false);
    }
  };

  const submitAction = async (action, amount = null) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/player-action/${gameId}`, {
        action,
        amount
      });
      
      setGameState(response.data.game_state);
    } catch (err) {
      setError(err.response?.data?.detail || 'Action failed');
    } finally {
      setLoading(false);
    }
  };

  const nextHand = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/next-hand/${gameId}`);
      setGameState(response.data.game_state);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start next hand');
    } finally {
      setLoading(false);
    }
  };

  const refreshGameState = async () => {
    if (!gameId) return;
    
    try {
      const response = await axios.get(`${API_BASE}/game-state/${gameId}`);
      setGameState(response.data.game_state);
    } catch (err) {
      setError('Failed to refresh game state');
    }
  };

  if (!gameId) {
    return (
      <div className="app">
        <h1>Simple Poker Learning App</h1>
        <div className="create-game">
          <input
            type="text"
            placeholder="Enter your name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            disabled={loading}
          />
          <button onClick={createGame} disabled={loading || !playerName.trim()}>
            {loading ? 'Creating...' : 'Create Game'}
          </button>
          {error && <div className="error">{error}</div>}
        </div>
      </div>
    );
  }

  if (!gameState) {
    return <div className="app">Loading game...</div>;
  }

  const humanPlayer = gameState.players.find(p => p.player_id === 'human');
  const showActions = gameState.game_state !== 'showdown' && humanPlayer?.is_active;

  return (
    <div className="app">
      <h1>Poker Game</h1>
      
      {/* Game Info */}
      <div className="game-info">
        <div>Hand: {gameState.hand_count}</div>
        <div>State: {gameState.game_state}</div>
        <div>Pot: ${gameState.pot}</div>
        <div>Current Bet: ${gameState.current_bet}</div>
      </div>

      {/* Community Cards */}
      <div className="community-cards">
        <h3>Community Cards</h3>
        <div className="cards">
          {gameState.community_cards.map((card, i) => (
            <span key={i} className="card">{card}</span>
          ))}
        </div>
      </div>

      {/* Players */}
      <div className="players">
        <h3>Players</h3>
        {gameState.players.map(player => (
          <div key={player.player_id} className={`player ${player.player_id === 'human' ? 'human' : 'ai'}`}>
            <div className="player-name">
              {player.name} {player.player_id === 'human' ? '(You)' : ''}
            </div>
            <div className="player-info">
              Stack: ${player.stack} | Bet: ${player.current_bet}
              {player.all_in && ' (ALL-IN)'}
              {!player.is_active && ' (FOLDED)'}
            </div>
            {player.player_id === 'human' && (
              <div className="hole-cards">
                Your cards: {player.hole_cards.map((card, i) => (
                  <span key={i} className="card">{card}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      {showActions && (
        <div className="actions">
          <h3>Your Actions</h3>
          <button onClick={() => submitAction('fold')} disabled={loading}>
            Fold
          </button>
          <button onClick={() => submitAction('call')} disabled={loading}>
            Call ${gameState.current_bet - humanPlayer.current_bet}
          </button>
          <button 
            onClick={() => {
              const amount = prompt('Enter raise amount:');
              if (amount) submitAction('raise', parseInt(amount));
            }} 
            disabled={loading}
          >
            Raise
          </button>
        </div>
      )}

      {/* Showdown */}
      {gameState.game_state === 'showdown' && (
        <div className="showdown">
          <h3>Hand Complete!</h3>
          <button onClick={nextHand} disabled={loading}>
            Next Hand
          </button>
        </div>
      )}

      {/* Controls */}
      <div className="controls">
        <button onClick={refreshGameState}>Refresh</button>
        <button onClick={() => { setGameId(null); setGameState(null); }}>
          New Game
        </button>
      </div>

      {error && <div className="error">{error}</div>}
    </div>
  );
}

export default App;