"""
Move Ordering and Search Optimization

Advanced move ordering techniques to improve search efficiency.
Better move ordering leads to more cutoffs in alpha-beta search,
significantly improving engine strength and speed.
"""

import chess
from typing import List, Tuple, Dict, Optional
from enum import Enum
import random


class MoveType(Enum):
    """Categories of moves for ordering."""
    HASH_MOVE = 0           # Move from transposition table
    WINNING_CAPTURE = 1     # Captures that win material
    PROMOTION = 2           # Pawn promotions
    KILLER_MOVE = 3         # Non-capture moves that caused cutoffs
    EVEN_CAPTURE = 4        # Captures that trade equally
    CASTLING = 5           # Castling moves
    CHECK = 6              # Moves that give check
    COUNTER_MOVE = 7       # Move that responds to opponent's last move
    QUIET_MOVE = 8         # Regular quiet moves
    LOSING_CAPTURE = 9     # Captures that lose material


class MoveOrderer:
    """
    Advanced move ordering system for chess search optimization.
    
    Implements multiple move ordering techniques:
    - MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
    - Killer moves
    - History heuristic
    - Counter moves
    - SEE (Static Exchange Evaluation)
    """
    
    # Piece values for MVV-LVA
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    def __init__(self, rating: int):
        """
        Initialize move orderer for specific rating level.
        
        Args:
            rating: Player rating (affects ordering sophistication)
        """
        self.rating = rating
        
        # Killer moves (non-captures that cause cutoffs)
        self.killer_moves = {}  # depth -> [move1, move2]
        
        # History heuristic (how often moves cause cutoffs)
        self.history_scores = {}  # (from_square, to_square) -> score
        
        # Counter moves (responses to opponent moves)
        self.counter_moves = {}  # last_move -> counter_move
        
        # Principal variation moves
        self.pv_moves = {}  # depth -> move
        
        # Maximum history score for normalization
        self.max_history_score = 1
    
    def order_moves(self, board: chess.Board, moves: List[chess.Move], 
                   depth: int = 0, hash_move: Optional[chess.Move] = None,
                   last_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        Order moves from most promising to least promising.
        
        Args:
            board: Current position
            moves: List of legal moves to order
            depth: Current search depth
            hash_move: Best move from transposition table
            last_move: Opponent's last move
            
        Returns:
            Moves ordered from best to worst
        """
        if not moves:
            return []
        
        # For very low ratings, use simple ordering
        if self.rating < 600:
            return self._order_moves_simple(board, moves)
        
        # For low ratings, use basic ordering
        if self.rating < 1000:
            return self._order_moves_basic(board, moves, hash_move)
        
        # For higher ratings, use advanced ordering
        return self._order_moves_advanced(board, moves, depth, hash_move, last_move)
    
    def _order_moves_simple(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Simple move ordering for very low ratings."""
        # Separate captures and non-captures
        captures = []
        non_captures = []
        
        for move in moves:
            if board.is_capture(move):
                captures.append(move)
            else:
                non_captures.append(move)
        
        # Shuffle to add some randomness
        random.shuffle(captures)
        random.shuffle(non_captures)
        
        return captures + non_captures
    
    def _order_moves_basic(self, board: chess.Board, moves: List[chess.Move], 
                          hash_move: Optional[chess.Move]) -> List[chess.Move]:
        """Basic move ordering for low-intermediate ratings."""
        scored_moves = []
        
        for move in moves:
            score = 0
            
            # Hash move gets highest priority
            if hash_move and move == hash_move:
                score = 10000
            
            # Captures ordered by MVV-LVA
            elif board.is_capture(move):
                score = self._mvv_lva_score(board, move)
            
            # Promotions
            elif move.promotion:
                promotion_value = self.PIECE_VALUES.get(move.promotion, 0)
                score = 8000 + promotion_value
            
            # Checks
            elif board.gives_check(move):
                score = 5000
            
            # Castling
            elif board.is_castling(move):
                score = 4000
            
            # Other moves get low score
            else:
                score = 1000
            
            scored_moves.append((score, move))
        
        # Sort by score (highest first)
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in scored_moves]
    
    def _order_moves_advanced(self, board: chess.Board, moves: List[chess.Move],
                             depth: int, hash_move: Optional[chess.Move], 
                             last_move: Optional[chess.Move]) -> List[chess.Move]:
        """Advanced move ordering for high ratings."""
        scored_moves = []
        
        for move in moves:
            score = self._calculate_move_score(board, move, depth, hash_move, last_move)
            scored_moves.append((score, move))
        
        # Sort by score (highest first)
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in scored_moves]
    
    def _calculate_move_score(self, board: chess.Board, move: chess.Move,
                             depth: int, hash_move: Optional[chess.Move], 
                             last_move: Optional[chess.Move]) -> int:
        """Calculate comprehensive score for move ordering."""
        score = 0
        
        # 1. Hash move (transposition table)
        if hash_move and move == hash_move:
            return 50000
        
        # 2. Principal variation move
        if depth in self.pv_moves and move == self.pv_moves[depth]:
            score += 45000
        
        # 3. Winning captures (positive SEE)
        if board.is_capture(move):
            see_score = self._static_exchange_evaluation(board, move)
            if see_score > 0:
                score += 40000 + see_score
            elif see_score == 0:
                score += 30000  # Even trades
            else:
                score += 10000 + see_score  # Losing captures (but still try them)
        
        # 4. Promotions
        elif move.promotion:
            promotion_value = self.PIECE_VALUES.get(move.promotion, 0)
            score += 35000 + promotion_value
        
        # 5. Killer moves (non-captures that caused cutoffs)
        elif self._is_killer_move(move, depth):
            score += 25000
        
        # 6. Counter moves (response to opponent's last move)
        elif last_move and self._is_counter_move(move, last_move):
            score += 20000
        
        # 7. Checks
        elif board.gives_check(move):
            score += 15000
        
        # 8. Castling
        elif board.is_castling(move):
            score += 12000
        
        # 9. History heuristic (how often this move type works)
        else:
            score += self._get_history_score(move)
        
        return score
    
    def _mvv_lva_score(self, board: chess.Board, move: chess.Move) -> int:
        """
        Most Valuable Victim - Least Valuable Attacker scoring.
        
        Prioritizes capturing valuable pieces with less valuable pieces.
        """
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        
        if not victim or not attacker:
            return 0
        
        victim_value = self.PIECE_VALUES.get(victim.piece_type, 0)
        attacker_value = self.PIECE_VALUES.get(attacker.piece_type, 0)
        
        # MVV-LVA: (victim_value * 10) - attacker_value
        return (victim_value * 10) - attacker_value
    
    def _static_exchange_evaluation(self, board: chess.Board, move: chess.Move) -> int:
        """
        Static Exchange Evaluation - determine if capture is profitable.
        
        Simulates the exchange sequence to see material balance.
        """
        # Simplified SEE implementation
        # Full implementation would simulate entire exchange sequence
        
        if not board.is_capture(move):
            return 0
        
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        
        if not victim or not attacker:
            return 0
        
        victim_value = self.PIECE_VALUES.get(victim.piece_type, 0)
        attacker_value = self.PIECE_VALUES.get(attacker.piece_type, 0)
        
        # Basic approximation: is piece defended?
        board.push(move)
        is_defended = board.is_attacked_by(not attacker.color, move.to_square)
        board.pop()
        
        if not is_defended:
            return victim_value
        else:
            return victim_value - attacker_value
    
    def _is_killer_move(self, move: chess.Move, depth: int) -> bool:
        """Check if move is a killer move at this depth."""
        if depth not in self.killer_moves:
            return False
        
        killers = self.killer_moves[depth]
        return move in killers
    
    def _is_counter_move(self, move: chess.Move, last_move: chess.Move) -> bool:
        """Check if move is a counter move to opponent's last move."""
        return last_move in self.counter_moves and self.counter_moves[last_move] == move
    
    def _get_history_score(self, move: chess.Move) -> int:
        """Get history heuristic score for move."""
        move_key = (move.from_square, move.to_square)
        raw_score = self.history_scores.get(move_key, 0)
        
        # Normalize to prevent scores from getting too large
        if self.max_history_score > 0:
            normalized = (raw_score * 1000) // self.max_history_score
            return min(normalized, 5000)
        
        return 0
    
    def update_killer_move(self, move: chess.Move, depth: int):
        """Update killer moves when a non-capture causes cutoff."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        killers = self.killer_moves[depth]
        
        # Remove if already in list
        if move in killers:
            killers.remove(move)
        
        # Add to front
        killers.insert(0, move)
        
        # Keep only top 2 killers per depth
        if len(killers) > 2:
            killers.pop()
    
    def update_history_score(self, move: chess.Move, depth: int):
        """Update history heuristic when move causes cutoff."""
        move_key = (move.from_square, move.to_square)
        
        # Increase score based on depth (deeper cutoffs are more valuable)
        bonus = depth * depth
        
        if move_key not in self.history_scores:
            self.history_scores[move_key] = 0
        
        self.history_scores[move_key] += bonus
        
        # Update maximum for normalization
        self.max_history_score = max(self.max_history_score, self.history_scores[move_key])
    
    def update_counter_move(self, last_move: chess.Move, counter_move: chess.Move):
        """Update counter move when it causes cutoff."""
        self.counter_moves[last_move] = counter_move
    
    def update_pv_move(self, move: chess.Move, depth: int):
        """Update principal variation move."""
        self.pv_moves[depth] = move
    
    def clear_history(self):
        """Clear all move ordering history (for new game)."""
        self.killer_moves.clear()
        self.history_scores.clear()
        self.counter_moves.clear()
        self.pv_moves.clear()
        self.max_history_score = 1
    
    def age_history(self):
        """Age the history scores to prevent them from becoming stale."""
        for move_key in self.history_scores:
            self.history_scores[move_key] = int(self.history_scores[move_key] * 0.9)
        
        # Recalculate max score
        if self.history_scores:
            self.max_history_score = max(self.history_scores.values())
        else:
            self.max_history_score = 1


class TranspositionTable:
    """
    Transposition table for storing previously evaluated positions.
    
    Stores position evaluations to avoid re-calculating the same positions.
    Critical for engine performance in middle and endgames.
    """
    
    def __init__(self, size_mb: int = 64):
        """
        Initialize transposition table.
        
        Args:
            size_mb: Size of table in megabytes
        """
        # Estimate entries (each entry ~32 bytes)
        self.max_entries = (size_mb * 1024 * 1024) // 32
        self.table = {}
        self.current_age = 0
    
    def store(self, board: chess.Board, depth: int, score: int, 
              move: Optional[chess.Move] = None, node_type: str = "exact"):
        """
        Store position evaluation in table.
        
        Args:
            board: Chess position
            depth: Search depth used
            score: Evaluation score
            move: Best move found
            node_type: Type of node ("exact", "lower", "upper")
        """
        if len(self.table) >= self.max_entries:
            self._cleanup_table()
        
        position_hash = self._hash_position(board)
        
        self.table[position_hash] = {
            'depth': depth,
            'score': score,
            'move': move,
            'type': node_type,
            'age': self.current_age
        }
    
    def probe(self, board: chess.Board, depth: int, alpha: int, beta: int) -> Tuple[Optional[int], Optional[chess.Move]]:
        """
        Probe table for stored evaluation.
        
        Args:
            board: Chess position
            depth: Required search depth
            alpha: Alpha bound
            beta: Beta bound
            
        Returns:
            Tuple of (score, best_move) or (None, move) if not usable
        """
        position_hash = self._hash_position(board)
        
        if position_hash not in self.table:
            return None, None
        
        entry = self.table[position_hash]
        
        # Return best move even if depth/bounds don't match
        best_move = entry['move']
        
        # Check if we can use the stored score
        if entry['depth'] >= depth:
            score = entry['score']
            node_type = entry['type']
            
            if node_type == "exact":
                return score, best_move
            elif node_type == "lower" and score >= beta:
                return score, best_move
            elif node_type == "upper" and score <= alpha:
                return score, best_move
        
        return None, best_move
    
    def _hash_position(self, board: chess.Board) -> int:
        """Generate hash for board position."""
        # Use board's FEN as hash (simplified)
        # Real implementation would use Zobrist hashing
        return hash(board.fen())
    
    def _cleanup_table(self):
        """Remove old entries when table is full."""
        # Remove entries from previous ages
        old_entries = [key for key, value in self.table.items() 
                      if value['age'] < self.current_age - 2]
        
        for key in old_entries[:len(old_entries)//2]:
            del self.table[key]
    
    def new_search(self):
        """Start new search (increment age)."""
        self.current_age += 1
    
    def clear(self):
        """Clear entire table."""
        self.table.clear()
        self.current_age = 0