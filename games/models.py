# games/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import chess
import json
import logging
from .utils.timer_manager import TimerManager
from .utils.time_control import TimeManager, create_time_manager

logger = logging.getLogger(__name__)


class ChessManager:
    """Manager class for chess platform data initialization and management"""
    
    @staticmethod
    def create_default_time_controls():
        """Create standard time controls used in professional chess"""
        defaults = [
            # Ultra-Bullet & Bullet (< 3 minutes)
            {'name': '30 sec', 'category': 'bullet', 'initial_time': 30, 'increment': 0,
             'description': 'Ultra-fast 30 second games'},
            {'name': 'Bullet 1+0', 'category': 'bullet', 'initial_time': 60, 'increment': 0, 
             'description': 'Ultra-fast 1 minute games'},
            {'name': 'Bullet 1+1', 'category': 'bullet', 'initial_time': 60, 'increment': 1,
             'description': '1 minute with 1 second increment'},
            {'name': 'Bullet 2+0', 'category': 'bullet', 'initial_time': 120, 'increment': 0,
             'description': '2 minute bullet games'},
            {'name': 'Bullet 2+1', 'category': 'bullet', 'initial_time': 120, 'increment': 1,
             'description': 'Fast-paced games with small increment'},

            # Blitz (3-10 minutes)
            {'name': 'Blitz 3+0', 'category': 'blitz', 'initial_time': 180, 'increment': 0,
             'description': 'Classic blitz format'},
            {'name': 'Blitz 3+2', 'category': 'blitz', 'initial_time': 180, 'increment': 2,
             'description': 'Popular online blitz format'},
            {'name': 'Blitz 5+0', 'category': 'blitz', 'initial_time': 300, 'increment': 0,
             'description': 'Standard 5-minute blitz'},
            {'name': 'Blitz 5+3', 'category': 'blitz', 'initial_time': 300, 'increment': 3,
             'description': '5-minute blitz with increment'},
            {'name': 'Blitz 5+5', 'category': 'blitz', 'initial_time': 300, 'increment': 5,
             'description': '5-minute blitz with 5 second increment'},

            # Rapid (10-30 minutes)
            {'name': 'Rapid 10+0', 'category': 'rapid', 'initial_time': 600, 'increment': 0,
             'description': 'Quick rapid games'},
            {'name': 'Rapid 10+5', 'category': 'rapid', 'initial_time': 600, 'increment': 5,
             'description': 'Popular rapid format with increment'},
            {'name': 'Rapid 15+0', 'category': 'rapid', 'initial_time': 900, 'increment': 0,
             'description': '15-minute rapid games'},
            {'name': 'Rapid 15+10', 'category': 'rapid', 'initial_time': 900, 'increment': 10,
             'description': 'Tournament-style rapid'},

            # Classical (30+ minutes)
            {'name': 'Classical 30+0', 'category': 'classical', 'initial_time': 1800, 'increment': 0,
             'description': 'Classical time control'},
            {'name': 'Classical 30+20', 'category': 'classical', 'initial_time': 1800, 'increment': 20,
             'description': 'Classical with 20 second increment'},
            {'name': 'Classical 60+0', 'category': 'classical', 'initial_time': 3600, 'increment': 0,
             'description': '60-minute classical games'},
            {'name': 'Classical 90+30', 'category': 'classical', 'initial_time': 5400, 'increment': 30,
             'description': 'FIDE-style long classical games'},
        ]

        created_count = 0
        for tc_data in defaults:
            time_control, created = TimeControl.objects.get_or_create(
                name=tc_data['name'],
                defaults=tc_data
            )
            if created:
                created_count += 1
        
        return created_count
    
    @staticmethod
    def create_default_achievements():
        """Create standard chess achievements"""
        from accounts.models import Achievement
        
        defaults = [
            # Milestone Achievements
            {'key': 'first_victory', 'name': 'First Victory', 'description': 'Win your first game', 
             'category': 'games', 'requirement': {'games_won': 1}, 'points': 10, 'icon': '🎯'},
            {'key': 'veteran_player', 'name': 'Veteran Player', 'description': 'Play 100 games', 
             'category': 'games', 'requirement': {'total_games': 100}, 'points': 50, 'icon': '🏆'},
            {'key': 'chess_master', 'name': 'Chess Master', 'description': 'Play 1000 games', 
             'category': 'games', 'requirement': {'total_games': 1000}, 'points': 200, 'icon': '👑'},
            
            # Rating Achievements
            {'key': 'rising_star', 'name': 'Rising Star', 'description': 'Reach 1400 rating', 
             'category': 'rating', 'requirement': {'rapid_rating': 1400}, 'points': 25, 'icon': '⭐'},
            {'key': 'strong_player', 'name': 'Strong Player', 'description': 'Reach 1600 rating', 
             'category': 'rating', 'requirement': {'rapid_rating': 1600}, 'points': 50, 'icon': '💪'},
            {'key': 'expert_level', 'name': 'Expert Level', 'description': 'Reach 1800 rating', 
             'category': 'rating', 'requirement': {'rapid_rating': 1800}, 'points': 100, 'icon': '🎓'},
            {'key': 'master_level', 'name': 'Master Level', 'description': 'Reach 2000 rating', 
             'category': 'rating', 'requirement': {'rapid_rating': 2000}, 'points': 200, 'icon': '🥇'},
            
            # Streak Achievements
            {'key': 'win_streak', 'name': 'Win Streak', 'description': 'Win 5 games in a row', 
             'category': 'streaks', 'requirement': {'win_streak': 5}, 'points': 30, 'icon': '🔥'},
            {'key': 'unstoppable', 'name': 'Unstoppable', 'description': 'Win 10 games in a row', 
             'category': 'streaks', 'requirement': {'win_streak': 10}, 'points': 75, 'icon': '⚡'},
            
            # Special Achievements
            {'key': 'speed_demon', 'name': 'Speed Demon', 'description': 'Win 50 blitz games', 
             'category': 'special', 'requirement': {'blitz_games': 50}, 'points': 40, 'icon': '💨'},
            {'key': 'puzzle_solver', 'name': 'Puzzle Solver', 'description': 'Solve 100 puzzles', 
             'category': 'puzzles', 'requirement': {'puzzles_solved': 100}, 'points': 35, 'icon': '🧩'},
        ]

        created_count = 0
        for ach_data in defaults:
            achievement, created = Achievement.objects.get_or_create(
                key=ach_data['key'],
                defaults=ach_data
            )
            if created:
                created_count += 1
        
        return created_count


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

    # ================== PROFESSIONAL TIMER INTEGRATION ==================

    def get_timer_manager(self):
        """Get professional TimerManager instance for this game"""
        if not hasattr(self, '_timer_manager'):
            # Map time control string to TimerManager format
            # Supports both category names and specific time controls
            time_control_map = {
                # Category defaults
                'bullet': 'bullet_2',
                'blitz': 'blitz_5',
                'rapid': 'rapid_10',
                'classical': 'classical_30',
                'unlimited': 'unlimited',
                
                # Specific time controls (pass through if already specific)
                'bullet_30s': 'bullet_30s',
                'bullet_1': 'bullet_1',
                'bullet_1_1': 'bullet_1_1',
                'bullet_2': 'bullet_2',
                'bullet_2_1': 'bullet_2_1',
                'blitz_3': 'blitz_3',
                'blitz_3_2': 'blitz_3_2',
                'blitz_5': 'blitz_5',
                'blitz_5_3': 'blitz_5_3',
                'blitz_5_5': 'blitz_5_5',
                'rapid_10': 'rapid_10',
                'rapid_10_5': 'rapid_10_5',
                'rapid_15': 'rapid_15',
                'rapid_15_10': 'rapid_15_10',
                'classical_30': 'classical_30',
                'classical_30_20': 'classical_30_20',
                'classical_60': 'classical_60',
                'classical_90_30': 'classical_90_30'
            }
            
            timer_control = time_control_map.get(self.time_control, 'rapid_10')
            self._timer_manager = TimerManager(timer_control)
            
            # Initialize TimerManager with current game state from database
            # This is critical: use DATABASE values, not TimerManager defaults!
            if self.status == 'active':
                self._timer_manager.white_time = self.white_time_left
                self._timer_manager.black_time = self.black_time_left
                self._timer_manager.current_turn = self.get_current_player_color()
                self._timer_manager.game_started = True
                
                # Use last_move_at from database for accurate elapsed time calculation
                if self.last_move_at:
                    self._timer_manager.last_move_time = self.last_move_at.timestamp()
                else:
                    # No last_move_at set - use game creation time or current time
                    import time
                    self._timer_manager.last_move_time = time.time()
                
        return self._timer_manager

    def get_bot_time_manager(self, bot_rating=1500):
        """Get professional TimeManager for bot thinking time"""
        if not hasattr(self, '_bot_time_manager'):
            self._bot_time_manager = create_time_manager(bot_rating)
        return self._bot_time_manager

    def start_professional_timer(self):
        """
        Start the professional timer system when game becomes active.
        
        IMPORTANT: This method should only SET last_move_at to mark the game start.
        It should NOT overwrite white_time_left/black_time_left which were already
        set correctly when the game was created.
        """
        # CRITICAL: Only set last_move_at to mark the start of the game
        # Do NOT overwrite time values - they were correctly set in create_game
        self.status = 'active'
        self.last_move_at = timezone.now()
        self.save()
        
        logger.info(f"Game {self.id} started: white={self.white_time_left}s, black={self.black_time_left}s, time_control={self.time_control}")
        
        return {
            'white_time': self.white_time_left,
            'black_time': self.black_time_left,
            'game_started': True,
            'time_control': self.time_control
        }

    def make_timer_move(self, player_color):
        """Professional move timing with TimerManager"""
        timer = self.get_timer_manager()
        timer_state = timer.make_move(player_color)
        
        # Update model with new timer state (convert to int for database storage)
        white_time = timer_state.get('white_time')
        black_time = timer_state.get('black_time')
        self.white_time_left = int(white_time) if white_time is not None else 0
        self.black_time_left = int(black_time) if black_time is not None else 0
        self.last_move_at = timezone.now()
        
        # Check for timeout
        timeout_player = timer.check_timeout()
        if timeout_player:
            self.status = 'finished'
            self.result = '0-1' if timeout_player == 'white' else '1-0'
            self.termination = 'timeout'
            self.winner = self.black_player if timeout_player == 'white' else self.white_player
        
        self.save()
        return timer_state

    def get_professional_timer_state(self):
        """Get current professional timer state"""
        timer = self.get_timer_manager()
        return timer.get_timer_state()

    def calculate_bot_thinking_time(self, bot_rating, board, move_complexity=5.0):
        """Calculate realistic bot thinking time"""
        from .utils.time_control import MoveType
        
        bot_timer = self.get_bot_time_manager(bot_rating)
        
        # Determine move type based on position
        move_type = MoveType.ROUTINE  # Default
        if board.is_check():
            move_type = MoveType.TACTICAL
        elif len(list(board.legal_moves)) > 20:
            move_type = MoveType.COMPLEX
        elif len(list(board.legal_moves)) < 5:
            move_type = MoveType.FORCED
            
        return bot_timer.calculate_thinking_time(
            board, move_type, move_complexity
        )

    def get_current_player_color(self):
        """Get current player color based on move count"""
        move_count = self.moves.count()
        return 'white' if move_count % 2 == 0 else 'black'

    # ================== END PROFESSIONAL TIMER INTEGRATION ==================

    # ================== WEBSOCKET INTEGRATION ==================
    
    def notify_move(self, move_data):
        """Notify all players about a move via WebSocket - OPTIMIZED for speed."""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        import threading
        
        channel_layer = get_channel_layer()
        group_name = f'game_{self.id}'
        
        print(f"🔍 Channel layer available: {channel_layer is not None}")
        print(f"🔍 Group name: {group_name}")
        
        if channel_layer:
            # Send notification in a separate thread for instant response
            def send_notification():
                try:
                    print(f"📡 Broadcasting move to WebSocket group: {group_name}")
                    print(f"Move data: {move_data}")
                    
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'move_made',
                            'move': move_data,
                            'game_state': {
                                'id': self.id,
                                'fen': self.fen,
                                'status': self.status,
                                'white_time_left': self.white_time_left,
                                'black_time_left': self.black_time_left,
                                'moves': list(self.moves.all().values(
                                    'move_number', 'notation', 'from_square', 'to_square',
                                    'player__username', 'created_at'
                                )),
                                'white_player': self.white_player.username if self.white_player else None,
                                'black_player': self.black_player.username if self.black_player else None,
                            }
                        }
                    )
                    print(f"✅ WebSocket broadcast completed for game {self.id}")
                except Exception as e:
                    logger.warning(f"WebSocket notification failed: {e}")
                    print(f"❌ WebSocket broadcast failed: {e}")
            
            # Execute notification asynchronously
            thread = threading.Thread(target=send_notification)
            thread.daemon = True
            thread.start()
    
    def notify_timer_update(self):
        """Notify all players about timer updates via WebSocket."""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        timer_group = f'timer_{self.id}'
        
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                timer_group,
                {
                    'type': 'timer_update',
                    'data': {
                        'white_time': self.white_time_left,
                        'black_time': self.black_time_left,
                        'current_turn': self.get_current_player_color()
                    }
                }
            )
    
    def notify_game_finished(self, reason):
        """Notify all players that the game has finished."""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        group_name = f'game_{self.id}'
        
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'game_finished',
                    'result': self.result,
                    'termination': self.termination,
                    'winner': self.winner.username if self.winner else None,
                    'reason': reason
                }
            )
    
    def get_websocket_state(self):
        """Get game state data optimized for WebSocket transmission."""
        board = chess.Board(self.fen)
        
        return {
            'id': self.id,
            'fen': self.fen,
            'status': self.status,
            'result': self.result,
            'white_player': self.white_player.username if self.white_player else None,
            'black_player': self.black_player.username if self.black_player else None,
            'current_turn': 'white' if board.turn else 'black',
            'is_check': board.is_check(),
            'is_checkmate': board.is_checkmate(),
            'is_stalemate': board.is_stalemate(),
            'white_time_left': self.white_time_left,
            'black_time_left': self.black_time_left,
        }
    
    # ================== END WEBSOCKET INTEGRATION ==================

    # ================== ENHANCED TIMEOUT HANDLING ==================
    
    def check_timeout(self):
        """
        Check if any player has timed out. 
        Returns timeout information if timeout occurred.
        """
        if self.status != 'active':
            return {'timeout': False}
        
        try:
            timer = self.get_timer_manager()
            timeout_player = timer.check_timeout()
            
            if timeout_player:
                return {
                    'timeout': True,
                    'timeout_player': timeout_player,
                    'winner': self.black_player if timeout_player == 'white' else self.white_player
                }
            
            return {'timeout': False}
            
        except Exception as e:
            logger.error(f"Error checking timeout for game {self.id}: {e}")
            return {'timeout': False}
    
    def handle_timeout(self):
        """
        Handle timeout by ending the game and setting the winner.
        Returns True if timeout was handled, False otherwise.
        """
        try:
            timeout_info = self.check_timeout()
            
            if not timeout_info['timeout']:
                return False
            
            timeout_player = timeout_info['timeout_player']
            winner = timeout_info['winner']
            
            # Update game status for timeout
            self.status = 'finished'
            self.result = '0-1' if timeout_player == 'white' else '1-0'
            self.termination = 'timeout'
            self.winner = winner
            self.finished_at = timezone.now()
            
            # Set time left to 0 for the player who timed out
            if timeout_player == 'white':
                self.white_time_left = 0
            else:
                self.black_time_left = 0
            
            # UPDATE RATINGS - Professional global rating system
            # ONLY UPDATE FOR PLAYER VS PLAYER GAMES (not bot games)
            if self.white_player and self.black_player:
                # Check if either player is a bot (has 'computer' in username)
                is_white_bot = 'computer' in self.white_player.username.lower()
                is_black_bot = 'computer' in self.black_player.username.lower()
                
                # Only update ratings if BOTH players are humans (not bots)
                if not is_white_bot and not is_black_bot:
                    try:
                        from games.services import update_game_ratings
                        # Get time control string (category) from TimeControl model
                        time_control_str = self.time_control.category if self.time_control else 'rapid'
                        rating_result = update_game_ratings(
                            white_player=self.white_player,
                            black_player=self.black_player,
                            game_result=self.result,
                            time_control=time_control_str,
                            game_instance=self
                        )
                        logger.info(f"Ratings updated after timeout: {rating_result}")
                    except Exception as e:
                        logger.error(f"Failed to update ratings after timeout: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    logger.info(f"Skipping rating update - bot game timeout")
                
            self.save()
            
            # Create timeout move record for history
            move_number = self.moves.count() + 1
            Move.objects.create(
                game=self,
                player=self.white_player if timeout_player == 'white' else self.black_player,
                move_number=move_number,
                from_square='',
                to_square='',
                notation=f'{timeout_player.capitalize()} forfeits on time',
                fen_after_move=self.fen
            )
            
            # Notify via WebSocket
            self.notify_game_finished('timeout')
            
            logger.info(f"Game {self.id} ended due to timeout: {timeout_player} player timed out, {winner.username if winner else 'None'} wins")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling timeout for game {self.id}: {e}")
            return False
    
    def get_timer_display(self):
        """Get timer display information for management commands and logging"""
        try:
            timer = self.get_timer_manager()
            timer_state = timer.get_timer_state()
            
            return {
                'white_time': f"{timer_state.get('white_time', 0):.1f}",
                'black_time': f"{timer_state.get('black_time', 0):.1f}",
                'current_turn': timer_state.get('current_turn', 'white'),
                'game_started': timer_state.get('game_started', False),
                'game_ended': timer_state.get('game_ended', False)
            }
        except Exception as e:
            return {
                'white_time': 'N/A',
                'black_time': 'N/A',
                'current_turn': 'unknown',
                'game_started': False,
                'game_ended': False,
                'error': str(e)
            }
    
    # ================== END ENHANCED TIMEOUT HANDLING ==================


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


class GameInvitation(models.Model):
    """Handle game invitations between players"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    to_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    time_control = models.ForeignKey(TimeControl, on_delete=models.CASCADE)
    message = models.TextField(max_length=200, blank=True, help_text="Optional invitation message")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this invitation expires")
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'games_gameinvitation'  # Following your naming convention
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_player', 'status']),
            models.Index(fields=['to_player', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.from_player.username} → {self.to_player.username} ({self.time_control})"
    
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at
    
    def accept(self):
        """Accept the invitation and create game"""
        if self.status != 'pending' or self.is_expired():
            return None
            
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
        
        # Create the game with proper time control format
        game = Game.objects.create(
            white_player=self.from_player,
            black_player=self.to_player,
            time_control=self.time_control.category,  # Use category string to match Game model
            white_time_left=self.time_control.initial_time,
            black_time_left=self.time_control.initial_time,
            status='waiting'
        )
        return game
    
    def decline(self):
        """Decline the invitation"""
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancel the invitation (only by sender)"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.responded_at = timezone.now()
            self.save()
    
    def get_display_name(self):
        """Get user-friendly display for the invitation"""
        return f"{self.time_control.get_display_name()} game"

class Puzzle(models.Model):
    """Chess puzzle for tactical training"""
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    CATEGORY_CHOICES = [
        ('tactics', 'Tactics'),
        ('endgame', 'Endgame'),
        ('opening', 'Opening'),
        ('strategy', 'Strategy'),
        ('checkmate', 'Checkmate Pattern'),
        ('defense', 'Defense'),
    ]
    
    THEME_CHOICES = [
        ('fork', 'Fork'),
        ('pin', 'Pin'),
        ('skewer', 'Skewer'),
        ('discovery', 'Discovered Attack'),
        ('double_check', 'Double Check'),
        ('sacrifice', 'Sacrifice'),
        ('back_rank', 'Back Rank'),
        ('deflection', 'Deflection'),
        ('decoy', 'Decoy'),
        ('overloading', 'Overloading'),
        ('zwischenzug', 'Zwischenzug'),
        ('mate_in_1', 'Mate in 1'),
        ('mate_in_2', 'Mate in 2'),
        ('mate_in_3', 'Mate in 3+'),
        ('endgame_basic', 'Basic Endgame'),
        ('endgame_advanced', 'Advanced Endgame'),
        ('mixed', 'Mixed'),
    ]

    # Puzzle identification
    external_id = models.CharField(max_length=50, unique=True, null=True, blank=True,
                                   help_text="External puzzle ID (e.g., from Lichess)")
    
    # Position and solution
    fen = models.CharField(max_length=200, help_text="Starting position in FEN notation")
    solution = models.JSONField(help_text="List of moves in UCI format, e.g., ['e2e4', 'd7d5', 'e4d5']")
    
    # Metadata
    title = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='', help_text="Puzzle objective description")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tactics')
    themes = models.JSONField(default=list, help_text="List of tactical themes")
    
    # Rating and popularity
    rating = models.IntegerField(default=1500, help_text="Puzzle difficulty rating")
    times_played = models.IntegerField(default=0)
    times_solved = models.IntegerField(default=0)
    average_time = models.FloatField(default=0.0, help_text="Average solve time in seconds")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Source game reference (optional)
    source_game = models.ForeignKey(
        'Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_puzzles',
        help_text="Original game this puzzle was derived from"
    )

    class Meta:
        db_table = 'games_puzzle'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['difficulty', 'category']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Puzzle #{self.id} ({self.difficulty} - {self.category})"

    def get_solve_rate(self):
        """Calculate puzzle solve rate as percentage"""
        if self.times_played == 0:
            return 0
        return round((self.times_solved / self.times_played) * 100, 1)

    def record_attempt(self, solved, time_spent):
        """Record a puzzle attempt"""
        self.times_played += 1
        if solved:
            self.times_solved += 1
        
        # Update average time
        if self.average_time == 0:
            self.average_time = time_spent
        else:
            # Weighted average
            self.average_time = (self.average_time * (self.times_played - 1) + time_spent) / self.times_played
        
        self.save()

    def get_objective(self):
        """Generate objective text based on solution"""
        if not self.solution:
            return "Find the best move"
        
        # Parse FEN to determine whose turn it is
        parts = self.fen.split(' ')
        to_move = 'White' if parts[1] == 'w' else 'Black'
        
        move_count = len(self.solution)
        
        # Generate objective based on themes
        themes = self.themes if self.themes else []
        
        if 'mate_in_1' in themes:
            return f"{to_move} to move and checkmate in 1"
        elif 'mate_in_2' in themes:
            return f"{to_move} to move and checkmate in 2"
        elif 'mate_in_3' in themes:
            return f"{to_move} to move and checkmate"
        elif 'fork' in themes:
            return f"{to_move} to move and win material with a fork"
        elif 'pin' in themes:
            return f"{to_move} to move and exploit the pin"
        elif self.category == 'endgame':
            return f"{to_move} to move in this endgame"
        else:
            return f"{to_move} to move and find the best continuation"


class PuzzleAttempt(models.Model):
    """Track user attempts on puzzles"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='puzzle_attempts'
    )
    puzzle = models.ForeignKey(
        Puzzle,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    
    # Attempt details
    solved = models.BooleanField(default=False)
    time_spent = models.FloatField(help_text="Time spent in seconds")
    moves_made = models.JSONField(default=list, help_text="List of moves attempted")
    hints_used = models.IntegerField(default=0)
    
    # Rating change (for puzzle rating system)
    rating_before = models.IntegerField(null=True, blank=True)
    rating_after = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'games_puzzleattempt'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'puzzle']),
            models.Index(fields=['user', 'solved']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        status = "✓" if self.solved else "✗"
        return f"{self.user.username} - Puzzle #{self.puzzle.id} {status}"


class UserPuzzleStats(models.Model):
    """User's overall puzzle statistics"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='puzzle_stats'
    )
    
    # Rating
    puzzle_rating = models.IntegerField(default=1500)
    highest_rating = models.IntegerField(default=1500)
    
    # Stats
    puzzles_attempted = models.IntegerField(default=0)
    puzzles_solved = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    total_time_spent = models.FloatField(default=0.0, help_text="Total time in seconds")
    
    # Category breakdown
    tactics_solved = models.IntegerField(default=0)
    endgame_solved = models.IntegerField(default=0)
    opening_solved = models.IntegerField(default=0)
    strategy_solved = models.IntegerField(default=0)
    
    # Last activity
    last_puzzle_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'games_userpuzzlestats'

    def __str__(self):
        return f"{self.user.username} - Puzzle Rating: {self.puzzle_rating}"

    def get_accuracy(self):
        """Calculate overall accuracy"""
        if self.puzzles_attempted == 0:
            return 0
        return round((self.puzzles_solved / self.puzzles_attempted) * 100, 1)

    def record_attempt(self, puzzle, solved, time_spent):
        """Update stats after a puzzle attempt"""
        self.puzzles_attempted += 1
        self.total_time_spent += time_spent
        self.last_puzzle_at = timezone.now()
        
        if solved:
            self.puzzles_solved += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
            
            # Update category stats
            category_field = f"{puzzle.category}_solved"
            if hasattr(self, category_field):
                setattr(self, category_field, getattr(self, category_field) + 1)
            
            # Update rating (simple Elo-like system)
            rating_diff = puzzle.rating - self.puzzle_rating
            k_factor = 32
            expected = 1 / (1 + 10 ** (-rating_diff / 400))
            self.puzzle_rating = int(self.puzzle_rating + k_factor * (1 - expected))
        else:
            self.current_streak = 0
            
            # Rating decrease on failure
            rating_diff = puzzle.rating - self.puzzle_rating
            k_factor = 32
            expected = 1 / (1 + 10 ** (-rating_diff / 400))
            self.puzzle_rating = int(self.puzzle_rating + k_factor * (0 - expected))
        
        # Update highest rating
        if self.puzzle_rating > self.highest_rating:
            self.highest_rating = self.puzzle_rating
        
        self.save()