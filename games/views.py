from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Game
from .serializers import GameSerializer

class GameListCreateView(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Optional: Auto-assign one side to the user
        serializer.save(white_player=self.request.user)
