import chess
from django.db import transaction
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny


from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer
from django.shortcuts import render



@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])  # Make public for now

def create_game(request):
    """Create a new chess game with the current user as white."""
    game = Game.objects.create(
        white_player=request.user,
        fen=chess.STARTING_FEN,     # proper FEN
        status='waiting'
    )
    serializer = GameSerializer(game)
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
    game.status = 'active'   # <-- important: match model choices
    game.save()

    serializer = GameSerializer(game)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def make_move(request, pk):
    """Submit a move for the game using python-chess for rules/legality."""
    game = get_object_or_404(Game, pk=pk)

    # Must be a participant
    if request.user not in [game.white_player, game.black_player]:
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)

    # Load board
    try:
        board = chess.Board(game.fen)
    except Exception:
        return Response({"detail": "Corrupted game state (invalid FEN)."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Enforce turn
    expected_player = game.white_player if board.turn == chess.WHITE else game.black_player
    if expected_player != request.user:
        return Response({"detail": "It is not your turn."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Read payload
    from_sq = (request.data.get('from_square') or "").strip().lower()
    to_sq = (request.data.get('to_square') or "").strip().lower()
    promotion = request.data.get('promotion')  # optional: 'q','r','b','n'

    if not (len(from_sq) == 2 and len(to_sq) == 2):
        return Response({"detail": "from_square/to_square must be like 'e2' and 'e4'."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Build UCI, handle optional promotion
    uci = f"{from_sq}{to_sq}"
    if promotion:
        promo = str(promotion).lower()
        if promo not in ['q', 'r', 'b', 'n']:
            return Response({"detail": "Invalid promotion piece (use q/r/b/n)."},
                            status=status.HTTP_400_BAD_REQUEST)
        uci += promo

    try:
        move = chess.Move.from_uci(uci)
    except Exception:
        return Response({"detail": "Invalid move format."},
                        status=status.HTTP_400_BAD_REQUEST)

    if move not in board.legal_moves:
        # (Optional) show a few legal SAN moves to help debugging
        sample_legal = []
        for i, m in enumerate(board.legal_moves):
            if i >= 10:
                break
            sample_legal.append(board.san(m))
        return Response({
            "detail": "Illegal move for current position.",
            "hint_sample_legal_san": sample_legal
        }, status=status.HTTP_400_BAD_REQUEST)

    # Notation must be computed BEFORE pushing
    san = board.san(move)

    # Apply move
    board.push(move)
    new_fen = board.fen()

    # Prepare serializer for Move creation (keep your existing serializer)
    move_number = game.moves.count() + 1
    serializer = MoveSerializer(data={
        "from_square": from_sq,
        "to_square": to_sq,
    })

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Save Move row
    serializer.save(
        game=game,
        player=request.user,
        move_number=move_number,
        notation=san,
        fen_after_move=new_fen
    )

    # Update game state
    game.fen = new_fen

    if board.is_game_over():
        game.status = 'finished'
        result = board.result()  # '1-0', '0-1', '1/2-1/2'
        if result == '1-0':
            game.winner = game.white_player
        elif result == '0-1':
            game.winner = game.black_player
        else:
            game.winner = None
    else:
        game.status = 'active'

    game.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)



class GameListView(generics.ListAPIView):
    """List recent games."""
    queryset = Game.objects.all().order_by('-created_at')
    serializer_class = GameSerializer


class GameDetailView(generics.RetrieveAPIView):
    """Get a single game."""
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    
class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    
def game_list_page(request):
    return render(request, "games/game_list.html")