from django.db import models
from django.conf import settings

class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for opponent'),
        ('active', 'In progress'),
        ('finished', 'Finished'),
    ]

    white_player = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_as_white', on_delete=models.CASCADE)
    black_player = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_as_black', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    fen = models.CharField(max_length=100, default="startpos")
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='games_won')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Game {self.id} ({self.white_player} vs {self.black_player or 'TBD'})"

    def get_current_turn(self):
        """Determine whose turn it is from the FEN string."""
        # FEN format: piece_placement active_color castling ... 
        # Example: "rnbqkbnr/pppppppp/8/... w KQkq - 0 1"
        return 'white' if self.fen.split()[1] == 'w' else 'black'

    def is_player_turn(self, player):
        """Check if it's this player's turn."""
        current_turn = self.get_current_turn()
        return (current_turn == 'white' and player == self.white_player) or \
               (current_turn == 'black' and player == self.black_player)


class Move(models.Model):
    game = models.ForeignKey(Game, related_name='moves', on_delete=models.CASCADE)
    move_number = models.IntegerField()
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_square = models.CharField(max_length=2)
    to_square = models.CharField(max_length=2)
    notation = models.CharField(max_length=10)
    fen_after_move = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['move_number']
        indexes = [
            models.Index(fields=['game', 'move_number']),
        ]

    def __str__(self):
        return f"{self.player.username} {self.notation} (move {self.move_number})"


class PlayerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=1200)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def record_game(self, won: bool):
        """Update stats after a game."""
        self.games_played += 1
        if won:
            self.games_won += 1
        self.save()
