from django.urls import path
from . import views
from .views import GameListCreateView

urlpatterns = [
    path('games/', GameListCreateView.as_view(), name='game-list-create'),
    path('create/', views.create_game, name='create-game'),

]
