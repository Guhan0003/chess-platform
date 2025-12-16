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

      // Load profile data and achievements
      await Promise.all([
        this.loadProfileData(),
        this.loadAchievements()
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

  displayProfile(profile) {
    // Display username
    const usernameEl = document.getElementById('userName');
    if (usernameEl) {
      usernameEl.textContent = profile.username;
    }

    // Display avatar
    const avatarEl = document.getElementById('userAvatar');
    if (avatarEl) {
      if (profile.avatar_url) {
        avatarEl.innerHTML = `<img src="${profile.avatar_url}" alt="${profile.username}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
      } else {
        avatarEl.textContent = profile.username.charAt(0).toUpperCase();
      }
    }

    // Display ratings
    this.displayRating('blitzRating', profile.blitz_rating);
    this.displayRating('rapidRating', profile.rapid_rating);
    this.displayRating('classicalRating', profile.classical_rating);

    // Display stats
    this.displayStat('totalGames', profile.total_games);
    this.displayStat('gamesWon', profile.games_won);
    this.displayStat('gamesDrawn', profile.games_drawn);
    this.displayStat('gamesLost', profile.games_lost);

    // Calculate and display win rate
    const winRate = profile.total_games > 0 
      ? ((profile.games_won / profile.total_games) * 100).toFixed(1)
      : 0;
    this.displayStat('winRate', `${winRate}%`);

    // Display streak
    this.displayStat('currentStreak', profile.current_win_streak);
    this.displayStat('bestStreak', profile.best_win_streak);
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
    const container = document.getElementById('achievementsList');
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    if (!data.achievements || data.achievements.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: var(--space-xl); color: var(--color-text-muted);">
          No achievements available yet
        </div>
      `;
      return;
    }

    // Display achievements
    data.achievements.forEach(achievement => {
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

    // Display stats
    this.displayAchievementStats(data.stats);
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

  setupEventListeners() {
    // Back button
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.history.back();
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
