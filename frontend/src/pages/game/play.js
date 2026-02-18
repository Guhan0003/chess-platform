/**
 * Chess Game Page Controller
 * Professional chess platform game interface with real-time WebSocket support
 */

/**
 * Chess Game Controller v2.0 - 401 Error Fixes Applied
 * Updated: October 7, 2025
 */

class ChessGameController {
  constructor() {
    // Game state
    this.gameData = null;
    this.selectedSquare = null;
    this.possibleMoves = [];
    this.gameId = null;
    this.currentUser = null;
    this.api = null;
    
    // WebSocket management
    this.webSocketManager = null;
    this.wsConnected = false;
    this.wsReconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    
    // Timer management
    this.timerInterval = null;
    this.currentTurn = 'white';
    this.gameTimerData = null;
    this.lastTimerUpdate = null;
    this.useWebSocketTimer = false;
    
    // Computer move state
    this.computerMoveInProgress = false;
    this.computerMoveRetryCount = 0;
    this.MAX_COMPUTER_MOVE_RETRIES = 3;
    this.lastComputerMoveAttempt = 0; // Timestamp to prevent rapid duplicate calls
    
    // Move navigation state
    this.viewingMoveIndex = -1; // -1 means viewing current position
    this.isViewingHistory = false;
    
    // Draw offer state
    this.drawOfferPending = false;
    this.drawOfferSentByMe = false;
    this.drawOfferShownForId = null; // Track which draw offer was already shown
    
    // Captured pieces tracking
    this.capturedPieces = { white: [], black: [] };
    
    // Theme settings
    this.boardTheme = 'classic';
    this.pieceSet = 'unicode';
    this.loadThemeSettings();
    
    // Bind methods
    this.handleSquareClick = this.handleSquareClick.bind(this);
    this.updateTimerDisplay = this.updateTimerDisplay.bind(this);
    this.handleWebSocketMove = this.handleWebSocketMove.bind(this);
    this.handleWebSocketTimer = this.handleWebSocketTimer.bind(this);
    this.handleWebSocketConnection = this.handleWebSocketConnection.bind(this);
  }
  
  /**
   * Load theme settings from localStorage
   */
  loadThemeSettings() {
    this.boardTheme = localStorage.getItem('chess_board_theme') || 'classic';
    this.pieceSet = localStorage.getItem('chess_piece_set') || 'unicode';
    
    // Apply board theme CSS variables immediately
    this.applyBoardTheme();
  }
  
  /**
   * Apply board theme CSS variables
   */
  applyBoardTheme() {
    const themes = {
      'classic': { light: '#f0d9b5', dark: '#769656' },
      'blue': { light: '#dee3e6', dark: '#5d8aa8' },
      'brown': { light: '#f0dab5', dark: '#b58863' },
      'gray': { light: '#ffffff', dark: '#9e9e9e' },
      'purple': { light: '#e8e0f0', dark: '#7c4daf' },
      'tournament': { light: '#eeeed2', dark: '#769656' },
      'wood': { light: '#deb887', dark: '#8b4513' },
      'marble': { light: '#f5f5f5', dark: '#505050' }
    };
    
    const theme = themes[this.boardTheme] || themes['classic'];
    const root = document.documentElement;
    root.style.setProperty('--board-light-color', theme.light);
    root.style.setProperty('--board-dark-color', theme.dark);
  }
  
  /**
   * Get the piece set configuration
   */
  getPieceSetConfig() {
    const pieceSets = {
      'unicode': { folder: null },
      'classic': { folder: 'classic' },
      'modern': { folder: 'modern' },
      'staunton': { folder: 'staunton' },
      'neo': { folder: 'neo' },
      'alpha': { folder: 'alpha' },
      'cburnett': { folder: 'cburnett' }
    };
    return pieceSets[this.pieceSet] || pieceSets['unicode'];
  }

  /**
   * Initialize the game controller
   */
  async initialize() {
    try {
      console.log('Initializing chess game controller...');
      
      // Initialize API
      this.api = new ChessAPI();
      window.api = this.api;
      
      // Setup routes and navigation
      this.setupRoutes();
      this.setupNavigation();
      
      // Authenticate user
      await this.ensureAuthentication();
      
      // Get game ID and load data
      this.gameId = this.getGameIdFromUrl();
      if (!this.gameId) {
        this.api.showError('Invalid game URL');
        this.navigateToRoute('/lobby');
        return;
      }
      
      // Load user and game data
      await this.loadCurrentUser();
      await this.loadGameData();
      
      // Initialize WebSocket connection (skip for bot games)
      if (!this.isComputerGame()) {
        console.log('Human vs Human game detected - initializing WebSocket...');
        await this.initializeWebSocket();
      } else {
        console.log('Bot game detected - skipping WebSocket initialization');
        this.wsConnected = false;
        this.useWebSocketTimer = false;
      }
      
      // Setup UI
      this.setupEventListeners();
      this.setupPeriodicUpdates();
      
      // Show connection mode info
      let mode;
      if (this.isComputerGame()) {
        mode = '🤖 Bot game (WebSocket disabled)';
      } else {
        mode = this.wsConnected ? '🚀 WebSocket (instant)' : '⚡ Fast polling (1.5s)';
      }
      console.log(`🎯 Game ready - Move updates: ${mode}`);
    } catch (error) {
      console.error('Failed to initialize game:', error);
      this.api.showError('Failed to load game');
    }
  }

  // ===========================================
  // WEBSOCKET MANAGEMENT
  // ===========================================

  async initializeWebSocket() {
    // WebSocket enabled for fast 1-2 second move updates
    
    try {
      // Check if WebSocket utilities are available
      if (typeof WebSocketManager === 'undefined') {
        console.log('WebSocket utilities not available - using polling mode');
        this.useWebSocketTimer = false;
        return;
      }
      
      this.webSocketManager = new WebSocketManager();
      
      // Get access token for WebSocket authentication
      const accessToken = localStorage.getItem('access');
      if (!accessToken) {
        console.log('No access token available - using polling mode');
        this.useWebSocketTimer = false;
        return;
      }
      
      // Connect to game WebSocket
      const gameWs = await this.webSocketManager.connectToGame(this.gameId, accessToken);
      
      // Setup event handlers
      gameWs.on('move_made', this.handleWebSocketMove);
      gameWs.on('timer_update', this.handleWebSocketTimer);
      gameWs.on('connected', () => this.handleWebSocketConnection(true));
      gameWs.on('disconnected', () => this.handleWebSocketConnection(false));
      gameWs.on('reconnectionFailed', () => {
        console.log('WebSocket reconnection failed - switching to polling permanently');
        this.webSocketManager = null;
        this.updateConnectionStatus(false);
      });
      gameWs.on('pollingMode', () => {
        console.log('Switching to polling mode');
        this.updateConnectionStatus(false);
      });
      gameWs.on('error', (error) => {
        // WebSocket connection failed - using polling fallback
        console.log('WebSocket error - falling back to polling');
        this.updateConnectionStatus(false);
      });
      
      this.updateConnectionStatus(true);
    } catch (error) {
      // WebSocket unavailable - using optimized polling mode
      console.log('WebSocket connection failed - using polling mode');
      this.useWebSocketTimer = false;
      this.webSocketManager = null;
      this.updateConnectionStatus(false);
    }
  }

  handleWebSocketMove(data) {
    console.log('📡 Received WebSocket move data:', data);
    
    if (data.type === 'move_made' && data.game_state) {
      console.log('✅ Processing move_made message');
      console.log('Previous moves count:', this.gameData?.moves?.length || 0);
      console.log('New moves count:', data.game_state.moves?.length || 0);
      
      // Update game state from WebSocket
      this.gameData = {
        ...this.gameData,
        ...data.game_state,
        moves: data.game_state.moves || this.gameData.moves
      };
      
      // Update display immediately
      this.updateGameDisplay();
      this.renderBoard();
      this.updateMoveHistory();
      this.updateGameStatus();
      
      console.log('🎯 Board and UI updated from WebSocket');
      
      // Show move notification if it's opponent's move
      if (data.move && !this.isPlayerMove(data.move)) {
        this.api.showSuccess(`Opponent moved: ${data.move.notation}`, 3000);
        console.log('👥 Opponent move notification shown');
      }
      
      // Handle computer turn if needed
      if (this.isComputerTurn()) {
        console.log('🤖 Triggering computer turn');
        this.handleComputerTurn();
      }
      
      // Handle game over
      if (data.game_state.status && ['finished', 'checkmate', 'stalemate'].includes(data.game_state.status)) {
        this.handleGameOverStatus(data);
        this.stopTimerUpdates();
      }
    } else {
      console.warn('❌ Invalid move_made data:', data);
    }
  }

  handleWebSocketTimer(data) {
    if (data.type === 'timer_update' || data.type === 'timer_tick') {
      this.useWebSocketTimer = true;
      
      // Update timer display with real-time data
      const whiteTimer = document.getElementById('whiteTimer');
      const blackTimer = document.getElementById('blackTimer');
      
      const timerData = data.data || data;
      
      if (whiteTimer && timerData.white_time !== undefined) {
        whiteTimer.textContent = this.formatTime(timerData.white_time);
      }
      if (blackTimer && timerData.black_time !== undefined) {
        blackTimer.textContent = this.formatTime(timerData.black_time);
      }
      
      // Update current turn
      if (timerData.current_turn) {
        this.currentTurn = timerData.current_turn;
        this.updateTimerVisuals(timerData.white_time, timerData.black_time);
      }
      
      // Handle timeout
      if (timerData.white_time <= 0 || timerData.black_time <= 0) {
        this.handleTimeout(timerData.white_time <= 0 ? 'white' : 'black');
      }
    }
  }

  handleWebSocketConnection(connected) {
    this.updateConnectionStatus(connected);
    
    if (connected) {
      this.wsReconnectAttempts = 0;
      console.log('WebSocket connection established successfully');
    } else if (this.wsReconnectAttempts < this.maxReconnectAttempts && this.webSocketManager) {
      console.log('WebSocket disconnected - attempting reconnection...');
      this.attemptReconnection();
    } else {
      console.log('WebSocket permanently disconnected - polling mode active');
    }
  }

  updateConnectionStatus(connected) {
    const wasConnected = this.wsConnected;
    this.wsConnected = connected;
    
    if (connected && !wasConnected) {
      console.log('🚀 WebSocket connected - Real-time updates enabled');
    } else if (!connected && wasConnected) {
      console.log('⚡ WebSocket disconnected - Polling mode active (1.5s intervals)');
    }
    
    // Enable/disable real-time features
    if (!connected && this.useWebSocketTimer) {
      // Fall back to polling timer if WebSocket disconnects
      this.useWebSocketTimer = false;
      this.startTimerUpdates();
    }
  }

  async attemptReconnection() {
    if (this.wsReconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max WebSocket reconnection attempts reached - switching to polling mode');
      this.webSocketManager = null;
      this.updateConnectionStatus(false);
      return;
    }
    
    this.wsReconnectAttempts++;
    console.log(`Attempting WebSocket reconnection (${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(async () => {
      try {
        if (this.webSocketManager) {
          const gameWs = this.webSocketManager.getGameConnection(this.gameId);
          if (gameWs) {
            await gameWs.connect();
          }
        }
      } catch (error) {
        console.log(`WebSocket reconnection attempt ${this.wsReconnectAttempts} failed`);
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnection();
        } else {
          console.log('All WebSocket reconnection attempts failed - using polling mode');
          this.webSocketManager = null;
          this.updateConnectionStatus(false);
        }
      }
    }, 2000 * this.wsReconnectAttempts); // Exponential backoff
  }

  isPlayerMove(move) {
    if (!move || !this.currentUser) return false;
    
    const isWhitePlayer = this.currentUser.id === this.gameData.white_player;
    const isWhiteMove = move.color === 'white';
    
    return (isWhitePlayer && isWhiteMove) || (!isWhitePlayer && !isWhiteMove);
  }

  /**
   * Check if the current user is a player in this game (not a spectator)
   * @returns {boolean} True if user is white or black player
   */
  isCurrentUserPlayer() {
    if (!this.currentUser || !this.gameData) return false;
    
    const userId = this.currentUser.id;
    return userId === this.gameData.white_player || userId === this.gameData.black_player;
  }

  /**
   * Check if the game is completed (no longer active)
   * @returns {boolean} True if game has ended
   */
  isGameCompleted() {
    if (!this.gameData) return false;
    
    const completedStatuses = ['finished', 'checkmate', 'stalemate', 'resigned', 'timeout', 'draw', 'abandoned'];
    return completedStatuses.includes(this.gameData.status);
  }

  /**
   * Update the visibility of game controls based on game state and user role
   * - Player in active game: Show all controls (Offer Draw, Resign, Flip Board, Analysis)
   * - Player in completed game: Show only Flip Board and Analysis
   * - Spectator (any state): Show only Flip Board and Analysis
   */
  updateGameControlsVisibility() {
    const offerDrawBtn = document.getElementById('offerDrawBtn');
    const resignBtn = document.getElementById('resignBtn');
    const flipBoardBtn = document.getElementById('flipBoardBtn');
    const analysisBtn = document.getElementById('analysisBtn');
    
    // Determine visibility conditions
    const isPlayer = this.isCurrentUserPlayer();
    const isCompleted = this.isGameCompleted();
    const isActivePlayer = isPlayer && !isCompleted && this.gameData?.status === 'active';
    
    // Player-only action buttons (Offer Draw, Resign)
    // Only visible for players in an active, ongoing game
    if (offerDrawBtn) {
      offerDrawBtn.style.display = isActivePlayer ? '' : 'none';
    }
    if (resignBtn) {
      resignBtn.style.display = isActivePlayer ? '' : 'none';
    }
    
    // Universal controls (Flip Board, Analysis) - always visible
    if (flipBoardBtn) {
      flipBoardBtn.style.display = '';
    }
    if (analysisBtn) {
      analysisBtn.style.display = '';
    }
    
    console.log(`Game controls updated - isPlayer: ${isPlayer}, isCompleted: ${isCompleted}, isActivePlayer: ${isActivePlayer}`);
  }

  // ===========================================
  // ROUTING AND NAVIGATION
  // ===========================================

  setupRoutes() {
    console.log('Setting up routes for game page...');
    
    if (!window.router) {
      console.warn('Router not available, skipping route setup');
      return;
    }
    
    const routes = [
      { path: '/lobby', title: 'Lobby - Chess Platform', url: '/lobby/' },
      { path: '/profile', title: 'Profile - Chess Platform', url: '/profile/' },
      { path: '/puzzles', title: 'Puzzles - Chess Platform', url: '/puzzles/' }
    ];
    
    routes.forEach(route => {
      window.router.addRoute(route.path, {
        title: route.title,
        controller: () => window.location.href = route.url,
        requiresAuth: true
      });
    });
    
    console.log('Routes configured for game page');
  }

  setupNavigation() {
    console.log('Setting up navigation for game page...');
    
    document.querySelectorAll('a[data-route]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const route = link.getAttribute('data-route');
        console.log('Navigating to:', route);
        window.location.href = route + '/';
      });
    });
  }

  navigateToRoute(path) {
    console.log('Navigating to route:', path);
    
    const djangoUrlMap = {
      '/lobby': '/lobby/',
      '/login': '/login/',
      '/register': '/register/',
      '/profile': '/profile/',
      '/': '/'
    };
    
    if (djangoUrlMap[path]) {
      window.location.href = djangoUrlMap[path];
    } else if (window.router) {
      window.router.navigate(path);
    } else {
      console.error('No route mapping found for:', path);
      window.location.href = '/lobby/';
    }
  }

  // ===========================================
  // AUTHENTICATION AND USER MANAGEMENT
  // ===========================================

  async ensureAuthentication() {
    console.log('Checking authentication status...');
    
    if (this.api.isAuthenticated()) {
      console.log('User is already authenticated');
      return true;
    }
    
    console.log('User not authenticated - redirecting to login');
    this.api.showError('Please log in to view games');
    
    const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login/?next=${returnUrl}`;
    
    return false;
  }

  async loadCurrentUser() {
    try {
      const response = await this.api.getUserProfile();
      if (response.ok) {
        this.currentUser = response.data;
        this.updateCurrentUserDisplay();
      }
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  }

  updateCurrentUserDisplay() {
    if (!this.currentUser) return;
    
    const elements = {
      name: document.getElementById('currentUserName'),
      rating: document.getElementById('currentUserRating'),
      info: document.getElementById('currentUserInfo')
    };
    
    if (elements.name) elements.name.textContent = this.currentUser.username;
    if (elements.rating) elements.rating.textContent = this.currentUser.rating || 1200;
    if (elements.info) elements.info.style.display = 'block';
  }

  // ===========================================
  // GAME DATA MANAGEMENT
  // ===========================================

  getGameIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const gameIdParam = urlParams.get('game');
    
    if (gameIdParam) {
      return parseInt(gameIdParam);
    }
    
    const path = window.location.pathname;
    const matches = path.match(/\/game\/(\d+)/);
    return matches ? parseInt(matches[1]) : null;
  }

  async loadGameData() {
    try {
      this.showBoardLoading(true);
      const response = await this.api.getGameDetail(this.gameId);
      
      if (response.ok) {
        this.gameData = response.data;
        console.log('Game data loaded:', this.gameData);
        
        // Ensure valid FEN
        if (!this.gameData.fen || this.gameData.fen === 'startpos') {
          this.gameData.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
        }
        
        this.updateGameDisplay();
        this.renderBoard();
        
        // Check for incoming draw offers
        this.checkForDrawOffer();
        
        // Start timer for active games
        if (this.gameData.status === 'active') {
          // For active games, just start polling the existing timer
          this.startTimerUpdates();
        } else if (this.gameData.status === 'waiting') {
          // Only try to start timer for waiting games
          await this.startProfessionalTimer();
        }
      } else {
        throw new Error(`Failed to load game: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to load game data:', error);
      this.api.showError('Failed to load game data');
    } finally {
      this.showBoardLoading(false);
    }
  }

  checkForDrawOffer() {
    // Check if there's an active draw offer from opponent
    const currentUsername = this.currentUser?.username;
    const drawOfferedBy = this.gameData?.draw_offered_by_username;
    
    if (drawOfferedBy && drawOfferedBy !== currentUsername && !this.drawOfferShownForId) {
      // Show draw offer received modal
      this.drawOfferPending = true;
      this.drawOfferShownForId = this.gameData.id + '_' + drawOfferedBy;
      this.showDrawReceivedModal();
    }
  }

  // ===========================================
  // GAME DISPLAY MANAGEMENT
  // ===========================================

  updateGameDisplay() {
    if (!this.gameData) return;
    
    this.updateGameHeader();
    this.updatePlayerInfo();
    this.updateTurnIndicator();
    this.updateMoveHistory();
    this.updateGameStatus();
    
    // Ensure controls visibility is always in sync with game state
    this.updateGameControlsVisibility();
  }

  updateGameHeader() {
    const gameIdEl = document.getElementById('gameId');
    const statusEl = document.getElementById('gameStatus');
    
    if (gameIdEl) gameIdEl.textContent = `Game #${this.gameData.id}`;
    if (statusEl) {
      statusEl.textContent = this.getStatusText(this.gameData.status);
      statusEl.className = `game-status-badge status-${this.gameData.status}`;
    }
  }

  updatePlayerInfo() {
    this.updateSinglePlayerInfo('white', this.gameData.white_player_username, this.gameData.white_player_rating);
    this.updateSinglePlayerInfo('black', this.gameData.black_player_username, this.gameData.black_player_rating);
  }

  updateSinglePlayerInfo(color, username, rating) {
    const elements = {
      name: document.getElementById(`${color}Name`),
      avatar: document.getElementById(`${color}Avatar`),
      rating: document.getElementById(`${color}Rating`)
    };
    
    if (username) {
      if (elements.name) elements.name.textContent = username;
      if (elements.avatar) elements.avatar.textContent = username.charAt(0).toUpperCase();
      if (elements.rating) elements.rating.textContent = rating || 1200;
    } else {
      if (elements.name) elements.name.textContent = color === 'white' ? 'White Player' : 'Waiting...';
      if (elements.avatar) elements.avatar.textContent = '?';
      if (elements.rating) elements.rating.textContent = '----';
    }
  }

  updateTurnIndicator() {
    const whiteCard = document.getElementById('whitePlayer');
    const blackCard = document.getElementById('blackPlayer');
    
    if (!whiteCard || !blackCard) return;
    
    // Clear existing indicators
    [whiteCard, blackCard].forEach(card => {
      card.classList.remove('current-turn');
      card.querySelector('.turn-indicator')?.remove();
    });
    
    if (this.gameData.status === 'active') {
      const currentTurn = this.getCurrentTurn();
      const currentPlayerCard = document.getElementById(`${currentTurn}Player`);
      
      if (currentPlayerCard) {
        currentPlayerCard.classList.add('current-turn');
        
        const indicator = document.createElement('div');
        indicator.className = 'turn-indicator';
        const avatar = currentPlayerCard.querySelector('.player-avatar');
        if (avatar) avatar.appendChild(indicator);
      }
    }
  }

  updateMoveHistory() {
    const moveListEl = document.getElementById('moveList');
    if (!moveListEl) return;
    
    const moves = this.gameData.moves || [];
    
    if (moves.length === 0) {
      moveListEl.innerHTML = `
        <div style="text-align: center; color: var(--color-text-muted); font-size: var(--font-size-sm);">
          No moves yet. Game starting...
        </div>
      `;
      this.updateNavigationButtons();
      this.updateCapturedPiecesDisplay();
      return;
    }
    
    let html = '';
    for (let i = 0; i < moves.length; i += 2) {
      const moveNumber = Math.floor(i / 2) + 1;
      const whiteMove = moves[i];
      const blackMove = moves[i + 1];
      
      // Determine if this move is currently being viewed
      const whiteIsCurrent = this.viewingMoveIndex === i;
      const blackIsCurrent = this.viewingMoveIndex === i + 1;
      
      html += `
        <div class="move-pair">
          <span class="move-number">${moveNumber}.</span>
          <span class="move-white${whiteIsCurrent ? ' move-current' : ''}" data-move-index="${i}">${whiteMove.notation}</span>
          <span class="move-black${blackIsCurrent ? ' move-current' : ''}" data-move-index="${i + 1}">
            ${blackMove ? blackMove.notation : ''}
          </span>
        </div>
      `;
    }
    
    moveListEl.innerHTML = html;
    
    // Update viewing state if we're at the latest position
    if (!this.isViewingHistory) {
      this.viewingMoveIndex = moves.length - 1;
    }
    
    // Scroll to bottom (only if viewing current position)
    if (!this.isViewingHistory) {
      const historyEl = document.getElementById('moveHistory');
      if (historyEl) historyEl.scrollTop = historyEl.scrollHeight;
    }
    
    // Update navigation buttons and captured pieces
    this.updateNavigationButtons();
    this.updateCapturedPiecesDisplay();
  }

  updateGameStatus() {
    const statusMessageEl = document.getElementById('statusMessage');
    const statusDetailsEl = document.getElementById('statusDetails');
    
    if (!statusMessageEl || !statusDetailsEl) return;
    
    const status = this.gameData.status;
    
    // Update game controls visibility based on current state
    this.updateGameControlsVisibility();
    
    if (status === 'waiting') {
      statusMessageEl.textContent = 'Waiting for opponent';
      statusDetailsEl.textContent = 'Game will start when black player joins';
    } else if (status === 'active') {
      const currentTurn = this.getCurrentTurn();
      statusMessageEl.textContent = 'Game in progress';
      statusDetailsEl.textContent = `${currentTurn.charAt(0).toUpperCase() + currentTurn.slice(1)} to move`;
    } else if (['finished', 'checkmate', 'stalemate', 'resigned', 'timeout', 'draw', 'abandoned'].includes(status)) {
      this.stopTimerUpdates();
      this.handleGameEndStatus(status);
    }
  }

  handleGameEndStatus(status) {
    const statusMessageEl = document.getElementById('statusMessage');
    const statusDetailsEl = document.getElementById('statusDetails');
    
    const termination = this.gameData.termination;
    const winnerColor = this.gameData.winner === this.gameData.white_player ? 'White' : 'Black';
    const loserColor = winnerColor === 'White' ? 'Black' : 'White';
    
    // Check termination reason first for accurate messages
    if (termination === 'resignation') {
      statusMessageEl.textContent = `${winnerColor} wins by resignation!`;
      statusDetailsEl.textContent = `${loserColor} resigned the game`;
      this.api.showSuccess(`${winnerColor} wins - ${loserColor} resigned!`, 8000);
    } else if (termination === 'timeout') {
      statusMessageEl.textContent = `${winnerColor} wins on time!`;
      statusDetailsEl.textContent = `${loserColor} ran out of time`;
      this.api.showSuccess(`${winnerColor} wins on time!`, 8000);
    } else if (termination === 'agreement' || termination === 'draw_agreement') {
      statusMessageEl.textContent = 'Game drawn by agreement!';
      statusDetailsEl.textContent = 'Both players agreed to a draw';
      this.api.showSuccess('Game ended in a draw by agreement!', 6000);
    } else if (termination === 'checkmate' || status === 'checkmate') {
      statusMessageEl.textContent = `Checkmate! ${winnerColor} wins!`;
      statusDetailsEl.textContent = `${winnerColor} achieved checkmate`;
      this.api.showSuccess(`Checkmate! ${winnerColor} wins!`, 8000);
    } else if (termination === 'stalemate' || status === 'stalemate') {
      statusMessageEl.textContent = 'Stalemate!';
      statusDetailsEl.textContent = 'Game ended in a stalemate (draw)';
      this.api.showSuccess('Game ended in stalemate - it\'s a draw!', 6000);
    } else if (termination === 'insufficient_material') {
      statusMessageEl.textContent = 'Draw - Insufficient material!';
      statusDetailsEl.textContent = 'Neither player has enough pieces to checkmate';
      this.api.showSuccess('Game drawn - insufficient material!', 6000);
    } else if (termination === 'threefold_repetition') {
      statusMessageEl.textContent = 'Draw - Threefold repetition!';
      statusDetailsEl.textContent = 'Same position occurred three times';
      this.api.showSuccess('Game drawn by threefold repetition!', 6000);
    } else if (termination === 'fifty_move_rule') {
      statusMessageEl.textContent = 'Draw - Fifty move rule!';
      statusDetailsEl.textContent = '50 moves without pawn move or capture';
      this.api.showSuccess('Game drawn by fifty-move rule!', 6000);
    } else if (this.gameData.winner) {
      statusMessageEl.textContent = `${winnerColor} wins!`;
      statusDetailsEl.textContent = 'Game completed';
      this.api.showSuccess(`${winnerColor} wins the game!`, 8000);
    } else {
      statusMessageEl.textContent = 'Game drawn';
      statusDetailsEl.textContent = 'Game ended in a draw';
      this.api.showSuccess('Game ended in a draw!', 6000);
    }
    
    // Ensure controls are updated when game ends
    this.updateGameControlsVisibility();
  }

  // ===========================================
  // BOARD RENDERING AND INTERACTION
  // ===========================================

  renderBoard() {
    const boardEl = this.safeElementAccess('chessBoard');
    if (!boardEl) {
      console.error('Chess board element not found!');
      return;
    }
    
    console.log('Rendering board with FEN:', this.gameData?.fen);
    
    // Remove viewing-history class when rendering current position
    boardEl.classList.remove('viewing-history');
    
    // Preserve the loading overlay before clearing
    const loadingOverlay = boardEl.querySelector('#boardLoading');
    boardEl.innerHTML = '';
    
    // Re-add the loading overlay if it existed
    if (loadingOverlay) {
      boardEl.appendChild(loadingOverlay);
    }
    
    // Create squares
    for (let rank = 8; rank >= 1; rank--) {
      for (let file = 1; file <= 8; file++) {
        const square = this.createSquareElement(rank, file);
        boardEl.appendChild(square);
      }
    }
    
    console.log('Board rendered, total squares:', boardEl.children.length);
    this.setupBoardEventListeners();
  }

  createSquareElement(rank, file) {
    const fileChar = String.fromCharCode(96 + file);
    const squareName = fileChar + rank;
    
    const square = document.createElement('div');
    square.className = `chess-square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
    square.dataset.square = squareName;
    
    // Add coordinate labels
    this.addCoordinateLabels(square, rank, file, fileChar);
    
    // Add piece if present
    const piece = this.getPieceAtSquare(squareName);
    if (piece) {
      const pieceEl = this.createPieceElement(piece);
      square.appendChild(pieceEl);
    }
    
    return square;
  }

  addCoordinateLabels(square, rank, file, fileChar) {
    if (rank === 1) {
      const fileLabel = document.createElement('div');
      fileLabel.className = 'coord-label coord-file';
      fileLabel.textContent = fileChar;
      square.appendChild(fileLabel);
    }
    
    if (file === 1) {
      const rankLabel = document.createElement('div');
      rankLabel.className = 'coord-label coord-rank';
      rankLabel.textContent = rank;
      square.appendChild(rankLabel);
    }
  }

  createPieceElement(piece) {
    const pieceEl = document.createElement('div');
    const isWhitePiece = piece === piece.toUpperCase();
    pieceEl.className = `chess-piece ${isWhitePiece ? 'white-piece' : 'black-piece'}`;
    pieceEl.dataset.piece = piece;
    
    const pieceSetConfig = this.getPieceSetConfig();
    
    if (pieceSetConfig.folder) {
      // Use image piece
      const color = isWhitePiece ? 'w' : 'b';
      const pieceLetter = piece.toUpperCase();
      const imageUrl = `/static/images/pieces/${pieceSetConfig.folder}/${color}${pieceLetter}.png`;
      
      pieceEl.classList.add('piece-image');
      pieceEl.style.backgroundImage = `url('${imageUrl}')`;
      pieceEl.style.backgroundSize = 'contain';
      pieceEl.style.backgroundRepeat = 'no-repeat';
      pieceEl.style.backgroundPosition = 'center';
      
      // Fallback to unicode on image error
      const img = new Image();
      img.onerror = () => {
        pieceEl.classList.remove('piece-image');
        pieceEl.classList.add('piece-unicode');
        pieceEl.style.backgroundImage = '';
        pieceEl.textContent = this.getPieceUnicode(piece);
      };
      img.src = imageUrl;
    } else {
      // Use Unicode piece
      pieceEl.classList.add('piece-unicode');
      pieceEl.textContent = this.getPieceUnicode(piece);
    }
    
    return pieceEl;
  }

  getPieceAtSquare(squareName) {
    if (!this.gameData || !this.gameData.fen) return null;
    
    const fenParts = this.gameData.fen.split(' ');
    const placement = fenParts[0];
    const ranks = placement.split('/');
    
    const file = squareName.charCodeAt(0) - 97;
    const rank = parseInt(squareName[1]) - 1;
    const rankString = ranks[7 - rank];
    
    let currentFile = 0;
    for (const char of rankString) {
      if (/\d/.test(char)) {
        currentFile += parseInt(char);
      } else {
        if (currentFile === file) {
          return char;
        }
        currentFile++;
      }
    }
    
    return null;
  }

  getPieceUnicode(piece) {
    const pieces = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };
    return pieces[piece] || '';
  }

  setupBoardEventListeners() {
    const squares = document.querySelectorAll('.chess-square');
    console.log('Setting up board event listeners for', squares.length, 'squares');
    
    squares.forEach(square => {
      square.addEventListener('click', this.handleSquareClick);
    });
  }

  // ===========================================
  // MOVE HANDLING
  // ===========================================

  async handleSquareClick(event) {
    const square = event.currentTarget;
    const squareName = square.dataset.square;
    
    console.log('Square clicked:', squareName);
    
    if (!this.isPlayerTurn()) {
      this.api.showToast("It's not your turn!", 'info');
      return;
    }
    
    if (!this.selectedSquare) {
      await this.handleFirstClick(squareName);
    } else {
      await this.handleSecondClick(squareName);
    }
  }

  async handleFirstClick(squareName) {
    const piece = this.getPieceAtSquare(squareName);
    if (piece && this.isOwnPiece(piece)) {
      this.selectSquare(squareName);
      await this.highlightPossibleMoves(squareName);
    }
  }

  async handleSecondClick(squareName) {
    if (squareName === this.selectedSquare) {
      this.clearSelection();
    } else if (this.isPossibleMove(squareName)) {
      await this.makeMove(this.selectedSquare, squareName);
    } else {
      const piece = this.getPieceAtSquare(squareName);
      if (piece && this.isOwnPiece(piece)) {
        this.clearSelection();
        this.selectSquare(squareName);
        await this.highlightPossibleMoves(squareName);
      } else {
        this.clearSelection();
      }
    }
  }

  isPlayerTurn() {
    if (!this.gameData || this.gameData.status !== 'active') return false;
    
    const currentTurn = this.getCurrentTurn();
    const isWhitePlayer = this.currentUser?.id === this.gameData.white_player;
    const isBlackPlayer = this.currentUser?.id === this.gameData.black_player;
    
    return (currentTurn === 'white' && isWhitePlayer) || (currentTurn === 'black' && isBlackPlayer);
  }

  isOwnPiece(piece) {
    if (!this.currentUser) return false;
    
    const isWhitePlayer = this.currentUser.id === this.gameData.white_player;
    const isWhitePiece = piece === piece.toUpperCase();
    
    return (isWhitePlayer && isWhitePiece) || (!isWhitePlayer && !isWhitePiece);
  }

  getCurrentTurn() {
    const fenParts = this.gameData.fen.split(' ');
    return fenParts[1] === 'w' ? 'white' : 'black';
  }

  selectSquare(squareName) {
    this.selectedSquare = squareName;
    const square = document.querySelector(`[data-square="${squareName}"]`);
    if (square) square.classList.add('selected');
  }

  clearSelection() {
    if (this.selectedSquare) {
      const square = document.querySelector(`[data-square="${this.selectedSquare}"]`);
      if (square) square.classList.remove('selected');
      this.selectedSquare = null;
    }
    
    document.querySelectorAll('.possible-move, .possible-capture').forEach(square => {
      square.classList.remove('possible-move', 'possible-capture');
    });
    this.possibleMoves = [];
  }

  async highlightPossibleMoves(squareName) {
    try {
      const response = await this.api.getLegalMoves(this.gameId, squareName);
      
      if (response.ok) {
        this.possibleMoves = response.data.moves.map(move => ({
          to: move.to,
          capture: move.capture || false
        }));
      } else {
        this.possibleMoves = this.calculateBasicMoves(squareName);
      }
      
      this.possibleMoves.forEach(move => {
        const square = document.querySelector(`[data-square="${move.to}"]`);
        if (square) {
          square.classList.add(move.capture ? 'possible-capture' : 'possible-move');
        }
      });
    } catch (error) {
      console.warn('Failed to get legal moves from backend, using fallback');
      this.possibleMoves = this.calculateBasicMoves(squareName);
    }
  }

  calculateBasicMoves(squareName) {
    const moves = [];
    const piece = this.getPieceAtSquare(squareName);
    
    if (!piece || piece.toLowerCase() !== 'p') return moves;
    
    const file = squareName.charCodeAt(0) - 97;
    const rank = parseInt(squareName[1]) - 1;
    const direction = piece === 'P' ? 1 : -1;
    const newRank = rank + direction;
    
    if (newRank >= 0 && newRank < 8) {
      const newSquare = String.fromCharCode(97 + file) + (newRank + 1);
      if (!this.getPieceAtSquare(newSquare)) {
        moves.push({ to: newSquare, capture: false });
        
        const startingRank = piece === 'P' ? 1 : 6;
        if (rank === startingRank) {
          const doubleRank = rank + (direction * 2);
          if (doubleRank >= 0 && doubleRank < 8) {
            const doubleSquare = String.fromCharCode(97 + file) + (doubleRank + 1);
            if (!this.getPieceAtSquare(doubleSquare)) {
              moves.push({ to: doubleSquare, capture: false });
            }
          }
        }
      }
    }
    
    return moves;
  }

  isPossibleMove(squareName) {
    return this.possibleMoves.some(move => move.to === squareName);
  }

  async makeMove(from, to) {
    try {
      console.log(`Making move: ${from} → ${to}`);
      this.clearSelection();
      this.showBoardLoading(true);
      
      // Reset viewing history state - we're making a new move
      this.isViewingHistory = false;
      this.viewingMoveIndex = -1;
      
      // Handle promotion
      let promotion = null;
      const piece = this.getPieceAtSquare(from);
      const isPromotion = piece?.toLowerCase() === 'p' && (to[1] === '8' || to[1] === '1');
      
      if (isPromotion) {
        promotion = await this.showPromotionDialog();
        if (!promotion) return;
      }
      
      const response = await this.api.makeMove(this.gameId, from, to, promotion);
      
      if (response.ok) {
        console.log('✅ Move API call successful');
        
        // Always update the game data from the response
        // The WebSocket will provide real-time updates, but we need immediate feedback
        this.gameData = response.data.game;
        this.updateGameDisplay();
        this.renderBoard();
        this.updateMoveHistory();
        this.updateGameStatus();
        
        if (response.data.game_status) {
          this.handleGameOverStatus(response.data.game_status);
        }
        
        console.log('🎯 Local game state updated from API response');
        
        // Always handle timer switching for player moves
        this.switchTurn('player_move');
        this.updateTimerData(response.data.timer);
        
        // Start/update timers based on game status
        if (this.gameData.status === 'active' || response.data.game?.status === 'active') {
          this.startTimerUpdates();
        } else {
          this.stopTimerUpdates();
        }
        
        this.api.showSuccess('Move made successfully!');
        
        // Handle computer turn
        await this.handleComputerTurn();
      } else {
        this.api.showError(this.api.formatError(response));
      }
    } catch (error) {
      console.error('Move error:', error);
      this.api.showError('Failed to make move');
    } finally {
      this.showBoardLoading(false);
    }
  }

  // ===========================================
  // TIMER MANAGEMENT
  // ===========================================

  async startProfessionalTimer() {
    try {
      const response = await this.api.request(`/games/${this.gameId}/start-timer/`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = response.data;
        if (data.timer_state) {
          console.log('Professional timer started');
          this.currentTurn = data.timer_state.current_turn || 'white';
          this.startTimerUpdates();
        }
      }
    } catch (error) {
      console.error('Failed to start professional timer:', error);
      // Fallback to simple timer updates
      this.startTimerUpdates();
    }
  }

  updateTimerDisplay() {
    // Use professional timer API for accurate timer display
    if (!this.gameId) {
      return;
    }
    
    this.api.request(`/games/${this.gameId}/professional-timer/`)
      .then(response => {
        if (response.ok && response.data) {
          const data = response.data;
          if (data.white_time !== undefined && data.black_time !== undefined) {
            const whiteTime = this.formatTime(data.white_time);
            const blackTime = this.formatTime(data.black_time);
            
            const whiteTimer = document.getElementById('whiteTimer');
            const blackTimer = document.getElementById('blackTimer');
            
            if (whiteTimer) whiteTimer.textContent = whiteTime;
            if (blackTimer) blackTimer.textContent = blackTime;
            
            if (data.current_turn) {
              this.currentTurn = data.current_turn;
            }
            
            // Update visual indicators
            this.updateTimerVisuals(data.white_time, data.black_time);
            
            // Check for timeout
            if (data.white_time <= 0 || data.black_time <= 0) {
              this.handleTimeout(data.white_time <= 0 ? 'white' : 'black');
            }
          }
        }
      })
      .catch(error => {
        console.error('Professional timer error:', error);
        // Don't spam console on auth errors, fail silently
        if (error.status !== 401) {
          console.error('Timer update failed:', error);
        }
      });
  }

  updateTimerVisuals(whiteTime, blackTime) {
    const whiteTimer = document.getElementById('whiteTimer');
    const blackTimer = document.getElementById('blackTimer');
    
    if (whiteTimer && blackTimer) {
      whiteTimer.classList.toggle('low-time', whiteTime <= 30);
      blackTimer.classList.toggle('low-time', blackTime <= 30);
      
      const whiteCard = whiteTimer.closest('.player-card');
      const blackCard = blackTimer.closest('.player-card');
      
      if (whiteCard && blackCard) {
        whiteCard.classList.toggle('current-turn', this.currentTurn === 'white');
        blackCard.classList.toggle('current-turn', this.currentTurn === 'black');
      }
    }
  }

  switchTurn(reason = 'move') {
    try {
      console.log(`Professional Timer Move - Reason: ${reason}`);
      
      // Use WebSocket for timer synchronization instead of API calls
      if (this.useWebSocketTimer && this.webSocketManager) {
        console.log('Timer move handled via WebSocket');
        return;
      }
      
      // Simple local turn switching to avoid 401 errors
      this.currentTurn = this.currentTurn === 'white' ? 'black' : 'white';
      console.log(`Turn switched to: ${this.currentTurn}`);
      this.updateTurnIndicator();
      
    } catch (error) {
      console.error('Switch turn error:', error);
    }
  }

  formatTime(seconds) {
    if (seconds === null || seconds === undefined) return '∞';
    if (seconds < 0) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  handleTimeout(timeoutPlayer) {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
    
    this.api.showError(`${timeoutPlayer === 'white' ? 'White' : 'Black'} player ran out of time!`);
    
    setTimeout(() => this.loadGameData(), 1000);
  }

  startTimerUpdates() {
    // Stop any existing timer
    if (this.timerInterval) clearInterval(this.timerInterval);
    
    // Fast polling timer for reliable updates
    this.timerInterval = setInterval(() => {
      this.updateTimerDisplay();
    }, 1000);
    this.updateTimerDisplay();
  }

  stopTimerUpdates() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  updateTimerData(timerData) {
    if (!timerData) return;
    
    const gameFinished = this.gameData && 
      ['finished', 'checkmate', 'stalemate'].includes(this.gameData.status);
    
    if (gameFinished && this.gameTimerData) {
      console.log('Game finished - preserving final timer state');
      this.gameTimerData.game_status = timerData.game_status || this.gameTimerData.game_status;
      this.gameTimerData.current_turn = timerData.current_turn || this.gameTimerData.current_turn;
    } else if (this.gameData?.status === 'active' && this.gameTimerData && this.lastTimerUpdate) {
      console.log('Active game - preserving client timer countdown');
    } else {
      this.gameTimerData = timerData;
      this.lastTimerUpdate = Date.now();
    }
  }

  // ===========================================
  // COMPUTER OPPONENT HANDLING
  // ===========================================

  async handleComputerTurn() {
    try {
      // Prevent rapid-fire calls using timestamp
      const now = Date.now();
      if (now - this.lastComputerMoveAttempt < 2000) { // 2 second minimum between attempts
        console.log('Computer move attempt too soon, skipping...');
        return;
      }
      
      // Enhanced validation to prevent unnecessary API calls
      if (this.gameData && ['finished', 'checkmate', 'stalemate'].includes(this.gameData.status)) {
        console.log(`Game is finished (${this.gameData.status}), skipping computer move`);
        return;
      }
      
      // More robust checks to prevent race conditions
      if (this.computerMoveInProgress) {
        console.log('Computer move already in progress, skipping...');
        return;
      }
      
      if (!this.isComputerGame()) {
        console.log('Not a computer game, skipping computer move');
        return;
      }
      
      if (!this.isComputerTurn()) {
        console.log('Not computer\'s turn, skipping computer move');
        return;
      }
      
      // Additional check: make sure we have valid game data and FEN
      if (!this.gameData.fen || this.gameData.fen === '') {
        console.log('Invalid FEN state, skipping computer move');
        return;
      }
      
      // Update timestamp to prevent rapid calls
      this.lastComputerMoveAttempt = now;
      
      console.log('Initiating computer move...');
      
      setTimeout(async () => {
        // Double-check before actually making the move
        if (!this.computerMoveInProgress && this.isComputerTurn()) {
          await this.makeComputerMoveWithRetry();
        } else {
          console.log('Computer move conditions changed, aborting...');
        }
      }, 800);
      
    } catch (error) {
      console.error('Error handling computer turn:', error);
      this.computerMoveInProgress = false;
    }
  }

  async makeComputerMoveWithRetry() {
    if (this.computerMoveInProgress) {
      console.log('Computer move already in progress, skipping retry...');
      return;
    }
    
    // Additional validation before starting
    if (!this.isComputerGame() || !this.isComputerTurn()) {
      console.log('Computer move conditions not met, aborting retry...');
      return;
    }
    
    this.computerMoveInProgress = true;
    
    try {
      await this.makeComputerMove();
      this.computerMoveRetryCount = 0;
    } catch (error) {
      console.error(`Computer move failed (attempt ${this.computerMoveRetryCount + 1}):`, error);
      
      // Handle 400 error (not computer's turn) gracefully
      if (error.status === 400) {
        console.log('Computer move failed with 400 error - not computer\'s turn or game finished');
        this.computerMoveInProgress = false;
        this.computerMoveRetryCount = 0;
        this.showBoardLoading(false); // Ensure loading state is cleared
        return;
      }
      
      // Only retry on 500 errors or network issues, not on 400 errors
      if (error.status !== 400 && this.computerMoveRetryCount < this.MAX_COMPUTER_MOVE_RETRIES) {
        this.computerMoveRetryCount++;
        console.log(`Retrying computer move in 2 seconds... (${this.computerMoveRetryCount}/${this.MAX_COMPUTER_MOVE_RETRIES})`);
        
        setTimeout(async () => {
          this.computerMoveInProgress = false;
          // Re-check conditions before retry
          if (this.isComputerGame() && this.isComputerTurn()) {
            await this.makeComputerMoveWithRetry();
          } else {
            console.log('Computer move conditions changed during retry, aborting...');
            this.computerMoveRetryCount = 0;
          }
        }, 2000);
      } else {
        if (error.status === 400) {
          console.log('Computer move aborted due to invalid conditions (400 error)');
        } else {
          console.error('Max computer move retries exceeded');
          this.api.showError('Computer failed to move after multiple attempts. Please refresh the page.');
        }
        this.computerMoveInProgress = false;
        this.computerMoveRetryCount = 0;
        this.showBoardLoading(false); // Clear loading state
      }
    }
  }

  async makeComputerMove() {
    try {
      console.log('Starting computer move execution...');
      this.showBoardLoading(true);
      
      if (!this.isComputerGame() || !this.isComputerTurn()) {
        console.log('Computer move cancelled - not computer\'s turn anymore');
        this.computerMoveInProgress = false;
        this.showBoardLoading(false);
        return;
      }
      
      const urlParams = new URLSearchParams(window.location.search);
      const difficulty = urlParams.get('difficulty') || 'medium';
      
      console.log(`Making computer move with difficulty: ${difficulty} for game ${this.gameId}`);
      
      const response = await this.api.makeComputerMove(this.gameId, difficulty);
      console.log('Computer move response:', response);
      
      if (response.ok) {
        console.log('Computer move successful:', response.data);
        
        // If WebSocket is connected, it will handle the game state update
        if (!this.wsConnected) {
          // Fallback: update locally if no WebSocket
          this.gameData = response.data.game;
          this.updateGameDisplay();
          this.renderBoard();
          
          if (response.data.game_status) {
            this.handleGameOverStatus(response.data.game_status);
          }
        }
        
        // Always handle timer for computer moves
        this.switchTurn('computer_move');
        this.updateTimerData(response.data.timer);
        
        const moveInfo = response.data.computer_move;
        this.api.showSuccess(
          `Computer moved: ${moveInfo.from_square} → ${moveInfo.to_square} (${moveInfo.notation})`,
          3000
        );
        
        // Update timers based on game status
        if (this.gameData?.status === 'active' || response.data.game?.status === 'active') {
          this.startTimerUpdates();
        } else {
          this.stopTimerUpdates();
        }
      } else {
        console.error('Computer move API failed:', response);
        this.api.showError(`Computer move failed: ${this.api.formatError(response)}`);
        throw new Error(`Computer move API failed: ${this.api.formatError(response)}`);
      }
    } catch (error) {
      console.error('Error making computer move:', error);
      this.api.showError('Failed to make computer move');
      throw error;
    } finally {
      this.showBoardLoading(false);
      this.computerMoveInProgress = false;
    }
  }

  isComputerGame() {
    if (!this.gameData) return false;
    
    const isWhiteComputer = this.gameData.white_player_username && 
      this.isComputerUsername(this.gameData.white_player_username);
    const isBlackComputer = this.gameData.black_player_username && 
      this.isComputerUsername(this.gameData.black_player_username);
    
    return isWhiteComputer || isBlackComputer;
  }

  isComputerTurn() {
    if (!this.gameData || !this.currentUser) return false;
    
    const currentTurn = this.getCurrentTurn();
    const currentPlayerUsername = currentTurn === 'white' 
      ? this.gameData.white_player_username 
      : this.gameData.black_player_username;
    
    return currentPlayerUsername && 
           currentPlayerUsername !== this.currentUser.username &&
           this.isComputerUsername(currentPlayerUsername);
  }

  isComputerUsername(username) {
    return username.toLowerCase().includes('computer') || 
           username.toLowerCase().includes('bot');
  }

  // ===========================================
  // GAME OVER HANDLING
  // ===========================================

  handleGameOverStatus(gameStatus) {
    if (!gameStatus?.is_game_over) return;
    
    let message = '';
    let details = '';
    
    if (gameStatus.is_checkmate) {
      const currentTurn = this.getCurrentTurn();
      const winner = currentTurn === 'white' ? 'Black' : 'White';
      message = `Checkmate! ${winner} Wins!`;
      details = `${currentTurn === 'white' ? 'White' : 'Black'} is in checkmate`;
      this.api.showSuccess(message, 8000);
    } else if (gameStatus.is_stalemate) {
      message = 'Stalemate! Game Drawn';
      details = 'No legal moves available, but king is not in check';
      this.api.showSuccess(message, 8000);
    } else if (gameStatus.result) {
      const resultMessages = {
        '1/2-1/2': { message: 'Game Drawn', details: 'Draw by rule' },
        '1-0': { message: 'White Wins!', details: 'Game completed' },
        '0-1': { message: 'Black Wins!', details: 'Game completed' }
      };
      
      const result = resultMessages[gameStatus.result];
      if (result) {
        message = result.message;
        details = result.details;
        this.api.showSuccess(message, 6000);
      }
    }
    
    if (message) {
      const statusMessageEl = document.getElementById('statusMessage');
      const statusDetailsEl = document.getElementById('statusDetails');
      if (statusMessageEl) statusMessageEl.textContent = message;
      if (statusDetailsEl) statusDetailsEl.textContent = details;
    }
    
    // Update controls visibility when game is over
    this.updateGameControlsVisibility();
    
    console.log('Game Over:', { message, details, gameStatus });
  }

  // ===========================================
  // UI HELPERS AND UTILITIES
  // ===========================================

  showPromotionDialog() {
    return new Promise((resolve) => {
      const dialog = document.getElementById('promotionDialog');
      if (!dialog) {
        resolve('q'); // Default to queen
        return;
      }
      
      dialog.classList.add('show');
      
      const pieces = dialog.querySelectorAll('.promotion-piece');
      pieces.forEach(piece => {
        piece.onclick = () => {
          dialog.classList.remove('show');
          resolve(piece.dataset.piece);
        };
      });
    });
  }

  setupEventListeners() {
    // Back button navigation
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const route = e.currentTarget.dataset.route;
        this.navigateToRoute(route);
      });
    }
    
    // Resign button - show modal
    const resignBtn = document.getElementById('resignBtn');
    if (resignBtn) {
      resignBtn.addEventListener('click', () => this.showResignModal());
    }
    
    // Resign modal buttons
    const resignCancelBtn = document.getElementById('resignCancelBtn');
    const resignConfirmBtn = document.getElementById('resignConfirmBtn');
    if (resignCancelBtn) {
      resignCancelBtn.addEventListener('click', () => this.hideResignModal());
    }
    if (resignConfirmBtn) {
      resignConfirmBtn.addEventListener('click', () => this.handleResign());
    }
    
    // Draw offer button - show modal
    const offerDrawBtn = document.getElementById('offerDrawBtn');
    if (offerDrawBtn) {
      offerDrawBtn.addEventListener('click', () => this.showDrawOfferModal());
    }
    
    // Draw offer modal buttons
    const drawOfferCancelBtn = document.getElementById('drawOfferCancelBtn');
    const drawOfferConfirmBtn = document.getElementById('drawOfferConfirmBtn');
    if (drawOfferCancelBtn) {
      drawOfferCancelBtn.addEventListener('click', () => this.hideDrawOfferModal());
    }
    if (drawOfferConfirmBtn) {
      drawOfferConfirmBtn.addEventListener('click', () => this.handleDrawOffer());
    }
    
    // Draw received modal buttons
    const drawAcceptBtn = document.getElementById('drawAcceptBtn');
    const drawDeclineBtn = document.getElementById('drawDeclineBtn');
    if (drawAcceptBtn) {
      drawAcceptBtn.addEventListener('click', () => this.handleDrawAccept());
    }
    if (drawDeclineBtn) {
      drawDeclineBtn.addEventListener('click', () => this.handleDrawDecline());
    }
    
    // Other game control buttons
    const flipBoardBtn = document.getElementById('flipBoardBtn');
    const analysisBtn = document.getElementById('analysisBtn');
    if (flipBoardBtn) {
      flipBoardBtn.addEventListener('click', () => this.flipBoard());
    }
    if (analysisBtn) {
      analysisBtn.addEventListener('click', () => this.openAnalysis());
    }
    
    // Move navigation buttons
    const moveFirst = document.getElementById('moveFirst');
    const movePrev = document.getElementById('movePrev');
    const moveNext = document.getElementById('moveNext');
    const moveLast = document.getElementById('moveLast');
    
    if (moveFirst) moveFirst.addEventListener('click', () => this.navigateToMove(0));
    if (movePrev) movePrev.addEventListener('click', () => this.navigateToPrevMove());
    if (moveNext) moveNext.addEventListener('click', () => this.navigateToNextMove());
    if (moveLast) moveLast.addEventListener('click', () => this.navigateToCurrentPosition());
    
    // Update control visibility based on game state and user role
    this.updateGameControlsVisibility();
    
    // Move history clicks - navigate to that position
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('move-white') || e.target.classList.contains('move-black')) {
        const moveIndex = parseInt(e.target.dataset.moveIndex);
        if (!isNaN(moveIndex)) {
          this.navigateToMove(moveIndex);
        }
      }
    });
    
    // Keyboard navigation for moves
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      // Escape key closes modals
      if (e.key === 'Escape') {
        this.hideResignModal();
        this.hideDrawOfferModal();
        this.hideDrawReceivedModal();
        return;
      }
      
      switch(e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          this.navigateToPrevMove();
          break;
        case 'ArrowRight':
          e.preventDefault();
          this.navigateToNextMove();
          break;
        case 'Home':
          e.preventDefault();
          this.navigateToMove(0);
          break;
        case 'End':
          e.preventDefault();
          this.navigateToCurrentPosition();
          break;
      }
    });
    
    // Click outside modal to close
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        this.hideResignModal();
        this.hideDrawOfferModal();
        this.hideDrawReceivedModal();
      }
    });
  }

  // ===========================================
  // RESIGN FUNCTIONALITY
  // ===========================================

  showResignModal() {
    const modal = document.getElementById('resignModal');
    if (modal) modal.style.display = 'flex';
  }

  hideResignModal() {
    const modal = document.getElementById('resignModal');
    if (modal) modal.style.display = 'none';
  }

  async handleResign() {
    this.hideResignModal();
    
    try {
      const response = await this.api.resignGame(this.gameId);
      
      if (response.ok) {
        this.api.showSuccess('You have resigned from the game');
        // Reload game data to get final state
        await this.loadGameData();
        this.updateGameStatus();
        this.updateGameControlsVisibility();
      } else {
        this.api.showError(response.error || 'Failed to resign');
      }
    } catch (error) {
      console.error('Resign error:', error);
      this.api.showError('Failed to resign from game');
    }
  }

  // ===========================================
  // DRAW OFFER FUNCTIONALITY
  // ===========================================

  showDrawOfferModal() {
    const modal = document.getElementById('drawOfferModal');
    if (modal) modal.style.display = 'flex';
  }

  hideDrawOfferModal() {
    const modal = document.getElementById('drawOfferModal');
    if (modal) modal.style.display = 'none';
  }

  async handleDrawOffer() {
    this.hideDrawOfferModal();
    
    try {
      const response = await this.api.offerDraw(this.gameId);
      
      if (response.ok) {
        if (response.data.status === 'declined') {
          // Bot declined
          this.api.showToast(response.data.message || 'Draw offer declined', 'info');
        } else {
          // Offer sent successfully
          this.drawOfferSentByMe = true;
          this.drawOfferPending = true;
          this.api.showSuccess('Draw offer sent to opponent');
          this.updateDrawOfferButton();
        }
      } else {
        this.api.showError(response.error || 'Failed to send draw offer');
      }
    } catch (error) {
      console.error('Failed to send draw offer:', error);
      this.api.showError('Failed to send draw offer');
    }
  }

  showDrawReceivedModal() {
    const modal = document.getElementById('drawReceivedModal');
    if (modal) modal.style.display = 'flex';
  }

  hideDrawReceivedModal() {
    const modal = document.getElementById('drawReceivedModal');
    if (modal) modal.style.display = 'none';
  }

  async handleDrawAccept() {
    this.hideDrawReceivedModal();
    
    try {
      const response = await this.api.respondDraw(this.gameId, 'accept');
      
      if (response.ok) {
        this.api.showSuccess('Draw accepted - game ended');
        this.drawOfferPending = false;
        this.drawOfferShownForId = null;
        // Reload game data
        await this.loadGameData();
        this.updateGameStatus();
        this.updateGameControlsVisibility();
      } else {
        this.api.showError(response.error || 'Failed to accept draw');
      }
    } catch (error) {
      console.error('Failed to accept draw:', error);
      this.api.showError('Failed to accept draw');
    }
  }

  async handleDrawDecline() {
    this.hideDrawReceivedModal();
    
    try {
      const response = await this.api.respondDraw(this.gameId, 'decline');
      
      if (response.ok) {
        this.api.showToast('Draw offer declined', 'info');
        this.drawOfferPending = false;
        this.drawOfferShownForId = null;
      } else {
        this.api.showError(response.error || 'Failed to decline draw');
      }
    } catch (error) {
      console.error('Failed to decline draw:', error);
      this.api.showError('Failed to decline draw');
    }
  }

  updateDrawOfferButton() {
    const btn = document.getElementById('offerDrawBtn');
    if (!btn) return;
    
    if (this.drawOfferSentByMe && this.drawOfferPending) {
      btn.textContent = '⏳ Draw Pending...';
      btn.disabled = true;
    } else {
      btn.textContent = '🤝 Offer Draw';
      btn.disabled = false;
    }
  }

  // ===========================================
  // FLIP BOARD & ANALYSIS
  // ===========================================

  flipBoard() {
    const board = document.getElementById('chessBoard');
    if (!board) return;
    
    board.classList.toggle('flipped');
    this.api.showToast('Board flipped', 'info');
  }

  openAnalysis() {
    // For now, show a toast - can be expanded to open analysis page
    this.api.showToast('Opening analysis mode...', 'info');
    // Future: window.open(`/analysis/${this.gameId}/`, '_blank');
  }

  // ===========================================
  // MOVE NAVIGATION
  // ===========================================

  navigateToMove(moveIndex) {
    const moves = this.gameData?.moves || [];
    if (moves.length === 0) return;
    
    // Clamp to valid range
    moveIndex = Math.max(-1, Math.min(moveIndex, moves.length - 1));
    
    this.viewingMoveIndex = moveIndex;
    this.isViewingHistory = moveIndex < moves.length - 1;
    
    // Render board at this position
    this.renderBoardAtMove(moveIndex);
    
    // Update move list highlighting
    this.updateMoveHighlighting();
    
    // Update navigation button states
    this.updateNavigationButtons();
  }

  navigateToPrevMove() {
    const moves = this.gameData?.moves || [];
    if (moves.length === 0) return;
    
    const currentIndex = this.viewingMoveIndex === -1 ? moves.length - 1 : this.viewingMoveIndex;
    if (currentIndex > 0) {
      this.navigateToMove(currentIndex - 1);
    } else if (currentIndex === 0) {
      // Go to starting position
      this.navigateToMove(-1);
    }
  }

  navigateToNextMove() {
    const moves = this.gameData?.moves || [];
    if (moves.length === 0) return;
    
    const currentIndex = this.viewingMoveIndex;
    if (currentIndex < moves.length - 1) {
      this.navigateToMove(currentIndex + 1);
    }
  }

  navigateToCurrentPosition() {
    const moves = this.gameData?.moves || [];
    this.viewingMoveIndex = moves.length - 1;
    this.isViewingHistory = false;
    
    // Render current position
    this.renderBoard();
    
    // Update UI
    this.updateMoveHighlighting();
    this.updateNavigationButtons();
  }

  renderBoardAtMove(moveIndex) {
    const moves = this.gameData?.moves || [];
    
    // Get board state at this move
    // If moveIndex is -1, show starting position
    if (moveIndex === -1) {
      // Starting position FEN
      this.renderBoardFromFEN('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR');
      return;
    }
    
    // Otherwise, get the FEN from the move data
    const move = moves[moveIndex];
    if (move && move.fen_after_move) {
      this.renderBoardFromFEN(move.fen_after_move);
    } else if (moveIndex === moves.length - 1) {
      // Last move - use current board state
      this.renderBoard();
    }
  }

  renderBoardFromFEN(fen) {
    const chessBoard = document.getElementById('chessBoard');
    if (!chessBoard) return;
    
    // Parse FEN to get piece positions
    const fenParts = fen.split(' ');
    const piecePlacement = fenParts[0];
    const rows = piecePlacement.split('/');
    
    // Build position map (using FEN character directly)
    const position = {};
    const files = 'abcdefgh';
    
    rows.forEach((row, rowIndex) => {
      const rank = 8 - rowIndex;
      let fileIndex = 0;
      
      for (const char of row) {
        if (/[1-8]/.test(char)) {
          fileIndex += parseInt(char);
        } else {
          const file = files[fileIndex];
          const square = file + rank;
          position[square] = char; // Store FEN char directly
          fileIndex++;
        }
      }
    });
    
    // Update board display
    const squares = chessBoard.querySelectorAll('.chess-square');
    squares.forEach(square => {
      const squareId = square.dataset.square;
      const piece = position[squareId];
      let pieceEl = square.querySelector('.chess-piece');
      
      if (piece) {
        // Remove existing piece if any
        if (pieceEl) {
          pieceEl.remove();
        }
        // Create new piece element
        const newPieceEl = this.createPieceElement(piece);
        square.appendChild(newPieceEl);
      } else if (pieceEl) {
        // Hide or remove piece if square is empty
        pieceEl.remove();
      }
    });
    
    // Add visual indicator that we're viewing history
    if (this.isViewingHistory) {
      chessBoard.classList.add('viewing-history');
    } else {
      chessBoard.classList.remove('viewing-history');
    }
  }

  fenCharToPiece(char) {
    const pieceMap = {
      'K': 'white_king', 'Q': 'white_queen', 'R': 'white_rook',
      'B': 'white_bishop', 'N': 'white_knight', 'P': 'white_pawn',
      'k': 'black_king', 'q': 'black_queen', 'r': 'black_rook',
      'b': 'black_bishop', 'n': 'black_knight', 'p': 'black_pawn'
    };
    return pieceMap[char] || null;
  }

  updateMoveHighlighting() {
    const moveList = document.getElementById('moveList');
    if (!moveList) return;
    
    // Remove all current highlights
    moveList.querySelectorAll('.move-current').forEach(el => {
      el.classList.remove('move-current');
    });
    
    // Add highlight to current viewed move
    if (this.viewingMoveIndex >= 0) {
      const moveEl = moveList.querySelector(`[data-move-index="${this.viewingMoveIndex}"]`);
      if (moveEl) {
        moveEl.classList.add('move-current');
        // Scroll into view
        moveEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  updateNavigationButtons() {
    const moves = this.gameData?.moves || [];
    const totalMoves = moves.length;
    const currentIndex = this.viewingMoveIndex;
    
    const firstBtn = document.getElementById('moveFirst');
    const prevBtn = document.getElementById('movePrev');
    const nextBtn = document.getElementById('moveNext');
    const lastBtn = document.getElementById('moveLast');
    
    // First and Prev disabled at start
    if (firstBtn) firstBtn.disabled = currentIndex <= -1 || totalMoves === 0;
    if (prevBtn) prevBtn.disabled = currentIndex <= -1 || totalMoves === 0;
    
    // Next and Last disabled at end
    if (nextBtn) nextBtn.disabled = currentIndex >= totalMoves - 1 || totalMoves === 0;
    if (lastBtn) {
      lastBtn.disabled = currentIndex >= totalMoves - 1 || totalMoves === 0;
      lastBtn.classList.toggle('active', !this.isViewingHistory && totalMoves > 0);
    }
  }

  // ===========================================
  // CAPTURED PIECES TRACKING
  // ===========================================

  calculateCapturedPieces() {
    // Standard starting pieces for each side
    const startingPieces = {
      white: { p: 8, n: 2, b: 2, r: 2, q: 1, k: 1 },
      black: { p: 8, n: 2, b: 2, r: 2, q: 1, k: 1 }
    };
    
    // Count current pieces on board from FEN
    const currentPieces = { white: {}, black: {} };
    const fen = this.gameData?.fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR';
    const piecePlacement = fen.split(' ')[0];
    
    for (const char of piecePlacement) {
      if (/[a-zA-Z]/.test(char)) {
        const isWhite = char === char.toUpperCase();
        const pieceType = char.toLowerCase();
        const side = isWhite ? 'white' : 'black';
        currentPieces[side][pieceType] = (currentPieces[side][pieceType] || 0) + 1;
      }
    }
    
    // Calculate captured pieces (what's missing from starting position)
    const captured = {
      byWhite: [], // Black pieces captured by white
      byBlack: []  // White pieces captured by black
    };
    
    // Piece values for material calculation
    const pieceValues = { p: 1, n: 3, b: 3, r: 5, q: 9 };
    let whiteMaterial = 0;
    let blackMaterial = 0;
    
    // Black pieces captured by white
    for (const [piece, startCount] of Object.entries(startingPieces.black)) {
      const currentCount = currentPieces.black[piece] || 0;
      const capturedCount = startCount - currentCount;
      for (let i = 0; i < capturedCount; i++) {
        captured.byWhite.push({ type: piece, color: 'black' });
        whiteMaterial += pieceValues[piece] || 0;
      }
    }
    
    // White pieces captured by black
    for (const [piece, startCount] of Object.entries(startingPieces.white)) {
      const currentCount = currentPieces.white[piece] || 0;
      const capturedCount = startCount - currentCount;
      for (let i = 0; i < capturedCount; i++) {
        captured.byBlack.push({ type: piece, color: 'white' });
        blackMaterial += pieceValues[piece] || 0;
      }
    }
    
    // Sort captures by value (most valuable first)
    const sortByValue = (a, b) => (pieceValues[b.type] || 0) - (pieceValues[a.type] || 0);
    captured.byWhite.sort(sortByValue);
    captured.byBlack.sort(sortByValue);
    
    return {
      byWhite: captured.byWhite,
      byBlack: captured.byBlack,
      whiteAdvantage: whiteMaterial - blackMaterial,
      blackAdvantage: blackMaterial - whiteMaterial
    };
  }

  updateCapturedPiecesDisplay() {
    const captured = this.calculateCapturedPieces();
    
    const whiteCapturedEl = document.getElementById('whiteCaptured');
    const blackCapturedEl = document.getElementById('blackCaptured');
    const whiteAdvantageEl = document.getElementById('whiteAdvantage');
    const blackAdvantageEl = document.getElementById('blackAdvantage');
    
    // Piece symbols
    const pieceSymbols = {
      white: { k: '♔', q: '♕', r: '♖', b: '♗', n: '♘', p: '♙' },
      black: { k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟' }
    };
    
    // Update White's captures (black pieces they took)
    if (whiteCapturedEl) {
      if (captured.byWhite.length > 0) {
        whiteCapturedEl.innerHTML = captured.byWhite.map(p => 
          `<span class="captured-piece black" title="${p.type}">${pieceSymbols.black[p.type]}</span>`
        ).join('');
      } else {
        whiteCapturedEl.innerHTML = '<span class="no-captures">—</span>';
      }
    }
    
    // Update Black's captures (white pieces they took)
    if (blackCapturedEl) {
      if (captured.byBlack.length > 0) {
        blackCapturedEl.innerHTML = captured.byBlack.map(p => 
          `<span class="captured-piece white" title="${p.type}">${pieceSymbols.white[p.type]}</span>`
        ).join('');
      } else {
        blackCapturedEl.innerHTML = '<span class="no-captures">—</span>';
      }
    }
    
    // Update advantage indicators
    if (whiteAdvantageEl) {
      if (captured.whiteAdvantage > 0) {
        whiteAdvantageEl.textContent = `+${captured.whiteAdvantage}`;
        whiteAdvantageEl.className = 'captured-advantage positive';
      } else {
        whiteAdvantageEl.textContent = '';
        whiteAdvantageEl.className = 'captured-advantage';
      }
    }
    
    if (blackAdvantageEl) {
      if (captured.blackAdvantage > 0) {
        blackAdvantageEl.textContent = `+${captured.blackAdvantage}`;
        blackAdvantageEl.className = 'captured-advantage positive';
      } else {
        blackAdvantageEl.textContent = '';
        blackAdvantageEl.className = 'captured-advantage';
      }
    }
  }

  setupPeriodicUpdates() {
    // Determine polling interval based on game type
    const pollingInterval = this.isComputerGame() ? 2000 : 1500; // Slower for bot games
    
    // Fast game state refresh for 1-2 second move updates  
    const gameInterval = setInterval(async () => {
      // Only poll when WebSocket is not connected and page is visible
      // For bot games, always poll since WebSocket is disabled
      const shouldPoll = document.visibilityState === 'visible' && 
                        this.gameData?.status === 'active' &&
                        (this.isComputerGame() || (!this.wsConnected || !this.webSocketManager));
      
      if (shouldPoll) {
        try {
          const response = await this.api.getGameDetail(this.gameId);
          if (response.ok && response.data) {
            const newMoveCount = response.data.moves ? response.data.moves.length : 0;
            const currentMoveCount = this.gameData.moves ? this.gameData.moves.length : 0;
            
            // Check for draw offer changes
            const newDrawOfferedBy = response.data.draw_offered_by_username;
            const currentDrawOfferedBy = this.gameData.draw_offered_by_username;
            
            if (newDrawOfferedBy !== currentDrawOfferedBy) {
              this.gameData.draw_offered_by_username = newDrawOfferedBy;
              this.gameData.draw_offered_by = response.data.draw_offered_by;
              
              // Check if we need to show draw offer modal
              if (newDrawOfferedBy && newDrawOfferedBy !== this.currentUser?.username) {
                this.checkForDrawOffer();
              } else if (!newDrawOfferedBy) {
                // Draw offer was cleared (accepted, declined, or expired)
                this.drawOfferPending = false;
                this.drawOfferShownForId = null;
                this.hideDrawReceivedModal();
              }
            }
            
            if (newMoveCount !== currentMoveCount) {
              console.log(`Polling detected move update: ${currentMoveCount} → ${newMoveCount} moves`);
              this.gameData = response.data;
              this.updateMoveHistory();
              this.updateGameStatus();
              this.renderBoard();
              
              // Update timer data if available
              if (response.data.timer_data) {
                this.updateTimerData(response.data.timer_data);
              }
              
              // Handle computer turn if needed (with additional safety checks)
              if (this.isComputerGame() && this.isComputerTurn() && !this.computerMoveInProgress) {
                // Add a small delay to prevent immediate rapid-fire calls
                setTimeout(() => {
                  if (this.isComputerTurn() && !this.computerMoveInProgress) {
                    this.handleComputerTurn();
                  }
                }, 300);
              }
            }
          }
        } catch (error) {
          if (error.status !== 401) { // Don't log auth errors
            console.error('Polling failed:', error);
          }
        }
      }
    }, pollingInterval); // Use dynamic interval based on game type
    
    // Store interval reference for cleanup
    this.gamePollingInterval = gameInterval;
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
      if (this.gamePollingInterval) {
        clearInterval(this.gamePollingInterval);
      }
      this.stopTimerUpdates();
      
      // Clean up WebSocket connection
      if (this.webSocketManager) {
        this.webSocketManager.disconnectAll();
      }
    });
  }

  showBoardLoading(show) {
    console.log(`showBoardLoading called with: ${show}`);
    const loadingEl = document.getElementById('boardLoading');
    const chessBoard = document.getElementById('chessBoard');
    
    if (loadingEl) {
      console.log(`Setting loading overlay show class to: ${show}`);
      loadingEl.classList.toggle('show', show);
    } else {
      console.log('No boardLoading element found, using fallback opacity');
      if (chessBoard) {
        // Fallback loading indicator
        chessBoard.style.opacity = show ? '0.5' : '1';
        chessBoard.style.pointerEvents = show ? 'none' : 'auto';
        console.log(`Set chessBoard opacity to: ${show ? '0.5' : '1'}`);
      }
    }
  }

  getStatusText(status) {
    const statusMap = {
      waiting: 'Waiting',
      active: 'Active',
      finished: 'Finished'
    };
    return statusMap[status] || status;
  }

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  safeElementAccess(id, defaultValue = null) {
    try {
      const element = document.getElementById(id);
      if (!element) {
        console.warn(`Element with id '${id}' not found`);
        return defaultValue;
      }
      return element;
    } catch (error) {
      console.error(`Error accessing element '${id}':`, error);
      return defaultValue;
    }
  }
}

// ===========================================
// UTILITY FUNCTIONS
// ===========================================

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toastContainer') || document.body;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, duration);
}

// ===========================================
// INITIALIZATION
// ===========================================

let gameController = null;

function initializeGamePage() {
  console.log('Initializing game page...');
  
  // Check dependencies
  if (typeof ChessAPI === 'undefined') {
    console.error('ChessAPI not found - make sure api.js is loaded');
    showToast('Failed to load game dependencies. Please refresh.', 'error');
    return;
  }
  
  try {
    // Create and initialize game controller
    gameController = new ChessGameController();
    gameController.initialize();
    
    console.log('Game page initialized successfully');
    
    // Mark as ready
    window.gamePageReady = true;
    window.gameController = gameController;
    
    // Dispatch ready event
    window.dispatchEvent(new CustomEvent('gamePageReady'));
    
  } catch (error) {
    console.error('Failed to initialize game page:', error);
    showToast('Failed to initialize game page. Please refresh.', 'error');
  }
}

// Multiple initialization strategies for reliability
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeGamePage);
} else {
  initializeGamePage();
}

// Fallback initialization
setTimeout(() => {
  if (!window.gamePageReady) {
    console.warn('Game page not ready after timeout, attempting fallback initialization');
    initializeGamePage();
  }
}, 2000);