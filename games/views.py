from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Game, Move
from .serializers import GameSerializer, MoveSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_game(request):
    """Create a new chess game with the current user as white."""
    game = Game.objects.create(white_player=request.user)
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
    game.status = 'in_progress'
    game.save()

    serializer = GameSerializer(game)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_move(request, pk):
    """Submit a move for the game."""
    game = get_object_or_404(Game, pk=pk)

    if request.user not in [game.white_player, game.black_player]:
        return Response({"detail": "You are not a player in this game."},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = MoveSerializer(data=request.data)
    if serializer.is_valid():
        move_number = game.moves.count() + 1
        serializer.save(game=game, player=request.user, move_number=move_number)

        # Optionally update FEN or status here

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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