// Zustand store for game state management

import { create } from 'zustand';
import { GameState } from './types';
import { pokerApi } from './api';
import { PokerWebSocket, ConnectionState } from './websocket';

interface GameStore {
  // State
  gameId: string | null;
  gameState: GameState | null;
  loading: boolean;
  error: string | null;
  showAiThinking: boolean; // UX Phase 1: Control AI reasoning visibility
  handAnalysis: any | null; // UX Phase 2: Store hand analysis

  // Phase 4: Step Mode (UAT-1 fix)
  stepMode: boolean; // If true, pause after each AI action
  awaitingContinue: boolean; // If true, waiting for user to click Continue

  // WebSocket state (Phase 1.4)
  wsClient: PokerWebSocket | null;
  connectionState: ConnectionState;
  aiActionQueue: any[]; // Queue of AI actions for animations

  // Actions
  createGame: (playerName: string, aiCount: number) => Promise<void>;
  submitAction: (action: 'fold' | 'call' | 'raise', amount?: number) => void;
  nextHand: () => void;
  toggleShowAiThinking: () => void; // UX Phase 1: Toggle AI reasoning
  toggleStepMode: () => void; // Phase 4: Toggle step mode
  sendContinue: () => void; // Phase 4: Send continue signal
  getHandAnalysis: () => Promise<void>; // UX Phase 2: Fetch analysis (still uses REST)
  quitGame: () => void; // Bug fix: Allow player to quit
  setError: (error: string | null) => void;

  // WebSocket actions (Phase 1.4)
  connectWebSocket: (gameId: string) => void;
  disconnectWebSocket: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gameId: null,
  gameState: null,
  loading: false,
  error: null,
  showAiThinking: false, // UX Phase 1: Hidden by default for cleaner UI
  handAnalysis: null, // UX Phase 2: No analysis initially

  // Phase 4: Step Mode (UAT-1 fix) - Disabled by default
  stepMode: false,
  awaitingContinue: false,

  // WebSocket state (Phase 1.4)
  wsClient: null,
  connectionState: ConnectionState.DISCONNECTED,
  aiActionQueue: [],

  // Create a new game (Phase 1.4: Now uses WebSocket)
  createGame: async (playerName: string, aiCount: number) => {
    set({ loading: true, error: null });
    try {
      const response = await pokerApi.createGame(playerName, aiCount);
      const gameId = response.game_id;
      set({ gameId });

      // Connect to WebSocket for real-time updates
      get().connectWebSocket(gameId);
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

  // Bug fix: Quit game and return to lobby
  quitGame: () => {
    // Disconnect WebSocket (Phase 1.4)
    get().disconnectWebSocket();

    set({
      gameId: null,
      gameState: null,
      handAnalysis: null,
      error: null,
      loading: false,
      aiActionQueue: [],
      awaitingContinue: false,  // Phase 4: Reset step mode state
      stepMode: false  // Phase 4: Reset step mode
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
      },

      onAIAction: (aiAction: any) => {
        // Add AI action to queue for animations (Phase 2)
        set(state => ({
          aiActionQueue: [...state.aiActionQueue, aiAction]
        }));
      },

      onError: (error: string) => {
        set({ error });
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
}));
