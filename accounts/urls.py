from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints (keep existing ones)
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.RegisterView.as_view(), name='register'),  # Enhanced registration
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),  # Forgot password
    path('protected/', views.ProtectedView.as_view(), name='protected'),
    
    # Enhanced profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile'),  # Current user profile (backward compatible)
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='profile-detail'),  # Other user profile
    
    # Avatar upload endpoint
    path('avatar/upload/', views.upload_avatar, name='avatar-upload'),
    
    # Alternative enhanced profile endpoint (new enhanced version)
    path('profile/enhanced/', views.EnhancedUserProfileView.as_view(), name='profile-enhanced'),
    path('profile/enhanced/<int:pk>/', views.EnhancedUserProfileView.as_view(), name='profile-enhanced-detail'),
    
    # User statistics and data endpoints
    path('stats/', views.user_stats_summary, name='user-stats'),  # Dashboard stats
    path('search/', views.user_search, name='user-search'),  # User search
    path('leaderboard/', views.leaderboard, name='leaderboard'),  # Public leaderboards
    
    # User activity endpoints
    path('toggle-online/', views.toggle_online_status, name='toggle-online'),  # Online status
    path('game-history/', views.user_game_history, name='user-game-history'),  # Own game history
    path('game-history/<int:pk>/', views.user_game_history, name='user-game-history-detail'),  # Other user history
    
    # Skill level endpoints
    path('skill-levels/', views.get_skill_levels, name='skill-levels'),  # Get available skill levels
]

# URL Pattern Examples for Frontend Integration:
"""
GET /api/auth/profile/                     - Get own complete profile
GET /api/auth/profile/123/                 - Get user 123's public profile
PATCH /api/auth/profile/                   - Update own profile
GET /api/auth/stats/                       - Get dashboard statistics
GET /api/auth/search/?q=username&limit=10  - Search users
GET /api/auth/leaderboard/?time_control=rapid&limit=50  - Get leaderboard
POST /api/auth/toggle-online/              - Toggle online status
GET /api/auth/game-history/                - Get own game history
GET /api/auth/game-history/123/            - Get user 123's game history
"""
