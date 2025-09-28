# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
import os


class CustomUser(AbstractUser):
    """Enhanced user model with chess-specific fields"""
    
    # Basic Profile Info
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Chess Ratings (different time controls)
    blitz_rating = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    rapid_rating = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    classical_rating = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    
    # Peak ratings (for profile display)
    blitz_peak = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    rapid_peak = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    classical_peak = models.IntegerField(default=1200, validators=[MinValueValidator(100), MaxValueValidator(3500)])
    
    # Game Statistics
    total_games = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    games_drawn = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    
    # Time control specific stats
    blitz_games = models.IntegerField(default=0)
    rapid_games = models.IntegerField(default=0)
    classical_games = models.IntegerField(default=0)
    
    # Streaks and achievements
    current_win_streak = models.IntegerField(default=0)
    best_win_streak = models.IntegerField(default=0)
    puzzles_solved = models.IntegerField(default=0)
    
    # Account settings
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    preferred_time_control = models.CharField(
        max_length=10,
        choices=[('blitz', 'Blitz'), ('rapid', 'Rapid'), ('classical', 'Classical')],
        default='rapid'
    )
    initial_skill_level = models.CharField(
        max_length=15,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'), 
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ],
        null=True,
        blank=True,
        help_text="Initial skill level selected during registration"
    )
    
    # Privacy settings
    profile_public = models.BooleanField(default=True)
    show_rating = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_customuser'  # Use existing table name
        indexes = [
            models.Index(fields=['blitz_rating']),
            models.Index(fields=['rapid_rating']),
            models.Index(fields=['classical_rating']),
            models.Index(fields=['is_online']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """Override save to resize avatar and update peak ratings"""
        super().save(*args, **kwargs)
        
        # Resize avatar if it exists
        if self.avatar:
            self.resize_avatar()
        
        # Update peak ratings
        self.update_peak_ratings()

    def resize_avatar(self):
        """Resize uploaded avatar to 200x200"""
        if not self.avatar:
            return
            
        try:
            img = Image.open(self.avatar.path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 200x200
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            img.save(self.avatar.path, 'JPEG', quality=90)
            
        except Exception as e:
            print(f"Error resizing avatar for user {self.username}: {e}")

    def update_peak_ratings(self):
        """Update peak ratings if current ratings are higher"""
        updated = False
        
        if self.blitz_rating > self.blitz_peak:
            self.blitz_peak = self.blitz_rating
            updated = True
            
        if self.rapid_rating > self.rapid_peak:
            self.rapid_peak = self.rapid_rating
            updated = True
            
        if self.classical_rating > self.classical_peak:
            self.classical_peak = self.classical_rating
            updated = True
        
        if updated:
            # Use update() to avoid infinite recursion
            CustomUser.objects.filter(pk=self.pk).update(
                blitz_peak=self.blitz_peak,
                rapid_peak=self.rapid_peak,
                classical_peak=self.classical_peak
            )

    def get_rating(self, time_control='rapid'):
        """Get rating for specific time control"""
        return getattr(self, f'{time_control}_rating', self.rapid_rating)

    def get_peak_rating(self, time_control='rapid'):
        """Get peak rating for specific time control"""
        return getattr(self, f'{time_control}_peak', self.rapid_peak)

    def get_win_rate(self):
        """Calculate win percentage"""
        if self.total_games == 0:
            return 0
        return round((self.games_won / self.total_games) * 100, 1)

    def get_avatar_url(self):
        """Get avatar URL or return None"""
        if self.avatar:
            return self.avatar.url
        return None

    def update_game_stats(self, result, time_control='rapid'):
        """Update user statistics after a game"""
        self.total_games += 1
        
        # Update time control specific games
        time_control_games_field = f'{time_control}_games'
        current_games = getattr(self, time_control_games_field, 0)
        setattr(self, time_control_games_field, current_games + 1)
        
        # Update result stats and streaks
        if result == 'win':
            self.games_won += 1
            self.current_win_streak += 1
            if self.current_win_streak > self.best_win_streak:
                self.best_win_streak = self.current_win_streak
        elif result == 'loss':
            self.games_lost += 1
            self.current_win_streak = 0
        elif result == 'draw':
            self.games_drawn += 1
            self.current_win_streak = 0
        
        self.save()

    def get_recent_rating_change(self, time_control='rapid'):
        """Get recent rating change (mock for now - implement with rating history)"""
        # This would be calculated from RatingHistory model
        return 0


class RatingHistory(models.Model):
    """Track rating changes over time"""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rating_history')
    time_control = models.CharField(
        max_length=10,
        choices=[('blitz', 'Blitz'), ('rapid', 'Rapid'), ('classical', 'Classical')]
    )
    old_rating = models.IntegerField()
    new_rating = models.IntegerField()
    rating_change = models.IntegerField()  # Can be positive or negative
    game = models.ForeignKey('games.Game', on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(
        max_length=20,
        choices=[
            ('game_result', 'Game Result'),
            ('manual_adjustment', 'Manual Adjustment'),
            ('decay', 'Rating Decay'),
        ],
        default='game_result'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rating_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'time_control']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.time_control}: {self.old_rating} → {self.new_rating}"


class Achievement(models.Model):
    """Define available achievements"""
    
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=10, default='🏆')  # Unicode emoji
    category = models.CharField(
        max_length=20,
        choices=[
            ('games', 'Games'),
            ('rating', 'Rating'),
            ('streaks', 'Streaks'),
            ('puzzles', 'Puzzles'),
            ('special', 'Special'),
        ],
        default='games'
    )
    requirement = models.JSONField(default=dict)  # Store achievement requirements
    points = models.IntegerField(default=10)  # Achievement points
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achievements'

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Track user achievements"""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UserSettings(models.Model):
    """User preferences and settings"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='settings')
    
    # Game preferences
    auto_queen_promotion = models.BooleanField(default=True)
    show_coordinates = models.BooleanField(default=True)
    highlight_moves = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    
    # Notification settings
    email_game_invites = models.BooleanField(default=True)
    email_game_results = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Privacy settings
    allow_challenges = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)
    
    # UI preferences
    board_theme = models.CharField(
        max_length=20,
        choices=[
            ('classic', 'Classic'),
            ('modern', 'Modern'),
            ('wood', 'Wood'),
            ('marble', 'Marble'),
        ],
        default='classic'
    )
    piece_set = models.CharField(
        max_length=20,
        choices=[
            ('classic', 'Classic'),
            ('modern', 'Modern'),
            ('staunton', 'Staunton'),
        ],
        default='classic'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_settings'

    def __str__(self):
        return f"{self.user.username} Settings"