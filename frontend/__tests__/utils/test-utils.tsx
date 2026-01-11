import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

/**
 * Create a mock GameState object for testing.
 * Provides sensible defaults and allows overrides.
 */
export function createMockGameState(overrides: Partial<any> = {}) {
  const mockPlayer = {
    player_id: 'human',
    name: 'Human',
    stack: 1000,
    current_bet: 0,
    total_invested: 0,
    hole_cards: [],
    is_active: true,
    is_current_turn: true,
    all_in: false,
    is_human: true,
    folded: false,
  }

  const defaultState = {
    state: 'pre_flop',
    pot: 0,
    current_bet: 0,
    small_blind: 5,
    big_blind: 10,
    last_raise_amount: null,
    dealer_position: 0,
    small_blind_position: 1,
    big_blind_position: 2,
    current_player_index: 0,
    hand_count: 1,
    players: [
      mockPlayer,
      { ...mockPlayer, player_id: 'ai1', name: 'AI 1', is_human: false, is_current_turn: false },
      { ...mockPlayer, player_id: 'ai2', name: 'AI 2', is_human: false, is_current_turn: false },
      { ...mockPlayer, player_id: 'ai3', name: 'AI 3', is_human: false, is_current_turn: false },
    ],
    human_player: mockPlayer,
    community_cards: [],
    last_ai_decisions: {},
  }

  return {
    ...defaultState,
    ...overrides,
    // Merge players if provided
    players: overrides.players || defaultState.players,
    human_player: overrides.human_player || defaultState.human_player,
  }
}

/**
 * Create a mock Player object.
 */
export function createMockPlayer(overrides: Partial<any> = {}) {
  return {
    player_id: 'test-player',
    name: 'Test Player',
    stack: 1000,
    current_bet: 0,
    total_invested: 0,
    hole_cards: [],
    is_active: true,
    is_current_turn: false,
    all_in: false,
    is_human: false,
    folded: false,
    personality: 'Balanced',
    ...overrides,
  }
}

/**
 * Custom render that can inject providers if needed.
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions
) {
  return render(ui, { ...options })
}

// Re-export everything from React Testing Library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
