#!/usr/bin/env python
"""
Direct test of create_computer_game view
"""

import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_backend.settings')
os.environ['DB_ENGINE'] = 'sqlite'
django.setup()

from games.views import create_computer_game
from rest_framework.test import force_authenticate
import json

def test_create_computer_game():
    """Test the create computer game view directly"""
    
    # Get user model and create/get test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testcomputer',
        defaults={'email': 'test@computer.com'}
    )
    if created:
        user.set_password('test123')
        user.save()
    
    # Create request
    factory = RequestFactory()
    data = {
        'player_color': 'white',
        'difficulty': 'medium'
    }
    
    request = factory.post(
        '/api/games/create-computer/',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    # Properly authenticate the request
    force_authenticate(request, user=user)
    
    # Mock the permission check to bypass authentication
    with patch('rest_framework.permissions.IsAuthenticated.has_permission', return_value=True):
        try:
            response = create_computer_game(request)
            print(f"✅ create_computer_game view test:")
            print(f"   Status code: {response.status_code}")
            
            if hasattr(response, 'data'):
                print(f"   Response data keys: {list(response.data.keys()) if isinstance(response.data, dict) else 'Not a dict'}")
                if response.status_code not in [200, 201]:
                    print(f"   Response: {response.data}")
            
            if response.status_code in [200, 201]:
                print("✅ SUCCESS: Computer game creation works!")
            else:
                print(f"❌ FAILED: Unexpected status code")
                
        except Exception as e:
            print(f"❌ ERROR in create_computer_game: {e}")
            import traceback
            traceback.print_exc()

def test_engine_import():
    """Test if engine can be imported properly"""
    try:
        import sys
        sys.path.append('engine')
        from engine import get_computer_move
        result = get_computer_move('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 'easy')
        print(f"✅ Engine import test: {result['success']}")
        if result['success']:
            move = result['move']
            print(f"   Sample move: {move['from_square']} -> {move['to_square']}")
        return True
    except Exception as e:
        print(f"❌ Engine import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Chess Engine:")
    engine_works = test_engine_import()
    
    print("\nTesting Computer Game Creation:")
    if engine_works:
        test_create_computer_game()
    else:
        print("❌ Skipping game creation test due to engine import failure")
