"""
WebSocket URL routing for chess game real-time communication.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Game WebSocket for real-time gameplay
    re_path(r'ws/game/(?P<game_id>\d+)/$', consumers.GameConsumer.as_asgi()),
    
    # Timer WebSocket for precise timer synchronization
    re_path(r'ws/timer/(?P<game_id>\d+)/$', consumers.TimerConsumer.as_asgi()),
]