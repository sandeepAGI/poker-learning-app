/**
 * WebSocket Client for Real-Time Poker Game Updates
 * Phase 1.3: Frontend WebSocket infrastructure
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Event-driven architecture
 * - Type-safe message handling
 * - Connection state management
 * - Error handling and logging
 */

import { GameState } from './types';

// WebSocket message types from backend
export interface WSMessage {
  type: 'state_update' | 'ai_action' | 'error' | 'game_over' | 'awaiting_continue' | 'auto_resumed';
  data: any;
}

// WebSocket client callbacks
export interface WebSocketCallbacks {
  onStateUpdate: (state: GameState) => void;
  onError: (error: string) => void;
  onGameOver: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
  onAwaitingContinue?: (playerName: string, action: string) => void; // Phase 4: Step Mode
  onAutoResumed?: (reason: string) => void; // Issue #4: Step Mode auto-resume notification
}

// Connection states
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed'
}

export class PokerWebSocket {
  private ws: WebSocket | null = null;
  private gameId: string;
  private callbacks: WebSocketCallbacks;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000; // Start with 1 second
  private reconnectTimer: NodeJS.Timeout | null = null;
  private shouldReconnect: boolean = true;

  constructor(gameId: string, callbacks: WebSocketCallbacks) {
    this.gameId = gameId;
    this.callbacks = callbacks;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    this.connectionState = ConnectionState.CONNECTING;
    console.log(`[WebSocket] Connecting to game ${this.gameId}...`);

    const wsUrl = this.getWebSocketUrl();

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventListeners();
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.handleError('Failed to connect to server');
      this.attemptReconnect();
    }
  }

  /**
   * Get WebSocket URL (handles http/https → ws/wss conversion)
   */
  private getWebSocketUrl(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws';
    const host = apiUrl.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${host}/ws/${this.gameId}`;
  }

  /**
   * Setup WebSocket event listeners
   */
  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected!');
      this.connectionState = ConnectionState.CONNECTED;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.callbacks.onConnect();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      this.handleError('WebSocket error occurred');
    };

    this.ws.onclose = (event) => {
      console.log(`[WebSocket] Disconnected (code: ${event.code})`);
      this.connectionState = ConnectionState.DISCONNECTED;
      this.callbacks.onDisconnect();

      // Attempt reconnection if not closed intentionally
      if (this.shouldReconnect && event.code !== 1000) {
        this.attemptReconnect();
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WSMessage): void {
    console.log('[WebSocket] Received:', message.type, message.data);

    switch (message.type) {
      case 'state_update':
        this.callbacks.onStateUpdate(message.data);
        break;

      case 'error':
        this.handleError(message.data.message || 'Unknown error');
        break;

      case 'game_over':
        this.callbacks.onGameOver();
        break;

      case 'awaiting_continue':
        // Phase 4: Step Mode - waiting for user to continue
        if (this.callbacks.onAwaitingContinue) {
          this.callbacks.onAwaitingContinue(
            message.data.player_name,
            message.data.action
          );
        }
        break;

      case 'auto_resumed':
        // Issue #4: Step Mode auto-resumed after timeout
        if (this.callbacks.onAutoResumed) {
          this.callbacks.onAutoResumed(message.data.reason);
        }
        break;

      default:
        console.warn('[WebSocket] Unknown message type:', message.type);
    }
  }

  /**
   * Send action to server
   */
  sendAction(action: 'fold' | 'call' | 'raise', amount?: number, showAiThinking: boolean = false, stepMode: boolean = false): void {
    if (!this.isConnected()) {
      console.error('[WebSocket] Cannot send action: not connected');
      this.handleError('Not connected to server');
      return;
    }

    const message = {
      type: 'action',
      action,
      amount,
      show_ai_thinking: showAiThinking,
      step_mode: stepMode // Phase 4: Step Mode
    };

    console.log('[WebSocket] Sending action:', message);
    this.ws!.send(JSON.stringify(message));
  }

  /**
   * Request next hand
   */
  nextHand(showAiThinking: boolean = false, stepMode: boolean = false): void {
    if (!this.isConnected()) {
      console.error('[WebSocket] Cannot start next hand: not connected');
      this.handleError('Not connected to server');
      return;
    }

    const message = {
      type: 'next_hand',
      show_ai_thinking: showAiThinking,
      step_mode: stepMode // Phase 4: Step Mode
    };

    console.log('[WebSocket] Starting next hand');
    this.ws!.send(JSON.stringify(message));
  }

  /**
   * Send continue signal (Phase 4: Step Mode)
   */
  sendContinue(): void {
    if (!this.isConnected()) {
      console.error('[WebSocket] Cannot send continue: not connected');
      this.handleError('Not connected to server');
      return;
    }

    const message = {
      type: 'continue'
    };

    console.log('[WebSocket] Sending continue signal');
    this.ws!.send(JSON.stringify(message));
  }

  /**
   * Request current game state
   */
  getState(showAiThinking: boolean = false): void {
    if (!this.isConnected()) {
      console.error('[WebSocket] Cannot get state: not connected');
      return;
    }

    const message = {
      type: 'get_state',
      show_ai_thinking: showAiThinking
    };

    console.log('[WebSocket] Requesting state');
    this.ws!.send(JSON.stringify(message));
  }

  /**
   * Disconnect from WebSocket (intentional)
   */
  disconnect(): void {
    console.log('[WebSocket] Disconnecting...');
    this.shouldReconnect = false;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect'); // Normal closure
      this.ws = null;
    }

    this.connectionState = ConnectionState.DISCONNECTED;
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (!this.shouldReconnect) {
      console.log('[WebSocket] Reconnection disabled');
      return;
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.connectionState = ConnectionState.FAILED;
      this.handleError('Failed to reconnect after multiple attempts');
      return;
    }

    this.reconnectAttempts++;
    this.connectionState = ConnectionState.RECONNECTING;

    console.log(
      `[WebSocket] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect();
      // Exponential backoff: 1s, 2s, 4s, 8s, 16s
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 16000);
    }, this.reconnectDelay);
  }

  /**
   * Handle errors
   */
  private handleError(message: string): void {
    console.error('[WebSocket] Error:', message);
    this.callbacks.onError(message);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Get reconnection info
   */
  getReconnectInfo(): { attempts: number; maxAttempts: number; delay: number } {
    return {
      attempts: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      delay: this.reconnectDelay
    };
  }
}
