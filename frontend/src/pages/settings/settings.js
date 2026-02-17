/**
 * Settings Page Controller
 * Manages user settings and preferences
 */

// Board theme configurations
const BOARD_THEMES = [
  { id: 'classic', name: 'Classic', lightColor: '#f0d9b5', darkColor: '#769656' },
  { id: 'blue', name: 'Ocean', lightColor: '#dee3e6', darkColor: '#5d8aa8' },
  { id: 'brown', name: 'Brown', lightColor: '#f0dab5', darkColor: '#b58863' },
  { id: 'gray', name: 'Gray', lightColor: '#ffffff', darkColor: '#9e9e9e' },
  { id: 'purple', name: 'Purple', lightColor: '#e8e0f0', darkColor: '#7c4daf' },
  { id: 'tournament', name: 'Tournament', lightColor: '#eeeed2', darkColor: '#769656' },
  { id: 'wood', name: 'Wood', lightColor: '#deb887', darkColor: '#8b4513' },
  { id: 'marble', name: 'Marble', lightColor: '#f5f5f5', darkColor: '#505050' }
];

// Piece set configurations
const PIECE_SETS = [
  { id: 'unicode', name: 'Unicode', folder: null, description: 'Text symbols' },
  { id: 'classic', name: 'Classic', folder: 'classic', description: 'Traditional' },
  { id: 'modern', name: 'Modern', folder: 'modern', description: 'Contemporary' },
  { id: 'staunton', name: 'Staunton', folder: 'staunton', description: 'Tournament' },
  { id: 'neo', name: 'Neo', folder: 'neo', description: 'Minimalist' },
  { id: 'alpha', name: 'Alpha', folder: 'alpha', description: 'Clean vector' },
  { id: 'cburnett', name: 'CBurnett', folder: 'cburnett', description: 'Popular style' }
];

class SettingsController {
  constructor() {
    this.api = new ChessAPI();
    this.originalSettings = null;
    this.currentSettings = null;
    this.hasChanges = false;

    // Field IDs (excluding board_theme and piece_set which are handled separately)
    this.fields = [
      'auto_queen_promotion',
      'show_coordinates',
      'highlight_moves',
      'sound_enabled',
      'email_game_invites',
      'email_game_results',
      'push_notifications',
      'allow_challenges',
      'show_online_status'
    ];
    
    // Theme selections (handled by grid UI)
    this.selectedBoardTheme = 'classic';
    this.selectedPieceSet = 'unicode';
  }

  async initialize() {
    console.log('🎯 Initializing Settings Page...');

    try {
      // Check authentication
      if (!this.api.isAuthenticated()) {
        console.log('❌ Not authenticated, redirecting to login');
        window.location.href = '/login/';
        return;
      }

      // Load current settings
      await this.loadSettings();

      // Setup theme grids
      this.setupBoardThemeGrid();
      this.setupPieceSetGrid();
      this.updatePreviewBoard();

      // Setup event listeners
      this.setupEventListeners();

      console.log('✅ Settings Page initialized');
    } catch (error) {
      console.error('❌ Failed to initialize settings:', error);
      this.showMessage('Failed to load settings', 'error');
    }
  }

  async loadSettings() {
    console.log('📥 Loading user settings...');

    try {
      const response = await this.api.request('/auth/settings/');

      if (response.ok && response.data.settings) {
        this.originalSettings = { ...response.data.settings };
        this.currentSettings = { ...response.data.settings };

        // Load theme settings from server or localStorage
        this.selectedBoardTheme = this.currentSettings.board_theme || localStorage.getItem('chess_board_theme') || 'classic';
        this.selectedPieceSet = this.currentSettings.piece_set || localStorage.getItem('chess_piece_set') || 'unicode';

        // Populate form fields
        this.populateForm(this.currentSettings);

        console.log('✅ Settings loaded:', this.currentSettings);
      } else {
        throw new Error('Invalid response from settings API');
      }
    } catch (error) {
      console.error('❌ Failed to load settings:', error);
      throw error;
    }
  }

  populateForm(settings) {
    this.fields.forEach(field => {
      const element = document.getElementById(field);
      if (element) {
        if (element.type === 'checkbox') {
          element.checked = settings[field];
        } else {
          element.value = settings[field];
        }
      }
    });
  }

  setupEventListeners() {
    // Back button navigation
    const backButton = document.querySelector('.back-btn');
    if (backButton) {
      backButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (this.hasChanges) {
          if (confirm('You have unsaved changes. Are you sure you want to leave?')) {
            window.location.href = '/lobby/';
          }
        } else {
          window.location.href = '/lobby/';
        }
      });
    }

    // Track changes on all inputs
    this.fields.forEach(field => {
      const element = document.getElementById(field);
      if (element) {
        element.addEventListener('change', () => {
          this.onFieldChange(field);
        });
      }
    });

    // Save button
    const saveButton = document.getElementById('saveButton');
    if (saveButton) {
      saveButton.addEventListener('click', () => this.saveSettings());
    }

    // Cancel button
    const cancelButton = document.getElementById('cancelButton');
    if (cancelButton) {
      cancelButton.addEventListener('click', () => this.cancelChanges());
    }

    // Reset button
    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
      resetButton.addEventListener('click', () => this.resetToDefaults());
    }

    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', (e) => {
      if (this.hasChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    });
  }

  onFieldChange(field) {
    const element = document.getElementById(field);
    if (!element) return;

    // Update current settings
    if (element.type === 'checkbox') {
      this.currentSettings[field] = element.checked;
    } else {
      this.currentSettings[field] = element.value;
    }

    // Check if there are changes
    this.checkForChanges();

    console.log(`📝 Setting changed: ${field} = ${this.currentSettings[field]}`);
  }

  checkForChanges() {
    this.hasChanges = false;

    for (const field of this.fields) {
      if (this.currentSettings[field] !== this.originalSettings[field]) {
        this.hasChanges = true;
        break;
      }
    }

    // Update save button state
    const saveButton = document.getElementById('saveButton');
    if (saveButton) {
      if (this.hasChanges) {
        saveButton.classList.add('has-changes');
        saveButton.textContent = '💾 Save Changes *';
      } else {
        saveButton.classList.remove('has-changes');
        saveButton.textContent = '💾 Save Changes';
      }
    }
  }

  async saveSettings() {
    console.log('💾 Saving settings...');

    const saveButton = document.getElementById('saveButton');
    if (saveButton) {
      saveButton.disabled = true;
      saveButton.textContent = '⏳ Saving...';
    }

    try {
      // Send only changed fields
      const changedFields = {};
      this.fields.forEach(field => {
        if (this.currentSettings[field] !== this.originalSettings[field]) {
          changedFields[field] = this.currentSettings[field];
        }
      });

      if (Object.keys(changedFields).length === 0) {
        this.showMessage('No changes to save', 'success');
        return;
      }

      const response = await this.api.request('/auth/settings/update/', {
        method: 'PATCH',
        body: JSON.stringify(changedFields)
      });

      if (response.ok) {
        // Update original settings
        this.originalSettings = { ...this.currentSettings };
        this.hasChanges = false;

        this.showMessage(
          `✅ Settings saved! Updated: ${response.data.updated_fields.join(', ')}`,
          'success'
        );

        console.log('✅ Settings saved successfully:', response.data);

        // Apply settings immediately if they affect the current page
        this.applySettings(changedFields);
      } else {
        throw new Error(response.data?.error || 'Failed to save settings');
      }
    } catch (error) {
      console.error('❌ Failed to save settings:', error);
      this.showMessage('Failed to save settings: ' + error.message, 'error');
    } finally {
      if (saveButton) {
        saveButton.disabled = false;
        saveButton.textContent = '💾 Save Changes';
      }
    }
  }

  cancelChanges() {
    if (!this.hasChanges) {
      // Navigate back to previous page or lobby
      window.history.back();
      return;
    }

    if (confirm('Discard all unsaved changes?')) {
      // Restore original settings
      this.currentSettings = { ...this.originalSettings };
      this.populateForm(this.currentSettings);
      this.hasChanges = false;
      this.checkForChanges();

      this.showMessage('Changes discarded', 'success');
      console.log('↩️ Changes cancelled');
    }
  }

  async resetToDefaults() {
    if (!confirm('Reset all settings to default values? This cannot be undone.')) {
      return;
    }

    console.log('🔄 Resetting settings to defaults...');

    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
      resetButton.disabled = true;
      resetButton.textContent = '⏳ Resetting...';
    }

    try {
      const response = await this.api.request('/auth/settings/reset/', {
        method: 'POST'
      });

      if (response.ok) {
        // Update settings
        this.originalSettings = { ...response.data.settings };
        this.currentSettings = { ...response.data.settings };
        this.hasChanges = false;

        // Populate form with defaults
        this.populateForm(this.currentSettings);

        this.showMessage('Settings reset to defaults', 'success');
        console.log('✅ Settings reset successfully');
      } else {
        throw new Error(response.data?.error || 'Failed to reset settings');
      }
    } catch (error) {
      console.error('❌ Failed to reset settings:', error);
      this.showMessage('Failed to reset settings: ' + error.message, 'error');
    } finally {
      if (resetButton) {
        resetButton.disabled = false;
        resetButton.textContent = '🔄 Reset to Defaults';
      }
    }
  }

  // ===========================================
  // BOARD THEME & PIECE SET GRID
  // ===========================================

  setupBoardThemeGrid() {
    const grid = document.getElementById('boardThemeGrid');
    if (!grid) return;

    grid.innerHTML = BOARD_THEMES.map(theme => `
      <div class="theme-option ${theme.id === this.selectedBoardTheme ? 'selected' : ''}" 
           data-theme-id="${theme.id}">
        <div class="board-mini-preview">
          ${this.generateMiniBoard(theme.lightColor, theme.darkColor)}
        </div>
        <span class="theme-label">${theme.name}</span>
      </div>
    `).join('');

    // Add click handlers
    grid.querySelectorAll('.theme-option').forEach(option => {
      option.addEventListener('click', () => {
        this.selectBoardTheme(option.dataset.themeId);
      });
    });
  }

  setupPieceSetGrid() {
    const grid = document.getElementById('pieceSetGrid');
    if (!grid) return;

    grid.innerHTML = PIECE_SETS.map(set => `
      <div class="piece-set-option ${set.id === this.selectedPieceSet ? 'selected' : ''}" 
           data-set-id="${set.id}">
        <div class="piece-preview">
          ${this.generatePiecePreview(set)}
        </div>
        <span class="set-label">${set.name}</span>
      </div>
    `).join('');

    // Add click handlers
    grid.querySelectorAll('.piece-set-option').forEach(option => {
      option.addEventListener('click', () => {
        this.selectPieceSet(option.dataset.setId);
      });
    });
  }

  generateMiniBoard(lightColor, darkColor) {
    let html = '';
    for (let i = 0; i < 16; i++) {
      const row = Math.floor(i / 4);
      const col = i % 4;
      const isLight = (row + col) % 2 === 0;
      const color = isLight ? lightColor : darkColor;
      html += `<div class="sq" style="background-color: ${color};"></div>`;
    }
    return html;
  }

  generatePiecePreview(set) {
    if (!set.folder) {
      // Unicode preview
      return `
        <span class="unicode-white">♔</span>
        <span class="unicode-white">♕</span>
        <span class="unicode-black">♚</span>
        <span class="unicode-black">♛</span>
      `;
    }
    // Image preview
    return `
      <img src="/static/images/pieces/${set.folder}/wK.png" alt="WK" 
           onerror="this.outerHTML='<span class=\\'unicode-white\\'>♔</span>'">
      <img src="/static/images/pieces/${set.folder}/wQ.png" alt="WQ"
           onerror="this.outerHTML='<span class=\\'unicode-white\\'>♕</span>'">
      <img src="/static/images/pieces/${set.folder}/bK.png" alt="BK"
           onerror="this.outerHTML='<span class=\\'unicode-black\\'>♚</span>'">
      <img src="/static/images/pieces/${set.folder}/bQ.png" alt="BQ"
           onerror="this.outerHTML='<span class=\\'unicode-black\\'>♛</span>'">
    `;
  }

  selectBoardTheme(themeId) {
    this.selectedBoardTheme = themeId;
    
    // Update grid selection
    document.querySelectorAll('#boardThemeGrid .theme-option').forEach(opt => {
      opt.classList.toggle('selected', opt.dataset.themeId === themeId);
    });

    // Update current settings
    this.currentSettings.board_theme = themeId;
    this.hasChanges = this.checkForChanges();
    
    // Update preview and CSS variables
    this.updatePreviewBoard();
    this.applyBoardThemeCSS(themeId);
    
    console.log('🎨 Board theme selected:', themeId);
  }

  selectPieceSet(setId) {
    this.selectedPieceSet = setId;
    
    // Update grid selection
    document.querySelectorAll('#pieceSetGrid .piece-set-option').forEach(opt => {
      opt.classList.toggle('selected', opt.dataset.setId === setId);
    });

    // Update current settings
    this.currentSettings.piece_set = setId;
    this.hasChanges = this.checkForChanges();
    
    // Update preview
    this.updatePreviewBoard();
    
    console.log('♟️ Piece set selected:', setId);
  }

  updatePreviewBoard() {
    const preview = document.getElementById('previewBoard');
    if (!preview) return;

    const theme = BOARD_THEMES.find(t => t.id === this.selectedBoardTheme) || BOARD_THEMES[0];
    const pieceSet = PIECE_SETS.find(s => s.id === this.selectedPieceSet) || PIECE_SETS[0];

    // 4x4 preview with some pieces
    const previewPieces = [
      { pos: 0, piece: 'r', color: 'black' },
      { pos: 1, piece: 'n', color: 'black' },
      { pos: 2, piece: 'b', color: 'black' },
      { pos: 3, piece: 'q', color: 'black' },
      { pos: 4, piece: 'p', color: 'black' },
      { pos: 5, piece: 'p', color: 'black' },
      { pos: 6, piece: 'p', color: 'black' },
      { pos: 7, piece: 'p', color: 'black' },
      { pos: 8, piece: 'P', color: 'white' },
      { pos: 9, piece: 'P', color: 'white' },
      { pos: 10, piece: 'P', color: 'white' },
      { pos: 11, piece: 'P', color: 'white' },
      { pos: 12, piece: 'R', color: 'white' },
      { pos: 13, piece: 'N', color: 'white' },
      { pos: 14, piece: 'B', color: 'white' },
      { pos: 15, piece: 'Q', color: 'white' }
    ];

    let html = '';
    for (let i = 0; i < 16; i++) {
      const row = Math.floor(i / 4);
      const col = i % 4;
      const isLight = (row + col) % 2 === 0;
      const bgColor = isLight ? theme.lightColor : theme.darkColor;
      const pieceInfo = previewPieces.find(p => p.pos === i);
      
      html += `<div class="preview-square ${isLight ? 'light' : 'dark'}" style="background-color: ${bgColor};">`;
      
      if (pieceInfo) {
        if (pieceSet.folder) {
          // Image piece
          const prefix = pieceInfo.color === 'white' ? 'w' : 'b';
          const pieceLetter = pieceInfo.piece.toUpperCase();
          html += `<div class="preview-piece piece-img" 
                        style="background-image: url('/static/images/pieces/${pieceSet.folder}/${prefix}${pieceLetter}.png');"
                        onerror="this.textContent='${this.getPieceUnicode(pieceInfo.piece)}'"></div>`;
        } else {
          // Unicode piece
          html += `<span class="preview-piece ${pieceInfo.color}">${this.getPieceUnicode(pieceInfo.piece)}</span>`;
        }
      }
      
      html += '</div>';
    }

    preview.innerHTML = html;
  }

  getPieceUnicode(piece) {
    const pieces = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };
    return pieces[piece] || pieces[piece.toLowerCase()] || '';
  }

  applyBoardThemeCSS(themeId) {
    const theme = BOARD_THEMES.find(t => t.id === themeId);
    if (!theme) return;

    const root = document.documentElement;
    root.style.setProperty('--board-light-color', theme.lightColor);
    root.style.setProperty('--board-dark-color', theme.darkColor);
  }

  checkForChanges() {
    if (!this.originalSettings || !this.currentSettings) return false;
    
    // Check regular fields
    for (const field of this.fields) {
      if (this.originalSettings[field] !== this.currentSettings[field]) {
        return true;
      }
    }
    
    // Check theme settings
    if (this.originalSettings.board_theme !== this.currentSettings.board_theme) return true;
    if (this.originalSettings.piece_set !== this.currentSettings.piece_set) return true;
    
    return false;
  }

  applySettings(changedFields) {
    // Apply settings that can be immediately applied
    // For example, sound effects, board theme, etc.
    
    if ('sound_enabled' in changedFields) {
      // Update sound preference in localStorage or global settings
      localStorage.setItem('sound_enabled', changedFields.sound_enabled);
      console.log('🔊 Sound settings applied');
    }

    if ('board_theme' in changedFields) {
      // Update board theme in localStorage
      localStorage.setItem('chess_board_theme', changedFields.board_theme);
      this.applyBoardThemeCSS(changedFields.board_theme);
      console.log('🎨 Board theme applied');
    }

    if ('piece_set' in changedFields) {
      // Update piece set in localStorage
      localStorage.setItem('chess_piece_set', changedFields.piece_set);
      console.log('♟️ Piece set applied');
    }
  }

  showMessage(message, type = 'success') {
    const messageBox = document.getElementById('messageBox');
    if (!messageBox) return;

    messageBox.textContent = message;
    messageBox.className = `message ${type} show`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
      messageBox.classList.remove('show');
    }, 5000);
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  const controller = new SettingsController();
  controller.initialize();

  // Make controller globally accessible for debugging
  window.settingsController = controller;
});
