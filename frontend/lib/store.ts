// Zustand store for game state management

import { create } from 'zustand';
import { GameState } from './types';
import { pokerApi } from './api';

interface GameStore {
  // State
  gameId: string | null;
  gameState: GameState | null;
  loading: boolean;
  error: string | null;
  beginnerMode: boolean;

  // Actions
  createGame: (playerName: string, aiCount: number) => Promise<void>;
  fetchGameState: () => Promise<void>;
  submitAction: (action: 'fold' | 'call' | 'raise', amount?: number) => Promise<void>;
  nextHand: () => Promise<void>;
  toggleBeginnerMode: () => void;
  setError: (error: string | null) => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gameId: null,
  gameState: null,
  loading: false,
  error: null,
  beginnerMode: true, // Start in beginner mode for educational purposes

  // Create a new game
  createGame: async (playerName: string, aiCount: number) => {
    set({ loading: true, error: null });
    try {
      const response = await pokerApi.createGame(playerName, aiCount);
      set({ gameId: response.game_id });

      // Fetch initial game state
      await get().fetchGameState();
    } catch (error: any) {
      console.error('Error creating game:', error);
      set({
        error: error.response?.data?.detail || 'Failed to create game. Please try again.',
        loading: false
      });
    }
  },

  // Fetch current game state
  fetchGameState: async () => {
    const { gameId } = get();
    if (!gameId) {
      set({ error: 'No game ID found' });
      return;
    }

    set({ loading: true, error: null });
    try {
      const gameState = await pokerApi.getGameState(gameId);
      set({ gameState, loading: false });
    } catch (error: any) {
      console.error('Error fetching game state:', error);
      set({
        error: error.response?.data?.detail || 'Failed to fetch game state',
        loading: false
      });
    }
  },

  // Submit a player action
  submitAction: async (action: 'fold' | 'call' | 'raise', amount?: number) => {
    const { gameId } = get();
    if (!gameId) {
      set({ error: 'No game ID found' });
      return;
    }

    set({ loading: true, error: null });
    try {
      const gameState = await pokerApi.submitAction(gameId, action, amount);
      set({ gameState, loading: false });
    } catch (error: any) {
      console.error('Error submitting action:', error);
      set({
        error: error.response?.data?.detail || `Failed to ${action}. Please try again.`,
        loading: false
      });

      // Refresh game state even on error
      await get().fetchGameState();
    }
  },

  // Start next hand
  nextHand: async () => {
    const { gameId } = get();
    if (!gameId) {
      set({ error: 'No game ID found' });
      return;
    }

    set({ loading: true, error: null });
    try {
      const gameState = await pokerApi.nextHand(gameId);
      set({ gameState, loading: false });
    } catch (error: any) {
      console.error('Error starting next hand:', error);
      set({
        error: error.response?.data?.detail || 'Failed to start next hand',
        loading: false
      });
    }
  },

  // Toggle between beginner and expert mode
  toggleBeginnerMode: () => {
    set((state) => ({ beginnerMode: !state.beginnerMode }));
  },

  // Set error message
  setError: (error: string | null) => {
    set({ error });
  },
}));
