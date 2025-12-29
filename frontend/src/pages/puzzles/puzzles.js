/**
 * Chess Puzzle System - Frontend Controller
 * Connects to the backend API for puzzle serving and solving
 */

class ChessPuzzleController {
  constructor() {
    this.currentPuzzle = null;
    this.selectedSquare = null;
    this.moveHistory = [];
    this.currentMoveIndex = 0;
    this.startTime = null;
    this.attempts = 0;
    this.hintsUsed = 0;
    this.timer = null;
    this.board = null;
    this.playerColor = 'white';
    
    // API instance
    this.api = null;
    
    // User stats
    this.userStats = {
      puzzleRating: 1500,
      puzzlesSolved: 0,
      accuracy: 0,
      currentStreak: 0
    };
    
    this.initialize();
  }

  async initialize() {
    try {
      // Initialize API
      if (typeof ChessAPI !== 'undefined') {
        this.api = new ChessAPI();
      } else {
        console.warn('ChessAPI not loaded, using fallback');
        this.api = this.createFallbackAPI();
      }
      
      // Check authentication
      await this.checkAuthentication();
      
      // Initialize UI
      this.initializeBoard();
      this.setupEventListeners();
      
      // Load initial puzzle
      await this.loadRandomPuzzle();
      
    } catch (error) {
      console.error('Failed to initialize puzzle system:', error);
      this.showStatusMessage('error', 'Error', 'Failed to initialize. Please refresh the page.');
    }
  }

  createFallbackAPI() {
    // Fallback API for when ChessAPI is not available
    const baseURL = '/api';
    const getToken = () => localStorage.getItem('access');
    
    return {
      request: async (endpoint, options = {}) => {
        const headers = {
          'Content-Type': 'application/json',
          ...(getToken() ? { 'Authorization': `Bearer ${getToken()}` } : {})
        };
        
        const response = await fetch(`${baseURL}${endpoint}`, {
          ...options,
          headers: { ...headers, ...options.headers }
        });
        
        const data = await response.json().catch(() => ({}));
        return { ok: response.ok, data, status: response.status };
      }
    };
  }

  async checkAuthentication() {
    const token = localStorage.getItem('access');
    if (!token) {
      window.location.href = '/login/?next=/puzzles/';
      return false;
    }
    return true;
  }

  initializeBoard() {
    const boardEl = document.getElementById('chessboard');
    if (!boardEl) return;
    
    boardEl.innerHTML = '';
    
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const square = document.createElement('div');
        const isLight = (row + col) % 2 === 0;
        square.className = `square ${isLight ? 'light' : 'dark'}`;
        square.dataset.row = row;
        square.dataset.col = col;
        square.dataset.square = this.rowColToSquare(row, col);
        square.addEventListener('click', (e) => this.handleSquareClick(e));
        boardEl.appendChild(square);
      }
    }
  }

  setupEventListeners() {
    // Navigation buttons
    document.getElementById('nextPuzzleBtn')?.addEventListener('click', () => this.loadRandomPuzzle());
    document.getElementById('restartBtn')?.addEventListener('click', () => this.restartPuzzle());
    document.getElementById('hintBtn')?.addEventListener('click', () => this.getHint());
    document.getElementById('solutionBtn')?.addEventListener('click', () => this.showSolution());
    document.getElementById('statusButton')?.addEventListener('click', () => this.hideStatusMessage());
    
    // Close modal on overlay click
    document.getElementById('statusOverlay')?.addEventListener('click', (e) => {
      if (e.target.id === 'statusOverlay') {
        this.hideStatusMessage();
      }
    });
    
    // Mobile menu toggle
    document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
      document.getElementById('sidebar')?.classList.toggle('open');
    });
    
    // Category filter buttons
    document.querySelectorAll('[data-category]').forEach(btn => {
      btn.addEventListener('click', () => {
        const category = btn.dataset.category;
        this.loadRandomPuzzle({ category });
        
        // Update active state
        document.querySelectorAll('[data-category]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  async loadRandomPuzzle(filters = {}) {
    try {
      this.showLoading();
      
      // Build query string
      const params = new URLSearchParams();
      if (filters.category) params.append('category', filters.category);
      if (filters.difficulty) params.append('difficulty', filters.difficulty);
      
      const response = await this.api.request(`/games/puzzles/random/?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(response.data?.error || 'Failed to load puzzle');
      }
      
      this.currentPuzzle = response.data.puzzle;
      this.userStats = response.data.user_stats || this.userStats;
      
      // Reset state
      this.startTime = Date.now();
      this.attempts = 0;
      this.hintsUsed = 0;
      this.moveHistory = [];
      this.currentMoveIndex = 0;
      this.selectedSquare = null;
      
      // Determine player color from FEN
      const fenParts = this.currentPuzzle.fen.split(' ');
      this.playerColor = fenParts[1] === 'w' ? 'white' : 'black';
      
      // Update UI
      this.updatePuzzleDisplay();
      this.loadPosition(this.currentPuzzle.fen);
      this.updateStatsDisplay();
      this.startTimer();
      
    } catch (error) {
      console.error('Failed to load puzzle:', error);
      
      // Try to load a sample puzzle as fallback
      this.loadSamplePuzzle();
    }
  }

  loadSamplePuzzle() {
    // Fallback sample puzzle when API is unavailable
    this.currentPuzzle = {
      id: 0,
      fen: 'r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
      solution: ['h5f7'],
      title: 'Sample Puzzle',
      description: 'Find checkmate in one move',
      objective: 'White to play and checkmate',
      difficulty: 'beginner',
      category: 'checkmate',
      themes: ['mate_in_1'],
      rating: 800
    };
    
    this.startTime = Date.now();
    this.attempts = 0;
    this.hintsUsed = 0;
    this.moveHistory = [];
    this.currentMoveIndex = 0;
    this.playerColor = 'white';
    
    this.updatePuzzleDisplay();
    this.loadPosition(this.currentPuzzle.fen);
    this.startTimer();
  }

  updatePuzzleDisplay() {
    const puzzle = this.currentPuzzle;
    if (!puzzle) return;
    
    // Update title and info
    const titleEl = document.getElementById('puzzleTitle');
    if (titleEl) titleEl.textContent = puzzle.title || `Puzzle #${puzzle.id}`;
    
    const difficultyEl = document.getElementById('puzzleDifficulty');
    if (difficultyEl) difficultyEl.textContent = puzzle.difficulty || 'Unknown';
    
    const objectiveEl = document.getElementById('puzzleObjective');
    if (objectiveEl) objectiveEl.textContent = puzzle.objective || 'Find the best move';
    
    const descriptionEl = document.getElementById('puzzleDescription');
    if (descriptionEl) descriptionEl.textContent = puzzle.description || '';
    
    const ratingEl = document.getElementById('puzzleRating');
    if (ratingEl) ratingEl.textContent = this.userStats.puzzleRating || puzzle.rating || '--';
    
    const categoryEl = document.getElementById('puzzleCategory');
    if (categoryEl) categoryEl.textContent = puzzle.category || '--';
    
    const attemptsEl = document.getElementById('attempts');
    if (attemptsEl) attemptsEl.textContent = this.attempts;
    
    // Update difficulty badge
    const badge = document.getElementById('difficultyBadge');
    if (badge) {
      const difficulty = (puzzle.difficulty || 'intermediate').toLowerCase();
      badge.className = `difficulty-badge ${difficulty}`;
    }
  }

  updateStatsDisplay() {
    const stats = this.userStats;
    
    const solvedEl = document.getElementById('puzzlesSolved');
    if (solvedEl) solvedEl.textContent = stats.puzzles_solved ?? stats.puzzlesSolved ?? '--';
    
    const accuracyEl = document.getElementById('accuracy');
    if (accuracyEl) accuracyEl.textContent = `${stats.accuracy ?? 0}%`;
    
    const streakEl = document.getElementById('streak');
    if (streakEl) streakEl.textContent = stats.current_streak ?? stats.currentStreak ?? '--';
  }

  loadPosition(fen) {
    const pieces = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };

    const boardPart = fen.split(' ')[0];
    const rows = boardPart.split('/');
    
    // Clear all squares first
    document.querySelectorAll('.square').forEach(sq => {
      sq.innerHTML = '';
      sq.dataset.piece = '';
    });
    
    for (let row = 0; row < 8; row++) {
      let col = 0;
      for (const char of rows[row]) {
        if (isNaN(char)) {
          const square = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
          if (square) {
            const pieceEl = document.createElement('span');
            pieceEl.className = 'piece';
            pieceEl.textContent = pieces[char] || '';
            square.appendChild(pieceEl);
            square.dataset.piece = char;
          }
          col++;
        } else {
          col += parseInt(char);
        }
      }
    }
    
    // Store current FEN
    this.currentFen = fen;
  }

  handleSquareClick(event) {
    const square = event.currentTarget;
    
    if (this.selectedSquare) {
      // Try to make a move
      this.tryMove(this.selectedSquare, square);
      this.clearSelection();
    } else if (square.dataset.piece) {
      // Check if it's player's piece
      const piece = square.dataset.piece;
      const isWhitePiece = piece === piece.toUpperCase();
      
      if ((this.playerColor === 'white' && isWhitePiece) ||
          (this.playerColor === 'black' && !isWhitePiece)) {
        this.selectSquare(square);
      }
    }
  }

  selectSquare(square) {
    this.clearSelection();
    this.selectedSquare = square;
    square.classList.add('selected');
  }

  clearSelection() {
    if (this.selectedSquare) {
      this.selectedSquare.classList.remove('selected');
      this.selectedSquare = null;
    }
    
    document.querySelectorAll('.possible-move').forEach(s => {
      s.classList.remove('possible-move');
    });
  }

  async tryMove(fromSquare, toSquare) {
    this.attempts++;
    document.getElementById('attempts').textContent = this.attempts;
    
    const fromSq = fromSquare.dataset.square;
    const toSq = toSquare.dataset.square;
    const move = `${fromSq}${toSq}`;
    
    try {
      const response = await this.api.request(`/games/puzzles/${this.currentPuzzle.id}/validate/`, {
        method: 'POST',
        body: JSON.stringify({
          move: move,
          current_position: this.currentFen,
          move_index: this.currentMoveIndex
        })
      });
      
      if (response.ok && response.data.correct) {
        // Correct move
        this.executeMove(fromSquare, toSquare);
        this.addMoveToHistory(move, true);
        this.currentMoveIndex = response.data.next_move_index || this.currentMoveIndex + 1;
        
        // Apply opponent's response if any
        if (response.data.opponent_move) {
          setTimeout(() => {
            this.executeOpponentMove(response.data.opponent_move);
            this.addMoveToHistory(response.data.opponent_move, true);
          }, 500);
        }
        
        // Update position
        if (response.data.new_position) {
          this.currentFen = response.data.new_position;
        }
        
        // Check if puzzle is complete
        if (response.data.is_complete) {
          this.completePuzzle(true);
        }
      } else {
        // Incorrect move
        this.addMoveToHistory(move, false);
        this.showStatusMessage('error', 'Incorrect', response.data?.message || "That's not the best move. Try again!");
        this.animateIncorrectMove(toSquare);
      }
    } catch (error) {
      console.error('Move validation failed:', error);
      // Fallback: local validation
      this.validateMoveLocally(fromSquare, toSquare, move);
    }
  }

  validateMoveLocally(fromSquare, toSquare, move) {
    // Local fallback validation when API is unavailable
    if (!this.currentPuzzle?.solution) return;
    
    const expectedMove = this.currentPuzzle.solution[this.currentMoveIndex];
    
    if (move.toLowerCase() === expectedMove?.toLowerCase()) {
      this.executeMove(fromSquare, toSquare);
      this.addMoveToHistory(move, true);
      this.currentMoveIndex++;
      
      // Apply opponent move if exists
      if (this.currentMoveIndex < this.currentPuzzle.solution.length) {
        const oppMove = this.currentPuzzle.solution[this.currentMoveIndex];
        setTimeout(() => {
          this.executeOpponentMoveLocal(oppMove);
          this.addMoveToHistory(oppMove, true);
          this.currentMoveIndex++;
          
          // Check completion
          if (this.currentMoveIndex >= this.currentPuzzle.solution.length) {
            this.completePuzzle(true);
          }
        }, 500);
      } else {
        this.completePuzzle(true);
      }
    } else {
      this.addMoveToHistory(move, false);
      this.showStatusMessage('error', 'Incorrect', "That's not the best move. Try again!");
      this.animateIncorrectMove(toSquare);
    }
  }

  executeMove(fromSquare, toSquare) {
    // Animate and move the piece
    toSquare.innerHTML = fromSquare.innerHTML;
    toSquare.dataset.piece = fromSquare.dataset.piece;
    fromSquare.innerHTML = '';
    fromSquare.dataset.piece = '';
    
    // Visual feedback
    toSquare.classList.add('last-move');
    fromSquare.classList.add('last-move');
    
    setTimeout(() => {
      toSquare.classList.remove('last-move');
      fromSquare.classList.remove('last-move');
    }, 1000);
  }

  executeOpponentMove(uciMove) {
    const fromSq = uciMove.substring(0, 2);
    const toSq = uciMove.substring(2, 4);
    
    const fromSquare = document.querySelector(`[data-square="${fromSq}"]`);
    const toSquare = document.querySelector(`[data-square="${toSq}"]`);
    
    if (fromSquare && toSquare) {
      this.executeMove(fromSquare, toSquare);
    }
  }

  executeOpponentMoveLocal(uciMove) {
    this.executeOpponentMove(uciMove);
  }

  addMoveToHistory(move, correct) {
    this.moveHistory.push({ move, correct });
    this.updateMoveHistoryDisplay();
  }

  updateMoveHistoryDisplay() {
    const historyEl = document.getElementById('moveHistory');
    if (!historyEl) return;
    
    if (this.moveHistory.length === 0) {
      historyEl.innerHTML = '<div class="move-item empty">No moves yet...</div>';
      return;
    }
    
    historyEl.innerHTML = this.moveHistory.map((item, index) => {
      const statusClass = item.correct ? 'current' : '';
      const statusIcon = item.correct ? '✓' : '✗';
      return `<div class="move-item ${statusClass}">
        ${Math.floor(index / 2) + 1}${index % 2 === 0 ? '.' : '...'} ${item.move} ${statusIcon}
      </div>`;
    }).join('');
  }

  async completePuzzle(solved) {
    this.stopTimer();
    const timeSpent = (Date.now() - this.startTime) / 1000;
    
    try {
      const response = await this.api.request(`/games/puzzles/${this.currentPuzzle.id}/complete/`, {
        method: 'POST',
        body: JSON.stringify({
          solved: solved,
          time_spent: timeSpent,
          moves_made: this.moveHistory.map(m => m.move),
          hints_used: this.hintsUsed
        })
      });
      
      if (response.ok) {
        this.userStats = response.data.stats || this.userStats;
        this.updateStatsDisplay();
        
        const ratingChange = response.data.attempt?.rating_change || 0;
        const ratingText = ratingChange >= 0 ? `+${ratingChange}` : `${ratingChange}`;
        
        this.showStatusMessage('success', 'Puzzle Solved! 🎉', 
          `Completed in ${this.attempts} attempt${this.attempts !== 1 ? 's' : ''} and ${Math.round(timeSpent)} seconds. Rating: ${ratingText}`);
      }
    } catch (error) {
      console.error('Failed to record completion:', error);
      this.showStatusMessage('success', 'Puzzle Solved! 🎉',
        `Completed in ${this.attempts} attempt${this.attempts !== 1 ? 's' : ''} and ${Math.round(timeSpent)} seconds.`);
    }
    
    // Update progress
    const progressEl = document.getElementById('progressFill');
    const progressText = document.getElementById('puzzleProgress');
    if (progressEl && progressText) {
      const newProgress = Math.min(100, ((this.userStats.puzzles_solved || 0) % 10) * 10 + 10);
      progressEl.style.width = `${newProgress}%`;
      progressText.textContent = `${newProgress}%`;
    }
  }

  async getHint() {
    this.hintsUsed++;
    
    try {
      const response = await this.api.request(
        `/games/puzzles/${this.currentPuzzle.id}/hint/?move_index=${this.currentMoveIndex}`
      );
      
      if (response.ok) {
        this.showStatusMessage('info', '💡 Hint', response.data.hint);
        
        // Highlight starting square if provided
        if (response.data.starting_square) {
          const square = document.querySelector(`[data-square="${response.data.starting_square}"]`);
          if (square) {
            square.classList.add('hint-highlight');
            setTimeout(() => square.classList.remove('hint-highlight'), 3000);
          }
        }
      }
    } catch (error) {
      // Fallback hint
      const themes = this.currentPuzzle?.themes || [];
      let hint = 'Look for tactical opportunities!';
      
      if (themes.includes('fork')) hint = 'Look for a move that attacks two pieces at once';
      else if (themes.includes('pin')) hint = 'Look for a pinned piece';
      else if (themes.includes('mate_in_1')) hint = 'Can you deliver checkmate?';
      
      this.showStatusMessage('info', '💡 Hint', hint);
    }
  }

  async showSolution() {
    try {
      const response = await this.api.request(`/games/puzzles/${this.currentPuzzle.id}/solution/`);
      
      if (response.ok) {
        const solution = response.data.solution_formatted || response.data.solution;
        const solutionText = Array.isArray(solution) 
          ? solution.map(m => m.san || m).join(' → ')
          : solution;
        
        this.showStatusMessage('info', '📖 Solution', solutionText);
        
        // Mark puzzle as failed
        await this.completePuzzle(false);
      }
    } catch (error) {
      // Fallback
      if (this.currentPuzzle?.solution) {
        this.showStatusMessage('info', '📖 Solution', this.currentPuzzle.solution.join(' → '));
      }
    }
  }

  restartPuzzle() {
    if (!this.currentPuzzle) return;
    
    this.clearSelection();
    this.attempts = 0;
    this.hintsUsed = 0;
    this.moveHistory = [];
    this.currentMoveIndex = 0;
    this.startTime = Date.now();
    
    this.loadPosition(this.currentPuzzle.fen);
    this.updatePuzzleDisplay();
    this.updateMoveHistoryDisplay();
    this.startTimer();
    
    this.hideStatusMessage();
  }

  startTimer() {
    this.stopTimer();
    
    this.timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      
      const timerEl = document.getElementById('timeElapsed');
      if (timerEl) {
        timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
    }, 1000);
  }

  stopTimer() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  showStatusMessage(type, title, description) {
    const overlayEl = document.getElementById('statusOverlay');
    const modalEl = document.getElementById('statusModal');
    const iconEl = document.getElementById('statusIcon');
    const titleEl = document.getElementById('statusTitle');
    const descEl = document.getElementById('statusDescription');
    
    if (!overlayEl || !modalEl) return;
    
    modalEl.className = `status-modal ${type}`;
    
    if (iconEl) {
      if (type === 'success') iconEl.textContent = '🎉';
      else if (type === 'error') iconEl.textContent = '❌';
      else iconEl.textContent = '💡';
    }
    
    if (titleEl) titleEl.textContent = title;
    if (descEl) descEl.textContent = description;
    
    overlayEl.classList.add('show');
  }

  hideStatusMessage() {
    const overlayEl = document.getElementById('statusOverlay');
    if (overlayEl) {
      overlayEl.classList.remove('show');
    }
  }

  showLoading() {
    const objectiveEl = document.getElementById('puzzleObjective');
    if (objectiveEl) {
      objectiveEl.innerHTML = '<span class="loading-spinner"></span> Loading puzzle...';
    }
  }

  animateIncorrectMove(square) {
    square.style.background = 'rgba(239, 68, 68, 0.5)';
    setTimeout(() => {
      square.style.background = '';
    }, 500);
  }

  // Utility: Convert row/col to algebraic notation
  rowColToSquare(row, col) {
    const files = 'abcdefgh';
    const ranks = '87654321';
    return files[col] + ranks[row];
  }
}

// Global filter function
function filterPuzzles(category) {
  console.log('Filtering puzzles by category:', category);
  if (window.puzzleController) {
    window.puzzleController.loadRandomPuzzle({ category });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.puzzleController = new ChessPuzzleController();
});
