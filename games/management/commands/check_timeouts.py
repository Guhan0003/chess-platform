"""
Django management command for checking and handling game timeouts
Professional timeout detection system for chess games

Usage:
    python manage.py check_timeouts
    
This command should be run periodically (every 30 seconds) via cron job or task scheduler:
    */30 * * * * cd /path/to/chess-platform && python manage.py check_timeouts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import logging
from games.models import Game

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for game timeouts and automatically end timed-out games'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each game checked',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        start_time = timezone.now()
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'Starting timeout check at {start_time}')
            )

        # Get all active games
        active_games = Game.objects.filter(status='active').select_related(
            'white_player', 'black_player', 'time_control'
        )
        
        games_checked = 0
        games_timed_out = 0
        errors = 0

        for game in active_games:
            games_checked += 1
            
            try:
                with transaction.atomic():
                    # Check for timeout
                    timeout_info = game.check_timeout()
                    
                    if timeout_info['timeout']:
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'DRY RUN: Game {game.id} would be ended due to timeout '
                                    f'({timeout_info["timeout_player"]} player)'
                                )
                            )
                        else:
                            # Handle the timeout
                            success = game.handle_timeout()
                            if success:
                                games_timed_out += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Game {game.id} ended due to timeout '
                                        f'({timeout_info["timeout_player"]} player). '
                                        f'Winner: {timeout_info["winner"].username if timeout_info["winner"] else "None"}'
                                    )
                                )
                                
                                # Log the timeout for monitoring
                                logger.info(
                                    f'Game timeout handled: Game {game.id}, '
                                    f'timeout_player: {timeout_info["timeout_player"]}, '
                                    f'winner: {timeout_info["winner"].username if timeout_info["winner"] else "None"}'
                                )
                    elif verbose:
                        # Show game status for verbose mode
                        timer_info = game.get_timer_display()
                        self.stdout.write(
                            f'Game {game.id}: White {timer_info["white_time"]}s, '
                            f'Black {timer_info["black_time"]}s, '
                            f'Turn: {timer_info["current_turn"]}'
                        )
                        
            except Exception as e:
                errors += 1
                error_msg = f'Error checking game {game.id}: {str(e)}'
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(error_msg, exc_info=True)

        # Summary
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        summary_style = self.style.SUCCESS if errors == 0 else self.style.WARNING
        
        self.stdout.write(
            summary_style(
                f'\nTimeout check completed in {duration:.2f}s\n'
                f'Games checked: {games_checked}\n'
                f'Games timed out: {games_timed_out}\n'
                f'Errors: {errors}'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes were made')
            )
