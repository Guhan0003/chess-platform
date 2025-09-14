"""
Chess Opening Book System

Manages opening book knowledge for different rating levels.
Provides rating-appropriate opening moves and variations.

Features:
- Rating-based opening selection
- Opening databases for different skill levels
- Variation management
- Book learning from games
"""

import chess
import chess.pgn
import random
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import sqlite3


@dataclass
class OpeningMove:
    """Represents a move in the opening book."""
    move: chess.Move
    weight: int          # How often this move should be played
    rating_min: int      # Minimum rating for this move
    rating_max: int      # Maximum rating for this move
    name: str           # Opening/variation name
    eco_code: str       # ECO (Encyclopedia of Chess Openings) code
    win_rate: float     # Historical win rate
    draw_rate: float    # Historical draw rate
    games_count: int    # Number of games with this move


@dataclass
class OpeningPosition:
    """Represents a position in the opening book."""
    fen: str
    moves: List[OpeningMove]
    popularity_rating: int  # How popular this position is
    complexity_level: int   # How complex the resulting positions are


class OpeningBook:
    """
    Opening book manager with rating-based move selection.
    
    Provides appropriate opening moves based on player rating level.
    Lower rated players get simpler, more principled openings.
    Higher rated players get access to complex theoretical lines.
    """
    
    def __init__(self, rating: int, personality: str = "balanced"):
        """
        Initialize opening book for specific rating and personality.
        
        Args:
            rating: Player rating level
            personality: Playing style preference
        """
        self.rating = rating
        self.personality = personality
        self.book_data = {}  # FEN -> OpeningPosition
        self.loaded_books = set()
        
        # Opening preferences based on personality
        self.personality_preferences = {
            "aggressive": {"sharp": 1.5, "tactical": 1.3, "gambit": 1.4},
            "positional": {"strategic": 1.4, "solid": 1.2, "classical": 1.3},
            "defensive": {"solid": 1.5, "safe": 1.3, "symmetrical": 1.2},
            "tactical": {"sharp": 1.4, "tactical": 1.5, "complex": 1.2},
            "attacking": {"aggressive": 1.5, "gambit": 1.6, "sharp": 1.3},
            "solid": {"safe": 1.4, "classical": 1.3, "mainstream": 1.2},
            "creative": {"unusual": 1.5, "sideline": 1.3, "creative": 1.4},
            "pragmatic": {"mainstream": 1.3, "practical": 1.4, "solid": 1.2}
        }
        
        # Load appropriate opening books
        self._load_rating_appropriate_books()
    
    def get_book_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get best opening book move for current position.
        
        Args:
            board: Current chess position
            
        Returns:
            Opening book move or None if out of book
        """
        fen = self._normalize_fen(board.fen())
        
        if fen not in self.book_data:
            return None
        
        position = self.book_data[fen]
        candidate_moves = self._filter_moves_by_rating(position.moves)
        
        if not candidate_moves:
            return None
        
        # Apply personality preferences
        weighted_moves = self._apply_personality_weights(candidate_moves)
        
        # Select move based on weights
        return self._select_weighted_move(weighted_moves)
    
    def is_in_book(self, board: chess.Board) -> bool:
        """Check if current position is in opening book."""
        fen = self._normalize_fen(board.fen())
        return fen in self.book_data
    
    def get_opening_name(self, board: chess.Board) -> Optional[str]:
        """Get opening name for current position."""
        fen = self._normalize_fen(board.fen())
        
        if fen in self.book_data:
            position = self.book_data[fen]
            if position.moves:
                # Return name of most popular move
                best_move = max(position.moves, key=lambda m: m.weight)
                return best_move.name
        
        return None
    
    def get_opening_info(self, board: chess.Board) -> Dict:
        """Get comprehensive opening information."""
        fen = self._normalize_fen(board.fen())
        
        if fen not in self.book_data:
            return {"in_book": False}
        
        position = self.book_data[fen]
        candidate_moves = self._filter_moves_by_rating(position.moves)
        
        move_info = []
        for opening_move in candidate_moves[:5]:  # Top 5 moves
            move_info.append({
                "move": opening_move.move.uci(),
                "san": board.san(opening_move.move),
                "name": opening_move.name,
                "eco_code": opening_move.eco_code,
                "weight": opening_move.weight,
                "win_rate": opening_move.win_rate,
                "draw_rate": opening_move.draw_rate,
                "games": opening_move.games_count
            })
        
        return {
            "in_book": True,
            "position_popularity": position.popularity_rating,
            "complexity_level": position.complexity_level,
            "candidate_moves": move_info,
            "opening_name": self.get_opening_name(board)
        }
    
    def _load_rating_appropriate_books(self):
        """Load opening books appropriate for rating level."""
        # Define which books to load based on rating
        if self.rating < 800:
            self._load_beginner_openings()
        elif self.rating < 1200:
            self._load_beginner_openings()
            self._load_intermediate_openings()
        elif self.rating < 1600:
            self._load_intermediate_openings()
            self._load_advanced_openings()
        else:
            self._load_intermediate_openings()
            self._load_advanced_openings()
            self._load_master_openings()
    
    def _load_beginner_openings(self):
        """Load basic, principled openings for beginners."""
        if "beginner" in self.loaded_books:
            return
        
        # Basic opening principles - control center, develop pieces, castle
        beginner_openings = [
            # 1.e4 openings
            {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -",
                "moves": [
                    {"move": "e2e4", "weight": 40, "name": "King's Pawn Opening", "eco": "B00"},
                    {"move": "d2d4", "weight": 35, "name": "Queen's Pawn Opening", "eco": "D00"},
                    {"move": "g1f3", "weight": 20, "name": "Réti Opening", "eco": "A04"},
                    {"move": "c2c4", "weight": 5, "name": "English Opening", "eco": "A10"}
                ]
            },
            # Response to 1.e4
            {
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3",
                "moves": [
                    {"move": "e7e5", "weight": 50, "name": "King's Pawn Game", "eco": "C20"},
                    {"move": "c7c5", "weight": 25, "name": "Sicilian Defense", "eco": "B20"},
                    {"move": "e7e6", "weight": 15, "name": "French Defense", "eco": "C00"},
                    {"move": "c7c6", "weight": 10, "name": "Caro-Kann Defense", "eco": "B10"}
                ]
            }
        ]
        
        for opening_data in beginner_openings:
            self._add_position_to_book(opening_data, rating_range=(400, 1000))
        
        self.loaded_books.add("beginner")
    
    def _load_intermediate_openings(self):
        """Load more complex openings for intermediate players."""
        if "intermediate" in self.loaded_books:
            return
        
        # More specific variations and tactical openings
        intermediate_openings = [
            # Italian Game
            {
                "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq -",
                "moves": [
                    {"move": "f7f5", "weight": 30, "name": "Italian Game: Rousseau Gambit", "eco": "C50"},
                    {"move": "b8c6", "weight": 25, "name": "Italian Game: Hungarian Defense", "eco": "C50"},
                    {"move": "f7f6", "weight": 20, "name": "Italian Game: Paris Defense", "eco": "C50"},
                    {"move": "g8f6", "weight": 25, "name": "Italian Game: Two Knights Defense", "eco": "C55"}
                ]
            },
            # Sicilian Dragon
            {
                "fen": "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R b KQkq -",
                "moves": [
                    {"move": "g7g6", "weight": 40, "name": "Sicilian Defense: Dragon Variation", "eco": "B70"},
                    {"move": "e7e6", "weight": 30, "name": "Sicilian Defense: Najdorf Variation", "eco": "B90"},
                    {"move": "a7a6", "weight": 30, "name": "Sicilian Defense: Najdorf Variation", "eco": "B90"}
                ]
            }
        ]
        
        for opening_data in intermediate_openings:
            self._add_position_to_book(opening_data, rating_range=(800, 1800))
        
        self.loaded_books.add("intermediate")
    
    def _load_advanced_openings(self):
        """Load complex theoretical openings for advanced players."""
        if "advanced" in self.loaded_books:
            return
        
        # Complex theoretical lines
        # This would include deep preparation and sharp variations
        # For now, placeholder structure
        
        self.loaded_books.add("advanced")
    
    def _load_master_openings(self):
        """Load cutting-edge theoretical openings for masters."""
        if "master" in self.loaded_books:
            return
        
        # Latest theoretical developments
        # Computer-generated novelties
        # For now, placeholder structure
        
        self.loaded_books.add("master")
    
    def _add_position_to_book(self, opening_data: Dict, rating_range: Tuple[int, int]):
        """Add position and moves to opening book."""
        fen = self._normalize_fen(opening_data["fen"])
        moves = []
        
        for move_data in opening_data["moves"]:
            move = chess.Move.from_uci(move_data["move"])
            opening_move = OpeningMove(
                move=move,
                weight=move_data["weight"],
                rating_min=rating_range[0],
                rating_max=rating_range[1],
                name=move_data["name"],
                eco_code=move_data["eco"],
                win_rate=0.5,  # Default values
                draw_rate=0.3,
                games_count=1000
            )
            moves.append(opening_move)
        
        position = OpeningPosition(
            fen=fen,
            moves=moves,
            popularity_rating=sum(m.weight for m in moves),
            complexity_level=len(moves)
        )
        
        self.book_data[fen] = position
    
    def _normalize_fen(self, fen: str) -> str:
        """Normalize FEN by removing move counters."""
        parts = fen.split()
        # Keep only position, turn, castling, en passant
        return " ".join(parts[:4])
    
    def _filter_moves_by_rating(self, moves: List[OpeningMove]) -> List[OpeningMove]:
        """Filter moves appropriate for current rating."""
        return [
            move for move in moves
            if move.rating_min <= self.rating <= move.rating_max
        ]
    
    def _apply_personality_weights(self, moves: List[OpeningMove]) -> List[Tuple[OpeningMove, float]]:
        """Apply personality-based weights to moves."""
        weighted_moves = []
        
        personality_prefs = self.personality_preferences.get(self.personality, {})
        
        for move in moves:
            weight = move.weight
            
            # Apply personality modifiers based on opening characteristics
            # This is simplified - real implementation would analyze opening properties
            opening_lower = move.name.lower()
            
            for trait, multiplier in personality_prefs.items():
                if trait in opening_lower:
                    weight *= multiplier
            
            weighted_moves.append((move, weight))
        
        return weighted_moves
    
    def _select_weighted_move(self, weighted_moves: List[Tuple[OpeningMove, float]]) -> Optional[chess.Move]:
        """Select move based on weights with some randomness."""
        if not weighted_moves:
            return None
        
        # Add some randomness to avoid being completely predictable
        total_weight = sum(weight for _, weight in weighted_moves)
        
        if total_weight <= 0:
            return random.choice(weighted_moves)[0].move
        
        # Weighted random selection
        target = random.uniform(0, total_weight)
        current = 0
        
        for opening_move, weight in weighted_moves:
            current += weight
            if current >= target:
                return opening_move.move
        
        # Fallback
        return weighted_moves[0][0].move
    
    def add_game_to_book(self, pgn_game: chess.pgn.Game, max_moves: int = 15):
        """
        Learn from a game by adding moves to opening book.
        
        Args:
            pgn_game: Game in PGN format
            max_moves: Maximum opening moves to consider
        """
        board = chess.Board()
        move_count = 0
        
        for move in pgn_game.mainline_moves():
            if move_count >= max_moves:
                break
            
            fen = self._normalize_fen(board.fen())
            
            # Add position if not in book
            if fen not in self.book_data:
                self.book_data[fen] = OpeningPosition(
                    fen=fen,
                    moves=[],
                    popularity_rating=0,
                    complexity_level=0
                )
            
            # Add or update move
            position = self.book_data[fen]
            existing_move = None
            
            for opening_move in position.moves:
                if opening_move.move == move:
                    existing_move = opening_move
                    break
            
            if existing_move:
                # Update existing move weight
                existing_move.weight += 1
                existing_move.games_count += 1
            else:
                # Add new move
                opening_move = OpeningMove(
                    move=move,
                    weight=1,
                    rating_min=400,
                    rating_max=2800,
                    name="Unknown",
                    eco_code="",
                    win_rate=0.5,
                    draw_rate=0.3,
                    games_count=1
                )
                position.moves.append(opening_move)
            
            board.push(move)
            move_count += 1
    
    def save_book(self, filename: str):
        """Save opening book to file."""
        book_export = {}
        
        for fen, position in self.book_data.items():
            moves_data = []
            for move in position.moves:
                moves_data.append({
                    "move": move.move.uci(),
                    "weight": move.weight,
                    "rating_min": move.rating_min,
                    "rating_max": move.rating_max,
                    "name": move.name,
                    "eco_code": move.eco_code,
                    "win_rate": move.win_rate,
                    "draw_rate": move.draw_rate,
                    "games_count": move.games_count
                })
            
            book_export[fen] = {
                "moves": moves_data,
                "popularity_rating": position.popularity_rating,
                "complexity_level": position.complexity_level
            }
        
        with open(filename, 'w') as f:
            json.dump(book_export, f, indent=2)
    
    def load_book(self, filename: str):
        """Load opening book from file."""
        try:
            with open(filename, 'r') as f:
                book_data = json.load(f)
            
            for fen, position_data in book_data.items():
                moves = []
                for move_data in position_data["moves"]:
                    move = chess.Move.from_uci(move_data["move"])
                    opening_move = OpeningMove(
                        move=move,
                        weight=move_data["weight"],
                        rating_min=move_data["rating_min"],
                        rating_max=move_data["rating_max"],
                        name=move_data["name"],
                        eco_code=move_data["eco_code"],
                        win_rate=move_data["win_rate"],
                        draw_rate=move_data["draw_rate"],
                        games_count=move_data["games_count"]
                    )
                    moves.append(opening_move)
                
                position = OpeningPosition(
                    fen=fen,
                    moves=moves,
                    popularity_rating=position_data["popularity_rating"],
                    complexity_level=position_data["complexity_level"]
                )
                
                self.book_data[fen] = position
                
        except FileNotFoundError:
            print(f"Opening book file {filename} not found")
        except Exception as e:
            print(f"Error loading opening book: {e}")


# Factory function for external use
def create_opening_book(rating: int, personality: str = "balanced") -> OpeningBook:
    """
    Create opening book appropriate for rating level.
    
    Args:
        rating: Player rating
        personality: Playing style
        
    Returns:
        Configured OpeningBook instance
    """
    return OpeningBook(rating, personality)