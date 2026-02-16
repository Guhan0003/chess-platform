"""
WebSocket URL routing for accounts/friends functionality.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Friends WebSocket for real-time status and notifications
    re_path(r'ws/friends/$', consumers.FriendsConsumer.as_asgi()),
]
