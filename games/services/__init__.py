"""
Chess Platform Rating Services
================================

Centralized rating management for the chess platform.
All rating-related functionality exported from this package.
"""

from .rating_service import (
    GlobalRatingService,
    update_game_ratings,
    get_rating_preview,
    get_player_rating_stats
)

# Export main service class
__all__ = [
    'GlobalRatingService',
    'update_game_ratings',
    'get_rating_preview', 
    'get_player_rating_stats'
]

# Also import from old rating calculators for backward compatibility
try:
    from games.utils.rating_calculator import (
        ELORatingCalculator,
        SkillLevelManager,
        initialize_user_ratings
    )
    
    __all__.extend([
        'ELORatingCalculator',
        'SkillLevelManager',
        'initialize_user_ratings'
    ])
except ImportError:
    pass  # Old calculators not available

try:
    from games.utils.rating_system import (
        RatingIntegration,
        create_rating_integration,
        calculate_game_rating_impact
    )
    
    __all__.extend([
        'RatingIntegration',
        'create_rating_integration',
        'calculate_game_rating_impact'
    ])
except ImportError:
    pass  # Rating integration not available

