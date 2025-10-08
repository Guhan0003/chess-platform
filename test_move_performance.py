#!/usr/bin/env python
"""
Performance test script for move synchronization optimization.
Tests the move response time to ensure it's under 3 seconds.
"""

import os
import sys
import django
import time
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from games.models import Game
from django.test import Client

User = get_user_model()

class MovePerformanceTester:
    def __init__(self):
        self.client = Client()
        self.base_url = "http://127.0.0.1:8000/api"
        self.access_token = None
        
    def setup_test_users(self):
        """Create test users for the performance test."""
        # Create test users if they don't exist
        try:
            user1 = User.objects.get(username='testuser1')
        except User.DoesNotExist:
            user1 = User.objects.create_user(
                username='testuser1',
                email='test1@example.com',
                password='testpass123'
            )
            
        try:
            user2 = User.objects.get(username='testuser2')
        except User.DoesNotExist:
            user2 = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='testpass123'
            )
            
        return user1, user2
    
    def login_user(self, username, password):
        """Login and get access token."""
        response = requests.post(f"{self.base_url}/auth/login/", json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            return True
        return False
    
    def create_test_game(self):
        """Create a new game for testing."""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.post(f"{self.base_url}/games/create/", headers=headers)
        
        if response.status_code == 201:
            return response.json()['id']
        return None
    
    def make_test_move(self, game_id, from_square, to_square):
        """Make a move and measure response time."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'from_square': from_square,
            'to_square': to_square
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/games/{game_id}/move/",
            headers=headers,
            json=payload
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        return {
            'success': response.status_code == 200,
            'response_time': response_time,
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else None
        }
    
    def test_move_performance(self):
        """Run the complete performance test."""
        print("🚀 Starting Move Performance Test")
        print("=" * 50)
        
        # Setup
        self.setup_test_users()
        
        # Login
        if not self.login_user('testuser1', 'testpass123'):
            print("❌ Login failed")
            return False
        
        print("✅ User logged in successfully")
        
        # Create game
        game_id = self.create_test_game()
        if not game_id:
            print("❌ Game creation failed")
            return False
        
        print(f"✅ Game created with ID: {game_id}")
        
        # Test moves with timing
        test_moves = [
            ('e2', 'e4'),
            ('e7', 'e5'),
            ('g1', 'f3'),
            ('b8', 'c6'),
            ('f1', 'c4')
        ]
        
        total_time = 0
        successful_moves = 0
        
        print("\n📊 Testing move response times:")
        print("-" * 40)
        
        for i, (from_sq, to_sq) in enumerate(test_moves, 1):
            result = self.make_test_move(game_id, from_sq, to_sq)
            
            if result['success']:
                print(f"Move {i}: {from_sq}→{to_sq} | ⏱️  {result['response_time']:.3f}s | ✅")
                total_time += result['response_time']
                successful_moves += 1
            else:
                print(f"Move {i}: {from_sq}→{to_sq} | ❌ Failed (Status: {result['status_code']})")
                break
        
        if successful_moves > 0:
            avg_response_time = total_time / successful_moves
            print("\n" + "=" * 50)
            print("📈 PERFORMANCE RESULTS:")
            print(f"Total moves tested: {successful_moves}")
            print(f"Average response time: {avg_response_time:.3f} seconds")
            print(f"Target: < 3.0 seconds")
            
            if avg_response_time < 3.0:
                print("🎉 SUCCESS: Response time is under 3 seconds!")
                if avg_response_time < 2.0:
                    print("⚡ EXCELLENT: Response time is under 2 seconds!")
                return True
            else:
                print("⚠️  WARNING: Response time exceeds 3 seconds")
                return False
        else:
            print("❌ No successful moves to analyze")
            return False

def main():
    """Run the performance test."""
    print(f"🔧 Chess Platform Move Performance Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = MovePerformanceTester()
    success = tester.test_move_performance()
    
    print("\n" + "=" * 50)
    if success:
        print("🏆 PERFORMANCE TEST PASSED!")
        print("The optimizations have successfully reduced move response time to <3 seconds.")
    else:
        print("🚨 PERFORMANCE TEST FAILED!")
        print("Additional optimizations may be needed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)