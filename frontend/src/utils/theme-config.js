/**
 * Chess Theme Configuration
 * Defines available board themes and piece sets
 */

// Board themes configuration
export const BOARD_THEMES = [
  {
    id: 'classic',
    name: 'Classic Green',
    lightColor: '#f0d9b5',
    darkColor: '#769656',
    hasTexture: false,
    preview: ['#f0d9b5', '#769656']
  },
  {
    id: 'blue',
    name: 'Ocean Blue',
    lightColor: '#dee3e6',
    darkColor: '#5d8aa8',
    hasTexture: false,
    preview: ['#dee3e6', '#5d8aa8']
  },
  {
    id: 'brown',
    name: 'Classic Brown',
    lightColor: '#f0dab5',
    darkColor: '#b58863',
    hasTexture: false,
    preview: ['#f0dab5', '#b58863']
  },
  {
    id: 'gray',
    name: 'Minimalist Gray',
    lightColor: '#ffffff',
    darkColor: '#9e9e9e',
    hasTexture: false,
    preview: ['#ffffff', '#9e9e9e']
  },
  {
    id: 'purple',
    name: 'Royal Purple',
    lightColor: '#e8e0f0',
    darkColor: '#7c4daf',
    hasTexture: false,
    preview: ['#e8e0f0', '#7c4daf']
  },
  {
    id: 'wood',
    name: 'Wooden',
    lightColor: '#deb887',
    darkColor: '#8b4513',
    hasTexture: true,
    preview: ['#deb887', '#8b4513']
  },
  {
    id: 'marble',
    name: 'Marble',
    lightColor: '#f5f5f5',
    darkColor: '#505050',
    hasTexture: true,
    preview: ['#f5f5f5', '#505050']
  },
  {
    id: 'tournament',
    name: 'Tournament',
    lightColor: '#eeeed2',
    darkColor: '#769656',
    hasTexture: false,
    preview: ['#eeeed2', '#769656']
  }
];

// Piece sets configuration
export const PIECE_SETS = [
  {
    id: 'unicode',
    name: 'Unicode (Default)',
    folder: null, // Uses Unicode characters
    description: 'Simple Unicode chess symbols'
  },
  {
    id: 'classic',
    name: 'Classic',
    folder: 'classic',
    description: 'Traditional Staunton-style pieces'
  },
  {
    id: 'modern',
    name: 'Modern',
    folder: 'modern',
    description: 'Sleek contemporary design'
  },
  {
    id: 'staunton',
    name: 'Staunton',
    folder: 'staunton',
    description: 'Official tournament style'
  },
  {
    id: 'neo',
    name: 'Neo',
    folder: 'neo',
    description: 'Minimalist modern pieces'
  },
  {
    id: 'alpha',
    name: 'Alpha',
    folder: 'alpha',
    description: 'Clean vector design'
  },
  {
    id: 'cburnett',
    name: 'CBurnett',
    folder: 'cburnett',
    description: 'Popular classic style'
  }
];

// Export default theme settings
export const DEFAULT_SETTINGS = {
  boardTheme: 'classic',
  pieceSet: 'unicode'
};

// Get theme by ID
export function getBoardTheme(themeId) {
  return BOARD_THEMES.find(t => t.id === themeId) || BOARD_THEMES[0];
}

// Get piece set by ID
export function getPieceSet(setId) {
  return PIECE_SETS.find(s => s.id === setId) || PIECE_SETS[0];
}

// Get piece image URL
export function getPieceImageUrl(pieceSet, piece) {
  if (!pieceSet.folder) return null; // Unicode fallback
  
  // Convert FEN character to filename format
  // 'K' -> 'wK', 'k' -> 'bK', 'P' -> 'wP', 'p' -> 'bP', etc.
  const isWhite = piece === piece.toUpperCase();
  const color = isWhite ? 'w' : 'b';
  const pieceChar = piece.toUpperCase();
  const filename = `${color}${pieceChar}.png`;
  
  return `/static/images/pieces/${pieceSet.folder}/${filename}`;
}

// CSS variable names for board theme
export function applyBoardTheme(theme) {
  const root = document.documentElement;
  root.style.setProperty('--board-light-color', theme.lightColor);
  root.style.setProperty('--board-dark-color', theme.darkColor);
  
  if (theme.hasTexture) {
    root.style.setProperty('--board-light-texture', `url('/static/images/boards/${theme.id}/light.png')`);
    root.style.setProperty('--board-dark-texture', `url('/static/images/boards/${theme.id}/dark.png')`);
    root.style.setProperty('--board-use-texture', '1');
  } else {
    root.style.setProperty('--board-use-texture', '0');
  }
}
