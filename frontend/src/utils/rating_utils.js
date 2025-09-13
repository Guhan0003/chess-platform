/**
 * Chess Platform - Frontend Rating Utilities
 * JavaScript utilities for rating display and calculations
 */

class RatingUtils {
  /**
   * Get rating class/title based on rating
   */
  static getRatingClass(rating) {
    if (rating < 800) return 'Beginner';
    if (rating < 1000) return 'Novice';
    if (rating < 1200) return 'Amateur';
    if (rating < 1400) return 'Intermediate';
    if (rating < 1600) return 'Advanced';
    if (rating < 1800) return 'Expert';
    if (rating < 2000) return 'Master';
    if (rating < 2200) return 'International Master';
    if (rating < 2400) return 'Grandmaster';
    return 'Super Grandmaster';
  }

  /**
   * Get rating class color
   */
  static getRatingColor(rating) {
    if (rating < 1000) return '#8b5cf6'; // Purple
    if (rating < 1200) return '#06b6d4'; // Cyan
    if (rating < 1400) return '#10b981'; // Green
    if (rating < 1600) return '#f59e0b'; // Amber
    if (rating < 1800) return '#ef4444'; // Red
    if (rating < 2000) return '#ec4899'; // Pink
    if (rating < 2200) return '#8b5cf6'; // Purple
    if (rating < 2400) return '#f59e0b'; // Gold
    return '#dc2626'; // Dark Red
  }

  /**
   * Format rating change with proper sign and color
   */
  static formatRatingChange(change) {
    if (change > 0) {
      return {
        text: `+${change}`,
        color: 'var(--color-success)',
        class: 'rating-increase'
      };
    } else if (change < 0) {
      return {
        text: `${change}`,
        color: 'var(--color-error)',
        class: 'rating-decrease'
      };
    } else {
      return {
        text: '0',
        color: 'var(--color-text-muted)',
        class: 'rating-unchanged'
      };
    }
  }

  /**
   * Calculate expected score for rating display
   * This is for frontend display only - actual calculations are done on backend
   */
  static calculateExpectedScore(playerRating, opponentRating) {
    const ratingDifference = opponentRating - playerRating;
    return 1 / (1 + Math.pow(10, ratingDifference / 400));
  }

  /**
   * Get confidence level based on games played
   */
  static getConfidenceLevel(gamesCount) {
    if (gamesCount < 10) return { level: 'Very Low', color: '#ef4444' };
    if (gamesCount < 30) return { level: 'Low', color: '#f59e0b' };
    if (gamesCount < 100) return { level: 'Medium', color: '#10b981' };
    if (gamesCount < 500) return { level: 'High', color: '#06b6d4' };
    return { level: 'Very High', color: '#8b5cf6' };
  }

  /**
   * Format rating with appropriate styling
   */
  static formatRating(rating, options = {}) {
    const {
      showClass = true,
      showColor = true,
      abbreviated = false
    } = options;

    const ratingClass = this.getRatingClass(rating);
    const color = this.getRatingColor(rating);

    const result = {
      rating: rating,
      class: ratingClass,
      color: color,
      display: rating.toString()
    };

    if (abbreviated) {
      result.classAbbr = this.getAbbreviatedClass(ratingClass);
    }

    return result;
  }

  /**
   * Get abbreviated rating class
   */
  static getAbbreviatedClass(ratingClass) {
    const abbreviations = {
      'Beginner': 'BEG',
      'Novice': 'NOV',
      'Amateur': 'AM',
      'Intermediate': 'INT',
      'Advanced': 'ADV',
      'Expert': 'EXP',
      'Master': 'M',
      'International Master': 'IM',
      'Grandmaster': 'GM',
      'Super Grandmaster': 'SGM'
    };
    return abbreviations[ratingClass] || 'UNK';
  }

  /**
   * Create rating badge HTML
   */
  static createRatingBadge(rating, options = {}) {
    const {
      size = 'medium',
      showClass = false,
      className = ''
    } = options;

    const ratingInfo = this.formatRating(rating, options);
    const sizeClass = `rating-badge--${size}`;
    
    return `
      <span class="rating-badge ${sizeClass} ${className}" 
            style="background: linear-gradient(135deg, ${ratingInfo.color}20, ${ratingInfo.color}10); 
                   border: 1px solid ${ratingInfo.color}40; 
                   color: ${ratingInfo.color};">
        ${ratingInfo.display}
        ${showClass ? `<small class="rating-class">${ratingInfo.classAbbr || ratingInfo.class}</small>` : ''}
      </span>
    `;
  }

  /**
   * Calculate win rate percentage
   */
  static calculateWinRate(wins, total) {
    if (total === 0) return 0;
    return Math.round((wins / total) * 100 * 10) / 10; // Round to 1 decimal
  }

  /**
   * Format win rate with styling
   */
  static formatWinRate(winRate) {
    let color = 'var(--color-text-muted)';
    
    if (winRate >= 70) color = 'var(--color-success)';
    else if (winRate >= 55) color = 'var(--color-accent-primary)';
    else if (winRate >= 45) color = 'var(--color-warning)';
    else if (winRate < 35) color = 'var(--color-error)';

    return {
      percentage: winRate,
      display: `${winRate}%`,
      color: color
    };
  }

  /**
   * Simulate rating change for preview (frontend only)
   * Note: Actual rating calculations happen on the backend
   */
  static simulateRatingChange(playerRating, opponentRating, gameResult, timeControl = 'rapid') {
    // This is a simplified simulation for UI preview only
    const expectedScore = this.calculateExpectedScore(playerRating, opponentRating);
    
    // Simplified K-factor
    let kFactor = 20;
    if (timeControl === 'blitz') kFactor = 32;
    else if (timeControl === 'classical') kFactor = 16;
    
    const rawChange = kFactor * (gameResult - expectedScore);
    const change = Math.round(Math.max(-50, Math.min(50, rawChange)));
    
    return {
      change: change,
      newRating: playerRating + change,
      expectedScore: Math.round(expectedScore * 1000) / 1000
    };
  }

  /**
   * Get time control display name
   */
  static getTimeControlDisplay(timeControl) {
    const displays = {
      'bullet': { name: 'Bullet', icon: '⚡', color: '#ef4444' },
      'blitz': { name: 'Blitz', icon: '🔥', color: '#f59e0b' },
      'rapid': { name: 'Rapid', icon: '🏃', color: '#10b981' },
      'classical': { name: 'Classical', icon: '🏛️', color: '#06b6d4' }
    };
    return displays[timeControl] || { name: timeControl, icon: '♟️', color: 'var(--color-accent-primary)' };
  }

  /**
   * Format game result for display
   */
  static formatGameResult(result, userColor) {
    const resultMap = {
      '1-0': { white: 'Win', black: 'Loss', color: { white: 'success', black: 'error' } },
      '0-1': { white: 'Loss', black: 'Win', color: { white: 'error', black: 'success' } },
      '1/2-1/2': { white: 'Draw', black: 'Draw', color: { white: 'warning', black: 'warning' } }
    };

    const resultInfo = resultMap[result];
    if (!resultInfo) return { text: 'Unknown', color: 'muted' };

    return {
      text: resultInfo[userColor],
      color: `var(--color-${resultInfo.color[userColor]})`
    };
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RatingUtils;
}

// Make available globally
window.RatingUtils = RatingUtils;
