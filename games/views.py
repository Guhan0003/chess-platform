import chess
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
import json
import logging

from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer

# Import chess engine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine'))
from engine import get_computer_move

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

    # Return updated game info
    game_serializer = GameSerializer(game)
    move_serializer = MoveSerializer(move_obj)
    
    response_data = {
        "move": move_serializer.data,
        "game": game_serializer.data
    }
    
    logger.info(f"Returning response: {response_data}")
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_game(request):
    """Create a new chess game with the current user as white."""
    game = Game.objects.create(
        white_player=request.user,
        fen=chess.STARTING_FEN,  # Use actual FEN, not "startpos"
        status='waiting'
    )
    serializer = GameSerializer(game)
    logger.info(f"Game created: {game.id} by {request.user}")
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
    """Get timer status for a game."""
    game = get_object_or_404(Game, pk=pk)
    
    # Must be a participant
    if request.user not in [game.white_player, game.black_player]:
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Parse FEN to get current turn
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
        
        board = chess.Board(game.fen)
        current_turn = "white" if board.turn == chess.WHITE else "black"
        
        return Response({
            "game_id": game.id,
            "white_time": game.white_time_left,
            "black_time": game.black_time_left,
            "current_turn": current_turn,
            "game_status": game.status,
            "last_move_at": game.last_move_at
        })
        
    except Exception as e:
        logger.error(f"Error getting timer for game {pk}: {e}")
        return Response({"detail": "Error getting timer data"},
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
    
    # Check if game allows computer moves (could add a field for this)
    # For now, allow if one player is None (indicating computer opponent)
    if game.white_player and game.black_player:
        return Response({"detail": "This is a human vs human game."},
                        status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Handle "startpos" FEN
        if game.fen == "startpos":
            game.fen = chess.STARTING_FEN
            game.save()
        
        board = chess.Board(game.fen)
        
        # Get difficulty from request or use default
        difficulty = request.data.get('difficulty', 'medium')
        if difficulty not in ['easy', 'medium', 'hard', 'expert']:
            difficulty = 'medium'
        
        logger.info(f"Making computer move with difficulty: {difficulty}")
        
        # Get computer move
        result = get_computer_move(game.fen, difficulty)
        
        if not result['success']:
            logger.error(f"Computer move failed: {result['error']}")
            return Response({"detail": f"Computer move failed: {result['error']}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        move_info = result['move']
        new_fen = result['new_fen']
        
        # Determine which player is the computer
        current_turn = board.turn
        computer_player = None
        if current_turn == chess.WHITE and not game.white_player:
            # White is computer, create a virtual computer user if needed
            computer_player, created = User.objects.get_or_create(
                username='computer_white',
                defaults={'first_name': 'Computer', 'last_name': 'White'}
            )
            if not game.white_player:
                game.white_player = computer_player
        elif current_turn == chess.BLACK and not game.black_player:
            # Black is computer
            computer_player, created = User.objects.get_or_create(
                username='computer_black', 
                defaults={'first_name': 'Computer', 'last_name': 'Black'}
            )
            if not game.black_player:
                game.black_player = computer_player
        else:
            return Response({"detail": "It's not the computer's turn."},
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
        
        # Return response
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
            "engine_info": result['engine_info'],
            "game_status": result['game_status']
        }
        
        logger.info(f"Computer move response: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)
        
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
        
        if difficulty not in ['easy', 'medium', 'hard', 'expert']:
            difficulty = 'medium'
        
        # Create computer user if it doesn't exist
        if player_color == 'white':
            computer_user, created = User.objects.get_or_create(
                username='computer_black',
                defaults={'first_name': 'Computer', 'last_name': 'Black'}
            )
            game = Game.objects.create(
                white_player=request.user,
                black_player=computer_user,
                fen=chess.STARTING_FEN,
                status='active'
            )
        else:
            computer_user, created = User.objects.get_or_create(
                username='computer_white',
                defaults={'first_name': 'Computer', 'last_name': 'White'}
            )
            game = Game.objects.create(
                white_player=computer_user,
                black_player=request.user,
                fen=chess.STARTING_FEN,
                status='active'
            )
        
        # Store difficulty in game metadata (you might want to add this field to the model)
        # For now, we'll include it in the response
        
        serializer = GameSerializer(game)
        logger.info(f"Computer game created: {game.id} by {request.user}, player_color: {player_color}, difficulty: {difficulty}")
        
        response_data = serializer.data
        response_data['difficulty'] = difficulty
        response_data['player_color'] = player_color
        response_data['is_computer_game'] = True
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating computer game: {e}")
        return Response({"detail": f"Error creating computer game: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)