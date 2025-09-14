"""
Chess Position Evaluation Module

Comprehensive position evaluation system that adapts to different rating levels.
Includes material, positional, tactical, and strategic evaluation components.
"""

import chess
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class EvaluationComponents:
    """Container for different evaluation components."""
    material: float = 0.0
    positional: float = 0.0
    tactical: float = 0.0
    king_safety: float = 0.0
    mobility: float = 0.0
    pawn_structure: float = 0.0
    endgame: float = 0.0
    total: float = 0.0


class PositionEvaluator:
    """
    Advanced position evaluation with rating-based complexity.
    
    Lower ratings focus on basic material and simple positional factors.
    Higher ratings include complex tactical and strategic considerations.
    """
    
    # Enhanced piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    # Piece-square tables for positional evaluation
    PIECE_SQUARE_TABLES = {
        chess.PAWN: [
            [  0,  0,  0,  0,  0,  0,  0,  0],
            [ 50, 50, 50, 50, 50, 50, 50, 50],
            [ 10, 10, 20, 30, 30, 20, 10, 10],
            [  5,  5, 10, 25, 25, 10,  5,  5],
            [  0,  0,  0, 20, 20,  0,  0,  0],
            [  5, -5,-10,  0,  0,-10, -5,  5],
            [  5, 10, 10,-20,-20, 10, 10,  5],
            [  0,  0,  0,  0,  0,  0,  0,  0]
        ],
        chess.KNIGHT: [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ],
        chess.BISHOP: [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ],
        chess.ROOK: [
            [  0,  0,  0,  0,  0,  0,  0,  0],
            [  5, 10, 10, 10, 10, 10, 10,  5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [  0,  0,  0,  5,  5,  0,  0,  0]
        ],
        chess.QUEEN: [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [ -5,  0,  5,  5,  5,  5,  0, -5],
            [  0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ],
        chess.KING: [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [ 20, 20,  0,  0,  0,  0, 20, 20],
            [ 20, 30, 10,  0,  0, 10, 30, 20]
        ]
    }
    
    # Endgame king table (more active king)
    KING_ENDGAME_TABLE = [
        [-50,-40,-30,-20,-20,-30,-40,-50],
        [-30,-20,-10,  0,  0,-10,-20,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-30,  0,  0,  0,  0,-30,-30],
        [-50,-30,-30,-30,-30,-30,-30,-50]
    ]
    
    def __init__(self, rating: int):
        """Initialize evaluator for specific rating level."""
        self.rating = rating
        self.endgame_threshold = 1300  # Points below which we consider endgame
    
    def evaluate_position(self, board: chess.Board, config) -> EvaluationComponents:
        """
        Comprehensive position evaluation.
        
        Args:
            board: Current chess position
            config: Rating configuration object
            
        Returns:
            EvaluationComponents with breakdown of evaluation
        """
        components = EvaluationComponents()
        
        # Check for terminal positions
        if board.is_checkmate():
            components.total = -20000 if board.turn else 20000
            return components
        
        if board.is_stalemate() or board.is_insufficient_material():
            components.total = 0
            return components
        
        # Material evaluation (always included)
        components.material = self._evaluate_material(board)
        
        # Positional evaluation (weighted by rating)
        if config.positional_weight > 0:
            components.positional = self._evaluate_positional(board, config)
        
        # Tactical evaluation (for intermediate+ players)
        if config.tactical_awareness > 0.3:
            components.tactical = self._evaluate_tactical(board, config)
        
        # King safety (important at all levels)
        components.king_safety = self._evaluate_king_safety(board, config)
        
        # Mobility (for higher ratings)
        if self.rating >= 1000:
            components.mobility = self._evaluate_mobility(board, config)
        
        # Pawn structure (for advanced players)
        if self.rating >= 1400:
            components.pawn_structure = self._evaluate_pawn_structure(board, config)
        
        # Endgame evaluation (for experienced players)
        if self.rating >= 1200 and self._is_endgame(board):
            components.endgame = self._evaluate_endgame(board, config)
        
        # Combine all components
        components.total = (
            components.material +
            components.positional * config.positional_weight +
            components.tactical * config.tactical_awareness +
            components.king_safety +
            components.mobility * 0.5 +
            components.pawn_structure * 0.3 +
            components.endgame * 0.4
        )
        
        # Add evaluation noise for lower ratings
        if config.evaluation_noise > 0:
            noise = random.uniform(-config.evaluation_noise, config.evaluation_noise)
            components.total += noise
        
        return components
    
    def _evaluate_material(self, board: chess.Board) -> float:
        """Calculate material balance."""
        evaluation = 0
        
        for piece_type in self.PIECE_VALUES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            material_diff = white_count - black_count
            evaluation += material_diff * self.PIECE_VALUES[piece_type]
        
        return evaluation
    
    def _evaluate_positional(self, board: chess.Board, config) -> float:
        """Evaluate piece positioning using piece-square tables."""
        evaluation = 0
        is_endgame = self._is_endgame(board)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
            
            # Get piece-square table value
            row = 7 - (square // 8)
            col = square % 8
            
            # Flip row for black pieces
            if piece.color == chess.BLACK:
                row = 7 - row
            
            # Use endgame king table in endgame
            if piece.piece_type == chess.KING and is_endgame:
                piece_value = self.KING_ENDGAME_TABLE[row][col]
            else:
                piece_value = self.PIECE_SQUARE_TABLES[piece.piece_type][row][col]
            
            # Apply to evaluation
            if piece.color == chess.WHITE:
                evaluation += piece_value
            else:
                evaluation -= piece_value
        
        return evaluation
    
    def _evaluate_tactical(self, board: chess.Board, config) -> float:
        """Evaluate tactical opportunities and threats."""
        evaluation = 0
        
        # Check for hanging pieces
        evaluation += self._evaluate_hanging_pieces(board) * config.tactical_awareness
        
        # Check for pins and skewers (higher ratings only)
        if self.rating >= 1200:
            evaluation += self._evaluate_pins_and_skewers(board) * config.tactical_awareness
        
        # Check for forks and double attacks
        if self.rating >= 1000:
            evaluation += self._evaluate_forks(board) * config.tactical_awareness
        
        return evaluation
    
    def _evaluate_king_safety(self, board: chess.Board, config) -> float:
        """Evaluate king safety for both sides."""
        evaluation = 0
        
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        
        if white_king_square and black_king_square:
            # Evaluate pawn shield
            white_safety = self._king_pawn_shield_score(board, white_king_square, chess.WHITE)
            black_safety = self._king_pawn_shield_score(board, black_king_square, chess.BLACK)
            
            evaluation += (white_safety - black_safety) * 20
            
            # Penalty for king in center (non-endgame)
            if not self._is_endgame(board):
                if chess.square_file(white_king_square) in [3, 4]:  # d or e file
                    evaluation -= 50
                if chess.square_file(black_king_square) in [3, 4]:
                    evaluation += 50
        
        return evaluation
    
    def _evaluate_mobility(self, board: chess.Board, config) -> float:
        """Evaluate piece mobility."""
        white_mobility = len(list(board.legal_moves))
        
        # Switch sides to count black mobility
        board.turn = not board.turn
        black_mobility = len(list(board.legal_moves))
        board.turn = not board.turn
        
        return (white_mobility - black_mobility) * 2
    
    def _evaluate_pawn_structure(self, board: chess.Board, config) -> float:
        """Evaluate pawn structure quality."""
        evaluation = 0
        
        # Doubled pawns penalty
        evaluation += self._evaluate_doubled_pawns(board)
        
        # Isolated pawns penalty
        evaluation += self._evaluate_isolated_pawns(board)
        
        # Passed pawns bonus
        evaluation += self._evaluate_passed_pawns(board)
        
        # Backward pawns penalty
        evaluation += self._evaluate_backward_pawns(board)
        
        return evaluation
    
    def _evaluate_endgame(self, board: chess.Board, config) -> float:
        """Evaluate endgame-specific factors."""
        evaluation = 0
        
        # King activity in endgame
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king and black_king:
            # Centralized kings are better in endgame
            white_center_distance = self._distance_to_center(white_king)
            black_center_distance = self._distance_to_center(black_king)
            
            evaluation += (black_center_distance - white_center_distance) * 10
            
            # Opposition in king and pawn endgames
            if self._is_king_pawn_endgame(board):
                if self._has_opposition(board, white_king, black_king):
                    evaluation += 50 if board.turn == chess.WHITE else -50
        
        return evaluation
    
    def _evaluate_hanging_pieces(self, board: chess.Board) -> float:
        """Check for hanging (undefended) pieces."""
        evaluation = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
            
            # Skip pawns and kings
            if piece.piece_type in [chess.PAWN, chess.KING]:
                continue
            
            if self._is_piece_hanging(board, square):
                piece_value = self.PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    evaluation -= piece_value * 0.5  # Penalty for white hanging piece
                else:
                    evaluation += piece_value * 0.5   # Bonus for black hanging piece
        
        return evaluation
    
    def _is_piece_hanging(self, board: chess.Board, square: int) -> bool:
        """Check if piece on square is hanging (undefended)."""
        piece = board.piece_at(square)
        if not piece:
            return False
        
        # Check if piece is attacked
        if not board.is_attacked_by(not piece.color, square):
            return False
        
        # Check if piece is defended
        if board.is_attacked_by(piece.color, square):
            return False
        
        return True
    
    def _king_pawn_shield_score(self, board: chess.Board, king_square: int, color: chess.Color) -> int:
        """Evaluate pawn shield in front of king."""
        score = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check files around king
        for file_offset in [-1, 0, 1]:
            check_file = king_file + file_offset
            if check_file < 0 or check_file > 7:
                continue
            
            # Look for pawns in front of king
            direction = 1 if color == chess.WHITE else -1
            for rank_offset in [1, 2, 3]:
                check_rank = king_rank + (rank_offset * direction)
                if check_rank < 0 or check_rank > 7:
                    break
                
                check_square = chess.square(check_file, check_rank)
                piece = board.piece_at(check_square)
                
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    score += 10 - (rank_offset * 2)  # Closer pawns are better
                    break
        
        return score
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Determine if position is in endgame phase."""
        total_material = 0
        
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            for color in [chess.WHITE, chess.BLACK]:
                count = len(board.pieces(piece_type, color))
                total_material += count * self.PIECE_VALUES[piece_type]
        
        return total_material < self.endgame_threshold
    
    def _distance_to_center(self, square: int) -> int:
        """Calculate distance from square to center of board."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        center_distance = max(abs(file - 3.5), abs(rank - 3.5))
        return int(center_distance)
    
    # Placeholder methods for advanced evaluations
    def _evaluate_pins_and_skewers(self, board: chess.Board) -> float:
        """Evaluate pins and skewers."""
        return 0  # TODO: Implement pin/skewer detection
    
    def _evaluate_forks(self, board: chess.Board) -> float:
        """Evaluate fork opportunities."""
        return 0  # TODO: Implement fork detection
    
    def _evaluate_doubled_pawns(self, board: chess.Board) -> float:
        """Evaluate doubled pawn penalty."""
        return 0  # TODO: Implement doubled pawn evaluation
    
    def _evaluate_isolated_pawns(self, board: chess.Board) -> float:
        """Evaluate isolated pawn penalty."""
        return 0  # TODO: Implement isolated pawn evaluation
    
    def _evaluate_passed_pawns(self, board: chess.Board) -> float:
        """Evaluate passed pawn bonus."""
        return 0  # TODO: Implement passed pawn evaluation
    
    def _evaluate_backward_pawns(self, board: chess.Board) -> float:
        """Evaluate backward pawn penalty."""
        return 0  # TODO: Implement backward pawn evaluation
    
    def _is_king_pawn_endgame(self, board: chess.Board) -> bool:
        """Check if it's a king and pawn endgame."""
        return False  # TODO: Implement king-pawn endgame detection
    
    def _has_opposition(self, board: chess.Board, white_king: int, black_king: int) -> bool:
        """Check if the side to move has opposition."""
        return False  # TODO: Implement opposition detection