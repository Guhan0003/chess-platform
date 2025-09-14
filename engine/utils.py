"""
Chess Engine Utilities

Helper functions and utilities for the chess engine system.
Includes position analysis, debugging tools, performance monitoring,
and various chess-specific utility functions.
"""

import chess
import chess.pgn
import chess.polyglot
import time
import hashlib
import json
import io
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """Chess game phases."""
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"


@dataclass
class PositionInfo:
    """Comprehensive information about a chess position."""
    fen: str
    phase: GamePhase
    material_balance: int
    piece_count: Dict[str, int]
    king_safety_white: float
    king_safety_black: float
    mobility_white: int
    mobility_black: int
    center_control: float
    development: Dict[str, int]
    pawn_structure_score: float
    tactical_complexity: float


@dataclass
class PerformanceMetrics:
    """Engine performance tracking."""
    positions_evaluated: int
    time_spent: float
    nodes_per_second: int
    cache_hits: int
    cache_misses: int
    average_depth: float
    cutoffs: int
    transposition_hits: int


class ChessUtilities:
    """
    Collection of utility functions for chess engine operations.
    """
    
    # Piece values for quick reference
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    # Center squares
    CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
    EXTENDED_CENTER = [chess.C3, chess.C4, chess.C5, chess.C6,
                      chess.D3, chess.D4, chess.D5, chess.D6,
                      chess.E3, chess.E4, chess.E5, chess.E6,
                      chess.F3, chess.F4, chess.F5, chess.F6]
    
    @staticmethod
    def normalize_fen(fen: str) -> str:
        """
        Normalize FEN string by removing move counters.
        
        Args:
            fen: Full FEN string
            
        Returns:
            Normalized FEN (position + turn + castling + en passant)
        """
        parts = fen.split()
        return " ".join(parts[:4]) if len(parts) >= 4 else fen
    
    @staticmethod
    def get_material_balance(board: chess.Board) -> int:
        """
        Calculate material balance in centipawns.
        
        Args:
            board: Chess position
            
        Returns:
            Material balance (positive = white advantage)
        """
        balance = 0
        
        for piece_type in ChessUtilities.PIECE_VALUES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            balance += (white_count - black_count) * ChessUtilities.PIECE_VALUES[piece_type]
        
        return balance
    
    @staticmethod
    def get_piece_counts(board: chess.Board) -> Dict[str, int]:
        """
        Get count of all pieces on the board.
        
        Args:
            board: Chess position
            
        Returns:
            Dictionary with piece counts
        """
        counts = {}
        
        for color in [chess.WHITE, chess.BLACK]:
            color_name = "white" if color == chess.WHITE else "black"
            
            for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, 
                              chess.ROOK, chess.QUEEN, chess.KING]:
                piece_name = chess.piece_name(piece_type)
                count = len(board.pieces(piece_type, color))
                counts[f"{color_name}_{piece_name}"] = count
        
        return counts
    
    @staticmethod
    def determine_game_phase(board: chess.Board) -> GamePhase:
        """
        Determine current game phase based on material and piece development.
        
        Args:
            board: Chess position
            
        Returns:
            Current game phase
        """
        # Calculate total material (excluding kings and pawns)
        total_pieces = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            for color in [chess.WHITE, chess.BLACK]:
                total_pieces += len(board.pieces(piece_type, color))
        
        # Phase determination based on piece count
        if total_pieces >= 20:  # Most pieces still on board
            return GamePhase.OPENING
        elif total_pieces >= 12:  # Some pieces traded
            return GamePhase.MIDDLEGAME
        else:  # Few pieces remaining
            return GamePhase.ENDGAME
    
    @staticmethod
    def calculate_mobility(board: chess.Board, color: chess.Color) -> int:
        """
        Calculate mobility (number of legal moves) for a color.
        
        Args:
            board: Chess position
            color: Color to calculate mobility for
            
        Returns:
            Number of legal moves
        """
        if board.turn == color:
            return len(list(board.legal_moves))
        else:
            # Temporarily switch turns
            board.turn = color
            mobility = len(list(board.legal_moves))
            board.turn = not color
            return mobility
    
    @staticmethod
    def evaluate_center_control(board: chess.Board) -> float:
        """
        Evaluate control of center squares.
        
        Args:
            board: Chess position
            
        Returns:
            Center control score (positive = white advantage)
        """
        score = 0
        
        for square in ChessUtilities.CENTER_SQUARES:
            white_attacks = len(board.attackers(chess.WHITE, square))
            black_attacks = len(board.attackers(chess.BLACK, square))
            
            # Piece on center square gets bonus
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    score += 20
                else:
                    score -= 20
            
            # Control of center square
            score += (white_attacks - black_attacks) * 5
        
        return score
    
    @staticmethod
    def evaluate_development(board: chess.Board) -> Dict[str, int]:
        """
        Evaluate piece development for both colors.
        
        Args:
            board: Chess position
            
        Returns:
            Development scores for both colors
        """
        def count_developed_pieces(color: chess.Color) -> int:
            developed = 0
            
            # Knights developed if not on starting squares
            knights = board.pieces(chess.KNIGHT, color)
            start_squares = [chess.B1, chess.G1] if color == chess.WHITE else [chess.B8, chess.G8]
            
            for knight_sq in knights:
                if knight_sq not in start_squares:
                    developed += 1
            
            # Bishops developed if not on starting squares
            bishops = board.pieces(chess.BISHOP, color)
            start_squares = [chess.C1, chess.F1] if color == chess.WHITE else [chess.C8, chess.F8]
            
            for bishop_sq in bishops:
                if bishop_sq not in start_squares:
                    developed += 1
            
            # Queen developed if moved (but not too early)
            queen_squares = board.pieces(chess.QUEEN, color)
            start_square = chess.D1 if color == chess.WHITE else chess.D8
            
            if queen_squares and start_square not in queen_squares:
                # Penalty for early queen development in opening
                if ChessUtilities.determine_game_phase(board) == GamePhase.OPENING:
                    developed -= 1
                else:
                    developed += 1
            
            return developed
        
        return {
            "white": count_developed_pieces(chess.WHITE),
            "black": count_developed_pieces(chess.BLACK)
        }
    
    @staticmethod
    def evaluate_king_safety(board: chess.Board, color: chess.Color) -> float:
        """
        Evaluate king safety for given color.
        
        Args:
            board: Chess position
            color: Color to evaluate
            
        Returns:
            King safety score (higher = safer)
        """
        king_square = board.king(color)
        if not king_square:
            return -1000  # No king = very unsafe!
        
        safety_score = 0
        
        # Check if king is castled
        if color == chess.WHITE:
            if king_square in [chess.G1, chess.C1]:
                safety_score += 50  # Castled king is safer
        else:
            if king_square in [chess.G8, chess.C8]:
                safety_score += 50
        
        # Penalty for king in center
        if king_square in ChessUtilities.EXTENDED_CENTER:
            safety_score -= 30
        
        # Check pawn shield
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Look for pawns in front of king
        direction = 1 if color == chess.WHITE else -1
        for file_offset in [-1, 0, 1]:
            check_file = king_file + file_offset
            if 0 <= check_file <= 7:
                for rank_offset in [1, 2]:
                    check_rank = king_rank + (rank_offset * direction)
                    if 0 <= check_rank <= 7:
                        check_square = chess.square(check_file, check_rank)
                        piece = board.piece_at(check_square)
                        
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            safety_score += 10 - (rank_offset * 2)
                            break
        
        # Check for attacking pieces near king
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color != color:
                distance = ChessUtilities.square_distance(square, king_square)
                if distance <= 2:
                    # Enemy piece near king = danger
                    safety_score -= (3 - distance) * 5
        
        return safety_score
    
    @staticmethod
    def square_distance(sq1: int, sq2: int) -> int:
        """
        Calculate distance between two squares.
        
        Args:
            sq1: First square
            sq2: Second square
            
        Returns:
            Distance between squares (max of rank/file distance)
        """
        file1, rank1 = chess.square_file(sq1), chess.square_rank(sq1)
        file2, rank2 = chess.square_file(sq2), chess.square_rank(sq2)
        
        return max(abs(file1 - file2), abs(rank1 - rank2))
    
    @staticmethod
    def get_position_info(board: chess.Board) -> PositionInfo:
        """
        Get comprehensive information about a position.
        
        Args:
            board: Chess position
            
        Returns:
            PositionInfo object with detailed analysis
        """
        return PositionInfo(
            fen=board.fen(),
            phase=ChessUtilities.determine_game_phase(board),
            material_balance=ChessUtilities.get_material_balance(board),
            piece_count=ChessUtilities.get_piece_counts(board),
            king_safety_white=ChessUtilities.evaluate_king_safety(board, chess.WHITE),
            king_safety_black=ChessUtilities.evaluate_king_safety(board, chess.BLACK),
            mobility_white=ChessUtilities.calculate_mobility(board, chess.WHITE),
            mobility_black=ChessUtilities.calculate_mobility(board, chess.BLACK),
            center_control=ChessUtilities.evaluate_center_control(board),
            development=ChessUtilities.evaluate_development(board),
            pawn_structure_score=0.0,  # TODO: Implement pawn structure evaluation
            tactical_complexity=0.0    # TODO: Implement tactical complexity assessment
        )
    
    @staticmethod
    def validate_fen(fen: str) -> bool:
        """
        Validate FEN string.
        
        Args:
            fen: FEN string to validate
            
        Returns:
            True if valid FEN, False otherwise
        """
        try:
            chess.Board(fen)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def fen_to_board(fen: str) -> Optional[chess.Board]:
        """
        Safely create board from FEN string.
        
        Args:
            fen: FEN string
            
        Returns:
            Board object or None if invalid FEN
        """
        try:
            return chess.Board(fen)
        except ValueError:
            logger.error(f"Invalid FEN: {fen}")
            return None
    
    @staticmethod
    def moves_to_san(board: chess.Board, moves: List[chess.Move]) -> List[str]:
        """
        Convert list of moves to SAN notation.
        
        Args:
            board: Starting position
            moves: List of moves
            
        Returns:
            List of moves in SAN notation
        """
        san_moves = []
        temp_board = board.copy()
        
        for move in moves:
            try:
                san = temp_board.san(move)
                san_moves.append(san)
                temp_board.push(move)
            except ValueError:
                logger.error(f"Invalid move: {move}")
                break
        
        return san_moves
    
    @staticmethod
    def pgn_to_moves(pgn_string: str) -> Optional[List[chess.Move]]:
        """
        Extract moves from PGN string.
        
        Args:
            pgn_string: PGN formatted game
            
        Returns:
            List of moves or None if invalid PGN
        """
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_string))
            if game:
                return list(game.mainline_moves())
        except Exception as e:
            logger.error(f"Error parsing PGN: {e}")
        
        return None
    
    @staticmethod
    def position_hash(board: chess.Board) -> str:
        """
        Generate hash for position (for caching/transposition table).
        
        Args:
            board: Chess position
            
        Returns:
            Hash string for position
        """
        # Use normalized FEN for position hash
        normalized_fen = ChessUtilities.normalize_fen(board.fen())
        return hashlib.md5(normalized_fen.encode()).hexdigest()


class PerformanceMonitor:
    """
    Monitor and track engine performance metrics.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.reset()
    
    def reset(self):
        """Reset all metrics."""
        self.start_time = time.time()
        self.positions_evaluated = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.depths_reached = []
        self.cutoffs = 0
        self.transposition_hits = 0
    
    def record_evaluation(self):
        """Record a position evaluation."""
        self.positions_evaluated += 1
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1
    
    def record_depth(self, depth: int):
        """Record search depth reached."""
        self.depths_reached.append(depth)
    
    def record_cutoff(self):
        """Record an alpha-beta cutoff."""
        self.cutoffs += 1
    
    def record_transposition_hit(self):
        """Record a transposition table hit."""
        self.transposition_hits += 1
    
    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current performance metrics.
        
        Returns:
            PerformanceMetrics object
        """
        elapsed_time = time.time() - self.start_time
        
        nps = int(self.positions_evaluated / elapsed_time) if elapsed_time > 0 else 0
        avg_depth = sum(self.depths_reached) / len(self.depths_reached) if self.depths_reached else 0
        
        return PerformanceMetrics(
            positions_evaluated=self.positions_evaluated,
            time_spent=elapsed_time,
            nodes_per_second=nps,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            average_depth=avg_depth,
            cutoffs=self.cutoffs,
            transposition_hits=self.transposition_hits
        )
    
    def print_summary(self):
        """Print performance summary."""
        metrics = self.get_metrics()
        
        print("\n=== Performance Summary ===")
        print(f"Positions evaluated: {metrics.positions_evaluated:,}")
        print(f"Time spent: {metrics.time_spent:.2f}s")
        print(f"Nodes per second: {metrics.nodes_per_second:,}")
        print(f"Average depth: {metrics.average_depth:.1f}")
        print(f"Cache hit rate: {(metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100):.1f}%" 
              if (metrics.cache_hits + metrics.cache_misses) > 0 else "No cache data")
        print(f"Alpha-beta cutoffs: {metrics.cutoffs}")
        print(f"Transposition hits: {metrics.transposition_hits}")


class DebugUtils:
    """
    Debugging utilities for chess engine development.
    """
    
    @staticmethod
    def print_board(board: chess.Board, flip: bool = False):
        """
        Print board in a readable format.
        
        Args:
            board: Chess position to print
            flip: Whether to flip board (black perspective)
        """
        print("\n" + str(board) + "\n")
        print(f"FEN: {board.fen()}")
        print(f"Turn: {'White' if board.turn else 'Black'}")
        print(f"Legal moves: {len(list(board.legal_moves))}")
        
        if board.is_check():
            print("CHECK!")
        if board.is_checkmate():
            print("CHECKMATE!")
        if board.is_stalemate():
            print("STALEMATE!")
    
    @staticmethod
    def analyze_move_generation(board: chess.Board) -> Dict[str, Any]:
        """
        Analyze move generation for debugging.
        
        Args:
            board: Chess position
            
        Returns:
            Move generation analysis
        """
        moves = list(board.legal_moves)
        
        move_types = {
            "captures": 0,
            "quiet": 0,
            "checks": 0,
            "promotions": 0,
            "castling": 0,
            "en_passant": 0
        }
        
        for move in moves:
            if board.is_capture(move):
                move_types["captures"] += 1
            else:
                move_types["quiet"] += 1
            
            if board.gives_check(move):
                move_types["checks"] += 1
            
            if move.promotion:
                move_types["promotions"] += 1
            
            if board.is_castling(move):
                move_types["castling"] += 1
            
            if board.is_en_passant(move):
                move_types["en_passant"] += 1
        
        return {
            "total_moves": len(moves),
            "move_breakdown": move_types,
            "sample_moves": [move.uci() for move in moves[:10]]
        }
    
    @staticmethod
    def save_position(board: chess.Board, filename: str, description: str = ""):
        """
        Save position to file for later analysis.
        
        Args:
            board: Chess position
            filename: File to save to
            description: Optional description
        """
        position_data = {
            "fen": board.fen(),
            "description": description,
            "timestamp": time.time(),
            "position_info": ChessUtilities.get_position_info(board).__dict__
        }
        
        with open(filename, 'w') as f:
            json.dump(position_data, f, indent=2, default=str)
        
        print(f"Position saved to {filename}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions for external use
def get_position_analysis(fen: str) -> Optional[PositionInfo]:
    """
    Get comprehensive position analysis from FEN.
    
    Args:
        fen: FEN string
        
    Returns:
        PositionInfo or None if invalid FEN
    """
    board = ChessUtilities.fen_to_board(fen)
    if board:
        return ChessUtilities.get_position_info(board)
    return None


def validate_move_sequence(start_fen: str, moves: List[str]) -> bool:
    """
    Validate a sequence of moves from starting position.
    
    Args:
        start_fen: Starting FEN position
        moves: List of moves in UCI or SAN format
        
    Returns:
        True if all moves are legal, False otherwise
    """
    board = ChessUtilities.fen_to_board(start_fen)
    if not board:
        return False
    
    try:
        for move_str in moves:
            # Try UCI format first
            try:
                move = chess.Move.from_uci(move_str)
            except ValueError:
                # Try SAN format
                move = board.parse_san(move_str)
            
            if move not in board.legal_moves:
                return False
            
            board.push(move)
        
        return True
    except ValueError:
        return False


def benchmark_position(fen: str, depth: int = 6) -> Dict[str, Any]:
    """
    Benchmark position analysis performance.
    
    Args:
        fen: Position to analyze
        depth: Search depth
        
    Returns:
        Benchmark results
    """
    from .unified_engine import UnifiedChessEngine
    
    engine = UnifiedChessEngine(rating=2000)
    
    start_time = time.time()
    result = engine.get_computer_move(fen)
    end_time = time.time()
    
    return {
        "position": fen,
        "analysis_time": end_time - start_time,
        "result": result,
        "nodes_searched": result.get("engine_info", {}).get("nodes_searched", 0) if result["success"] else 0
    }