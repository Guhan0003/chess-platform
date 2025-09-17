#!/usr/bin/env python
"""
Test script for computer move functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_backend.settings')
django.setup()

from games.models import Game
from games.views import make_computer_move
from accounts.models import CustomUser
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_computer_move():
    try:
        # Get the game
        game = Game.objects.get(id=77)
        print(f"Testing game {game.id}")
        print(f"Status: {game.status}")
        print(f"FEN: {game.fen}")
        print(f"White: {game.white_player}")
        print(f"Black: {game.black_player}")
        
        # Create a test user for authentication
        user = CustomUser.objects.get(username='testuser2')
        
        # Create a mock request
        factory = APIRequestFactory()
        request = factory.post(f'/api/games/{game.id}/computer-move/')
        request.user = user
        django_request = Request(request)
        
        # Call the view function directly
        print("\nCalling make_computer_move...")
        result = make_computer_move(django_request, pk=game.id)
        
        print(f"Result status: {result.status_code}")
        print(f"Result data: {result.data}")
        
        # Check game state after move
        game.refresh_from_db()
        print(f"\nAfter move:")
        print(f"FEN: {game.fen}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_computer_move()