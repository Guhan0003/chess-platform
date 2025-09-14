"""
Rating-based configuration system for chess engines.

Each rating level has specific parameters that control:
- Search depth and time limits
- Evaluation accuracy and noise
- Blunder frequency and types
- Opening book depth
- Tactical awareness
- Positional understanding
"""

from dataclasses import dataclass
from typing import Dict, Any
import random


@dataclass
class RatingConfig:
    """Configuration for a specific rating level"""
    rating: int
    search_depth: int
    time_limit: float
    blunder_chance: float
    tactical_awareness: float
    positional_weight: float
    opening_book_depth: int
    evaluation_noise: float
    endgame_skill: float
    calculation_accuracy: float


def get_rating_config(rating: int) -> RatingConfig:
    """
    Get configuration parameters for a given rating level.
    
    Args:
        rating: ELO rating (400-2400+)
        
    Returns:
        RatingConfig object with appropriate parameters
    """
    
    # Base configurations for each rating milestone
    base_configs = {
        400: RatingConfig(
            rating=400,
            search_depth=1,          # Reduced from 2 to 1 - only looks 1 move ahead
            time_limit=0.3,          # Reduced from 0.5 to 0.3 - thinks faster = weaker
            blunder_chance=0.65,     # Increased from 0.30 to 0.65 - blunders 65% of the time!
            tactical_awareness=0.05, # Reduced from 0.1 to 0.05 - misses tactics more
            positional_weight=0.1,   # Reduced from 0.2 to 0.1 - poor positioning
            opening_book_depth=2,    # Reduced from 3 to 2 - limited opening knowledge
            evaluation_noise=150.0,  # Increased from 100.0 to 150.0 - more evaluation errors
            endgame_skill=0.1,       # Reduced from 0.2 to 0.1 - poor endgame play
            calculation_accuracy=0.2 # Reduced from 0.3 to 0.2 - more calculation errors
        ),
        600: RatingConfig(
            rating=600,
            search_depth=2,
            time_limit=0.8,
            blunder_chance=0.20,
            tactical_awareness=0.2,
            positional_weight=0.3,
            opening_book_depth=4,
            evaluation_noise=80.0,
            endgame_skill=0.3,
            calculation_accuracy=0.4
        ),
        800: RatingConfig(
            rating=800,
            search_depth=3,
            time_limit=1.0,
            blunder_chance=0.15,
            tactical_awareness=0.4,
            positional_weight=0.4,
            opening_book_depth=5,
            evaluation_noise=60.0,
            endgame_skill=0.4,
            calculation_accuracy=0.5
        ),
        1000: RatingConfig(
            rating=1000,
            search_depth=3,
            time_limit=1.5,
            blunder_chance=0.10,
            tactical_awareness=0.5,
            positional_weight=0.5,
            opening_book_depth=6,
            evaluation_noise=40.0,
            endgame_skill=0.5,
            calculation_accuracy=0.6
        ),
        1200: RatingConfig(
            rating=1200,
            search_depth=4,
            time_limit=2.0,
            blunder_chance=0.08,
            tactical_awareness=0.7,
            positional_weight=0.6,
            opening_book_depth=8,
            evaluation_noise=30.0,
            endgame_skill=0.6,
            calculation_accuracy=0.7
        ),
        1400: RatingConfig(
            rating=1400,
            search_depth=4,
            time_limit=2.5,
            blunder_chance=0.05,
            tactical_awareness=0.8,
            positional_weight=0.7,
            opening_book_depth=10,
            evaluation_noise=20.0,
            endgame_skill=0.7,
            calculation_accuracy=0.8
        ),
        1600: RatingConfig(
            rating=1600,
            search_depth=5,
            time_limit=3.0,
            blunder_chance=0.03,
            tactical_awareness=0.9,
            positional_weight=0.8,
            opening_book_depth=12,
            evaluation_noise=15.0,
            endgame_skill=0.8,
            calculation_accuracy=0.85
        ),
        1800: RatingConfig(
            rating=1800,
            search_depth=5,
            time_limit=4.0,
            blunder_chance=0.02,
            tactical_awareness=0.95,
            positional_weight=0.85,
            opening_book_depth=15,
            evaluation_noise=10.0,
            endgame_skill=0.85,
            calculation_accuracy=0.9
        ),
        2000: RatingConfig(
            rating=2000,
            search_depth=6,
            time_limit=5.0,
            blunder_chance=0.01,
            tactical_awareness=0.98,
            positional_weight=0.9,
            opening_book_depth=18,
            evaluation_noise=5.0,
            endgame_skill=0.9,
            calculation_accuracy=0.95
        ),
        2200: RatingConfig(
            rating=2200,
            search_depth=7,
            time_limit=7.0,
            blunder_chance=0.005,
            tactical_awareness=0.99,
            positional_weight=0.95,
            opening_book_depth=20,
            evaluation_noise=2.0,
            endgame_skill=0.95,
            calculation_accuracy=0.98
        ),
        2400: RatingConfig(
            rating=2400,
            search_depth=8,
            time_limit=10.0,
            blunder_chance=0.002,
            tactical_awareness=0.995,
            positional_weight=0.98,
            opening_book_depth=25,
            evaluation_noise=1.0,
            endgame_skill=0.98,
            calculation_accuracy=0.99
        )
    }
    
    # Find closest rating configuration
    closest_rating = min(base_configs.keys(), key=lambda x: abs(x - rating))
    base_config = base_configs[closest_rating]
    
    # Interpolate if rating is between two milestones
    if rating != closest_rating:
        base_config = _interpolate_config(rating, base_configs)
    
    return base_config


def _interpolate_config(target_rating: int, configs: Dict[int, RatingConfig]) -> RatingConfig:
    """
    Interpolate configuration between two rating levels.
    
    Args:
        target_rating: Desired rating level
        configs: Dictionary of base configurations
        
    Returns:
        Interpolated RatingConfig
    """
    ratings = sorted(configs.keys())
    
    # Find the two ratings to interpolate between
    lower_rating = None
    upper_rating = None
    
    for i, rating in enumerate(ratings):
        if rating <= target_rating:
            lower_rating = rating
        if rating >= target_rating and upper_rating is None:
            upper_rating = rating
            break
    
    # If exact match or at boundaries
    if lower_rating == target_rating:
        return configs[lower_rating]
    if upper_rating == target_rating:
        return configs[upper_rating]
    if lower_rating is None:
        return configs[ratings[0]]
    if upper_rating is None:
        return configs[ratings[-1]]
    
    # Interpolate between lower and upper
    lower_config = configs[lower_rating]
    upper_config = configs[upper_rating]
    
    # Calculate interpolation factor
    factor = (target_rating - lower_rating) / (upper_rating - lower_rating)
    
    return RatingConfig(
        rating=target_rating,
        search_depth=int(lower_config.search_depth + factor * (upper_config.search_depth - lower_config.search_depth)),
        time_limit=lower_config.time_limit + factor * (upper_config.time_limit - lower_config.time_limit),
        blunder_chance=lower_config.blunder_chance + factor * (upper_config.blunder_chance - lower_config.blunder_chance),
        tactical_awareness=lower_config.tactical_awareness + factor * (upper_config.tactical_awareness - lower_config.tactical_awareness),
        positional_weight=lower_config.positional_weight + factor * (upper_config.positional_weight - lower_config.positional_weight),
        opening_book_depth=int(lower_config.opening_book_depth + factor * (upper_config.opening_book_depth - lower_config.opening_book_depth)),
        evaluation_noise=lower_config.evaluation_noise + factor * (upper_config.evaluation_noise - lower_config.evaluation_noise),
        endgame_skill=lower_config.endgame_skill + factor * (upper_config.endgame_skill - lower_config.endgame_skill),
        calculation_accuracy=lower_config.calculation_accuracy + factor * (upper_config.calculation_accuracy - lower_config.calculation_accuracy)
    )


def get_personality_modifier(personality: str) -> Dict[str, float]:
    """
    Get personality-based modifiers for engine behavior.
    
    Args:
        personality: Type of personality ("aggressive", "positional", "defensive", etc.)
        
    Returns:
        Dictionary of parameter modifiers
    """
    personalities = {
        "aggressive": {
            "tactical_awareness": 1.2,
            "positional_weight": 0.8,
            "attack_bonus": 50.0,
            "sacrifice_threshold": 0.7
        },
        "positional": {
            "tactical_awareness": 0.9,
            "positional_weight": 1.3,
            "patience_factor": 1.5,
            "pawn_structure_bonus": 30.0
        },
        "defensive": {
            "king_safety_weight": 1.5,
            "material_conservation": 1.2,
            "counterattack_threshold": 0.8
        },
        "balanced": {
            # No modifiers - uses base config
        },
        "tactical": {
            "tactical_awareness": 1.4,
            "combination_bonus": 40.0,
            "piece_activity": 1.2
        }
    }
    
    return personalities.get(personality, personalities["balanced"])


# Testing and validation functions
def validate_config(config: RatingConfig) -> bool:
    """Validate that a configuration has reasonable values"""
    return (
        100 <= config.rating <= 3000 and
        1 <= config.search_depth <= 20 and
        0.1 <= config.time_limit <= 60.0 and
        0.0 <= config.blunder_chance <= 1.0 and
        0.0 <= config.tactical_awareness <= 1.0 and
        0.0 <= config.positional_weight <= 2.0
    )


def get_human_readable_description(config: RatingConfig) -> str:
    """Get human-readable description of engine strength"""
    if config.rating < 600:
        return f"Beginner ({config.rating}) - Learning the basics"
    elif config.rating < 1000:
        return f"Novice ({config.rating}) - Knows basic tactics"
    elif config.rating < 1400:
        return f"Intermediate ({config.rating}) - Solid fundamentals"
    elif config.rating < 1800:
        return f"Advanced ({config.rating}) - Strong player"
    elif config.rating < 2200:
        return f"Expert ({config.rating}) - Tournament level"
    else:
        return f"Master ({config.rating}) - Near-perfect play"