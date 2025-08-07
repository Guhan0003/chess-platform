
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Game
from .serializers import GameSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Optional: Auto-assign one side to the user
        serializer.save(white_player=self.request.user)

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_game(request):
    user = request.user
    game = Game.objects.create(
        white_player=user,
        black_player=None,
        status='waiting',
        fen=STARTING_FEN
    )
    serializer = GameSerializer(game)
    return Response(serializer.data, status=status.HTTP_201_CREATED)