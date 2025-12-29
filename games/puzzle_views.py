"""
Puzzle System API Views
Handles puzzle serving, solving, and progress tracking
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, F, Count
from django.utils import timezone
import random
import chess

from .models import Puzzle, PuzzleAttempt, UserPuzzleStats

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_puzzle(request):
    """
    Get a random puzzle for the user based on their rating and preferences.
    
    Query params:
        - category: Filter by category (tactics, endgame, opening, strategy)
        - difficulty: Filter by difficulty (beginner, intermediate, advanced, expert)
        - theme: Filter by tactical theme
        - rating_range: How far from user's rating to look (default: 200)
    """
    user = request.user
    
    # Get or create user puzzle stats
    stats, created = UserPuzzleStats.objects.get_or_create(user=user)
    user_rating = stats.puzzle_rating
    
    # Build query
    puzzles = Puzzle.objects.filter(is_active=True)
    
    # Apply filters
    category = request.GET.get('category')
    if category and category in ['tactics', 'endgame', 'opening', 'strategy', 'checkmate', 'defense']:
        puzzles = puzzles.filter(category=category)
    
    difficulty = request.GET.get('difficulty')
    if difficulty and difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
        puzzles = puzzles.filter(difficulty=difficulty)
    
    theme = request.GET.get('theme')
    if theme:
        puzzles = puzzles.filter(themes__contains=[theme])
    
    # Filter by rating range
    rating_range = int(request.GET.get('rating_range', 200))
    puzzles = puzzles.filter(
        rating__gte=user_rating - rating_range,
        rating__lte=user_rating + rating_range
    )
    
    # Exclude recently attempted puzzles (last 20)
    recent_puzzle_ids = PuzzleAttempt.objects.filter(
        user=user
    ).order_by('-created_at')[:20].values_list('puzzle_id', flat=True)
    
    puzzles = puzzles.exclude(id__in=recent_puzzle_ids)
    
    # Get random puzzle
    puzzle = puzzles.order_by('?').first()
    
    if not puzzle:
        # Fallback: get any active puzzle
        puzzle = Puzzle.objects.filter(is_active=True).order_by('?').first()
    
    if not puzzle:
        return Response({
            'error': 'No puzzles available. Please try again later.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'puzzle': {
            'id': puzzle.id,
            'fen': puzzle.fen,
            'title': puzzle.title or f'Puzzle #{puzzle.id}',
            'description': puzzle.description or puzzle.get_objective(),
            'objective': puzzle.get_objective(),
            'difficulty': puzzle.difficulty,
            'category': puzzle.category,
            'themes': puzzle.themes,
            'rating': puzzle.rating,
            'times_played': puzzle.times_played,
            'solve_rate': puzzle.get_solve_rate(),
        },
        'user_stats': {
            'puzzle_rating': stats.puzzle_rating,
            'puzzles_solved': stats.puzzles_solved,
            'current_streak': stats.current_streak,
            'accuracy': stats.get_accuracy(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_puzzle_by_id(request, puzzle_id):
    """Get a specific puzzle by ID"""
    try:
        puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
    except Puzzle.DoesNotExist:
        return Response({
            'error': 'Puzzle not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'puzzle': {
            'id': puzzle.id,
            'fen': puzzle.fen,
            'title': puzzle.title or f'Puzzle #{puzzle.id}',
            'description': puzzle.description or puzzle.get_objective(),
            'objective': puzzle.get_objective(),
            'difficulty': puzzle.difficulty,
            'category': puzzle.category,
            'themes': puzzle.themes,
            'rating': puzzle.rating,
            'times_played': puzzle.times_played,
            'solve_rate': puzzle.get_solve_rate(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_puzzle_move(request, puzzle_id):
    """
    Validate a move in a puzzle.
    
    Request body:
        - move: Move in UCI format (e.g., 'e2e4')
        - current_position: Current FEN position
        - move_index: Which move in the solution sequence (0-indexed)
    """
    user = request.user
    
    try:
        puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
    except Puzzle.DoesNotExist:
        return Response({
            'error': 'Puzzle not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    move = request.data.get('move', '').strip().lower()
    move_index = request.data.get('move_index', 0)
    current_fen = request.data.get('current_position', puzzle.fen)
    
    if not move:
        return Response({
            'error': 'Move is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate move format
    if len(move) < 4 or len(move) > 5:
        return Response({
            'correct': False,
            'message': 'Invalid move format'
        }, status=status.HTTP_200_OK)
    
    solution = puzzle.solution
    
    if move_index >= len(solution):
        return Response({
            'error': 'Invalid move index'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if the move is correct
    expected_move = solution[move_index].lower()
    is_correct = (move == expected_move)
    
    if is_correct:
        # Calculate next position
        try:
            board = chess.Board(current_fen)
            chess_move = chess.Move.from_uci(move)
            
            if chess_move in board.legal_moves:
                board.push(chess_move)
                new_fen = board.fen()
                
                # Check if there's an opponent response
                opponent_move = None
                if move_index + 1 < len(solution):
                    opponent_move_uci = solution[move_index + 1]
                    try:
                        opp_chess_move = chess.Move.from_uci(opponent_move_uci)
                        if opp_chess_move in board.legal_moves:
                            board.push(opp_chess_move)
                            opponent_move = opponent_move_uci
                            new_fen = board.fen()
                    except:
                        pass
                
                # Check if puzzle is complete
                is_complete = (move_index + 2 >= len(solution)) if opponent_move else (move_index + 1 >= len(solution))
                
                return Response({
                    'correct': True,
                    'message': 'Correct!' if is_complete else 'Good move! Continue...',
                    'new_position': new_fen,
                    'opponent_move': opponent_move,
                    'is_complete': is_complete,
                    'next_move_index': move_index + 2 if opponent_move else move_index + 1
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'correct': False,
                    'message': 'Illegal move'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'correct': False,
                'message': f'Error processing move: {str(e)}'
            }, status=status.HTTP_200_OK)
    else:
        return Response({
            'correct': False,
            'message': "That's not the best move. Try again!",
            'hint': f"Think about {puzzle.category} concepts..." if puzzle.category else None
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_puzzle(request, puzzle_id):
    """
    Record puzzle completion.
    
    Request body:
        - solved: boolean - whether puzzle was solved correctly
        - time_spent: float - time in seconds
        - moves_made: list - moves attempted
        - hints_used: int - number of hints used
    """
    user = request.user
    
    try:
        puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
    except Puzzle.DoesNotExist:
        return Response({
            'error': 'Puzzle not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    solved = request.data.get('solved', False)
    time_spent = float(request.data.get('time_spent', 0))
    moves_made = request.data.get('moves_made', [])
    hints_used = int(request.data.get('hints_used', 0))
    
    # Get user stats
    stats, created = UserPuzzleStats.objects.get_or_create(user=user)
    rating_before = stats.puzzle_rating
    
    # Record attempt on puzzle
    puzzle.record_attempt(solved, time_spent)
    
    # Record user attempt
    attempt = PuzzleAttempt.objects.create(
        user=user,
        puzzle=puzzle,
        solved=solved,
        time_spent=time_spent,
        moves_made=moves_made,
        hints_used=hints_used,
        rating_before=rating_before
    )
    
    # Update user stats
    stats.record_attempt(puzzle, solved, time_spent)
    
    # Update attempt with new rating
    attempt.rating_after = stats.puzzle_rating
    attempt.save()
    
    # Also update user's puzzles_solved count
    if solved:
        user.puzzles_solved = (user.puzzles_solved or 0) + 1
        user.save()
        
        # Check achievements
        try:
            from accounts.achievement_views import check_and_unlock_achievements
            # This will be called on next achievement check
        except:
            pass
    
    return Response({
        'success': True,
        'attempt': {
            'id': attempt.id,
            'solved': solved,
            'time_spent': time_spent,
            'rating_change': stats.puzzle_rating - rating_before
        },
        'stats': {
            'puzzle_rating': stats.puzzle_rating,
            'puzzles_solved': stats.puzzles_solved,
            'puzzles_attempted': stats.puzzles_attempted,
            'current_streak': stats.current_streak,
            'best_streak': stats.best_streak,
            'accuracy': stats.get_accuracy()
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_puzzle_hint(request, puzzle_id):
    """Get a hint for a puzzle"""
    try:
        puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
    except Puzzle.DoesNotExist:
        return Response({
            'error': 'Puzzle not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    move_index = int(request.GET.get('move_index', 0))
    
    if not puzzle.solution or move_index >= len(puzzle.solution):
        return Response({
            'hint': 'Look for tactical opportunities!',
            'hint_type': 'general'
        }, status=status.HTTP_200_OK)
    
    solution_move = puzzle.solution[move_index]
    
    # Parse the move to give a hint
    from_square = solution_move[:2]
    
    # Generate hints based on themes
    themes = puzzle.themes if puzzle.themes else []
    
    if 'fork' in themes:
        hint = "Look for a move that attacks two pieces at once"
    elif 'pin' in themes:
        hint = "Look for a piece that's pinned to a more valuable piece"
    elif 'skewer' in themes:
        hint = "Look for a way to attack through a piece"
    elif 'back_rank' in themes:
        hint = "Check if the back rank is weak"
    elif 'mate_in_1' in themes or 'mate_in_2' in themes:
        hint = "Look for a checkmate sequence"
    elif 'sacrifice' in themes:
        hint = "Sometimes you need to give up material to win"
    else:
        hint = f"Consider the piece on {from_square}"
    
    return Response({
        'hint': hint,
        'hint_type': 'thematic',
        'starting_square': from_square
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_puzzle_solution(request, puzzle_id):
    """Get the full solution for a puzzle (marks as failed if not solved)"""
    try:
        puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
    except Puzzle.DoesNotExist:
        return Response({
            'error': 'Puzzle not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Format solution moves with SAN notation
    solution_formatted = []
    board = chess.Board(puzzle.fen)
    
    for uci_move in puzzle.solution:
        try:
            move = chess.Move.from_uci(uci_move)
            if move in board.legal_moves:
                san = board.san(move)
                solution_formatted.append({
                    'uci': uci_move,
                    'san': san,
                    'fen_after': None  # Could compute if needed
                })
                board.push(move)
        except:
            solution_formatted.append({
                'uci': uci_move,
                'san': uci_move,
                'fen_after': None
            })
    
    return Response({
        'solution': puzzle.solution,
        'solution_formatted': solution_formatted,
        'explanation': puzzle.description or puzzle.get_objective()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_puzzle_stats(request):
    """Get current user's puzzle statistics"""
    user = request.user
    
    stats, created = UserPuzzleStats.objects.get_or_create(user=user)
    
    # Get recent attempts
    recent_attempts = PuzzleAttempt.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    recent_data = [{
        'puzzle_id': a.puzzle_id,
        'solved': a.solved,
        'time_spent': a.time_spent,
        'rating_change': (a.rating_after - a.rating_before) if a.rating_before and a.rating_after else 0,
        'date': a.created_at.isoformat()
    } for a in recent_attempts]
    
    return Response({
        'stats': {
            'puzzle_rating': stats.puzzle_rating,
            'highest_rating': stats.highest_rating,
            'puzzles_attempted': stats.puzzles_attempted,
            'puzzles_solved': stats.puzzles_solved,
            'accuracy': stats.get_accuracy(),
            'current_streak': stats.current_streak,
            'best_streak': stats.best_streak,
            'total_time_spent': stats.total_time_spent,
            'category_breakdown': {
                'tactics': stats.tactics_solved,
                'endgame': stats.endgame_solved,
                'opening': stats.opening_solved,
                'strategy': stats.strategy_solved,
            },
            'last_puzzle_at': stats.last_puzzle_at.isoformat() if stats.last_puzzle_at else None
        },
        'recent_attempts': recent_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_sample_puzzles(request):
    """
    Admin endpoint to create sample puzzles for testing.
    Only for development/setup purposes.
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Admin privileges required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    sample_puzzles = [
        {
            'fen': 'r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
            'solution': ['h5f7'],
            'title': 'Scholar\'s Mate',
            'description': 'Deliver checkmate with the queen',
            'difficulty': 'beginner',
            'category': 'checkmate',
            'themes': ['mate_in_1', 'back_rank'],
            'rating': 800
        },
        {
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
            'solution': ['f3g5', 'd8g5', 'c4f7'],
            'title': 'Knight Fork',
            'description': 'Win material with a knight fork',
            'difficulty': 'intermediate',
            'category': 'tactics',
            'themes': ['fork'],
            'rating': 1200
        },
        {
            'fen': '6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1',
            'solution': ['e1e8'],
            'title': 'Back Rank Mate',
            'description': 'Exploit the weak back rank',
            'difficulty': 'beginner',
            'category': 'checkmate',
            'themes': ['mate_in_1', 'back_rank'],
            'rating': 900
        },
        {
            'fen': 'r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5',
            'solution': ['a4c6', 'd7c6'],
            'title': 'Pin the Knight',
            'description': 'Use a pin to win material',
            'difficulty': 'intermediate',
            'category': 'tactics',
            'themes': ['pin'],
            'rating': 1300
        },
        {
            'fen': '2r3k1/5ppp/p7/1p6/8/1P2B3/P4PPP/2R3K1 w - - 0 1',
            'solution': ['c1c8'],
            'title': 'Rook Endgame',
            'description': 'Find the winning rook move',
            'difficulty': 'intermediate',
            'category': 'endgame',
            'themes': ['endgame_basic'],
            'rating': 1400
        },
        {
            'fen': 'r1b1kb1r/pppp1ppp/5n2/4N2Q/2B1n3/8/PPPP1qPP/RNB1K2R w KQkq - 0 7',
            'solution': ['c4f7', 'e8e7', 'h5e2'],
            'title': 'Queen Sacrifice',
            'description': 'Sacrifice the queen for a winning attack',
            'difficulty': 'advanced',
            'category': 'tactics',
            'themes': ['sacrifice', 'mate_in_3'],
            'rating': 1600
        },
        {
            'fen': '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1',
            'solution': ['e1e2', 'e8e7', 'e2e3', 'e7e6', 'e3e4', 'e6f6', 'e4d5'],
            'title': 'King and Pawn Endgame',
            'description': 'Win the pawn endgame with correct king play',
            'difficulty': 'intermediate',
            'category': 'endgame',
            'themes': ['endgame_basic'],
            'rating': 1350
        },
        {
            'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5',
            'solution': ['c4f7', 'e8f7', 'd1b3', 'd7d5', 'b3b7'],
            'title': 'Italian Game Trap',
            'description': 'Spring the trap in the Italian Game',
            'difficulty': 'advanced',
            'category': 'opening',
            'themes': ['sacrifice', 'discovery'],
            'rating': 1550
        },
    ]
    
    created_count = 0
    for puzzle_data in sample_puzzles:
        puzzle, created = Puzzle.objects.get_or_create(
            fen=puzzle_data['fen'],
            defaults=puzzle_data
        )
        if created:
            created_count += 1
    
    return Response({
        'message': f'Created {created_count} sample puzzles',
        'total_puzzles': Puzzle.objects.count()
    }, status=status.HTTP_200_OK)
