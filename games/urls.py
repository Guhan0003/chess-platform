from django.urls import path
from .views import GameListCreateView

urlpatterns = [
    path('games/', GameListCreateView.as_view(), name='game-list-create'),
]
