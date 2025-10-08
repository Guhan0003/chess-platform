/**
 * WebSocket Manager for Real-time Chess Communication
 *       this.gameSocket.onclose = (event) => {
        this.isConnected = false;
        this._triggerEvent('disconnected', { type: 'game', code: event.code, reason: event.reason });
        
        if (this.reconnectAttempts < this.maxReconnectAttempts && event.code !== 1000) {
          this._scheduleReconnect();
        }
      };ate synchronization, move updates, and timer management
 */

class GameWebSocket {
  constructor(gameId, accessToken) {
    this.gameId = gameId;
    this.accessToken = accessToken;
    this.gameSocket = null;
    this.timerSocket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.eventHandlers = new Map();
    this.isConnected = false;
    this.connectionPromise = null;
    
    // Bind methods
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.sendMessage = this.sendMessage.bind(this);
    this.makeMove = this.makeMove.bind(this);
  }

  /**
   * Connect to WebSocket servers
   */
  async connect() {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._connect();
    return this.connectionPromise;
  }

  async _connect() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      
      // Connect to game WebSocket  
      const gameWsUrl = `${protocol}//${host}/ws/game/${this.gameId}/?token=${this.accessToken}`;
      
      // Create WebSocket with error suppression
      this.gameSocket = new WebSocket(gameWsUrl);
      
      // Suppress browser's native connection error messages
      this.gameSocket.addEventListener('error', () => {
        // Silent handling - we'll show our own clean message
      });
      
      // Setup game socket event handlers
      this.gameSocket.onopen = (event) => {
        console.log('✅ WebSocket connected - Real-time moves enabled');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this._triggerEvent('connected', { type: 'game' });
      };

      this.gameSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._handleGameMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.gameSocket.onclose = (event) => {
        this.isConnected = false;
        this._triggerEvent('disconnected', { type: 'game', code: event.code });
        
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this._scheduleReconnect();
        }
      };

      this.gameSocket.onerror = (error) => {
        // WebSocket connection failed - but we have polling fallback
        if (this.reconnectAttempts === 0) {
          console.warn('⚠️ WebSocket connection failed - using fast polling fallback');
        }
        this._triggerEvent('error', { type: 'game', error });
      };

      // Connect to timer WebSocket (optional)
      try {
        const timerWsUrl = `${protocol}//${host}/ws/timer/${this.gameId}/?token=${this.accessToken}`;
        this.timerSocket = new WebSocket(timerWsUrl);
        
        // Suppress browser's native timer connection error messages
        this.timerSocket.addEventListener('error', () => {
          // Silent handling - timer is optional
        });
        
        this.timerSocket.onopen = () => {
          // Timer WebSocket connected - silent success
        };
        
        this.timerSocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this._handleTimerMessage(data);
          } catch (error) {
            console.warn('Timer message parsing failed');
          }
        };
        
        this.timerSocket.onerror = () => {
          // Silent fallback for timer WebSocket - not critical
        };
        
        this.timerSocket.onclose = () => {
          // Silent fallback for timer WebSocket - polling handles timing
        };
        
      } catch (error) {
        // Timer WebSocket is optional - silent fallback to polling
      }

      // Wait for connection to be established
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.gameSocket.addEventListener('open', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.gameSocket.addEventListener('error', () => {
          clearTimeout(timeout);
          reject(new Error('WebSocket connection failed'));
        });
      });

      return true;
      
    } catch (error) {
      console.warn('WebSocket connection failed - falling back to polling');
      this.connectionPromise = null;
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket servers
   */
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
    
    if (this.gameSocket) {
      this.gameSocket.close(1000, 'Client disconnect');
      this.gameSocket = null;
    }
    
    if (this.timerSocket) {
      this.timerSocket.close(1000, 'Client disconnect');
      this.timerSocket = null;
    }
    
    this.isConnected = false;
    this.connectionPromise = null;
  }

  /**
   * Send message through game WebSocket
   */
  sendMessage(message) {
    if (!this.gameSocket || this.gameSocket.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      this.gameSocket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Make a move through WebSocket
   */
  makeMove(fromSquare, toSquare, promotion = null) {
    const message = {
      type: 'make_move',
      from_square: fromSquare,
      to_square: toSquare,
      promotion: promotion
    };

    return this.sendMessage(message);
  }

  /**
   * Request current game state
   */
  requestGameState() {
    return this.sendMessage({ type: 'request_game_state' });
  }

  /**
   * Send ping to keep connection alive
   */
  ping() {
    return this.sendMessage({ type: 'ping' });
  }

  /**
   * Add event handler
   */
  on(event, handler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event).push(handler);
  }

  /**
   * Remove event handler
   */
  off(event, handler) {
    if (this.eventHandlers.has(event)) {
      const handlers = this.eventHandlers.get(event);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Trigger event handlers
   */
  _triggerEvent(event, data) {
    if (this.eventHandlers.has(event)) {
      this.eventHandlers.get(event).forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Handle game WebSocket messages
   */
  _handleGameMessage(data) {
    // Process game message silently

    switch (data.type) {
      case 'game_state':
        this._triggerEvent('gameState', data.data);
        break;
        
      case 'move_made':
        this._triggerEvent('moveMade', data);
        break;
        
      case 'player_connected':
        this._triggerEvent('playerConnected', data);
        break;
        
      case 'player_disconnected':
        this._triggerEvent('playerDisconnected', data);
        break;
        
      case 'game_finished':
        this._triggerEvent('gameFinished', data);
        break;
        
      case 'error':
        this._triggerEvent('error', data);
        break;
        
      case 'pong':
        this._triggerEvent('pong', data);
        break;
        
      default:
        console.warn('Unknown game message type:', data.type);
    }
  }

  /**
   * Handle timer WebSocket messages
   */
  _handleTimerMessage(data) {
    if (data.type === 'timer_tick') {
      this._triggerEvent('timerUpdate', data.data);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  _scheduleReconnect() {
    this.reconnectAttempts++;
    
    setTimeout(() => {
      this.connectionPromise = null;
      this.connect().catch(error => {
        console.warn('WebSocket reconnection failed - using polling mode');
      });
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      gameSocket: this.gameSocket?.readyState,
      timerSocket: this.timerSocket?.readyState,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

/**
 * Global WebSocket manager for easy access
 */
class WebSocketManager {
  constructor() {
    this.gameConnections = new Map();
  }

  /**
   * Connect to a game's WebSocket
   */
  async connectToGame(gameId, accessToken) {
    const key = `game_${gameId}`;
    
    if (this.gameConnections.has(key)) {
      const existing = this.gameConnections.get(key);
      if (existing.isConnected) {
        return existing;
      } else {
        existing.disconnect();
        this.gameConnections.delete(key);
      }
    }

    const gameWs = new GameWebSocket(gameId, accessToken);
    await gameWs.connect();
    
    this.gameConnections.set(key, gameWs);
    return gameWs;
  }

  /**
   * Disconnect from a game's WebSocket
   */
  disconnectFromGame(gameId) {
    const key = `game_${gameId}`;
    
    if (this.gameConnections.has(key)) {
      const gameWs = this.gameConnections.get(key);
      gameWs.disconnect();
      this.gameConnections.delete(key);
    }
  }

  /**
   * Get WebSocket connection for a game
   */
  getGameConnection(gameId) {
    const key = `game_${gameId}`;
    return this.gameConnections.get(key);
  }

  /**
   * Disconnect all connections
   */
  disconnectAll() {
    this.gameConnections.forEach((gameWs) => {
      gameWs.disconnect();
    });
    this.gameConnections.clear();
  }

  /**
   * Get status of all connections
   */
  getAllConnectionStatuses() {
    const statuses = {};
    this.gameConnections.forEach((gameWs, key) => {
      statuses[key] = gameWs.getConnectionStatus();
    });
    return statuses;
  }
}

// Create global instance
window.webSocketManager = new WebSocketManager();

// Export classes for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GameWebSocket, WebSocketManager };
}