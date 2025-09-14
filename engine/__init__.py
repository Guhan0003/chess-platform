"""
Multi-Rating Chess Engine System
================================

A unified chess engine architecture that supports multiple playing strengths,
personalities, and analysis capabilities.

Main Components:
- UnifiedChessEngine: Core engine with rating-based configurations
- RatingConfigs: ELO-based parameter settings
- Personality modules: Different playing styles
- Opening books: Rating-appropriate opening knowledge
- Game analyzer: Post-game analysis and coaching
"""

from .unified_engine import UnifiedChessEngine, ChessAI
from .rating_configs import RatingConfig, get_rating_config
from .game_analyzer import GameAnalyzer

# Export main interface functions for backward compatibility
def get_computer_move(fen: str, difficulty: str = "medium") -> dict:
    """
    Main interface function for getting computer moves.
    
    Args:
        fen: Current board position in FEN notation
        difficulty: Either rating number (e.g., "1200") or difficulty name
        
    Returns:
        Dictionary with move information and analysis
    """
    # Convert difficulty to rating if needed
    rating_map = {
        "easy": 400,
        "medium": 1200, 
        "hard": 1600,
        "expert": 2000
    }
    
    if difficulty in rating_map:
        rating = rating_map[difficulty]
    else:
        try:
            rating = int(difficulty)
        except ValueError:
            rating = 1200  # Default fallback
    
    engine = UnifiedChessEngine(rating)
    return engine.get_computer_move(fen)

# Version info
__version__ = "2.0.0"
__author__ = "Chess Platform Team"