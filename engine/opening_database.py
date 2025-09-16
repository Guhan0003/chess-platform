"""
Chess Opening Database Implementation
====================================

A comprehensive opening book system for multi-rating chess engines.
Includes 20+ opening variations with proper rating stratification.

Features:
- Rating-specific opening selection (400-2400+ ELO)
- Deep theoretical lines (15-20 moves)
- Advanced move weight algorithms
- ECO code classification
- Tactical and positional themes integration
"""

import chess
import chess.pgn
import random
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class OpeningMove:
    """Represents a single move in an opening variation."""
    move_san: str
    move_uci: str
    weight: int          # How often this move should be played (1-1000)
    rating_min: int      # Minimum rating for this move
    rating_max: int      # Maximum rating for this move
    popularity: float    # Professional game frequency (0.0-1.0)
    success_rate: float  # Win+Draw rate for this move (0.0-1.0)
    key_ideas: str       # Explanation of move's purpose
    follow_up_moves: List[str]  # Typical continuation moves


@dataclass
class OpeningVariation:
    """Complete opening variation with metadata."""
    id: str
    eco: str
    name: str
    variation: str
    moves: List[str]
    depth_moves: int
    skill_levels: List[str]
    key_ideas: str
    typical_plans: str
    traps_and_tactics: str
    transpositions: str
    
    # Professional metadata
    popularity_by_rating: Dict[str, float]
    typical_game_length: int
    complexity_score: float  # 0.0-10.0, higher = more complex
    aggressive_score: float  # 0.0-10.0, higher = more aggressive
    positional_score: float  # 0.0-10.0, higher = more positional


class PlayingStyle(Enum):
    """Chess playing styles for personality-based selection."""
    AGGRESSIVE = "aggressive"
    TACTICAL = "tactical"
    POSITIONAL = "positional"
    BALANCED = "balanced"
    SOLID = "solid"
    CREATIVE = "creative"


class OpeningDatabase:
    """
    Professional opening database with master-level variations.
    
    Provides rating-appropriate opening moves with proper weighting
    and style-based selection for different playing personalities.
    """
    
    def __init__(self, rating: int, style: PlayingStyle = PlayingStyle.BALANCED):
        """
        Initialize master opening database.
        
        Args:
            rating: Player rating (400-2400+)
            style: Playing style preference
        """
        self.rating = rating
        self.style = style
        self.opening_book = {}  # position_hash -> List[OpeningMove]
        self.variation_database = {}  # variation_id -> OpeningVariation
        self.position_cache = {}  # FEN -> cached analysis
        
        # Load master opening database
        self._load_master_variations()
        self._build_position_book()
        
        logger.info(f"Master opening database loaded for rating {rating}, style {style.value}")
    
    def _load_master_variations(self):
        """Load the master opening variations from the provided data."""
        # Import the complete master variations database
        from .opening_variations import MASTER_OPENING_VARIATIONS
        
        # Convert to OpeningVariation objects
        for var_data in MASTER_OPENING_VARIATIONS:
            variation = OpeningVariation(**var_data)
            self.variation_database[variation.id] = variation
    
    def _build_position_book(self):
        """Build position-based opening book from variations."""
        for variation in self.variation_database.values():
            if not self._is_variation_suitable(variation):
                continue
            
            board = chess.Board()
            moves_played = []
            
            for i, move_san in enumerate(variation.moves):
                try:
                    move = board.parse_san(move_san)
                    moves_played.append(move_san)
                    
                    # Create opening move entry
                    opening_move = self._create_opening_move(
                        move, move_san, variation, i, moves_played
                    )
                    
                    # Add to position book
                    position_key = self._get_position_key(board)
                    if position_key not in self.opening_book:
                        self.opening_book[position_key] = []
                    
                    self.opening_book[position_key].append(opening_move)
                    
                    # Apply move to board
                    board.push(move)
                    
                except chess.IllegalMoveError:
                    logger.warning(f"Illegal move {move_san} in variation {variation.id}")
                    break
                except Exception as e:
                    logger.error(f"Error processing {move_san} in {variation.id}: {e}")
                    break
    
    def _is_variation_suitable(self, variation: OpeningVariation) -> bool:
        """Check if variation is suitable for current rating."""
        for skill_level in variation.skill_levels:
            if '-' in skill_level:
                min_rating, max_rating = skill_level.split('-')
                min_rating = int(min_rating)
                max_rating = int(max_rating.replace('+', '')) if '+' not in max_rating else 2500
                
                if min_rating <= self.rating <= max_rating:
                    return True
            elif skill_level.endswith('+'):
                min_rating = int(skill_level.replace('+', ''))
                if self.rating >= min_rating:
                    return True
        
        return False
    
    def _create_opening_move(self, move: chess.Move, move_san: str, 
                           variation: OpeningVariation, move_index: int, 
                           moves_played: List[str]) -> OpeningMove:
        """Create OpeningMove object with proper weighting."""
        # Calculate weight based on rating, style, and position
        base_weight = self._calculate_base_weight(variation, move_index)
        style_modifier = self._get_style_modifier(variation)
        rating_modifier = self._get_rating_modifier(variation)
        
        final_weight = int(base_weight * style_modifier * rating_modifier)
        
        # Determine rating range for this specific move
        min_rating, max_rating = self._get_move_rating_range(variation, move_index)
        
        return OpeningMove(
            move_san=move_san,
            move_uci=move.uci(),
            weight=max(1, min(1000, final_weight)),
            rating_min=min_rating,
            rating_max=max_rating,
            popularity=self._calculate_popularity(variation, move_index),
            success_rate=self._calculate_success_rate(variation, move_index),
            key_ideas=self._get_move_ideas(variation, move_index),
            follow_up_moves=self._get_follow_up_moves(variation.moves, move_index)
        )
    
    def _calculate_base_weight(self, variation: OpeningVariation, move_index: int) -> float:
        """Calculate base weight for opening move."""
        # Early moves get higher weight
        early_move_bonus = max(1.0, 2.0 - (move_index * 0.1))
        
        # Popular variations get higher weight
        popularity_bonus = 1.0
        for rating_range, pop_score in variation.popularity_by_rating.items():
            if self._rating_in_range(rating_range):
                popularity_bonus = 1.0 + pop_score
                break
        
        return 500 * early_move_bonus * popularity_bonus
    
    def _get_style_modifier(self, variation: OpeningVariation) -> float:
        """Get style-based modifier for variation selection."""
        if self.style == PlayingStyle.AGGRESSIVE:
            return 1.0 + (variation.aggressive_score / 10.0)
        elif self.style == PlayingStyle.POSITIONAL:
            return 1.0 + (variation.positional_score / 10.0)
        elif self.style == PlayingStyle.TACTICAL:
            return 1.0 + (variation.complexity_score / 10.0)
        elif self.style == PlayingStyle.SOLID:
            return 1.0 + ((10.0 - variation.aggressive_score) / 10.0)
        else:  # BALANCED or CREATIVE
            return 1.0
    
    def _get_rating_modifier(self, variation: OpeningVariation) -> float:
        """Get rating-based modifier for variation selection."""
        complexity_tolerance = min(1.0, self.rating / 2000.0)
        if variation.complexity_score > 8.0 and complexity_tolerance < 0.8:
            return 0.5  # Reduce complex variations for lower ratings
        return 1.0
    
    def _get_move_rating_range(self, variation: OpeningVariation, move_index: int) -> Tuple[int, int]:
        """Get rating range for specific move in variation."""
        base_min = 400
        base_max = 2400
        
        # Later moves in complex variations require higher ratings
        if variation.complexity_score > 7.0 and move_index > 6:
            base_min = max(base_min, 1400)
        
        return base_min, base_max
    
    def _calculate_popularity(self, variation: OpeningVariation, move_index: int) -> float:
        """Calculate move popularity based on professional games."""
        # Use variation popularity as base
        base_popularity = 0.5
        for rating_range, pop_score in variation.popularity_by_rating.items():
            if self._rating_in_range(rating_range):
                base_popularity = pop_score
                break
        
        # Reduce popularity for later moves
        move_decay = max(0.1, 1.0 - (move_index * 0.05))
        return base_popularity * move_decay
    
    def _calculate_success_rate(self, variation: OpeningVariation, move_index: int) -> float:
        """Calculate expected success rate for move."""
        # Base success rate depends on variation strength
        base_rate = 0.55  # Slightly above 50% for good openings
        
        # Adjust based on complexity and rating suitability
        if variation.complexity_score > 8.0:
            base_rate += 0.05  # Complex openings reward preparation
        
        # Early moves tend to have more neutral success rates
        if move_index < 5:
            base_rate = 0.52
        
        return min(0.9, max(0.3, base_rate))
    
    def _get_move_ideas(self, variation: OpeningVariation, move_index: int) -> str:
        """Get key ideas for specific move in variation."""
        if move_index < 3:
            return "Opening development and central control"
        elif move_index < 6:
            return variation.key_ideas[:100] + "..."
        else:
            return variation.typical_plans[:100] + "..."
    
    def _get_follow_up_moves(self, moves: List[str], move_index: int) -> List[str]:
        """Get typical follow-up moves."""
        max_follow_ups = min(3, len(moves) - move_index - 1)
        return moves[move_index + 1:move_index + 1 + max_follow_ups]
    
    def _rating_in_range(self, rating_range: str) -> bool:
        """Check if current rating is in given range."""
        if '-' in rating_range:
            min_rating, max_rating = rating_range.split('-')
            min_rating = int(min_rating)
            max_rating = int(max_rating) if '+' not in max_rating else 2500
            return min_rating <= self.rating <= max_rating
        elif rating_range.endswith('+'):
            min_rating = int(rating_range.replace('+', ''))
            return self.rating >= min_rating
        return False
    
    def _get_position_key(self, board: chess.Board) -> str:
        """Get position key for opening book lookup."""
        # Use simplified FEN (position only, no move counts)
        fen_parts = board.fen().split()
        return f"{fen_parts[0]} {fen_parts[1]} {fen_parts[2]} {fen_parts[3]}"
    
    def get_opening_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get opening book move for current position.
        
        Args:
            board: Current chess position
            
        Returns:
            Opening move or None if out of book
        """
        position_key = self._get_position_key(board)
        
        if position_key not in self.opening_book:
            return None
        
        candidate_moves = self.opening_book[position_key]
        
        # Filter moves by rating suitability
        suitable_moves = [
            move for move in candidate_moves
            if move.rating_min <= self.rating <= move.rating_max
        ]
        
        if not suitable_moves:
            return None
        
        # Weighted random selection
        weights = [move.weight for move in suitable_moves]
        selected_move = random.choices(suitable_moves, weights=weights)[0]
        
        try:
            return board.parse_san(selected_move.move_san)
        except chess.IllegalMoveError:
            logger.warning(f"Illegal move from book: {selected_move.move_san}")
            return None
    
    def get_opening_analysis(self, board: chess.Board) -> Optional[Dict]:
        """Get detailed analysis of current opening position."""
        position_key = self._get_position_key(board)
        
        if position_key not in self.opening_book:
            return None
        
        moves = self.opening_book[position_key]
        suitable_moves = [
            move for move in moves
            if move.rating_min <= self.rating <= move.rating_max
        ]
        
        if not suitable_moves:
            return None
        
        return {
            'position_key': position_key,
            'available_moves': len(suitable_moves),
            'best_move': max(suitable_moves, key=lambda m: m.weight),
            'move_options': [
                {
                    'move': move.move_san,
                    'weight': move.weight,
                    'popularity': move.popularity,
                    'success_rate': move.success_rate,
                    'ideas': move.key_ideas
                }
                for move in sorted(suitable_moves, key=lambda m: m.weight, reverse=True)[:5]
            ]
        }
    
    def is_in_opening_book(self, board: chess.Board) -> bool:
        """Check if position is in opening book."""
        position_key = self._get_position_key(board)
        return position_key in self.opening_book
    
    def get_opening_statistics(self) -> Dict:
        """Get statistics about the opening book."""
        total_positions = len(self.opening_book)
        total_moves = sum(len(moves) for moves in self.opening_book.values())
        
        return {
            'total_positions': total_positions,
            'total_moves': total_moves,
            'variations_loaded': len(self.variation_database),
            'rating_range': f"{self.rating}",
            'playing_style': self.style.value,
            'average_moves_per_position': total_moves / max(1, total_positions)
        }


def create_opening_book(rating: int, style: str = "balanced") -> OpeningDatabase:
    """
    Factory function to create master opening book.
    
    Args:
        rating: Player rating (400-2400+)
        style: Playing style ("aggressive", "positional", "balanced", etc.)
        
    Returns:
        MasterOpeningDatabase instance
    """
    try:
        playing_style = PlayingStyle(style)
    except ValueError:
        playing_style = PlayingStyle.BALANCED
        logger.warning(f"Unknown style '{style}', defaulting to balanced")
    
    return OpeningDatabase(rating, playing_style)


# Export main classes and functions
__all__ = [
    'MasterOpeningDatabase',
    'OpeningMove',
    'OpeningVariation',
    'PlayingStyle',
    'create_master_opening_book'
]