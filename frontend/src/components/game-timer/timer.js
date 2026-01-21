/**
 * Chess Game Timer Component
 * Professional timer display with real-time countdown and visual indicators
 */

class GameTimer {
  /**
   * Create a timer component
   * @param {Object} options - Timer configuration
   * @param {string} options.whiteTimerSelector - CSS selector for white timer element
   * @param {string} options.blackTimerSelector - CSS selector for black timer element
   * @param {number} options.initialWhiteTime - Initial time for white in seconds
   * @param {number} options.initialBlackTime - Initial time for black in seconds
   * @param {number} options.increment - Time increment per move in seconds
   * @param {string} options.timeControl - Time control type ('bullet', 'blitz', 'rapid', 'classical')
   * @param {Function} options.onTimeout - Callback when a player runs out of time
   * @param {Function} options.onLowTime - Callback when a player has low time
   */
  constructor(options = {}) {
    this.whiteTimerEl = document.querySelector(options.whiteTimerSelector || '#whiteTimer');
    this.blackTimerEl = document.querySelector(options.blackTimerSelector || '#blackTimer');
    
    this.whiteTime = options.initialWhiteTime ?? 600; // Default 10 minutes
    this.blackTime = options.initialBlackTime ?? 600;
    this.increment = options.increment ?? 0;
    this.timeControl = options.timeControl || 'rapid';
    
    this.currentTurn = 'white';
    this.isRunning = false;
    this.intervalId = null;
    this.lastTickTime = null;
    
    // Thresholds for visual indicators (in seconds)
    this.lowTimeThreshold = 30;
    this.criticalTimeThreshold = 10;
    
    // Callbacks
    this.onTimeout = options.onTimeout || (() => {});
    this.onLowTime = options.onLowTime || (() => {});
    this.onTick = options.onTick || (() => {});
    
    // Audio for time warnings
    this.lowTimeWarningPlayed = { white: false, black: false };
    
    // Initialize display
    this.updateDisplay();
  }

  /**
   * Start the timer
   */
  start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.lastTickTime = Date.now();
    
    // High-precision interval (100ms for smooth countdown)
    this.intervalId = setInterval(() => this.tick(), 100);
    
    this.updateActiveIndicators();
    console.log(`⏱️ Timer started - ${this.currentTurn}'s turn`);
  }

  /**
   * Stop the timer
   */
  stop() {
    if (!this.isRunning) return;
    
    this.isRunning = false;
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    this.updateActiveIndicators();
    console.log('⏱️ Timer stopped');
  }

  /**
   * Pause the timer (keeps state, can resume)
   */
  pause() {
    this.stop();
  }

  /**
   * Resume the timer after pause
   */
  resume() {
    this.start();
  }

  /**
   * Handle a move being made
   * @param {string} playerColor - 'white' or 'black'
   */
  makeMove(playerColor) {
    if (playerColor !== this.currentTurn) {
      console.warn(`Timer: Expected ${this.currentTurn} to move, got ${playerColor}`);
      return;
    }
    
    // Add increment to the player who just moved
    if (this.increment > 0) {
      if (playerColor === 'white') {
        this.whiteTime += this.increment;
      } else {
        this.blackTime += this.increment;
      }
    }
    
    // Switch turn
    this.currentTurn = this.currentTurn === 'white' ? 'black' : 'white';
    this.lastTickTime = Date.now();
    
    // Update display
    this.updateDisplay();
    this.updateActiveIndicators();
    
    console.log(`⏱️ Move made - now ${this.currentTurn}'s turn`);
  }

  /**
   * Timer tick - called every 100ms
   */
  tick() {
    if (!this.isRunning) return;
    
    const now = Date.now();
    const elapsed = (now - this.lastTickTime) / 1000; // Convert to seconds
    this.lastTickTime = now;
    
    // Deduct time from current player
    if (this.currentTurn === 'white') {
      this.whiteTime = Math.max(0, this.whiteTime - elapsed);
      
      // Check for low time
      if (this.whiteTime <= this.lowTimeThreshold && !this.lowTimeWarningPlayed.white) {
        this.lowTimeWarningPlayed.white = true;
        this.onLowTime('white', this.whiteTime);
      }
      
      // Check for timeout
      if (this.whiteTime <= 0) {
        this.handleTimeout('white');
        return;
      }
    } else {
      this.blackTime = Math.max(0, this.blackTime - elapsed);
      
      // Check for low time
      if (this.blackTime <= this.lowTimeThreshold && !this.lowTimeWarningPlayed.black) {
        this.lowTimeWarningPlayed.black = true;
        this.onLowTime('black', this.blackTime);
      }
      
      // Check for timeout
      if (this.blackTime <= 0) {
        this.handleTimeout('black');
        return;
      }
    }
    
    this.updateDisplay();
    this.onTick(this.getState());
  }

  /**
   * Handle timeout
   * @param {string} playerColor - Player who ran out of time
   */
  handleTimeout(playerColor) {
    this.stop();
    console.log(`⏱️ Timeout: ${playerColor} ran out of time!`);
    this.onTimeout(playerColor);
  }

  /**
   * Update the timer display
   */
  updateDisplay() {
    if (this.whiteTimerEl) {
      this.whiteTimerEl.textContent = this.formatTime(this.whiteTime);
      this.updateTimerStyling(this.whiteTimerEl, this.whiteTime, this.currentTurn === 'white');
    }
    
    if (this.blackTimerEl) {
      this.blackTimerEl.textContent = this.formatTime(this.blackTime);
      this.updateTimerStyling(this.blackTimerEl, this.blackTime, this.currentTurn === 'black');
    }
  }

  /**
   * Update timer element styling based on time remaining
   * @param {HTMLElement} element - Timer element
   * @param {number} time - Time remaining in seconds
   * @param {boolean} isActive - Whether this is the active player's timer
   */
  updateTimerStyling(element, time, isActive) {
    // Remove existing classes
    element.classList.remove('timer-active', 'timer-low', 'timer-critical', 'timer-pulse');
    
    // Add active class
    if (isActive && this.isRunning) {
      element.classList.add('timer-active');
    }
    
    // Add time-based classes
    if (time <= this.criticalTimeThreshold) {
      element.classList.add('timer-critical', 'timer-pulse');
    } else if (time <= this.lowTimeThreshold) {
      element.classList.add('timer-low');
    }
  }

  /**
   * Update active turn indicators on player cards
   */
  updateActiveIndicators() {
    // Find parent player cards and update their state
    if (this.whiteTimerEl) {
      const whiteCard = this.whiteTimerEl.closest('.player-card');
      if (whiteCard) {
        whiteCard.classList.toggle('current-turn', this.currentTurn === 'white' && this.isRunning);
      }
    }
    
    if (this.blackTimerEl) {
      const blackCard = this.blackTimerEl.closest('.player-card');
      if (blackCard) {
        blackCard.classList.toggle('current-turn', this.currentTurn === 'black' && this.isRunning);
      }
    }
  }

  /**
   * Format time as MM:SS or M:SS.s for low time
   * @param {number} seconds - Time in seconds
   * @returns {string} Formatted time string
   */
  formatTime(seconds) {
    if (seconds === null || seconds === undefined) return '∞';
    if (seconds < 0) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    
    // Show decimal for very low time
    if (seconds < 10) {
      const decimal = Math.floor((seconds % 1) * 10);
      return `${secs}.${decimal}`;
    }
    
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Sync timer with server data
   * @param {Object} serverData - Timer data from server
   */
  syncWithServer(serverData) {
    if (serverData.white_time !== undefined) {
      this.whiteTime = serverData.white_time;
    }
    if (serverData.black_time !== undefined) {
      this.blackTime = serverData.black_time;
    }
    if (serverData.current_turn) {
      this.currentTurn = serverData.current_turn;
    }
    if (serverData.is_active !== undefined) {
      if (serverData.is_active && !this.isRunning) {
        this.start();
      } else if (!serverData.is_active && this.isRunning) {
        this.stop();
      }
    }
    
    this.updateDisplay();
    this.updateActiveIndicators();
  }

  /**
   * Set current turn manually
   * @param {string} turn - 'white' or 'black'
   */
  setTurn(turn) {
    this.currentTurn = turn;
    this.updateDisplay();
    this.updateActiveIndicators();
  }

  /**
   * Set time for a player
   * @param {string} color - 'white' or 'black'
   * @param {number} time - Time in seconds
   */
  setTime(color, time) {
    if (color === 'white') {
      this.whiteTime = time;
    } else {
      this.blackTime = time;
    }
    this.updateDisplay();
  }

  /**
   * Get current timer state
   * @returns {Object} Timer state
   */
  getState() {
    return {
      whiteTime: this.whiteTime,
      blackTime: this.blackTime,
      currentTurn: this.currentTurn,
      isRunning: this.isRunning,
      increment: this.increment,
      timeControl: this.timeControl
    };
  }

  /**
   * Reset timer to initial values
   * @param {number} initialTime - Initial time in seconds (optional)
   */
  reset(initialTime = null) {
    this.stop();
    
    if (initialTime !== null) {
      this.whiteTime = initialTime;
      this.blackTime = initialTime;
    }
    
    this.currentTurn = 'white';
    this.lowTimeWarningPlayed = { white: false, black: false };
    
    this.updateDisplay();
    this.updateActiveIndicators();
  }

  /**
   * Destroy the timer instance
   */
  destroy() {
    this.stop();
    this.whiteTimerEl = null;
    this.blackTimerEl = null;
  }
}

// Factory function to create timer with time control presets
function createGameTimer(timeControlType, options = {}) {
  // Professional time controls - Categories: Bullet (<3min), Blitz (3-10min), Rapid (10-30min), Classical (>30min)
  const timeControls = {
    // Ultra-Bullet & Bullet (30 sec - 2 min)
    'bullet_30s': { initial: 30, increment: 0, category: 'bullet', display: '⚡ 30 sec' },
    'bullet_1': { initial: 60, increment: 0, category: 'bullet', display: '⚡ 1 min' },
    'bullet_1_1': { initial: 60, increment: 1, category: 'bullet', display: '⚡ 1|1' },
    'bullet_2': { initial: 120, increment: 0, category: 'bullet', display: '⚡ 2 min' },
    'bullet_2_1': { initial: 120, increment: 1, category: 'bullet', display: '⚡ 2|1' },
    
    // Blitz (3-10 minutes)
    'blitz_3': { initial: 180, increment: 0, category: 'blitz', display: '🔥 3 min' },
    'blitz_3_2': { initial: 180, increment: 2, category: 'blitz', display: '🔥 3|2' },
    'blitz_5': { initial: 300, increment: 0, category: 'blitz', display: '🔥 5 min' },
    'blitz_5_3': { initial: 300, increment: 3, category: 'blitz', display: '🔥 5|3' },
    'blitz_5_5': { initial: 300, increment: 5, category: 'blitz', display: '🔥 5|5' },
    
    // Rapid (10-30 minutes)
    'rapid_10': { initial: 600, increment: 0, category: 'rapid', display: '🏃 10 min' },
    'rapid_10_5': { initial: 600, increment: 5, category: 'rapid', display: '🏃 10|5' },
    'rapid_15': { initial: 900, increment: 0, category: 'rapid', display: '🏃 15 min' },
    'rapid_15_10': { initial: 900, increment: 10, category: 'rapid', display: '🏃 15|10' },
    
    // Classical (30+ minutes)
    'classical_30': { initial: 1800, increment: 0, category: 'classical', display: '♔ 30 min' },
    'classical_30_20': { initial: 1800, increment: 20, category: 'classical', display: '♔ 30|20' },
    'classical_60': { initial: 3600, increment: 0, category: 'classical', display: '♔ 60 min' },
    'classical_90_30': { initial: 5400, increment: 30, category: 'classical', display: '♔ 90|30' },
    
    // Unlimited
    'unlimited': { initial: null, increment: 0, category: 'unlimited', display: '∞ Unlimited' },
    
    // Simple category mappings for backward compatibility
    'bullet': { initial: 120, increment: 0, category: 'bullet', display: '⚡ 2 min' },
    'blitz': { initial: 300, increment: 0, category: 'blitz', display: '🔥 5 min' },
    'rapid': { initial: 600, increment: 0, category: 'rapid', display: '🏃 10 min' },
    'classical': { initial: 1800, increment: 0, category: 'classical', display: '♔ 30 min' }
  };

  const preset = timeControls[timeControlType] || timeControls['rapid_10'];
  
  return new GameTimer({
    initialWhiteTime: preset.initial,
    initialBlackTime: preset.initial,
    increment: preset.increment,
    timeControl: timeControlType.split('_')[0], // Extract category
    ...options
  });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GameTimer, createGameTimer };
}
