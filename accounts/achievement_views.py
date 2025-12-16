"""
Achievement System API Views
Handles user achievements, unlocking, and progress tracking
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from accounts.models import Achievement, UserAchievement
from django.db.models import Count, Q
from django.utils import timezone

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_achievements(request):
    """
    Get all achievements for the current user.
    Returns both unlocked and locked achievements.
    """
    user = request.user
    
    # Get all achievements
    all_achievements = Achievement.objects.filter(is_active=True).order_by('category', 'points')
    
    # Get user's unlocked achievements
    unlocked_achievement_ids = UserAchievement.objects.filter(
        user=user
    ).values_list('achievement_id', flat=True)
    
    # Build response
    achievements_data = []
    for achievement in all_achievements:
        is_unlocked = achievement.id in unlocked_achievement_ids
        unlock_date = None
        
        if is_unlocked:
            user_achievement = UserAchievement.objects.get(user=user, achievement=achievement)
            unlock_date = user_achievement.unlocked_at.isoformat()
        
        achievements_data.append({
            'id': achievement.id,
            'key': achievement.key if hasattr(achievement, 'key') else achievement.name.lower().replace(' ', '_'),
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'category': achievement.category,
            'points': achievement.points,
            'unlocked': is_unlocked,
            'unlocked_at': unlock_date,
            'requirement': achievement.requirement
        })
    
    # Calculate stats
    total_achievements = len(achievements_data)
    unlocked_count = len(unlocked_achievement_ids)
    total_points = sum(ach['points'] for ach in achievements_data if ach['unlocked'])
    
    return Response({
        'achievements': achievements_data,
        'stats': {
            'total': total_achievements,
            'unlocked': unlocked_count,
            'locked': total_achievements - unlocked_count,
            'total_points': total_points,
            'completion_percentage': round((unlocked_count / total_achievements * 100), 1) if total_achievements > 0 else 0
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_achievements(request, user_id):
    """
    Get achievements for a specific user (public view).
    Only shows unlocked achievements.
    """
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if profile is public
    if not target_user.profile_public and request.user != target_user:
        return Response({
            'error': 'This profile is private'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get user's unlocked achievements
    user_achievements = UserAchievement.objects.filter(
        user=target_user
    ).select_related('achievement').order_by('-unlocked_at')
    
    achievements_data = []
    total_points = 0
    
    for user_achievement in user_achievements:
        achievement = user_achievement.achievement
        achievements_data.append({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'category': achievement.category,
            'points': achievement.points,
            'unlocked_at': user_achievement.unlocked_at.isoformat()
        })
        total_points += achievement.points
    
    return Response({
        'username': target_user.username,
        'achievements': achievements_data,
        'stats': {
            'total_unlocked': len(achievements_data),
            'total_points': total_points
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_and_unlock_achievements(request):
    """
    Check user's stats and unlock any newly earned achievements.
    This should be called after significant events (game completion, rating change, etc.)
    """
    user = request.user
    newly_unlocked = []
    
    # Get all active achievements
    all_achievements = Achievement.objects.filter(is_active=True)
    
    # Get already unlocked achievement IDs
    unlocked_ids = set(UserAchievement.objects.filter(
        user=user
    ).values_list('achievement_id', flat=True))
    
    # Check each achievement
    for achievement in all_achievements:
        if achievement.id in unlocked_ids:
            continue  # Already unlocked
        
        # Check if user meets requirement
        if check_achievement_requirement(user, achievement):
            # Unlock the achievement
            UserAchievement.objects.create(
                user=user,
                achievement=achievement
            )
            newly_unlocked.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'category': achievement.category
            })
    
    return Response({
        'newly_unlocked': newly_unlocked,
        'count': len(newly_unlocked)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_achievement_progress(request):
    """
    Get user's progress toward locked achievements.
    Shows how close they are to unlocking each achievement.
    """
    user = request.user
    
    # Get locked achievements
    unlocked_ids = UserAchievement.objects.filter(
        user=user
    ).values_list('achievement_id', flat=True)
    
    locked_achievements = Achievement.objects.filter(
        is_active=True
    ).exclude(id__in=unlocked_ids)
    
    progress_data = []
    
    for achievement in locked_achievements:
        progress = calculate_achievement_progress(user, achievement)
        if progress:
            progress_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'category': achievement.category,
                'points': achievement.points,
                'progress': progress['current'],
                'required': progress['required'],
                'percentage': round((progress['current'] / progress['required'] * 100), 1) if progress['required'] > 0 else 0
            })
    
    # Sort by closest to completion
    progress_data.sort(key=lambda x: x['percentage'], reverse=True)
    
    return Response({
        'progress': progress_data
    }, status=status.HTTP_200_OK)


def check_achievement_requirement(user, achievement):
    """
    Check if user meets the requirement for an achievement.
    Returns True if requirement is met, False otherwise.
    """
    requirement = achievement.requirement
    
    # Handle different requirement types
    if 'games_won' in requirement:
        return user.games_won >= requirement['games_won']
    
    if 'total_games' in requirement:
        return user.total_games >= requirement['total_games']
    
    if 'rating' in requirement:
        # Check highest rating across all time controls
        highest_rating = max(user.blitz_rating, user.rapid_rating, user.classical_rating)
        return highest_rating >= requirement['rating']
    
    if 'rapid_rating' in requirement:
        return user.rapid_rating >= requirement['rapid_rating']
    
    if 'blitz_rating' in requirement:
        return user.blitz_rating >= requirement['blitz_rating']
    
    if 'classical_rating' in requirement:
        return user.classical_rating >= requirement['classical_rating']
    
    if 'win_streak' in requirement:
        return user.current_win_streak >= requirement['win_streak']
    
    if 'blitz_games' in requirement:
        return user.blitz_games >= requirement['blitz_games']
    
    if 'rapid_games' in requirement:
        return user.rapid_games >= requirement['rapid_games']
    
    if 'classical_games' in requirement:
        return user.classical_games >= requirement['classical_games']
    
    if 'puzzles_solved' in requirement:
        return user.puzzles_solved >= requirement['puzzles_solved']
    
    return False


def calculate_achievement_progress(user, achievement):
    """
    Calculate user's progress toward an achievement.
    Returns dict with current and required values.
    """
    requirement = achievement.requirement
    
    if 'games_won' in requirement:
        return {'current': user.games_won, 'required': requirement['games_won']}
    
    if 'total_games' in requirement:
        return {'current': user.total_games, 'required': requirement['total_games']}
    
    if 'rating' in requirement:
        highest_rating = max(user.blitz_rating, user.rapid_rating, user.classical_rating)
        return {'current': highest_rating, 'required': requirement['rating']}
    
    if 'rapid_rating' in requirement:
        return {'current': user.rapid_rating, 'required': requirement['rapid_rating']}
    
    if 'blitz_rating' in requirement:
        return {'current': user.blitz_rating, 'required': requirement['blitz_rating']}
    
    if 'classical_rating' in requirement:
        return {'current': user.classical_rating, 'required': requirement['classical_rating']}
    
    if 'win_streak' in requirement:
        return {'current': user.current_win_streak, 'required': requirement['win_streak']}
    
    if 'blitz_games' in requirement:
        return {'current': user.blitz_games, 'required': requirement['blitz_games']}
    
    if 'rapid_games' in requirement:
        return {'current': user.rapid_games, 'required': requirement['rapid_games']}
    
    if 'classical_games' in requirement:
        return {'current': user.classical_games, 'required': requirement['classical_games']}
    
    if 'puzzles_solved' in requirement:
        return {'current': user.puzzles_solved, 'required': requirement['puzzles_solved']}
    
    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_default_achievements(request):
    """
    Admin endpoint to create default achievements in the database.
    Only for development/setup purposes.
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Admin privileges required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from games.models import ChessManager
    
    count = ChessManager.create_default_achievements()
    
    return Response({
        'message': f'Created {count} default achievements',
        'count': count
    }, status=status.HTTP_200_OK)
