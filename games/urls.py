from django.urls import path
from games import views
from games import puzzle_views

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
    
    # ================== PUZZLE SYSTEM ENDPOINTS ==================
    path("puzzles/random/", puzzle_views.get_random_puzzle, name="puzzle-random"),
    path("puzzles/stats/", puzzle_views.get_user_puzzle_stats, name="puzzle-stats"),
    path("puzzles/initialize/", puzzle_views.initialize_sample_puzzles, name="puzzle-initialize"),
    path("puzzles/<int:puzzle_id>/", puzzle_views.get_puzzle_by_id, name="puzzle-detail"),
    path("puzzles/<int:puzzle_id>/validate/", puzzle_views.validate_puzzle_move, name="puzzle-validate"),
    path("puzzles/<int:puzzle_id>/complete/", puzzle_views.complete_puzzle, name="puzzle-complete"),
    path("puzzles/<int:puzzle_id>/hint/", puzzle_views.get_puzzle_hint, name="puzzle-hint"),
    path("puzzles/<int:puzzle_id>/solution/", puzzle_views.get_puzzle_solution, name="puzzle-solution"),
    # ================== END PUZZLE SYSTEM ENDPOINTS ==================
]
