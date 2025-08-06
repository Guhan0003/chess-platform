from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    rating = models.IntegerField(default=1200)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

User = get_user_model()

class Game(models.Model):
    WHITE = 'w'
    BLACK = 'b'
    RESULT_CHOICES = [
        ('1-0', 'White wins'),
        ('0-1', 'Black wins'),
        ('1/2-1/2', 'Draw'),
    ]

    white_player = models.ForeignKey(User, related_name='white_games', on_delete=models.CASCADE)
    black_player = models.ForeignKey(User, related_name='black_games', on_delete=models.CASCADE)
    result = models.CharField(max_length=7, choices=RESULT_CHOICES)
    moves = models.TextField(blank=True)  # can be PGN or FEN later
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.white_player} vs {self.black_player} - {self.result}"