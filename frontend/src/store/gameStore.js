// Game state management using React Context and useReducer
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { gameApi } from '../services/apiClient';
import websocketManager, { EVENT_TYPES, CONNECTION_STATES } from '../services/websocketManager';

// Game states
const GAME_STATES = {
  LOBBY: 'lobby',
  WAITING: 'waiting',
  PLAYING: 'playing',
  PAUSED: 'paused',
  FINISHED: 'finished'
};

// Round states
const ROUND_STATES = {
  PRE_FLOP: 'pre_flop',
  FLOP: 'flop',
  TURN: 'turn',
  RIVER: 'river',
  SHOWDOWN: 'showdown'
};

// Player actions
const PLAYER_ACTIONS = {
  FOLD: 'fold',
  CHECK: 'check',
  CALL: 'call',
  BET: 'bet',
  RAISE: 'raise',
  ALL_IN: 'all_in'
};

// Initial state
const initialState = {
  // Game information
  gameId: null,
  gameState: GAME_STATES.LOBBY,
  roundState: ROUND_STATES.PRE_FLOP,
  
  // Player information
  playerId: null,
  playerName: null,
  isAuthenticated: false,
  
  // Game data
  players: [],
  communityCards: [],
  pot: 0,
  currentBet: 0,
  smallBlind: 5,
  bigBlind: 10,
  dealerIndex: 0,
  currentPlayerIndex: 0,
  handCount: 0,
  
  // UI state
  selectedAction: null,
  betAmount: 0,
  showCards: false,
  animating: false,
  
  // WebSocket connection
  wsConnected: false,
  wsConnectionState: CONNECTION_STATES.DISCONNECTED,
  
  // History and analytics
  handHistory: [],
  actionHistory: [],
  
  // Debug information
  correlationId: null,
  lastApiCall: null,
  performanceMetrics: [],
  
  // Error handling
  error: null,
  loading: false
};

// Action types
const ACTION_TYPES = {
  // Authentication
  SET_PLAYER: 'SET_PLAYER',
  CLEAR_PLAYER: 'CLEAR_PLAYER',
  
  // Game management
  SET_GAME_ID: 'SET_GAME_ID',
  UPDATE_GAME_STATE: 'UPDATE_GAME_STATE',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  
  // Player actions
  SET_SELECTED_ACTION: 'SET_SELECTED_ACTION',
  SET_BET_AMOUNT: 'SET_BET_AMOUNT',
  ADD_ACTION_TO_HISTORY: 'ADD_ACTION_TO_HISTORY',
  
  // WebSocket
  SET_WS_CONNECTION_STATE: 'SET_WS_CONNECTION_STATE',
  
  // UI state
  SET_SHOW_CARDS: 'SET_SHOW_CARDS',
  SET_ANIMATING: 'SET_ANIMATING',
  
  // Debug
  SET_CORRELATION_ID: 'SET_CORRELATION_ID',
  ADD_PERFORMANCE_METRIC: 'ADD_PERFORMANCE_METRIC',
  SET_LAST_API_CALL: 'SET_LAST_API_CALL'
};

// Reducer function
const gameReducer = (state, action) => {
  switch (action.type) {
    case ACTION_TYPES.SET_PLAYER:
      return {
        ...state,
        playerId: action.payload.playerId,
        playerName: action.payload.playerName,
        isAuthenticated: true,
        error: null
      };

    case ACTION_TYPES.CLEAR_PLAYER:
      return {
        ...state,
        playerId: null,
        playerName: null,
        isAuthenticated: false,
        gameId: null,
        gameState: GAME_STATES.LOBBY
      };

    case ACTION_TYPES.SET_GAME_ID:
      return {
        ...state,
        gameId: action.payload,
        error: null
      };

    case ACTION_TYPES.UPDATE_GAME_STATE:
      return {
        ...state,
        ...action.payload,
        loading: false,
        error: null
      };

    case ACTION_TYPES.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };

    case ACTION_TYPES.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };

    case ACTION_TYPES.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    case ACTION_TYPES.SET_SELECTED_ACTION:
      return {
        ...state,
        selectedAction: action.payload
      };

    case ACTION_TYPES.SET_BET_AMOUNT:
      return {
        ...state,
        betAmount: action.payload
      };

    case ACTION_TYPES.ADD_ACTION_TO_HISTORY:
      return {
        ...state,
        actionHistory: [action.payload, ...state.actionHistory.slice(0, 99)] // Keep last 100 actions
      };

    case ACTION_TYPES.SET_WS_CONNECTION_STATE:
      return {
        ...state,
        wsConnectionState: action.payload,
        wsConnected: action.payload === CONNECTION_STATES.CONNECTED
      };

    case ACTION_TYPES.SET_SHOW_CARDS:
      return {
        ...state,
        showCards: action.payload
      };

    case ACTION_TYPES.SET_ANIMATING:
      return {
        ...state,
        animating: action.payload
      };

    case ACTION_TYPES.SET_CORRELATION_ID:
      return {
        ...state,
        correlationId: action.payload
      };

    case ACTION_TYPES.ADD_PERFORMANCE_METRIC:
      return {
        ...state,
        performanceMetrics: [action.payload, ...state.performanceMetrics.slice(0, 49)] // Keep last 50 metrics
      };

    case ACTION_TYPES.SET_LAST_API_CALL:
      return {
        ...state,
        lastApiCall: action.payload
      };

    default:
      return state;
  }
};

// Helper function to map backend response to frontend state
const mapBackendResponse = (response) => {
  return {
    gameState: response.current_state ? GAME_STATES.PLAYING : GAME_STATES.LOBBY,
    roundState: response.current_state || ROUND_STATES.PRE_FLOP,
    players: response.players || [],
    pot: response.pot || 0,
    currentBet: response.current_bet || 0,
    smallBlind: response.small_blind || 5,
    bigBlind: response.big_blind || 10,
    dealerIndex: response.dealer_position || 0,
    communityCards: response.community_cards || [],
    handCount: response.hand_number || 1,
    currentPlayerIndex: response.current_player ? 
      (response.players || []).findIndex(p => p.player_id === response.current_player) : 0
  };
};

// Create context
const GameContext = createContext();

// Game provider component
export const GameProvider = ({ children }) => {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // WebSocket event handlers
  useEffect(() => {
    const handleGameUpdate = (data) => {
      console.log('[GameStore] Game update received:', data);
      dispatch({
        type: ACTION_TYPES.UPDATE_GAME_STATE,
        payload: data
      });
    };

    const handlePlayerAction = (data) => {
      console.log('[GameStore] Player action received:', data);
      dispatch({
        type: ACTION_TYPES.ADD_ACTION_TO_HISTORY,
        payload: {
          ...data,
          timestamp: new Date().toISOString()
        }
      });
    };

    const handleConnectionStatus = (data) => {
      console.log('[GameStore] WebSocket status:', data.state);
      dispatch({
        type: ACTION_TYPES.SET_WS_CONNECTION_STATE,
        payload: data.state
      });
    };

    // Register WebSocket event listeners
    websocketManager.addEventListener(EVENT_TYPES.GAME_UPDATE, handleGameUpdate);
    websocketManager.addEventListener(EVENT_TYPES.PLAYER_ACTION, handlePlayerAction);
    websocketManager.addEventListener(EVENT_TYPES.CONNECTION_STATUS, handleConnectionStatus);

    // Cleanup
    return () => {
      websocketManager.removeEventListener(EVENT_TYPES.GAME_UPDATE, handleGameUpdate);
      websocketManager.removeEventListener(EVENT_TYPES.PLAYER_ACTION, handlePlayerAction);
      websocketManager.removeEventListener(EVENT_TYPES.CONNECTION_STATUS, handleConnectionStatus);
    };
  }, []);

  // Action creators
  const actions = {
    // Authentication actions
    setPlayer: (playerId, playerName) => {
      dispatch({
        type: ACTION_TYPES.SET_PLAYER,
        payload: { playerId, playerName }
      });
    },

    clearPlayer: () => {
      dispatch({ type: ACTION_TYPES.CLEAR_PLAYER });
    },

    // Game actions
    createGame: async (gameConfig) => {
      try {
        dispatch({ type: ACTION_TYPES.SET_LOADING, payload: true });
        const response = await gameApi.createGame(gameConfig);
        
        dispatch({
          type: ACTION_TYPES.SET_GAME_ID,
          payload: response.game_id
        });
        
        // Map backend response to frontend state
        dispatch({
          type: ACTION_TYPES.UPDATE_GAME_STATE,
          payload: mapBackendResponse(response)
        });

        // Connect to WebSocket
        websocketManager.connect(response.game_id, state.playerId);

        return response;
      } catch (error) {
        dispatch({
          type: ACTION_TYPES.SET_ERROR,
          payload: error.message
        });
        throw error;
      }
    },

    getGameState: async (gameId, playerId) => {
      try {
        dispatch({ type: ACTION_TYPES.SET_LOADING, payload: true });
        const response = await gameApi.getGameState(gameId, playerId);
        
        dispatch({
          type: ACTION_TYPES.UPDATE_GAME_STATE,
          payload: mapBackendResponse(response)
        });

        return response;
      } catch (error) {
        dispatch({
          type: ACTION_TYPES.SET_ERROR,
          payload: error.message
        });
        throw error;
      }
    },

    submitAction: async (action, amount = null) => {
      try {
        if (!state.gameId || !state.playerId) {
          throw new Error('Game or player not initialized');
        }

        dispatch({ type: ACTION_TYPES.SET_LOADING, payload: true });
        
        const response = await gameApi.submitAction(state.gameId, state.playerId, {
          action_type: action,
          amount: amount
        });

        // Add to action history
        dispatch({
          type: ACTION_TYPES.ADD_ACTION_TO_HISTORY,
          payload: {
            playerId: state.playerId,
            action,
            amount,
            timestamp: new Date().toISOString()
          }
        });

        // Update game state
        dispatch({
          type: ACTION_TYPES.UPDATE_GAME_STATE,
          payload: mapBackendResponse(response)
        });

        // Send via WebSocket for real-time updates
        websocketManager.sendPlayerAction(action, amount);

        return response;
      } catch (error) {
        dispatch({
          type: ACTION_TYPES.SET_ERROR,
          payload: error.message
        });
        throw error;
      }
    },

    nextHand: async () => {
      try {
        if (!state.gameId || !state.playerId) {
          throw new Error('Game or player not initialized');
        }

        dispatch({ type: ACTION_TYPES.SET_LOADING, payload: true });
        const response = await gameApi.nextHand(state.gameId, state.playerId);
        
        dispatch({
          type: ACTION_TYPES.UPDATE_GAME_STATE,
          payload: mapBackendResponse(response)
        });

        return response;
      } catch (error) {
        dispatch({
          type: ACTION_TYPES.SET_ERROR,
          payload: error.message
        });
        throw error;
      }
    },

    // UI actions
    setSelectedAction: (action) => {
      dispatch({
        type: ACTION_TYPES.SET_SELECTED_ACTION,
        payload: action
      });
    },

    setBetAmount: (amount) => {
      dispatch({
        type: ACTION_TYPES.SET_BET_AMOUNT,
        payload: amount
      });
    },

    setShowCards: (show) => {
      dispatch({
        type: ACTION_TYPES.SET_SHOW_CARDS,
        payload: show
      });
    },

    clearError: () => {
      dispatch({ type: ACTION_TYPES.CLEAR_ERROR });
    },

    // Debug actions
    addPerformanceMetric: (metric) => {
      dispatch({
        type: ACTION_TYPES.ADD_PERFORMANCE_METRIC,
        payload: metric
      });
    }
  };

  const value = {
    state,
    actions,
    // Computed values
    computed: {
      currentPlayer: state.players[state.currentPlayerIndex] || null,
      isCurrentPlayer: state.players[state.currentPlayerIndex]?.player_id === state.playerId,
      canAct: state.gameState === GAME_STATES.PLAYING && 
              state.players[state.currentPlayerIndex]?.player_id === state.playerId,
      playerCount: state.players.length,
      activePlayers: state.players.filter(p => p.is_active),
      gameInProgress: state.gameState === GAME_STATES.PLAYING,
      wsConnected: state.wsConnected
    }
  };

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
};

// Hook to use game context
export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

// Export constants
export { GAME_STATES, ROUND_STATES, PLAYER_ACTIONS, ACTION_TYPES };