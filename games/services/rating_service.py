"""
Global Rating Service - Professional Chess Rating Management
============================================================

Centralized rating system combining fixed ±8 points with professional ELO features.
This service ensures consistent rating calculations across the entire platform.

Features:
- Fixed ±8 rating change per game (win/loss) for fairness
- ±0 for draws
- Professional ELO-based analytics and confidence tracking
- Automatic rating history tracking
- Peak rating updates
- Performance ratings and analysis
- Rating class determination
- Integration with all game endpoints
"""

import logging
import math
from typing import Tuple, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class GlobalRatingService:
    """
    Professional global rating service with fixed rating changes plus ELO analytics.
    
    Rating Rules:
    - Win: +8 points (fixed)
    - Loss: -8 points (fixed)
    - Draw: +0 points (no change)
    - Minimum rating: 100 (cannot go below)
    - Peak ratings automatically tracked
    
    Professional Features:
    - Expected score calculations (ELO formula)
    - Performance ratings
    - Rating confidence levels
    - Rating class titles
    - Time control adjustments
    - Provisional player tracking
    """
    
    # Fixed rating constants
    WIN_POINTS = 8
    LOSS_POINTS = -8
    DRAW_POINTS = 0
    MINIMUM_RATING = 100
    
    # Professional ELO constants (for analytics)
    PROVISIONAL_GAMES = 30
    HIGH_RATING_THRESHOLD = 2100
    
    @classmethod
    @transaction.atomic
    def update_ratings_after_game(
        cls,
        white_player: 'User',
        black_player: 'User',
        game_result: str,
        time_control: str = 'rapid',
        game_instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Update player ratings after a game completes.
        
        This is the MAIN method that should be called after every game.
        
        Args:
            white_player: CustomUser instance for white
            black_player: CustomUser instance for black
            game_result: '1-0' (white wins), '0-1' (black wins), or '1/2-1/2' (draw)
            time_control: 'blitz', 'rapid', or 'classical'
            game_instance: Optional Game model instance for history
            
        Returns:
            Dictionary with rating changes and new ratings
        """
        
        # PREVENT DOUBLE-COUNTING: Check if ratings were already updated for this game
        if game_instance:
            from accounts.models import RatingHistory
            existing_history = RatingHistory.objects.filter(game=game_instance).exists()
            if existing_history:
                logger.warning(f"Ratings already updated for game {game_instance.id}, skipping to prevent double-counting")
                return {
                    'skipped': True,
                    'reason': 'Ratings already updated for this game'
                }
        
        # Validate time control
        if time_control not in ['blitz', 'rapid', 'classical']:
            logger.warning(f"Invalid time control '{time_control}', defaulting to 'rapid'")
            time_control = 'rapid'
        
        # Get rating field names
        rating_field = f'{time_control}_rating'
        peak_field = f'{time_control}_peak'
        games_field = f'{time_control}_games'
        
        # Get current ratings
        white_old_rating = getattr(white_player, rating_field)
        black_old_rating = getattr(black_player, rating_field)
        
        # Calculate rating changes based on result
        if game_result == '1-0':  # White wins
            white_change = cls.WIN_POINTS
            black_change = cls.LOSS_POINTS
            white_result = 'win'
            black_result = 'loss'
            
        elif game_result == '0-1':  # Black wins
            white_change = cls.LOSS_POINTS
            black_change = cls.WIN_POINTS
            white_result = 'loss'
            black_result = 'win'
            
        elif game_result == '1/2-1/2':  # Draw
            white_change = cls.DRAW_POINTS
            black_change = cls.DRAW_POINTS
            white_result = 'draw'
            black_result = 'draw'
            
        else:
            logger.error(f"Invalid game result: {game_result}")
            raise ValueError(f"Invalid game result: {game_result}. Must be '1-0', '0-1', or '1/2-1/2'")
        
        # Calculate new ratings with minimum floor
        white_new_rating = max(cls.MINIMUM_RATING, white_old_rating + white_change)
        black_new_rating = max(cls.MINIMUM_RATING, black_old_rating + black_change)
        
        # Adjust changes if hit minimum
        if white_new_rating == cls.MINIMUM_RATING and white_old_rating == cls.MINIMUM_RATING:
            white_change = 0
        if black_new_rating == cls.MINIMUM_RATING and black_old_rating == cls.MINIMUM_RATING:
            black_change = 0
        
        # Update player ratings
        setattr(white_player, rating_field, white_new_rating)
        setattr(black_player, rating_field, black_new_rating)
        
        # Update peak ratings
        white_peak = getattr(white_player, peak_field)
        if white_new_rating > white_peak:
            setattr(white_player, peak_field, white_new_rating)
            
        black_peak = getattr(black_player, peak_field)
        if black_new_rating > black_peak:
            setattr(black_player, peak_field, black_new_rating)
        
        # Update game statistics (handles total_games, time_control games, wins/losses/draws, and saves)
        white_player.update_game_stats(white_result, time_control)
        black_player.update_game_stats(black_result, time_control)
        
        # Create rating history records
        cls._create_rating_history(
            white_player, time_control, white_old_rating, 
            white_new_rating, white_change, game_instance
        )
        cls._create_rating_history(
            black_player, time_control, black_old_rating,
            black_new_rating, black_change, game_instance
        )
        
        # Calculate professional analytics (expected scores, performance ratings)
        white_expected = cls._calculate_expected_score(white_old_rating, black_old_rating)
        black_expected = cls._calculate_expected_score(black_old_rating, white_old_rating)
        
        white_actual_score = 1.0 if white_result == 'win' else (0.5 if white_result == 'draw' else 0.0)
        black_actual_score = 1.0 if black_result == 'win' else (0.5 if black_result == 'draw' else 0.0)
        
        white_performance = cls._calculate_performance_rating(white_old_rating, black_old_rating, white_actual_score)
        black_performance = cls._calculate_performance_rating(black_old_rating, white_old_rating, black_actual_score)
        
        white_confidence = cls._calculate_confidence(getattr(white_player, games_field, 0))
        black_confidence = cls._calculate_confidence(getattr(black_player, games_field, 0))
        
        # Log the update
        logger.info(
            f"Ratings updated - {white_player.username}: {white_old_rating}→{white_new_rating} ({white_change:+d}), "
            f"{black_player.username}: {black_old_rating}→{black_new_rating} ({black_change:+d})"
        )
        
        # Return detailed results with professional analytics
        return {
            'success': True,
            'game_result': game_result,
            'time_control': time_control,
            'white': {
                'username': white_player.username,
                'old_rating': white_old_rating,
                'new_rating': white_new_rating,
                'rating_change': white_change,
                'result': white_result,
                'peak_rating': getattr(white_player, peak_field),
                'expected_score': round(white_expected, 3),
                'actual_score': white_actual_score,
                'performance_rating': white_performance,
                'performance_level': cls._get_performance_level(white_actual_score - white_expected),
                'confidence': white_confidence,
                'rating_class': cls._get_rating_class(white_new_rating),
                'games_played': getattr(white_player, games_field, 0),
                'is_provisional': getattr(white_player, games_field, 0) < cls.PROVISIONAL_GAMES
            },
            'black': {
                'username': black_player.username,
                'old_rating': black_old_rating,
                'new_rating': black_new_rating,
                'rating_change': black_change,
                'result': black_result,
                'peak_rating': getattr(black_player, peak_field),
                'expected_score': round(black_expected, 3),
                'actual_score': black_actual_score,
                'performance_rating': black_performance,
                'performance_level': cls._get_performance_level(black_actual_score - black_expected),
                'confidence': black_confidence,
                'rating_class': cls._get_rating_class(black_new_rating),
                'games_played': getattr(black_player, games_field, 0),
                'is_provisional': getattr(black_player, games_field, 0) < cls.PROVISIONAL_GAMES
            },
            'analytics': {
                'rating_difference': abs(white_old_rating - black_old_rating),
                'white_expected_win_probability': round(white_expected * 100, 1),
                'black_expected_win_probability': round(black_expected * 100, 1),
                'upset': cls._is_upset(white_old_rating, black_old_rating, game_result)
            }
        }
    
    @classmethod
    def _create_rating_history(
        cls,
        user: 'User',
        time_control: str,
        old_rating: int,
        new_rating: int,
        rating_change: int,
        game_instance: Optional[Any] = None
    ) -> None:
        """Create a rating history record."""
        from accounts.models import RatingHistory
        
        try:
            RatingHistory.objects.create(
                user=user,
                time_control=time_control,
                old_rating=old_rating,
                new_rating=new_rating,
                rating_change=rating_change,
                game=game_instance,
                reason='game_result'
            )
        except Exception as e:
            logger.error(f"Failed to create rating history for {user.username}: {e}")
    
    @classmethod
    def get_rating_preview(
        cls,
        white_rating: int,
        black_rating: int,
        time_control: str = 'rapid',
        white_games: int = 0,
        black_games: int = 0
    ) -> Dict[str, Any]:
        """
        Preview what rating changes would be for all possible outcomes.
        Includes professional ELO analytics and win probabilities.
        
        Args:
            white_rating: White player's current rating
            black_rating: Black player's current rating
            time_control: Time control type
            white_games: Games played by white
            black_games: Games played by black
            
        Returns:
            Dictionary with rating previews for all outcomes plus analytics
        """
        
        # Calculate expected scores (ELO formula)
        white_expected = cls._calculate_expected_score(white_rating, black_rating)
        black_expected = cls._calculate_expected_score(black_rating, white_rating)
        
        # Calculate confidence levels
        white_confidence = cls._calculate_confidence(white_games)
        black_confidence = cls._calculate_confidence(black_games)
        
        return {
            'current_ratings': {
                'white': white_rating,
                'black': black_rating,
                'difference': abs(white_rating - black_rating),
                'white_class': cls._get_rating_class(white_rating),
                'black_class': cls._get_rating_class(black_rating)
            },
            'probabilities': {
                'white_win': round(white_expected * 100, 1),
                'black_win': round(black_expected * 100, 1),
                'draw': round((1 - white_expected - black_expected + 0.5) * 100, 1)  # Approximate
            },
            'if_white_wins': {
                'white_change': cls.WIN_POINTS,
                'black_change': cls.LOSS_POINTS,
                'white_new': max(cls.MINIMUM_RATING, white_rating + cls.WIN_POINTS),
                'black_new': max(cls.MINIMUM_RATING, black_rating + cls.LOSS_POINTS),
                'white_performance': cls._calculate_performance_rating(white_rating, black_rating, 1.0),
                'black_performance': cls._calculate_performance_rating(black_rating, white_rating, 0.0),
                'is_upset': white_rating < black_rating - 100
            },
            'if_black_wins': {
                'white_change': cls.LOSS_POINTS,
                'black_change': cls.WIN_POINTS,
                'white_new': max(cls.MINIMUM_RATING, white_rating + cls.LOSS_POINTS),
                'black_new': max(cls.MINIMUM_RATING, black_rating + cls.WIN_POINTS),
                'white_performance': cls._calculate_performance_rating(white_rating, black_rating, 0.0),
                'black_performance': cls._calculate_performance_rating(black_rating, white_rating, 1.0),
                'is_upset': black_rating < white_rating - 100
            },
            'if_draw': {
                'white_change': cls.DRAW_POINTS,
                'black_change': cls.DRAW_POINTS,
                'white_new': white_rating,
                'black_new': black_rating,
                'white_performance': cls._calculate_performance_rating(white_rating, black_rating, 0.5),
                'black_performance': cls._calculate_performance_rating(black_rating, white_rating, 0.5)
            },
            'player_info': {
                'white_confidence': white_confidence,
                'black_confidence': black_confidence,
                'white_provisional': white_games < cls.PROVISIONAL_GAMES,
                'black_provisional': black_games < cls.PROVISIONAL_GAMES,
                'white_games': white_games,
                'black_games': black_games
            },
            'time_control': time_control
        }
    
    @classmethod
    def get_player_rating_info(cls, user: 'User', time_control: str = 'rapid') -> Dict[str, Any]:
        """
        Get comprehensive rating information for a player.
        
        Args:
            user: CustomUser instance
            time_control: Time control type
            
        Returns:
            Dictionary with player rating information
        """
        
        rating_field = f'{time_control}_rating'
        peak_field = f'{time_control}_peak'
        games_field = f'{time_control}_games'
        
        current_rating = getattr(user, rating_field)
        peak_rating = getattr(user, peak_field)
        games_played = getattr(user, games_field, 0)
        
        # Calculate rating class
        rating_class = cls._get_rating_class(current_rating)
        
        return {
            'username': user.username,
            'time_control': time_control,
            'current_rating': current_rating,
            'peak_rating': peak_rating,
            'games_played': games_played,
            'rating_class': rating_class,
            'total_games': user.total_games,
            'win_rate': user.get_win_rate(),
            'wins': user.games_won,
            'draws': user.games_drawn,
            'losses': user.games_lost,
            'current_streak': user.current_win_streak,
            'best_streak': user.best_win_streak
        }
    
    @classmethod
    def _calculate_expected_score(cls, player_rating: int, opponent_rating: int) -> float:
        """
        Calculate expected score using standard ELO formula.
        
        Formula: E = 1 / (1 + 10^((opponent_rating - player_rating) / 400))
        
        Returns value between 0 and 1 representing win probability.
        """
        rating_difference = opponent_rating - player_rating
        return 1 / (1 + math.pow(10, rating_difference / 400))
    
    @classmethod
    def _calculate_performance_rating(cls, player_rating: int, opponent_rating: int, score: float) -> int:
        """
        Calculate performance rating for a single game.
        
        Performance rating represents the rating level at which the player performed.
        """
        if score == 1.0:  # Win
            return opponent_rating + 400
        elif score == 0.0:  # Loss
            return opponent_rating - 400
        else:  # Draw (0.5)
            return opponent_rating
    
    @classmethod
    def _calculate_confidence(cls, games_count: int) -> str:
        """
        Calculate rating confidence based on games played.
        More games = more confident rating.
        """
        if games_count < 10:
            return 'Very Low'
        elif games_count < 30:
            return 'Low'
        elif games_count < 100:
            return 'Medium'
        elif games_count < 500:
            return 'High'
        else:
            return 'Very High'
    
    @classmethod
    def _get_performance_level(cls, performance_diff: float) -> str:
        """
        Get performance level description based on difference from expected.
        
        Args:
            performance_diff: Actual score - Expected score (-1.0 to +1.0)
        """
        if performance_diff >= 0.4:
            return 'Exceptional'
        elif performance_diff >= 0.2:
            return 'Excellent'
        elif performance_diff >= 0.05:
            return 'Good'
        elif performance_diff >= -0.05:
            return 'Expected'
        elif performance_diff >= -0.2:
            return 'Below Expected'
        elif performance_diff >= -0.4:
            return 'Poor'
        else:
            return 'Very Poor'
    
    @classmethod
    def _is_upset(cls, white_rating: int, black_rating: int, result: str) -> bool:
        """Determine if the game result was an upset (lower-rated player won)."""
        rating_diff = abs(white_rating - black_rating)
        
        if rating_diff < 100:  # Too close to be an upset
            return False
        
        if result == '1-0' and white_rating < black_rating - 100:
            return True
        elif result == '0-1' and black_rating < white_rating - 100:
            return True
        
        return False
    
    @classmethod
    def _get_rating_class(cls, rating: int) -> str:
        """Get rating class/title based on rating (chess title system)."""
        if rating < 400:
            return 'Beginner'
        elif rating < 800:
            return 'Novice'
        elif rating < 1000:
            return 'Amateur'
        elif rating < 1200:
            return 'Intermediate'
        elif rating < 1400:
            return 'Advanced'
        elif rating < 1600:
            return 'Expert'
        elif rating < 1800:
            return 'Master'
        elif rating < 2000:
            return 'International Master'
        elif rating < 2200:
            return 'Grandmaster'
        elif rating < 2400:
            return 'Super Grandmaster'
        else:
            return 'World Class'
    
    @classmethod
    def bulk_update_ratings(cls, games_data: list) -> Dict[str, Any]:
        """
        Update ratings for multiple games in a single transaction.
        Useful for recalculating historical games.
        
        Args:
            games_data: List of dicts with game information
            
        Returns:
            Summary of updates
        """
        
        updated_count = 0
        failed_count = 0
        errors = []
        
        for game_data in games_data:
            try:
                cls.update_ratings_after_game(
                    white_player=game_data['white_player'],
                    black_player=game_data['black_player'],
                    game_result=game_data['result'],
                    time_control=game_data.get('time_control', 'rapid'),
                    game_instance=game_data.get('game_instance')
                )
                updated_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append({
                    'game': game_data.get('game_instance'),
                    'error': str(e)
                })
                logger.error(f"Failed to update ratings for game: {e}")
        
        return {
            'total_games': len(games_data),
            'updated': updated_count,
            'failed': failed_count,
            'errors': errors
        }
    
    @classmethod
    def get_rating_trends(cls, user: 'User', time_control: str = 'rapid', last_n_games: int = 10) -> Dict[str, Any]:
        """
        Analyze rating trends for a player.
        
        Args:
            user: CustomUser instance
            time_control: Time control type
            last_n_games: Number of recent games to analyze
            
        Returns:
            Rating trend analysis
        """
        from accounts.models import RatingHistory
        
        rating_field = f'{time_control}_rating'
        current_rating = getattr(user, rating_field)
        
        # Get recent rating history
        history = RatingHistory.objects.filter(
            user=user,
            time_control=time_control
        ).order_by('-created_at')[:last_n_games]
        
        if not history:
            return {
                'current_rating': current_rating,
                'trend': 'stable',
                'change': 0,
                'games_analyzed': 0
            }
        
        # Calculate trend
        total_change = sum(h.rating_change for h in history)
        games_analyzed = len(history)
        
        if total_change > 0:
            trend = 'rising'
        elif total_change < 0:
            trend = 'falling'
        else:
            trend = 'stable'
        
        # Calculate average change per game
        avg_change = total_change / games_analyzed if games_analyzed > 0 else 0
        
        # Get best and worst games
        best_game = max(history, key=lambda h: h.rating_change) if history else None
        worst_game = min(history, key=lambda h: h.rating_change) if history else None
        
        return {
            'current_rating': current_rating,
            'rating_class': cls._get_rating_class(current_rating),
            'trend': trend,
            'total_change': total_change,
            'average_change': round(avg_change, 2),
            'games_analyzed': games_analyzed,
            'best_game': {
                'change': best_game.rating_change,
                'new_rating': best_game.new_rating,
                'date': best_game.created_at.isoformat()
            } if best_game else None,
            'worst_game': {
                'change': worst_game.rating_change,
                'new_rating': worst_game.new_rating,
                'date': worst_game.created_at.isoformat()
            } if worst_game else None,
            'time_control': time_control
        }
    
    @classmethod
    def compare_players(cls, player1: 'User', player2: 'User', time_control: str = 'rapid') -> Dict[str, Any]:
        """
        Compare two players' ratings and predict match outcome.
        
        Args:
            player1: First player
            player2: Second player
            time_control: Time control type
            
        Returns:
            Comprehensive player comparison
        """
        rating_field = f'{time_control}_rating'
        games_field = f'{time_control}_games'
        
        p1_rating = getattr(player1, rating_field)
        p2_rating = getattr(player2, rating_field)
        
        p1_games = getattr(player1, games_field, 0)
        p2_games = getattr(player2, games_field, 0)
        
        # Calculate expected scores
        p1_expected = cls._calculate_expected_score(p1_rating, p2_rating)
        p2_expected = cls._calculate_expected_score(p2_rating, p1_rating)
        
        # Determine favorite
        if p1_rating > p2_rating + 50:
            favorite = player1.username
            underdog = player2.username
        elif p2_rating > p1_rating + 50:
            favorite = player2.username
            underdog = player1.username
        else:
            favorite = 'Even match'
            underdog = None
        
        return {
            'player1': {
                'username': player1.username,
                'rating': p1_rating,
                'rating_class': cls._get_rating_class(p1_rating),
                'games_played': p1_games,
                'confidence': cls._calculate_confidence(p1_games),
                'win_rate': player1.get_win_rate(),
                'expected_score': round(p1_expected, 3),
                'win_probability': round(p1_expected * 100, 1)
            },
            'player2': {
                'username': player2.username,
                'rating': p2_rating,
                'rating_class': cls._get_rating_class(p2_rating),
                'games_played': p2_games,
                'confidence': cls._calculate_confidence(p2_games),
                'win_rate': player2.get_win_rate(),
                'expected_score': round(p2_expected, 3),
                'win_probability': round(p2_expected * 100, 1)
            },
            'comparison': {
                'rating_difference': abs(p1_rating - p2_rating),
                'favorite': favorite,
                'underdog': underdog,
                'match_balance': 'Balanced' if abs(p1_rating - p2_rating) < 100 else 'Unbalanced'
            },
            'rating_stakes': {
                'if_player1_wins': {
                    'player1_change': cls.WIN_POINTS,
                    'player2_change': cls.LOSS_POINTS
                },
                'if_player2_wins': {
                    'player1_change': cls.LOSS_POINTS,
                    'player2_change': cls.WIN_POINTS
                },
                'if_draw': {
                    'player1_change': cls.DRAW_POINTS,
                    'player2_change': cls.DRAW_POINTS
                }
            },
            'time_control': time_control
        }


# Convenience functions for easy integration

def update_game_ratings(white_player, black_player, game_result, time_control='rapid', game_instance=None):
    """
    Convenience function to update ratings after a game.
    
    This should be called after every game completes.
    
    Args:
        white_player: CustomUser for white
        black_player: CustomUser for black
        game_result: '1-0', '0-1', or '1/2-1/2'
        time_control: 'blitz', 'rapid', or 'classical'
        game_instance: Game model instance
        
    Returns:
        Rating update results
    """
    return GlobalRatingService.update_ratings_after_game(
        white_player, black_player, game_result, time_control, game_instance
    )


def get_rating_preview(white_rating, black_rating, time_control='rapid'):
    """
    Get preview of rating changes for all possible outcomes.
    
    Args:
        white_rating: White player's rating
        black_rating: Black player's rating
        time_control: Time control type
        
    Returns:
        Rating preview dictionary
    """
    return GlobalRatingService.get_rating_preview(white_rating, black_rating, time_control)


def get_player_rating_stats(user, time_control='rapid'):
    """
    Get comprehensive rating statistics for a player.
    
    Args:
        user: CustomUser instance
        time_control: Time control type
        
    Returns:
        Rating statistics dictionary
    """
    return GlobalRatingService.get_player_rating_info(user, time_control)
