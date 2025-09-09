# games/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import chess
import json


class TimeControl(models.Model):
    """Define different time control formats"""

    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(
        max_length=10,
        choices=[
            ('bullet', 'Bullet'),
            ('blitz', 'Blitz'),
            ('rapid', 'Rapid'),
            ('classical', 'Classical'),
            ('custom', 'Custom'),
        ]
    )
    initial_time = models.IntegerField(help_text="Initial time in seconds")
    increment = models.IntegerField(default=0, help_text="Increment per move in seconds")
    description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'time_controls'
        ordering = ['category', 'initial_time']

    def __str__(self):
        minutes = self.initial_time // 60
        if self.increment > 0:
            return f"{minutes}+{self.increment}"
        return f"{minutes} min"

    def get_display_name(self):
        """Get user-friendly display name"""
        minutes = self.initial_time // 60
        if self.increment > 0:
            return f"{self.name} ({minutes}+{self.increment})"
        return f"{self.name} ({minutes} min)"

    @classmethod
    def get_default_time_controls(cls):
        """Create default time controls if they don't exist"""
        defaults = [
            # Bullet
            {'name': 'Bullet 1+0', 'category': 'bullet', 'initial_time': 60, 'increment': 0},
            {'name': 'Bullet 2+1', 'category': 'bullet', 'initial_time': 120, 'increment': 1},

            # Blitz
            {'name': 'Blitz 3+0', 'category': 'blitz', 'initial_time': 180, 'increment': 0},
            {'name': 'Blitz 3+2', 'category': 'blitz', 'initial_time': 180, 'increment': 2},
            {'name': 'Blitz 5+0', 'category': 'blitz', 'initial_time': 300, 'increment': 0},
            {'name': 'Blitz 5+3', 'category': 'blitz', 'initial_time': 300, 'increment': 3},

            # Rapid
            {'name': 'Rapid 10+0', 'category': 'rapid', 'initial_time': 600, 'increment': 0},
            {'name': 'Rapid 10+5', 'category': 'rapid', 'initial_time': 600, 'increment': 5},
            {'name': 'Rapid 15+10', 'category': 'rapid', 'initial_time': 900, 'increment': 10},

            # Classical
            {'name': 'Classical 30+0', 'category': 'classical', 'initial_time': 1800, 'increment': 0},
            {'name': 'Classical 30+30', 'category': 'classical', 'initial_time': 1800, 'increment': 30},
            {'name': 'Classical 90+30', 'category': 'classical', 'initial_time': 5400, 'increment': 30},
        ]

        for tc_data in defaults:
            cls.objects.get_or_create(
                name=tc_data['name'],
                defaults=tc_data
            )


class Game(models.Model):
    """Enhanced game model with timer support and detailed tracking"""

    STATUS_CHOICES = [
        ('waiting', 'Waiting for opponent'),
        ('active', 'In progress'),
        ('finished', 'Finished'),
        ('aborted', 'Aborted'),
    ]

    RESULT_CHOICES = [
        ('1-0', 'White wins'),
        ('0-1', 'Black wins'),
        ('1/2-1/2', 'Draw'),
        ('*', 'Game in progress'),
    ]

    TERMINATION_CHOICES = [
        ('checkmate', 'Checkmate'),
        ('resignation', 'Resignation'),
        ('timeout', 'Time out'),
        ('draw_agreement', 'Draw by agreement'),
        ('stalemate', 'Stalemate'),
        ('insufficient_material', 'Insufficient material'),
        ('threefold_repetition', 'Threefold repetition'),
        ('fifty_move_rule', 'Fifty-move rule'),
        ('abandoned', 'Game abandoned'),
    ]

    # Players
    white_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_white',
        null=True,
        blank=True
    )
    black_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_black',
        null=True,
        blank=True
    )

    # Game state
    fen = models.CharField(
        max_length=200,
        default=chess.STARTING_FEN,
        help_text="Current board position in FEN"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='*')
    termination = models.CharField(max_length=30, choices=TERMINATION_CHOICES, blank=True, null=True)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_games'
    )

    # Timers
    time_control = models.CharField(max_length=20, default='rapid', help_text="Time control format")
    white_time_left = models.IntegerField(default=600, help_text="Remaining time in seconds for white")
    black_time_left = models.IntegerField(default=600, help_text="Remaining time in seconds for black")
    last_move_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'games_game'  # Use existing table name
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Game {self.id} ({self.white_player} vs {self.black_player})"

    def initialize_timers(self):
        """Set both players' clocks to the initial time"""
        if self.time_control:
            self.white_time_remaining = self.time_control.initial_time
            self.black_time_remaining = self.time_control.initial_time
        self.last_move_time = timezone.now()
        self.save()

    def update_clock(self, is_white_move=True):
        """
        Deduct time from the player who is currently moving.
        Should be called when a move is made.
        """
        if not self.last_move_time:
            self.last_move_time = timezone.now()
            self.save()
            return

        now = timezone.now()
        elapsed = int((now - self.last_move_time).total_seconds())

        if is_white_move:
            self.white_time_remaining = max(0, self.white_time_remaining - elapsed)
            if self.white_time_remaining > 0 and self.time_control:
                self.white_time_remaining += self.time_control.increment
        else:
            self.black_time_remaining = max(0, self.black_time_remaining - elapsed)
            if self.black_time_remaining > 0 and self.time_control:
                self.black_time_remaining += self.time_control.increment

        self.last_move_time = now
        self.save()

    def check_time_expired(self):
        """Return 'white' or 'black' if a player's time ran out"""
        if self.white_time_remaining <= 0:
            return 'white'
        if self.black_time_remaining <= 0:
            return 'black'
        return None


class Move(models.Model):
    """Store moves with notation and metadata"""

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    move_number = models.IntegerField()
    from_square = models.CharField(max_length=5)
    to_square = models.CharField(max_length=5)
    notation = models.CharField(max_length=20)
    fen_after_move = models.CharField(max_length=200, help_text="FEN after move", default=chess.STARTING_FEN)
    created_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.IntegerField(default=0, help_text="Seconds spent on this move")
    time_left = models.IntegerField(default=600, help_text="Time remaining after this move")
    captured_piece = models.CharField(max_length=2, blank=True, null=True)
    is_check = models.BooleanField(default=False)
    is_checkmate = models.BooleanField(default=False)
    is_castling = models.BooleanField(default=False)
    is_en_passant = models.BooleanField(default=False)
    promotion_piece = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        db_table = 'games_move'  # Use existing table name
        ordering = ['move_number']
        indexes = [
            models.Index(fields=['game', 'move_number']),
        ]

    def __str__(self):
        return f"Move {self.move_number}: {self.notation}"

    def to_dict(self):
        """Return JSON-serializable representation of move"""
        return {
            "move_number": self.move_number,
            "from": self.from_square,
            "to": self.to_square,
            "promotion": self.promotion_piece,
            "notation": self.notation,
            "fen_after": self.fen_after_move,
            "timestamp": self.created_at.isoformat(),
            "time_taken": self.time_taken,
        }
