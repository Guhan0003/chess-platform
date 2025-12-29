/**
 * Profile Page Controller
 * Manages user profile display and achievements
 */

class ProfileController {
  constructor() {
    this.api = new ChessAPI();
    this.profileData = null;
    this.achievements = null;
  }

  async initialize() {
    console.log('🎯 Initializing Profile Page...');

    try {
      // Check authentication
      if (!this.api.isAuthenticated()) {
        console.log('❌ Not authenticated, redirecting to login');
        window.location.href = '/login/';
        return;
      }

      // Load profile data first
      await this.loadProfileData();
      
      // Auto-check for new achievements silently
      this.checkAchievementsSilently();
      
      // Then load achievements and recent games in parallel
      await Promise.all([
        this.loadAchievements(),
        this.loadRecentGames()
      ]);

      // Setup event listeners
      this.setupEventListeners();

      console.log('✅ Profile Page initialized');
    } catch (error) {
      console.error('❌ Failed to initialize profile:', error);
      this.showError('Failed to load profile data');
    }
  }

  async loadProfileData() {
    console.log('📥 Loading profile data...');

    try {
      const response = await this.api.getUserProfile();

      if (response.ok && response.data) {
        this.profileData = response.data;
        this.displayProfile(this.profileData);
        console.log('✅ Profile loaded:', this.profileData);
      } else {
        throw new Error('Invalid response from profile API');
      }
    } catch (error) {
      console.error('❌ Failed to load profile:', error);
      throw error;
    }
  }

  async loadAchievements() {
    console.log('🏆 Loading achievements...');

    try {
      const response = await this.api.getUserAchievements();

      if (response.ok && response.data) {
        this.achievements = response.data;
        this.displayAchievements(this.achievements);
        console.log('✅ Achievements loaded:', this.achievements);
      } else {
        throw new Error('Invalid response from achievements API');
      }
    } catch (error) {
      console.error('❌ Failed to load achievements:', error);
      // Don't throw - achievements are not critical
      this.displayAchievementsError();
    }
  }

  async loadRecentGames() {
    // Wait for profile data to be loaded first
    if (!this.profileData) {
      console.warn('Profile data not loaded yet, skipping recent games');
      return;
    }

    try {
      const response = await this.api.getUserGames(this.profileData.id, 5);
      console.log('Recent games response:', response);
      
      if (response.ok && response.data) {
        this.displayRecentGames(response.data);
      } else {
        this.displayRecentGamesError();
      }
    } catch (error) {
      console.error('Failed to load recent games:', error);
      this.displayRecentGamesError();
    }
  }

  displayRecentGames(games) {
    const container = document.getElementById('recentGamesList');
    if (!container) return;

    container.innerHTML = '';

    if (!games || games.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: var(--space-xl); color: var(--color-text-muted);">
          <div style="font-size: 2rem; margin-bottom: var(--space-sm);">🎮</div>
          <div>No games played yet</div>
          <div style="font-size: var(--font-size-sm); margin-top: var(--space-xs);">Start playing to see your game history</div>
        </div>
      `;
      return;
    }

    games.forEach(game => {
      const gameEl = document.createElement('div');
      gameEl.className = 'game-item';
      
      const currentUserId = this.profileData.id;
      const isWhite = game.white_player === currentUserId;
      const opponentName = isWhite ? game.black_player_username : game.white_player_username;
      const result = this.getGameResult(game, isWhite);
      
      // Format time control better
      let timeControl = 'Standard';
      if (game.time_control) {
        const tc = game.time_control.toString().toLowerCase();
        if (tc.includes('bullet')) timeControl = '⚡ Bullet';
        else if (tc.includes('blitz')) timeControl = '⚡ Blitz';
        else if (tc.includes('rapid')) timeControl = '⏱️ Rapid';
        else if (tc.includes('classical')) timeControl = '♟️ Classical';
      }
      
      gameEl.innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--space-md); flex: 1;">
          <div style="font-size: 1.5rem;">${result.icon}</div>
          <div style="flex: 1;">
            <div style="font-weight: var(--font-weight-semibold); color: var(--color-text-primary); margin-bottom: 2px;">
              vs ${opponentName || 'Unknown'}
            </div>
            <div style="font-size: var(--font-size-sm); color: var(--color-text-muted);">
              ${timeControl} • ${this.formatDate(game.created_at)}
            </div>
          </div>
          <div class="game-result ${result.class}" style="padding: var(--space-xs) var(--space-sm); border-radius: var(--radius-sm); font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm);">
            ${result.text}
          </div>
        </div>
      `;

      gameEl.style.cursor = 'pointer';
      gameEl.style.padding = 'var(--space-md)';
      gameEl.style.borderRadius = 'var(--radius-md)';
      gameEl.style.transition = 'all var(--transition-normal)';
      
      gameEl.addEventListener('mouseenter', () => {
        gameEl.style.background = 'rgba(255, 255, 255, 0.05)';
      });
      gameEl.addEventListener('mouseleave', () => {
        gameEl.style.background = 'transparent';
      });
      gameEl.addEventListener('click', () => {
        window.location.href = `/play/?game=${game.id}`;
      });

      container.appendChild(gameEl);
    });
  }

  getGameResult(game, isWhite) {
    if (game.status === 'active' || game.status === 'waiting') {
      return { text: 'Active', class: 'in-progress', icon: '⏳' };
    }

    if (!game.winner) {
      return { text: 'Draw', class: 'draw', icon: '🤝' };
    }

    // Check if the current user won
    const playerWon = (isWhite && game.winner === game.white_player) || 
                      (!isWhite && game.winner === game.black_player);
    
    return playerWon 
      ? { text: 'Won', class: 'won', icon: '🏆' }
      : { text: 'Lost', class: 'lost', icon: '💔' };
  }

  displayRecentGamesError() {
    const container = document.getElementById('recentGamesList');
    if (!container) return;
    container.innerHTML = '<div style="text-align: center; padding: var(--space-lg); color: var(--color-error);">Failed to load recent games</div>';
  }

  displayProfile(profile) {
    console.log('📊 Displaying profile data:', profile);

    // Display username
    const usernameEl = document.getElementById('profileUsername');
    if (usernameEl) {
      usernameEl.textContent = profile.username;
    }

    // Display avatar
    const avatarEl = document.getElementById('profileAvatar');
    const avatarTextEl = document.getElementById('avatarText');
    if (avatarEl && avatarTextEl) {
      if (profile.avatar || profile.avatar_url) {
        const avatarUrl = profile.avatar || profile.avatar_url;
        avatarEl.style.backgroundImage = `url(${avatarUrl})`;
        avatarEl.style.backgroundSize = 'cover';
        avatarEl.style.backgroundPosition = 'center';
        avatarTextEl.style.display = 'none';
      } else {
        avatarTextEl.textContent = profile.username.charAt(0).toUpperCase();
        avatarTextEl.style.display = 'flex';
      }
    }

    // Display ratings
    this.displayRating('blitzRating', profile.blitz_rating);
    this.displayRating('rapidRating', profile.rapid_rating);
    this.displayRating('classicalRating', profile.classical_rating);

    // Display peak ratings
    this.displayStat('blitzPeak', `Peak: ${profile.blitz_peak || profile.blitz_rating || 1200}`);
    this.displayStat('rapidPeak', `Peak: ${profile.rapid_peak || profile.rapid_rating || 1200}`);
    this.displayStat('classicalPeak', `Peak: ${profile.classical_peak || profile.classical_rating || 1200}`);

    // Display stats
    this.displayStat('totalGames', profile.total_games || 0);

    // Calculate and display win rate
    const winRate = profile.total_games > 0 
      ? ((profile.games_won / profile.total_games) * 100).toFixed(1)
      : 0;
    this.displayStat('winRate', `${winRate}%`);

    // Display best rating (highest of all time controls)
    const bestRating = Math.max(
      profile.rapid_peak || profile.rapid_rating || 1200,
      profile.blitz_peak || profile.blitz_rating || 1200,
      profile.classical_peak || profile.classical_rating || 1200
    );
    this.displayStat('bestRating', bestRating);

    // Display wins/losses/draws
    this.displayStat('gamesWon', profile.games_won || 0);
    this.displayStat('gamesLost', profile.games_lost || 0);
    this.displayStat('gamesDrawn', profile.games_drawn || 0);

    // Display streak
    this.displayStat('currentStreak', profile.current_win_streak || 0);
    this.displayStat('bestStreak', profile.best_win_streak || 0);

    console.log('✅ Profile displayed successfully');
  }

  displayRating(elementId, rating) {
    const el = document.getElementById(elementId);
    if (el) {
      el.textContent = rating;
    }
  }

  displayStat(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) {
      el.textContent = value;
    }
  }

  displayAchievements(data) {
    console.log('🏆 Displaying achievements:', data);
    
    const container = document.getElementById('achievementsList');
    if (!container) {
      console.warn('⚠️ Achievements container not found');
      return;
    }

    // Clear existing content
    container.innerHTML = '';

    // Handle both direct array and object with achievements property
    const achievements = Array.isArray(data) ? data : (data.achievements || []);

    if (achievements.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: var(--space-xl); color: var(--color-text-muted);">
          No achievements available yet
        </div>
      `;
      return;
    }

    // Display achievements
    achievements.forEach(achievement => {
      const achievementEl = document.createElement('div');
      achievementEl.className = `achievement-item ${achievement.unlocked ? 'unlocked' : 'locked'}`;
      
      achievementEl.innerHTML = `
        <span class="achievement-icon">${achievement.icon}</span>
        <div class="achievement-title">${achievement.name}</div>
        <div class="achievement-description">${achievement.description}</div>
        ${achievement.unlocked 
          ? `<div class="achievement-date">${this.formatDate(achievement.unlocked_at)}</div>` 
          : `<div class="achievement-locked">🔒 Locked</div>`
        }
        <div class="achievement-points">${achievement.points} pts</div>
      `;

      container.appendChild(achievementEl);
    });

    // Display stats if available
    if (data.stats) {
      this.displayAchievementStats(data.stats);
    }

    console.log(`✅ Displayed ${achievements.length} achievements`);
  }

  displayAchievementStats(stats) {
    // You can add achievement stats display here if needed
    console.log('Achievement Stats:', stats);
  }

  displayAchievementsError() {
    const container = document.getElementById('achievementsList');
    if (!container) return;

    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: var(--space-xl); color: var(--color-error);">
        Failed to load achievements
      </div>
    `;
  }

  formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return date.toLocaleDateString();
  }

  async checkAchievementsSilently() {
    try {
      const response = await this.api.checkAchievements();
      if (response.ok) {
        const newlyUnlocked = response.data.newly_unlocked || [];
        if (newlyUnlocked.length > 0) {
          console.log(`🎉 ${newlyUnlocked.length} new achievement(s) unlocked:`, newlyUnlocked);
          // Achievements will be shown when loadAchievements() runs
        }
      }
    } catch (error) {
      console.error('Failed to check achievements:', error);
    }
  }

  setupEventListeners() {
    // Back button
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.href = '/lobby/';
      });
    }

    // Edit profile button (if exists)
    const editBtn = document.getElementById('editProfileBtn');
    if (editBtn) {
      editBtn.addEventListener('click', () => {
        this.openEditModal();
      });
    }
  }

  openEditModal() {
    // Implementation for edit modal
    console.log('Opening edit modal...');
  }

  showError(message) {
    console.error('Error:', message);
    // You can add UI error display here
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  const controller = new ProfileController();
  controller.initialize();

  // Make controller globally accessible for debugging
  window.profileController = controller;
});
