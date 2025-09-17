// Game Page - Chess Platform
// Enhanced error handling and robust initialization

// Utility functions
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

function safeElementAccess(id, defaultValue = null) {
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

// Set up router routes for game page
function setupRoutes() {
  console.log('Setting up routes for game page...');
  
  // Check if router is available
  if (!window.router) {
    console.warn('Router not available, skipping route setup');
    return;
  }
  
  // Add route for lobby
  window.router.addRoute('/lobby', {
    title: 'Lobby - Chess Platform',
    controller: () => {
      window.location.href = '/lobby/';
    },
    requiresAuth: true
  });
  
  // Add route for profile
  window.router.addRoute('/profile', {
    title: 'Profile - Chess Platform',
    controller: () => {
      window.location.href = '/profile/';
    },
    requiresAuth: true
  });
  
  // Add route for puzzles
  window.router.addRoute('/puzzles', {
    title: 'Puzzles - Chess Platform',
    controller: () => {
      window.location.href = '/puzzles/';
    },
    requiresAuth: true
  });
  
  console.log('Routes configured for game page');
}

// Set up navigation click handlers
function setupNavigation() {
  console.log('Setting up navigation for game page...');
  
  document.querySelectorAll('a[data-route]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const route = link.getAttribute('data-route');
      console.log('Navigating to:', route);
      
      // Use direct navigation for reliability
      window.location.href = route + '/';
    });
  });
}

// Game page controller
function initGamePage() {
  // Set up router routes
  setupRoutes();
  
  // Set up navigation click handlers
  setupNavigation();
  
  let gameData = null;
  let selectedSquare = null;
  let possibleMoves = [];
  let gameId = null;
  let currentUser = null;
  let moveHistory = [];
  let api;
  
  // Timer management
  let timerInterval = null;
  let timerFetchInterval = null;
  let gameTimerData = null;
  let lastTimerUpdate = null;
  
  // Timer Functions
  function formatTime(seconds) {
    if (seconds === null || seconds === undefined) return '∞';
    if (seconds < 0) return '0:00';
    
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
  
  function updateTimerDisplay() {
    if (!gameTimerData) return;
    
    const whiteTimer = document.getElementById('whiteTimer');
    const blackTimer = document.getElementById('blackTimer');
    
    if (!whiteTimer || !blackTimer) return;
    
    // Calculate current time for display
    let whiteTime = gameTimerData.white_time;
    let blackTime = gameTimerData.black_time;
    
    // If game is active and we have a last update timestamp, calculate elapsed time
    if (gameTimerData && gameTimerData.game_status === 'active' && lastTimerUpdate) {
      const elapsed = Math.floor((Date.now() - lastTimerUpdate) / 1000);
      
      if (gameTimerData.current_turn === 'white') {
        whiteTime = Math.max(0, whiteTime - elapsed);
      } else {
        blackTime = Math.max(0, blackTime - elapsed);
      }
    }
    
    // Update display
    whiteTimer.textContent = formatTime(whiteTime);
    blackTimer.textContent = formatTime(blackTime);
    
    // Add warning classes for low time
    whiteTimer.classList.toggle('low-time', whiteTime <= 30);
    blackTimer.classList.toggle('low-time', blackTime <= 30);
    
    // Update turn indicators
    const whiteCard = whiteTimer.closest('.player-card');
    const blackCard = blackTimer.closest('.player-card');
    
    if (whiteCard && blackCard) {
      // Use gameTimerData if available, otherwise fall back to FEN parsing
      const currentTurn = gameTimerData ? gameTimerData.current_turn : getCurrentTurn();
      whiteCard.classList.toggle('current-turn', currentTurn === 'white');
      blackCard.classList.toggle('current-turn', currentTurn === 'black');
    }
    
    // Check for timeout
    if (whiteTime <= 0 || blackTime <= 0) {
      handleTimeout(whiteTime <= 0 ? 'white' : 'black');
    }
  }
  
  function handleTimeout(timeoutPlayer) {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    
    api.showError(`${timeoutPlayer === 'white' ? 'White' : 'Black'} player ran out of time!`);
    
    // Refresh game data to get the final state
    setTimeout(() => {
      loadGameData();
    }, 1000);
  }
  
  async function fetchTimerData() {
    try {
      const response = await api.getGameTimer(gameId);
      if (response.ok) {
        gameTimerData = response.data;
        lastTimerUpdate = Date.now();
        updateTimerDisplay();
      }
    } catch (error) {
      console.error('Failed to fetch timer data:', error);
    }
  }
  
  function startTimerUpdates() {
    // Clear any existing intervals first
    stopTimerUpdates();
    
    // Update timer display every second
    timerInterval = setInterval(() => {
      updateTimerDisplay();
    }, 1000);
    
    // Fetch fresh timer data every 10 seconds
    timerFetchInterval = setInterval(() => {
      fetchTimerData();
    }, 10000);
    
    // Initial fetch
    fetchTimerData();
  }
  
  function stopTimerUpdates() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    if (timerFetchInterval) {
      clearInterval(timerFetchInterval);
      timerFetchInterval = null;
    }
  }
  
  // Initialize game
  initializeGame();
  
  async function initializeGame() {
    try {
      // Initialize API
      api = new ChessAPI();
      window.api = api;
      
      // Check authentication - for demo purposes, auto-login testuser
      await ensureAuthentication();
      
      // Get game ID from URL
      gameId = getGameIdFromUrl();
      if (!gameId) {
        api.showError('Invalid game URL');
        navigateToRoute('/lobby');
        return;
      }
      
      // Load current user
      await loadCurrentUser();
      
      // Load game data
      await loadGameData();
      
      // Set up event listeners
      setupEventListeners();
      
      // Start periodic updates
      setupPeriodicUpdates();
      
    } catch (error) {
      console.error('Failed to initialize game:', error);
      api.showError('Failed to load game');
    }
  }
  
  function getGameIdFromUrl() {
    // Check URL parameters first (e.g., ?game=123)
    const urlParams = new URLSearchParams(window.location.search);
    const gameIdParam = urlParams.get('game');
    if (gameIdParam) {
      return parseInt(gameIdParam);
    }
    
    // Fallback to path-based extraction
    const path = window.location.pathname;
    const matches = path.match(/\/game\/(\d+)/);
    return matches ? parseInt(matches[1]) : null;
  }
  
  async function loadCurrentUser() {
    try {
      const response = await api.getUserProfile();
      if (response.ok) {
        currentUser = response.data;
        updateCurrentUserDisplay();
      }
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  }
  
  function updateCurrentUserDisplay() {
    if (currentUser) {
      document.getElementById('currentUserName').textContent = currentUser.username;
      document.getElementById('currentUserRating').textContent = currentUser.rating || 1200;
      document.getElementById('currentUserInfo').style.display = 'block';
    }
  }
  
  async function ensureAuthentication() {
    console.log('🔐 Checking authentication status...');
    
    // Check if already authenticated
    if (api.isAuthenticated()) {
      console.log('✅ User is already authenticated');
      return true;
    }
    
    console.log('❌ User not authenticated');
    
    // Professional implementation: redirect to login
    console.log('🔄 Redirecting to login page...');
    api.showError('Please log in to view games');
    
    // Redirect to login with return URL
    const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login/?next=${returnUrl}`;
    
    return false;
  }
  
  // Professional navigation helper function with proper Django URL support
  function navigateToRoute(path) {
    console.log('🧭 Navigating to route:', path);
    
    // Use Django URLs for proper backend integration
    const djangoUrlMap = {
      '/lobby': '/lobby/',           // Django serves lobby.html
      '/login': '/login/',           // Django serves login.html  
      '/register': '/register/',     // Django serves register.html
      '/profile': '/profile/',       // Django serves profile page
      '/': '/'                       // Django serves home/login
    };
    
    // Check if we have a Django URL mapping
    if (djangoUrlMap[path]) {
      console.log('✅ Using Django URL:', djangoUrlMap[path]);
      window.location.href = djangoUrlMap[path];
      return;
    }
    
    // Fallback to router if available
    if (window.router) {
      console.log('🔄 Using router navigation');
      window.router.navigate(path);
    } else {
      // Last resort: relative path mapping (deprecated)
      console.warn('⚠️ Using deprecated relative path mapping for:', path);
      const pathMap = {
        '/lobby': '../dashboard/lobby.html',
        '/login': '../auth/login.html',
        '/profile': '../profile/index.html'
      };
      
      if (pathMap[path]) {
        window.location.href = pathMap[path];
      } else {
        console.error('❌ No route mapping found for:', path);
        // Default to lobby as safe fallback
        window.location.href = '/lobby/';
      }
    }
  }
  
  async function loadGameData() {
    try {
      showBoardLoading(true);
      const response = await api.getGameDetail(gameId);
      
      if (response.ok) {
        gameData = response.data;
        console.log('Game data loaded:', gameData);
        
        // Ensure we have a valid FEN
        if (!gameData.fen || gameData.fen === 'startpos') {
          gameData.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
        }
        
        console.log('Using FEN:', gameData.fen);
        
        updateGameDisplay();
        renderBoard();
        
        // Load timer data (non-blocking)
        fetchTimerData().catch(err => {
          console.warn('Timer data not available:', err);
        });
        
        // Start timer updates if game is active
        if (gameData.status === 'active') {
          startTimerUpdates();
          
          // Check if computer should move immediately after game load
          setTimeout(() => {
            handleComputerTurn();
          }, 500);
        } else {
          stopTimerUpdates();
        }
      } else {
        throw new Error(api.formatError(response));
      }
    } catch (error) {
      console.error('Failed to load game data:', error);
      api.showError('Failed to load game data');
    } finally {
      showBoardLoading(false);
    }
  }
  
  function updateGameDisplay() {
    if (!gameData) return;
    
    // Update game header
    document.getElementById('gameId').textContent = `Game #${gameData.id}`;
    const statusEl = document.getElementById('gameStatus');
    statusEl.textContent = getStatusText(gameData.status);
    statusEl.className = `game-status-badge status-${gameData.status}`;
    
    // Update player info
    updatePlayerInfo('white', gameData.white_player_username, gameData.white_player_rating);
    updatePlayerInfo('black', gameData.black_player_username, gameData.black_player_rating);
    
    // Update turn indicator
    updateTurnIndicator();
    
    // Update move history
    updateMoveHistory();
    
    // Update game status
    updateGameStatus();
  }
  
  function updatePlayerInfo(color, username, rating) {
    const nameEl = document.getElementById(`${color}Name`);
    const avatarEl = document.getElementById(`${color}Avatar`);
    const ratingEl = document.getElementById(`${color}Rating`);
    
    if (username) {
      nameEl.textContent = username;
      avatarEl.textContent = username.charAt(0).toUpperCase();
      ratingEl.textContent = rating || 1200;
    } else {
      nameEl.textContent = color === 'white' ? 'White Player' : 'Waiting...';
      avatarEl.textContent = '?';
      ratingEl.textContent = '----';
    }
  }
  
  function updateTurnIndicator() {
    const whiteCard = document.getElementById('whitePlayer');
    const blackCard = document.getElementById('blackPlayer');
    
    // Remove current turn indicators
    whiteCard.classList.remove('current-turn');
    blackCard.classList.remove('current-turn');
    whiteCard.querySelector('.turn-indicator')?.remove();
    blackCard.querySelector('.turn-indicator')?.remove();
    
    if (gameData.status === 'active') {
      const currentTurn = getCurrentTurn();
      const currentPlayerCard = document.getElementById(`${currentTurn}Player`);
      currentPlayerCard.classList.add('current-turn');
      
      // Add turn indicator dot
      const indicator = document.createElement('div');
      indicator.className = 'turn-indicator';
      currentPlayerCard.querySelector('.player-avatar').appendChild(indicator);
    }
  }
  
  function getCurrentTurn() {
    // Parse FEN to get current turn
    const fenParts = gameData.fen.split(' ');
    return fenParts[1] === 'w' ? 'white' : 'black';
  }
  
  function updateMoveHistory() {
    const moveListEl = document.getElementById('moveList');
    const moves = gameData.moves || [];
    
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
    historyEl.scrollTop = historyEl.scrollHeight;
  }
  
  function updateGameStatus() {
    const statusMessageEl = document.getElementById('statusMessage');
    const statusDetailsEl = document.getElementById('statusDetails');
    
    if (gameData.status === 'waiting') {
      statusMessageEl.textContent = 'Waiting for opponent';
      statusDetailsEl.textContent = 'Game will start when black player joins';
    } else if (gameData.status === 'active') {
      const currentTurn = getCurrentTurn();
      statusMessageEl.textContent = 'Game in progress';
      statusDetailsEl.textContent = `${currentTurn.charAt(0).toUpperCase() + currentTurn.slice(1)} to move`;
    } else if (gameData.status === 'finished') {
      // Check if we have detailed game ending information
      if (gameData.winner) {
        const winnerColor = gameData.winner === gameData.white_player ? 'White' : 'Black';
        statusMessageEl.textContent = `${winnerColor} wins!`;
        statusDetailsEl.textContent = 'Game completed';
      } else {
        statusMessageEl.textContent = 'Game drawn';
        statusDetailsEl.textContent = 'Game ended in a draw';
      }
    }
  }
  
  function renderBoard() {
    const boardEl = safeElementAccess('chessBoard');
    if (!boardEl) {
      console.error('Chess board element not found!');
      showToast('Chess board not available', 'error');
      return;
    }
    
    console.log('Rendering board with FEN:', gameData?.fen);
    boardEl.innerHTML = '';
    
    // Create squares
    for (let rank = 8; rank >= 1; rank--) {
      for (let file = 1; file <= 8; file++) {
        const square = document.createElement('div');
        const fileChar = String.fromCharCode(96 + file); // a-h
        const squareName = fileChar + rank;
        
        square.className = `chess-square ${(rank + file) % 2 === 0 ? 'dark' : 'light'}`;
        square.dataset.square = squareName;
        
        // Add coordinate labels
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
        
        // Add piece if present
        const piece = getPieceAtSquare(squareName);
        if (piece) {
          console.log(`Placing piece ${piece} at ${squareName}`);
          const pieceEl = document.createElement('div');
          const isWhitePiece = piece === piece.toUpperCase();
          pieceEl.className = `chess-piece ${isWhitePiece ? 'white-piece' : 'black-piece'}`;
          pieceEl.textContent = getPieceUnicode(piece);
          pieceEl.dataset.piece = piece;
          square.appendChild(pieceEl);
        }
        
        boardEl.appendChild(square);
      }
    }
    
    console.log('Board rendered, total squares:', boardEl.children.length);
    setupBoardEventListeners();
  }
  
  function getPieceAtSquare(squareName) {
    // Parse FEN to get piece at specific square
    if (!gameData || !gameData.fen) {
      console.warn('No game data or FEN available');
      return null;
    }
    
    const fenParts = gameData.fen.split(' ');
    const placement = fenParts[0];
    const ranks = placement.split('/');
    
    const file = squareName.charCodeAt(0) - 97; // a=0, b=1, etc.
    const rank = parseInt(squareName[1]) - 1; // 1-8 to 0-7
    const rankString = ranks[7 - rank]; // FEN ranks are from 8 to 1
    
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
  
  function getPieceUnicode(piece) {
    const pieces = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };
    return pieces[piece] || '';
  }

  function getPieceImageName(piece) {
    // Convert piece notation to image filename
    const color = piece === piece.toUpperCase() ? 'w' : 'b';
    const pieceType = piece.toLowerCase();
    
    const pieceMap = {
      'k': 'K', 'q': 'Q', 'r': 'R', 'b': 'B', 'n': 'N', 'p': 'P'
    };
    
    return `${color}${pieceMap[pieceType]}.png`;
  }
  
  function setupBoardEventListeners() {
    const squares = document.querySelectorAll('.chess-square');
    console.log('🎯 Setting up board event listeners for', squares.length, 'squares');
    
    squares.forEach(square => {
      square.addEventListener('click', handleSquareClick);
    });
    
    console.log('✅ Board event listeners set up');
  }
  
  async function handleSquareClick(event) {
    console.log('🎯 Square clicked!', event.currentTarget.dataset.square);
    const square = event.currentTarget;
    const squareName = square.dataset.square;
    
    console.log('🎮 Current game state:', {
      gameData: gameData?.status,
      currentUser: currentUser?.id,
      whitePlayer: gameData?.white_player,
      blackPlayer: gameData?.black_player
    });
    
    // Check if it's the player's turn
    if (!isPlayerTurn()) {
      console.log('❌ Not player turn');
      api.showToast("It's not your turn!", 'info');
      return;
    }
    
    console.log('✅ Player turn confirmed');
    
    if (!selectedSquare) {
      // First click - select piece
      const piece = getPieceAtSquare(squareName);
      console.log('🎯 First click - piece at square:', piece);
      if (piece && isOwnPiece(piece)) {
        console.log('✅ Valid piece selected');
        selectSquare(squareName);
        highlightPossibleMoves(squareName);
      } else {
        console.log('❌ Invalid piece or not own piece');
      }
    } else {
      // Second click - make move or select different piece
      console.log('🎯 Second click - selected square:', selectedSquare, 'target:', squareName);
      if (squareName === selectedSquare) {
        // Deselect
        console.log('🔄 Deselecting piece');
        clearSelection();
      } else if (isPossibleMove(squareName)) {
        // Make move
        console.log('✅ Making move from', selectedSquare, 'to', squareName);
        await makeMove(selectedSquare, squareName);
      } else {
        // Select different piece
        const piece = getPieceAtSquare(squareName);
        console.log('🎯 Attempting to select different piece:', piece);
        if (piece && isOwnPiece(piece)) {
          console.log('✅ Selecting different piece');
          clearSelection();
          selectSquare(squareName);
          highlightPossibleMoves(squareName);
        } else {
          console.log('🔄 Clearing selection');
          clearSelection();
        }
      }
    }
  }
  
  function isPlayerTurn() {
    if (!gameData || gameData.status !== 'active') {
      console.log('❌ Game not active or no game data:', gameData?.status);
      return false;
    }
    
    const currentTurn = getCurrentTurn();
    const isWhitePlayer = currentUser && currentUser.id === gameData.white_player;
    const isBlackPlayer = currentUser && currentUser.id === gameData.black_player;
    
    console.log('🔍 Turn check:', {
      currentTurn,
      currentUserId: currentUser?.id,
      whitePlayerId: gameData.white_player,
      blackPlayerId: gameData.black_player,
      isWhitePlayer,
      isBlackPlayer,
      result: (currentTurn === 'white' && isWhitePlayer) || (currentTurn === 'black' && isBlackPlayer)
    });
    
    return (currentTurn === 'white' && isWhitePlayer) || 
           (currentTurn === 'black' && isBlackPlayer);
  }
  
  function isOwnPiece(piece) {
    if (!currentUser) {
      console.log('❌ No current user');
      return false;
    }
    
    const isWhitePlayer = currentUser.id === gameData.white_player;
    const isWhitePiece = piece === piece.toUpperCase();
    
    console.log('🔍 Piece ownership check:', {
      piece,
      currentUserId: currentUser.id,
      whitePlayerId: gameData.white_player,
      isWhitePlayer,
      isWhitePiece,
      result: (isWhitePlayer && isWhitePiece) || (!isWhitePlayer && !isWhitePiece)
    });
    
    return (isWhitePlayer && isWhitePiece) || (!isWhitePlayer && !isWhitePiece);
  }
  
  function selectSquare(squareName) {
    selectedSquare = squareName;
    const square = document.querySelector(`[data-square="${squareName}"]`);
    square.classList.add('selected');
  }
  
  function clearSelection() {
    if (selectedSquare) {
      const square = document.querySelector(`[data-square="${selectedSquare}"]`);
      square?.classList.remove('selected');
      selectedSquare = null;
    }
    
    // Clear all move highlights
    document.querySelectorAll('.possible-move, .possible-capture').forEach(square => {
      square.classList.remove('possible-move', 'possible-capture');
    });
    possibleMoves = [];
  }
  
  async function highlightPossibleMoves(squareName) {
    try {
      // Get legal moves from backend
      const response = await api.getLegalMoves(gameId, squareName);
      if (response.ok) {
        possibleMoves = response.data.moves.map(move => ({
          to: move.to,
          capture: move.capture || false
        }));
        
        possibleMoves.forEach(move => {
          const square = document.querySelector(`[data-square="${move.to}"]`);
          if (square) {
            square.classList.add(move.capture ? 'possible-capture' : 'possible-move');
          }
        });
      } else {
        // Fallback to basic move highlighting
        possibleMoves = calculateBasicMoves(squareName);
        possibleMoves.forEach(move => {
          const square = document.querySelector(`[data-square="${move.to}"]`);
          if (square) {
            square.classList.add(move.capture ? 'possible-capture' : 'possible-move');
          }
        });
      }
    } catch (error) {
      console.warn('Failed to get legal moves from backend, using fallback');
      possibleMoves = calculateBasicMoves(squareName);
      possibleMoves.forEach(move => {
        const square = document.querySelector(`[data-square="${move.to}"]`);
        if (square) {
          square.classList.add(move.capture ? 'possible-capture' : 'possible-move');
        }
      });
    }
  }
  
  function calculateBasicMoves(squareName) {
    // Simplified move calculation - fallback only
    const moves = [];
    const piece = getPieceAtSquare(squareName);
    
    if (!piece) return moves;
    
    const file = squareName.charCodeAt(0) - 97;
    const rank = parseInt(squareName[1]) - 1;
    
    // Basic pawn moves only
    if (piece.toLowerCase() === 'p') {
      const direction = piece === 'P' ? 1 : -1;
      const newRank = rank + direction;
      
      if (newRank >= 0 && newRank < 8) {
        const newSquare = String.fromCharCode(97 + file) + (newRank + 1);
        if (!getPieceAtSquare(newSquare)) {
          moves.push({ to: newSquare, capture: false });
          
          // Double pawn move from starting position
          const startingRank = piece === 'P' ? 1 : 6;
          if (rank === startingRank) {
            const doubleRank = rank + (direction * 2);
            if (doubleRank >= 0 && doubleRank < 8) {
              const doubleSquare = String.fromCharCode(97 + file) + (doubleRank + 1);
              if (!getPieceAtSquare(doubleSquare)) {
                moves.push({ to: doubleSquare, capture: false });
              }
            }
          }
        }
      }
    }
    
    return moves;
  }
  
  function isPossibleMove(squareName) {
    return possibleMoves.some(move => move.to === squareName);
  }
  
  async function makeMove(from, to) {
    try {
      clearSelection();
      showBoardLoading(true);
      
      // Check if move requires promotion
      const piece = getPieceAtSquare(from);
      const isPromotion = piece && piece.toLowerCase() === 'p' && 
                         (to[1] === '8' || to[1] === '1');
      
      let promotion = null;
      if (isPromotion) {
        promotion = await showPromotionDialog();
        if (!promotion) {
          showBoardLoading(false);
          return;
        }
      }
      
      const response = await api.makeMove(gameId, from, to, promotion);
      
      if (response.ok) {
        gameData = response.data.game;
        
        // Update timer data if provided in response
        if (response.data.timer) {
          gameTimerData = response.data.timer;
          lastTimerUpdate = Date.now();
        }
        
        updateGameDisplay();
        renderBoard();
        updateTimerDisplay();
        
        // Check for game over conditions (checkmate, stalemate, etc.)
        if (response.data.game_status) {
          handleGameOverStatus(response.data.game_status);
        }
        
        // Restart timer updates if game is still active
        if (gameData.status === 'active') {
          startTimerUpdates();
        } else {
          stopTimerUpdates();
        }
        
        api.showSuccess('Move made successfully!');
        
        // Check if it's a computer game and it's the computer's turn
        await handleComputerTurn();
      } else {
        api.showError(api.formatError(response));
      }
    } catch (error) {
      console.error('Move error:', error);
      api.showError('Failed to make move');
    } finally {
      showBoardLoading(false);
    }
  }
  
  // Game Over Status Handler
  function handleGameOverStatus(gameStatus) {
    if (!gameStatus || !gameStatus.is_game_over) {
      return; // Game is still active
    }
    
    let message = '';
    let details = '';
    
    if (gameStatus.is_checkmate) {
      // Determine winner based on current turn (the player who just got checkmated)
      const currentTurn = getCurrentTurn();
      const winner = currentTurn === 'white' ? 'Black' : 'White';
      message = `Checkmate! ${winner} Wins!`;
      details = `${currentTurn === 'white' ? 'White' : 'Black'} is in checkmate`;
      
      // Show prominent notification
      api.showSuccess(message, 8000);
      
      // Update status display
      const statusMessageEl = document.getElementById('statusMessage');
      const statusDetailsEl = document.getElementById('statusDetails');
      if (statusMessageEl) statusMessageEl.textContent = message;
      if (statusDetailsEl) statusDetailsEl.textContent = details;
      
    } else if (gameStatus.is_stalemate) {
      message = 'Stalemate! Game Drawn';
      details = 'No legal moves available, but king is not in check';
      
      // Show prominent notification
      api.showSuccess(message, 8000);
      
      // Update status display
      const statusMessageEl = document.getElementById('statusMessage');
      const statusDetailsEl = document.getElementById('statusDetails');
      if (statusMessageEl) statusMessageEl.textContent = message;
      if (statusDetailsEl) statusDetailsEl.textContent = details;
      
    } else if (gameStatus.result) {
      // Handle other game endings (draw by repetition, insufficient material, etc.)
      if (gameStatus.result === '1/2-1/2') {
        message = 'Game Drawn';
        details = 'Draw by rule';
      } else if (gameStatus.result === '1-0') {
        message = 'White Wins!';
        details = 'Game completed';
      } else if (gameStatus.result === '0-1') {
        message = 'Black Wins!';
        details = 'Game completed';
      }
      
      if (message) {
        api.showSuccess(message, 6000);
        
        const statusMessageEl = document.getElementById('statusMessage');
        const statusDetailsEl = document.getElementById('statusDetails');
        if (statusMessageEl) statusMessageEl.textContent = message;
        if (statusDetailsEl) statusDetailsEl.textContent = details;
      }
    }
    
    console.log('Game Over:', { message, details, gameStatus });
  }
  
  // Computer Chess Functions
  // Computer move state tracking
  let computerMoveInProgress = false;
  let computerMoveRetryCount = 0;
  const MAX_COMPUTER_MOVE_RETRIES = 3;
  
  async function handleComputerTurn() {
    try {
      // Prevent multiple simultaneous computer moves
      if (computerMoveInProgress) {
        console.log('Computer move already in progress, skipping');
        return;
      }
      
      if (!isComputerGame() || !isComputerTurn()) {
        console.log('Not computer\'s turn or not a computer game');
        return;
      }
      
      console.log('Initiating computer move...');
      
      // Small delay for better UX, then make the move
      setTimeout(async () => {
        await makeComputerMoveWithRetry();
      }, 800);
      
    } catch (error) {
      console.error('Error handling computer turn:', error);
      computerMoveInProgress = false; // Reset flag on error
    }
  }
  
  async function makeComputerMoveWithRetry() {
    if (computerMoveInProgress) {
      console.log('Computer move already in progress');
      return;
    }
    
    computerMoveInProgress = true;
    
    try {
      await makeComputerMove();
      computerMoveRetryCount = 0; // Reset retry count on success
    } catch (error) {
      console.error(`Computer move failed (attempt ${computerMoveRetryCount + 1}):`, error);
      
      if (computerMoveRetryCount < MAX_COMPUTER_MOVE_RETRIES) {
        computerMoveRetryCount++;
        console.log(`Retrying computer move in 2 seconds... (${computerMoveRetryCount}/${MAX_COMPUTER_MOVE_RETRIES})`);
        
        // Retry after delay
        setTimeout(async () => {
          computerMoveInProgress = false; // Reset flag before retry
          await makeComputerMoveWithRetry();
        }, 2000);
      } else {
        console.error('Max computer move retries exceeded');
        api.showError('Computer failed to move after multiple attempts. Please refresh the page.');
        computerMoveInProgress = false;
        computerMoveRetryCount = 0;
      }
    }
  }
  
  function isComputerGame() {
    if (!gameData) return false;
    
    // Check if either player is a computer using the corrected field names
    const isWhiteComputer = gameData.white_player_username && 
      (gameData.white_player_username.includes('computer') || 
       gameData.white_player_username.includes('Computer') ||
       gameData.white_player_username.includes('bot'));
    const isBlackComputer = gameData.black_player_username && 
      (gameData.black_player_username.includes('computer') || 
       gameData.black_player_username.includes('Computer') ||
       gameData.black_player_username.includes('bot'));
    
    return isWhiteComputer || isBlackComputer;
  }
  
  function isComputerTurn() {
    if (!gameData || !currentUser) return false;
    
    const currentTurn = getCurrentTurn();
    
    if (currentTurn === 'white') {
      return gameData.white_player_username && 
        gameData.white_player_username !== currentUser.username &&
        (gameData.white_player_username.includes('computer') || 
         gameData.white_player_username.includes('Computer') ||
         gameData.white_player_username.includes('bot'));
    } else {
      return gameData.black_player_username && 
        gameData.black_player_username !== currentUser.username &&
        (gameData.black_player_username.includes('computer') || 
         gameData.black_player_username.includes('Computer') ||
         gameData.black_player_username.includes('bot'));
    }
  }
  
  async function makeComputerMove() {
    try {
      console.log('Starting computer move execution...');
      showBoardLoading(true);
      
      // Verify it's still the computer's turn (double-check)
      if (!isComputerGame() || !isComputerTurn()) {
        console.log('Computer move cancelled - not computer\'s turn anymore');
        computerMoveInProgress = false;
        return;
      }
      
      // Get difficulty from URL params or use default
      const urlParams = new URLSearchParams(window.location.search);
      const difficulty = urlParams.get('difficulty') || 'medium';
      
      console.log(`Making computer move with difficulty: ${difficulty}`);
      
      const response = await api.makeComputerMove(gameId, difficulty);
      
      if (response.ok) {
        console.log('Computer move successful');
        gameData = response.data.game;
        
        // Update timer data if provided
        if (response.data.timer) {
          gameTimerData = response.data.timer;
          lastTimerUpdate = Date.now();
        }
        
        updateGameDisplay();
        renderBoard();
        updateTimerDisplay();
        
        // Show computer move info
        const moveInfo = response.data.computer_move;
        const engineInfo = response.data.engine_info;
        
        console.log('Computer move:', moveInfo);
        console.log('Engine info:', engineInfo);
        
        api.showSuccess(
          `Computer moved: ${moveInfo.from_square} → ${moveInfo.to_square} (${moveInfo.notation})`,
          3000
        );
        
        // Check for game over conditions (checkmate, stalemate, etc.)
        if (response.data.game_status) {
          handleGameOverStatus(response.data.game_status);
        }
        
        // Continue timer updates if game is still active
        if (gameData.status === 'active') {
          startTimerUpdates();
        } else {
          stopTimerUpdates();
        }
        
        // Success - clear progress flag
        computerMoveInProgress = false;
        
      } else {
        console.error('Computer move API failed:', response);
        api.showError(`Computer move failed: ${api.formatError(response)}`);
        throw new Error(`Computer move API failed: ${api.formatError(response)}`);
      }
      
    } catch (error) {
      console.error('Error making computer move:', error);
      api.showError('Failed to make computer move');
      throw error; // Re-throw to trigger retry mechanism
    } finally {
      showBoardLoading(false);
    }
  }
  
  function showPromotionDialog() {
    return new Promise((resolve) => {
      const dialog = document.getElementById('promotionDialog');
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
  
  function setupEventListeners() {
    // Back button navigation
    document.querySelector('.back-btn').addEventListener('click', (e) => {
      e.preventDefault();
      const route = e.currentTarget.dataset.route;
      navigateToRoute(route);
    });
    
    // Game controls
    document.getElementById('offerDrawBtn')?.addEventListener('click', () => {
      api.showToast('Draw offer feature coming soon!', 'info');
    });
    
    document.getElementById('resignBtn')?.addEventListener('click', () => {
      if (confirm('Are you sure you want to resign?')) {
        api.showToast('Resignation feature coming soon!', 'info');
      }
    });
    
    document.getElementById('flipBoardBtn')?.addEventListener('click', () => {
      api.showToast('Board flip feature coming soon!', 'info');
    });
    
    document.getElementById('analysisBtn')?.addEventListener('click', () => {
      api.showToast('Analysis feature coming soon!', 'info');
    });
    
    // Move history clicks
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('move-white') || e.target.classList.contains('move-black')) {
        api.showToast('Move navigation coming soon!', 'info');
      }
    });
  }
  
  function setupPeriodicUpdates() {
    // Refresh game state every 3 seconds
    const gameInterval = setInterval(async () => {
      if (document.visibilityState === 'visible' && gameData?.status === 'active') {
        try {
          const response = await api.getGameDetail(gameId);
          if (response.ok && response.data.moves.length !== gameData.moves.length) {
            gameData = response.data;
            updateGameDisplay();
            renderBoard();
          }
        } catch (error) {
          console.error('Failed to refresh game:', error);
        }
      }
    }, 3000);
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
      clearInterval(gameInterval);
    });
  }
  
  function showBoardLoading(show) {
    const loadingEl = document.getElementById('boardLoading');
    if (!loadingEl) {
      console.warn('boardLoading element not found');
      // Create a fallback loading indicator if element is missing
      const chessBoard = document.getElementById('chessBoard');
      if (chessBoard && show) {
        chessBoard.style.opacity = '0.5';
        chessBoard.style.pointerEvents = 'none';
      } else if (chessBoard && !show) {
        chessBoard.style.opacity = '1';
        chessBoard.style.pointerEvents = 'auto';
      }
      return;
    }
    if (show) {
      loadingEl.classList.add('show');
    } else {
      loadingEl.classList.remove('show');
    }
  }
  
  function getStatusText(status) {
    const statusMap = {
      waiting: 'Waiting',
      active: 'Active',
      finished: 'Finished'
    };
    return statusMap[status] || status;
  }
}

// Initialize when DOM is ready
function initializeGamePage() {
  console.log('Initializing game page...');
  
  // Check if dependencies are loaded
  if (typeof ChessAPI === 'undefined') {
    console.error('ChessAPI not found - make sure api.js is loaded');
    return;
  }
  
  if (typeof ChessRouter === 'undefined') {
    console.error('ChessRouter not found - make sure router.js is loaded');
    return;
  }
  
  try {
    // Initialize the game page
    initGamePage();
    console.log('Game page initialized successfully');
    
    // Mark as ready
    window.gamePageReady = true;
    
    // Dispatch custom event for other scripts
    window.dispatchEvent(new CustomEvent('gamePageReady'));
    
  } catch (error) {
    console.error('Failed to initialize game page:', error);
    
    // Show error to user
    showToast('Failed to initialize game page. Please refresh.', 'error');
  }
}

// Toast notification function
function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toastContainer') || document.body;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  // Auto remove after duration
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, duration);
}

// Multiple initialization strategies
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeGamePage);
} else {
  // DOM already loaded
  initializeGamePage();
}

// Fallback initialization after a delay
setTimeout(() => {
  if (!window.gamePageReady) {
    console.warn('Game page not ready after timeout, attempting fallback initialization');
    initializeGamePage();
  }
}, 2000);