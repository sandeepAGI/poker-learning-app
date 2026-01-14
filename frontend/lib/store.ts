// Zustand store for game state management

import { create } from 'zustand';
import { GameState, AIDecisionEntry } from './types';
import { pokerApi } from './api';
import { PokerWebSocket, ConnectionState } from './websocket';

interface GameStore {
  // State
  gameId: string | null;
  gameState: GameState | null;
  loading: boolean;
  error: string | null; // Action/validation errors (won't kick user out)
  connectionError: string | null; // Issue #3: Connection errors (triggers reconnect screen)
  showAiThinking: boolean; // UX Phase 1: Control AI reasoning visibility
  handAnalysis: any | null; // UX Phase 2: Store hand analysis

  // Phase 4: Step Mode (UAT-1 fix)
  stepMode: boolean; // If true, pause after each AI action
  awaitingContinue: boolean; // If true, waiting for user to click Continue

  // WebSocket state (Phase 1.4)
  wsClient: PokerWebSocket | null;
  connectionState: ConnectionState;

  // Phase 3: AI Decision History (React infinite loop fix)
  decisionHistory: AIDecisionEntry[];

  // Actions
  createGame: (playerName: string, aiCount: number) => Promise<void>;
  submitAction: (action: 'fold' | 'call' | 'raise', amount?: number) => void;
  nextHand: () => void;
  toggleShowAiThinking: () => void; // UX Phase 1: Toggle AI reasoning
  toggleStepMode: () => void; // Phase 4: Toggle step mode
  sendContinue: () => void; // Phase 4: Send continue signal
  getHandAnalysis: () => Promise<void>; // UX Phase 2: Fetch analysis (still uses REST)
  clearHandAnalysis: () => void; // UX Fix: Clear analysis to allow modal re-opening
  quitGame: () => void; // Bug fix: Allow player to quit
  setError: (error: string | null) => void;

  // WebSocket actions (Phase 1.4)
  connectWebSocket: (gameId: string) => void;
  disconnectWebSocket: () => void;

  // Browser refresh recovery (Phase 7 enhancement)
  reconnectToGame: (gameId: string) => Promise<boolean>;
  initializeFromStorage: () => void;

  // Phase 3: AI Decision History management (internal)
  _processAIDecisions: (gameState: GameState) => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gameId: null,
  gameState: null,
  loading: false,
  error: null,
  connectionError: null, // Issue #3: Separate connection errors
  showAiThinking: false, // UX Phase 1: Hidden by default for cleaner UI
  handAnalysis: null, // UX Phase 2: No analysis initially

  // Phase 4: Step Mode (UAT-1 fix) - Disabled by default
  stepMode: false,
  awaitingContinue: false,

  // WebSocket state (Phase 1.4)
  wsClient: null,
  connectionState: ConnectionState.DISCONNECTED,

  // Phase 3: AI Decision History
  decisionHistory: [],

  // Create a new game (Phase 1.4: Now uses WebSocket)
  createGame: async (playerName: string, aiCount: number) => {
    set({ loading: true, error: null });
    try {
      const response = await pokerApi.createGame(playerName, aiCount);
      const gameId = response.game_id;
      set({ gameId });

      // Phase 7+: Persist gameId to localStorage for browser refresh recovery
      if (typeof window !== 'undefined') {
        localStorage.setItem('poker_game_id', gameId);
        localStorage.setItem('poker_player_name', playerName);
      }

      // Connect to WebSocket for real-time updates
      get().connectWebSocket(gameId);

      // Navigation now handled by component using Next.js router
    } catch (error: any) {
      console.error('Error creating game:', error);
      set({
        error: error.response?.data?.detail || 'Failed to create game. Please try again.',
        loading: false
      });
    }
  },

  // Submit a player action (Phase 1.4: Now uses WebSocket)
  submitAction: (action: 'fold' | 'call' | 'raise', amount?: number) => {
    const { wsClient, showAiThinking, stepMode } = get();
    if (!wsClient) {
      set({ error: 'Not connected to game server' });
      return;
    }

    try {
      wsClient.sendAction(action, amount, showAiThinking, stepMode);
      // State updates will come via WebSocket events
    } catch (error: any) {
      console.error('Error submitting action:', error);
      set({ error: `Failed to ${action}. Please try again.` });
    }
  },

  // Start next hand (Phase 1.4: Now uses WebSocket)
  nextHand: () => {
    const { wsClient, showAiThinking, stepMode } = get();
    if (!wsClient) {
      set({ error: 'Not connected to game server' });
      return;
    }

    try {
      wsClient.nextHand(showAiThinking, stepMode);
      // State updates will come via WebSocket events
    } catch (error: any) {
      console.error('Error starting next hand:', error);
      set({ error: 'Failed to start next hand' });
    }
  },

  // UX Phase 1: Toggle AI reasoning visibility
  toggleShowAiThinking: () => {
    const newValue = !get().showAiThinking;
    set({ showAiThinking: newValue });
    // With WebSocket, this will affect future actions only
    // No need to re-fetch state
  },

  // Phase 4: Toggle step mode (UAT-1 fix)
  toggleStepMode: () => {
    const newValue = !get().stepMode;
    set({ stepMode: newValue });
    console.log(`Step mode ${newValue ? 'enabled' : 'disabled'}`);
  },

  // Phase 4: Send continue signal to proceed to next AI action
  sendContinue: () => {
    const { wsClient } = get();
    if (!wsClient) {
      console.error('[Store] sendContinue: No WebSocket client');
      set({ error: 'Not connected to game server' });
      return;
    }

    try {
      console.log('[Store] Sending continue signal...');
      wsClient.sendContinue();
      set({ awaitingContinue: false });
      console.log('[Store] Continue signal sent, awaitingContinue set to false');
    } catch (error: any) {
      console.error('[Store] Error sending continue signal:', error);
      set({ error: 'Failed to send continue signal' });
    }
  },

  // UX Phase 2: Get hand analysis
  getHandAnalysis: async () => {
    const { gameId } = get();
    if (!gameId) {
      set({ error: 'No game ID found' });
      return;
    }

    set({ loading: true, error: null });
    try {
      const analysis = await pokerApi.getHandAnalysis(gameId);
      set({ handAnalysis: analysis, loading: false });
    } catch (error: any) {
      console.error('Error fetching hand analysis:', error);
      const errorMsg = error.response?.status === 404
        ? 'No completed hands to analyze yet. Play at least one hand first!'
        : error.response?.data?.detail || 'Failed to fetch hand analysis';
      set({
        error: errorMsg,
        loading: false,
        handAnalysis: null  // Clear any stale analysis
      });
    }
  },

  // UX Fix: Clear hand analysis (allows modal to reopen on subsequent clicks)
  clearHandAnalysis: () => {
    set({ handAnalysis: null });
  },

  // Bug fix: Quit game and return to lobby
  quitGame: () => {
    // Disconnect WebSocket (Phase 1.4)
    get().disconnectWebSocket();

    // Phase 7+: Clear localStorage on quit
    if (typeof window !== 'undefined') {
      localStorage.removeItem('poker_game_id');
      localStorage.removeItem('poker_player_name');
      // Navigation now handled by component using Next.js router
    }

    set({
      gameId: null,
      gameState: null,
      handAnalysis: null,
      error: null,
      connectionError: null, // Issue #3: Clear connection errors too
      loading: false,
      awaitingContinue: false,  // Phase 4: Reset step mode state
      stepMode: false,  // Phase 4: Reset step mode
      decisionHistory: []  // Phase 3: Clear decision history on quit
    });
  },

  // Set error message
  setError: (error: string | null) => {
    set({ error });
  },

  // WebSocket connection management (Phase 1.4)
  connectWebSocket: (gameId: string) => {
    const { showAiThinking } = get();

    // Disconnect any existing connection first
    get().disconnectWebSocket();

    // Create new WebSocket client with event handlers
    const wsClient = new PokerWebSocket(gameId, {
      onStateUpdate: (gameState: GameState) => {
        set({ gameState, loading: false });
        // Phase 3: Process AI decisions when state updates
        get()._processAIDecisions(gameState);
      },

      onError: (error: string) => {
        set({ connectionError: error }); // Issue #3: WebSocket errors are connection errors
      },

      onGameOver: () => {
        // Game over event received
        console.log('Game over - player eliminated');
      },

      onConnect: () => {
        set({
          connectionState: ConnectionState.CONNECTED,
          loading: false
        });

        // Phase 7: Request state upon reconnection
        // This ensures the UI shows current game state after network disruptions
        const client = get().wsClient;
        if (client) {
          console.log('[Store] Connected - requesting current game state');
          client.getState(get().showAiThinking);
        }
      },

      onDisconnect: () => {
        set({
          connectionState: ConnectionState.DISCONNECTED
        });
      },

      // Phase 4: Handle awaiting_continue event (Step Mode)
      onAwaitingContinue: (playerName: string, action: string) => {
        console.log(`[Store] Step mode: Waiting for continue after ${playerName} ${action}`);
        set({ awaitingContinue: true });
        console.log('[Store] awaitingContinue set to TRUE - Continue button should appear');
      },

      // Issue #4: Handle auto_resumed event (Step Mode auto-resume after timeout)
      onAutoResumed: (reason: string) => {
        console.log(`[Store] Step mode auto-resumed: ${reason}`);
        set({ awaitingContinue: false });
        console.log('[Store] awaitingContinue set to FALSE - Continue button should disappear');
      }
    });

    // Connect to WebSocket
    wsClient.connect();
    set({ wsClient, connectionState: ConnectionState.CONNECTING });
  },

  disconnectWebSocket: () => {
    const { wsClient } = get();
    if (wsClient) {
      wsClient.disconnect();
      set({ wsClient: null, connectionState: ConnectionState.DISCONNECTED });
    }
  },

  // Phase 7+: Reconnect to existing game (browser refresh recovery)
  reconnectToGame: async (gameId: string): Promise<boolean> => {
    console.log(`[Store] Attempting to reconnect to game ${gameId}`);
    set({ loading: true, error: null, connectionError: null }); // Issue #3: Clear both error types

    try {
      // Verify game still exists via REST API
      const response = await pokerApi.getGameState(gameId);

      if (response) {
        console.log('[Store] Game found! Reconnecting...');

        // Force component remount by clearing state first
        set({ gameState: null });

        // Wait for React to flush the update
        await new Promise(resolve => setTimeout(resolve, 0));

        // Then set the new state
        set({ gameId, gameState: response, loading: false });

        // Phase 3: Process AI decisions from reconnected state
        get()._processAIDecisions(response);

        // Connect to WebSocket
        get().connectWebSocket(gameId);

        return true;
      } else {
        console.log('[Store] Game not found');
        // Game doesn't exist anymore, clear localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('poker_game_id');
          localStorage.removeItem('poker_player_name');
        }
        set({ loading: false, connectionError: 'Game session expired. Please start a new game.' }); // Issue #3
        return false;
      }
    } catch (error: any) {
      console.error('[Store] Error reconnecting to game:', error);
      // Clear localStorage on error
      if (typeof window !== 'undefined') {
        localStorage.removeItem('poker_game_id');
        localStorage.removeItem('poker_player_name');
      }
      set({ loading: false, connectionError: 'Failed to reconnect to game. Please start a new game.' }); // Issue #3
      return false;
    }
  },

  // Phase 7+: Initialize from localStorage on app load
  initializeFromStorage: () => {
    if (typeof window === 'undefined') return;

    const savedGameId = localStorage.getItem('poker_game_id');

    if (savedGameId) {
      console.log(`[Store] Found saved game ID: ${savedGameId}`);
      // Attempt to reconnect
      get().reconnectToGame(savedGameId);
    } else {
      console.log('[Store] No saved game found');
    }
  },

  // Phase 3: AI Decision History Management
  // Internal: Process AI decisions from game state
  // Called automatically when game state updates
  _processAIDecisions: (gameState: GameState) => {
    const currentHistory = get().decisionHistory;

    // Clear history when starting a new hand
    if (gameState.state === 'pre_flop' && currentHistory.length > 0) {
      set({ decisionHistory: [] });
      return;
    }

    // Add new AI decisions to history
    const newDecisions: AIDecisionEntry[] = [];
    Object.entries(gameState.last_ai_decisions).forEach(([playerId, decision]) => {
      // FIX Issue #3: Deduplicate based on decision_id instead of reasoning text
      // This prevents data loss when reasoning is hidden (show_ai_thinking=false)
      const alreadyExists = currentHistory.some(
        entry => entry.playerId === playerId && entry.decision.decision_id === decision.decision_id
      );

      if (!alreadyExists) {
        const player = gameState.players.find(p => p.player_id === playerId);
        if (player && !player.is_human) {
          newDecisions.push({
            playerName: player.name,
            playerId,
            decision,
            timestamp: Date.now()
          });
        }
      }
    });

    if (newDecisions.length > 0) {
      set(state => ({
        decisionHistory: [...newDecisions, ...state.decisionHistory]
      }));
    }
  },
}));
