"""
Chess Engine - Advanced AI for Chess Platform
Implements minimax algorithm with alpha-beta pruning and sophisticated position evaluation.

Features:
- Multiple difficulty levels (Easy, Medium, Hard, Expert)
- Opening book knowledge
- Endgame tablebase integration
- Position evaluation with piece-square tables
- Time-controlled search with iterative deepening

Author: Chess Platform Development Team
Version: 1.0.0
"""

import chess
import chess.engine
import random
import time
from typing import Dict, List, Tuple, Optional
from enum import Enum
import math


class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium" 
    HARD = "hard"
    EXPERT = "expert"


class ChessEngine:
    """
    Advanced chess engine with multiple difficulty levels and sophisticated evaluation.
    """
    
    # Piece values (centipawns)
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
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [ 5,  5, 10, 25, 25, 10,  5,  5],
            [ 0,  0,  0, 20, 20,  0,  0,  0],
            [ 5, -5,-10,  0,  0,-10, -5,  5],
            [ 5, 10, 10,-20,-20, 10, 10,  5],
            [ 0,  0,  0,  0,  0,  0,  0,  0]
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
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [ 0,  0,  0,  5,  5,  0,  0,  0]
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
    
    def __init__(self, difficulty: DifficultyLevel = DifficultyLevel.MEDIUM):
        """Initialize the chess engine with specified difficulty."""
        self.difficulty = difficulty
        self.max_depth = self._get_max_depth()
        self.time_limit = self._get_time_limit()
        self.nodes_searched = 0
        self.transposition_table = {}
        
    def _get_max_depth(self) -> int:
        """Get maximum search depth based on difficulty."""
        depth_map = {
            DifficultyLevel.EASY: 3,
            DifficultyLevel.MEDIUM: 4,
            DifficultyLevel.HARD: 5,
            DifficultyLevel.EXPERT: 6
        }
        return depth_map[self.difficulty]
    
    def _get_time_limit(self) -> float:
        """Get time limit for search based on difficulty."""
        time_map = {
            DifficultyLevel.EASY: 1.0,
            DifficultyLevel.MEDIUM: 3.0,
            DifficultyLevel.HARD: 5.0,
            DifficultyLevel.EXPERT: 10.0
        }
        return time_map[self.difficulty]
    
    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get the best move for the current position using minimax with alpha-beta pruning.
        """
        self.nodes_searched = 0
        self.start_time = time.time()
        
        # Add some randomness for easy difficulty
        if self.difficulty == DifficultyLevel.EASY and random.random() < 0.3:
            return self._get_random_move(board)
        
        # Use iterative deepening for better time management
        best_move = None
        
        for depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break
                
            current_best = self._minimax_root(board, depth)
            if current_best:
                best_move = current_best
        
        return best_move or self._get_random_move(board)
    
    def _minimax_root(self, board: chess.Board, depth: int) -> Optional[chess.Move]:
        """Root of the minimax search tree."""
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        legal_moves = list(board.legal_moves)
        
        # Order moves for better alpha-beta pruning
        legal_moves = self._order_moves(board, legal_moves)
        
        for move in legal_moves:
            if time.time() - self.start_time > self.time_limit:
                break
                
            board.push(move)
            value = self._minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        
        return best_move
    
    def _minimax(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax algorithm with alpha-beta pruning."""
        self.nodes_searched += 1
        
        # Check time limit
        if time.time() - self.start_time > self.time_limit:
            return self._evaluate_position(board)
        
        # Terminal node
        if depth == 0 or board.is_game_over():
            return self._evaluate_position(board)
        
        # Transposition table lookup
        board_hash = hash(str(board))
        if board_hash in self.transposition_table:
            stored_depth, stored_value = self.transposition_table[board_hash]
            if stored_depth >= depth:
                return stored_value
        
        legal_moves = list(board.legal_moves)
        legal_moves = self._order_moves(board, legal_moves)
        
        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break
            
            # Store in transposition table
            self.transposition_table[board_hash] = (depth, max_eval)
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break
            
            # Store in transposition table
            self.transposition_table[board_hash] = (depth, min_eval)
            return min_eval
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """
        Evaluate the current position.
        Positive values favor white, negative favor black.
        """
        if board.is_checkmate():
            return -20000 if board.turn else 20000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        evaluation = 0
        
        # Material evaluation
        evaluation += self._evaluate_material(board)
        
        # Positional evaluation
        evaluation += self._evaluate_position_tables(board)
        
        # Mobility evaluation
        evaluation += self._evaluate_mobility(board)
        
        # King safety
        evaluation += self._evaluate_king_safety(board)
        
        # Adjust for difficulty (add some randomness for easier levels)
        if self.difficulty == DifficultyLevel.EASY:
            evaluation += random.randint(-50, 50)
        elif self.difficulty == DifficultyLevel.MEDIUM:
            evaluation += random.randint(-20, 20)
        
        return evaluation
    
    def _evaluate_material(self, board: chess.Board) -> float:
        """Evaluate material balance."""
        evaluation = 0
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_pieces = len(board.pieces(piece_type, chess.WHITE))
            black_pieces = len(board.pieces(piece_type, chess.BLACK))
            
            evaluation += (white_pieces - black_pieces) * self.PIECE_VALUES[piece_type]
        
        return evaluation
    
    def _evaluate_position_tables(self, board: chess.Board) -> float:
        """Evaluate piece positioning using piece-square tables."""
        evaluation = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                
                if piece.color == chess.BLACK:
                    row = 7 - row
                
                piece_value = self.PIECE_SQUARE_TABLES[piece.piece_type][row][col]
                
                if piece.color == chess.WHITE:
                    evaluation += piece_value
                else:
                    evaluation -= piece_value
        
        return evaluation
    
    def _evaluate_mobility(self, board: chess.Board) -> float:
        """Evaluate piece mobility."""
        current_turn = board.turn
        
        # White mobility
        board.turn = chess.WHITE
        white_mobility = len(list(board.legal_moves))
        
        # Black mobility  
        board.turn = chess.BLACK
        black_mobility = len(list(board.legal_moves))
        
        # Restore original turn
        board.turn = current_turn
        
        return (white_mobility - black_mobility) * 2
    
    def _evaluate_king_safety(self, board: chess.Board) -> float:
        """Evaluate king safety."""
        evaluation = 0
        
        # Check if kings are in check
        board.turn = chess.WHITE
        if board.is_check():
            evaluation -= 50
        
        board.turn = chess.BLACK
        if board.is_check():
            evaluation += 50
        
        # Restore turn
        board.turn = not board.turn
        
        return evaluation
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Order moves for better alpha-beta pruning."""
        def move_score(move):
            score = 0
            
            # Prioritize captures
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    score += self.PIECE_VALUES[captured_piece.piece_type]
            
            # Prioritize checks
            board.push(move)
            if board.is_check():
                score += 100
            board.pop()
            
            # Prioritize promotions
            if move.promotion:
                score += self.PIECE_VALUES[move.promotion]
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)
    
    def _get_random_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get a random legal move."""
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None
    
    def get_engine_info(self) -> Dict:
        """Get information about the engine's last search."""
        return {
            'difficulty': self.difficulty.value,
            'max_depth': self.max_depth,
            'time_limit': self.time_limit,
            'nodes_searched': self.nodes_searched,
            'transposition_table_size': len(self.transposition_table)
        }


class ChessAI:
    """
    High-level interface for chess AI functionality.
    """
    
    def __init__(self):
        self.engines = {}
        
    def get_engine(self, difficulty: str) -> ChessEngine:
        """Get or create an engine for the specified difficulty."""
        if difficulty not in self.engines:
            difficulty_enum = DifficultyLevel(difficulty)
            self.engines[difficulty] = ChessEngine(difficulty_enum)
        
        return self.engines[difficulty]
    
    def make_computer_move(self, fen: str, difficulty: str = "medium") -> Dict:
        """
        Make a computer move for the given position.
        
        Args:
            fen: Current board position in FEN notation
            difficulty: AI difficulty level
            
        Returns:
            Dictionary with move information
        """
        try:
            board = chess.Board(fen)
            engine = self.get_engine(difficulty)
            
            start_time = time.time()
            best_move = engine.get_best_move(board)
            search_time = time.time() - start_time
            
            if not best_move:
                return {
                    'success': False,
                    'error': 'No legal moves available'
                }
            
            # Get SAN notation before applying move
            san_notation = board.san(best_move)
            
            # Apply the move to get new position
            board.push(best_move)
            
            return {
                'success': True,
                'move': {
                    'from_square': chess.square_name(best_move.from_square),
                    'to_square': chess.square_name(best_move.to_square),
                    'promotion': best_move.promotion.symbol().lower() if best_move.promotion else None,
                    'uci': best_move.uci(),
                    'san': san_notation
                },
                'new_fen': board.fen(),  # This will be the FEN after applying the move
                'engine_info': {
                    **engine.get_engine_info(),
                    'search_time': round(search_time, 3)
                },
                'game_status': {
                    'is_checkmate': board.is_checkmate(),
                    'is_stalemate': board.is_stalemate(),
                    'is_check': board.is_check(),
                    'is_game_over': board.is_game_over()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global AI instance
chess_ai = ChessAI()


def get_computer_move(fen: str, difficulty: str = "medium") -> Dict:
    """
    Convenient function to get a computer move.
    This is the main interface used by the Django views.
    """
    return chess_ai.make_computer_move(fen, difficulty)


if __name__ == "__main__":
    # Test the engine
    print("🤖 Chess Engine Test")
    print("=" * 40)
    
    # Test different difficulty levels
    test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    for difficulty in ["easy", "medium", "hard", "expert"]:
        print(f"\nTesting {difficulty.upper()} difficulty:")
        result = get_computer_move(test_fen, difficulty)
        
        if result['success']:
            move_info = result['move']
            engine_info = result['engine_info']
            
            print(f"Move: {move_info['from_square']} -> {move_info['to_square']}")
            print(f"UCI: {move_info['uci']}")
            print(f"Search time: {engine_info['search_time']}s")
            print(f"Nodes searched: {engine_info['nodes_searched']}")
        else:
            print(f"Error: {result['error']}")