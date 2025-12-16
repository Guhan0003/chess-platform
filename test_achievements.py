"""
Test script to verify achievement system
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def test_achievement_system():
    print('🧪 Testing Achievement System\n')
    
    # Test 1: Check default achievements exist
    print('Test 1: Get all achievements')
    try:
        response = requests.get(f'{BASE_URL}/api/auth/achievements/')
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Found {len(data)} achievements')
            for achievement in data[:3]:  # Show first 3
                print(f'   - {achievement["name"]} ({achievement["points"]} pts) - {achievement["category"]}')
        else:
            print(f'❌ Error: {response.status_code}')
    except Exception as e:
        print(f'❌ Exception: {e}')
    
    print()
    
    # Test 2: Login and get user achievements
    print('Test 2: Login and get user achievements')
    try:
        # Try to login (replace with actual credentials)
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data)
        
        if response.status_code == 200:
            tokens = response.json()
            headers = {'Authorization': f'Bearer {tokens["access"]}'}
            
            print('✅ Login successful')
            
            # Get user achievements
            response = requests.get(f'{BASE_URL}/api/auth/achievements/user/', headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f'✅ User has {len(data["unlocked"])} unlocked achievements')
                print(f'   Locked: {len(data["locked"])}')
                print(f'   Total Points: {data["total_points"]}')
            else:
                print(f'❌ Error getting user achievements: {response.status_code}')
        else:
            print(f'⚠️ Login failed (expected if no test user): {response.status_code}')
            print('   Create a test user first: python manage.py createsuperuser')
    except Exception as e:
        print(f'❌ Exception: {e}')
    
    print('\n✅ Achievement system tests complete!')

if __name__ == '__main__':
    test_achievement_system()
