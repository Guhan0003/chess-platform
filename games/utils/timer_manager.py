"""
Timer Management System for Chess Games
=======================================

Integrates with chess engine and rating system to provide:
- Accurate time tracking with high precision
- Increment support (Fischer time controls)
- Time pressure analysis for engine strength adjustment
- Timer display and management
- Game termination on timeout
- Time-based performance metrics
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import threading
import logging

logger = logging.getLogger(__name__)


class TimerManager:
    """
    Timer management for chess games with:
    - High-precision timing (millisecond accuracy)
    - Increment support (Fischer time controls)
    - Time pressure detection for engine adaptation
    - Tournament time formats
    - Automatic timeout detection
    """
    
    # Standard time control formats (in seconds)
    # Categories: Bullet (<3 min), Blitz (3-10 min), Rapid (10-30 min), Classical (>30 min)
    TIME_CONTROLS = {
        # Ultra-Bullet (30 seconds - 1 minute)
        'bullet_30s': {'initial': 30, 'increment': 0, 'name': '30 sec', 'category': 'bullet', 'display': '⚡ 30 sec'},
        'bullet_1': {'initial': 60, 'increment': 0, 'name': '1+0 Bullet', 'category': 'bullet', 'display': '⚡ 1 min'},
        'bullet_1_1': {'initial': 60, 'increment': 1, 'name': '1+1 Bullet', 'category': 'bullet', 'display': '⚡ 1|1'},
        
        # Bullet (1-2 minutes)
        'bullet_2': {'initial': 120, 'increment': 0, 'name': '2+0 Bullet', 'category': 'bullet', 'display': '⚡ 2 min'},
        'bullet_2_1': {'initial': 120, 'increment': 1, 'name': '2+1 Bullet', 'category': 'bullet', 'display': '⚡ 2|1'},
        
        # Blitz (3-10 minutes)
        'blitz_3': {'initial': 180, 'increment': 0, 'name': '3+0 Blitz', 'category': 'blitz', 'display': '🔥 3 min'},
        'blitz_3_2': {'initial': 180, 'increment': 2, 'name': '3+2 Blitz', 'category': 'blitz', 'display': '🔥 3|2'},
        'blitz_5': {'initial': 300, 'increment': 0, 'name': '5+0 Blitz', 'category': 'blitz', 'display': '🔥 5 min'},
        'blitz_5_3': {'initial': 300, 'increment': 3, 'name': '5+3 Blitz', 'category': 'blitz', 'display': '🔥 5|3'},
        'blitz_5_5': {'initial': 300, 'increment': 5, 'name': '5+5 Blitz', 'category': 'blitz', 'display': '🔥 5|5'},
        
        # Rapid (10-30 minutes)
        'rapid_10': {'initial': 600, 'increment': 0, 'name': '10+0 Rapid', 'category': 'rapid', 'display': '🏃 10 min'},
        'rapid_10_5': {'initial': 600, 'increment': 5, 'name': '10+5 Rapid', 'category': 'rapid', 'display': '🏃 10|5'},
        'rapid_15': {'initial': 900, 'increment': 0, 'name': '15+0 Rapid', 'category': 'rapid', 'display': '🏃 15 min'},
        'rapid_15_10': {'initial': 900, 'increment': 10, 'name': '15+10 Rapid', 'category': 'rapid', 'display': '🏃 15|10'},
        
        # Classical (30+ minutes)
        'classical_30': {'initial': 1800, 'increment': 0, 'name': '30+0 Classical', 'category': 'classical', 'display': '♔ 30 min'},
        'classical_30_20': {'initial': 1800, 'increment': 20, 'name': '30+20 Classical', 'category': 'classical', 'display': '♔ 30|20'},
        'classical_60': {'initial': 3600, 'increment': 0, 'name': '60+0 Classical', 'category': 'classical', 'display': '♔ 60 min'},
        'classical_90_30': {'initial': 5400, 'increment': 30, 'name': '90+30 Classical', 'category': 'classical', 'display': '♔ 90|30'},
        
        # Unlimited
        'unlimited': {'initial': None, 'increment': 0, 'name': 'Unlimited', 'category': 'unlimited', 'display': '∞ Unlimited'}
    }
    
    # Category to simple time control mapping for API compatibility
    CATEGORY_DEFAULTS = {
        'bullet': 'bullet_2',
        'blitz': 'blitz_5',
        'rapid': 'rapid_10',
        'classical': 'classical_30',
        'unlimited': 'unlimited'
    }
    
    def __init__(self, time_control: str = 'rapid_10'):
        """
        Initialize professional timer manager.
        
        Args:
            time_control: Time control format key from TIME_CONTROLS
        """
        self.time_control = self.TIME_CONTROLS.get(time_control, self.TIME_CONTROLS['rapid_10'])
        
        # Timer state
        self.white_time = self.time_control['initial']
        self.black_time = self.time_control['initial']
        self.increment = self.time_control['increment']
        
        # Timing precision
        self.last_move_time = None
        self.current_turn = 'white'  # who is to move
        self.game_started = False
        self.game_ended = False
        
        # Time pressure thresholds (for engine adaptation)
        self.time_pressure_thresholds = {
            'critical': 30,  # Less than 30 seconds
            'low': 60,       # Less than 1 minute
            'moderate': 180, # Less than 3 minutes
        }
        
        # Performance tracking
        self.move_times = []
        self.time_usage_stats = {
            'white': {'total_time_used': 0, 'average_move_time': 0, 'moves_count': 0},
            'black': {'total_time_used': 0, 'average_move_time': 0, 'moves_count': 0}
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Professional timer initialized: {self.time_control['name']}")
    
    def start_game(self) -> Dict[str, Any]:
        """
        Start the game timer.
        
        Returns:
            Timer state information
        """
        with self._lock:
            if self.game_started:
                logger.warning("Game timer already started")
                return self.get_timer_state()
            
            self.game_started = True
            self.last_move_time = time.time()
            self.current_turn = 'white'
            
            logger.info(f"Game timer started - {self.time_control['name']}")
            return self.get_timer_state()
    
    def make_move(self, player_color: str) -> Dict[str, Any]:
        """
        Record a move and update timers with professional precision.
        
        Args:
            player_color: 'white' or 'black'
            
        Returns:
            Updated timer state with move timing information
        """
        with self._lock:
            if not self.game_started or self.game_ended:
                logger.warning(f"Cannot make move - game not active")
                return self.get_timer_state()
            
            if player_color != self.current_turn:
                logger.warning(f"Wrong turn: expected {self.current_turn}, got {player_color}")
                return self.get_timer_state()
            
            current_time = time.time()
            
            if self.last_move_time:
                # Calculate time elapsed for this move
                time_elapsed = current_time - self.last_move_time
                
                # Deduct time from current player
                if player_color == 'white':
                    if self.white_time is not None:
                        self.white_time = max(0, self.white_time - time_elapsed)
                        # Add increment
                        if self.white_time > 0:
                            self.white_time += self.increment
                else:
                    if self.black_time is not None:
                        self.black_time = max(0, self.black_time - time_elapsed)
                        # Add increment
                        if self.black_time > 0:
                            self.black_time += self.increment
                
                # Update performance tracking
                self._update_performance_stats(player_color, time_elapsed)
                
                # Log the move timing
                logger.debug(f"{player_color} move took {time_elapsed:.2f}s")
            
            # Switch turns
            self.current_turn = 'black' if player_color == 'white' else 'white'
            self.last_move_time = current_time
            
            # Check for timeout
            timeout_player = self.check_timeout()
            if timeout_player:
                self.game_ended = True
                logger.info(f"Game ended - {timeout_player} timeout")
            
            return self.get_timer_state()
    
    def get_timer_state(self) -> Dict[str, Any]:
        """
        Get current timer state with professional accuracy.
        
        Returns:
            Complete timer state information
        """
        with self._lock:
            # Calculate current time if game is active
            current_white_time = self.white_time
            current_black_time = self.black_time
            
            if self.game_started and not self.game_ended and self.last_move_time:
                elapsed_since_last_move = time.time() - self.last_move_time
                
                if self.current_turn == 'white' and self.white_time is not None:
                    current_white_time = max(0, self.white_time - elapsed_since_last_move)
                elif self.current_turn == 'black' and self.black_time is not None:
                    current_black_time = max(0, self.black_time - elapsed_since_last_move)
            
            return {
                'white_time': current_white_time,
                'black_time': current_black_time,
                'current_turn': self.current_turn,
                'game_started': self.game_started,
                'game_ended': self.game_ended,
                'time_control': self.time_control,
                'increment': self.increment,
                'time_pressure': {
                    'white': self._get_time_pressure_level(current_white_time),
                    'black': self._get_time_pressure_level(current_black_time)
                },
                'performance_stats': self.time_usage_stats,
                'last_update': time.time()
            }
    
    def check_timeout(self) -> Optional[str]:
        """
        Check if any player has run out of time.
        
        Returns:
            'white' or 'black' if timeout occurred, None otherwise
        """
        if self.white_time is not None and self.white_time <= 0:
            return 'white'
        if self.black_time is not None and self.black_time <= 0:
            return 'black'
        return None
    
    def get_time_pressure_level(self, player_color: str) -> str:
        """
        Get time pressure level for engine adaptation.
        
        Args:
            player_color: 'white' or 'black'
            
        Returns:
            'none', 'moderate', 'low', or 'critical'
        """
        time_remaining = self.white_time if player_color == 'white' else self.black_time
        return self._get_time_pressure_level(time_remaining)
    
    def _get_time_pressure_level(self, time_remaining: Optional[float]) -> str:
        """Internal method to determine time pressure level."""
        if time_remaining is None:
            return 'none'  # Unlimited time
        
        if time_remaining <= self.time_pressure_thresholds['critical']:
            return 'critical'
        elif time_remaining <= self.time_pressure_thresholds['low']:
            return 'low'
        elif time_remaining <= self.time_pressure_thresholds['moderate']:
            return 'moderate'
        else:
            return 'none'
    
    def _update_performance_stats(self, player_color: str, time_elapsed: float):
        """Update performance statistics for time usage analysis."""
        stats = self.time_usage_stats[player_color]
        stats['moves_count'] += 1
        stats['total_time_used'] += time_elapsed
        stats['average_move_time'] = stats['total_time_used'] / stats['moves_count']
        
        # Track move times for analysis
        self.move_times.append({
            'player': player_color,
            'time': time_elapsed,
            'move_number': stats['moves_count'],
            'timestamp': time.time()
        })
    
    def get_time_management_advice(self, player_color: str) -> Dict[str, Any]:
        """
        Provide time management advice based on current state.
        
        Args:
            player_color: 'white' or 'black'
            
        Returns:
            Time management advice and analysis
        """
        stats = self.time_usage_stats[player_color]
        time_remaining = self.white_time if player_color == 'white' else self.black_time
        pressure_level = self.get_time_pressure_level(player_color)
        
        advice = {
            'pressure_level': pressure_level,
            'time_remaining': time_remaining,
            'average_move_time': stats['average_move_time'],
            'moves_played': stats['moves_count'],
            'suggestions': []
        }
        
        if pressure_level == 'critical':
            advice['suggestions'].extend([
                'Play very quickly - use intuition',
                'Avoid deep calculations',
                'Focus on safe moves'
            ])
        elif pressure_level == 'low':
            advice['suggestions'].extend([
                'Speed up your play',
                'Use pattern recognition',
                'Avoid long thinks'
            ])
        elif pressure_level == 'moderate':
            advice['suggestions'].extend([
                'Manage time carefully',
                'Prioritize key moments',
                'Balance speed and accuracy'
            ])
        else:
            advice['suggestions'].extend([
                'Use time wisely',
                'Calculate important variations',
                'Build good positions'
            ])
        
        return advice
    
    def format_time_display(self, seconds: Optional[float]) -> str:
        """
        Format time for professional display.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds is None:
            return '∞'
        
        if seconds < 0:
            return '0:00'
        
        if seconds >= 3600:  # More than 1 hour
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
    
    def export_timing_data(self) -> Dict[str, Any]:
        """
        Export comprehensive timing data for analysis.
        
        Returns:
            Complete timing analysis data
        """
        return {
            'game_summary': {
                'time_control': self.time_control,
                'total_game_time': time.time() - (self.last_move_time - sum(move['time'] for move in self.move_times)) if self.move_times else 0,
                'total_moves': len(self.move_times),
                'game_status': 'ended' if self.game_ended else ('active' if self.game_started else 'not_started')
            },
            'performance_stats': self.time_usage_stats,
            'move_times': self.move_times,
            'time_pressure_analysis': {
                'white_pressure_periods': self._analyze_time_pressure('white'),
                'black_pressure_periods': self._analyze_time_pressure('black')
            },
            'final_times': {
                'white': self.white_time,
                'black': self.black_time
            }
        }
    
    def _analyze_time_pressure(self, player_color: str) -> Dict[str, int]:
        """Analyze time pressure periods for a player."""
        pressure_counts = {'none': 0, 'moderate': 0, 'low': 0, 'critical': 0}
        
        for move in self.move_times:
            if move['player'] == player_color:
                # This is simplified - in a real implementation, you'd track
                # time remaining at each move
                pressure_counts['none'] += 1
        
        return pressure_counts

    @classmethod
    def create_timer_for_rating(cls, player_rating: int) -> 'TimerManager':
        """
        Create appropriate timer based on player rating.
        
        Args:
            player_rating: Player's ELO rating
            
        Returns:
            Timer with appropriate time control
        """
        if player_rating < 1000:
            return cls('rapid_15_10')  # More time for beginners
        elif player_rating < 1600:
            return cls('rapid_10')
        elif player_rating < 2000:
            return cls('blitz_5_3')
        else:
            return cls('blitz_3')  # Masters play faster
    
    def get_available_time_controls(self) -> list:
        """
        Get list of available time control formats.
        
        Returns:
            List of time control keys
        """
        return list(self.TIME_CONTROLS.keys())