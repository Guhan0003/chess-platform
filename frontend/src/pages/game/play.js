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
    
    // Bind methods
    this.handleSquareClick = this.handleSquareClick.bind(this);
    this.updateTimerDisplay = this.updateTimerDisplay.bind(this);
    this.handleWebSocketMove = this.handleWebSocketMove.bind(this);
    this.handleWebSocketTimer = this.handleWebSocketTimer.bind(this);
    this.handleWebSocketConnection = this.handleWebSocketConnection.bind(this);
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
      
      // Initialize WebSocket connection
      await this.initializeWebSocket();
      
      // Setup UI
      this.setupEventListeners();
      this.setupPeriodicUpdates();
      
      console.log('Chess game controller initialized successfully');
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
    console.log('Initializing WebSocket connection for fast game updates');
    
    try {
      console.log('Initializing WebSocket connection for game:', this.gameId);
      
      // Check if WebSocket utilities are available
      if (typeof WebSocketManager === 'undefined') {
        console.warn('WebSocket utilities not available, using fallback polling');
        this.useWebSocketTimer = false;
        return;
      }
      
      this.webSocketManager = new WebSocketManager();
      
      // Check if WebSocket utilities are available
      if (typeof WebSocketManager === 'undefined') {
        console.warn('WebSocket utilities not available, using fallback polling');
        this.useWebSocketTimer = false;
        return;
      }
      
      this.webSocketManager = new WebSocketManager();
      
      // Get access token for WebSocket authentication
      const accessToken = localStorage.getItem('access');
      console.log('Access token from localStorage:', typeof accessToken, accessToken);
      if (!accessToken) {
        console.warn('No access token available for WebSocket');
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
      gameWs.on('error', (error) => {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus(false);
      });
      
      console.log('WebSocket connection established');
      this.updateConnectionStatus(true);
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      this.useWebSocketTimer = false;
      this.updateConnectionStatus(false);
    }
  }

  handleWebSocketMove(data) {
    console.log('Received WebSocket move:', data);
    
    if (data.type === 'move_made' && data.game_state) {
      // Update game state from WebSocket
      this.gameData = {
        ...this.gameData,
        ...data.game_state,
        moves: data.game_state.moves || this.gameData.moves
      };
      
      // Update display
      this.updateGameDisplay();
      this.renderBoard();
      
      // Show move notification if it's opponent's move
      if (data.move && !this.isPlayerMove(data.move)) {
        this.api.showSuccess(`Opponent moved: ${data.move.notation}`, 3000);
      }
      
      // Handle game over
      if (data.game_state.status && ['finished', 'checkmate', 'stalemate'].includes(data.game_state.status)) {
        this.handleGameOverStatus(data);
        this.stopTimerUpdates();
      }
    }
  }

  handleWebSocketTimer(data) {
    console.log('Received WebSocket timer:', data);
    
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
    console.log('WebSocket connection status:', connected);
    this.updateConnectionStatus(connected);
    
    if (connected) {
      this.wsReconnectAttempts = 0;
      this.api.showSuccess('Connected to game server', 2000);
    } else {
      this.api.showToast('Connection lost - attempting to reconnect...', 'warning');
      this.attemptReconnection();
    }
  }

  updateConnectionStatus(connected) {
    this.wsConnected = connected;
    
    // No UI indicators needed - remove unnecessary connection status
    
    // Enable/disable real-time features
    if (!connected && this.useWebSocketTimer) {
      // Fall back to polling timer if WebSocket disconnects
      this.useWebSocketTimer = false;
      this.startTimerUpdates();
    }
  }

  async attemptReconnection() {
    if (this.wsReconnectAttempts >= this.maxReconnectAttempts) {
      this.api.showError('Failed to reconnect. Please refresh the page.');
      return;
    }
    
    this.wsReconnectAttempts++;
    console.log(`Attempting WebSocket reconnection (${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(async () => {
      try {
        if (this.webSocketManager) {
          await this.webSocketManager.reconnect();
        }
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.attemptReconnection();
      }
    }, 2000 * this.wsReconnectAttempts); // Exponential backoff
  }

  isPlayerMove(move) {
    if (!move || !this.currentUser) return false;
    
    const isWhitePlayer = this.currentUser.id === this.gameData.white_player;
    const isWhiteMove = move.color === 'white';
    
    return (isWhitePlayer && isWhiteMove) || (!isWhitePlayer && !isWhiteMove);
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
      return;
    }
    
    let html = '';
    for (let i = 0; i < moves.length; i += 2) {
      const moveNumber = Math.floor(i / 2) + 1;
      const whiteMove = moves[i];
      const blackMove = moves[i + 1];
      
      html += `
        <div class="move-pair">
          <span class="move-number">${moveNumber}.</span>
          <span class="move-white" data-move-index="${i}">${whiteMove.notation}</span>
          <span class="move-black" data-move-index="${i + 1}">
            ${blackMove ? blackMove.notation : ''}
          </span>
        </div>
      `;
    }
    
    moveListEl.innerHTML = html;
    
    // Scroll to bottom
    const historyEl = document.getElementById('moveHistory');
    if (historyEl) historyEl.scrollTop = historyEl.scrollHeight;
  }

  updateGameStatus() {
    const statusMessageEl = document.getElementById('statusMessage');
    const statusDetailsEl = document.getElementById('statusDetails');
    
    if (!statusMessageEl || !statusDetailsEl) return;
    
    const status = this.gameData.status;
    
    if (status === 'waiting') {
      statusMessageEl.textContent = 'Waiting for opponent';
      statusDetailsEl.textContent = 'Game will start when black player joins';
    } else if (status === 'active') {
      const currentTurn = this.getCurrentTurn();
      statusMessageEl.textContent = 'Game in progress';
      statusDetailsEl.textContent = `${currentTurn.charAt(0).toUpperCase() + currentTurn.slice(1)} to move`;
    } else if (['finished', 'checkmate', 'stalemate'].includes(status)) {
      this.stopTimerUpdates();
      this.handleGameEndStatus(status);
    }
  }

  handleGameEndStatus(status) {
    const statusMessageEl = document.getElementById('statusMessage');
    const statusDetailsEl = document.getElementById('statusDetails');
    
    if (status === 'checkmate' || (status === 'finished' && this.gameData.winner)) {
      const winnerColor = this.gameData.winner === this.gameData.white_player ? 'White' : 'Black';
      statusMessageEl.textContent = `Checkmate! ${winnerColor} wins!`;
      statusDetailsEl.textContent = `${winnerColor} player achieved checkmate`;
      this.api.showSuccess(`Checkmate! ${winnerColor} wins the game!`, 8000);
    } else if (status === 'stalemate') {
      statusMessageEl.textContent = 'Stalemate!';
      statusDetailsEl.textContent = 'Game ended in a stalemate (draw)';
      this.api.showSuccess('Game ended in stalemate - it\'s a draw!', 6000);
    } else if (this.gameData.winner) {
      const winnerColor = this.gameData.winner === this.gameData.white_player ? 'White' : 'Black';
      statusMessageEl.textContent = `${winnerColor} wins!`;
      statusDetailsEl.textContent = 'Game completed';
      this.api.showSuccess(`${winnerColor} wins the game!`, 8000);
    } else {
      statusMessageEl.textContent = 'Game drawn';
      statusDetailsEl.textContent = 'Game ended in a draw';
      this.api.showSuccess('Game ended in a draw!', 6000);
    }
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
    pieceEl.textContent = this.getPieceUnicode(piece);
    pieceEl.dataset.piece = piece;
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
        // If WebSocket is connected, it will handle the update
        if (!this.wsConnected) {
          // Fallback: update locally if no WebSocket
          this.gameData = response.data.game;
          this.updateGameDisplay();
          this.renderBoard();
          
          if (response.data.game_status) {
            this.handleGameOverStatus(response.data.game_status);
          }
        }
        
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
    console.log('Timer update started - WebSocket connected:', this.wsConnected, 'Use WebSocket timer:', this.useWebSocketTimer); // Debug log
    
    // Use professional timer API for accurate timer display
    if (!this.gameId) {
      console.log('No gameId available for timer update'); // Debug log
      return;
    }
    
    console.log('Fetching timer data for game:', this.gameId); // Debug log
    this.api.request(`/games/${this.gameId}/professional-timer/`)
      .then(response => {
        if (response.ok && response.data) {
          const data = response.data;
          console.log('Timer data received:', data); // Debug log
          if (data.white_time !== undefined && data.black_time !== undefined) {
            const whiteTime = this.formatTime(data.white_time);
            const blackTime = this.formatTime(data.black_time);
            
            console.log('Formatted times - White:', whiteTime, 'Black:', blackTime); // Debug log
            
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
    
    // Always use polling timer for reliable updates
    console.log('Starting polling timer updates'); // Debug log
    this.timerInterval = setInterval(() => {
      console.log('Timer interval tick'); // Debug log
      this.updateTimerDisplay();
    }, 1000);
    this.updateTimerDisplay();
  }

  stopTimerUpdates() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
      console.log('Timer stopped');
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
      if (this.gameData && ['finished', 'checkmate', 'stalemate'].includes(this.gameData.status)) {
        console.log(`Game is finished (${this.gameData.status}), skipping computer move`);
        return;
      }
      
      if (this.computerMoveInProgress || !this.isComputerGame() || !this.isComputerTurn()) {
        return;
      }
      
      console.log('Initiating computer move...');
      
      setTimeout(async () => {
        await this.makeComputerMoveWithRetry();
      }, 800);
      
    } catch (error) {
      console.error('Error handling computer turn:', error);
      this.computerMoveInProgress = false;
    }
  }

  async makeComputerMoveWithRetry() {
    if (this.computerMoveInProgress) return;
    
    this.computerMoveInProgress = true;
    
    try {
      await this.makeComputerMove();
      this.computerMoveRetryCount = 0;
    } catch (error) {
      console.error(`Computer move failed (attempt ${this.computerMoveRetryCount + 1}):`, error);
      
      if (error.status === 400) {
        console.log('Computer move failed with 400 error - game likely finished');
        this.computerMoveInProgress = false;
        this.computerMoveRetryCount = 0;
        return;
      }
      
      if (this.computerMoveRetryCount < this.MAX_COMPUTER_MOVE_RETRIES) {
        this.computerMoveRetryCount++;
        console.log(`Retrying computer move in 2 seconds... (${this.computerMoveRetryCount}/${this.MAX_COMPUTER_MOVE_RETRIES})`);
        
        setTimeout(async () => {
          this.computerMoveInProgress = false;
          await this.makeComputerMoveWithRetry();
        }, 2000);
      } else {
        console.error('Max computer move retries exceeded');
        this.api.showError('Computer failed to move after multiple attempts. Please refresh the page.');
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
    
    // Game control buttons
    const gameControls = {
      'offerDrawBtn': () => this.api.showToast('Draw offer feature coming soon!', 'info'),
      'resignBtn': () => {
        if (confirm('Are you sure you want to resign?')) {
          this.api.showToast('Resignation feature coming soon!', 'info');
        }
      },
      'flipBoardBtn': () => this.api.showToast('Board flip feature coming soon!', 'info'),
      'analysisBtn': () => this.api.showToast('Analysis feature coming soon!', 'info')
    };
    
    Object.entries(gameControls).forEach(([id, handler]) => {
      const element = document.getElementById(id);
      if (element) element.addEventListener('click', handler);
    });
    
    // Move history clicks
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('move-white') || e.target.classList.contains('move-black')) {
        this.api.showToast('Move navigation coming soon!', 'info');
      }
    });
  }

  setupPeriodicUpdates() {
    // Fast game state refresh for 1-2 second move updates  
    const gameInterval = setInterval(async () => {
      if (document.visibilityState === 'visible' && 
          this.gameData?.status === 'active') {
        try {
          const response = await this.api.getGameDetail(this.gameId);
          if (response.ok && response.data.moves.length !== this.gameData.moves.length) {
            this.gameData = response.data;
            this.updateMoveHistory();
            this.updateGameStatus();
            this.renderBoard();
          }
        } catch (error) {
          console.error('Failed to refresh game:', error);
        }
      }
    }, 1500); // Optimized to 1.5 seconds for fast move detection
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
      clearInterval(gameInterval);
      this.stopTimerUpdates();
      
      // Clean up WebSocket connection
      if (this.webSocketManager) {
        this.webSocketManager.disconnect();
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