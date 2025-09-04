import chess
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import logging

from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer

# Add logging
logger = logging.getLogger(__name__)

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