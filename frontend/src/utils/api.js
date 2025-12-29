/**
 * Chess Platform - Enhanced API Communication
 * Handles all backend communication with proper error handling and token management
 */

class ChessAPI {
  constructor() {
    // Auto-detect the appropriate base URL
    const currentHost = window.location.hostname;
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
      this.baseURL = 'http://localhost:8000/api';
    } else {
      // Use the current host (works for mobile access via IP)
      this.baseURL = `http://${currentHost}:8000/api`;
    }
    this.accessToken = localStorage.getItem('access');
    this.refreshToken = localStorage.getItem('refresh');
    this.isRefreshing = false;
    this.failedQueue = [];
  }

  /**
   * Set authentication tokens
   * @param {string} access - Access token
   * @param {string} refresh - Refresh token
   */
  setTokens(access, refresh) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    
    // Update router auth status
    if (window.router) {
      window.router.setAuth(true);
    }
  }

  /**
   * Clear authentication tokens
   */
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    
    // Update router auth status
    if (window.router) {
      window.router.setAuth(false);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.accessToken;
  }

  /**
   * Make API request with automatic token refresh
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // Add authentication header
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    // Prepare request options
    const requestOptions = {
      ...options,
      headers
    };

    try {
      let response = await fetch(url, requestOptions);

      // Handle 401 - Unauthorized (token expired)
      if (response.status === 401 && this.refreshToken && !this.isRefreshing) {
        const refreshed = await this.refreshAccessToken();
        
        if (refreshed) {
          // Retry original request with new token
          headers['Authorization'] = `Bearer ${this.accessToken}`;
          response = await fetch(url, { ...requestOptions, headers });
        } else {
          // Refresh failed, redirect to login
          this.clearTokens();
          if (window.router) {
            window.router.navigate('/login');
          }
          throw new Error('Authentication expired');
        }
      }

      return this.handleResponse(response);
      
    } catch (error) {
      console.error('API Request failed:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle API response
   * @param {Response} response - Fetch response
   */
  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    let data;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      throw {
        status: response.status,
        statusText: response.statusText,
        data: data
      };
    }

    return {
      ok: true,
      status: response.status,
      data: data
    };
  }

  /**
   * Handle API errors
   * @param {Error|Object} error - Error object
   */
  handleError(error) {
    if (error.status) {
      // HTTP error
      return {
        ok: false,
        status: error.status,
        message: this.getErrorMessage(error),
        data: error.data
      };
    } else {
      // Network or other error
      return {
        ok: false,
        status: 0,
        message: error.message || 'Network error occurred',
        data: null
      };
    }
  }

  /**
   * Get user-friendly error message
   * @param {Object} error - Error object
   */
  getErrorMessage(error) {
    const statusMessages = {
      400: 'Invalid request data',
      401: 'Authentication required',
      403: 'Access denied',
      404: 'Resource not found',
      409: 'Resource conflict',
      422: 'Validation error',
      429: 'Too many requests',
      500: 'Server error occurred',
      502: 'Server temporarily unavailable',
      503: 'Service temporarily unavailable'
    };

    if (error.data && typeof error.data === 'object') {
      // Try to extract specific error message
      if (error.data.detail) return error.data.detail;
      if (error.data.message) return error.data.message;
      if (error.data.error) return error.data.error;
      
      // Handle field validation errors
      const fields = Object.keys(error.data);
      if (fields.length > 0) {
        const field = fields[0];
        const messages = error.data[field];
        if (Array.isArray(messages)) {
          return `${field}: ${messages[0]}`;
        }
        return `${field}: ${messages}`;
      }
    }

    return statusMessages[error.status] || 'An error occurred';
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken() {
    if (!this.refreshToken || this.isRefreshing) {
      return false;
    }

    this.isRefreshing = true;

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh: this.refreshToken
        })
      });

      if (response.ok) {
        const data = await response.json();
        this.setTokens(data.access, this.refreshToken);
        this.processQueue(null, data.access);
        return true;
      } else {
        this.processQueue(new Error('Token refresh failed'), null);
        this.clearTokens();
        return false;
      }
    } catch (error) {
      this.processQueue(error, null);
      this.clearTokens();
      return false;
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Process queued requests after token refresh
   */
  processQueue(error, token) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });
    
    this.failedQueue = [];
  }

  // =================================
  // Authentication API Methods
  // =================================

  /**
   * Register new user
   * @param {Object} userData - User registration data
   */
  async register(userData) {
    return this.request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  /**
   * Login user
   * @param {string} username - Username
   * @param {string} password - Password
   */
  async login(username, password) {
    const response = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });

    if (response.ok && response.data.access) {
      this.setTokens(response.data.access, response.data.refresh);
    }

    return response;
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      if (this.refreshToken) {
        await this.request('/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh: this.refreshToken })
        });
      }
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.clearTokens();
      if (window.router) {
        window.router.navigate('/login');
      }
    }
  }

  /**
   * Get current user profile
   */
  async getUserProfile() {
    // Add cache-busting timestamp to ensure fresh data
    const timestamp = new Date().getTime();
    return this.request(`/auth/profile/?t=${timestamp}`);
  }

  /**
   * Get available skill levels for registration
   */
  async getSkillLevels() {
    return this.request('/auth/skill-levels/');
  }

  /**
   * Send forgot password request
   * @param {string} email - User's email address
   */
  async forgotPassword(email) {
    return this.request('/auth/forgot-password/', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  // =================================
  // User Settings API Methods
  // =================================

  /**
   * Get current user settings
   */
  async getUserSettings() {
    return this.request('/auth/settings/');
  }

  /**
   * Update user settings (partial update)
   * @param {Object} settings - Settings object with fields to update
   */
  async updateUserSettings(settings) {
    return this.request('/auth/settings/update/', {
      method: 'PATCH',
      body: JSON.stringify(settings)
    });
  }

  /**
   * Reset settings to default values
   */
  async resetSettingsToDefault() {
    return this.request('/auth/settings/reset/', {
      method: 'POST'
    });
  }

  /**
   * Get available themes and piece sets
   */
  async getAvailableThemes() {
    return this.request('/auth/settings/themes/');
  }

  // =================================
  // Achievement API Methods
  // =================================

  /**
   * Get all achievements for current user
   */
  async getUserAchievements() {
    return this.request('/auth/achievements/');
  }

  /**
   * Get public achievements for a specific user
   * @param {number} userId - User ID
   */
  async getPublicAchievements(userId) {
    return this.request(`/auth/achievements/${userId}/`);
  }

  /**
   * Check and unlock newly earned achievements
   */
  async checkAchievements() {
    return this.request('/auth/achievements/check/', {
      method: 'POST'
    });
  }

  /**
   * Get progress toward locked achievements
   */
  async getAchievementProgress() {
    return this.request('/auth/achievements/progress/');
  }

  // =================================
  // Game API Methods
  // =================================

  /**
   * Get game timer status
   */
  async getGameTimer(gameId) {
    return this.request(`/games/${gameId}/timer/`);
  }

  /**
   * Get all games
   */
  async getGames() {
    return this.request('/games/');
  }

  /**
   * Get games for a specific user
   * @param {number} userId - User ID (required)
   * @param {number} limit - Number of games to retrieve (default: 10)
   */
  async getUserGames(userId, limit = 10) {
    if (!userId) {
      throw new Error('userId is required');
    }
    return this.request(`/games/?user_id=${userId}&limit=${limit}`);
  }

  /**
   * Create new game
   */
  async createGame() {
    return this.request('/games/create/', {
      method: 'POST'
    });
  }

  /**
   * Join game
   * @param {number} gameId - Game ID
   */
  async joinGame(gameId) {
    return this.request(`/games/${gameId}/join/`, {
      method: 'POST'
    });
  }

  /**
   * Get game details
   * @param {number} gameId - Game ID
   */
  async getGameDetail(gameId) {
    return this.request(`/games/${gameId}/`);
  }

  /**
   * Make a move
   * @param {number} gameId - Game ID
   * @param {string} from - From square (e.g., 'e2')
   * @param {string} to - To square (e.g., 'e4')
   * @param {string} promotion - Promotion piece (optional)
   */
  async makeMove(gameId, from, to, promotion = null) {
    const payload = {
      from_square: from,
      to_square: to
    };

    if (promotion) {
      payload.promotion = promotion;
    }

    return this.request(`/games/${gameId}/move/`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Make a computer move
   * @param {number} gameId - Game ID
   * @param {string} difficulty - AI difficulty ('easy', 'medium', 'hard', 'expert')
   */
  async makeComputerMove(gameId, difficulty = 'medium') {
    const payload = {
      difficulty: difficulty
    };

    return this.request(`/games/${gameId}/computer-move/`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Create a game against the computer
   * @param {string} playerColor - Player's color ('white' or 'black')
   * @param {string} difficulty - AI difficulty ('easy', 'medium', 'hard', 'expert')
   */
  async createComputerGame(playerColor = 'white', difficulty = 'medium') {
    const payload = {
      player_color: playerColor,
      difficulty: difficulty
    };

    return this.request('/games/create-computer/', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  /**
   * Get legal moves for a piece at a specific square
   * @param {number} gameId - Game ID  
   * @param {string} fromSquare - Square to get legal moves from (e.g., 'e2')
   */
  async getLegalMoves(gameId, fromSquare) {
    return this.request(`/games/${gameId}/legal-moves/?from_square=${fromSquare}`, {
      method: 'GET'
    });
  }

  // =================================
  // Puzzle API Methods
  // =================================

  /**
   * Get a random puzzle for the user
   * @param {Object} filters - Optional filters (category, difficulty, theme)
   */
  async getRandomPuzzle(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.difficulty) params.append('difficulty', filters.difficulty);
    if (filters.theme) params.append('theme', filters.theme);
    if (filters.rating_range) params.append('rating_range', filters.rating_range);
    
    const queryString = params.toString();
    return this.request(`/games/puzzles/random/${queryString ? '?' + queryString : ''}`);
  }

  /**
   * Get a specific puzzle by ID
   * @param {number} puzzleId - Puzzle ID
   */
  async getPuzzle(puzzleId) {
    return this.request(`/games/puzzles/${puzzleId}/`);
  }

  /**
   * Validate a move in a puzzle
   * @param {number} puzzleId - Puzzle ID
   * @param {string} move - Move in UCI format
   * @param {string} currentPosition - Current FEN position
   * @param {number} moveIndex - Index in solution sequence
   */
  async validatePuzzleMove(puzzleId, move, currentPosition, moveIndex = 0) {
    return this.request(`/games/puzzles/${puzzleId}/validate/`, {
      method: 'POST',
      body: JSON.stringify({
        move: move,
        current_position: currentPosition,
        move_index: moveIndex
      })
    });
  }

  /**
   * Complete a puzzle (record attempt)
   * @param {number} puzzleId - Puzzle ID
   * @param {boolean} solved - Whether puzzle was solved
   * @param {number} timeSpent - Time spent in seconds
   * @param {Array} movesMade - List of moves attempted
   * @param {number} hintsUsed - Number of hints used
   */
  async completePuzzle(puzzleId, solved, timeSpent, movesMade = [], hintsUsed = 0) {
    return this.request(`/games/puzzles/${puzzleId}/complete/`, {
      method: 'POST',
      body: JSON.stringify({
        solved: solved,
        time_spent: timeSpent,
        moves_made: movesMade,
        hints_used: hintsUsed
      })
    });
  }

  /**
   * Get a hint for a puzzle
   * @param {number} puzzleId - Puzzle ID
   * @param {number} moveIndex - Current move index
   */
  async getPuzzleHint(puzzleId, moveIndex = 0) {
    return this.request(`/games/puzzles/${puzzleId}/hint/?move_index=${moveIndex}`);
  }

  /**
   * Get the full solution for a puzzle
   * @param {number} puzzleId - Puzzle ID
   */
  async getPuzzleSolution(puzzleId) {
    return this.request(`/games/puzzles/${puzzleId}/solution/`);
  }

  /**
   * Get user's puzzle statistics
   */
  async getPuzzleStats() {
    return this.request('/games/puzzles/stats/');
  }

  // =================================
  // Game Session Guard Methods
  // =================================

  /**
   * Check for active games that prevent navigation
   * Used by GameSessionGuard to determine if resignation is required
   */
  async checkActiveGameConstraints() {
    return this.request('/games/active-constraints/');
  }

  /**
   * Resign from a specific game
   * @param {number} gameId - Game ID to resign from
   */
  async resignGame(gameId) {
    return this.request(`/games/${gameId}/resign/`, {
      method: 'POST'
    });
  }

  // =================================
  // Profile API Methods
  // =================================

  /**
   * Update user profile
   * @param {Object} profileData - Profile data
   */
  async updateProfile(profileData) {
    return this.request('/profiles/update/', {
      method: 'PATCH',
      body: JSON.stringify(profileData)
    });
  }

  /**
   * Upload user avatar
   * @param {File} file - Avatar image file
   */
  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);

    // Don't set Content-Type header - let browser handle it for FormData
    const headers = {};
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const url = `${this.baseURL}/auth/avatar/upload/`;
    console.log('Uploading avatar to:', url);
    console.log('File details:', { name: file.name, type: file.type, size: file.size });

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData
      });

      console.log('Upload response status:', response.status);
      console.log('Upload response headers:', response.headers);

      return this.handleResponse(response);
    } catch (error) {
      console.error('Upload fetch error:', error);
      throw error;
    }
  }

  /**
   * Delete user avatar
   */
  async deleteAvatar() {
    return this.request('/auth/avatar/delete/', {
      method: 'DELETE'
    });
  }

  /**
   * Get user statistics
   */
  async getUserStats() {
    return this.request('/profiles/stats/');
  }

  // =================================
  // Utility Methods
  // =================================

  /**
   * Show API error to user
   * @param {Object} error - Error object from API response
   */
  showError(error) {
    const message = error.message || 'An error occurred';
    
    // Create or update error toast
    this.showToast(message, 'error');
  }

  /**
   * Show success message to user
   * @param {string} message - Success message
   */
  showSuccess(message) {
    this.showToast(message, 'success');
  }

  /**
   * Show toast notification
   * @param {string} message - Message text
   * @param {string} type - Toast type ('success', 'error', 'info')
   */
  showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
      existingToast.remove();
    }

    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type} slide-up`;
    toast.innerHTML = `
      <div class="toast-content">
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;

    // Add styles if not already present
    if (!document.querySelector('#toast-styles')) {
      const style = document.createElement('style');
      style.id = 'toast-styles';
      style.textContent = `
        .toast-notification {
          position: fixed;
          top: var(--space-lg);
          right: var(--space-lg);
          min-width: 300px;
          max-width: 500px;
          padding: var(--space-md);
          border-radius: var(--radius-md);
          box-shadow: var(--shadow-lg);
          z-index: 1000;
          backdrop-filter: blur(16px);
        }
        
        .toast-success {
          background: rgba(34, 197, 94, 0.9);
          border: 1px solid var(--color-success);
          color: white;
        }
        
        .toast-error {
          background: rgba(239, 68, 68, 0.9);
          border: 1px solid var(--color-error);
          color: white;
        }
        
        .toast-info {
          background: var(--glass-bg);
          border: 1px solid var(--glass-border);
          color: var(--color-text-primary);
        }
        
        .toast-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--space-md);
        }
        
        .toast-message {
          flex: 1;
          font-size: var(--font-size-sm);
        }
        
        .toast-close {
          background: none;
          border: none;
          color: inherit;
          font-size: var(--font-size-lg);
          cursor: pointer;
          padding: 0;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm);
          transition: background var(--transition-fast);
        }
        
        .toast-close:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        @media (max-width: 480px) {
          .toast-notification {
            left: var(--space-md);
            right: var(--space-md);
            min-width: auto;
          }
        }
      `;
      document.head.appendChild(style);
    }

    // Add to DOM
    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 5000);
  }

  /**
   * Format API error for display
   * @param {Object} error - Error object
   */
  formatError(error) {
    if (!error) return 'Unknown error occurred';
    
    if (typeof error === 'string') return error;
    
    if (error.message) return error.message;
    
    if (error.data && typeof error.data === 'object') {
      // Handle validation errors
      const fields = Object.keys(error.data);
      if (fields.length > 0) {
        const errors = [];
        fields.forEach(field => {
          const messages = error.data[field];
          if (Array.isArray(messages)) {
            errors.push(`${field}: ${messages.join(', ')}`);
          } else {
            errors.push(`${field}: ${messages}`);
          }
        });
        return errors.join('; ');
      }
    }
    
    return 'An error occurred';
  }
}

// Create global API instance
const api = new ChessAPI();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ChessAPI;
}

// Make available globally
window.api = api;