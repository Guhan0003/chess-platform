"""
Chess Position Evaluation Module

Comprehensive position evaluation system that adapts to different rating levels.
Includes material, positional, tactical, and strategic evaluation components.
Enhanced with professional AdvancedEvaluator for master-level analysis.
"""

import chess
import random
import math
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


class AdvancedEvaluator:
    """
    Advanced chess position evaluator with professional-level analysis.
    """
    
    # Base piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0  # King safety handled separately
    }
    
    # Piece-square tables (from White's perspective)
    PAWN_TABLE = [
        [  0,   0,   0,   0,   0,   0,   0,   0],
        [ 50,  50,  50,  50,  50,  50,  50,  50],
        [ 10,  10,  20,  30,  30,  20,  10,  10],
        [  5,   5,  10,  25,  25,  10,   5,   5],
        [  0,   0,   0,  20,  20,   0,   0,   0],
        [  5,  -5, -10,   0,   0, -10,  -5,   5],
        [  5,  10,  10, -20, -20,  10,  10,   5],
        [  0,   0,   0,   0,   0,   0,   0,   0]
    ]
    
    KNIGHT_TABLE = [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20,   0,   0,   0,   0, -20, -40],
        [-30,   0,  10,  15,  15,  10,   0, -30],
        [-30,   5,  15,  20,  20,  15,   5, -30],
        [-30,   0,  15,  20,  20,  15,   0, -30],
        [-30,   5,  10,  15,  15,  10,   5, -30],
        [-40, -20,   0,   5,   5,   0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50]
    ]
    
    BISHOP_TABLE = [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10,   0,   0,   0,   0,   0,   0, -10],
        [-10,   0,   5,  10,  10,   5,   0, -10],
        [-10,   5,   5,  10,  10,   5,   5, -10],
        [-10,   0,  10,  10,  10,  10,   0, -10],
        [-10,  10,  10,  10,  10,  10,  10, -10],
        [-10,   5,   0,   0,   0,   0,   5, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20]
    ]
    
    ROOK_TABLE = [
        [  0,   0,   0,   0,   0,   0,   0,   0],
        [  5,  10,  10,  10,  10,  10,  10,   5],
        [ -5,   0,   0,   0,   0,   0,   0,  -5],
        [ -5,   0,   0,   0,   0,   0,   0,  -5],
        [ -5,   0,   0,   0,   0,   0,   0,  -5],
        [ -5,   0,   0,   0,   0,   0,   0,  -5],
        [ -5,   0,   0,   0,   0,   0,   0,  -5],
        [  0,   0,   0,   5,   5,   0,   0,   0]
    ]
    
    QUEEN_TABLE = [
        [-20, -10, -10,  -5,  -5, -10, -10, -20],
        [-10,   0,   0,   0,   0,   0,   0, -10],
        [-10,   0,   5,   5,   5,   5,   0, -10],
        [ -5,   0,   5,   5,   5,   5,   0,  -5],
        [  0,   0,   5,   5,   5,   5,   0,  -5],
        [-10,   5,   5,   5,   5,   5,   0, -10],
        [-10,   0,   5,   0,   0,   0,   0, -10],
        [-20, -10, -10,  -5,  -5, -10, -10, -20]
    ]
    
    KING_MIDDLE_GAME = [
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [ 20,  20,   0,   0,   0,   0,  20,  20],
        [ 20,  30,  10,   0,   0,  10,  30,  20]
    ]
    
    KING_END_GAME = [
        [-50, -40, -30, -20, -20, -30, -40, -50],
        [-30, -20, -10,   0,   0, -10, -20, -30],
        [-30, -10,  20,  30,  30,  20, -10, -30],
        [-30, -10,  30,  40,  40,  30, -10, -30],
        [-30, -10,  30,  40,  40,  30, -10, -30],
        [-30, -10,  20,  30,  30,  20, -10, -30],
        [-30, -30,   0,   0,   0,   0, -30, -30],
        [-50, -30, -30, -30, -30, -30, -30, -50]
    ]
    
    def __init__(self, rating: int = 2000):
        """Initialize evaluator with rating-specific parameters."""
        self.rating = rating
        self.evaluation_depth = self._get_evaluation_depth(rating)
    
    def _get_evaluation_depth(self, rating: int) -> int:
        """Get evaluation depth based on rating."""
        if rating < 1000:
            return 1  # Basic evaluation only
        elif rating < 1600:
            return 2  # Add positional factors
        else:
            return 3  # Full evaluation
    
    def evaluate(self, board: chess.Board) -> float:
        """
        Evaluate chess position.
        
        Args:
            board: Chess position to evaluate
            
        Returns:
            Evaluation score (positive = good for current player)
        """
        if board.is_checkmate():
            return -29999 + len(board.move_stack)
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0.0
        
        # Determine game phase
        is_endgame = self._is_endgame(board)
        
        # Calculate evaluation components
        material_score = self._evaluate_material(board)
        positional_score = self._evaluate_position(board, is_endgame)
        
        if self.evaluation_depth >= 2:
            king_safety = self._evaluate_king_safety(board, is_endgame)
            mobility = self._evaluate_mobility(board)
        else:
            king_safety = 0.0
            mobility = 0.0
        
        if self.evaluation_depth >= 3:
            pawn_structure = self._evaluate_pawn_structure(board)
        else:
            pawn_structure = 0.0
        
        # Combine scores
        total_score = (
            material_score + 
            positional_score + 
            king_safety * 0.3 + 
            mobility * 0.2 + 
            pawn_structure * 0.1
        )
        
        # Apply rating-based evaluation noise for lower ratings
        if self.rating < 1400:
            noise_factor = (1400 - self.rating) / 1000.0
            noise = random.uniform(-noise_factor, noise_factor)
            total_score += noise
        
        return total_score
    
    def _evaluate_material(self, board: chess.Board) -> float:
        """Evaluate material balance."""
        material = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.PIECE_VALUES.get(piece.piece_type, 0)
                if piece.color == board.turn:
                    material += value
                else:
                    material -= value
        
        return material / 100.0  # Convert to pawn units
    
    def _evaluate_position(self, board: chess.Board, is_endgame: bool) -> float:
        """Evaluate positional factors using piece-square tables."""
        position_score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                table_score = self._get_piece_square_value(piece, square, is_endgame)
                
                if piece.color == board.turn:
                    position_score += table_score
                else:
                    position_score -= table_score
        
        return position_score / 100.0  # Convert to pawn units
    
    def _get_piece_square_value(self, piece: chess.Piece, square: int, is_endgame: bool) -> float:
        """Get piece-square table value for piece on square."""
        row = 7 - chess.square_rank(square) if piece.color == chess.WHITE else chess.square_rank(square)
        col = chess.square_file(square)
        
        if piece.piece_type == chess.PAWN:
            return self.PAWN_TABLE[row][col]
        elif piece.piece_type == chess.KNIGHT:
            return self.KNIGHT_TABLE[row][col]
        elif piece.piece_type == chess.BISHOP:
            return self.BISHOP_TABLE[row][col]
        elif piece.piece_type == chess.ROOK:
            return self.ROOK_TABLE[row][col]
        elif piece.piece_type == chess.QUEEN:
            return self.QUEEN_TABLE[row][col]
        elif piece.piece_type == chess.KING:
            if is_endgame:
                return self.KING_END_GAME[row][col]
            else:
                return self.KING_MIDDLE_GAME[row][col]
        
        return 0.0
    
    def _evaluate_king_safety(self, board: chess.Board, is_endgame: bool) -> float:
        """Evaluate king safety."""
        if is_endgame:
            return 0.0  # King safety less important in endgame
        
        safety_score = 0.0
        
        # Evaluate current player's king safety
        king_square = board.king(board.turn)
        if king_square:
            safety_score += self._get_king_safety_score(board, king_square, board.turn)
        
        # Evaluate opponent's king safety
        opponent_color = not board.turn
        opponent_king = board.king(opponent_color)
        if opponent_king:
            safety_score -= self._get_king_safety_score(board, opponent_king, opponent_color)
        
        return safety_score
    
    def _get_king_safety_score(self, board: chess.Board, king_square: int, color: bool) -> float:
        """Calculate king safety score for specific king."""
        safety = 0.0
        
        # Pawn shield evaluation
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check pawn shield in front of king
        direction = 1 if color == chess.WHITE else -1
        
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if 0 <= file <= 7:
                shield_rank = king_rank + direction
                if 0 <= shield_rank <= 7:
                    shield_square = chess.square(file, shield_rank)
                    piece = board.piece_at(shield_square)
                    
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        safety += 10  # Bonus for pawn shield
                    else:
                        safety -= 5   # Penalty for missing pawn
        
        # Check for attacks near king
        king_zone = self._get_king_zone(king_square)
        for square in king_zone:
            if board.is_attacked_by(not color, square):
                safety -= 8  # Penalty for attacks in king zone
        
        return safety
    
    def _get_king_zone(self, king_square: int) -> List[int]:
        """Get squares in king's immediate vicinity."""
        king_zone = []
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        for rank_offset in [-1, 0, 1]:
            for file_offset in [-1, 0, 1]:
                if rank_offset == 0 and file_offset == 0:
                    continue
                
                new_rank = king_rank + rank_offset
                new_file = king_file + file_offset
                
                if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
                    king_zone.append(chess.square(new_file, new_rank))
        
        return king_zone
    
    def _evaluate_mobility(self, board: chess.Board) -> float:
        """Evaluate piece mobility."""
        current_player_moves = len(list(board.legal_moves))
        
        # Switch turns to count opponent moves
        board.push(chess.Move.null())
        opponent_moves = len(list(board.legal_moves))
        board.pop()
        
        mobility_difference = current_player_moves - opponent_moves
        return mobility_difference * 0.1
    
    def _evaluate_pawn_structure(self, board: chess.Board) -> float:
        """Evaluate pawn structure."""
        pawn_score = 0.0
        
        # Get pawn positions for both colors
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        
        # Evaluate current player's pawns
        my_pawns = white_pawns if board.turn == chess.WHITE else black_pawns
        opponent_pawns = black_pawns if board.turn == chess.WHITE else white_pawns
        
        # Doubled pawns penalty
        pawn_score -= self._count_doubled_pawns(my_pawns) * 5
        pawn_score += self._count_doubled_pawns(opponent_pawns) * 5
        
        # Isolated pawns penalty
        pawn_score -= self._count_isolated_pawns(my_pawns) * 8
        pawn_score += self._count_isolated_pawns(opponent_pawns) * 8
        
        # Passed pawns bonus
        pawn_score += self._count_passed_pawns(board, my_pawns, board.turn) * 15
        pawn_score -= self._count_passed_pawns(board, opponent_pawns, not board.turn) * 15
        
        return pawn_score
    
    def _count_doubled_pawns(self, pawns: chess.SquareSet) -> int:
        """Count doubled pawns."""
        file_counts = [0] * 8
        
        for pawn_square in pawns:
            file = chess.square_file(pawn_square)
            file_counts[file] += 1
        
        return sum(max(0, count - 1) for count in file_counts)
    
    def _count_isolated_pawns(self, pawns: chess.SquareSet) -> int:
        """Count isolated pawns."""
        files_with_pawns = set()
        
        for pawn_square in pawns:
            files_with_pawns.add(chess.square_file(pawn_square))
        
        isolated_count = 0
        
        for pawn_square in pawns:
            file = chess.square_file(pawn_square)
            adjacent_files = {file - 1, file + 1}
            
            if not adjacent_files.intersection(files_with_pawns):
                isolated_count += 1
        
        return isolated_count
    
    def _count_passed_pawns(self, board: chess.Board, pawns: chess.SquareSet, color: bool) -> int:
        """Count passed pawns."""
        passed_count = 0
        opponent_pawns = board.pieces(chess.PAWN, not color)
        
        for pawn_square in pawns:
            if self._is_passed_pawn(pawn_square, opponent_pawns, color):
                passed_count += 1
        
        return passed_count
    
    def _is_passed_pawn(self, pawn_square: int, opponent_pawns: chess.SquareSet, color: bool) -> bool:
        """Check if pawn is passed."""
        pawn_file = chess.square_file(pawn_square)
        pawn_rank = chess.square_rank(pawn_square)
        
        # Check files that can block this pawn
        files_to_check = [pawn_file - 1, pawn_file, pawn_file + 1]
        files_to_check = [f for f in files_to_check if 0 <= f <= 7]
        
        # Direction of pawn advance
        direction = 1 if color == chess.WHITE else -1
        
        # Check all squares in front of pawn
        for rank in range(pawn_rank + direction, 8 if color == chess.WHITE else -1, direction):
            for file in files_to_check:
                check_square = chess.square(file, rank)
                if check_square in opponent_pawns:
                    return False
        
        return True
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Determine if position is in endgame."""
        # Count pieces (excluding pawns and kings)
        piece_count = 0
        
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
        
        # Endgame if few pieces remain
        return piece_count <= 6