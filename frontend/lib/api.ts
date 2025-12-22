// API client for backend communication

import axios from 'axios';
import {
  GameState,
  CreateGameRequest,
  CreateGameResponse,
  SubmitActionRequest,
} from './types';

// Get API URL from environment variable or default to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

  // Submit a player action
  async submitAction(
    gameId: string,
    action: 'fold' | 'call' | 'raise',
    amount?: number
  ): Promise<GameState> {
    const response = await api.post<GameState>(`/games/${gameId}/actions`, {
      action,
      amount,
    } as SubmitActionRequest);
    return response.data;
  },

  // Start next hand
  async nextHand(gameId: string): Promise<GameState> {
    const response = await api.post<GameState>(`/games/${gameId}/next`);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/');
    return response.data;
  },
};
