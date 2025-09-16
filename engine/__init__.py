"""
Multi-Rating Chess Engine System
================================

A unified chess engine architecture with advanced capabilities:
- Comprehensive opening database with 20+ opening variations
- Advanced search algorithms (PVS, iterative deepening, etc.)
- Sophisticated time management
- Rating-based intelligence (400-2400+ ELO)
- Multiple playing personalities

Main Components:
- ChessEngine: Advanced engine with all components
- OpeningDatabase: 20+ opening variations with deep theory
- AdvancedSearchEngine: PVS, killer moves, history heuristic
- TimeManager: Human-like time allocation
- Rating-based configurations and personalities
"""

from .chess_engine import ChessEngine, create_chess_engine
from .unified_engine import UnifiedChessEngine, ChessAI  # Legacy support
from .rating_configs import RatingConfig, get_rating_config
from .game_analyzer import GameAnalyzer

# Export main interface functions
def get_computer_move(fen: str, difficulty: str = "medium", personality: str = "balanced") -> dict:
    """
    Main interface function for getting computer moves with professional engine.
    
    Args:
        fen: Current board position in FEN notation
        difficulty: Either rating number (e.g., "2000") or difficulty name
        personality: Playing style ("aggressive", "positional", "balanced", etc.)
        
    Returns:
        Dictionary with move information and professional analysis
    """
    # Convert difficulty to rating if needed
    rating_map = {
        "beginner": 600,
        "easy": 800,
        "medium": 1200, 
        "hard": 1600,
        "expert": 2000,
        "master": 2200,
        "grandmaster": 2400
    }
    
    if difficulty in rating_map:
        rating = rating_map[difficulty]
    else:
        try:
            rating = int(difficulty)
            # Ensure rating is within valid range
            rating = max(400, min(2400, rating))
        except ValueError:
            rating = 1200  # Default fallback
    
    # Create chess engine
    engine = create_chess_engine(rating, personality)
    return engine.get_computer_move(fen)

def create_engine(rating: int, personality: str = "balanced") -> ChessEngine:
    """
    Create a chess engine instance.
    
    Args:
        rating: Engine rating (400-2400+)
        personality: Playing style personality
        
    Returns:
        ChessEngine instance
    """
    return create_chess_engine(rating, personality)

def get_position_analysis(fen: str, rating: int = 2000) -> dict:
    """
    Get detailed position analysis using chess engine.
    
    Args:
        fen: Position in FEN notation
        rating: Analysis strength rating
        
    Returns:
        Comprehensive position analysis
    """
    engine = create_chess_engine(rating)
    return engine.get_position_analysis(fen)

# Legacy compatibility function
def get_computer_move_legacy(fen: str, difficulty: str = "medium") -> dict:
    """Legacy interface using original unified engine."""
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
            rating = 1200
    
    engine = UnifiedChessEngine(rating)
    return engine.get_computer_move(fen)

# Version info
__version__ = "3.0.0"
__author__ = "Chess Platform Team"

# Export main classes for advanced usage
__all__ = [
    'ChessEngine',
    'UnifiedChessEngine',
    'get_computer_move',
    'create_engine',
    'get_position_analysis',
    'get_computer_move_legacy',
    'RatingConfig',
    'get_rating_config',
    'GameAnalyzer'
]