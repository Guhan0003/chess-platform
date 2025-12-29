"""
Management command to recalculate and fix user game statistics.

This command recalculates total_games, games_won, games_lost, games_drawn
based on actual finished games in the database.

Usage:
    python manage.py fix_game_stats
    python manage.py fix_game_stats --dry-run  # Preview changes without applying
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from games.models import Game

User = get_user_model()


class Command(BaseCommand):
    help = 'Recalculate user game statistics from actual game results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made\n'))
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            # Skip computer accounts
            if 'computer' in user.username.lower():
                continue
                
            # Calculate actual stats from finished games (human vs human only)
            # Games where user was white
            white_games = Game.objects.filter(
                white_player=user,
                status='finished',
                result__in=['1-0', '0-1', '1/2-1/2']
            ).exclude(black_player__username__icontains='computer')
            
            # Games where user was black
            black_games = Game.objects.filter(
                black_player=user,
                status='finished',
                result__in=['1-0', '0-1', '1/2-1/2']
            ).exclude(white_player__username__icontains='computer')
            
            # Count wins, losses, draws
            wins = 0
            losses = 0
            draws = 0
            
            # As white: 1-0 = win, 0-1 = loss, 1/2-1/2 = draw
            for game in white_games:
                if game.result == '1-0':
                    wins += 1
                elif game.result == '0-1':
                    losses += 1
                elif game.result == '1/2-1/2':
                    draws += 1
            
            # As black: 0-1 = win, 1-0 = loss, 1/2-1/2 = draw
            for game in black_games:
                if game.result == '0-1':
                    wins += 1
                elif game.result == '1-0':
                    losses += 1
                elif game.result == '1/2-1/2':
                    draws += 1
            
            total_games = wins + losses + draws
            
            # Check if stats need updating
            current_sum = user.games_won + user.games_lost + user.games_drawn
            needs_update = (
                user.total_games != total_games or
                user.games_won != wins or
                user.games_lost != losses or
                user.games_drawn != draws
            )
            
            if needs_update:
                self.stdout.write(f'\n{user.username}:')
                self.stdout.write(f'  Current: total={user.total_games}, won={user.games_won}, lost={user.games_lost}, drawn={user.games_drawn} (sum={current_sum})')
                self.stdout.write(f'  Correct: total={total_games}, won={wins}, lost={losses}, drawn={draws}')
                
                if not dry_run:
                    user.total_games = total_games
                    user.games_won = wins
                    user.games_lost = losses
                    user.games_drawn = draws
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Fixed!'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete. Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll user stats have been recalculated and fixed!'))
