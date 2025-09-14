"""
Chess Personality System

Defines different playing personalities and styles that can be applied
to the chess engine to create more human-like and varied play.

Each personality modifies evaluation weights and decision-making to
create distinct playing characteristics.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import random


class PersonalityType(Enum):
    """Predefined personality types."""
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    POSITIONAL = "positional"
    DEFENSIVE = "defensive"
    TACTICAL = "tactical"
    ENDGAME_SPECIALIST = "endgame_specialist"
    ATTACKING = "attacking"
    SOLID = "solid"
    CREATIVE = "creative"
    PRAGMATIC = "pragmatic"


@dataclass
class PersonalityModifiers:
    """
    Modifiers that adjust engine behavior based on personality.
    
    Values are multipliers applied to different evaluation components
    and decision-making parameters.
    """
    # Evaluation component weights
    material_weight: float = 1.0
    positional_weight: float = 1.0
    tactical_weight: float = 1.0
    king_safety_weight: float = 1.0
    mobility_weight: float = 1.0
    pawn_structure_weight: float = 1.0
    
    # Search behavior modifiers
    aggression_factor: float = 1.0      # Preference for sharp positions
    risk_tolerance: float = 1.0         # Willingness to take risks
    exchange_preference: float = 1.0    # Preference for piece exchanges
    
    # Move selection modifiers
    sacrifice_willingness: float = 1.0  # Willingness to sacrifice material
    positional_patience: float = 1.0    # Preference for long-term plans
    time_management: float = 1.0        # How much time to spend thinking
    
    # Opening and endgame preferences
    opening_variety: float = 1.0        # Preference for varied openings
    endgame_technique: float = 1.0      # Endgame playing strength modifier
    
    # Human-like characteristics
    consistency: float = 1.0            # How consistent the play is
    calculation_depth: float = 1.0      # Search depth modifier
    
    def __post_init__(self):
        """Validate modifier values."""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be a number")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")


class PersonalitySystem:
    """
    System for managing chess engine personalities.
    
    Provides predefined personalities and allows creation of custom ones.
    """
    
    # Predefined personality configurations
    PERSONALITIES = {
        PersonalityType.BALANCED: PersonalityModifiers(
            # Balanced approach - all factors weighted equally
            material_weight=1.0,
            positional_weight=1.0,
            tactical_weight=1.0,
            king_safety_weight=1.0,
            aggression_factor=1.0,
            risk_tolerance=1.0,
            consistency=1.0
        ),
        
        PersonalityType.AGGRESSIVE: PersonalityModifiers(
            # Aggressive - prioritizes attacks and tactics
            material_weight=0.9,         # Less concerned with material
            positional_weight=0.8,       # Less positional
            tactical_weight=1.4,         # More tactical
            king_safety_weight=0.7,      # Takes king safety risks
            mobility_weight=1.3,         # Values active pieces
            aggression_factor=1.6,       # Very aggressive
            risk_tolerance=1.4,          # High risk tolerance
            sacrifice_willingness=1.5,   # Willing to sacrifice
            positional_patience=0.6,     # Impatient for action
            consistency=0.8              # More unpredictable
        ),
        
        PersonalityType.POSITIONAL: PersonalityModifiers(
            # Positional - focuses on long-term advantages
            material_weight=1.1,         # Slightly values material
            positional_weight=1.5,       # Strong positional focus
            tactical_weight=0.9,         # Less tactical
            king_safety_weight=1.2,      # Values king safety
            pawn_structure_weight=1.4,   # Strong pawn play
            aggression_factor=0.7,       # Less aggressive
            risk_tolerance=0.8,          # Lower risk tolerance
            exchange_preference=1.2,     # Likes favorable exchanges
            positional_patience=1.5,     # Very patient
            endgame_technique=1.3        # Strong endgames
        ),
        
        PersonalityType.DEFENSIVE: PersonalityModifiers(
            # Defensive - prioritizes safety and solidity
            material_weight=1.2,         # Values material highly
            positional_weight=1.1,       # Solid positional play
            tactical_weight=0.8,         # Less tactical risks
            king_safety_weight=1.6,      # Very safety-conscious
            pawn_structure_weight=1.3,   # Solid pawn structure
            aggression_factor=0.5,       # Very defensive
            risk_tolerance=0.6,          # Low risk tolerance
            sacrifice_willingness=0.4,   # Rarely sacrifices
            positional_patience=1.3,     # Patient play
            consistency=1.2              # Very consistent
        ),
        
        PersonalityType.TACTICAL: PersonalityModifiers(
            # Tactical - looks for combinations and tactics
            material_weight=0.9,         # Less material focus
            positional_weight=0.8,       # Less positional
            tactical_weight=1.6,         # Very tactical
            king_safety_weight=0.9,      # Reasonable safety
            mobility_weight=1.4,         # Active piece play
            aggression_factor=1.3,       # Aggressive tactics
            risk_tolerance=1.2,          # Moderate risk
            sacrifice_willingness=1.3,   # Tactical sacrifices
            calculation_depth=1.2,       # Deeper calculation
            consistency=0.9              # Somewhat unpredictable
        ),
        
        PersonalityType.ENDGAME_SPECIALIST: PersonalityModifiers(
            # Endgame specialist - excellent in endings
            material_weight=1.0,         # Normal material value
            positional_weight=1.2,       # Good positional sense
            tactical_weight=1.0,         # Normal tactics
            king_safety_weight=1.1,      # Moderate safety
            pawn_structure_weight=1.5,   # Excellent pawn play
            exchange_preference=1.3,     # Likes simplification
            positional_patience=1.4,     # Very patient
            endgame_technique=1.6,       # Exceptional endgames
            consistency=1.3              # Very consistent in endings
        ),
        
        PersonalityType.ATTACKING: PersonalityModifiers(
            # Attacking - seeks attacking chances
            material_weight=0.8,         # Sacrifices for attack
            positional_weight=0.7,       # Less positional
            tactical_weight=1.3,         # Tactical attacker
            king_safety_weight=0.6,      # Takes safety risks
            mobility_weight=1.5,         # Very active pieces
            aggression_factor=1.7,       # Extremely aggressive
            risk_tolerance=1.5,          # High risk tolerance
            sacrifice_willingness=1.6,   # Frequent sacrifices
            positional_patience=0.5,     # Very impatient
            opening_variety=1.3,         # Varied attacking openings
            consistency=0.7              # Unpredictable attacks
        ),
        
        PersonalityType.SOLID: PersonalityModifiers(
            # Solid - reliable and steady
            material_weight=1.1,         # Values material
            positional_weight=1.3,       # Strong positional play
            tactical_weight=1.0,         # Normal tactics
            king_safety_weight=1.4,      # Safety-first
            pawn_structure_weight=1.3,   # Solid pawns
            aggression_factor=0.8,       # Moderately aggressive
            risk_tolerance=0.9,          # Conservative
            exchange_preference=1.1,     # Likes simplification
            positional_patience=1.2,     # Patient approach
            consistency=1.4              # Very consistent
        ),
        
        PersonalityType.CREATIVE: PersonalityModifiers(
            # Creative - unconventional and imaginative
            material_weight=0.9,         # Less material focus
            positional_weight=0.9,       # Less conventional
            tactical_weight=1.2,         # Creative tactics
            king_safety_weight=0.8,      # Takes calculated risks
            mobility_weight=1.2,         # Active, creative pieces
            aggression_factor=1.1,       # Moderately aggressive
            risk_tolerance=1.3,          # High creativity risk
            sacrifice_willingness=1.2,   # Creative sacrifices
            positional_patience=0.8,     # Less patient
            opening_variety=1.5,         # Very varied openings
            consistency=0.6              # Highly unpredictable
        ),
        
        PersonalityType.PRAGMATIC: PersonalityModifiers(
            # Pragmatic - practical and efficient
            material_weight=1.2,         # Values material
            positional_weight=1.1,       # Good positional sense
            tactical_weight=1.1,         # Practical tactics
            king_safety_weight=1.2,      # Safety-conscious
            pawn_structure_weight=1.1,   # Practical pawn play
            aggression_factor=0.9,       # Measured aggression
            risk_tolerance=0.9,          # Calculated risks
            exchange_preference=1.2,     # Practical exchanges
            positional_patience=1.1,     # Practical patience
            endgame_technique=1.2,       # Good technique
            consistency=1.3              # Very consistent
        )
    }
    
    @classmethod
    def get_personality(cls, personality_type: str) -> PersonalityModifiers:
        """
        Get personality modifiers for a given personality type.
        
        Args:
            personality_type: Name of personality type
            
        Returns:
            PersonalityModifiers for the specified personality
        """
        # Convert string to enum
        if isinstance(personality_type, str):
            try:
                personality_enum = PersonalityType(personality_type.lower())
            except ValueError:
                # Default to balanced if unknown personality
                personality_enum = PersonalityType.BALANCED
        else:
            personality_enum = personality_type
        
        return cls.PERSONALITIES.get(personality_enum, cls.PERSONALITIES[PersonalityType.BALANCED])
    
    @classmethod
    def create_custom_personality(cls, **modifiers) -> PersonalityModifiers:
        """
        Create a custom personality with specified modifiers.
        
        Args:
            **modifiers: Keyword arguments for PersonalityModifiers
            
        Returns:
            Custom PersonalityModifiers object
        """
        return PersonalityModifiers(**modifiers)
    
    @classmethod
    def get_random_personality(cls) -> PersonalityModifiers:
        """Get a random personality for variety."""
        personality_type = random.choice(list(PersonalityType))
        return cls.get_personality(personality_type)
    
    @classmethod
    def blend_personalities(cls, personality1: str, personality2: str, blend_factor: float = 0.5) -> PersonalityModifiers:
        """
        Blend two personalities to create a hybrid.
        
        Args:
            personality1: First personality name
            personality2: Second personality name
            blend_factor: How much to blend (0.0 = all personality1, 1.0 = all personality2)
            
        Returns:
            Blended PersonalityModifiers
        """
        p1 = cls.get_personality(personality1)
        p2 = cls.get_personality(personality2)
        
        # Blend all modifier values
        blended_values = {}
        for field_name in p1.__dict__:
            value1 = getattr(p1, field_name)
            value2 = getattr(p2, field_name)
            blended_value = value1 * (1 - blend_factor) + value2 * blend_factor
            blended_values[field_name] = blended_value
        
        return PersonalityModifiers(**blended_values)
    
    @classmethod
    def apply_rating_adjustment(cls, personality: PersonalityModifiers, rating: int) -> PersonalityModifiers:
        """
        Adjust personality based on rating level.
        
        Lower rated players have more extreme personalities,
        higher rated players are more balanced.
        
        Args:
            personality: Base personality
            rating: Player rating
            
        Returns:
            Rating-adjusted personality
        """
        # Calculate adjustment factor (higher rating = more balanced)
        balance_factor = min(1.0, (rating - 400) / 1600)  # 0.0 at 400, 1.0 at 2000+
        
        adjusted_values = {}
        for field_name, value in personality.__dict__.items():
            # Move extreme values toward 1.0 (balanced) based on rating
            if value > 1.0:
                adjusted_value = 1.0 + (value - 1.0) * (1.0 - balance_factor * 0.3)
            else:
                adjusted_value = 1.0 - (1.0 - value) * (1.0 - balance_factor * 0.3)
            
            adjusted_values[field_name] = adjusted_value
        
        return PersonalityModifiers(**adjusted_values)
    
    @classmethod
    def get_personality_description(cls, personality_type: str) -> str:
        """Get a human-readable description of a personality type."""
        descriptions = {
            "balanced": "A well-rounded player with no particular weaknesses or strengths.",
            "aggressive": "Prefers sharp, tactical positions and is willing to take risks for the initiative.",
            "positional": "Focuses on long-term strategic advantages and excellent endgame technique.",
            "defensive": "Prioritizes safety and solid positions, rarely taking unnecessary risks.",
            "tactical": "Excels at finding combinations and tactical solutions to problems.",
            "endgame_specialist": "Particularly strong in endgames with excellent technique.",
            "attacking": "Constantly seeks attacking chances, even at material cost.",
            "solid": "Plays reliable, consistent chess with few mistakes.",
            "creative": "Finds unconventional and imaginative solutions to positions.",
            "pragmatic": "Makes practical, efficient decisions focused on concrete advantages."
        }
        
        return descriptions.get(personality_type.lower(), "Unknown personality type.")
    
    @classmethod
    def list_available_personalities(cls) -> Dict[str, str]:
        """Get list of all available personalities with descriptions."""
        return {
            personality.value: cls.get_personality_description(personality.value)
            for personality in PersonalityType
        }


# Convenience function for external use
def get_personality_modifier(personality_type: str) -> PersonalityModifiers:
    """
    Get personality modifiers for use in engine.
    
    Args:
        personality_type: Name of personality type
        
    Returns:
        PersonalityModifiers for the specified personality
    """
    return PersonalitySystem.get_personality(personality_type)