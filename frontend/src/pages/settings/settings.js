/**
 * Settings Page Controller
 * Manages user settings and preferences
 */

class SettingsController {
  constructor() {
    this.api = new ChessAPI();
    this.originalSettings = null;
    this.currentSettings = null;
    this.hasChanges = false;

    // Field IDs
    this.fields = [
      'auto_queen_promotion',
      'show_coordinates',
      'highlight_moves',
      'sound_enabled',
      'email_game_invites',
      'email_game_results',
      'push_notifications',
      'allow_challenges',
      'show_online_status',
      'board_theme',
      'piece_set'
    ];
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
      localStorage.setItem('board_theme', changedFields.board_theme);
      console.log('🎨 Board theme applied');
    }

    if ('piece_set' in changedFields) {
      // Update piece set in localStorage
      localStorage.setItem('piece_set', changedFields.piece_set);
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
