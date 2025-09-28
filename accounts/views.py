from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveUpdateAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image


class ForgotPasswordView(APIView):
    """
    Forgot password endpoint for sending password reset emails.
    This is a basic implementation - in production, you'd want to integrate
    with Django's built-in password reset system and email backend.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # In a real implementation, you would:
                # 1. Generate a password reset token
                # 2. Send an email with reset link
                # 3. Store the token with expiration
                
                # For now, we'll just return success
                # You can integrate Django's built-in password reset system here
                pass
            
            # Always return success to prevent email enumeration attacks
            return Response({
                'message': 'If an account with this email exists, you will receive a password reset link shortly.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'An error occurred while processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
import os
import uuid
from .serializers import (
    RegisterSerializer, UserProfileSerializer, UserPublicSerializer,
    UserGameSerializer, UserUpdateSerializer, UserStatsSerializer,
    get_user_serializer
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Hello, {request.user.username}! You're authenticated."})

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get comprehensive user profile with chess-specific data"""
        user = request.user
        
        # Get user settings if they exist
        try:
            settings = user.settings
            settings_data = {
                'auto_queen_promotion': settings.auto_queen_promotion,
                'show_coordinates': settings.show_coordinates,
                'highlight_moves': settings.highlight_moves,
                'sound_enabled': settings.sound_enabled,
                'board_theme': settings.board_theme,
                'piece_set': settings.piece_set,
                'email_game_invites': settings.email_game_invites,
                'push_notifications': settings.push_notifications,
            }
        except:
            settings_data = None
        
        # Get recent achievements
        recent_achievements = []
        try:
            user_achievements = user.achievements.all()[:5]
            recent_achievements = [
                {
                    'name': ua.achievement.name,
                    'description': ua.achievement.description,
                    'icon': ua.achievement.icon,
                    'category': ua.achievement.category,
                    'earned_at': ua.earned_at
                }
                for ua in user_achievements
            ]
        except:
            pass
        
        return Response({
            # Basic user data
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
            
            # Chess-specific profile data
            "bio": user.bio,
            "country": user.country,
            "avatar": user.avatar.url if user.avatar else None,
            "is_online": user.is_online,
            "last_activity": user.last_activity,
            "preferred_time_control": user.preferred_time_control,
            "profile_public": user.profile_public,
            "show_rating": user.show_rating,
            
            # Rating data
            "blitz_rating": user.blitz_rating,
            "rapid_rating": user.rapid_rating,
            "classical_rating": user.classical_rating,
            "blitz_peak": user.blitz_peak,
            "rapid_peak": user.rapid_peak,
            "classical_peak": user.classical_peak,
            
            # Game statistics
            "total_games": user.total_games,
            "games_won": user.games_won,
            "games_lost": user.games_lost,
            "games_drawn": user.games_drawn,
            "blitz_games": user.blitz_games,
            "rapid_games": user.rapid_games,
            "classical_games": user.classical_games,
            "current_win_streak": user.current_win_streak,
            "best_win_streak": user.best_win_streak,
            "puzzles_solved": user.puzzles_solved,
            "win_rate": user.get_win_rate(),
            
            # Additional data
            "settings": settings_data,
            "recent_achievements": recent_achievements,
        })
    
    def patch(self, request):
        """Update user profile data"""
        user = request.user
        data = request.data
        
        # Update basic profile fields
        updatable_fields = [
            'first_name', 'last_name', 'bio', 'country', 
            'preferred_time_control', 'profile_public', 'show_rating'
        ]
        
        updated_fields = []
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.save()
        
        # Update settings if provided
        settings_data = data.get('settings', {})
        if settings_data:
            from .models import UserSettings
            settings, created = UserSettings.objects.get_or_create(user=user)
            
            settings_fields = [
                'auto_queen_promotion', 'show_coordinates', 'highlight_moves', 
                'sound_enabled', 'board_theme', 'piece_set',
                'email_game_invites', 'push_notifications'
            ]
            
            settings_updated = []
            for field in settings_fields:
                if field in settings_data:
                    setattr(settings, field, settings_data[field])
                    settings_updated.append(field)
            
            if settings_updated:
                settings.save()
                updated_fields.extend([f'settings.{f}' for f in settings_updated])
        
        return Response({
            'message': 'Profile updated successfully',
            'updated_fields': updated_fields
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)


# Enhanced Registration View
class EnhancedRegisterView(APIView):
    """Enhanced registration endpoint with better validation"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnhancedUserProfileView(RetrieveUpdateAPIView):
    """
    Enhanced user profile management with context-aware serialization
    GET: Retrieve user profile (own profile gets full data, others get public data)
    PATCH: Update user profile (own profile only)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get user object - defaults to current user if no pk provided"""
        pk = self.kwargs.get('pk')
        if pk:
            return get_object_or_404(User, pk=pk)
        return self.request.user

    def get_serializer_class(self):
        """Return appropriate serializer based on context"""
        target_user = self.get_object()
        
        if self.request.method == 'PATCH':
            # Only allow updating own profile
            if self.request.user != target_user:
                return None  # This will trigger permission denied
            return UserUpdateSerializer
        
        # For GET requests, use context-aware serializer
        return get_user_serializer(self.request, target_user)

    def get_serializer_context(self):
        """Add request context for URL building"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def patch(self, request, *args, **kwargs):
        """Update user profile with enhanced validation"""
        target_user = self.get_object()
        
        # Ensure user can only update their own profile
        if request.user != target_user:
            return Response(
                {'error': 'You can only update your own profile'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserUpdateSerializer(
            target_user, 
            data=request.data, 
            partial=True,
            context=self.get_serializer_context()
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Return updated profile data
            profile_serializer = UserProfileSerializer(
                user, 
                context=self.get_serializer_context()
            )
            
            return Response({
                'message': 'Profile updated successfully',
                'updated_fields': list(serializer.validated_data.keys()),
                'profile': profile_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_search(request):
    """
    Search for users by username
    Query parameters:
    - q: search query (username)
    - limit: number of results (default 10, max 50)
    """
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 10)), 50)
    
    if len(query) < 2:
        return Response({
            'error': 'Search query must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Search users by username (case-insensitive, starts with)
    users = User.objects.filter(
        username__icontains=query
    ).exclude(
        id=request.user.id  # Exclude current user
    )[:limit]
    
    # Use game serializer for search results (minimal data)
    serializer = UserGameSerializer(
        users, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'query': query,
        'results': serializer.data,
        'total_found': len(serializer.data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_summary(request):
    """Get current user's statistics summary for dashboard"""
    user = request.user
    
    # Calculate additional stats
    total_rating_points = user.blitz_rating + user.rapid_rating + user.classical_rating
    avg_rating = round(total_rating_points / 3, 1)
    
    # Recent activity (placeholder - will be enhanced in Task 4)
    recent_games_count = 0  # TODO: Calculate from actual recent games
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'total_games': user.total_games,
        'win_rate': round((user.games_won / user.total_games * 100), 1) if user.total_games > 0 else 0,
        'current_streak': user.current_win_streak,
        'best_streak': user.best_win_streak,
        'average_rating': avg_rating,
        'preferred_time_control': user.preferred_time_control,
        'recent_games_week': recent_games_count,
        'puzzles_solved': user.puzzles_solved,
        'member_since': user.date_joined.strftime('%B %Y'),
        'is_online': user.is_online
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint for leaderboards
def leaderboard(request):
    """
    Get leaderboard data
    Query parameters:
    - time_control: 'blitz', 'rapid', or 'classical' (default: rapid)
    - limit: number of results (default 50, max 100)
    - min_games: minimum games played (default 10)
    """
    time_control = request.GET.get('time_control', 'rapid')
    limit = min(int(request.GET.get('limit', 50)), 100)
    min_games = int(request.GET.get('min_games', 10))
    
    # Validate time control
    if time_control not in ['blitz', 'rapid', 'classical']:
        return Response({
            'error': 'Invalid time control. Must be blitz, rapid, or classical'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get rating field name
    rating_field = f'{time_control}_rating'
    games_field = f'{time_control}_games'
    
    # Query users with minimum games and order by rating
    users = User.objects.filter(
        **{f'{games_field}__gte': min_games},
        profile_public=True  # Only include users with public profiles
    ).order_by(f'-{rating_field}')[:limit]
    
    # Serialize with stats serializer
    serializer = UserStatsSerializer(
        users, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'time_control': time_control,
        'min_games': min_games,
        'leaderboard': serializer.data,
        'total_players': len(serializer.data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_game_history(request, pk=None):
    """
    Get user's recent games (placeholder for Task 2 enhancement)
    This will be enhanced when we improve the Game API endpoints
    """
    target_user = get_object_or_404(User, pk=pk) if pk else request.user
    
    # Privacy check
    if target_user != request.user and not target_user.profile_public:
        return Response({
            'error': 'This user\'s profile is private'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # TODO: Implement actual game history query in Task 2
    # For now, return user stats
    serializer_class = get_user_serializer(request, target_user)
    serializer = serializer_class(target_user, context={'request': request})
    
    return Response({
        'user': serializer.data,
        'recent_games': [],  # TODO: Implement in Task 2
        'message': 'Game history will be available after Task 2 implementation'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_online_status(request):
    """Toggle user online status"""
    user = request.user
    new_status = not user.is_online
    user.is_online = new_status
    user.save(update_fields=['is_online', 'last_activity'])
    
    return Response({
        'is_online': new_status,
        'message': f'Status changed to {"online" if new_status else "offline"}'
    })


# Enhanced version of your existing UserProfileView
class AlternativeUserProfileView(APIView):
    """
    Enhanced version that can replace your existing UserProfileView
    Maintains backward compatibility while adding new features
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """Get comprehensive user profile with chess-specific data"""
        target_user = get_object_or_404(User, pk=pk) if pk else request.user
        
        # Use context-aware serializer
        serializer_class = get_user_serializer(request, target_user)
        serializer = serializer_class(target_user, context={'request': request})
        
        return Response(serializer.data)
    
    def patch(self, request, pk=None):
        """Update user profile data (enhanced version of your existing logic)"""
        target_user = get_object_or_404(User, pk=pk) if pk else request.user
        
        # Ensure user can only update their own profile
        if request.user != target_user:
            return Response({
                'error': 'You can only update your own profile'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Use the update serializer for validation
        serializer = UserUpdateSerializer(
            target_user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Return full profile data after update
            profile_serializer = UserProfileSerializer(user, context={'request': request})
            
            return Response({
                'message': 'Profile updated successfully',
                'updated_fields': list(serializer.validated_data.keys()),
                'profile': profile_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    """
    Upload user avatar with proper validation and processing
    """
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request FILES: {request.FILES}")
    print(f"Request data: {request.data}")
    
    if 'avatar' not in request.FILES:
        return Response({
            'error': 'No avatar file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    avatar_file = request.FILES['avatar']
    user = request.user
    
    # Validate file size (max 5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response({
            'error': 'File size too large. Maximum size is 5MB.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if avatar_file.content_type not in allowed_types:
        return Response({
            'error': 'Invalid file type. Only JPEG, PNG and GIF files are allowed.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Delete old avatar if exists
        if user.avatar:
            if default_storage.exists(user.avatar.name):
                default_storage.delete(user.avatar.name)
        
        # Generate unique filename
        file_extension = avatar_file.name.split('.')[-1].lower()
        new_filename = f"avatars/user_{user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Save the new avatar
        saved_path = default_storage.save(new_filename, avatar_file)
        user.avatar = saved_path
        user.save()
        
        # Return updated profile data
        avatar_url = user.avatar.url if user.avatar else None
        if avatar_url and hasattr(request, 'build_absolute_uri'):
            avatar_url = request.build_absolute_uri(avatar_url)
        
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': avatar_url
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to upload avatar: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar(request):
    """
    Delete user's current avatar
    """
    user = request.user
    
    if not user.avatar:
        return Response({
            'error': 'No avatar to delete'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Delete the avatar file
        if default_storage.exists(user.avatar.name):
            default_storage.delete(user.avatar.name)
        
        # Clear avatar field
        user.avatar = None
        user.save()
        
        return Response({
            'message': 'Avatar deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to delete avatar: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_skill_levels(request):
    """
    Get available skill levels for registration
    """
    try:
        from games.utils.rating_calculator import SkillLevelManager
        
        skill_levels = SkillLevelManager.get_all_skill_levels()
        
        return Response({
            'skill_levels': skill_levels,
            'message': 'Skill levels retrieved successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve skill levels: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgotPasswordView(APIView):
    """
    Forgot password endpoint for sending password reset emails.
    This is a basic implementation - in production, you'd want to integrate
    with Django's built-in password reset system and email backend.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # In a real implementation, you would:
                # 1. Generate a password reset token
                # 2. Send an email with reset link
                # 3. Store the token with expiration
                
                # For now, we'll just return success
                # You can integrate Django's built-in password reset system here
                pass
            
            # Always return success to prevent email enumeration attacks
            return Response({
                'message': 'If an account with this email exists, you will receive a password reset link shortly.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'An error occurred while processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)