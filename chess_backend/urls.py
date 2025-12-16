# chess_backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
import os
from accounts.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def serve_frontend_static(request, path=""):
    """Custom view to serve frontend static files"""
    file_path = os.path.join(settings.BASE_DIR, 'frontend', path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        raise Http404("File not found")

def serve_professional_frontend(request, page_path=""):
    """Serve professional frontend pages"""
    # Map routes to actual files
    route_map = {
        '': 'src/pages/auth/login.html',  # Root goes to login
        'login': 'src/pages/auth/login.html',
        'register': 'src/pages/auth/register.html',
        'lobby': 'src/pages/dashboard/lobby.html',
        'play': 'src/pages/game/play.html',
        'forgot-password': 'src/pages/auth/forgot-password.html',
        'profile': 'src/pages/profile/profile.html',
        'settings': 'src/pages/settings/settings.html',
        'puzzles': 'src/pages/puzzles/puzzles.html'
    }
    
    # Get the file path
    file_relative_path = route_map.get(page_path, 'src/pages/auth/login.html')
    file_path = os.path.join(settings.BASE_DIR, 'frontend', file_relative_path)
    
    print(f"🔍 Trying to serve: {page_path} -> {file_path}")
    print(f"📁 File exists: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        # Default to login page if route not found
        login_path = os.path.join(settings.BASE_DIR, 'frontend', 'src/pages/auth/login.html')
        return FileResponse(open(login_path, 'rb'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/games/', include('games.urls')),

    # Serve frontend static files (CSS, JS, images) - Fix paths for professional frontend
    path('styles/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/styles/{filename}')),
    path('utils/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/utils/{filename}')),
    path('assets/<path:path>', lambda request, path: serve_frontend_static(request, f'src/assets/{path}')),
    path('src/styles/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/styles/{filename}')),
    path('src/utils/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/utils/{filename}')),
    path('src/assets/<path:path>', lambda request, path: serve_frontend_static(request, f'src/assets/{path}')),
    
    # Game page specific files
    path('play/play.css', lambda request: serve_frontend_static(request, 'src/pages/game/play.css')),
    path('play/play.js', lambda request: serve_frontend_static(request, 'src/pages/game/play.js')),
    path('src/pages/game/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/pages/game/{filename}')),
    
    # Professional frontend pages
    path('login/', serve_professional_frontend, {'page_path': 'login'}, name='login'),
    path('register/', serve_professional_frontend, {'page_path': 'register'}, name='register'),
    path('lobby/', serve_professional_frontend, {'page_path': 'lobby'}, name='lobby'),
    path('play/', serve_professional_frontend, {'page_path': 'play'}, name='play'),
    path('game/<int:game_id>/', serve_professional_frontend, {'page_path': 'play'}, name='game_detail'),
    path('forgot-password/', serve_professional_frontend, {'page_path': 'forgot-password'}, name='forgot-password'),
    path('profile/', serve_professional_frontend, {'page_path': 'profile'}, name='profile'),
    path('settings/', serve_professional_frontend, {'page_path': 'settings'}, name='settings'),
    path('puzzles/', serve_professional_frontend, {'page_path': 'puzzles'}, name='puzzles'),
    
    # Settings page resources
    path('settings/settings.js', lambda request: serve_frontend_static(request, 'src/pages/settings/settings.js')),
    path('src/pages/settings/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/pages/settings/{filename}')),
    
    # Profile page resources
    path('profile/profile.js', lambda request: serve_frontend_static(request, 'src/pages/profile/profile.js')),
    path('src/pages/profile/<str:filename>', lambda request, filename: serve_frontend_static(request, f'src/pages/profile/{filename}')),
    
    # Test WebSocket connection
    path('test_websocket_connection.html', lambda request: serve_frontend_static(request, '../test_websocket_connection.html')),
    
    # Root serves login page
    path('', serve_professional_frontend, name='home'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
