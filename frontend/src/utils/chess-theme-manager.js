/**
 * Chess Theme Manager
 * Handles loading, applying, and managing chess board themes and piece sets
 */

import { 
  BOARD_THEMES, 
  PIECE_SETS, 
  getBoardTheme, 
  getPieceSet, 
  getPieceImageUrl,
  applyBoardTheme,
  DEFAULT_SETTINGS 
} from './theme-config.js';

class ChessThemeManager {
  constructor() {
    this.currentBoardTheme = DEFAULT_SETTINGS.boardTheme;
    this.currentPieceSet = DEFAULT_SETTINGS.pieceSet;
    this.pieceImageCache = new Map();
    this.loadFromStorage();
  }

  /**
   * Load theme settings from localStorage
   */
  loadFromStorage() {
    try {
      const saved = localStorage.getItem('chess_theme_settings');
      if (saved) {
        const settings = JSON.parse(saved);
        this.currentBoardTheme = settings.boardTheme || DEFAULT_SETTINGS.boardTheme;
        this.currentPieceSet = settings.pieceSet || DEFAULT_SETTINGS.pieceSet;
      }
    } catch (e) {
      console.warn('Failed to load theme settings from storage:', e);
    }
  }

  /**
   * Save theme settings to localStorage
   */
  saveToStorage() {
    try {
      localStorage.setItem('chess_theme_settings', JSON.stringify({
        boardTheme: this.currentBoardTheme,
        pieceSet: this.currentPieceSet
      }));
    } catch (e) {
      console.warn('Failed to save theme settings:', e);
    }
  }

  /**
   * Get all available board themes
   */
  getBoardThemes() {
    return BOARD_THEMES;
  }

  /**
   * Get all available piece sets
   */
  getPieceSets() {
    return PIECE_SETS;
  }

  /**
   * Set the board theme
   * @param {string} themeId - Theme ID
   */
  setBoardTheme(themeId) {
    const theme = getBoardTheme(themeId);
    this.currentBoardTheme = theme.id;
    applyBoardTheme(theme);
    this.saveToStorage();
    
    // Dispatch event for any listeners
    window.dispatchEvent(new CustomEvent('boardThemeChanged', { 
      detail: { theme } 
    }));
  }

  /**
   * Set the piece set
   * @param {string} setId - Piece set ID
   */
  setPieceSet(setId) {
    const pieceSet = getPieceSet(setId);
    this.currentPieceSet = pieceSet.id;
    this.saveToStorage();
    
    // Dispatch event for any listeners
    window.dispatchEvent(new CustomEvent('pieceSetChanged', { 
      detail: { pieceSet } 
    }));
  }

  /**
   * Get the current board theme object
   */
  getCurrentBoardTheme() {
    return getBoardTheme(this.currentBoardTheme);
  }

  /**
   * Get the current piece set object
   */
  getCurrentPieceSet() {
    return getPieceSet(this.currentPieceSet);
  }

  /**
   * Check if current piece set uses images
   */
  usesImagePieces() {
    return this.getCurrentPieceSet().folder !== null;
  }

  /**
   * Get piece HTML element (image or unicode)
   * @param {string} piece - FEN piece character (K, Q, R, B, N, P, k, q, r, b, n, p)
   * @returns {HTMLElement} The piece element
   */
  createPieceElement(piece) {
    const pieceEl = document.createElement('div');
    const isWhite = piece === piece.toUpperCase();
    pieceEl.className = `chess-piece ${isWhite ? 'white-piece' : 'black-piece'}`;
    pieceEl.dataset.piece = piece;

    const currentSet = this.getCurrentPieceSet();
    
    if (currentSet.folder) {
      // Use image
      const imageUrl = getPieceImageUrl(currentSet, piece);
      pieceEl.classList.add('piece-image');
      pieceEl.style.backgroundImage = `url('${imageUrl}')`;
      pieceEl.textContent = ''; // Clear text
    } else {
      // Use Unicode
      pieceEl.classList.add('piece-unicode');
      pieceEl.textContent = this.getPieceUnicode(piece);
    }

    return pieceEl;
  }

  /**
   * Get Unicode symbol for a piece
   * @param {string} piece - FEN piece character
   */
  getPieceUnicode(piece) {
    const pieces = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };
    return pieces[piece] || '';
  }

  /**
   * Apply current theme to the page
   */
  applyCurrentTheme() {
    const theme = this.getCurrentBoardTheme();
    applyBoardTheme(theme);
  }

  /**
   * Preload piece images for the current set
   */
  async preloadPieceImages() {
    const currentSet = this.getCurrentPieceSet();
    if (!currentSet.folder) return;

    const pieces = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p'];
    const loadPromises = pieces.map(piece => {
      const url = getPieceImageUrl(currentSet, piece);
      return this.preloadImage(url);
    });

    try {
      await Promise.all(loadPromises);
      console.log(`✅ Piece images preloaded for set: ${currentSet.name}`);
    } catch (e) {
      console.warn('Some piece images failed to load:', e);
    }
  }

  /**
   * Preload a single image
   */
  preloadImage(url) {
    return new Promise((resolve, reject) => {
      if (this.pieceImageCache.has(url)) {
        resolve(this.pieceImageCache.get(url));
        return;
      }

      const img = new Image();
      img.onload = () => {
        this.pieceImageCache.set(url, img);
        resolve(img);
      };
      img.onerror = () => reject(new Error(`Failed to load: ${url}`));
      img.src = url;
    });
  }

  /**
   * Generate preview HTML for a board theme
   */
  generateBoardPreview(theme) {
    return `
      <div class="board-preview" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; width: 60px; height: 60px; border-radius: 4px; overflow: hidden;">
        ${[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map((_, i) => {
          const row = Math.floor(i / 4);
          const col = i % 4;
          const isLight = (row + col) % 2 === 0;
          const color = isLight ? theme.lightColor : theme.darkColor;
          return `<div style="background-color: ${color};"></div>`;
        }).join('')}
      </div>
    `;
  }

  /**
   * Generate preview HTML for a piece set
   */
  generatePiecePreview(pieceSet) {
    if (!pieceSet.folder) {
      // Unicode preview
      return `
        <div class="piece-preview" style="display: flex; gap: 2px; font-size: 18px;">
          <span style="color: white; text-shadow: 0 0 2px black;">♔</span>
          <span style="color: white; text-shadow: 0 0 2px black;">♕</span>
          <span style="color: #333;">♚</span>
          <span style="color: #333;">♛</span>
        </div>
      `;
    }

    // Image preview
    return `
      <div class="piece-preview" style="display: flex; gap: 4px;">
        <img src="/static/images/pieces/${pieceSet.folder}/wK.png" alt="WK" style="width: 24px; height: 24px;" onerror="this.style.display='none'">
        <img src="/static/images/pieces/${pieceSet.folder}/wQ.png" alt="WQ" style="width: 24px; height: 24px;" onerror="this.style.display='none'">
        <img src="/static/images/pieces/${pieceSet.folder}/bK.png" alt="BK" style="width: 24px; height: 24px;" onerror="this.style.display='none'">
        <img src="/static/images/pieces/${pieceSet.folder}/bQ.png" alt="BQ" style="width: 24px; height: 24px;" onerror="this.style.display='none'">
      </div>
    `;
  }
}

// Create singleton instance
const themeManager = new ChessThemeManager();

// Export for use in other modules
export default themeManager;
export { ChessThemeManager };
