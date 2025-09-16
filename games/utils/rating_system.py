"""
Chess Rating Integration System
==============================

Integrates the ELO rating calculator with the chess engine system:
- Real-time rating calculations during games
- Performance-based engine adjustments
- Rating tracking and analysis
- Integration with timer system for time-based ratings
- Comprehensive rating history and statistics
"""

from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json

from .timer_manager import TimerManager

logger = logging.getLogger(__name__)


class RatingIntegration:
    """
    Integration of rating calculations with chess engine.
    
    Features:
    - Real-time rating updates during games
    - Engine strength adjustment based on rating difference
    - Performance analysis and rating predictions
    - Time control specific ratings
    - Professional tournament rating management
    """
    
    # Rating-based engine adjustments
    ENGINE_ADJUSTMENTS = {
        'rating_difference_thresholds': {
            'massive': 400,     # 400+ rating difference
            'large': 200,       # 200-399 rating difference  
            'moderate': 100,    # 100-199 rating difference
            'small': 50,        # 50-99 rating difference
            'minimal': 0        # 0-49 rating difference
        },
        'strength_modifiers': {
            'massive': {'depth': -2, 'time': 0.6, 'randomness': 0.15},
            'large': {'depth': -1, 'time': 0.75, 'randomness': 0.1},
            'moderate': {'depth': 0, 'time': 0.9, 'randomness': 0.05},
            'small': {'depth': 0, 'time': 1.0, 'randomness': 0.02},
            'minimal': {'depth': 0, 'time': 1.0, 'randomness': 0.0}
        }
    }
    
    # Performance rating thresholds
    PERFORMANCE_THRESHOLDS = {
        'exceptional': 2.0,    # 2+ standard deviations above expected
        'excellent': 1.5,      # 1.5+ standard deviations above expected
        'good': 0.5,           # Above expected performance
        'expected': 0.0,       # Meeting expectations
        'below': -0.5,         # Below expected performance
        'poor': -1.5,          # Well below expectations
        'terrible': -2.0       # Significantly below expectations
    }
    
    def __init__(self):
        """Initialize professional rating integration."""
        self.current_game_data = None
        self.rating_calculator = None
        self.timer_manager = None
        
        # Import rating calculator
        try:
            from .rating_calculator import ELORatingCalculator
            self.rating_calculator = ELORatingCalculator
            logger.info("Professional rating calculator loaded successfully")
            
        except ImportError as e:
            logger.error(f"Failed to load rating calculator: {e}")
            self.rating_calculator = None
        
        # Performance tracking
        self.game_performance_data = {}
        
    def initialize_game_rating_tracking(
        self, 
        white_rating: int, 
        black_rating: int, 
        time_control: str = 'rapid',
        white_games_count: int = 0,
        black_games_count: int = 0
    ) -> Dict[str, Any]:
        """
        Initialize rating tracking for a new game.
        
        Args:
            white_rating: White player's current rating
            black_rating: Black player's current rating
            time_control: Time control format
            white_games_count: Total games played by white
            black_games_count: Total games played by black
            
        Returns:
            Game rating initialization data
        """
        if not self.rating_calculator:
            logger.warning("Rating calculator not available")
            return {}
        
        self.current_game_data = {
            'white_rating': white_rating,
            'black_rating': black_rating,
            'time_control': time_control,
            'white_games_count': white_games_count,
            'black_games_count': black_games_count,
            'rating_difference': abs(white_rating - black_rating),
            'stronger_player': 'white' if white_rating > black_rating else 'black',
            'game_start_time': datetime.now(),
            'expected_scores': {}
        }
        
        # Calculate expected scores
        white_expected = self.rating_calculator._calculate_expected_score(white_rating, black_rating)
        black_expected = self.rating_calculator._calculate_expected_score(black_rating, white_rating)
        
        self.current_game_data['expected_scores'] = {
            'white': white_expected,
            'black': black_expected
        }
        
        # Initialize timer manager with appropriate time control
        self.timer_manager = TimerManager.create_timer_for_rating(
            max(white_rating, black_rating)
        )
        
        logger.info(f"Game rating tracking initialized: {white_rating} vs {black_rating} ({time_control})")
        
        return {
            'rating_difference': self.current_game_data['rating_difference'],
            'expected_scores': self.current_game_data['expected_scores'],
            'stronger_player': self.current_game_data['stronger_player'],
            'engine_adjustments': self.get_engine_adjustments(),
            'timer_state': self.timer_manager.get_timer_state() if self.timer_manager else None
        }
    
    def get_engine_adjustments(self) -> Dict[str, Any]:
        """
        Get engine strength adjustments based on rating difference.
        
        Returns:
            Engine adjustment parameters
        """
        if not self.current_game_data:
            return {}
        
        rating_diff = self.current_game_data['rating_difference']
        
        # Determine adjustment level
        adjustment_level = 'minimal'
        for level, threshold in self.ENGINE_ADJUSTMENTS['rating_difference_thresholds'].items():
            if rating_diff >= threshold:
                adjustment_level = level
                break
        
        adjustments = self.ENGINE_ADJUSTMENTS['strength_modifiers'][adjustment_level].copy()
        adjustments['level'] = adjustment_level
        adjustments['rating_difference'] = rating_diff
        
        logger.debug(f"Engine adjustments for {rating_diff} rating difference: {adjustments}")
        
        return adjustments
    
    def calculate_provisional_rating_change(self, game_result: str) -> Dict[str, Any]:
        """
        Calculate what rating changes would be if game ended now.
        
        Args:
            game_result: '1-0', '0-1', or '1/2-1/2'
            
        Returns:
            Provisional rating change calculations
        """
        if not self.rating_calculator or not self.current_game_data:
            return {}
        
        try:
            white_change, black_change, details = self.rating_calculator.calculate_both_players(
                white_rating=self.current_game_data['white_rating'],
                black_rating=self.current_game_data['black_rating'],
                game_result=game_result,
                time_control=self.current_game_data['time_control'],
                white_games=self.current_game_data['white_games_count'],
                black_games=self.current_game_data['black_games_count']
            )
            
            return {
                'white_change': white_change,
                'black_change': black_change,
                'white_new_rating': self.current_game_data['white_rating'] + white_change,
                'black_new_rating': self.current_game_data['black_rating'] + black_change,
                'calculation_details': details,
                'game_result': game_result
            }
            
        except Exception as e:
            logger.error(f"Error calculating provisional rating change: {e}")
            return {}
    
    def analyze_game_performance(self, final_result: str) -> Dict[str, Any]:
        """
        Analyze overall game performance against rating expectations.
        
        Args:
            final_result: Final game result ('1-0', '0-1', '1/2-1/2')
            
        Returns:
            Comprehensive performance analysis
        """
        if not self.current_game_data:
            return {}
        
        # Calculate actual vs expected performance
        if final_result == '1-0':
            white_score, black_score = 1.0, 0.0
        elif final_result == '0-1':
            white_score, black_score = 0.0, 1.0
        else:  # Draw
            white_score, black_score = 0.5, 0.5
        
        expected_white = self.current_game_data['expected_scores']['white']
        expected_black = self.current_game_data['expected_scores']['black']
        
        # Performance relative to expectation
        white_performance = white_score - expected_white
        black_performance = black_score - expected_black
        
        # Get final rating changes
        rating_changes = self.calculate_provisional_rating_change(final_result)
        
        # Timer analysis
        timer_data = self.timer_manager.export_timing_data() if self.timer_manager else {}
        
        analysis = {
            'game_summary': {
                'result': final_result,
                'duration': (datetime.now() - self.current_game_data['game_start_time']).total_seconds(),
                'time_control': self.current_game_data['time_control']
            },
            'performance_analysis': {
                'white': {
                    'expected_score': expected_white,
                    'actual_score': white_score,
                    'performance_difference': white_performance,
                    'performance_rating': self._calculate_performance_rating(
                        self.current_game_data['white_rating'], 
                        self.current_game_data['black_rating'], 
                        white_score
                    ),
                    'performance_level': self._get_performance_level(white_performance)
                },
                'black': {
                    'expected_score': expected_black,
                    'actual_score': black_score,
                    'performance_difference': black_performance,
                    'performance_rating': self._calculate_performance_rating(
                        self.current_game_data['black_rating'], 
                        self.current_game_data['white_rating'], 
                        black_score
                    ),
                    'performance_level': self._get_performance_level(black_performance)
                }
            },
            'rating_changes': rating_changes,
            'timing_analysis': timer_data,
            'game_quality_metrics': self._calculate_game_quality_metrics(timer_data)
        }
        
        logger.info(f"Game performance analysis completed: {final_result}")
        
        return analysis
    
    def _calculate_performance_rating(self, player_rating: int, opponent_rating: int, score: float) -> int:
        """Calculate performance rating for a single game."""
        if score == 1.0:
            return opponent_rating + 400
        elif score == 0.0:
            return opponent_rating - 400
        else:  # Draw
            return opponent_rating
    
    def _get_performance_level(self, performance_diff: float) -> str:
        """Get performance level description."""
        for level, threshold in self.PERFORMANCE_THRESHOLDS.items():
            if performance_diff >= threshold:
                return level
        return 'terrible'
    
    def _calculate_game_quality_metrics(self, timer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate game quality metrics based on timing and play."""
        if not timer_data or not timer_data.get('performance_stats'):
            return {}
        
        metrics = {
            'time_management': {},
            'consistency': {},
            'pressure_handling': {}
        }
        
        for color in ['white', 'black']:
            stats = timer_data['performance_stats'].get(color, {})
            
            if stats.get('moves_count', 0) > 0:
                # Time management quality
                avg_time = stats.get('average_move_time', 0)
                if avg_time < 5:
                    time_quality = 'fast'
                elif avg_time < 15:
                    time_quality = 'balanced'
                elif avg_time < 30:
                    time_quality = 'thoughtful'
                else:
                    time_quality = 'slow'
                
                metrics['time_management'][color] = {
                    'average_move_time': avg_time,
                    'quality': time_quality,
                    'total_moves': stats['moves_count']
                }
        
        return metrics
    
    def get_real_time_rating_prediction(self, current_position_evaluation: float) -> Dict[str, Any]:
        """
        Get real-time rating change predictions based on current position.
        
        Args:
            current_position_evaluation: Engine evaluation of current position
            
        Returns:
            Rating predictions for different game outcomes
        """
        if not self.current_game_data:
            return {}
        
        predictions = {}
        
        for result in ['1-0', '0-1', '1/2-1/2']:
            predictions[result] = self.calculate_provisional_rating_change(result)
        
        # Add position-based likelihood estimates
        if abs(current_position_evaluation) > 3.0:
            # Clearly winning position
            if current_position_evaluation > 0:
                predictions['likely_result'] = '1-0'
                predictions['confidence'] = 'high'
            else:
                predictions['likely_result'] = '0-1'
                predictions['confidence'] = 'high'
        elif abs(current_position_evaluation) > 1.0:
            # Slight advantage
            if current_position_evaluation > 0:
                predictions['likely_result'] = '1-0'
            else:
                predictions['likely_result'] = '0-1'
            predictions['confidence'] = 'moderate'
        else:
            # Balanced position
            predictions['likely_result'] = '1/2-1/2'
            predictions['confidence'] = 'low'
        
        predictions['position_evaluation'] = current_position_evaluation
        
        return predictions
    
    def update_timer_on_move(self, player_color: str) -> Dict[str, Any]:
        """
        Update timer when a move is made.
        
        Args:
            player_color: 'white' or 'black'
            
        Returns:
            Updated timer state
        """
        if not self.timer_manager:
            return {}
        
        return self.timer_manager.make_move(player_color)
    
    def get_current_timer_state(self) -> Dict[str, Any]:
        """Get current timer state."""
        if not self.timer_manager:
            return {}
        
        return self.timer_manager.get_timer_state()
    
    def export_comprehensive_game_data(self, final_result: str) -> Dict[str, Any]:
        """
        Export comprehensive game data for storage and analysis.
        
        Args:
            final_result: Final game result
            
        Returns:
            Complete game data export
        """
        performance_analysis = self.analyze_game_performance(final_result)
        timer_data = self.timer_manager.export_timing_data() if self.timer_manager else {}
        
        return {
            'game_metadata': self.current_game_data,
            'performance_analysis': performance_analysis,
            'timer_data': timer_data,
            'final_result': final_result,
            'export_timestamp': datetime.now().isoformat(),
            'rating_integration_version': '1.0.0'
        }

# Convenience functions for easy integration

def create_rating_integration() -> RatingIntegration:
    """Create a new rating integration instance."""
    return RatingIntegration()

def calculate_game_rating_impact(
    white_rating: int, 
    black_rating: int, 
    game_result: str, 
    time_control: str = 'rapid'
) -> Dict[str, Any]:
    """
    Quick calculation of rating impact for a completed game.
    
    Args:
        white_rating: White player rating
        black_rating: Black player rating
        game_result: Game result ('1-0', '0-1', '1/2-1/2')
        time_control: Time control type
        
    Returns:
        Rating impact calculation
    """
    integration = RatingIntegration()
    
    if not integration.rating_calculator:
        return {}
    
    try:
        white_change, black_change, details = integration.rating_calculator.calculate_both_players(
            white_rating=white_rating,
            black_rating=black_rating,
            game_result=game_result,
            time_control=time_control
        )
        
        return {
            'white_change': white_change,
            'black_change': black_change,
            'white_new_rating': white_rating + white_change,
            'black_new_rating': black_rating + black_change,
            'details': details
        }
        
    except Exception as e:
        logger.error(f"Error calculating rating impact: {e}")
        return {}