from django.urls import path
from . import views

urlpatterns = [
    path("", views.GameListView.as_view(), name="game-list"),                  # GET list
    path("create/", views.create_game, name="game-create"),                    # POST create
    path("create-computer/", views.create_computer_game, name="game-create-computer"), # POST create vs computer
    path("<int:pk>/", views.GameDetailView.as_view(), name="game-detail"),     # GET detail
    path("<int:pk>/join/", views.join_game, name="game-join"),                 # POST join
    path("<int:pk>/move/", views.make_move, name="game-move"),                 # POST make move
    path("<int:pk>/computer-move/", views.make_computer_move, name="game-computer-move"), # POST computer move
    path("<int:pk>/legal-moves/", views.get_legal_moves, name="game-legal-moves"),  # GET legal moves
    path("<int:pk>/timer/", views.get_game_timer, name="game-timer"),          # GET timer status
]
