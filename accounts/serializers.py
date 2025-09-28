from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """Enhanced registration serializer with skill level and rating initialization"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    skill_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        required=True,
        write_only=True
    )
    initial_rating = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm', 
            'first_name', 'last_name', 'skill_level', 'initial_rating'
        )
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_username(self, value):
        """Validate username requirements"""
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
        return value

    def validate_email(self, value):
        """Check if email is already registered"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_skill_level(self, value):
        """Validate skill level choice"""
        from games.utils.rating_calculator import SkillLevelManager
        
        if not SkillLevelManager.validate_skill_level(value):
            raise serializers.ValidationError("Invalid skill level selected.")
        return value

    def validate(self, data):
        """Validate password confirmation and skill level consistency"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate skill level and initial rating consistency
        skill_level = data.get('skill_level')
        initial_rating = data.get('initial_rating')
        
        if skill_level and initial_rating:
            from games.utils.rating_calculator import SkillLevelManager
            expected_rating = SkillLevelManager.SKILL_LEVELS[skill_level]['rating']
            
            if abs(initial_rating - expected_rating) > 50:  # Allow some tolerance
                raise serializers.ValidationError(
                    f"Initial rating {initial_rating} doesn't match skill level {skill_level}"
                )
        
        return data

    def create(self, validated_data):
        """Create user with skill level and initial ratings"""
        from games.utils.rating_calculator import initialize_user_ratings
        
        # Extract skill level data
        skill_level = validated_data.pop('skill_level')
        validated_data.pop('initial_rating', None)  # Remove as it's calculated
        validated_data.pop('password_confirm')  # Remove password_confirm
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            initial_skill_level=skill_level
        )
        
        # Initialize ratings based on skill level
        try:
            applied_ratings = initialize_user_ratings(user, skill_level)
            
            # Log the successful rating initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"User {user.username} registered with skill level {skill_level} "
                       f"and ratings: {applied_ratings}")
                       
        except Exception as e:
            # If rating initialization fails, delete user and re-raise
            user.delete()
            raise serializers.ValidationError(f"Failed to initialize user ratings: {str(e)}")
        
        return user


class UserGameSerializer(serializers.ModelSerializer):
    """Minimal user data for game contexts"""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar', 'rapid_rating', 'is_online')

    def to_representation(self, instance):
        """Customize representation for game context"""
        data = super().to_representation(instance)
        # Ensure avatar URL is properly formatted
        if data['avatar']:
            request = self.context.get('request')
            if request:
                data['avatar'] = request.build_absolute_uri(data['avatar'])
        return data


class UserPublicSerializer(serializers.ModelSerializer):
    """Privacy-aware public profile for other users viewing"""
    avatar_url = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()
    member_since = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    # Privacy-aware rating fields
    blitz_rating_display = serializers.SerializerMethodField()
    rapid_rating_display = serializers.SerializerMethodField()
    classical_rating_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'avatar_url', 'bio', 'country', 'is_online',
            'blitz_rating_display', 'rapid_rating_display', 'classical_rating_display',
            'total_games', 'games_won', 'games_lost', 'games_drawn', 'win_rate',
            'member_since', 'recent_activity'
        )

    def get_avatar_url(self, obj):
        """Get full avatar URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_blitz_rating_display(self, obj):
        """Return rating if user allows it to be shown"""
        return obj.blitz_rating if obj.show_rating else None

    def get_rapid_rating_display(self, obj):
        """Return rating if user allows it to be shown"""
        return obj.rapid_rating if obj.show_rating else None

    def get_classical_rating_display(self, obj):
        """Return rating if user allows it to be shown"""
        return obj.classical_rating if obj.show_rating else None

    def get_win_rate(self, obj):
        """Calculate win rate percentage"""
        if obj.total_games == 0:
            return None
        return round((obj.games_won / obj.total_games) * 100, 1)

    def get_member_since(self, obj):
        """Get user registration date"""
        return obj.date_joined.strftime('%B %Y')

    def get_recent_activity(self, obj):
        """Get last activity status"""
        if obj.is_online:
            return "Online now"
        elif obj.last_activity:
            time_diff = timezone.now() - obj.last_activity
            if time_diff < timedelta(minutes=5):
                return "Just now"
            elif time_diff < timedelta(hours=1):
                return f"{int(time_diff.total_seconds() // 60)} minutes ago"
            elif time_diff < timedelta(days=1):
                return f"{int(time_diff.total_seconds() // 3600)} hours ago"
            else:
                return obj.last_activity.strftime('%B %d, %Y')
        return "Unknown"


class UserProfileSerializer(serializers.ModelSerializer):
    """Complete profile data for the user's own profile"""
    avatar_url = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()
    draw_rate = serializers.SerializerMethodField()
    member_since = serializers.SerializerMethodField()
    
    # Rating statistics
    peak_ratings = serializers.SerializerMethodField()
    recent_rating_changes = serializers.SerializerMethodField()
    rating_progress = serializers.SerializerMethodField()
    
    # Achievement summary
    achievement_summary = serializers.SerializerMethodField()
    recent_achievements = serializers.SerializerMethodField()
    
    # Time control statistics
    time_control_stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'avatar_url',
            'bio', 'country', 'is_online', 'member_since',
            
            # Skill level and ratings
            'initial_skill_level',
            'blitz_rating', 'rapid_rating', 'classical_rating',
            'blitz_peak', 'rapid_peak', 'classical_peak', 'peak_ratings',
            
            # Game statistics
            'total_games', 'games_won', 'games_lost', 'games_drawn',
            'win_rate', 'draw_rate', 'time_control_stats',
            
            # Streaks and achievements
            'current_win_streak', 'best_win_streak', 'puzzles_solved',
            'achievement_summary', 'recent_achievements',
            
            # Settings
            'preferred_time_control', 'profile_public', 'show_rating',
            
            # Rating analysis
            'recent_rating_changes', 'rating_progress'
        )

    def get_avatar_url(self, obj):
        """Get full avatar URL"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            try:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.avatar.url)
                else:
                    # Fallback: construct URL without request context
                    # obj.avatar.url already includes the MEDIA_URL prefix
                    return f"http://127.0.0.1:8000{obj.avatar.url}"
            except Exception:
                # If there's any issue with the avatar URL, return the path
                return f"http://127.0.0.1:8000{obj.avatar.url}" if obj.avatar else None
        return None

    def get_win_rate(self, obj):
        """Calculate win rate percentage"""
        if obj.total_games == 0:
            return 0.0
        return round((obj.games_won / obj.total_games) * 100, 1)

    def get_draw_rate(self, obj):
        """Calculate draw rate percentage"""
        if obj.total_games == 0:
            return 0.0
        return round((obj.games_drawn / obj.total_games) * 100, 1)

    def get_member_since(self, obj):
        """Get user registration date"""
        return obj.date_joined.strftime('%B %d, %Y')

    def get_peak_ratings(self, obj):
        """Get peak ratings with dates"""
        return {
            'blitz': {
                'rating': obj.blitz_peak,
                'achieved': obj.date_joined.strftime('%Y-%m-%d')  # TODO: Get actual peak date from RatingHistory
            },
            'rapid': {
                'rating': obj.rapid_peak,
                'achieved': obj.date_joined.strftime('%Y-%m-%d')  # TODO: Get actual peak date from RatingHistory
            },
            'classical': {
                'rating': obj.classical_peak,
                'achieved': obj.date_joined.strftime('%Y-%m-%d')  # TODO: Get actual peak date from RatingHistory
            }
        }

    def get_recent_rating_changes(self, obj):
        """Get recent rating changes (last 10)"""
        # TODO: Implement when RatingHistory model is available
        # For now, return placeholder data
        return []

    def get_rating_progress(self, obj):
        """Get 30-day rating progression"""
        # TODO: Calculate actual rating changes from RatingHistory
        # For now, return basic data
        return {
            'blitz_30d_change': 0,
            'rapid_30d_change': 0,
            'classical_30d_change': 0,
            'games_last_30d': 0
        }

    def get_achievement_summary(self, obj):
        """Get achievement summary"""
        try:
            achievements = obj.achievements.select_related('achievement')
            total_count = achievements.count()
            total_points = sum(ua.achievement.points for ua in achievements)
            
            # Count by category
            categories = {}
            for ua in achievements:
                category = ua.achievement.category
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            return {
                'total_achievements': total_count,
                'total_points': total_points,
                'categories': categories
            }
        except:
            return {
                'total_achievements': 0,
                'total_points': 0,
                'categories': {}
            }

    def get_recent_achievements(self, obj):
        """Get last 5 achievements earned"""
        try:
            recent = obj.achievements.select_related('achievement').order_by('-unlocked_at')[:5]
            return [
                {
                    'name': ua.achievement.name,
                    'description': ua.achievement.description,
                    'icon': ua.achievement.icon,
                    'category': ua.achievement.category,
                    'points': ua.achievement.points,
                    'unlocked_at': ua.unlocked_at.strftime('%Y-%m-%d')
                }
                for ua in recent
            ]
        except:
            return []

    def get_time_control_stats(self, obj):
        """Get time control specific statistics"""
        return {
            'blitz': {
                'games': obj.blitz_games,
                'rating': obj.blitz_rating,
                'peak': obj.blitz_peak
            },
            'rapid': {
                'games': obj.rapid_games,
                'rating': obj.rapid_rating,
                'peak': obj.rapid_peak
            },
            'classical': {
                'games': obj.classical_games,
                'rating': obj.classical_rating,
                'peak': obj.classical_peak
            }
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    """For profile updates with proper validation"""
    email = serializers.EmailField(required=False)
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'bio', 'country',
            'preferred_time_control', 'profile_public', 'show_rating', 'email'
        )
        extra_kwargs = {
            'bio': {'max_length': 500, 'allow_blank': True},
            'country': {'max_length': 2, 'allow_blank': True},
        }

    def validate_email(self, value):
        """Check if email is already taken by another user"""
        if value:
            user = self.instance
            if User.objects.filter(email=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_country(self, value):
        """Validate country code format"""
        if value and len(value) != 2:
            raise serializers.ValidationError("Country code must be 2 characters long.")
        return value.upper() if value else value


class UserStatsSerializer(serializers.ModelSerializer):
    """Statistics-only serializer for leaderboards/quick stats"""
    win_rate = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    rating_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'avatar_url', 'country', 'is_online',
            'blitz_rating', 'rapid_rating', 'classical_rating',
            'total_games', 'games_won', 'win_rate', 'rating_display'
        )

    def get_win_rate(self, obj):
        """Calculate win rate percentage"""
        if obj.total_games == 0:
            return 0.0
        return round((obj.games_won / obj.total_games) * 100, 1)

    def get_avatar_url(self, obj):
        """Get full avatar URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_rating_display(self, obj):
        """Get highest rating for general display"""
        return max(obj.blitz_rating, obj.rapid_rating, obj.classical_rating)


def get_user_serializer(request, target_user):
    """
    Context-aware serializer selection based on privacy settings and user relationship
    
    Args:
        request: Current HTTP request
        target_user: User object being serialized
        
    Returns:
        Appropriate serializer class
    """
    # User viewing their own profile
    if request.user == target_user:
        return UserProfileSerializer
    
    # Public profile or user has permission to view
    elif target_user.profile_public:
        return UserPublicSerializer
    
    # Private profile - minimal data only
    else:
        return UserGameSerializer