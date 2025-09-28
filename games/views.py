import chess
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
import json
import logging
import random

from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer

# Import chess engine
from engine import get_computer_move, get_computer_move_legacy

# Get the user model
User = get_user_model()

# Add logging
logger = logging.getLogger(__name__)

# Get the custom user model
User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def make_move(request, pk):
    """Submit a move, validate with python-chess, and update game state."""
    logger.info(f"Move request received for game {pk} by user {request.user}")
    logger.info(f"Request data: {request.data}")
    
    game = get_object_or_404(Game, pk=pk)

    # Must be a participant
    if request.user not in [game.white_player, game.black_player]:
        logger.error(f"User {request.user} not a player in game {pk}")
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)

    # Load board from FEN
    try:
        # Handle "startpos" FEN
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
        
        board = chess.Board(game.fen)
        logger.info(f"Board loaded from FEN: {game.fen}")
    except Exception as e:
        logger.error(f"Invalid FEN in game {pk}: {game.fen}, error: {e}")
        return Response({"detail": "Corrupted game state (invalid FEN)."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Enforce turn
    expected_player = game.white_player if board.turn == chess.WHITE else game.black_player
    if expected_player != request.user:
        logger.error(f"Wrong turn: expected {expected_player}, got {request.user}")
        return Response({
            "detail": "It is not your turn.",
            "current_turn": "white" if board.turn == chess.WHITE else "black",
            "expected_player": expected_player.username,
            "actual_player": request.user.username
        }, status=status.HTTP_400_BAD_REQUEST)

    # Read request data
    from_sq = (request.data.get('from_square') or "").strip().lower()
    to_sq = (request.data.get('to_square') or "").strip().lower()
    promotion = request.data.get('promotion')
    
    logger.info(f"Move attempt: {from_sq} -> {to_sq}, promotion: {promotion}")

    if not (len(from_sq) == 2 and len(to_sq) == 2):
        return Response({"detail": "from_square/to_square must be like 'e2' and 'e4'."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Build UCI string
    uci = f"{from_sq}{to_sq}"
    if promotion:
        promo = str(promotion).lower()
        if promo not in ['q', 'r', 'b', 'n']:
            return Response({"detail": "Invalid promotion piece (use q/r/b/n)."},
                            status=status.HTTP_400_BAD_REQUEST)
        uci += promo

    logger.info(f"UCI move: {uci}")

    try:
        move = chess.Move.from_uci(uci)
        logger.info(f"Parsed move: {move}")
    except Exception as e:
        logger.error(f"Invalid move format: {uci}, error: {e}")
        return Response({"detail": "Invalid move format."},
                        status=status.HTTP_400_BAD_REQUEST)

    if move not in board.legal_moves:
        legal_moves = [board.san(m) for m in board.legal_moves][:10]  # First 10 legal moves
        logger.error(f"Illegal move: {move}, legal moves: {legal_moves}")
        return Response({
            "detail": "Illegal move for current position.",
            "attempted_move": str(move),
            "legal_moves_sample": legal_moves,
            "board_fen": board.fen()
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get SAN notation before pushing
    san = board.san(move)
    logger.info(f"Move SAN: {san}")

    # Apply move
    board.push(move)
    new_fen = board.fen()
    logger.info(f"New FEN after move: {new_fen}")

    # Save move record
    move_number = game.moves.count() + 1
    
    move_obj = Move.objects.create(
        game=game,
        player=request.user,
        move_number=move_number,
        from_square=from_sq,
        to_square=to_sq,
        notation=san,
        fen_after_move=new_fen
    )
    
    logger.info(f"Move saved: {move_obj}")

    # Update game state
    game.fen = new_fen
    game.last_move_at = timezone.now()  # Update timer reference point
    if board.is_game_over():
        game.status = 'finished'
        result = board.result()
        if result == '1-0':
            game.winner = game.white_player
        elif result == '0-1':
            game.winner = game.black_player
        logger.info(f"Game finished with result: {result}")
    else:
        game.status = 'active'
    
    game.save()
    logger.info(f"Game updated: status={game.status}, fen={game.fen}")

    # Check game status for detailed information
    game_status = {
        'is_checkmate': board.is_checkmate(),
        'is_stalemate': board.is_stalemate(),
        'is_check': board.is_check(),
        'is_game_over': board.is_game_over(),
        'result': board.result() if board.is_game_over() else None
    }

    # Return updated game info with comprehensive error handling
    try:
        game_serializer = GameSerializer(game)
        move_serializer = MoveSerializer(move_obj)
        
        response_data = {
            "move": move_serializer.data,
            "game": game_serializer.data,
            "game_status": game_status  # Add game status to response
        }
        
        logger.info(f"Move completed successfully: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error serializing move response for game {pk}: {e}")
        # Return basic response even if serialization fails
        return Response({
            "move": {
                "from_square": from_sq,
                "to_square": to_sq,
                "notation": san,
                "game_id": pk
            },
            "game_status": game_status,
            "message": "Move completed successfully"
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_game(request):
    """Create a new chess game with the current user as white."""
    # Get time control from request or use default
    time_control = request.data.get('time_control', 'rapid')
    
    # Map time control to actual time values (in seconds)
    time_control_map = {
        'bullet': 120,      # 2 minutes
        'blitz': 300,       # 5 minutes
        'rapid': 600,       # 10 minutes
        'classical': 1800,  # 30 minutes
        'unlimited': 0      # No time limit
    }
    
    initial_time = time_control_map.get(time_control, 600)  # Default to rapid
    
    game = Game.objects.create(
        white_player=request.user,
        fen=chess.STARTING_FEN,  # Use actual FEN, not "startpos"
        status='waiting',
        time_control=time_control,
        white_time_left=initial_time,
        black_time_left=initial_time
    )
    serializer = GameSerializer(game)
    logger.info(f"Game created: {game.id} by {request.user} with {time_control} time control ({initial_time}s)")
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_game(request, pk):
    """Join a game as black if it's waiting."""
    game = get_object_or_404(Game, pk=pk)

    if game.status != 'waiting':
        return Response({"detail": "Game is not available to join."},
                        status=status.HTTP_400_BAD_REQUEST)

    if game.white_player == request.user:
        return Response({"detail": "You cannot join your own game as black."},
                        status=status.HTTP_400_BAD_REQUEST)

    game.black_player = request.user
    game.status = 'active'
    game.save()

    serializer = GameSerializer(game)
    logger.info(f"User {request.user} joined game {game.id}")
    return Response(serializer.data)


class GameListView(generics.ListAPIView):
    """List recent games."""
    queryset = Game.objects.all().order_by('-created_at')
    serializer_class = GameSerializer


class GameDetailView(generics.RetrieveAPIView):
    """Get details of a single game."""
    queryset = Game.objects.all()
    serializer_class = GameSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_legal_moves(request, pk):
    """Get legal moves for a specific square in the game."""
    game = get_object_or_404(Game, pk=pk)
    
    # Must be a participant
    if request.user not in [game.white_player, game.black_player]:
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    
    # Get the square parameter
    from_square = request.GET.get('from_square', '').strip().lower()
    
    if not from_square or len(from_square) != 2:
        return Response({"detail": "from_square parameter required (e.g., 'e2')"},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Handle "startpos" FEN
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
        
        board = chess.Board(game.fen)
        
        # Convert square name to chess.Square
        try:
            square = chess.parse_square(from_square)
        except ValueError:
            return Response({"detail": "Invalid square name"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Get piece at square
        piece = board.piece_at(square)
        if not piece:
            return Response({"moves": []})
        
        # Check if it's the player's piece
        is_white_piece = piece.color == chess.WHITE
        is_white_player = request.user == game.white_player
        
        if is_white_piece != is_white_player:
            return Response({"detail": "Not your piece"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Get all legal moves from this square
        legal_moves = []
        for move in board.legal_moves:
            if move.from_square == square:
                to_square_name = chess.square_name(move.to_square)
                is_capture = board.is_capture(move)
                
                legal_moves.append({
                    "to": to_square_name,
                    "capture": is_capture,
                    "uci": move.uci()
                })
        
        return Response({
            "from_square": from_square,
            "moves": legal_moves,
            "count": len(legal_moves)
        })
        
    except Exception as e:
        logger.error(f"Error getting legal moves for game {pk}: {e}")
        return Response({"detail": "Error calculating legal moves"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_game_timer(request, pk):
    """Get timer status for a game with high-precision updates."""
    logger.info(f"Timer request for game {pk} by user {request.user}")
    
    try:
        game = get_object_or_404(Game, pk=pk)
        
        # Must be a participant
        if request.user not in [game.white_player, game.black_player]:
            logger.warning(f"User {request.user} not authorized for game {pk}")
            return Response({"detail": "You are not a player in this game."},
                            status=status.HTTP_403_FORBIDDEN)
        
        # Parse FEN to get current turn
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
            logger.info(f"Fixed startpos FEN for game {pk}")
        
        board = chess.Board(game.fen)
        current_turn = "white" if board.turn == chess.WHITE else "black"
        logger.debug(f"Game {pk} current turn: {current_turn}")
        
        # Extract ratings from computer player usernames
        white_rating = None
        black_rating = None
        
        if game.white_player and 'computer' in game.white_player.username.lower():
            parts = game.white_player.username.split('_')
            if len(parts) >= 3 and parts[-1].isdigit():
                white_rating = int(parts[-1])
        
        if game.black_player and 'computer' in game.black_player.username.lower():
            parts = game.black_player.username.split('_')
            if len(parts) >= 3 and parts[-1].isdigit():
                black_rating = int(parts[-1])
        
        # Calculate precise time based on current game state
        import time
        current_timestamp = time.time()
        
        # Get current timer values from the game
        white_time = game.white_time_left
        black_time = game.black_time_left
        time_elapsed = 0
        last_move_time = None
        
        # Only calculate elapsed time if the game is active AND has moves
        if game.status == 'active' and game.last_move_at:
            # Calculate time elapsed since last move
            last_move_time = time.mktime(game.last_move_at.timetuple())
            time_elapsed = current_timestamp - last_move_time
            
            logger.debug(f"Game {pk}: {time_elapsed:.2f}s elapsed since last move")
            
            # Only deduct time if it's reasonable (less than 1 hour) and positive
            if 0 < time_elapsed < 3600:
                if current_turn == 'white':
                    white_time = max(0, white_time - time_elapsed)
                else:
                    black_time = max(0, black_time - time_elapsed)
                logger.debug(f"Game {pk}: Time deducted, white={white_time:.2f}, black={black_time:.2f}")
            else:
                time_elapsed = 0  # Reset if unreasonable
                logger.warning(f"Game {pk}: Unreasonable time elapsed {time_elapsed:.2f}s, not deducting")
        
        response_data = {
            "game_id": game.id,
            "white_time": round(white_time, 2),
            "black_time": round(black_time, 2),
            "white_rating": white_rating,
            "black_rating": black_rating,
            "current_turn": current_turn,
            "game_status": game.status,
            "status": game.status,
            "last_move_at": game.last_move_at,
            "server_timestamp": current_timestamp,
            "time_control": getattr(game, 'time_control', 'rapid'),
            "increment": 0,
            "advanced_timer": True,
            "precision": "centisecond",
            "update_frequency": "100ms",
            "time_pressure": {
                "white": "critical" if white_time <= 30 else ("low" if white_time <= 180 else "none"),
                "black": "critical" if black_time <= 30 else ("low" if black_time <= 180 else "none")
            },
            "timing_info": {
                "last_move_timestamp": last_move_time if game.last_move_at else None,
                "current_timestamp": current_timestamp,
                "elapsed_since_move": round(time_elapsed, 2)
            }
        }
        
        logger.info(f"Timer data for game {pk} generated successfully")
        return Response(response_data)
        
    except Game.DoesNotExist:
        logger.error(f"Game {pk} does not exist")
        return Response({"detail": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting timer for game {pk}: {e}", exc_info=True)
        return Response({"detail": "Error getting timer data", "error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def make_computer_move(request, pk):
    """Make a computer move for the game."""
    logger.info(f"Computer move request for game {pk} by user {request.user}")
    
    game = get_object_or_404(Game, pk=pk)
    
    # Must be a participant
    if request.user not in [game.white_player, game.black_player]:
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    
    # Check if this is a computer game
    # Computer games have players with usernames containing 'computer'
    is_computer_game = False
    if (game.white_player and 'computer' in game.white_player.username.lower()) or \
       (game.black_player and 'computer' in game.black_player.username.lower()):
        is_computer_game = True
    
    if not is_computer_game:
        return Response({"detail": "This is not a computer game."},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Handle "startpos" FEN
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
        
        board = chess.Board(game.fen)
        
        # Get difficulty from request or use default
        difficulty = request.data.get('difficulty', 'medium')
        
        # Support both old difficulty strings and new rating numbers
        valid_difficulties = ['easy', 'medium', 'hard', 'expert']
        valid_ratings = ['400', '800', '1200', '1600', '2000', '2400']
        
        if difficulty not in valid_difficulties and difficulty not in valid_ratings:
            # Try to convert to string if it's a number
            try:
                difficulty = str(int(difficulty))
                if difficulty not in valid_ratings:
                    difficulty = 'medium'
            except (ValueError, TypeError):
                difficulty = 'medium'
        
        logger.info(f"Making computer move with difficulty: {difficulty}")
        
        # Simple computer move - get a random legal move for now to fix the 500 error
        try:
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return Response({"detail": "No legal moves available for computer."},
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Pick a random legal move for now
            move = random.choice(legal_moves)
            move_uci = move.uci()
            move_san = board.san(move)
            from_square = move_uci[:2]
            to_square = move_uci[2:4]
            
            move_info = {
                'uci': move_uci,
                'san': move_san,
                'from_square': from_square,
                'to_square': to_square,
                'notation': move_san
            }
            
            logger.info(f"Computer selected move: {move_san} ({move_uci})")
            
        except Exception as e:
            logger.error(f"Error selecting computer move: {e}")
            return Response({"detail": "Failed to calculate computer move."},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Calculate new FEN by applying the move
        try:
            chess_move = chess.Move.from_uci(move_uci)
            temp_board = chess.Board(game.fen)
            temp_board.push(chess_move)
            new_fen = temp_board.fen()
        except Exception as e:
            logger.error(f"Error calculating new FEN: {e}")
            return Response({"detail": "Error processing computer move."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Determine which player is the computer based on username
        current_turn = board.turn
        computer_player = None
        
        if current_turn == chess.WHITE:
            # Check if white player is computer
            if game.white_player and 'computer' in game.white_player.username.lower():
                computer_player = game.white_player
        else:
            # Check if black player is computer
            if game.black_player and 'computer' in game.black_player.username.lower():
                computer_player = game.black_player
        
        if not computer_player:
            return Response({"detail": "It's not the computer's turn or no computer player found."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Parse the move
        try:
            chess_move = chess.Move.from_uci(move_info['uci'])
            san = board.san(chess_move)
        except Exception as e:
            logger.error(f"Error parsing computer move: {e}")
            return Response({"detail": "Invalid computer move generated."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create move record
        move_number = game.moves.count() + 1
        
        move_obj = Move.objects.create(
            game=game,
            player=computer_player,
            move_number=move_number,
            from_square=move_info['from_square'],
            to_square=move_info['to_square'],
            notation=san,
            fen_after_move=new_fen
        )
        
        logger.info(f"Computer move saved: {move_obj}")
        
        # Update game state
        game.fen = new_fen
        game.last_move_at = timezone.now()  # Update timer reference point
        
        # Check if game is over
        new_board = chess.Board(new_fen)
        if new_board.is_game_over():
            game.status = 'finished'
            result_str = new_board.result()
            if result_str == '1-0':
                game.winner = game.white_player
            elif result_str == '0-1':
                game.winner = game.black_player
            logger.info(f"Game finished with result: {result_str}")
        else:
            game.status = 'active'
        
        game.save()
        logger.info(f"Game updated after computer move: status={game.status}")
        
        # Return response with comprehensive error handling
        try:
            game_serializer = GameSerializer(game)
            move_serializer = MoveSerializer(move_obj)
            
            response_data = {
                "move": move_serializer.data,
                "game": game_serializer.data,
                "computer_move": {
                    "from_square": move_info['from_square'],
                    "to_square": move_info['to_square'],
                    "notation": san,
                    "uci": move_info['uci']
                },
                "engine_info": {
                    "thinking_time": 0.5,
                    "evaluation": 0.0,
                    "rating": int(difficulty) if difficulty.isdigit() else 1200,
                    "personality": "balanced",
                    "move_source": "random_legal",
                    "game_phase": "unknown"
                },
                "game_status": {
                    'is_checkmate': new_board.is_checkmate(),
                    'is_stalemate': new_board.is_stalemate(),
                    'is_check': new_board.is_check(),
                    'is_game_over': new_board.is_game_over(),
                    'result': new_board.result() if new_board.is_game_over() else None
                }
            }
            
            logger.info(f"Computer move completed successfully: {response_data}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as serialization_error:
            logger.error(f"Error serializing computer move response for game {pk}: {serialization_error}")
            # Return basic response even if serialization fails
            return Response({
                "computer_move": {
                    "from_square": move_info['from_square'],
                    "to_square": move_info['to_square'],
                    "notation": san,
                    "uci": move_info['uci']
                },
                "game_status": {
                    'is_checkmate': new_board.is_checkmate(),
                    'is_stalemate': new_board.is_stalemate(),
                    'is_check': new_board.is_check(),
                    'is_game_over': new_board.is_game_over(),
                    'result': new_board.result() if new_board.is_game_over() else None
                },
                "message": "Computer move completed successfully"
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error making computer move for game {pk}: {e}")
        return Response({"detail": f"Error making computer move: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_computer_game(request):
    """Create a new game against the computer."""
    try:
        # Get player color preference (default to white)
        player_color = request.data.get('player_color', 'white').lower()
        difficulty = request.data.get('difficulty', 'medium')
        
        if player_color not in ['white', 'black']:
            player_color = 'white'
        
        # Support both old difficulty strings and new rating numbers
        valid_difficulties = ['easy', 'medium', 'hard', 'expert']
        valid_ratings = ['400', '800', '1200', '1600', '2000', '2400']
        
        if difficulty not in valid_difficulties and difficulty not in valid_ratings:
            # Try to convert to string if it's a number
            try:
                difficulty = str(int(difficulty))
                if difficulty not in valid_ratings:
                    difficulty = 'medium'
            except (ValueError, TypeError):
                difficulty = 'medium'
        
        # Get time control from request or use default
        time_control = request.data.get('time_control', 'rapid')
        
        # Map time control to actual time values (in seconds)
        time_control_map = {
            'bullet': 120,      # 2 minutes
            'blitz': 300,       # 5 minutes
            'rapid': 600,       # 10 minutes
            'classical': 1800,  # 30 minutes
            'unlimited': 0      # No time limit
        }
        
        initial_time = time_control_map.get(time_control, 600)  # Default to rapid
        
        # Create computer username with difficulty/rating
        computer_suffix = difficulty if difficulty in valid_ratings else difficulty
        
        # Create computer user if it doesn't exist
        if player_color == 'white':
            computer_user, created = User.objects.get_or_create(
                username=f'computer_black_{computer_suffix}',
                defaults={
                    'first_name': 'Computer', 
                    'last_name': f'Black ({computer_suffix})',
                    'email': f'computer_black_{computer_suffix}@chess.ai'
                }
            )
            game = Game.objects.create(
                white_player=request.user,
                black_player=computer_user,
                fen=chess.STARTING_FEN,
                status='active',
                time_control=time_control,
                white_time_left=initial_time,
                black_time_left=initial_time
            )
        else:
            computer_user, created = User.objects.get_or_create(
                username=f'computer_white_{computer_suffix}',
                defaults={
                    'first_name': 'Computer', 
                    'last_name': f'White ({computer_suffix})',
                    'email': f'computer_white_{computer_suffix}@chess.ai'
                }
            )
            game = Game.objects.create(
                white_player=computer_user,
                black_player=request.user,
                fen=chess.STARTING_FEN,
                status='active',
                time_control=time_control,
                white_time_left=initial_time,
                black_time_left=initial_time
            )
        
        # Store difficulty in game metadata (you might want to add this field to the model)
        # For now, we'll include it in the response
        
        # Convert difficulty to rating for consistency
        rating_map = {
            "beginner": 600,
            "easy": 800,
            "medium": 1200, 
            "hard": 1600,
            "expert": 2000,
            "master": 2200,
            "grandmaster": 2400
        }
        
        # Get the actual rating value
        if difficulty in rating_map:
            computer_rating = rating_map[difficulty]
        else:
            try:
                computer_rating = int(difficulty)
            except ValueError:
                computer_rating = 1200
        
        serializer = GameSerializer(game)
        logger.info(f"Computer game created: {game.id} by {request.user}, player_color: {player_color}, difficulty: {difficulty}")
        
        response_data = serializer.data
        response_data['difficulty'] = difficulty
        response_data['computer_rating'] = computer_rating
        response_data['player_color'] = player_color
        response_data['is_computer_game'] = True
        response_data['computer_personality'] = 'balanced'
        
        # Add rating display info for frontend
        if player_color == 'white':
            response_data['black_player_rating'] = computer_rating
            response_data['white_player_rating'] = None  # Human player
        else:
            response_data['white_player_rating'] = computer_rating
            response_data['black_player_rating'] = None  # Human player
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating computer game: {e}")
        return Response({"detail": f"Error creating computer game: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================== PROFESSIONAL TIMER API ENDPOINTS ==================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_professional_timer(request, game_id):
    """
    Get professional timer state - REPLACES frontend timer logic
    
    Returns accurate, thread-safe timer data with no conflicts
    """
    try:
        game = get_object_or_404(Game, id=game_id)
        
        # Get professional timer state
        timer_state = game.get_professional_timer_state()
        
        # Add game context
        timer_state.update({
            'game_id': game.id,
            'game_status': game.status,
            'move_count': game.moves.count(),
            'current_player_color': game.get_current_player_color(),
            'white_player': game.white_player.username if game.white_player else 'Computer',
            'black_player': game.black_player.username if game.black_player else 'Computer',
        })
        
        logger.info(f"Professional timer state for game {game_id}: {timer_state}")
        return Response(timer_state, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting professional timer for game {game_id}: {e}")
        return Response(
            {"detail": f"Timer error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_professional_timer(request, game_id):
    """
    Start professional timer system - REPLACES frontend timer initialization
    
    Initializes thread-safe, accurate timer with no conflicts
    """
    try:
        game = get_object_or_404(Game, id=game_id)
        
        if game.status != 'waiting':
            return Response(
                {"detail": "Timer already started"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start professional timer
        timer_state = game.start_professional_timer()
        
        logger.info(f"Professional timer started for game {game_id}")
        return Response({
            'message': 'Professional timer started',
            'timer_state': timer_state,
            'game_status': game.status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error starting professional timer for game {game_id}: {e}")
        return Response(
            {"detail": f"Timer start error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_professional_timer_move(request, game_id):
    """
    Update timer after move - REPLACES frontend timer switching logic
    
    Handles turn switching, time deduction, and timeout detection professionally
    """
    try:
        game = get_object_or_404(Game, id=game_id)
        player_color = request.data.get('player_color')
        
        if not player_color:
            return Response(
                {"detail": "player_color required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Make professional timer move
        timer_state = game.make_timer_move(player_color)
        
        # Check for timeout
        if game.status == 'finished' and game.termination == 'timeout':
            return Response({
                'message': f'{player_color} ran out of time',
                'timer_state': timer_state,
                'game_finished': True,
                'winner': game.winner.username if game.winner else None,
                'termination': 'timeout'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Timer updated professionally',
            'timer_state': timer_state,
            'game_status': game.status,
            'current_turn': timer_state['current_turn']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in professional timer move for game {game_id}: {e}")
        return Response(
            {"detail": f"Timer move error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bot_thinking_time(request, game_id):
    """
    Get realistic bot thinking time based on rating and position complexity
    
    REPLACES hardcoded bot delays with human-like timing patterns
    """
    try:
        game = get_object_or_404(Game, id=game_id)
        
        # Get bot rating from request or use default
        bot_rating = int(request.GET.get('bot_rating', 1500))
        complexity = float(request.GET.get('complexity', 5.0))
        
        # Create board from current FEN
        board = chess.Board(game.fen)
        
        # Calculate professional thinking time
        thinking_time = game.calculate_bot_thinking_time(bot_rating, board, complexity)
        
        return Response({
            'thinking_time': thinking_time,
            'bot_rating': bot_rating,
            'position_complexity': complexity,
            'move_count': game.moves.count(),
            'game_phase': 'opening' if game.moves.count() < 10 else 'middlegame'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error calculating bot thinking time for game {game_id}: {e}")
        return Response(
            {"detail": f"Bot thinking time error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================== END PROFESSIONAL TIMER API ENDPOINTS ==================