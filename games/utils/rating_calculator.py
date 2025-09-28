# games/utils/rating_calculator.py
import math
from typing import Tuple
from django.conf import settings


class ELORatingCalculator:
    """
    Professional ELO rating system for chess games
    Based on standard FIDE ELO calculations with customizations
    """
    
    # K-factors based on rating and game count
    K_FACTORS = {
        'provisional': 40,  # First 30 games
        'below_2100': 20,   # Rating below 2100
        'above_2100': 10,   # Rating 2100 and above
        'blitz': 32,        # Blitz games get higher K-factor
        'rapid': 20,        # Rapid games standard K-factor
        'classical': 16,    # Classical games lower K-factor for stability
    }
    
    # Rating thresholds
    PROVISIONAL_GAMES = 30
    HIGH_RATING_THRESHOLD = 2100
    
    # Maximum rating change per game
    MAX_RATING_CHANGE = 50
    MIN_RATING_CHANGE = 1

    @classmethod
    def calculate_rating_change(
        cls, 
        player_rating: int,
        opponent_rating: int, 
        game_result: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
        time_control: str = 'rapid',
        player_games_count: int = 0,
        is_provisional: bool = False
    ) -> Tuple[int, dict]:
        """
        Calculate rating change for a player after a game
        
        Args:
            player_rating: Current rating of the player
            opponent_rating: Current rating of the opponent
            game_result: Game result (1.0/0.5/0.0)
            time_control: Type of game (blitz/rapid/classical)
            player_games_count: Total games played by player
            is_provisional: Whether player is in provisional period
            
        Returns:
            Tuple of (rating_change, calculation_details)
        """
        
        # Calculate expected score using ELO formula
        expected_score = cls._calculate_expected_score(player_rating, opponent_rating)
        
        # Determine K-factor
        k_factor = cls._get_k_factor(
            player_rating, 
            player_games_count, 
            time_control, 
            is_provisional
        )
        
        # Calculate raw rating change
        raw_change = k_factor * (game_result - expected_score)
        
        # Apply bounds and rounding
        rating_change = cls._apply_rating_change_bounds(raw_change)
        
        # Prepare calculation details
        details = {
            'expected_score': round(expected_score, 3),
            'k_factor': k_factor,
            'raw_change': round(raw_change, 2),
            'rating_change': rating_change,
            'new_rating': player_rating + rating_change,
            'confidence': cls._calculate_confidence(player_games_count)
        }
        
        return rating_change, details

    @classmethod
    def calculate_both_players(
        cls,
        white_rating: int,
        black_rating: int,
        game_result: str,  # '1-0', '0-1', '1/2-1/2'
        time_control: str = 'rapid',
        white_games: int = 0,
        black_games: int = 0
    ) -> Tuple[int, int, dict]:
        """
        Calculate rating changes for both players
        
        Returns:
            Tuple of (white_change, black_change, details)
        """
        
        # Convert result string to numeric values
        if game_result == '1-0':  # White wins
            white_result, black_result = 1.0, 0.0
        elif game_result == '0-1':  # Black wins
            white_result, black_result = 0.0, 1.0
        elif game_result == '1/2-1/2':  # Draw
            white_result, black_result = 0.5, 0.5
        else:
            raise ValueError(f"Invalid game result: {game_result}")
        
        # Calculate changes for both players
        white_change, white_details = cls.calculate_rating_change(
            white_rating, black_rating, white_result, time_control, white_games
        )
        
        black_change, black_details = cls.calculate_rating_change(
            black_rating, white_rating, black_result, time_control, black_games
        )
        
        # Combined details
        combined_details = {
            'white': white_details,
            'black': black_details,
            'game_result': game_result,
            'time_control': time_control,
            'rating_difference': abs(white_rating - black_rating)
        }
        
        return white_change, black_change, combined_details

    @classmethod
    def _calculate_expected_score(cls, player_rating: int, opponent_rating: int) -> float:
        """Calculate expected score using standard ELO formula"""
        rating_difference = opponent_rating - player_rating
        return 1 / (1 + math.pow(10, rating_difference / 400))

    @classmethod
    def _get_k_factor(
        cls, 
        rating: int, 
        games_count: int, 
        time_control: str, 
        is_provisional: bool
    ) -> int:
        """Determine K-factor based on various conditions"""
        
        if is_provisional or games_count < cls.PROVISIONAL_GAMES:
            return cls.K_FACTORS['provisional']
        
        # Time control specific K-factors
        time_control_k = cls.K_FACTORS.get(time_control, cls.K_FACTORS['rapid'])
        
        # Rating based adjustments
        if rating >= cls.HIGH_RATING_THRESHOLD:
            # Reduce K-factor for high-rated players for stability
            return max(time_control_k - 4, cls.K_FACTORS['above_2100'])
        else:
            return time_control_k

    @classmethod
    def _apply_rating_change_bounds(cls, raw_change: float) -> int:
        """Apply minimum and maximum bounds to rating changes"""
        # Round to nearest integer
        change = round(raw_change)
        
        # Apply bounds
        if change > 0:
            change = max(change, cls.MIN_RATING_CHANGE)
            change = min(change, cls.MAX_RATING_CHANGE)
        elif change < 0:
            change = min(change, -cls.MIN_RATING_CHANGE)
            change = max(change, -cls.MAX_RATING_CHANGE)
        
        return change

    @classmethod
    def _calculate_confidence(cls, games_count: int) -> str:
        """Calculate rating confidence based on games played"""
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
    def get_rating_class(cls, rating: int) -> str:
        """Get rating class/title based on rating"""
        if rating < 800:
            return 'Beginner'
        elif rating < 1000:
            return 'Novice'
        elif rating < 1200:
            return 'Amateur'
        elif rating < 1400:
            return 'Intermediate'
        elif rating < 1600:
            return 'Advanced'
        elif rating < 1800:
            return 'Expert'
        elif rating < 2000:
            return 'Master'
        elif rating < 2200:
            return 'International Master'
        elif rating < 2400:
            return 'Grandmaster'
        else:
            return 'Super Grandmaster'

    @classmethod
    def simulate_rating_progression(
        cls, 
        initial_rating: int = 1200, 
        games: int = 100,
        win_rate: float = 0.5,
        time_control: str = 'rapid'
    ) -> list:
        """
        Simulate rating progression over multiple games
        Useful for testing and demonstration
        """
        
        progression = [{'game': 0, 'rating': initial_rating, 'change': 0}]
        current_rating = initial_rating
        
        import random
        
        for game_num in range(1, games + 1):
            # Simulate opponent rating (normal distribution around player rating)
            opponent_rating = max(800, int(random.gauss(current_rating, 200)))
            
            # Simulate game result based on win rate
            rand_result = random.random()
            if rand_result < win_rate - 0.1:  # Win
                result = 1.0
            elif rand_result < win_rate + 0.1:  # Draw  
                result = 0.5
            else:  # Loss
                result = 0.0
            
            # Calculate rating change
            change, _ = cls.calculate_rating_change(
                current_rating, 
                opponent_rating, 
                result, 
                time_control, 
                game_num - 1
            )
            
            current_rating += change
            
            progression.append({
                'game': game_num,
                'rating': current_rating,
                'change': change,
                'opponent_rating': opponent_rating,
                'result': result
            })
        
        return progression


# Skill Level Management
class SkillLevelManager:
    """
    Professional skill level management for new players
    Maps user-selected skill levels to appropriate initial ratings
    """
    
    SKILL_LEVELS = {
        'beginner': {
            'name': 'Beginner',
            'rating': 400,
            'description': 'New to chess or learning basic rules',
            'characteristics': [
                'Learning piece movements',
                'Understanding basic rules',
                'Occasional blunders'
            ]
        },
        'intermediate': {
            'name': 'Intermediate', 
            'rating': 800,
            'description': 'Know basic tactics and openings',
            'characteristics': [
                'Knows common tactics',
                'Basic opening principles',
                'Understands piece values'
            ]
        },
        'advanced': {
            'name': 'Advanced',
            'rating': 1200, 
            'description': 'Understand strategy and complex tactics',
            'characteristics': [
                'Strategic thinking',
                'Complex tactical patterns',
                'Good endgame knowledge'
            ]
        },
        'expert': {
            'name': 'Expert',
            'rating': 1600,
            'description': 'Strong player with deep understanding', 
            'characteristics': [
                'Advanced strategy',
                'Deep opening knowledge', 
                'Strong endgame technique'
            ]
        }
    }
    
    @classmethod
    def get_initial_ratings(cls, skill_level: str) -> dict:
        """
        Get initial ratings for all time controls based on skill level
        
        Args:
            skill_level: Selected skill level ('beginner', 'intermediate', 'advanced', 'expert')
            
        Returns:
            Dictionary with ratings for all time controls
        """
        if skill_level not in cls.SKILL_LEVELS:
            raise ValueError(f"Invalid skill level: {skill_level}")
        
        base_rating = cls.SKILL_LEVELS[skill_level]['rating']
        
        # Slight variations for different time controls
        # Faster time controls tend to be slightly lower for beginners
        rating_adjustments = {
            'beginner': {'blitz': -50, 'rapid': 0, 'classical': +25},
            'intermediate': {'blitz': -25, 'rapid': 0, 'classical': +25},
            'advanced': {'blitz': -25, 'rapid': 0, 'classical': +50},
            'expert': {'blitz': -50, 'rapid': 0, 'classical': +75}
        }
        
        adjustments = rating_adjustments[skill_level]
        
        return {
            'blitz_rating': max(100, base_rating + adjustments['blitz']),
            'rapid_rating': base_rating + adjustments['rapid'],
            'classical_rating': base_rating + adjustments['classical'],
            'blitz_peak': max(100, base_rating + adjustments['blitz']),
            'rapid_peak': base_rating + adjustments['rapid'],
            'classical_peak': base_rating + adjustments['classical']
        }
    
    @classmethod
    def validate_skill_level(cls, skill_level: str) -> bool:
        """Validate if skill level is valid"""
        return skill_level in cls.SKILL_LEVELS
    
    @classmethod
    def get_skill_level_info(cls, skill_level: str) -> dict:
        """Get detailed information about a skill level"""
        if skill_level not in cls.SKILL_LEVELS:
            return None
        return cls.SKILL_LEVELS[skill_level].copy()
    
    @classmethod
    def get_all_skill_levels(cls) -> list:
        """Get all available skill levels"""
        return [
            {
                'key': key,
                **info
            }
            for key, info in cls.SKILL_LEVELS.items()
        ]


def initialize_user_ratings(user, skill_level: str):
    """
    Initialize a new user's ratings based on their selected skill level
    
    Args:
        user: CustomUser instance
        skill_level: Selected skill level string
        
    Returns:
        Dictionary with applied ratings
    """
    if not SkillLevelManager.validate_skill_level(skill_level):
        raise ValueError(f"Invalid skill level: {skill_level}")
    
    # Get initial ratings for all time controls
    ratings = SkillLevelManager.get_initial_ratings(skill_level)
    
    # Apply ratings to user
    for field, value in ratings.items():
        setattr(user, field, value)
    
    # Store the initial skill level for reference
    user.initial_skill_level = skill_level
    
    # Save the user
    user.save()
    
    return ratings


# Convenience functions for common calculations
def calculate_game_rating_changes(white_user, black_user, game_result, time_control='rapid'):
    """
    Calculate rating changes for a completed game
    
    Args:
        white_user: CustomUser instance for white player
        black_user: CustomUser instance for black player  
        game_result: '1-0', '0-1', or '1/2-1/2'
        time_control: 'blitz', 'rapid', or 'classical'
    
    Returns:
        Tuple of (white_change, black_change, details)
    """
    
    white_rating = white_user.get_rating(time_control)
    black_rating = black_user.get_rating(time_control)
    
    white_games = getattr(white_user, f'{time_control}_games', 0)
    black_games = getattr(black_user, f'{time_control}_games', 0)
    
    return ELORatingCalculator.calculate_both_players(
        white_rating=white_rating,
        black_rating=black_rating,
        game_result=game_result,
        time_control=time_control,
        white_games=white_games,
        black_games=black_games
    )


def update_player_ratings(white_user, black_user, game_result, time_control='rapid', game_instance=None):
    """
    Update both players' ratings and create rating history records
    
    Args:
        white_user: CustomUser instance for white player
        black_user: CustomUser instance for black player
        game_result: '1-0', '0-1', or '1/2-1/2' 
        time_control: 'blitz', 'rapid', or 'classical'
        game_instance: Game model instance for history tracking
    """
    
    from accounts.models import RatingHistory
    
    # Calculate rating changes
    white_change, black_change, details = calculate_game_rating_changes(
        white_user, black_user, game_result, time_control
    )
    
    # Update white player
    white_old_rating = white_user.get_rating(time_control)
    white_new_rating = white_old_rating + white_change
    setattr(white_user, f'{time_control}_rating', white_new_rating)
    
    # Update black player  
    black_old_rating = black_user.get_rating(time_control)
    black_new_rating = black_old_rating + black_change
    setattr(black_user, f'{time_control}_rating', black_new_rating)
    
    # Update game statistics
    white_result = 'win' if game_result == '1-0' else ('draw' if game_result == '1/2-1/2' else 'loss')
    black_result = 'win' if game_result == '0-1' else ('draw' if game_result == '1/2-1/2' else 'loss')
    
    white_user.update_game_stats(white_result, time_control)
    black_user.update_game_stats(black_result, time_control)
    
    # Save both users
    white_user.save()
    black_user.save()
    
    # Create rating history records
    RatingHistory.objects.create(
        user=white_user,
        time_control=time_control,
        old_rating=white_old_rating,
        new_rating=white_new_rating,
        rating_change=white_change,
        game=game_instance,
        reason='game_result'
    )
    
    RatingHistory.objects.create(
        user=black_user,
        time_control=time_control,
        old_rating=black_old_rating,
        new_rating=black_new_rating,
        rating_change=black_change,
        game=game_instance,
        reason='game_result'
    )
    
    return {
        'white_change': white_change,
        'black_change': black_change,
        'white_new_rating': white_new_rating,
        'black_new_rating': black_new_rating,
        'details': details
    }
