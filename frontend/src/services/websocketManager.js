// WebSocket manager for real-time game updates
import { useState, useEffect } from 'react';
import { correlation } from './apiClient';

// WebSocket connection states
const CONNECTION_STATES = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
};

// Event types
const EVENT_TYPES = {
  GAME_UPDATE: 'game_update',
  PLAYER_ACTION: 'player_action',
  ROUND_COMPLETE: 'round_complete',
  PLAYER_JOINED: 'player_joined',
  PLAYER_LEFT: 'player_left',
  CONNECTION_STATUS: 'connection_status',
  ERROR: 'error'
};

class WebSocketManager {
  constructor() {
    this.ws = null;
    this.gameId = null;
    this.playerId = null;
    this.connectionState = CONNECTION_STATES.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.heartbeatInterval = 30000; // 30 seconds
    this.eventListeners = new Map();
    this.messageQueue = [];
    this.correlationId = null;

    // Bind methods
    this.handleOpen = this.handleOpen.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleError = this.handleError.bind(this);
    this.sendHeartbeat = this.sendHeartbeat.bind(this);
  }

  // Connect to WebSocket
  connect(gameId, playerId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('[WebSocket] Already connected');
      return;
    }

    this.gameId = gameId;
    this.playerId = playerId;
    this.correlationId = correlation.trackUserAction('websocket_connect', {
      gameId,
      playerId
    });

    this.setConnectionState(CONNECTION_STATES.CONNECTING);

    const wsUrl = this.buildWebSocketUrl(gameId, playerId);
    console.log(`[WebSocket] Connecting to ${wsUrl}`);

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.onopen = this.handleOpen;
      this.ws.onmessage = this.handleMessage;
      this.ws.onclose = this.handleClose;
      this.ws.onerror = this.handleError;
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      this.setConnectionState(CONNECTION_STATES.ERROR);
      this.scheduleReconnect();
    }
  }

  // Disconnect from WebSocket
  disconnect() {
    console.log('[WebSocket] Disconnecting...');
    
    this.clearReconnectTimer();
    this.clearHeartbeatTimer();
    
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Client disconnect');
      }
      this.ws = null;
    }

    this.setConnectionState(CONNECTION_STATES.DISCONNECTED);
    this.gameId = null;
    this.playerId = null;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
  }

  // Send message through WebSocket
  send(message) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Connection not ready, queuing message:', message);
      this.messageQueue.push(message);
      return false;
    }

    try {
      const messageWithCorrelation = {
        ...message,
        correlationId: correlation.trackUserAction('websocket_send', message),
        timestamp: new Date().toISOString()
      };

      this.ws.send(JSON.stringify(messageWithCorrelation));
      console.log('[WebSocket] Message sent:', messageWithCorrelation);
      return true;
    } catch (error) {
      console.error('[WebSocket] Send failed:', error);
      return false;
    }
  }

  // Send player action
  sendPlayerAction(action, amount = null) {
    return this.send({
      type: 'player_action',
      data: {
        playerId: this.playerId,
        action,
        amount
      }
    });
  }

  // Add event listener
  addEventListener(eventType, callback) {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }
    this.eventListeners.get(eventType).add(callback);
  }

  // Remove event listener
  removeEventListener(eventType, callback) {
    if (this.eventListeners.has(eventType)) {
      this.eventListeners.get(eventType).delete(callback);
    }
  }

  // Remove all event listeners
  removeAllEventListeners() {
    this.eventListeners.clear();
  }

  // Get connection state
  getConnectionState() {
    return this.connectionState;
  }

  // Get connection info
  getConnectionInfo() {
    return {
      state: this.connectionState,
      gameId: this.gameId,
      playerId: this.playerId,
      reconnectAttempts: this.reconnectAttempts,
      correlationId: this.correlationId,
      readyState: this.ws ? this.ws.readyState : null,
      queuedMessages: this.messageQueue.length
    };
  }

  // Private methods

  buildWebSocketUrl(gameId, playerId) {
    const baseUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8080';
    const correlationId = this.correlationId;
    return `${baseUrl}/api/ws/games/${gameId}?player_id=${playerId}&correlation_id=${correlationId}`;
  }

  setConnectionState(newState) {
    const oldState = this.connectionState;
    this.connectionState = newState;
    
    console.log(`[WebSocket] State change: ${oldState} -> ${newState}`);
    
    this.emit(EVENT_TYPES.CONNECTION_STATUS, {
      state: newState,
      previousState: oldState,
      gameId: this.gameId,
      playerId: this.playerId
    });
  }

  handleOpen(event) {
    console.log('[WebSocket] Connected successfully');
    this.setConnectionState(CONNECTION_STATES.CONNECTED);
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000; // Reset delay
    
    this.startHeartbeat();
    this.processMessageQueue();
  }

  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('[WebSocket] Message received:', message);

      // Handle different message types
      switch (message.type) {
        case EVENT_TYPES.GAME_UPDATE:
          this.emit(EVENT_TYPES.GAME_UPDATE, message.data);
          break;
        case EVENT_TYPES.PLAYER_ACTION:
          this.emit(EVENT_TYPES.PLAYER_ACTION, message.data);
          break;
        case EVENT_TYPES.ROUND_COMPLETE:
          this.emit(EVENT_TYPES.ROUND_COMPLETE, message.data);
          break;
        case EVENT_TYPES.PLAYER_JOINED:
          this.emit(EVENT_TYPES.PLAYER_JOINED, message.data);
          break;
        case EVENT_TYPES.PLAYER_LEFT:
          this.emit(EVENT_TYPES.PLAYER_LEFT, message.data);
          break;
        case 'pong':
          // Heartbeat response
          console.log('[WebSocket] Heartbeat acknowledged');
          break;
        default:
          console.warn('[WebSocket] Unknown message type:', message.type);
          this.emit(message.type, message.data);
      }
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error);
      this.emit(EVENT_TYPES.ERROR, {
        type: 'parse_error',
        error: error.message,
        rawMessage: event.data
      });
    }
  }

  handleClose(event) {
    console.log(`[WebSocket] Connection closed:`, {
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean
    });

    this.clearHeartbeatTimer();
    
    if (event.code !== 1000) { // Not a normal closure
      this.setConnectionState(CONNECTION_STATES.DISCONNECTED);
      this.scheduleReconnect();
    } else {
      this.setConnectionState(CONNECTION_STATES.DISCONNECTED);
    }
  }

  handleError(error) {
    console.error('[WebSocket] Error:', error);
    this.setConnectionState(CONNECTION_STATES.ERROR);
    
    this.emit(EVENT_TYPES.ERROR, {
      type: 'connection_error',
      error: error.message || 'WebSocket connection error'
    });
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.emit(EVENT_TYPES.ERROR, {
        type: 'max_reconnect_attempts',
        attempts: this.reconnectAttempts
      });
      return;
    }

    this.clearReconnectTimer();
    this.setConnectionState(CONNECTION_STATES.RECONNECTING);
    
    console.log(`[WebSocket] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts + 1})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.gameId, this.playerId);
      
      // Exponential backoff with jitter
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2 + Math.random() * 1000,
        this.maxReconnectDelay
      );
    }, this.reconnectDelay);
  }

  clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  startHeartbeat() {
    this.clearHeartbeatTimer();
    this.heartbeatTimer = setInterval(this.sendHeartbeat, this.heartbeatInterval);
  }

  clearHeartbeatTimer() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  sendHeartbeat() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send({ type: 'ping' });
    }
  }

  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  emit(eventType, data) {
    if (this.eventListeners.has(eventType)) {
      this.eventListeners.get(eventType).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] Event listener error for ${eventType}:`, error);
        }
      });
    }
  }
}

// Create singleton instance
const websocketManager = new WebSocketManager();

// React hook for WebSocket integration

export const useWebSocket = (gameId, playerId) => {
  const [connectionState, setConnectionState] = useState(
    websocketManager.getConnectionState()
  );

  useEffect(() => {
    // Connect when component mounts
    if (gameId && playerId) {
      websocketManager.connect(gameId, playerId);
    }

    // Listen for connection state changes
    const handleConnectionState = (data) => {
      setConnectionState(data.state);
    };

    websocketManager.addEventListener(EVENT_TYPES.CONNECTION_STATUS, handleConnectionState);

    // Cleanup on unmount
    return () => {
      websocketManager.removeEventListener(EVENT_TYPES.CONNECTION_STATUS, handleConnectionState);
      websocketManager.disconnect();
    };
  }, [gameId, playerId]);

  return {
    connectionState,
    send: websocketManager.send.bind(websocketManager),
    sendPlayerAction: websocketManager.sendPlayerAction.bind(websocketManager),
    addEventListener: websocketManager.addEventListener.bind(websocketManager),
    removeEventListener: websocketManager.removeEventListener.bind(websocketManager),
    getConnectionInfo: websocketManager.getConnectionInfo.bind(websocketManager)
  };
};

// Export constants and manager
export { CONNECTION_STATES, EVENT_TYPES };
export default websocketManager;