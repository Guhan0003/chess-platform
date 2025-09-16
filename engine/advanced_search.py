"""
Advanced Search Algorithms for Professional Chess Engine
========================================================

Implements cutting-edge search techniques used in top-level chess engines:
- Iterative Deepening with Aspiration Windows
- Principal Variation Search (PVS)
- Killer Move Heuristic
- History Heuristic
- Late Move Reduction (LMR)
- Null Move Pruning
- Quiescence Search
"""

import chess
import chess.engine
import time
import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Search node types for different pruning strategies."""
    PV = "pv"          # Principal Variation node
    CUT = "cut"        # Cut node (beta cutoff expected)
    ALL = "all"        # All node (no cutoff expected)


@dataclass
class SearchResult:
    """Result of a search operation."""
    best_move: Optional[chess.Move]
    evaluation: float
    depth: int
    nodes_searched: int
    time_elapsed: float
    principal_variation: List[chess.Move]
    search_stats: Dict


@dataclass
class KillerMoves:
    """Killer move storage for move ordering."""
    primary: Optional[chess.Move] = None
    secondary: Optional[chess.Move] = None
    
    def add_killer(self, move: chess.Move):
        """Add a killer move, shifting existing ones."""
        if move != self.primary:
            self.secondary = self.primary
            self.primary = move
    
    def is_killer(self, move: chess.Move) -> bool:
        """Check if move is a killer move."""
        return move == self.primary or move == self.secondary


class TranspositionTable:
    """Transposition table for position caching."""
    
    def __init__(self, size_mb: int = 64):
        """Initialize transposition table with given size."""
        self.max_entries = (size_mb * 1024 * 1024) // 32  # Rough estimate
        self.table = {}
        self.hits = 0
        self.misses = 0
    
    def store(self, position_hash: int, depth: int, evaluation: float,
              node_type: NodeType, best_move: Optional[chess.Move] = None):
        """Store position evaluation in transposition table."""
        if len(self.table) >= self.max_entries:
            # Simple replacement: remove random entry
            self.table.pop(next(iter(self.table)))
        
        self.table[position_hash] = {
            'depth': depth,
            'evaluation': evaluation,
            'node_type': node_type,
            'best_move': best_move
        }
    
    def lookup(self, position_hash: int) -> Optional[Dict]:
        """Lookup position in transposition table."""
        if position_hash in self.table:
            self.hits += 1
            return self.table[position_hash]
        else:
            self.misses += 1
            return None
    
    def get_hit_rate(self) -> float:
        """Get transposition table hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class AdvancedSearchEngine:
    """
    Advanced chess search engine with professional algorithms.
    
    Implements state-of-the-art search techniques for master-level play.
    """
    
    def __init__(self, rating: int = 2000):
        """
        Initialize advanced search engine.
        
        Args:
            rating: Engine rating for search parameter tuning
        """
        self.rating = rating
        self.transposition_table = TranspositionTable(64)  # 64MB TT
        self.killer_moves = {}  # ply -> KillerMoves
        self.history_table = {}  # (from_square, to_square) -> score
        
        # Search parameters
        self.max_depth = self._get_max_depth_for_rating(rating)
        self.max_quiescence_depth = 8
        self.null_move_reduction = 3
        self.late_move_reduction_threshold = 3
        
        # Search statistics
        self.nodes_searched = 0
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0
        self.transposition_hits = 0
        
        # Time management
        self.start_time = 0.0
        self.max_time = 10.0
        self.stop_search = False
        
        logger.info(f"Advanced search engine initialized for rating {rating}")
    
    def _get_max_depth_for_rating(self, rating: int) -> int:
        """Get maximum search depth based on rating."""
        if rating < 1000:
            return 4
        elif rating < 1400:
            return 5
        elif rating < 1800:
            return 6
        elif rating < 2000:
            return 7
        elif rating < 2200:
            return 8
        elif rating < 2400:
            return 9
        else:
            return 10
    
    def search_best_move(self, board: chess.Board, max_time: float = 10.0,
                        max_depth: Optional[int] = None) -> SearchResult:
        """
        Search for the best move using advanced algorithms.
        
        Args:
            board: Current chess position
            max_time: Maximum search time in seconds
            max_depth: Maximum search depth (None for default)
            
        Returns:
            SearchResult with best move and analysis
        """
        self.start_time = time.time()
        self.max_time = max_time
        self.stop_search = False
        self.nodes_searched = 0
        self.beta_cutoffs = 0
        self.first_move_cutoffs = 0
        
        # Initialize search data structures
        self.killer_moves.clear()
        self.history_table.clear()
        
        target_depth = max_depth or self.max_depth
        best_move = None
        best_evaluation = -math.inf
        principal_variation = []
        
        # Iterative deepening with aspiration windows
        alpha = -math.inf
        beta = math.inf
        
        for depth in range(1, target_depth + 1):
            if self._should_stop_search():
                break
            
            # Use aspiration windows for depths > 2
            if depth > 2:
                window = 0.5  # Half-pawn window
                alpha = best_evaluation - window
                beta = best_evaluation + window
                
                # Search with aspiration window
                evaluation, move, pv = self._search_with_aspiration(
                    board, depth, alpha, beta
                )
                
                # If outside window, research with full window
                if evaluation <= alpha or evaluation >= beta:
                    alpha = -math.inf
                    beta = math.inf
                    evaluation, move, pv = self._principal_variation_search(
                        board, depth, alpha, beta, 0, NodeType.PV
                    )
            else:
                # Full window search for shallow depths
                evaluation, move, pv = self._principal_variation_search(
                    board, depth, alpha, beta, 0, NodeType.PV
                )
            
            if move is not None:
                best_move = move
                best_evaluation = evaluation
                principal_variation = pv
            
            # Log progress
            elapsed_time = time.time() - self.start_time
            logger.debug(f"Depth {depth}: {best_move} eval={best_evaluation:.2f} "
                        f"time={elapsed_time:.2f}s nodes={self.nodes_searched}")
        
        # Compile search statistics
        search_stats = {
            'final_depth': depth - 1 if self._should_stop_search() else depth,
            'nodes_searched': self.nodes_searched,
            'time_elapsed': time.time() - self.start_time,
            'nps': self.nodes_searched / max(0.001, time.time() - self.start_time),
            'beta_cutoffs': self.beta_cutoffs,
            'first_move_cutoffs': self.first_move_cutoffs,
            'cutoff_rate': self.first_move_cutoffs / max(1, self.beta_cutoffs),
            'tt_hit_rate': self.transposition_table.get_hit_rate()
        }
        
        return SearchResult(
            best_move=best_move,
            evaluation=best_evaluation,
            depth=search_stats['final_depth'],
            nodes_searched=self.nodes_searched,
            time_elapsed=search_stats['time_elapsed'],
            principal_variation=principal_variation,
            search_stats=search_stats
        )
    
    def _search_with_aspiration(self, board: chess.Board, depth: int,
                              alpha: float, beta: float) -> Tuple[float, Optional[chess.Move], List[chess.Move]]:
        """Search with aspiration windows."""
        try:
            return self._principal_variation_search(board, depth, alpha, beta, 0, NodeType.PV)
        except:
            # If aspiration search fails, fall back to full window
            return self._principal_variation_search(
                board, depth, -math.inf, math.inf, 0, NodeType.PV
            )
    
    def _principal_variation_search(self, board: chess.Board, depth: int,
                                  alpha: float, beta: float, ply: int,
                                  node_type: NodeType) -> Tuple[float, Optional[chess.Move], List[chess.Move]]:
        """
        Principal Variation Search (PVS) with alpha-beta pruning.
        
        Args:
            board: Current position
            depth: Remaining search depth
            alpha: Alpha bound
            beta: Beta bound
            ply: Current ply from root
            node_type: Type of search node
            
        Returns:
            Tuple of (evaluation, best_move, principal_variation)
        """
        self.nodes_searched += 1
        
        if self._should_stop_search():
            return 0.0, None, []
        
        # Check transposition table
        position_hash = hash(board.fen())  # Simple hash instead of polyglot
        tt_entry = self.transposition_table.lookup(position_hash)
        
        if tt_entry and tt_entry['depth'] >= depth:
            tt_eval = tt_entry['evaluation']
            if (tt_entry['node_type'] == NodeType.PV or
                (tt_entry['node_type'] == NodeType.CUT and tt_eval >= beta) or
                (tt_entry['node_type'] == NodeType.ALL and tt_eval <= alpha)):
                return tt_eval, tt_entry['best_move'], []
        
        # Terminal position checks
        if board.is_game_over():
            return self._evaluate_terminal_position(board), None, []
        
        # Quiescence search at leaf nodes
        if depth <= 0:
            return self._quiescence_search(board, alpha, beta, ply), None, []
        
        # Null move pruning
        if (depth >= 3 and not board.is_check() and 
            node_type != NodeType.PV and self._has_non_pawn_pieces(board)):
            
            board.push(chess.Move.null())
            null_score, _, _ = self._principal_variation_search(
                board, depth - 1 - self.null_move_reduction, 
                -beta, -beta + 1, ply + 1, NodeType.CUT
            )
            board.pop()
            
            if -null_score >= beta:
                return beta, None, []
        
        # Generate and order moves
        ordered_moves = self._order_moves(board, ply, tt_entry)
        
        best_move = None
        best_evaluation = -math.inf
        principal_variation = []
        moves_searched = 0
        
        for i, move in enumerate(ordered_moves):
            if not board.is_legal(move):
                continue
            
            board.push(move)
            
            # Determine search parameters
            gives_check = board.is_check()
            extension = 1 if gives_check else 0  # Check extension
            
            # Late Move Reduction (LMR)
            reduction = 0
            if (i >= self.late_move_reduction_threshold and depth > 2 and
                not gives_check and not board.is_capture(move)):
                reduction = 1
            
            # Principal Variation Search
            if i == 0:
                # Search first move with full window
                evaluation, _, pv = self._principal_variation_search(
                    board, depth - 1 + extension, -beta, -alpha, 
                    ply + 1, NodeType.PV
                )
                evaluation = -evaluation
            else:
                # Search other moves with null window first
                evaluation, _, _ = self._principal_variation_search(
                    board, depth - 1 - reduction + extension, 
                    -alpha - 1, -alpha, ply + 1, NodeType.CUT
                )
                evaluation = -evaluation
                
                # If it beats alpha, research with full window
                if evaluation > alpha and evaluation < beta:
                    evaluation, _, pv = self._principal_variation_search(
                        board, depth - 1 + extension, -beta, -alpha,
                        ply + 1, NodeType.PV
                    )
                    evaluation = -evaluation
            
            board.pop()
            moves_searched += 1
            
            # Update best move and alpha
            if evaluation > best_evaluation:
                best_evaluation = evaluation
                best_move = move
                
                if i == 0:  # Principal variation
                    principal_variation = [move] + pv
                
                if evaluation > alpha:
                    alpha = evaluation
                    
                    # Beta cutoff
                    if alpha >= beta:
                        self.beta_cutoffs += 1
                        if i == 0:
                            self.first_move_cutoffs += 1
                        
                        # Update killer moves and history
                        self._update_killer_moves(ply, move)
                        self._update_history_table(move, depth)
                        
                        # Store in transposition table
                        self.transposition_table.store(
                            position_hash, depth, beta, NodeType.CUT, best_move
                        )
                        
                        return beta, best_move, principal_variation
        
        # Store in transposition table
        node_type_result = NodeType.PV if best_evaluation > alpha else NodeType.ALL
        self.transposition_table.store(
            position_hash, depth, best_evaluation, node_type_result, best_move
        )
        
        return best_evaluation, best_move, principal_variation
    
    def _quiescence_search(self, board: chess.Board, alpha: float, beta: float,
                          ply: int, depth: int = 0) -> float:
        """
        Quiescence search to avoid horizon effect.
        
        Args:
            board: Current position
            alpha: Alpha bound
            beta: Beta bound
            ply: Current ply from root
            depth: Quiescence depth
            
        Returns:
            Position evaluation
        """
        self.nodes_searched += 1
        
        if depth > self.max_quiescence_depth or self._should_stop_search():
            return self._evaluate_position(board)
        
        # Stand-pat evaluation
        stand_pat = self._evaluate_position(board)
        
        if stand_pat >= beta:
            return beta
        
        if stand_pat > alpha:
            alpha = stand_pat
        
        # Generate and search captures
        for move in self._order_capture_moves(board):
            if not board.is_legal(move):
                continue
            
            # Delta pruning - skip hopeless captures
            if not self._is_promising_capture(board, move, alpha, stand_pat):
                continue
            
            board.push(move)
            evaluation = -self._quiescence_search(board, -beta, -alpha, ply + 1, depth + 1)
            board.pop()
            
            if evaluation >= beta:
                return beta
            
            if evaluation > alpha:
                alpha = evaluation
        
        return alpha
    
    def _order_moves(self, board: chess.Board, ply: int,
                    tt_entry: Optional[Dict] = None) -> List[chess.Move]:
        """
        Order moves for optimal alpha-beta pruning.
        
        Args:
            board: Current position
            ply: Current ply
            tt_entry: Transposition table entry
            
        Returns:
            List of ordered moves
        """
        moves = list(board.legal_moves)
        
        def move_priority(move: chess.Move) -> int:
            priority = 0
            
            # Transposition table move gets highest priority
            if tt_entry and tt_entry.get('best_move') == move:
                priority += 10000
            
            # Captures ordered by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if board.is_capture(move):
                victim_value = self._get_piece_value(board.piece_at(move.to_square))
                attacker_value = self._get_piece_value(board.piece_at(move.from_square))
                priority += 1000 + victim_value - attacker_value
            
            # Promotions
            if move.promotion:
                priority += 900
            
            # Killer moves
            if ply in self.killer_moves and self.killer_moves[ply].is_killer(move):
                priority += 800 if self.killer_moves[ply].primary == move else 700
            
            # History heuristic
            history_key = (move.from_square, move.to_square)
            if history_key in self.history_table:
                priority += min(600, self.history_table[history_key])
            
            # Checks
            board.push(move)
            if board.is_check():
                priority += 500
            board.pop()
            
            # Central moves
            if move.to_square in [chess.E4, chess.E5, chess.D4, chess.D5]:
                priority += 50
            
            return priority
        
        # Sort moves by priority (highest first)
        moves.sort(key=move_priority, reverse=True)
        return moves
    
    def _order_capture_moves(self, board: chess.Board) -> List[chess.Move]:
        """Order capture moves for quiescence search."""
        captures = [move for move in board.legal_moves if board.is_capture(move)]
        
        def capture_value(move: chess.Move) -> int:
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if victim is None:
                return 0
            
            # MVV-LVA ordering
            victim_value = self._get_piece_value(victim)
            attacker_value = self._get_piece_value(attacker)
            
            return victim_value * 10 - attacker_value
        
        captures.sort(key=capture_value, reverse=True)
        return captures
    
    def _get_piece_value(self, piece: Optional[chess.Piece]) -> int:
        """Get piece value for move ordering."""
        if piece is None:
            return 0
        
        values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        return values.get(piece.piece_type, 0)
    
    def _is_promising_capture(self, board: chess.Board, move: chess.Move,
                            alpha: float, stand_pat: float) -> bool:
        """Check if capture is worth searching in quiescence."""
        victim = board.piece_at(move.to_square)
        if victim is None:
            return False
        
        # Delta pruning - if capturing the piece can't improve alpha significantly
        victim_value = self._get_piece_value(victim)
        delta_margin = 200  # Safety margin
        
        return stand_pat + victim_value + delta_margin > alpha
    
    def _update_killer_moves(self, ply: int, move: chess.Move):
        """Update killer moves heuristic."""
        if ply not in self.killer_moves:
            self.killer_moves[ply] = KillerMoves()
        
        self.killer_moves[ply].add_killer(move)
    
    def _update_history_table(self, move: chess.Move, depth: int):
        """Update history heuristic table."""
        history_key = (move.from_square, move.to_square)
        
        if history_key not in self.history_table:
            self.history_table[history_key] = 0
        
        # Increase history score based on depth
        self.history_table[history_key] += depth * depth
        
        # Prevent overflow
        if self.history_table[history_key] > 10000:
            # Age all history entries
            for key in self.history_table:
                self.history_table[key] //= 2
    
    def _evaluate_terminal_position(self, board: chess.Board) -> float:
        """Evaluate terminal positions (checkmate, stalemate, etc.)."""
        if board.is_checkmate():
            # Return negative value for losing, adjusted by ply for faster mates
            return -29000 + len(board.move_stack)
        elif board.is_stalemate() or board.is_insufficient_material():
            return 0.0  # Draw
        elif board.can_claim_draw():
            return 0.0  # Draw by repetition or 50-move rule
        else:
            # Shouldn't reach here in normal game
            return self._evaluate_position(board)
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """
        Basic position evaluation function.
        Note: This would be replaced by the sophisticated evaluation from the main engine.
        """
        if board.is_checkmate():
            return -29000 + len(board.move_stack)
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0.0
        
        # Simple material evaluation
        material_balance = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self._get_piece_value(piece)
                if piece.color == board.turn:
                    material_balance += value
                else:
                    material_balance -= value
        
        return material_balance / 100.0  # Convert to pawn units
    
    def _has_non_pawn_pieces(self, board: chess.Board) -> bool:
        """Check if current side has non-pawn pieces."""
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if (piece and piece.color == board.turn and 
                piece.piece_type != chess.PAWN):
                return True
        return False
    
    def _should_stop_search(self) -> bool:
        """Check if search should be stopped due to time limit."""
        if self.stop_search:
            return True
        
        elapsed_time = time.time() - self.start_time
        return elapsed_time >= self.max_time
    
    def stop_search_immediately(self):
        """Stop the search immediately."""
        self.stop_search = True
    
    def get_search_statistics(self) -> Dict:
        """Get detailed search statistics."""
        elapsed_time = time.time() - self.start_time
        nps = self.nodes_searched / max(0.001, elapsed_time)
        
        return {
            'nodes_searched': self.nodes_searched,
            'time_elapsed': elapsed_time,
            'nodes_per_second': nps,
            'beta_cutoffs': self.beta_cutoffs,
            'first_move_cutoffs': self.first_move_cutoffs,
            'cutoff_rate': self.first_move_cutoffs / max(1, self.beta_cutoffs),
            'transposition_hits': self.transposition_table.hits,
            'transposition_misses': self.transposition_table.misses,
            'tt_hit_rate': self.transposition_table.get_hit_rate(),
            'max_depth': self.max_depth,
            'rating': self.rating
        }


# Export main classes
__all__ = [
    'AdvancedSearchEngine',
    'SearchResult',
    'NodeType',
    'TranspositionTable'
]