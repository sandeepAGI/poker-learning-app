// API client for backend communication

import axios from 'axios';
import {
  GameState,
  CreateGameRequest,
  CreateGameResponse,
} from './types';
import { getToken, logout } from './auth';

// Get API URL from environment variable or default to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication interceptor
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (logout on auth failure)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const pokerApi = {
  // Create a new game
  async createGame(playerName: string, aiCount: number): Promise<CreateGameResponse> {
    const response = await api.post<CreateGameResponse>('/games', {
      player_name: playerName,
      ai_count: aiCount,
    } as CreateGameRequest);
    return response.data;
  },

  // Get current game state
  async getGameState(gameId: string, showAiThinking: boolean = false): Promise<GameState> {
    const response = await api.get<GameState>(`/games/${gameId}`, {
      params: { show_ai_thinking: showAiThinking }
    });
    return response.data;
  },

  // Get hand analysis (UX Phase 2)
  async getHandAnalysis(gameId: string): Promise<any> {
    const response = await api.get(`/games/${gameId}/analysis`);
    return response.data;
  },

  // Get LLM-powered hand analysis (Phase 4 - Haiku only)
  async getHandAnalysisLLM(
    gameId: string,
    options: {
      handNumber?: number,
      useCache?: boolean
    } = {}
  ): Promise<{
    analysis: any,
    model_used: string,
    cost: number,
    cached: boolean,
    analysis_count: number,
    error?: string
  }> {
    const params = new URLSearchParams();
    if (options.handNumber) params.set('hand_number', options.handNumber.toString());
    if (options.useCache !== undefined) params.set('use_cache', options.useCache.toString());

    const response = await api.get(`/games/${gameId}/analysis-llm?${params}`);
    return response.data;
  },

  // Get LLM-powered session analysis (Phase 4.5)
  async getSessionAnalysis(
    gameId: string,
    options: {
      depth?: 'quick' | 'deep',
      handCount?: number,
      useCache?: boolean
    } = {}
  ): Promise<{
    analysis: any,
    model_used: string,
    cost: number,
    cached: boolean,
    hands_analyzed: number,
    error?: string
  }> {
    const params = new URLSearchParams();
    if (options.depth) params.set('depth', options.depth);
    if (options.handCount) params.set('hand_count', options.handCount.toString());
    if (options.useCache !== undefined) params.set('use_cache', options.useCache.toString());

    const response = await api.get(`/games/${gameId}/analysis-session?${params}`);
    return response.data;
  },

  // Get user's game history
  async getMyGames(limit: number = 20): Promise<any> {
    const response = await api.get('/users/me/games', {
      params: { limit }
    });
    return response.data;
  },

  // Get hands for a specific game
  async getGameHands(gameId: string): Promise<any> {
    const response = await api.get(`/games/${gameId}/hands`);
    return response.data;
  },

  // Quit game and mark as completed
  async quitGame(gameId: string): Promise<any> {
    const response = await api.post(`/games/${gameId}/quit`);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/');
    return response.data;
  },
};
