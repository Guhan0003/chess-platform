"""
Chess Game Analysis and Coaching System

Provides post-game analysis with move evaluation, mistake detection,
and pers        self.analysis_engine = ChessEngine(rating=2400, personality="balanced")
        self.player_engine = ChessEngine(rating=player_rating, personality="balanced")alized coaching suggestions based on player rating level.

Features:
- Move-by-move analysis
- Mistake categorization (blunder, mistake, inaccuracy)
- Rating-appropriate coaching advice
- Opening and endgame analysis
- Tactical pattern recognition
- Improvement suggestions
"""

import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time

from .chess_engine import ChessEngine
from .evaluation import PositionEvaluator
from .opening_database import OpeningDatabase


class MistakeType(Enum):
    """Types of chess mistakes."""
    BLUNDER = "blunder"           # Major mistake (-300+ centipawns)
    MISTAKE = "mistake"           # Significant error (-100 to -300)
    INACCURACY = "inaccuracy"     # Minor error (-50 to -100)
    MISSED_WIN = "missed_win"     # Missed forced win
    MISSED_TACTIC = "missed_tactic"  # Missed tactical opportunity
    BOOK_DEVIATION = "book_deviation"  # Deviation from opening theory
    TIME_TROUBLE = "time_trouble"      # Poor move due to time pressure


@dataclass
class MoveAnalysis:
    """Analysis of a single move."""
    move_number: int
    move: chess.Move
    san_notation: str
    position_before: str  # FEN
    position_after: str   # FEN
    
    # Evaluation
    evaluation_before: float
    evaluation_after: float
    evaluation_change: float
    
    # Best alternatives
    best_move: Optional[chess.Move]
    best_move_san: str
    best_evaluation: float
    
    # Analysis
    mistake_type: Optional[MistakeType]
    mistake_severity: int  # 0-100 scale
    
    # Comments and suggestions
    analysis_comment: str
    tactical_themes: List[str]
    coaching_tip: str
    
    # Timing
    time_taken: Optional[float]
    time_remaining: Optional[float]


@dataclass
class GameAnalysis:
    """Complete analysis of a chess game."""
    game_info: Dict[str, Any]
    final_result: str
    
    # Move analysis
    moves_analysis: List[MoveAnalysis]
    
    # Game phases
    opening_analysis: Dict[str, Any]
    middlegame_analysis: Dict[str, Any]
    endgame_analysis: Dict[str, Any]
    
    # Statistics
    accuracy_white: float
    accuracy_black: float
    blunders_white: int
    blunders_black: int
    mistakes_white: int
    mistakes_black: int
    inaccuracies_white: int
    inaccuracies_black: int
    
    # Overall assessment
    game_quality: str
    key_moments: List[MoveAnalysis]
    improvement_areas: List[str]
    strengths: List[str]
    
    # Coaching summary
    coaching_summary: str
    study_suggestions: List[str]


class GameAnalyzer:
    """
    Advanced game analysis system with rating-appropriate feedback.
    
    Analyzes games at different depths based on player rating.
    Provides educational feedback and improvement suggestions.
    """
    
    def __init__(self, player_rating: int, opponent_rating: int = None):
        """
        Initialize game analyzer.
        
        Args:
            player_rating: Rating of player whose games we're analyzing
            opponent_rating: Rating of opponent (if known)
        """
        self.player_rating = player_rating
        self.opponent_rating = opponent_rating or player_rating
        
        # Create analysis engines
        self.analysis_engine = ChessEngine(rating=2400, personality="balanced")
        self.player_engine = ChessEngine(rating=player_rating, personality="balanced")
        
        # Position evaluator
        self.evaluator = PositionEvaluator(rating=2400)
        
        # Opening book
        self.opening_book = OpeningDatabase(rating=2400)
        
        # Analysis settings based on player rating
        self.analysis_depth = self._get_analysis_depth()
        self.analysis_time = self._get_analysis_time()
        
        # Mistake thresholds (in centipawns)
        self.blunder_threshold = 300
        self.mistake_threshold = 100
        self.inaccuracy_threshold = 50
    
    def analyze_game(self, pgn_game: chess.pgn.Game, player_color: chess.Color = chess.WHITE) -> GameAnalysis:
        """
        Perform comprehensive game analysis.
        
        Args:
            pgn_game: Game in PGN format
            player_color: Which color the player was playing
            
        Returns:
            Complete GameAnalysis object
        """
        print(f"Starting analysis for {player_color} player (rating: {self.player_rating})")
        
        # Extract game information
        game_info = self._extract_game_info(pgn_game)
        
        # Analyze moves
        moves_analysis = self._analyze_moves(pgn_game)
        
        # Analyze game phases
        opening_analysis = self._analyze_opening(moves_analysis)
        middlegame_analysis = self._analyze_middlegame(moves_analysis)
        endgame_analysis = self._analyze_endgame(moves_analysis)
        
        # Calculate statistics
        stats = self._calculate_statistics(moves_analysis, player_color)
        
        # Identify key moments
        key_moments = self._identify_key_moments(moves_analysis)
        
        # Generate coaching feedback
        improvement_areas = self._identify_improvement_areas(moves_analysis, player_color)
        strengths = self._identify_strengths(moves_analysis, player_color)
        coaching_summary = self._generate_coaching_summary(stats, improvement_areas, strengths)
        study_suggestions = self._generate_study_suggestions(moves_analysis, player_color)
        
        return GameAnalysis(
            game_info=game_info,
            final_result=game_info.get("result", "*"),
            moves_analysis=moves_analysis,
            opening_analysis=opening_analysis,
            middlegame_analysis=middlegame_analysis,
            endgame_analysis=endgame_analysis,
            accuracy_white=stats["accuracy_white"],
            accuracy_black=stats["accuracy_black"],
            blunders_white=stats["blunders_white"],
            blunders_black=stats["blunders_black"],
            mistakes_white=stats["mistakes_white"],
            mistakes_black=stats["mistakes_black"],
            inaccuracies_white=stats["inaccuracies_white"],
            inaccuracies_black=stats["inaccuracies_black"],
            game_quality=self._assess_game_quality(stats),
            key_moments=key_moments,
            improvement_areas=improvement_areas,
            strengths=strengths,
            coaching_summary=coaching_summary,
            study_suggestions=study_suggestions
        )
    
    def _analyze_moves(self, pgn_game: chess.pgn.Game) -> List[MoveAnalysis]:
        """Analyze each move in the game."""
        board = chess.Board()
        moves_analysis = []
        move_number = 1
        
        previous_evaluation = 0.0
        
        for move in pgn_game.mainline_moves():
            print(f"Analyzing move {move_number}: {board.san(move)}")
            
            # Position before move
            position_before = board.fen()
            
            # Get current evaluation
            current_eval = self._get_position_evaluation(board)
            
            # Get best move according to analysis engine
            best_move_info = self._get_best_move(board)
            best_move = best_move_info["move"]
            best_evaluation = best_move_info["evaluation"]
            
            # Apply the actual move
            san_notation = board.san(move)
            board.push(move)
            position_after = board.fen()
            
            # Evaluation after move
            move_evaluation = -self._get_position_evaluation(board)  # Negative because turn changed
            
            # Calculate evaluation change
            eval_change = move_evaluation - current_eval
            
            # Determine if move was a mistake
            mistake_type, mistake_severity = self._classify_mistake(
                move, best_move, eval_change, current_eval
            )
            
            # Generate analysis comments
            analysis_comment = self._generate_move_comment(
                move, best_move, eval_change, mistake_type, board
            )
            
            # Identify tactical themes
            tactical_themes = self._identify_tactical_themes(board, move)
            
            # Generate coaching tip
            coaching_tip = self._generate_coaching_tip(
                move, mistake_type, tactical_themes, move_number
            )
            
            # Create move analysis
            move_analysis = MoveAnalysis(
                move_number=move_number,
                move=move,
                san_notation=san_notation,
                position_before=position_before,
                position_after=position_after,
                evaluation_before=current_eval,
                evaluation_after=move_evaluation,
                evaluation_change=eval_change,
                best_move=best_move,
                best_move_san=board.san(best_move) if best_move else "",
                best_evaluation=best_evaluation,
                mistake_type=mistake_type,
                mistake_severity=mistake_severity,
                analysis_comment=analysis_comment,
                tactical_themes=tactical_themes,
                coaching_tip=coaching_tip,
                time_taken=None,  # Would need game with time info
                time_remaining=None
            )
            
            moves_analysis.append(move_analysis)
            previous_evaluation = move_evaluation
            move_number += 1
        
        return moves_analysis
    
    def _get_position_evaluation(self, board: chess.Board) -> float:
        """Get position evaluation from analysis engine."""
        # Use simplified evaluation for speed
        # In production, would use full engine analysis
        result = self.analysis_engine.get_computer_move(board.fen())
        
        if result["success"]:
            return result["engine_info"]["evaluation"]
        else:
            return 0.0
    
    def _get_best_move(self, board: chess.Board) -> Dict:
        """Get best move and evaluation from analysis engine."""
        result = self.analysis_engine.get_computer_move(board.fen())
        
        if result["success"]:
            move_uci = result["move"]["uci"]
            best_move = chess.Move.from_uci(move_uci)
            evaluation = result["engine_info"]["evaluation"]
            
            return {
                "move": best_move,
                "evaluation": evaluation
            }
        else:
            return {
                "move": None,
                "evaluation": 0.0
            }
    
    def _classify_mistake(self, played_move: chess.Move, best_move: Optional[chess.Move], 
                         eval_change: float, position_eval: float) -> Tuple[Optional[MistakeType], int]:
        """Classify the type and severity of a mistake."""
        if not best_move or played_move == best_move:
            return None, 0
        
        # Convert evaluation change to centipawns
        centipawn_loss = abs(eval_change * 100)
        
        if centipawn_loss >= self.blunder_threshold:
            if position_eval > 500:  # Winning position
                return MistakeType.MISSED_WIN, min(100, int(centipawn_loss / 10))
            else:
                return MistakeType.BLUNDER, min(100, int(centipawn_loss / 10))
        elif centipawn_loss >= self.mistake_threshold:
            return MistakeType.MISTAKE, min(100, int(centipawn_loss / 5))
        elif centipawn_loss >= self.inaccuracy_threshold:
            return MistakeType.INACCURACY, min(100, int(centipawn_loss / 2))
        
        return None, 0
    
    def _generate_move_comment(self, played_move: chess.Move, best_move: Optional[chess.Move],
                              eval_change: float, mistake_type: Optional[MistakeType], 
                              board: chess.Board) -> str:
        """Generate human-readable comment for the move."""
        if not mistake_type:
            return "Good move!"
        
        centipawn_loss = abs(eval_change * 100)
        
        if mistake_type == MistakeType.BLUNDER:
            return f"This is a blunder! You lost about {centipawn_loss:.0f} centipawns. Consider {board.san(best_move)} instead."
        elif mistake_type == MistakeType.MISTAKE:
            return f"This move loses material or position. {board.san(best_move)} was better."
        elif mistake_type == MistakeType.INACCURACY:
            return f"A slightly inaccurate move. {board.san(best_move)} maintains a better position."
        elif mistake_type == MistakeType.MISSED_WIN:
            return f"You missed a winning opportunity! {board.san(best_move)} would have been much stronger."
        
        return "Analyze this position more carefully."
    
    def _identify_tactical_themes(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Identify tactical patterns in the position."""
        themes = []
        
        # Basic tactical detection (simplified)
        if board.is_capture(move):
            themes.append("capture")
        
        if board.gives_check(move):
            themes.append("check")
        
        if move.promotion:
            themes.append("promotion")
        
        if board.is_castling(move):
            themes.append("castling")
        
        # TODO: Add more sophisticated tactical pattern detection
        # (pins, forks, skewers, discovered attacks, etc.)
        
        return themes
    
    def _generate_coaching_tip(self, move: chess.Move, mistake_type: Optional[MistakeType],
                              tactical_themes: List[str], move_number: int) -> str:
        """Generate coaching tip based on player rating and mistake type."""
        if self.player_rating < 800:
            # Beginner tips
            if mistake_type == MistakeType.BLUNDER:
                return "Always check if your pieces are safe after moving. Look for opponent threats!"
            elif "capture" in tactical_themes:
                return "When capturing, make sure you're not losing more than you gain."
            else:
                return "Focus on basic principles: control the center, develop pieces, keep your king safe."
        
        elif self.player_rating < 1200:
            # Intermediate beginner tips
            if mistake_type in [MistakeType.BLUNDER, MistakeType.MISTAKE]:
                return "Take more time to calculate the consequences of your moves."
            elif "check" in tactical_themes:
                return "Checks can be powerful, but make sure they improve your position."
            else:
                return "Look for tactics before making positional moves."
        
        elif self.player_rating < 1600:
            # Intermediate tips
            if mistake_type == MistakeType.MISSED_WIN:
                return "In winning positions, look for forcing moves that maintain your advantage."
            elif mistake_type == MistakeType.BLUNDER:
                return "Double-check for tactical shots before committing to your move."
            else:
                return "Consider your opponent's best responses before moving."
        
        else:
            # Advanced tips
            if mistake_type:
                return "Analyze critical positions more deeply and consider all candidate moves."
            else:
                return "Well played! Continue to maintain pressure and look for improvements."
    
    def _calculate_statistics(self, moves_analysis: List[MoveAnalysis], 
                             player_color: chess.Color) -> Dict[str, Any]:
        """Calculate game statistics."""
        white_moves = [m for m in moves_analysis if m.move_number % 2 == 1]
        black_moves = [m for m in moves_analysis if m.move_number % 2 == 0]
        
        def calculate_color_stats(moves):
            blunders = sum(1 for m in moves if m.mistake_type == MistakeType.BLUNDER)
            mistakes = sum(1 for m in moves if m.mistake_type == MistakeType.MISTAKE)
            inaccuracies = sum(1 for m in moves if m.mistake_type == MistakeType.INACCURACY)
            
            # Calculate accuracy (percentage of moves without significant errors)
            total_moves = len(moves)
            error_moves = blunders + mistakes
            accuracy = ((total_moves - error_moves) / total_moves * 100) if total_moves > 0 else 100
            
            return {
                "blunders": blunders,
                "mistakes": mistakes,
                "inaccuracies": inaccuracies,
                "accuracy": accuracy
            }
        
        white_stats = calculate_color_stats(white_moves)
        black_stats = calculate_color_stats(black_moves)
        
        return {
            "accuracy_white": white_stats["accuracy"],
            "accuracy_black": black_stats["accuracy"],
            "blunders_white": white_stats["blunders"],
            "blunders_black": black_stats["blunders"],
            "mistakes_white": white_stats["mistakes"],
            "mistakes_black": black_stats["mistakes"],
            "inaccuracies_white": white_stats["inaccuracies"],
            "inaccuracies_black": black_stats["inaccuracies"]
        }
    
    # Placeholder methods for additional analysis
    def _extract_game_info(self, pgn_game: chess.pgn.Game) -> Dict[str, Any]:
        """Extract game metadata."""
        return {
            "white": pgn_game.headers.get("White", "Unknown"),
            "black": pgn_game.headers.get("Black", "Unknown"),
            "result": pgn_game.headers.get("Result", "*"),
            "date": pgn_game.headers.get("Date", "Unknown"),
            "event": pgn_game.headers.get("Event", "Unknown")
        }
    
    def _analyze_opening(self, moves_analysis: List[MoveAnalysis]) -> Dict[str, Any]:
        """Analyze opening phase."""
        opening_moves = moves_analysis[:20]  # First 20 moves
        return {"phase": "opening", "moves_count": len(opening_moves)}
    
    def _analyze_middlegame(self, moves_analysis: List[MoveAnalysis]) -> Dict[str, Any]:
        """Analyze middlegame phase."""
        return {"phase": "middlegame"}
    
    def _analyze_endgame(self, moves_analysis: List[MoveAnalysis]) -> Dict[str, Any]:
        """Analyze endgame phase."""
        return {"phase": "endgame"}
    
    def _identify_key_moments(self, moves_analysis: List[MoveAnalysis]) -> List[MoveAnalysis]:
        """Identify critical moments in the game."""
        key_moments = []
        for move in moves_analysis:
            if move.mistake_type in [MistakeType.BLUNDER, MistakeType.MISSED_WIN]:
                key_moments.append(move)
        return key_moments[:5]  # Top 5 key moments
    
    def _identify_improvement_areas(self, moves_analysis: List[MoveAnalysis], 
                                   player_color: chess.Color) -> List[str]:
        """Identify areas for improvement."""
        areas = []
        
        player_moves = [m for m in moves_analysis 
                       if (player_color == chess.WHITE and m.move_number % 2 == 1) or
                          (player_color == chess.BLACK and m.move_number % 2 == 0)]
        
        blunders = sum(1 for m in player_moves if m.mistake_type == MistakeType.BLUNDER)
        tactical_themes = [theme for m in player_moves for theme in m.tactical_themes]
        
        if blunders > 2:
            areas.append("Calculation and tactics")
        
        if "capture" in tactical_themes:
            areas.append("Material evaluation")
        
        return areas
    
    def _identify_strengths(self, moves_analysis: List[MoveAnalysis], 
                           player_color: chess.Color) -> List[str]:
        """Identify player strengths."""
        return ["Solid play"]  # Placeholder
    
    def _generate_coaching_summary(self, stats: Dict, improvement_areas: List[str], 
                                  strengths: List[str]) -> str:
        """Generate overall coaching summary."""
        accuracy = stats["accuracy_white"] if stats["accuracy_white"] > 0 else stats["accuracy_black"]
        
        summary = f"Your accuracy this game was {accuracy:.1f}%. "
        
        if accuracy >= 90:
            summary += "Excellent play! "
        elif accuracy >= 80:
            summary += "Good game overall. "
        elif accuracy >= 70:
            summary += "Decent play with some room for improvement. "
        else:
            summary += "This game had several inaccuracies to learn from. "
        
        if improvement_areas:
            summary += f"Focus on improving: {', '.join(improvement_areas)}."
        
        return summary
    
    def _generate_study_suggestions(self, moves_analysis: List[MoveAnalysis], 
                                   player_color: chess.Color) -> List[str]:
        """Generate specific study suggestions."""
        suggestions = []
        
        player_moves = [m for m in moves_analysis 
                       if (player_color == chess.WHITE and m.move_number % 2 == 1) or
                          (player_color == chess.BLACK and m.move_number % 2 == 0)]
        
        if any(m.mistake_type == MistakeType.BLUNDER for m in player_moves):
            suggestions.append("Practice tactical puzzles to improve calculation")
        
        if any("capture" in m.tactical_themes for m in player_moves):
            suggestions.append("Study basic piece values and exchanges")
        
        return suggestions
    
    def _assess_game_quality(self, stats: Dict) -> str:
        """Assess overall game quality."""
        avg_accuracy = (stats["accuracy_white"] + stats["accuracy_black"]) / 2
        
        if avg_accuracy >= 90:
            return "High quality"
        elif avg_accuracy >= 80:
            return "Good quality"
        elif avg_accuracy >= 70:
            return "Average quality"
        else:
            return "Below average quality"
    
    def _get_analysis_depth(self) -> int:
        """Get analysis depth based on player rating."""
        if self.player_rating < 1000:
            return 8
        elif self.player_rating < 1600:
            return 12
        else:
            return 16
    
    def _get_analysis_time(self) -> float:
        """Get analysis time per move based on player rating."""
        if self.player_rating < 1000:
            return 1.0  # 1 second per move
        elif self.player_rating < 1600:
            return 2.0  # 2 seconds per move
        else:
            return 3.0  # 3 seconds per move


# Factory function for external use
def create_game_analyzer(player_rating: int, opponent_rating: int = None) -> GameAnalyzer:
    """
    Create game analyzer for specific rating level.
    
    Args:
        player_rating: Rating of player to analyze
        opponent_rating: Rating of opponent
        
    Returns:
        Configured GameAnalyzer instance
    """
    return GameAnalyzer(player_rating, opponent_rating)