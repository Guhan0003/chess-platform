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

from .unified_engine import UnifiedChessEngine
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
    
    # Create unified chess engine
    engine = UnifiedChessEngine(rating, personality)
    result = engine.get_computer_move(fen)
    
    # Format response for compatibility
    if result['success']:
        return {
            'success': True,
            'move': result['move']['uci'],
            'san': result['move']['san'],
            'evaluation': result['engine_info']['evaluation'],
            'thinking_time': result['engine_info']['search_time'],
            'new_fen': result['new_fen'],
            'game_status': result['game_status']
        }
    else:
        return result

def create_engine(rating: int, personality: str = "balanced") -> UnifiedChessEngine:
    """
    Create a chess engine instance.
    
    Args:
        rating: Engine rating (400-2400+)
        personality: Playing style personality
        
    Returns:
        UnifiedChessEngine instance
    """
    return UnifiedChessEngine(rating, personality)

def get_position_analysis(fen: str, rating: int = 2000) -> dict:
    """
    Get detailed position analysis using chess engine.
    
    Args:
        fen: Position in FEN notation
        rating: Analysis strength rating
        
    Returns:
        Comprehensive position analysis
    """
    engine = UnifiedChessEngine(rating)
    result = engine.get_computer_move(fen)
    
    # Format response for compatibility
    if result['success']:
        return {
            'success': True,
            'move': result['move']['uci'],
            'evaluation': result['engine_info']['evaluation'],
            'thinking_time': result['engine_info']['search_time']
        }
    else:
        return result

# Legacy compatibility function
def get_computer_move_legacy(fen: str, difficulty: str = "medium") -> dict:
    """Legacy interface - now uses modern engine for compatibility."""
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
    
    # Use unified engine but format output for legacy compatibility
    result = get_computer_move(fen, str(rating))
    
    if result['success']:
        return {
            'move': {
                'notation': result.get('san', ''),
                'uci': result.get('move', '')
            },
            'evaluation': result.get('evaluation', 0),
            'thinking_time': result.get('thinking_time', 0)
        }
    else:
        return {'error': result.get('error', 'Unknown error')}

# Version info
__version__ = "3.0.0"
__author__ = "Chess Platform Team"

# Export main classes for advanced usage
__all__ = [
    'UnifiedChessEngine',
    'get_computer_move',
    'create_engine',
    'get_position_analysis',
    'get_computer_move_legacy',
    'RatingConfig',
    'get_rating_config',
    'GameAnalyzer'
]