from django.urls import path
from games import views

urlpatterns = [
    path("", views.GameListView.as_view(), name="game-list"),                  # GET list
    path("create/", views.create_game, name="game-create"),                    # POST create
    path("create-computer/", views.create_computer_game, name="game-create-computer"), # POST create vs computer
    path("<int:pk>/", views.GameDetailView.as_view(), name="game-detail"),     # GET detail
    path("<int:pk>/join/", views.join_game, name="game-join"),                 # POST join
    path("<int:pk>/move/", views.make_move, name="game-move"),                 # POST make move
    path("<int:pk>/computer-move/", views.make_computer_move, name="game-computer-move"), # POST computer move
    path("<int:pk>/legal-moves/", views.get_legal_moves, name="game-legal-moves"),  # GET legal moves
    path("<int:pk>/timer/", views.get_game_timer, name="game-timer"),          # GET timer status (OLD - to be deprecated)
    
    # ================== PROFESSIONAL TIMER ENDPOINTS ==================
    path("<int:game_id>/professional-timer/", views.get_professional_timer, name="professional-timer"),
    path("<int:game_id>/start-timer/", views.start_professional_timer, name="start-professional-timer"),
    path("<int:game_id>/timer-move/", views.make_professional_timer_move, name="professional-timer-move"),
    path("<int:game_id>/bot-thinking-time/", views.get_bot_thinking_time, name="bot-thinking-time"),
    # ================== END PROFESSIONAL TIMER ENDPOINTS ==================
    
    # ================== GAME SESSION GUARD ENDPOINTS ==================
    path("active-constraints/", views.check_active_game_constraints, name="check-active-constraints"),
    path("<int:game_id>/resign/", views.resign_game, name="resign-game"),
    # ================== END GAME SESSION GUARD ENDPOINTS ==================
    
    # ================== RATING SYSTEM ENDPOINTS ==================
    path("<int:game_id>/rating-preview/", views.get_rating_preview_view, name="rating-preview"),
    # ================== END RATING SYSTEM ENDPOINTS ==================
]
