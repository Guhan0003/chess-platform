"""
Advanced Chess Engine Implementation
===================================

Complete integration of all advanced components:
- Opening Database with 20+ variations
- Advanced Search Algorithms (PVS, Iterative Deepening, etc.)
- Time Management
- Sophisticated Evaluation
- Rating-based Play Strength
"""

import chess
import chess.engine
import time
import random
import math
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
import logging

# Import engine components
from .opening_database import create_opening_book, PlayingStyle
from .advanced_search import AdvancedSearchEngine, SearchResult, NodeType
from games.utils.time_control import create_time_manager, MoveType
from games.utils.timer_manager import TimerManager
from games.utils.rating_system import RatingIntegration
from .rating_configs import get_rating_config
from .evaluation import AdvancedEvaluator

logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """Chess game phases."""
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"


class ChessEngine:
    """
    Advanced chess engine with sophisticated capabilities.
    
    Integrates all advanced components for high-level chess play:
    - Opening database
    - Advanced search algorithms
    - Time management
    - Sophisticated evaluation
    - Human-like error modeling
    """
    
    def __init__(self, rating: int = 2000, personality: str = "balanced"):
        """
        Initialize chess engine.
        
        Args:
            rating: Engine rating (400-2400+)
            personality: Playing style ("aggressive", "positional", "balanced", etc.)
        """
        self.rating = rating
        self.personality = personality
        
        # Initialize all professional components
        self._initialize_components()
        
        # Game state tracking
        self.game_history = []
        self.position_count = {}
        self.fifty_move_counter = 0
        
        # Analysis data
        self.last_search_result = None
        self.opening_phase = True
        self.current_game_phase = GamePhase.OPENING
        
        logger.info(f"Chess engine initialized: Rating {rating}, Style {personality}")
    
    def _initialize_components(self):
        """Initialize all engine components."""
        # Convert personality to playing style
        style_mapping = {
            "aggressive": PlayingStyle.AGGRESSIVE,
            "tactical": PlayingStyle.TACTICAL,
            "positional": PlayingStyle.POSITIONAL,
            "balanced": PlayingStyle.BALANCED,
            "solid": PlayingStyle.SOLID,
            "creative": PlayingStyle.CREATIVE
        }
        
        playing_style = style_mapping.get(self.personality, PlayingStyle.BALANCED)
        
        # Initialize opening database
        self.opening_database = create_opening_book(self.rating, playing_style.value)
        
        # Initialize advanced search engine
        self.search_engine = AdvancedSearchEngine(self.rating)
        
        # Initialize time manager
        self.time_manager = create_time_manager(self.rating)
        
        # Initialize evaluator
        self.evaluator = AdvancedEvaluator(self.rating)
        
        # Initialize timer and rating integration
        self.game_timer = None  # Will be created when game starts
        self.rating_integration = RatingIntegration()
        
        # Get rating configuration
        self.rating_config = get_rating_config(self.rating)
        
        logger.info(f"All professional components initialized successfully")
    
    def get_computer_move(self, fen: str, max_time: Optional[float] = None) -> Dict:
        """
        Get computer move using professional analysis.
        
        Args:
            fen: Current position in FEN notation
            max_time: Maximum thinking time (None for auto)
            
        Returns:
            Dictionary with move and analysis information
        """
        try:
            board = chess.Board(fen)
            move_start_time = time.time()
            
            # Update game state
            self._update_game_state(board)
            
            # Determine move type and complexity
            move_type, complexity_score = self._analyze_position_complexity(board)
            
            # Calculate thinking time
            if max_time is None:
                thinking_time = self._calculate_thinking_time(board, move_type, complexity_score)
            else:
                thinking_time = max_time
            
            # Check for opening book move
            opening_move = self._get_opening_book_move(board)
            if opening_move:
                # Use quick opening book time
                book_time = self.time_manager.get_opening_book_time()
                self.time_manager.simulate_human_thinking_delay(book_time)
                
                return self._format_move_response(
                    board, opening_move, "opening_book", 
                    book_time, self.opening_database.get_opening_analysis(board)
                )
            
            # Check for obviously forced moves
            forced_move = self._check_forced_moves(board)
            if forced_move:
                forced_time = self.time_manager.get_forced_move_time()
                self.time_manager.simulate_human_thinking_delay(forced_time)
                
                return self._format_move_response(
                    board, forced_move, "forced", forced_time
                )
            
            # Perform full search
            best_move, search_result = self._search_best_move(board, thinking_time)
            
            # Apply human-like errors based on rating
            final_move = self._apply_human_errors(board, best_move, search_result)
            
            # Simulate thinking time
            actual_time = time.time() - move_start_time
            remaining_time = max(0, thinking_time - actual_time)
            self.time_manager.simulate_human_thinking_delay(remaining_time)
            
            return self._format_move_response(
                board, final_move, "search", thinking_time, search_result
            )
            
        except Exception as e:
            logger.error(f"Error in get_computer_move: {e}")
            return {
                'success': False,
                'error': str(e),
                'move': None
            }
    
    def _update_game_state(self, board: chess.Board):
        """Update internal game state tracking."""
        # Update game phase
        self.current_game_phase = self._determine_game_phase(board)
        
        # Update opening phase tracking
        move_count = len(board.move_stack)
        if move_count > 15 or not self.opening_database.is_in_opening_book(board):
            self.opening_phase = False
        
        # Update position count for repetition detection
        position_key = board.fen().split()[0]  # Position without move counts
        self.position_count[position_key] = self.position_count.get(position_key, 0) + 1
    
    def _determine_game_phase(self, board: chess.Board) -> GamePhase:
        """Determine current game phase."""
        piece_count = len(board.piece_map())
        move_count = len(board.move_stack)
        
        if move_count < 15 and piece_count > 20:
            return GamePhase.OPENING
        elif piece_count <= 12:
            return GamePhase.ENDGAME
        else:
            return GamePhase.MIDDLEGAME
    
    def _analyze_position_complexity(self, board: chess.Board) -> Tuple[MoveType, float]:
        """Analyze position to determine move type and complexity."""
        # Check for tactical motifs
        tactical_count = self._count_tactical_motifs(board)
        
        # Check for forced sequences
        legal_moves = list(board.legal_moves)
        if len(legal_moves) == 1:
            return MoveType.FORCED, 1.0
        
        # Analyze position characteristics
        if board.is_check():
            return MoveType.TACTICAL, 7.0 + tactical_count
        
        if tactical_count > 2:
            return MoveType.TACTICAL, 6.0 + tactical_count
        
        if self.current_game_phase == GamePhase.ENDGAME:
            return MoveType.ENDGAME, 5.0 + tactical_count
        
        if self.current_game_phase == GamePhase.OPENING:
            return MoveType.OPENING_BOOK, 3.0
        
        # Determine if position is complex
        complexity_factors = [
            len(legal_moves) > 30,  # Many options
            any(board.is_capture(move) for move in legal_moves),  # Captures available
            board.is_check(),  # In check
            tactical_count > 0  # Tactical elements
        ]
        
        complexity_score = 4.0 + sum(complexity_factors) + tactical_count
        
        if complexity_score > 7.0:
            return MoveType.COMPLEX, complexity_score
        else:
            return MoveType.POSITIONAL, complexity_score
    
    def _count_tactical_motifs(self, board: chess.Board) -> int:
        """Count tactical motifs in position."""
        tactical_count = 0
        
        for move in board.legal_moves:
            board.push(move)
            
            # Check for checks
            if board.is_check():
                tactical_count += 1
            
            # Check for captures
            if board.is_capture(move):
                tactical_count += 1
            
            # Check for promotions
            if move.promotion:
                tactical_count += 2
            
            board.pop()
            
            # Limit counting for performance
            if tactical_count > 10:
                break
        
        return min(tactical_count, 10)
    
    def _calculate_thinking_time(self, board: chess.Board, move_type: MoveType, 
                               complexity_score: float) -> float:
        """Calculate appropriate thinking time for position."""
        legal_moves = list(board.legal_moves)
        tactical_motifs = self._count_tactical_motifs(board)
        
        return self.time_manager.calculate_thinking_time(
            board, move_type, complexity_score, len(legal_moves), tactical_motifs
        )
    
    def _get_opening_book_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get move from opening book if available."""
        if not self.opening_phase:
            return None
        
        # Only use opening book for appropriate ratings
        if self.rating < 600:
            # Lower rated players don't always use book
            if random.random() > 0.6:
                return None
        
        return self.opening_database.get_opening_move(board)
    
    def _check_forced_moves(self, board: chess.Board) -> Optional[chess.Move]:
        """Check for obviously forced moves."""
        legal_moves = list(board.legal_moves)
        
        # Only one legal move
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Must escape check with only one reasonable option
        if board.is_check():
            reasonable_moves = []
            for move in legal_moves:
                board.push(move)
                if not board.is_check():  # Escapes check
                    reasonable_moves.append(move)
                board.pop()
            
            if len(reasonable_moves) == 1:
                return reasonable_moves[0]
        
        return None
    
    def _search_best_move(self, board: chess.Board, max_time: float) -> Tuple[chess.Move, SearchResult]:
        """Perform full search to find best move."""
        # Determine search depth based on rating and time
        max_depth = self._get_search_depth(max_time)
        
        # Perform search
        search_result = self.search_engine.search_best_move(
            board, max_time, max_depth
        )
        
        self.last_search_result = search_result
        
        if search_result.best_move is None:
            # Fallback to random legal move
            legal_moves = list(board.legal_moves)
            if legal_moves:
                return random.choice(legal_moves), search_result
            else:
                raise ValueError("No legal moves available")
        
        return search_result.best_move, search_result
    
    def _get_search_depth(self, max_time: float) -> int:
        """Determine search depth based on rating and time."""
        base_depth = {
            400: 3, 600: 4, 800: 4, 1000: 5, 1200: 5,
            1400: 6, 1600: 6, 1800: 7, 2000: 7, 2200: 8, 2400: 8
        }
        
        # Find closest rating
        closest_rating = min(base_depth.keys(), key=lambda x: abs(x - self.rating))
        depth = base_depth[closest_rating]
        
        # Adjust for time available
        if max_time > 15.0:
            depth += 1
        elif max_time < 3.0:
            depth = max(2, depth - 1)
        
        return depth
    
    def _apply_human_errors(self, board: chess.Board, best_move: chess.Move,
                          search_result: Optional[SearchResult] = None) -> chess.Move:
        """Apply human-like errors based on rating."""
        # High-rated players make fewer errors
        if self.rating >= 2200:
            error_probability = 0.02
        elif self.rating >= 2000:
            error_probability = 0.05
        elif self.rating >= 1800:
            error_probability = 0.08
        elif self.rating >= 1600:
            error_probability = 0.12
        elif self.rating >= 1400:
            error_probability = 0.15
        elif self.rating >= 1200:
            error_probability = 0.20
        elif self.rating >= 1000:
            error_probability = 0.25
        elif self.rating >= 800:
            error_probability = 0.30
        else:
            error_probability = 0.35
        
        # Check if error should occur
        if random.random() > error_probability:
            return best_move
        
        # Select alternative move
        legal_moves = list(board.legal_moves)
        if len(legal_moves) <= 1:
            return best_move
        
        # Remove best move from options
        alternative_moves = [move for move in legal_moves if move != best_move]
        
        # Weight alternative moves (avoid completely random blunders)
        if self.rating >= 1400:
            # Higher rated players make "reasonable" errors
            reasonable_moves = []
            for move in alternative_moves:
                board.push(move)
                # Avoid moves that immediately lose material
                if not self._is_obvious_blunder(board):
                    reasonable_moves.append(move)
                board.pop()
            
            if reasonable_moves:
                return random.choice(reasonable_moves)
        
        # Lower rated players can make more random errors
        return random.choice(alternative_moves)
    
    def _is_obvious_blunder(self, board: chess.Board) -> bool:
        """Check if the last move was an obvious blunder."""
        # Simple blunder detection - losing a piece for nothing
        if len(board.move_stack) == 0:
            return False
        
        last_move = board.peek()
        
        # Check if piece can be captured immediately
        for move in board.legal_moves:
            if move.to_square == last_move.to_square and board.is_capture(move):
                # Check if it's an undefended capture
                board.push(move)
                can_recapture = any(
                    m.to_square == move.to_square for m in board.legal_moves
                )
                board.pop()
                
                if not can_recapture:
                    return True
        
        return False
    
    def _format_move_response(self, board: chess.Board, move: chess.Move,
                            move_source: str, thinking_time: float,
                            additional_info: Optional[Dict] = None) -> Dict:
        """Format the move response with comprehensive information."""
        try:
            san_notation = board.san(move)
            
            # Calculate position after move
            board.push(move)
            position_eval = self.evaluator.evaluate(board) if hasattr(self, 'evaluator') else 0.0
            board.pop()
            
            response = {
                'success': True,
                'move': move.uci(),
                'san': san_notation,
                'move_source': move_source,
                'thinking_time': round(thinking_time, 2),
                'evaluation': round(position_eval, 2),
                'rating': self.rating,
                'personality': self.personality,
                'game_phase': self.current_game_phase.value
            }
            
            # Add search information if available
            if self.last_search_result:
                response.update({
                    'search_depth': self.last_search_result.depth,
                    'nodes_searched': self.last_search_result.nodes_searched,
                    'principal_variation': [
                        move.uci() for move in self.last_search_result.principal_variation[:5]
                    ]
                })
            
            # Add opening information if available
            if additional_info:
                response['opening_info'] = additional_info
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting move response: {e}")
            return {
                'success': True,
                'move': move.uci(),
                'san': board.san(move),
                'error': 'Partial response due to formatting error'
            }
    
    def get_position_analysis(self, fen: str) -> Dict:
        """Get detailed position analysis."""
        try:
            board = chess.Board(fen)
            
            # Basic position info
            analysis = {
                'position': fen,
                'game_phase': self._determine_game_phase(board).value,
                'legal_moves': len(list(board.legal_moves)),
                'in_check': board.is_check(),
                'rating': self.rating
            }
            
            # Opening book analysis
            if self.opening_database.is_in_opening_book(board):
                opening_analysis = self.opening_database.get_opening_analysis(board)
                if opening_analysis:
                    analysis['opening_analysis'] = opening_analysis
            
            # Position complexity
            move_type, complexity = self._analyze_position_complexity(board)
            analysis['complexity_score'] = complexity
            analysis['move_type'] = move_type.value
            
            # Time recommendation
            thinking_time = self._calculate_thinking_time(board, move_type, complexity)
            analysis['recommended_thinking_time'] = thinking_time
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in position analysis: {e}")
            return {'error': str(e)}
    
    def get_engine_statistics(self) -> Dict:
        """Get comprehensive engine statistics."""
        stats = {
            'rating': self.rating,
            'personality': self.personality,
            'game_phase': self.current_game_phase.value if hasattr(self, 'current_game_phase') else 'unknown',
            'opening_phase': self.opening_phase
        }
        
        # Opening database stats
        if hasattr(self, 'opening_database'):
            stats['opening_database'] = self.opening_database.get_opening_statistics()
        
        # Search engine stats
        if hasattr(self, 'search_engine'):
            stats['search_engine'] = self.search_engine.get_search_statistics()
        
        # Time manager stats
        if hasattr(self, 'time_manager'):
            stats['time_manager'] = self.time_manager.get_time_statistics()
        
        return stats

    def initialize_game_with_timer(
        self, 
        time_control: str = 'rapid_10',
        opponent_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Initialize a game with professional timer and rating tracking.
        
        Args:
            time_control: Time control format
            opponent_rating: Opponent's rating for rating calculations
            
        Returns:
            Game initialization data
        """
        # Create timer
        self.game_timer = TimerManager(time_control)
        
        # Initialize rating tracking if opponent rating provided
        if opponent_rating:
            rating_data = self.rating_integration.initialize_game_rating_tracking(
                white_rating=self.rating if self.rating > opponent_rating else opponent_rating,
                black_rating=self.rating if self.rating <= opponent_rating else opponent_rating,
                time_control=time_control.split('_')[0]  # Extract base time control
            )
        else:
            rating_data = {}
        
        logger.info(f"Game initialized with timer ({time_control}) and rating tracking")
        
        return {
            'timer_state': self.game_timer.get_timer_state(),
            'rating_data': rating_data,
            'engine_rating': self.rating,
            'time_control': time_control
        }
    
    def make_timed_move(self, fen: str, player_color: str) -> Dict[str, Any]:
        """
        Make a move with professional timer tracking.
        
        Args:
            fen: Current position
            player_color: 'white' or 'black' for timer tracking
            
        Returns:
            Move result with timing information
        """
        # Start timer if not started
        if self.game_timer and not self.game_timer.game_started:
            self.game_timer.start_game()
        
        # Get the computer move
        move_result = self.get_computer_move(fen)
        
        # Update timer if this is the engine's move
        if self.game_timer:
            engine_color = self._determine_engine_color(fen)
            if engine_color == player_color:
                timer_state = self.game_timer.make_move(player_color)
                move_result['timer_state'] = timer_state
                
                # Update rating integration
                if self.rating_integration:
                    self.rating_integration.update_timer_on_move(player_color)
        
        return move_result
    
    def get_timer_state(self) -> Dict[str, Any]:
        """Get current timer state."""
        if not self.game_timer:
            return {}
        
        return self.game_timer.get_timer_state()
    
    def get_rating_predictions(self, current_evaluation: float) -> Dict[str, Any]:
        """
        Get rating change predictions based on current position.
        
        Args:
            current_evaluation: Current position evaluation
            
        Returns:
            Rating predictions for different outcomes
        """
        if not self.rating_integration:
            return {}
        
        return self.rating_integration.get_real_time_rating_prediction(current_evaluation)
    
    def finalize_game(self, final_result: str) -> Dict[str, Any]:
        """
        Finalize game with comprehensive analysis.
        
        Args:
            final_result: '1-0', '0-1', or '1/2-1/2'
            
        Returns:
            Complete game analysis including ratings and timing
        """
        if not self.rating_integration:
            return {'result': final_result}
        
        # End timer
        if self.game_timer:
            self.game_timer.game_ended = True
        
        # Get comprehensive analysis
        analysis = self.rating_integration.export_comprehensive_game_data(final_result)
        analysis['engine_stats'] = self._get_engine_performance_stats()
        
        logger.info(f"Game finalized with result: {final_result}")
        
        return analysis
    
    def _determine_engine_color(self, fen: str) -> str:
        """Determine which color the engine is playing based on context."""
        # This is a simplified implementation
        # In a real game, this would be set during initialization
        board = chess.Board(fen)
        return 'white' if board.turn else 'black'
    
    def _get_engine_performance_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics for the current game."""
        return {
            'total_positions_analyzed': getattr(self.search_engine, 'total_positions', 0),
            'average_search_depth': getattr(self.search_engine, 'average_depth', 0),
            'opening_book_usage': getattr(self.search_engine, 'book_hits', 0),
            'cache_efficiency': getattr(self.search_engine, 'cache_hit_rate', 0.0),
            'engine_version': '3.0.0_professional'
        }


def create_chess_engine(rating: int, personality: str = "balanced") -> ChessEngine:
    """
    Factory function to create chess engine.
    
    Args:
        rating: Engine rating (400-2400+)
        personality: Playing style personality
        
    Returns:
        ChessEngine instance
    """
    return ChessEngine(rating, personality)


# Export main classes and functions
__all__ = [
    'ChessEngine',
    'GamePhase',
    'create_chess_engine'
]