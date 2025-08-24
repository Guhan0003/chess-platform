from django.urls import path
from . import views

urlpatterns = [
    path("", views.GameListView.as_view(), name="game-list"),                  # GET list
    path("create/", views.create_game, name="game-create"),                    # POST create
    path("<int:pk>/", views.GameDetailView.as_view(), name="game-detail"),     # GET detail
    path("<int:pk>/join/", views.join_game, name="game-join"),                 # POST join
    path("<int:pk>/move/", views.make_move, name="game-move"),                 # POST make move
]
