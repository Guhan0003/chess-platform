/**
 * Game Session Guard System
 * Professional implementation for preventing unauthorized game exits
 * and handling active game reconnection scenarios
 */

class GameSessionGuard {
  constructor(apiInstance) {
    this.api = apiInstance;
    this.isInitialized = false;
    this.activeGames = [];
    this.currentGameId = null;
    this.navigationBlocked = false;
    
    // Bind methods
    this.handleBeforeUnload = this.handleBeforeUnload.bind(this);
    this.handleNavigation = this.handleNavigation.bind(this);
    this.showResignationDialog = this.showResignationDialog.bind(this);
  }

  /**
   * Initialize the game session guard
   */
  async initialize() {
    if (this.isInitialized) return;
    
    // Set up navigation guards
    this.setupNavigationGuards();
    
    // Check for active games on initialization
    await this.checkActiveGames();
    
    this.isInitialized = true;
    console.log('🛡️ Game Session Guard initialized successfully');
  }

  /**
   * Set up navigation guards to prevent unauthorized exits
   */
  setupNavigationGuards() {
    // Prevent page unload/refresh during active games
    window.addEventListener('beforeunload', this.handleBeforeUnload);
    
    // Override browser back/forward navigation
    window.addEventListener('popstate', this.handleNavigation);
    
    // Intercept programmatic navigation
    this.interceptRouterNavigation();
  }

  /**
   * Handle browser refresh/close attempts
   */
  handleBeforeUnload(event) {
    if (this.hasActiveTimedGames()) {
      const message = 'You have an active timed game. Leaving will require resignation. Are you sure?';
      event.preventDefault();
      event.returnValue = message;
      return message;
    }
  }

  /**
   * Handle browser navigation (back/forward buttons)
   */
  async handleNavigation(event) {
    if (this.hasActiveTimedGames() && !this.navigationBlocked) {
      event.preventDefault();
      const shouldResign = await this.showResignationDialog();
      
      if (shouldResign) {
        await this.resignActiveGames();
        this.allowNavigation();
      } else {
        // Push current state back to prevent navigation
        history.pushState(null, null, window.location.href);
      }
    }
  }

  /**
   * Intercept router navigation attempts
   */
  interceptRouterNavigation() {
    // Store original router navigate function if it exists
    if (window.router && window.router.navigate) {
      const originalNavigate = window.router.navigate.bind(window.router);
      
      window.router.navigate = async (path, ...args) => {
        if (await this.shouldBlockNavigation(path)) {
          const shouldResign = await this.showResignationDialog();
          
          if (shouldResign) {
            await this.resignActiveGames();
            this.allowNavigation();
            return originalNavigate(path, ...args);
          }
          return false; // Block navigation
        }
        
        return originalNavigate(path, ...args);
      };
    }

    // Intercept direct link clicks
    document.addEventListener('click', async (event) => {
      const link = event.target.closest('a[href]');
      if (link && await this.shouldBlockNavigation(link.href)) {
        event.preventDefault();
        
        const shouldResign = await this.showResignationDialog();
        if (shouldResign) {
          await this.resignActiveGames();
          this.allowNavigation();
          window.location.href = link.href;
        }
      }
    });
  }

  /**
   * Check if navigation should be blocked
   */
  async shouldBlockNavigation(targetPath) {
    if (!this.hasActiveTimedGames()) return false;
    
    // Don't block navigation within the same game
    const currentPath = window.location.pathname;
    const isGamePage = currentPath.includes('/play/') || currentPath.includes('/game/');
    const isTargetGamePage = targetPath.includes('/play/') || targetPath.includes('/game/');
    
    if (isGamePage && isTargetGamePage) {
      // Extract game IDs to see if it's the same game
      const currentGameId = this.extractGameIdFromUrl(currentPath);
      const targetGameId = this.extractGameIdFromUrl(targetPath);
      
      if (currentGameId === targetGameId) return false;
    }
    
    // Block navigation away from active games
    return true;
  }

  /**
   * Extract game ID from URL
   */
  extractGameIdFromUrl(url) {
    const match = url.match(/game[=/](\d+)/);
    return match ? match[1] : null;
  }

  /**
   * Check for active games and update internal state
   */
  async checkActiveGames() {
    try {
      const result = await this.api.checkActiveGameConstraints();
      if (result.ok) {
        this.activeGames = result.data.games || [];
        
        if (result.data.hasActiveGames) {
          console.log(`🕐 Found ${this.activeGames.length} active game(s) requiring resignation`);
        }
        
        return {
          hasActiveGames: result.data.hasActiveGames,
          games: this.activeGames
        };
      } else {
        console.error('Failed to check active games:', result.message);
        return { hasActiveGames: false, games: [] };
      }
    } catch (error) {
      console.error('Error checking active games:', error);
      return { hasActiveGames: false, games: [] };
    }
  }

  /**
   * Check if user has active timed games
   */
  hasActiveTimedGames() {
    return this.activeGames && this.activeGames.length > 0;
  }

  /**
   * Show professional resignation confirmation dialog
   */
  async showResignationDialog() {
    return new Promise((resolve) => {
      const modal = this.createResignationModal();
      document.body.appendChild(modal);
      
      // Focus on cancel button for safety
      const cancelBtn = modal.querySelector('.resign-cancel-btn');
      if (cancelBtn) cancelBtn.focus();
      
      // Handle button clicks
      modal.addEventListener('click', (event) => {
        if (event.target.classList.contains('resign-confirm-btn')) {
          resolve(true);
          this.closeModal(modal);
        } else if (event.target.classList.contains('resign-cancel-btn') || 
                   event.target.classList.contains('modal-overlay')) {
          resolve(false);
          this.closeModal(modal);
        }
      });
      
      // Handle escape key
      const handleEscape = (event) => {
        if (event.key === 'Escape') {
          resolve(false);
          this.closeModal(modal);
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);
    });
  }

  /**
   * Create professional resignation confirmation modal
   */
  createResignationModal() {
    const modal = document.createElement('div');
    modal.className = 'game-guard-modal-overlay';
    modal.innerHTML = `
      <div class="game-guard-modal">
        <div class="modal-header">
          <h3 class="modal-title">
            <span class="warning-icon">⚠️</span>
            Active Game Warning
          </h3>
        </div>
        
        <div class="modal-body">
          <p class="warning-message">
            You have an active timed game in progress. Leaving now will automatically resign the game.
          </p>
          
          <div class="active-games-list">
            ${this.activeGames.map(game => `
              <div class="active-game-item">
                <div class="game-players">
                  <strong>${game.white_player_username}</strong> vs <strong>${game.black_player_username}</strong>
                </div>
                <div class="game-time">Time Control: ${game.time_control || 'N/A'} minutes</div>
              </div>
            `).join('')}
          </div>
          
          <p class="confirmation-text">
            Do you want to resign and leave the game?
          </p>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary resign-cancel-btn">
            <span>🎯</span> Stay in Game
          </button>
          <button class="btn btn-danger resign-confirm-btn">
            <span>🏳️</span> Resign & Leave
          </button>
        </div>
      </div>
    `;
    
    // Add styles
    this.addModalStyles();
    
    return modal;
  }

  /**
   * Add modal styles to document
   */
  addModalStyles() {
    if (document.getElementById('game-guard-modal-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'game-guard-modal-styles';
    styles.textContent = `
      .game-guard-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease-out;
      }
      
      .game-guard-modal {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        max-width: 500px;
        width: 90%;
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideUp 0.3s ease-out;
      }
      
      .modal-header {
        padding: 24px 24px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      .modal-title {
        margin: 0;
        color: #ff6b6b;
        font-size: 1.25rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 12px;
      }
      
      .warning-icon {
        font-size: 1.5rem;
      }
      
      .modal-body {
        padding: 24px;
      }
      
      .warning-message {
        color: #e0e0e0;
        margin: 0 0 16px;
        line-height: 1.5;
      }
      
      .active-games-list {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      .active-game-item {
        padding: 8px 0;
      }
      
      .active-game-item:not(:last-child) {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 8px;
        padding-bottom: 16px;
      }
      
      .game-players {
        color: #4fc3f7;
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .game-time {
        color: #b0b0b0;
        font-size: 0.875rem;
      }
      
      .confirmation-text {
        color: #ffa726;
        font-weight: 500;
        margin: 16px 0 0;
        text-align: center;
      }
      
      .modal-footer {
        padding: 0 24px 24px;
        display: flex;
        gap: 12px;
        justify-content: flex-end;
      }
      
      .resign-cancel-btn {
        background: rgba(76, 175, 80, 0.2);
        color: #4caf50;
        border: 1px solid #4caf50;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .resign-cancel-btn:hover {
        background: rgba(76, 175, 80, 0.3);
        transform: translateY(-1px);
      }
      
      .resign-confirm-btn {
        background: rgba(244, 67, 54, 0.2);
        color: #f44336;
        border: 1px solid #f44336;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .resign-confirm-btn:hover {
        background: rgba(244, 67, 54, 0.3);
        transform: translateY(-1px);
      }
      
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      
      @keyframes slideUp {
        from { 
          opacity: 0; 
          transform: translateY(30px) scale(0.95); 
        }
        to { 
          opacity: 1; 
          transform: translateY(0) scale(1); 
        }
      }
      
      @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
      }
    `;
    
    document.head.appendChild(styles);
  }

  /**
   * Close modal with animation
   */
  closeModal(modal) {
    modal.style.animation = 'fadeOut 0.2s ease-out forwards';
    modal.addEventListener('animationend', () => {
      if (modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
    });
  }

  /**
   * Resign from all active games
   */
  async resignActiveGames() {
    const resignPromises = this.activeGames.map(async (game) => {
      try {
        const result = await this.api.resignGame(game.id);
        if (result.ok) {
          console.log(`✓ Resigned from game ${game.id}`);
        } else {
          console.error(`✗ Failed to resign from game ${game.id}:`, result.message);
        }
      } catch (error) {
        console.error(`✗ Failed to resign from game ${game.id}:`, error);
      }
    });
    
    await Promise.all(resignPromises);
    this.activeGames = [];
  }

  /**
   * Allow navigation by temporarily disabling guards
   */
  allowNavigation() {
    this.navigationBlocked = true;
    this.activeGames = [];
    
    // Re-enable guards after a short delay
    setTimeout(() => {
      this.navigationBlocked = false;
    }, 1000);
  }

  /**
   * Set current game ID to avoid blocking navigation within the same game
   */
  setCurrentGame(gameId) {
    this.currentGameId = gameId;
  }

  /**
   * Check for active games and redirect to game if needed
   */
  async checkAndRedirectToActiveGame() {
    const result = await this.checkActiveGames();
    
    if (result.hasActiveGames && result.games.length === 1) {
      const game = result.games[0];
      const currentPath = window.location.pathname;
      
      // If not already on the game page, redirect
      if (!currentPath.includes('/play/') && !currentPath.includes('/game/')) {
        console.log(`🔄 Redirecting to active game ${game.id}`);
        window.location.href = `/play/?game=${game.id}`;
        return true;
      }
      
      // Check if on wrong game page
      const currentGameId = this.extractGameIdFromUrl(currentPath);
      if (currentGameId && currentGameId !== game.id.toString()) {
        console.log(`🔄 Redirecting from game ${currentGameId} to active game ${game.id}`);
        window.location.href = `/play/?game=${game.id}`;
        return true;
      }
    }
    
    return false;
  }

  /**
   * Clean up the guard system
   */
  destroy() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    window.removeEventListener('popstate', this.handleNavigation);
    
    // Remove modal styles
    const styles = document.getElementById('game-guard-modal-styles');
    if (styles) styles.remove();
    
    this.isInitialized = false;
    console.log('🛡️ Game Session Guard destroyed');
  }
}

// Export for use in other modules
window.GameSessionGuard = GameSessionGuard;

// Auto-initialize if API is available
if (window.api && typeof window.api === 'object') {
  window.gameSessionGuard = new GameSessionGuard(window.api);
}