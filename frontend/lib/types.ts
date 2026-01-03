// Type definitions for the Poker Learning App

export interface Player {
  player_id: string;
  name: string;
  stack: number;
  current_bet: number;
  is_active: boolean;
  all_in: boolean;
  is_human: boolean;
  personality: string | null;
  hole_cards: string[];
  is_current_turn?: boolean;
}

export interface AIDecision {
  action: string;
  amount: number;
  reasoning?: string;  // Optional when show_ai_thinking=false
  hand_strength?: number;  // Optional when show_ai_thinking=false
  pot_odds?: number;  // Optional when show_ai_thinking=false
  confidence?: number;  // Optional when show_ai_thinking=false
  spr?: number;  // Optional when show_ai_thinking=false
  decision_id: string;  // FIX Issue #3: Always present for deduplication
}

export interface WinnerInfo {
  player_id: string;
  name: string;
  amount: number;
  is_human: boolean;
  personality: string | null;
}

export interface GameState {
  game_id: string;
  state: 'pre_flop' | 'flop' | 'turn' | 'river' | 'showdown';
  pot: number;
  current_bet: number;
  players: Player[];
  community_cards: string[];
  current_player_index: number | null;
  human_player: Player;
  last_ai_decisions: Record<string, AIDecision>;
  winner_info: WinnerInfo | null;
  small_blind: number;
  big_blind: number;
  hand_count: number;
  dealer_position: number;
  small_blind_position: number;
  big_blind_position: number;
}

export interface CreateGameRequest {
  player_name: string;
  ai_count: number;
}

export interface CreateGameResponse {
  game_id: string;
}

export interface SubmitActionRequest {
  action: 'fold' | 'call' | 'raise';
  amount?: number;
}

/**
 * AI Decision Entry in history
 * Tracks when AI players make decisions with their reasoning
 */
export interface AIDecisionEntry {
  playerName: string;
  playerId: string;
  decision: AIDecision;
  timestamp: number;
}
