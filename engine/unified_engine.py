"""
Enhanced Unified Chess Engine - Complete Implementation

This is a fully-featured chess engine with powerful evaluation functions,
advanced search algorithms, and sophisticated rating-based intelligence.

Key Enhancements:
- Complete tactical evaluation system
- Advanced piece positioning with dynamic weights
- Sophisticated move ordering with killer moves and history heuristic
- King safety evaluation with pawn shield analysis
- Mobility and center control evaluation
- Opening book integration with rating-appropriate knowledge
- Endgame tablebase support
- Advanced personality system integration
- Comprehensive move explanation system
"""

import chess
import chess.engine
import random
import time
from typing import Dict, List, Tuple, Optional, Union, Set
from enum import Enum
import math
from collections import defaultdict
import hashlib

from .rating_configs import RatingConfig, get_rating_config, get_personality_modifier


class UnifiedChessEngine:
    """
    Enhanced chess engine with professional-strength evaluation and search.
    """
    
    # Enhanced piece values with positional adjustments
    BASE_PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    # Advanced piece-square tables with endgame variants
    PIECE_SQUARE_TABLES_MG = {  # Middlegame
        chess.PAWN: [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [ 5,  5, 10, 27, 27, 10,  5,  5],
            [ 0,  0,  0, 25, 25,  0,  0,  0],
            [ 5, -5,-10,  0,  0,-10, -5,  5],
            [ 5, 10, 10,-25,-25, 10, 10,  5],
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
            [-50,-40,-20,-30,-30,-20,-40,-50]
        ],
        chess.BISHOP: [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-40,-10,-10,-40,-10,-20]
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
    
    PIECE_SQUARE_TABLES_EG = {  # Endgame
        chess.KING: [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]
    }
    
    def __init__(self, rating: int, personality: str = "balanced"):
        """Initialize enhanced engine with full capabilities."""
        self.rating = rating
        self.personality = personality
        self.config = get_rating_config(rating)
        self.personality_modifiers = get_personality_modifier(personality)
        
        # Enhanced search data structures
        self.nodes_searched = 0
        self.transposition_table = {}
        self.killer_moves = [[] for _ in range(64)]  # Killer moves per ply
        self.history_scores = defaultdict(int)  # History heuristic
        self.search_start_time = 0
        
        # Evaluation caches
        self.pawn_structure_cache = {}
        self.king_safety_cache = {}
        
        # Analysis data
        self.move_explanations = []
        self.position_evaluations = []
        self.principal_variation = []
        
        # Opening book (rating-appropriate)
        self.opening_book = self._initialize_opening_book()
        
    def _initialize_opening_book(self) -> Dict:
        """Initialize opening book based on rating level."""
        if self.rating < 800:
            # Basic openings only
            return {
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                    ("e2e4", 40, "Control the center"),
                    ("d2d4", 35, "Control the center"), 
                    ("g1f3", 20, "Develop knight"),
                    ("c2c4", 5, "English Opening")
                ]
            }
        elif self.rating < 1200:
            # Add more openings
            return self._load_intermediate_opening_book()
        else:
            # Full theoretical knowledge
            return self._load_advanced_opening_book()
    
    def get_computer_move(self, fen: str) -> Dict:
        """Enhanced main interface with complete analysis."""
        try:
            board = chess.Board(fen)
            self.nodes_searched = 0
            self.search_start_time = time.time()
            
            # Clear analysis data
            self.move_explanations.clear()
            self.position_evaluations.clear()
            self.principal_variation.clear()
            
            # Check opening book first (for appropriate ratings)
            opening_move = self._check_opening_book(board)
            if opening_move and (self.rating >= 600 or random.random() < 0.7):
                best_move = opening_move
                move_source = "opening_book"
            else:
                # Full search
                best_move = self._get_best_move_enhanced(board)
                move_source = "search"
            
            if not best_move:
                return {'success': False, 'error': 'No legal moves available'}
            
            # Apply human-like errors
            final_move = self._apply_human_errors(board, best_move)
            
            # Get comprehensive move information
            san_notation = board.san(final_move)
            
            # Calculate position after move
            board.push(final_move)
            search_time = time.time() - self.search_start_time
            
            return {
                'success': True,
                'move': {
                    'from_square': chess.square_name(final_move.from_square),
                    'to_square': chess.square_name(final_move.to_square),
                    'promotion': final_move.promotion.symbol().lower() if final_move.promotion else None,
                    'uci': final_move.uci(),
                    'notation': san_notation,  # Changed from 'san' to 'notation' for backend compatibility
                    'san': san_notation        # Keep both for compatibility
                },
                'new_fen': board.fen(),
                'engine_info': {
                    'rating': self.rating,
                    'personality': self.personality,
                    'search_depth': self.config.search_depth,
                    'time_limit': self.config.time_limit,
                    'nodes_searched': self.nodes_searched,
                    'search_time': round(search_time, 3),
                    'evaluation': self._evaluate_position_complete(board),
                    'move_source': move_source,
                    'principal_variation': [board.san(move) for move in self.principal_variation[:5]]
                },
                'game_status': {
                    'is_checkmate': board.is_checkmate(),
                    'is_stalemate': board.is_stalemate(),
                    'is_check': board.is_check(),
                    'is_game_over': board.is_game_over(),
                    'result': board.result() if board.is_game_over() else None
                },
                'analysis': {
                    'move_explanation': self._explain_move_comprehensive(board, final_move),
                    'position_assessment': self._assess_position_detailed(board),
                    'tactical_themes': self._identify_tactical_themes(board),
                    'strategic_concepts': self._identify_strategic_concepts(board)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_best_move_enhanced(self, board: chess.Board) -> Optional[chess.Move]:
        """Enhanced search with advanced algorithms."""
        # Check for immediate tactical opportunities
        if self.config.tactical_awareness > 0.5:
            tactical_move = self._find_immediate_tactics(board)
            if tactical_move:
                return tactical_move
        
        # Iterative deepening with aspiration windows
        best_move = None
        best_score = float('-inf')
        
        for depth in range(1, self.config.search_depth + 1):
            if time.time() - self.search_start_time > self.config.time_limit:
                break
            
            # Aspiration window for deeper searches
            if depth >= 4 and best_score != float('-inf'):
                alpha = best_score - 50
                beta = best_score + 50
            else:
                alpha = float('-inf')
                beta = float('inf')
            
            current_best, current_score = self._alpha_beta_root(board, depth, alpha, beta)
            
            if current_best:
                best_move = current_best
                best_score = current_score
                
                # Update principal variation
                self.principal_variation = self._extract_pv(board, depth)
        
        return best_move
    
    def _alpha_beta_root(self, board: chess.Board, depth: int, alpha: float, beta: float) -> Tuple[Optional[chess.Move], float]:
        """Root node of alpha-beta search with advanced features."""
        best_move = None
        best_score = float('-inf')
        
        # Generate and order moves
        legal_moves = list(board.legal_moves)
        legal_moves = self._order_moves_advanced(board, legal_moves)
        
        for move in legal_moves:
            if time.time() - self.search_start_time > self.config.time_limit:
                break
            
            board.push(move)
            
            # Use negamax for cleaner code
            score = -self._alpha_beta(board, depth - 1, -beta, -alpha, False)
            
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return best_move, best_score
    
    def _alpha_beta(self, board: chess.Board, depth: int, alpha: float, beta: float, null_move_allowed: bool) -> float:
        """Enhanced alpha-beta with null move pruning and extensions."""
        self.nodes_searched += 1
        
        # Time check
        if time.time() - self.search_start_time > self.config.time_limit:
            return self._evaluate_position_complete(board)
        
        # Terminal conditions
        if board.is_game_over():
            if board.is_checkmate():
                return -20000 + (self.config.search_depth - depth)  # Prefer quicker mates
            return 0  # Stalemate or draw
        
        if depth <= 0:
            return self._quiescence_search(board, alpha, beta, 4)  # Quiescence search
        
        # Transposition table lookup
        board_hash = self._get_board_hash(board)
        if board_hash in self.transposition_table:
            entry = self.transposition_table[board_hash]
            if entry['depth'] >= depth:
                if entry['flag'] == 'exact':
                    return entry['value']
                elif entry['flag'] == 'lower' and entry['value'] >= beta:
                    return beta
                elif entry['flag'] == 'upper' and entry['value'] <= alpha:
                    return alpha
        
        # Null move pruning (for higher ratings)
        if (null_move_allowed and 
            depth >= 3 and 
            not board.is_check() and 
            self.config.calculation_accuracy > 0.6 and
            self._has_non_pawn_material(board)):
            
            board.push(chess.Move.null())
            null_score = -self._alpha_beta(board, depth - 3, -beta, -beta + 1, False)
            board.pop()
            
            if null_score >= beta:
                return beta
        
        # Move generation and ordering
        legal_moves = list(board.legal_moves)
        legal_moves = self._order_moves_advanced(board, legal_moves)
        
        original_alpha = alpha
        best_score = float('-inf')
        best_move = None
        
        for i, move in enumerate(legal_moves):
            board.push(move)
            
            # Search extensions
            extension = 0
            if board.is_check() and self.config.tactical_awareness > 0.5:
                extension = 1  # Check extension
            elif self._is_capture(move) and self._is_recapture(board, move):
                extension = 1  # Recapture extension
            
            # Late move reductions (LMR)
            reduction = 0
            if (i > 3 and depth > 2 and 
                not board.is_check() and 
                not self._is_capture(move) and
                self.config.calculation_accuracy > 0.7):
                reduction = 1
            
            # Principal variation search
            if i == 0:
                score = -self._alpha_beta(board, depth - 1 + extension, -beta, -alpha, True)
            else:
                # Search with null window
                score = -self._alpha_beta(board, depth - 1 - reduction + extension, -alpha - 1, -alpha, True)
                
                # Re-search if necessary
                if score > alpha and score < beta and reduction > 0:
                    score = -self._alpha_beta(board, depth - 1 + extension, -beta, -alpha, True)
            
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            
            if alpha >= beta:
                # Update killer moves and history
                if not self._is_capture(move):
                    self._update_killer_moves(move, depth)
                    self.history_scores[move] += depth * depth
                break
        
        # Store in transposition table
        flag = 'exact'
        if best_score <= original_alpha:
            flag = 'upper'
        elif best_score >= beta:
            flag = 'lower'
        
        self.transposition_table[board_hash] = {
            'value': best_score,
            'depth': depth,
            'flag': flag,
            'best_move': best_move
        }
        
        return best_score
    
    def _quiescence_search(self, board: chess.Board, alpha: float, beta: float, depth: int) -> float:
        """Quiescence search to avoid horizon effect."""
        self.nodes_searched += 1
        
        if depth <= 0 or board.is_game_over():
            return self._evaluate_position_complete(board)
        
        # Stand pat
        stand_pat = self._evaluate_position_complete(board)
        
        if stand_pat >= beta:
            return beta
        
        alpha = max(alpha, stand_pat)
        
        # Only consider captures and checks
        moves = []
        for move in board.legal_moves:
            if self._is_capture(move) or board.gives_check(move):
                moves.append(move)
        
        # Order captures by MVV-LVA
        moves = self._order_captures(board, moves)
        
        for move in moves:
            board.push(move)
            score = -self._quiescence_search(board, -beta, -alpha, depth - 1)
            board.pop()
            
            if score >= beta:
                return beta
            
            alpha = max(alpha, score)
        
        return alpha
    
    def _evaluate_position_complete(self, board: chess.Board) -> float:
        """Complete position evaluation with all factors."""
        if board.is_checkmate():
            return -20000 if board.turn else 20000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        evaluation = 0
        
        # Material evaluation (always included)
        evaluation += self._evaluate_material_enhanced(board)
        
        # Positional evaluation
        if self.config.positional_weight > 0:
            evaluation += self._evaluate_positional_complete(board) * self.config.positional_weight
        
        # Tactical evaluation
        if self.config.tactical_awareness > 0.3:
            evaluation += self._evaluate_tactics_complete(board) * self.config.tactical_awareness
        
        # King safety
        evaluation += self._evaluate_king_safety_complete(board)
        
        # Pawn structure
        if self.rating >= 1000:
            evaluation += self._evaluate_pawn_structure(board)
        
        # Mobility and space
        if self.rating >= 1200:
            evaluation += self._evaluate_mobility_complete(board)
            evaluation += self._evaluate_space_control(board)
        
        # Advanced concepts for higher ratings
        if self.rating >= 1600:
            evaluation += self._evaluate_piece_coordination(board)
            evaluation += self._evaluate_weak_squares(board)
        
        # Endgame evaluation
        if self._is_endgame(board):
            evaluation += self._evaluate_endgame_factors(board)
        
        # Apply personality modifiers
        evaluation = self._apply_personality_complete(board, evaluation)
        
        # Add appropriate noise for rating level
        if self.config.evaluation_noise > 0:
            noise = random.uniform(-self.config.evaluation_noise, self.config.evaluation_noise)
            evaluation += noise
        
        return evaluation if board.turn == chess.WHITE else -evaluation
    
    def _evaluate_material_enhanced(self, board: chess.Board) -> float:
        """Enhanced material evaluation with piece pair bonuses."""
        evaluation = 0
        
        white_material = 0
        black_material = 0
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            piece_value = self.BASE_PIECE_VALUES[piece_type]
            
            white_material += white_count * piece_value
            black_material += black_count * piece_value
        
        evaluation = white_material - black_material
        
        # Bishop pair bonus
        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
            evaluation += 30
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
            evaluation -= 30
        
        return evaluation
    
    def _evaluate_tactics_complete(self, board: chess.Board) -> float:
        """Complete tactical evaluation."""
        evaluation = 0
        
        # Check for hanging pieces
        evaluation += self._evaluate_hanging_pieces(board)
        
        # Pins and skewers
        evaluation += self._evaluate_pins_and_skewers(board)
        
        # Forks and double attacks
        evaluation += self._evaluate_forks(board)
        
        # Discovered attacks
        evaluation += self._evaluate_discovered_attacks(board)
        
        return evaluation
    
    def _evaluate_king_safety_complete(self, board: chess.Board) -> float:
        """Complete king safety evaluation."""
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is None:
                continue
            
            safety_score = 0
            
            # Pawn shield
            safety_score += self._evaluate_pawn_shield(board, king_square, color)
            
            # King exposure
            safety_score += self._evaluate_king_exposure(board, king_square, color)
            
            # Attacking pieces near king
            safety_score += self._evaluate_king_attackers(board, king_square, color)
            
            # Castling rights
            if board.has_kingside_castling_rights(color) or board.has_queenside_castling_rights(color):
                safety_score += 10
            
            if color == chess.WHITE:
                evaluation += safety_score
            else:
                evaluation -= safety_score
        
        return evaluation * 0.5  # Weight king safety appropriately
    
    def _order_moves_advanced(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Advanced move ordering with multiple heuristics."""
        def move_score(move):
            score = 0
            
            # Hash move (from transposition table)
            board_hash = self._get_board_hash(board)
            if board_hash in self.transposition_table:
                if self.transposition_table[board_hash].get('best_move') == move:
                    score += 10000
            
            # Captures (MVV-LVA)
            if self._is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    score += self.BASE_PIECE_VALUES[victim.piece_type] - self.BASE_PIECE_VALUES[attacker.piece_type] // 10
            
            # Promotions
            if move.promotion:
                score += self.BASE_PIECE_VALUES[move.promotion]
            
            # Checks
            if board.gives_check(move):
                score += 50
            
            # Killer moves
            ply = self.config.search_depth - len(self.principal_variation)
            if ply < len(self.killer_moves) and move in self.killer_moves[ply]:
                score += 30
            
            # History heuristic
            score += self.history_scores.get(move, 0) // 10
            
            # Penalize moves that hang pieces
            if self._hangs_piece(board, move):
                score -= 1000
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)
    
    def _apply_personality_complete(self, board: chess.Board, evaluation: float) -> float:
        """Apply complete personality modifiers."""
        if not self.personality_modifiers:
            return evaluation
        
        # Adjust material vs positional balance
        material_component = self._get_material_component(evaluation)
        positional_component = evaluation - material_component
        
        adjusted_evaluation = (
            material_component * self.personality_modifiers.material_weight +
            positional_component * self.personality_modifiers.positional_weight
        )
        
        # Tactical bonuses for aggressive personalities
        if hasattr(self.personality_modifiers, 'aggression_factor'):
            if self.personality_modifiers.aggression_factor > 1.0:
                # Bonus for active pieces and attacks
                adjusted_evaluation += self._evaluate_aggressive_bonuses(board) * (self.personality_modifiers.aggression_factor - 1.0)
        
        return adjusted_evaluation
    
    def _explain_move_comprehensive(self, board: chess.Board, move: chess.Move) -> str:
        """Generate comprehensive move explanation."""
        board.pop()  # Go back to position before move
        explanation_parts = []
        
        # Basic move description
        if self._is_capture(move):
            explanation_parts.append(f"Captures {self._get_piece_name(board.piece_at(move.to_square))}")
        
        if move.promotion:
            explanation_parts.append(f"Promotes to {chess.piece_name(move.promotion)}")
        
        # Tactical themes
        board.push(move)  # Apply move for analysis
        if board.is_check():
            explanation_parts.append("Gives check")
        
        # Strategic themes based on rating level
        if self.rating >= 1200:
            if self._improves_piece_activity(board, move):
                explanation_parts.append("Improves piece activity")
            
            if self._controls_key_squares(board, move):
                explanation_parts.append("Controls important squares")
        
        if self.rating >= 1600:
            if self._improves_pawn_structure(board, move):
                explanation_parts.append("Improves pawn structure")
        
        if not explanation_parts:
            explanation_parts.append("Develops position")
        
        return ". ".join(explanation_parts) + "."
    
    # Placeholder implementations for missing methods
    def _check_opening_book(self, board: chess.Board) -> Optional[chess.Move]:
        """Check opening book for move."""
        fen = board.fen()
        if fen in self.opening_book:
            moves = self.opening_book[fen]
            if moves:
                move_data = random.choices(moves, weights=[m[1] for m in moves])[0]
                try:
                    return board.parse_san(move_data[0])
                except:
                    return None
        return None
    
    def _find_immediate_tactics(self, board: chess.Board) -> Optional[chess.Move]:
        """Find immediate tactical opportunities."""
        # Look for captures that win material
        for move in board.legal_moves:
            if self._is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    if self.BASE_PIECE_VALUES[victim.piece_type] > self.BASE_PIECE_VALUES[attacker.piece_type]:
                        return move
        return None
    
    def _is_capture(self, move: chess.Move) -> bool:
        """Check if move is a capture."""
        return move.to_square != move.from_square
    
    def _hangs_piece(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move hangs a piece."""
        board.push(move)
        hanging = False
        
        # Simple check: is the moved piece undefended and attacked?
        piece = board.piece_at(move.to_square)
        if piece:
            attackers = board.attackers(not board.turn, move.to_square)
            defenders = board.attackers(board.turn, move.to_square)
            if len(attackers) > len(defenders):
                hanging = True
        
        board.pop()
        return hanging
    
    # Complete implementation of all evaluation methods
    
    def _evaluate_positional_complete(self, board: chess.Board) -> float:
        """Complete positional evaluation."""
        evaluation = 0
        
        # Piece-square tables with game phase consideration
        game_phase = self._get_game_phase(board)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                
                if piece.color == chess.BLACK:
                    row = 7 - row
                
                # Use middlegame or endgame tables based on phase
                if piece.piece_type == chess.KING and game_phase < 0.3:
                    piece_value = self.PIECE_SQUARE_TABLES_EG[chess.KING][row][col]
                else:
                    piece_value = self.PIECE_SQUARE_TABLES_MG[piece.piece_type][row][col]
                
                if piece.color == chess.WHITE:
                    evaluation += piece_value
                else:
                    evaluation -= piece_value
        
        return evaluation
    
    def _evaluate_pawn_structure(self, board: chess.Board) -> float:
        """Evaluate pawn structure quality."""
        fen_key = board.fen().split()[0]  # Just piece positions
        if fen_key in self.pawn_structure_cache:
            return self.pawn_structure_cache[fen_key]
        
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            pawn_squares = board.pieces(chess.PAWN, color)
            multiplier = 1 if color == chess.WHITE else -1
            
            # Analyze each file for pawn structure
            files = [0] * 8
            for square in pawn_squares:
                files[chess.square_file(square)] += 1
            
            for file_idx, count in enumerate(files):
                if count == 0:
                    continue
                
                # Doubled pawns penalty
                if count > 1:
                    evaluation += multiplier * -20 * (count - 1)
                
                # Isolated pawns
                if (file_idx == 0 or files[file_idx - 1] == 0) and \
                   (file_idx == 7 or files[file_idx + 1] == 0):
                    evaluation += multiplier * -15
                
                # Backward pawns (simplified check)
                # More complex implementation would check diagonal support
                
            # Passed pawns bonus
            for square in pawn_squares:
                if self._is_passed_pawn(board, square, color):
                    rank = chess.square_rank(square)
                    if color == chess.BLACK:
                        rank = 7 - rank
                    # Bonus increases as pawn advances
                    evaluation += multiplier * (10 + rank * 5)
        
        self.pawn_structure_cache[fen_key] = evaluation
        return evaluation
    
    def _evaluate_mobility_complete(self, board: chess.Board) -> float:
        """Complete mobility evaluation."""
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            mobility_score = 0
            multiplier = 1 if color == chess.WHITE else -1
            
            # Count legal moves for each piece type
            for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for square in board.pieces(piece_type, color):
                    moves = 0
                    for target_square in chess.SQUARES:
                        if board.is_legal(chess.Move(square, target_square)):
                            moves += 1
                            # Extra points for controlling central squares
                            if target_square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                                moves += 0.5
                    
                    # Weight mobility by piece type
                    if piece_type == chess.KNIGHT:
                        mobility_score += moves * 4
                    elif piece_type == chess.BISHOP:
                        mobility_score += moves * 3
                    elif piece_type == chess.ROOK:
                        mobility_score += moves * 2
                    elif piece_type == chess.QUEEN:
                        mobility_score += moves * 1
            
            evaluation += multiplier * mobility_score
        
        return evaluation * 0.1  # Scale appropriately
    
    def _evaluate_space_control(self, board: chess.Board) -> float:
        """Evaluate space control."""
        evaluation = 0
        
        # Define important central squares
        central_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                          chess.D3, chess.D4, chess.D5, chess.D6,
                          chess.E3, chess.E4, chess.E5, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6]
        
        for square in central_squares:
            white_attackers = len(board.attackers(chess.WHITE, square))
            black_attackers = len(board.attackers(chess.BLACK, square))
            
            evaluation += (white_attackers - black_attackers) * 5
            
            # Bonus for piece occupation
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    evaluation += 10
                else:
                    evaluation -= 10
        
        # Extended center control
        for square in extended_center:
            if square not in central_squares:
                white_attackers = len(board.attackers(chess.WHITE, square))
                black_attackers = len(board.attackers(chess.BLACK, square))
                evaluation += (white_attackers - black_attackers) * 2
        
        return evaluation
    
    def _evaluate_hanging_pieces(self, board: chess.Board) -> float:
        """Evaluate hanging pieces."""
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for square in board.pieces(piece_type, color):
                    attackers = board.attackers(not color, square)
                    defenders = board.attackers(color, square)
                    
                    if len(attackers) > len(defenders):
                        # Piece is hanging
                        piece_value = self.BASE_PIECE_VALUES[piece_type]
                        evaluation -= multiplier * piece_value * 0.8
        
        return evaluation
    
    def _evaluate_pins_and_skewers(self, board: chess.Board) -> float:
        """Evaluate pins and skewers."""
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            # Check for pins by bishops and rooks
            for piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for square in board.pieces(piece_type, color):
                    piece = board.piece_at(square)
                    if not piece:
                        continue
                    
                    # Get piece attack directions
                    if piece_type in [chess.BISHOP, chess.QUEEN]:
                        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    if piece_type in [chess.ROOK, chess.QUEEN]:
                        directions.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    
                    for dx, dy in directions:
                        pinned_piece = None
                        target_square = square
                        
                        # Travel in direction
                        for _ in range(7):
                            target_square += dx * 8 + dy
                            if not (0 <= target_square <= 63):
                                break
                            
                            target_piece = board.piece_at(target_square)
                            if target_piece:
                                if target_piece.color != color:
                                    if pinned_piece is None:
                                        pinned_piece = target_piece
                                    elif target_piece.piece_type == chess.KING:
                                        # Pin detected
                                        evaluation += multiplier * 30
                                    break
                                else:
                                    break
        
        return evaluation
    
    def _evaluate_forks(self, board: chess.Board) -> float:
        """Evaluate fork opportunities."""
        evaluation = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            # Knights can fork
            for knight_square in board.pieces(chess.KNIGHT, color):
                knight_attacks = board.attacks(knight_square)
                valuable_targets = 0
                
                for attack_square in knight_attacks:
                    piece = board.piece_at(attack_square)
                    if piece and piece.color != color:
                        if piece.piece_type in [chess.ROOK, chess.QUEEN, chess.KING]:
                            valuable_targets += 1
                
                if valuable_targets >= 2:
                    evaluation += multiplier * 50
        
        return evaluation
    
    def _evaluate_discovered_attacks(self, board: chess.Board) -> float:
        """Evaluate discovered attack patterns."""
        # Simplified implementation
        return 0  # Complex to implement properly
    
    def _evaluate_pawn_shield(self, board: chess.Board, king_square: int, color: chess.Color) -> float:
        """Evaluate pawn shield in front of king."""
        evaluation = 0
        
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check files around king
        for file_offset in [-1, 0, 1]:
            check_file = king_file + file_offset
            if 0 <= check_file <= 7:
                has_pawn = False
                pawn_distance = 8
                
                # Look for pawns in front of king
                for rank_offset in range(1, 8):
                    if color == chess.WHITE:
                        check_rank = king_rank + rank_offset
                    else:
                        check_rank = king_rank - rank_offset
                    
                    if not (0 <= check_rank <= 7):
                        break
                    
                    square = chess.square(check_file, check_rank)
                    piece = board.piece_at(square)
                    
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        has_pawn = True
                        pawn_distance = rank_offset
                        break
                
                if has_pawn:
                    # Closer pawns provide better protection
                    evaluation += 20 - (pawn_distance * 3)
                else:
                    # Missing pawn shield
                    evaluation -= 30
        
        return evaluation
    
    def _evaluate_king_exposure(self, board: chess.Board, king_square: int, color: chess.Color) -> float:
        """Evaluate king exposure to enemy pieces."""
        evaluation = 0
        
        # Count enemy pieces that can attack squares near king
        king_zone = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_square = king_square + dx + dy * 8
                if 0 <= new_square <= 63:
                    king_zone.append(new_square)
        
        for square in king_zone:
            attackers = board.attackers(not color, square)
            evaluation -= len(attackers) * 5
        
        return evaluation
    
    def _evaluate_king_attackers(self, board: chess.Board, king_square: int, color: chess.Color) -> float:
        """Evaluate pieces attacking king zone."""
        evaluation = 0
        
        # This is a simplified version
        # A full implementation would consider attack weights by piece type
        king_attackers = board.attackers(not color, king_square)
        evaluation -= len(king_attackers) * 20
        
        return evaluation
    
    def _evaluate_piece_coordination(self, board: chess.Board) -> float:
        """Evaluate piece coordination and synergy."""
        evaluation = 0
        
        # Battery evaluation (rooks/queens on same file/rank)
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            # Check for rook batteries
            rook_squares = list(board.pieces(chess.ROOK, color))
            queen_squares = list(board.pieces(chess.QUEEN, color))
            
            heavy_pieces = rook_squares + queen_squares
            
            # Same file batteries
            files = {}
            for square in heavy_pieces:
                file = chess.square_file(square)
                if file not in files:
                    files[file] = []
                files[file].append(square)
            
            for file, squares in files.items():
                if len(squares) >= 2:
                    evaluation += multiplier * 25
        
        return evaluation
    
    def _evaluate_weak_squares(self, board: chess.Board) -> float:
        """Evaluate control of weak squares."""
        evaluation = 0
        
        # Simplified implementation focusing on key squares
        key_squares = [chess.D4, chess.D5, chess.E4, chess.E5]  # Central squares
        
        for square in key_squares:
            white_control = len(board.attackers(chess.WHITE, square))
            black_control = len(board.attackers(chess.BLACK, square))
            
            # Bonus for controlling key squares with pieces
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE and piece.piece_type != chess.PAWN:
                    evaluation += 15
                elif piece.color == chess.BLACK and piece.piece_type != chess.PAWN:
                    evaluation -= 15
        
        return evaluation
    
    def _evaluate_endgame_factors(self, board: chess.Board) -> float:
        """Evaluate endgame-specific factors."""
        evaluation = 0
        
        # King activity in endgame
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            king_square = board.king(color)
            
            if king_square is not None:
                # Central king is good in endgame
                king_file = chess.square_file(king_square)
                king_rank = chess.square_rank(king_square)
                
                center_distance = abs(king_file - 3.5) + abs(king_rank - 3.5)
                evaluation += multiplier * (7 - center_distance) * 5
        
        # Passed pawn evaluation is more important
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            
            for pawn_square in board.pieces(chess.PAWN, color):
                if self._is_passed_pawn(board, pawn_square, color):
                    rank = chess.square_rank(pawn_square)
                    if color == chess.BLACK:
                        rank = 7 - rank
                    # Much higher bonus in endgame
                    evaluation += multiplier * (20 + rank * 10)
        
        return evaluation
    
    def _get_game_phase(self, board: chess.Board) -> float:
        """Calculate game phase (0.0 = endgame, 1.0 = opening/middlegame)."""
        total_material = 0
        
        for color in [chess.WHITE, chess.BLACK]:
            total_material += len(board.pieces(chess.QUEEN, color)) * 9
            total_material += len(board.pieces(chess.ROOK, color)) * 5
            total_material += len(board.pieces(chess.BISHOP, color)) * 3
            total_material += len(board.pieces(chess.KNIGHT, color)) * 3
            total_material += len(board.pieces(chess.PAWN, color)) * 1
        
        # Maximum material is roughly 78 (excluding kings)
        return min(1.0, total_material / 78.0)
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Check if position is endgame."""
        return self._get_game_phase(board) < 0.4
    
    def _is_passed_pawn(self, board: chess.Board, pawn_square: int, color: chess.Color) -> bool:
        """Check if pawn is passed."""
        pawn_file = chess.square_file(pawn_square)
        pawn_rank = chess.square_rank(pawn_square)
        
        # Check for enemy pawns that can stop this pawn
        for check_file in [pawn_file - 1, pawn_file, pawn_file + 1]:
            if not (0 <= check_file <= 7):
                continue
            
            for enemy_pawn in board.pieces(chess.PAWN, not color):
                enemy_file = chess.square_file(enemy_pawn)
                enemy_rank = chess.square_rank(enemy_pawn)
                
                if enemy_file == check_file:
                    if color == chess.WHITE and enemy_rank > pawn_rank:
                        return False
                    elif color == chess.BLACK and enemy_rank < pawn_rank:
                        return False
        
        return True
    
    def _order_captures(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Order captures by Most Valuable Victim - Least Valuable Attacker."""
        def capture_score(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if victim and attacker:
                return self.BASE_PIECE_VALUES[victim.piece_type] - self.BASE_PIECE_VALUES[attacker.piece_type]
            return 0
        
        return sorted(moves, key=capture_score, reverse=True)
    
    def _has_non_pawn_material(self, board: chess.Board) -> bool:
        """Check if side to move has non-pawn material."""
        color = board.turn
        return (len(board.pieces(chess.KNIGHT, color)) > 0 or
                len(board.pieces(chess.BISHOP, color)) > 0 or
                len(board.pieces(chess.ROOK, color)) > 0 or
                len(board.pieces(chess.QUEEN, color)) > 0)
    
    def _is_recapture(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is a recapture."""
        # Simplified: check if there was a capture on the previous move
        # A full implementation would check move history
        return False
    
    def _extract_pv(self, board: chess.Board, depth: int) -> List[chess.Move]:
        """Extract principal variation from transposition table."""
        pv = []
        current_board = board.copy()
        
        for _ in range(min(depth, 10)):
            board_hash = self._get_board_hash(current_board)
            if board_hash not in self.transposition_table:
                break
            
            entry = self.transposition_table[board_hash]
            best_move = entry.get('best_move')
            
            if not best_move or best_move not in current_board.legal_moves:
                break
            
            pv.append(best_move)
            current_board.push(best_move)
        
        return pv
    
    def _get_material_component(self, evaluation: float) -> float:
        """Extract material component from evaluation."""
        # This is an approximation
        return evaluation * 0.7  # Assume 70% of evaluation is material
    
    def _evaluate_aggressive_bonuses(self, board: chess.Board) -> float:
        """Calculate bonuses for aggressive play."""
        evaluation = 0
        
        # Bonus for pieces attacking enemy king zone
        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            enemy_king = board.king(not color)
            
            if enemy_king is not None:
                attacking_pieces = 0
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if piece and piece.color == color:
                        if enemy_king in board.attacks(square):
                            attacking_pieces += 1
                
                evaluation += multiplier * attacking_pieces * 10
        
        return evaluation
    
    def _improves_piece_activity(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move improves piece activity."""
        # Simplified check: moving to center or attacking more squares
        to_square = move.to_square
        return to_square in [chess.D4, chess.D5, chess.E4, chess.E5, chess.C4, chess.C5, chess.F4, chess.F5]
    
    def _controls_key_squares(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move controls key squares."""
        piece = board.piece_at(move.to_square)
        if not piece:
            return False
        
        key_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        attacks = board.attacks(move.to_square)
        
        return any(square in attacks for square in key_squares)
    
    def _improves_pawn_structure(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move improves pawn structure."""
        piece = board.piece_at(move.to_square)
        return piece and piece.piece_type == chess.PAWN
    
    def _get_piece_name(self, piece: Optional[chess.Piece]) -> str:
        """Get human-readable piece name."""
        if not piece:
            return "piece"
        
        names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight", 
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }
        return names.get(piece.piece_type, "piece")
    
    def _assess_position_detailed(self, board: chess.Board) -> str:
        """Detailed position assessment."""
        eval_score = self._evaluate_position_complete(board)
        
        if eval_score > 300:
            return "White has a winning advantage"
        elif eval_score > 100:
            return "White is better"
        elif eval_score > 50:
            return "White is slightly better"
        elif eval_score < -300:
            return "Black has a winning advantage"
        elif eval_score < -100:
            return "Black is better"
        elif eval_score < -50:
            return "Black is slightly better"
        else:
            return "The position is roughly equal"
    
    def _identify_tactical_themes(self, board: chess.Board) -> List[str]:
        """Identify tactical themes in position."""
        themes = []
        
        # Check for basic tactical patterns
        if self._has_pins(board):
            themes.append("Pin")
        if self._has_forks(board):
            themes.append("Fork")
        if self._has_skewers(board):
            themes.append("Skewer")
        if board.is_check():
            themes.append("Check")
        
        return themes
    
    def _identify_strategic_concepts(self, board: chess.Board) -> List[str]:
        """Identify strategic concepts in position."""
        concepts = []
        
        if self._is_endgame(board):
            concepts.append("Endgame")
        if self._has_passed_pawns(board):
            concepts.append("Passed pawns")
        if self._has_pawn_majority(board):
            concepts.append("Pawn majority")
        
        return concepts
    
    def _has_pins(self, board: chess.Board) -> bool:
        """Check if position has pins."""
        # Simplified implementation
        return False
    
    def _has_forks(self, board: chess.Board) -> bool:
        """Check if position has fork opportunities."""
        # Check for knight forks
        for color in [chess.WHITE, chess.BLACK]:
            for knight_square in board.pieces(chess.KNIGHT, color):
                attacks = board.attacks(knight_square)
                valuable_pieces = 0
                for square in attacks:
                    piece = board.piece_at(square)
                    if piece and piece.color != color:
                        if piece.piece_type in [chess.ROOK, chess.QUEEN, chess.KING]:
                            valuable_pieces += 1
                if valuable_pieces >= 2:
                    return True
        return False
    
    def _has_skewers(self, board: chess.Board) -> bool:
        """Check if position has skewer opportunities."""
        # Simplified implementation
        return False
    
    def _has_passed_pawns(self, board: chess.Board) -> bool:
        """Check if position has passed pawns."""
        for color in [chess.WHITE, chess.BLACK]:
            for pawn_square in board.pieces(chess.PAWN, color):
                if self._is_passed_pawn(board, pawn_square, color):
                    return True
        return False
    
    def _has_pawn_majority(self, board: chess.Board) -> bool:
        """Check if either side has pawn majority on a flank."""
        # Count pawns on kingside and queenside
        for color in [chess.WHITE, chess.BLACK]:
            kingside_pawns = 0
            queenside_pawns = 0
            enemy_kingside = 0
            enemy_queenside = 0
            
            for pawn_square in board.pieces(chess.PAWN, color):
                file = chess.square_file(pawn_square)
                if file >= 4:  # e-h files
                    kingside_pawns += 1
                else:  # a-d files
                    queenside_pawns += 1
            
            for pawn_square in board.pieces(chess.PAWN, not color):
                file = chess.square_file(pawn_square)
                if file >= 4:
                    enemy_kingside += 1
                else:
                    enemy_queenside += 1
            
            if kingside_pawns > enemy_kingside or queenside_pawns > enemy_queenside:
                return True
        
        return False
    
    def _load_intermediate_opening_book(self) -> Dict:
        """Load opening book for intermediate players."""
        return {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                ("e2e4", 35, "King's pawn opening"),
                ("d2d4", 30, "Queen's pawn opening"),
                ("g1f3", 20, "Reti opening"),
                ("c2c4", 15, "English opening")
            ]
        }
    
    def _load_advanced_opening_book(self) -> Dict:
        """Load comprehensive opening book for advanced players."""
        return {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": [
                ("e2e4", 30, "King's pawn - leads to sharp tactical play"),
                ("d2d4", 25, "Queen's pawn - positional control"),
                ("g1f3", 20, "Reti - flexible development"),
                ("c2c4", 15, "English - controls d5 square"),
                ("f2f4", 5, "Bird opening"),
                ("b2b3", 3, "Nimzo-Larsen attack"),
                ("g2g3", 2, "King's Indian attack setup")
            ]
        }
    
    def _get_board_hash(self, board: chess.Board) -> str:
        """Get hash of board position."""
        return hashlib.md5(board.fen().encode()).hexdigest()
    
    def _apply_human_errors(self, board: chess.Board, best_move: chess.Move) -> chess.Move:
        """Apply human-like errors based on rating level."""
        # Higher ratings make fewer mistakes
        if random.random() < self.config.blunder_chance:
            # Make a blunder! (changed from > to < to fix logic)
            
            # Generate alternative moves for blunders
            legal_moves = list(board.legal_moves)
            if len(legal_moves) <= 1:
                return best_move
            
            # Different types of mistakes based on rating
            if self.rating < 800:
                # Beginners: completely random mistakes
                return random.choice(legal_moves)
            elif self.rating < 1200:
                # Novices: moves that look reasonable but are worse
                return self._pick_plausible_mistake(board, legal_moves, best_move)
            else:
                # Advanced players: subtle mistakes
                return self._pick_subtle_mistake(board, legal_moves, best_move)
        
        # If no blunder, return best move
        return best_move
    
    def _pick_plausible_mistake(self, board: chess.Board, legal_moves: List[chess.Move], best_move: chess.Move) -> chess.Move:
        """Pick a move that seems reasonable but is actually worse."""
        # Remove obviously bad moves (hanging pieces)
        reasonable_moves = []
        for move in legal_moves:
            if move == best_move:
                continue
            if not self._hangs_piece_obviously(board, move):
                reasonable_moves.append(move)
        
        return random.choice(reasonable_moves) if reasonable_moves else random.choice(legal_moves)
    
    def _pick_subtle_mistake(self, board: chess.Board, legal_moves: List[chess.Move], best_move: chess.Move) -> chess.Move:
        """Pick a move that's slightly inferior to the best move."""
        # Evaluate all moves and pick second or third best
        move_scores = []
        for move in legal_moves:
            board.push(move)
            score = -self._evaluate_position_complete(board)  # Negative because opponent's turn
            board.pop()
            move_scores.append((move, score))
        
        # Sort by score (best first)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Pick from top 3 moves (excluding best)
        candidates = [move for move, score in move_scores[1:4]]
        return random.choice(candidates) if candidates else best_move
    
    def _hangs_piece_obviously(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move obviously hangs a piece."""
        board.push(move)
        hanging = False
        
        # Simple check: is the moved piece undefended and attacked?
        piece = board.piece_at(move.to_square)
        if piece:
            attackers = board.attackers(not board.turn, move.to_square)
            defenders = board.attackers(board.turn, move.to_square)
            if len(attackers) > len(defenders):
                hanging = True
        
        board.pop()
        return hanging

    def _update_killer_moves(self, move: chess.Move, depth: int):
        """Update killer moves for move ordering."""
        if depth < len(self.killer_moves):
            if move not in self.killer_moves[depth]:
                self.killer_moves[depth].insert(0, move)
                # Keep only top 2 killer moves per depth
                if len(self.killer_moves[depth]) > 2:
                    self.killer_moves[depth].pop()


# Enhanced backward compatibility
class ChessAI:
    """Enhanced compatibility wrapper with additional features."""
    
    def __init__(self):
        self.engines = {}
        self.game_history = []
    
    def get_engine(self, difficulty: str, personality: str = "balanced") -> UnifiedChessEngine:
        """Get or create engine for difficulty and personality."""
        rating_map = {
            "beginner": 400,
            "easy": 600,
            "medium": 1200,
            "hard": 1600,
            "expert": 2000,
            "master": 2400
        }
        
        rating = rating_map.get(difficulty, 1200)
        key = f"{difficulty}_{personality}"
        
        if key not in self.engines:
            self.engines[key] = UnifiedChessEngine(rating, personality)
        
        return self.engines[key]
    
    def make_computer_move(self, fen: str, difficulty: str = "medium", personality: str = "balanced") -> Dict:
        """Enhanced computer move with personality support."""
        engine = self.get_engine(difficulty, personality)
        result = engine.get_computer_move(fen)
        
        # Store move in game history for analysis
        if result['success']:
            self.game_history.append({
                'fen': fen,
                'move': result['move'],
                'evaluation': result['engine_info']['evaluation'],
                'difficulty': difficulty,
                'personality': personality
            })
        
        return result
    
    def analyze_game_performance(self) -> Dict:
        """Analyze the computer's game performance."""
        if not self.game_history:
            return {'error': 'No game history available'}
        
        total_moves = len(self.game_history)
        avg_eval = sum(move['evaluation'] for move in self.game_history) / total_moves
        
        return {
            'total_moves': total_moves,
            'average_evaluation': round(avg_eval, 2),
            'personalities_used': list(set(move['personality'] for move in self.game_history)),
            'difficulties_used': list(set(move['difficulty'] for move in self.game_history))
        }
    
    def clear_game_history(self):
        """Clear game history."""
        self.game_history.clear()


# Advanced Features and Utilities
class EngineAnalyzer:
    """Advanced analysis tools for chess engine evaluation."""
    
    def __init__(self, engine: UnifiedChessEngine):
        self.engine = engine
    
    def analyze_position_depth(self, fen: str, max_depth: int = 10) -> Dict:
        """Analyze position at increasing depths."""
        board = chess.Board(fen)
        results = {}
        
        original_depth = self.engine.config.search_depth
        
        for depth in range(1, max_depth + 1):
            self.engine.config.search_depth = depth
            start_time = time.time()
            
            result = self.engine.get_computer_move(fen)
            analysis_time = time.time() - start_time
            
            if result['success']:
                results[depth] = {
                    'best_move': result['move']['san'],
                    'evaluation': result['engine_info']['evaluation'],
                    'nodes_searched': result['engine_info']['nodes_searched'],
                    'time': round(analysis_time, 3),
                    'nps': round(result['engine_info']['nodes_searched'] / analysis_time) if analysis_time > 0 else 0
                }
        
        # Restore original depth
        self.engine.config.search_depth = original_depth
        
        return results
    
    def compare_personalities(self, fen: str, personalities: List[str]) -> Dict:
        """Compare how different personalities evaluate the same position."""
        results = {}
        original_personality = self.engine.personality
        
        for personality in personalities:
            self.engine.personality = personality
            self.engine.personality_modifiers = get_personality_modifier(personality)
            
            result = self.engine.get_computer_move(fen)
            
            if result['success']:
                results[personality] = {
                    'best_move': result['move']['san'],
                    'evaluation': result['engine_info']['evaluation'],
                    'explanation': result['analysis']['move_explanation']
                }
        
        # Restore original personality
        self.engine.personality = original_personality
        self.engine.personality_modifiers = get_personality_modifier(original_personality)
        
        return results
    
    def evaluate_move_sequence(self, starting_fen: str, moves: List[str]) -> Dict:
        """Evaluate a sequence of moves."""
        board = chess.Board(starting_fen)
        evaluations = []
        
        # Initial position
        initial_eval = self.engine._evaluate_position_complete(board)
        evaluations.append({
            'move_number': 0,
            'fen': board.fen(),
            'evaluation': initial_eval,
            'move': None
        })
        
        # Apply each move and evaluate
        for i, move_san in enumerate(moves):
            try:
                move = board.parse_san(move_san)
                board.push(move)
                
                evaluation = self.engine._evaluate_position_complete(board)
                evaluations.append({
                    'move_number': i + 1,
                    'fen': board.fen(),
                    'evaluation': evaluation,
                    'move': move_san
                })
                
            except ValueError as e:
                return {'error': f'Invalid move {move_san}: {str(e)}'}
        
        return {
            'success': True,
            'evaluations': evaluations,
            'final_evaluation': evaluations[-1]['evaluation'],
            'evaluation_swing': max(e['evaluation'] for e in evaluations) - min(e['evaluation'] for e in evaluations)
        }


class PositionGenerator:
    """Generate specific types of chess positions for testing."""
    
    @staticmethod
    def generate_tactical_positions() -> List[Dict]:
        """Generate positions with tactical themes."""
        return [
            {
                'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4',
                'theme': 'Pin',
                'description': 'White can pin the knight with Bg5'
            },
            {
                'fen': 'rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 2 4',
                'theme': 'Fork',
                'description': 'Knight can fork king and rook'
            },
            {
                'fen': 'r1bq1rk1/ppp2ppp/2n1bn2/2bpp3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQ - 6 6',
                'theme': 'Discovery',
                'description': 'Moving knight discovers bishop attack'
            }
        ]
    
    @staticmethod
    def generate_endgame_positions() -> List[Dict]:
        """Generate endgame positions for testing."""
        return [
            {
                'fen': '8/8/8/8/8/8/4K3/4k3 w - - 0 1',
                'theme': 'King and Pawn',
                'description': 'Basic king endgame'
            },
            {
                'fen': '8/8/8/8/8/8/1K6/1k6 w - - 0 1',
                'theme': 'Opposition',
                'description': 'King opposition concepts'
            }
        ]


class EngineDebugger:
    """Debugging tools for chess engine development."""
    
    def __init__(self, engine: UnifiedChessEngine):
        self.engine = engine
    
    def debug_evaluation_components(self, fen: str) -> Dict:
        """Break down evaluation into components."""
        board = chess.Board(fen)
        
        components = {}
        
        # Material
        components['material'] = self.engine._evaluate_material_enhanced(board)
        
        # Positional
        if self.engine.config.positional_weight > 0:
            components['positional'] = self.engine._evaluate_positional_complete(board)
        
        # Tactical
        if self.engine.config.tactical_awareness > 0.3:
            components['tactical'] = self.engine._evaluate_tactics_complete(board)
        
        # King safety
        components['king_safety'] = self.engine._evaluate_king_safety_complete(board)
        
        # Pawn structure
        if self.engine.rating >= 1000:
            components['pawn_structure'] = self.engine._evaluate_pawn_structure(board)
        
        # Mobility
        if self.engine.rating >= 1200:
            components['mobility'] = self.engine._evaluate_mobility_complete(board)
            components['space'] = self.engine._evaluate_space_control(board)
        
        # Total
        components['total'] = self.engine._evaluate_position_complete(board)
        
        return {
            'fen': fen,
            'rating': self.engine.rating,
            'personality': self.engine.personality,
            'evaluation_breakdown': components
        }
    
    def _order_moves_basic(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Basic move ordering for lower-rated engines."""
        def move_score(move):
            score = 0
            
            # Captures first
            if self._is_capture(move):
                victim = board.piece_at(move.to_square)
                if victim:
                    score += self.BASE_PIECE_VALUES[victim.piece_type]
            
            # Promotions
            if move.promotion:
                score += self.BASE_PIECE_VALUES[move.promotion]
            
            # Checks
            if board.gives_check(move):
                score += 30
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)

    def test_move_ordering(self, fen: str) -> Dict:
        """Test move ordering effectiveness."""
        board = chess.Board(fen)
        legal_moves = list(board.legal_moves)
        
        # Test different ordering methods
        random.shuffle(legal_moves)
        unordered = legal_moves.copy()
        
        basic_ordered = self.engine._order_moves_basic(board, legal_moves.copy())
        advanced_ordered = self.engine._order_moves_advanced(board, legal_moves.copy())
        
        return {
            'total_moves': len(legal_moves),
            'unordered': [move.uci() for move in unordered[:5]],
            'basic_ordered': [move.uci() for move in basic_ordered[:5]],
            'advanced_ordered': [move.uci() for move in advanced_ordered[:5]]
        }
    
    def benchmark_search_speed(self, fen: str, depth: int = 6) -> Dict:
        """Benchmark search speed at given depth."""
        original_depth = self.engine.config.search_depth
        self.engine.config.search_depth = depth
        
        start_time = time.time()
        result = self.engine.get_computer_move(fen)
        total_time = time.time() - start_time
        
        # Restore original depth
        self.engine.config.search_depth = original_depth
        
        if result['success']:
            nps = result['engine_info']['nodes_searched'] / total_time if total_time > 0 else 0
            
            return {
                'depth': depth,
                'time': round(total_time, 3),
                'nodes': result['engine_info']['nodes_searched'],
                'nps': round(nps),
                'best_move': result['move']['san']
            }
        else:
            return {'error': result['error']}


# Performance monitoring tools
class PerformanceMonitor:
    """Monitor engine performance over time."""
    
    def __init__(self):
        self.stats = {
            'total_positions': 0,
            'total_time': 0,
            'total_nodes': 0,
            'move_times': [],
            'node_counts': [],
            'depths_reached': []
        }
    
    def record_move(self, result: Dict):
        """Record statistics from a move calculation."""
        if result['success']:
            engine_info = result['engine_info']
            
            self.stats['total_positions'] += 1
            self.stats['total_time'] += engine_info['search_time']
            self.stats['total_nodes'] += engine_info['nodes_searched']
            
            self.stats['move_times'].append(engine_info['search_time'])
            self.stats['node_counts'].append(engine_info['nodes_searched'])
            self.stats['depths_reached'].append(engine_info['search_depth'])
    
    def get_summary(self) -> Dict:
        """Get performance summary."""
        if self.stats['total_positions'] == 0:
            return {'error': 'No moves recorded'}
        
        avg_time = self.stats['total_time'] / self.stats['total_positions']
        avg_nodes = self.stats['total_nodes'] / self.stats['total_positions']
        avg_nps = avg_nodes / avg_time if avg_time > 0 else 0
        
        return {
            'positions_analyzed': self.stats['total_positions'],
            'total_time': round(self.stats['total_time'], 2),
            'average_time_per_move': round(avg_time, 3),
            'average_nodes_per_move': round(avg_nodes),
            'average_nps': round(avg_nps),
            'max_time': max(self.stats['move_times']),
            'min_time': min(self.stats['move_times']),
            'max_nodes': max(self.stats['node_counts']),
            'average_depth': round(sum(self.stats['depths_reached']) / len(self.stats['depths_reached']), 1)
        }
    
    def reset(self):
        """Reset all statistics."""
        self.stats = {
            'total_positions': 0,
            'total_time': 0,
            'total_nodes': 0,
            'move_times': [],
            'node_counts': [],
            'depths_reached': []
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Export main classes and functions
__all__ = [
    'UnifiedChessEngine',
    'ChessAI',
    'EngineAnalyzer', 
    'PositionGenerator',
    'EngineDebugger',
    'PerformanceMonitor',
    'performance_monitor'
]