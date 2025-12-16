import { useState, useEffect } from 'react';
import type { GameState, AIDecision } from '../types';

/**
 * AI Decision Entry in history
 */
export interface AIDecisionEntry {
  playerName: string;
  playerId: string;
  decision: AIDecision;
  timestamp: number;
}

/**
 * Custom hook to manage AI decision history
 *
 * This hook tracks AI decisions from the game state and maintains a
 * deduplicated history. It automatically clears the history when a new
 * hand starts (pre_flop state).
 *
 * @param gameState - Current game state containing AI decisions
 * @returns Array of AI decision entries in chronological order (newest first)
 *
 * @example
 * ```tsx
 * const decisionHistory = useAIDecisionHistory(gameState);
 * ```
 *
 * @remarks
 * - Uses functional setState to avoid circular dependencies
 * - Deduplicates decisions based on playerId and reasoning text
 * - Clears history automatically on pre_flop state
 * - Returns empty array when gameState is null
 */
export function useAIDecisionHistory(gameState: GameState | null): AIDecisionEntry[] {
  const [decisionHistory, setDecisionHistory] = useState<AIDecisionEntry[]>([]);

  useEffect(() => {
    if (!gameState) return;

    setDecisionHistory(prev => {
      // Clear history when starting a new hand
      if (gameState.state === 'pre_flop' && prev.length > 0) {
        return [];
      }

      // Add new AI decisions to history
      const newDecisions: AIDecisionEntry[] = [];
      Object.entries(gameState.last_ai_decisions).forEach(([playerId, decision]) => {
        // Check if this decision is already in history (check against prev)
        const alreadyExists = prev.some(
          entry => entry.playerId === playerId && entry.decision.reasoning === decision.reasoning
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
        return [...newDecisions, ...prev];
      }

      return prev;
    });
  }, [gameState]);

  return decisionHistory;
}
