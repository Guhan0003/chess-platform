"""
Time Management System for Chess Engine
=======================================

Implements rating-specific time controls with sophisticated move decision algorithms.
Provides human-like thinking time patterns for different skill levels.
"""

import time
import math
import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class MoveType(Enum):
    """Classification of chess moves for time allocation."""
    OPENING_BOOK = "opening_book"
    TACTICAL = "tactical"
    POSITIONAL = "positional"
    ENDGAME = "endgame"
    FORCED = "forced"
    COMPLEX = "complex"
    ROUTINE = "routine"


class GamePhase(Enum):
    """Chess game phases for time management."""
    OPENING = "opening"
    EARLY_MIDDLEGAME = "early_middlegame"
    MIDDLEGAME = "middlegame"
    LATE_MIDDLEGAME = "late_middlegame"
    ENDGAME = "endgame"


@dataclass
class TimeProfile:
    """Time profile for different rating levels."""
    rating_min: int
    rating_max: int
    base_time: float          # Base thinking time in seconds
    max_time: float           # Maximum time for complex positions
    min_time: float           # Minimum time (fast obvious moves)
    
    # Phase-specific modifiers
    opening_modifier: float   # Multiplier for opening moves
    middlegame_modifier: float # Multiplier for middlegame
    endgame_modifier: float   # Multiplier for endgame
    
    # Move type modifiers
    tactical_modifier: float  # Extra time for tactics
    positional_modifier: float # Time for positional moves
    forced_modifier: float    # Time for forced moves
    
    # Human-like behavior
    inconsistency_factor: float # Random time variation (0.0-1.0)
    calculation_depth: int      # Search depth expectation
    blunder_chance: float       # Probability of time pressure blunders


class TimeManager:
    """
    Professional time management system that mimics human chess players.
    
    Provides realistic time allocation based on:
    - Player rating and skill level
    - Game phase and position complexity
    - Move type and difficulty
    - Human-like thinking patterns
    """
    
    def __init__(self, rating: int, time_control: Optional[Dict] = None):
        """
        Initialize professional time manager.
        
        Args:
            rating: Player rating (400-2400+)
            time_control: Optional time control settings
        """
        self.rating = rating
        self.time_control = time_control or {}
        self.move_history = []
        self.time_spent_history = []
        self.position_complexity_cache = {}
        
        # Load rating-specific time profile
        self.time_profile = self._get_time_profile(rating)
        
        # Initialize thinking patterns
        self.last_move_time = 0.0
        self.accumulated_complexity = 0.0
        self.fatigue_factor = 1.0
        
        logger.info(f"Professional time manager initialized for rating {rating}")
    
    def _get_time_profile(self, rating: int) -> TimeProfile:
        """Get time profile based on rating level."""
        # Define time profiles for different rating ranges
        time_profiles = [
            TimeProfile(
                rating_min=400, rating_max=800,
                base_time=3.0, max_time=8.0, min_time=1.0,
                opening_modifier=0.8, middlegame_modifier=1.2, endgame_modifier=1.0,
                tactical_modifier=1.5, positional_modifier=0.9, forced_modifier=0.5,
                inconsistency_factor=0.4, calculation_depth=3, blunder_chance=0.15
            ),
            TimeProfile(
                rating_min=800, rating_max=1200,
                base_time=4.0, max_time=10.0, min_time=1.5,
                opening_modifier=0.9, middlegame_modifier=1.3, endgame_modifier=1.1,
                tactical_modifier=1.8, positional_modifier=1.0, forced_modifier=0.6,
                inconsistency_factor=0.3, calculation_depth=4, blunder_chance=0.10
            ),
            TimeProfile(
                rating_min=1200, rating_max=1600,
                base_time=5.0, max_time=12.0, min_time=2.0,
                opening_modifier=1.0, middlegame_modifier=1.4, endgame_modifier=1.2,
                tactical_modifier=2.0, positional_modifier=1.1, forced_modifier=0.7,
                inconsistency_factor=0.25, calculation_depth=5, blunder_chance=0.08
            ),
            TimeProfile(
                rating_min=1600, rating_max=2000,
                base_time=6.0, max_time=15.0, min_time=2.5,
                opening_modifier=1.1, middlegame_modifier=1.5, endgame_modifier=1.3,
                tactical_modifier=2.2, positional_modifier=1.2, forced_modifier=0.8,
                inconsistency_factor=0.2, calculation_depth=6, blunder_chance=0.05
            ),
            TimeProfile(
                rating_min=2000, rating_max=2200,
                base_time=8.0, max_time=18.0, min_time=3.0,
                opening_modifier=1.2, middlegame_modifier=1.6, endgame_modifier=1.4,
                tactical_modifier=2.5, positional_modifier=1.3, forced_modifier=0.9,
                inconsistency_factor=0.15, calculation_depth=7, blunder_chance=0.03
            ),
            TimeProfile(
                rating_min=2200, rating_max=2400,
                base_time=10.0, max_time=20.0, min_time=3.5,
                opening_modifier=1.3, middlegame_modifier=1.7, endgame_modifier=1.5,
                tactical_modifier=2.8, positional_modifier=1.4, forced_modifier=1.0,
                inconsistency_factor=0.12, calculation_depth=8, blunder_chance=0.02
            ),
            TimeProfile(
                rating_min=2400, rating_max=3000,
                base_time=12.0, max_time=25.0, min_time=4.0,
                opening_modifier=1.4, middlegame_modifier=1.8, endgame_modifier=1.6,
                tactical_modifier=3.0, positional_modifier=1.5, forced_modifier=1.1,
                inconsistency_factor=0.10, calculation_depth=10, blunder_chance=0.01
            )
        ]
        
        # Find matching profile
        for profile in time_profiles:
            if profile.rating_min <= rating <= profile.rating_max:
                return profile
        
        # Default to highest profile for super-GMs
        return time_profiles[-1]
    
    def calculate_thinking_time(self, board, move_type: MoveType, 
                              complexity_score: float = 5.0,
                              candidate_moves: int = 5,
                              tactical_motifs: int = 0) -> float:
        """
        Calculate appropriate thinking time for a move.
        
        Args:
            board: Current chess position
            move_type: Type of move being considered
            complexity_score: Position complexity (0.0-10.0)
            candidate_moves: Number of reasonable candidate moves
            tactical_motifs: Number of tactical patterns detected
            
        Returns:
            Thinking time in seconds
        """
        # Get base time from profile
        base_time = self.time_profile.base_time
        
        # Apply game phase modifier
        game_phase = self._determine_game_phase(board)
        phase_modifier = self._get_phase_modifier(game_phase)
        
        # Apply move type modifier
        type_modifier = self._get_move_type_modifier(move_type)
        
        # Calculate complexity-based time adjustment
        complexity_modifier = self._calculate_complexity_modifier(
            complexity_score, candidate_moves, tactical_motifs
        )
        
        # Calculate base thinking time
        thinking_time = base_time * phase_modifier * type_modifier * complexity_modifier
        
        # Apply human-like inconsistency
        thinking_time = self._apply_inconsistency(thinking_time)
        
        # Apply fatigue and time pressure
        thinking_time = self._apply_fatigue_factor(thinking_time)
        
        # Enforce time bounds
        thinking_time = max(self.time_profile.min_time, 
                          min(self.time_profile.max_time, thinking_time))
        
        # Store for pattern analysis
        self.last_move_time = thinking_time
        self.time_spent_history.append(thinking_time)
        
        return thinking_time
    
    def _determine_game_phase(self, board) -> GamePhase:
        """Determine current game phase based on position."""
        move_number = len(board.move_stack)
        piece_count = len(board.piece_map())
        
        if move_number < 10:
            return GamePhase.OPENING
        elif move_number < 20:
            return GamePhase.EARLY_MIDDLEGAME
        elif piece_count > 16:
            return GamePhase.MIDDLEGAME
        elif piece_count > 10:
            return GamePhase.LATE_MIDDLEGAME
        else:
            return GamePhase.ENDGAME
    
    def _get_phase_modifier(self, phase: GamePhase) -> float:
        """Get time modifier based on game phase."""
        modifiers = {
            GamePhase.OPENING: self.time_profile.opening_modifier,
            GamePhase.EARLY_MIDDLEGAME: self.time_profile.middlegame_modifier * 0.9,
            GamePhase.MIDDLEGAME: self.time_profile.middlegame_modifier,
            GamePhase.LATE_MIDDLEGAME: self.time_profile.middlegame_modifier * 1.1,
            GamePhase.ENDGAME: self.time_profile.endgame_modifier
        }
        return modifiers[phase]
    
    def _get_move_type_modifier(self, move_type: MoveType) -> float:
        """Get time modifier based on move type."""
        modifiers = {
            MoveType.OPENING_BOOK: 0.3,  # Quick book moves
            MoveType.TACTICAL: self.time_profile.tactical_modifier,
            MoveType.POSITIONAL: self.time_profile.positional_modifier,
            MoveType.ENDGAME: self.time_profile.endgame_modifier,
            MoveType.FORCED: self.time_profile.forced_modifier,
            MoveType.COMPLEX: 1.5,  # Extra time for complex positions
            MoveType.ROUTINE: 0.7   # Less time for routine moves
        }
        return modifiers.get(move_type, 1.0)
    
    def _calculate_complexity_modifier(self, complexity_score: float,
                                     candidate_moves: int,
                                     tactical_motifs: int) -> float:
        """Calculate time modifier based on position complexity."""
        # Base complexity modifier (0.5x to 2.0x)
        complexity_modifier = 0.5 + (complexity_score / 10.0) * 1.5
        
        # Candidate moves modifier (more options = more time)
        candidate_modifier = 1.0 + (candidate_moves - 3) * 0.1
        candidate_modifier = max(0.8, min(1.5, candidate_modifier))
        
        # Tactical motifs modifier (tactics require calculation)
        tactical_modifier = 1.0 + tactical_motifs * 0.3
        tactical_modifier = min(2.0, tactical_modifier)
        
        return complexity_modifier * candidate_modifier * tactical_modifier
    
    def _apply_inconsistency(self, thinking_time: float) -> float:
        """Apply human-like time inconsistency."""
        inconsistency = self.time_profile.inconsistency_factor
        
        # Random variation in thinking time
        variation = random.uniform(-inconsistency, inconsistency)
        modified_time = thinking_time * (1.0 + variation)
        
        # Occasional "long thinks" for humans
        if random.random() < 0.05:  # 5% chance of extended thinking
            modified_time *= random.uniform(1.5, 2.5)
        
        return modified_time
    
    def _apply_fatigue_factor(self, thinking_time: float) -> float:
        """Apply fatigue effects in long games."""
        game_length = len(self.time_spent_history)
        
        if game_length > 30:  # After move 30, fatigue sets in
            fatigue_reduction = 1.0 - ((game_length - 30) * 0.01)
            fatigue_reduction = max(0.7, fatigue_reduction)  # Max 30% reduction
            thinking_time *= fatigue_reduction
        
        return thinking_time
    
    def get_opening_book_time(self) -> float:
        """Get quick time for opening book moves."""
        base_time = self.time_profile.min_time * 0.5
        variation = random.uniform(0.8, 1.2)
        return base_time * variation
    
    def get_forced_move_time(self) -> float:
        """Get time for obviously forced moves."""
        base_time = self.time_profile.min_time
        variation = random.uniform(0.9, 1.1)
        return base_time * variation
    
    def get_tactical_calculation_time(self, depth: int, complexity: float) -> float:
        """Get time for tactical calculations."""
        base_time = self.time_profile.base_time * self.time_profile.tactical_modifier
        
        # Depth-based time scaling
        depth_modifier = 1.0 + (depth - 3) * 0.3
        
        # Complexity scaling
        complexity_modifier = 0.8 + (complexity / 10.0) * 0.4
        
        total_time = base_time * depth_modifier * complexity_modifier
        return min(self.time_profile.max_time, total_time)
    
    def simulate_human_thinking_delay(self, calculated_time: float) -> None:
        """
        Simulate human thinking time with realistic delay patterns.
        
        Args:
            calculated_time: Time to think in seconds
        """
        if calculated_time <= 0:
            return
        
        # Simulate gradual thinking process
        start_time = time.time()
        remaining_time = calculated_time
        
        while remaining_time > 0.1:
            # Think in chunks (like humans do)
            chunk_time = min(0.5, remaining_time * 0.3)
            time.sleep(chunk_time)
            remaining_time -= chunk_time
            
            # Occasional pause (like humans reconsidering)
            if random.random() < 0.1 and remaining_time > 1.0:
                pause_time = random.uniform(0.2, 0.5)
                time.sleep(pause_time)
                remaining_time -= pause_time
        
        # Final thinking time
        if remaining_time > 0:
            time.sleep(remaining_time)
    
    def get_time_statistics(self) -> Dict:
        """Get time usage statistics."""
        if not self.time_spent_history:
            return {"no_moves": True}
        
        total_time = sum(self.time_spent_history)
        avg_time = total_time / len(self.time_spent_history)
        max_time = max(self.time_spent_history)
        min_time = min(self.time_spent_history)
        
        return {
            "total_moves": len(self.time_spent_history),
            "total_time_spent": total_time,
            "average_time_per_move": avg_time,
            "max_time_on_move": max_time,
            "min_time_on_move": min_time,
            "rating": self.rating,
            "base_time": self.time_profile.base_time,
            "max_allowed_time": self.time_profile.max_time
        }
    
    def should_use_extended_time(self, position_evaluation: float,
                               tactical_complexity: int) -> bool:
        """
        Determine if this position warrants extended thinking time.
        
        Args:
            position_evaluation: Current position evaluation
            tactical_complexity: Number of tactical motifs found
            
        Returns:
            True if extended time should be used
        """
        # Critical positions warrant more time
        is_critical = abs(position_evaluation) > 1.0  # More than 1 pawn advantage
        
        # Tactical positions need calculation time
        is_tactical = tactical_complexity > 2
        
        # Complex endgames require precision
        is_complex_endgame = (
            len(self.move_history) > 40 and
            tactical_complexity > 0
        )
        
        return is_critical or is_tactical or is_complex_endgame


def create_time_manager(rating: int, time_control: Optional[Dict] = None) -> TimeManager:
    """
    Factory function to create professional time manager.
    
    Args:
        rating: Player rating (400-2400+)
        time_control: Optional time control settings
        
    Returns:
        ProfessionalTimeManager instance
    """
    return TimeManager(rating, time_control)


# Export main classes and functions
__all__ = [
    'ProfessionalTimeManager',
    'MoveType',
    'GamePhase',
    'TimeProfile',
    'create_time_manager'
]