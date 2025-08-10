from django.urls import path
from . import views
from .views import GameListCreateView

urlpatterns = [
    path('games/', GameListCreateView.as_view(), name='game-list-create'),
    path('create/', views.create_game, name='create-game'),
    path('<int:pk>/join/', views.join_game, name='join-game'),
    path('<int:pk>/move/', views.make_move, name='make-move'),
    path('<int:pk>/', views.GameDetailView.as_view(), name='game-detail'),
    path('', views.GameListView.as_view(), name='game-list'),
]
