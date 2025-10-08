"""
ASGI config for chess_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_backend.settings')

# Initialize Django early to ensure the AppRegistry is populated
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import games.routing

# Get the Django ASGI application early
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        games.routing.websocket_urlpatterns
    ),
})
