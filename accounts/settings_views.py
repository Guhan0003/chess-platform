"""
User Settings Management Views
Handles user preferences, game settings, and UI customization
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import UserSettings

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_settings(request):
    """
    Get current user's settings.
    Creates default settings if they don't exist.
    """
    user = request.user
    
    # Get or create settings
    settings, created = UserSettings.objects.get_or_create(user=user)
    
    return Response({
        'settings': {
            # Game preferences
            'auto_queen_promotion': settings.auto_queen_promotion,
            'show_coordinates': settings.show_coordinates,
            'highlight_moves': settings.highlight_moves,
            'sound_enabled': settings.sound_enabled,
            
            # Notification settings
            'email_game_invites': settings.email_game_invites,
            'email_game_results': settings.email_game_results,
            'push_notifications': settings.push_notifications,
            
            # Privacy settings
            'allow_challenges': settings.allow_challenges,
            'show_online_status': settings.show_online_status,
            
            # UI preferences
            'board_theme': settings.board_theme,
            'piece_set': settings.piece_set,
        },
        'created': created
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_settings(request):
    """
    Update user settings (partial update supported).
    Only updates fields that are provided in the request.
    """
    user = request.user
    
    # Get or create settings
    settings, created = UserSettings.objects.get_or_create(user=user)
    
    # List of allowed fields
    allowed_fields = [
        'auto_queen_promotion', 'show_coordinates', 'highlight_moves', 'sound_enabled',
        'email_game_invites', 'email_game_results', 'push_notifications',
        'allow_challenges', 'show_online_status', 'board_theme', 'piece_set'
    ]
    
    # Track updated fields
    updated_fields = []
    
    # Update provided fields
    for field in allowed_fields:
        if field in request.data:
            value = request.data[field]
            
            # Validate choice fields
            if field == 'board_theme':
                valid_themes = ['classic', 'modern', 'wood', 'marble']
                if value not in valid_themes:
                    return Response({
                        'error': f'Invalid board theme. Must be one of: {", ".join(valid_themes)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif field == 'piece_set':
                valid_pieces = ['classic', 'modern', 'staunton']
                if value not in valid_pieces:
                    return Response({
                        'error': f'Invalid piece set. Must be one of: {", ".join(valid_pieces)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate boolean fields
            elif field not in ['board_theme', 'piece_set']:
                if not isinstance(value, bool):
                    return Response({
                        'error': f'Field {field} must be a boolean value'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            setattr(settings, field, value)
            updated_fields.append(field)
    
    if updated_fields:
        settings.save()
    
    return Response({
        'message': 'Settings updated successfully',
        'updated_fields': updated_fields,
        'settings': {
            'auto_queen_promotion': settings.auto_queen_promotion,
            'show_coordinates': settings.show_coordinates,
            'highlight_moves': settings.highlight_moves,
            'sound_enabled': settings.sound_enabled,
            'email_game_invites': settings.email_game_invites,
            'email_game_results': settings.email_game_results,
            'push_notifications': settings.push_notifications,
            'allow_challenges': settings.allow_challenges,
            'show_online_status': settings.show_online_status,
            'board_theme': settings.board_theme,
            'piece_set': settings.piece_set,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_settings_to_default(request):
    """
    Reset all user settings to default values.
    """
    user = request.user
    
    try:
        # Delete existing settings (will trigger default values on next get_or_create)
        UserSettings.objects.filter(user=user).delete()
        
        # Create fresh settings with defaults
        settings = UserSettings.objects.create(user=user)
        
        return Response({
            'message': 'Settings reset to defaults successfully',
            'settings': {
                'auto_queen_promotion': settings.auto_queen_promotion,
                'show_coordinates': settings.show_coordinates,
                'highlight_moves': settings.highlight_moves,
                'sound_enabled': settings.sound_enabled,
                'email_game_invites': settings.email_game_invites,
                'email_game_results': settings.email_game_results,
                'push_notifications': settings.push_notifications,
                'allow_challenges': settings.allow_challenges,
                'show_online_status': settings.show_online_status,
                'board_theme': settings.board_theme,
                'piece_set': settings.piece_set,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to reset settings: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_themes(request):
    """
    Get available board themes and piece sets.
    """
    return Response({
        'board_themes': [
            {'value': 'classic', 'label': 'Classic', 'description': 'Traditional brown and beige'},
            {'value': 'modern', 'label': 'Modern', 'description': 'Sleek blue and white'},
            {'value': 'wood', 'label': 'Wood', 'description': 'Natural wood texture'},
            {'value': 'marble', 'label': 'Marble', 'description': 'Elegant marble finish'},
        ],
        'piece_sets': [
            {'value': 'classic', 'label': 'Classic', 'description': 'Traditional chess pieces'},
            {'value': 'modern', 'label': 'Modern', 'description': 'Contemporary design'},
            {'value': 'staunton', 'label': 'Staunton', 'description': 'Tournament standard'},
        ]
    }, status=status.HTTP_200_OK)
