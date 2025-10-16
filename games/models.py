# games/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import chess
import json
from .utils.timer_manager import TimerManager
from .utils.time_control import TimeManager, create_time_manager


class ChessManager:
    """Manager class for chess platform data initialization and management"""
    
    @staticmethod
    def create_default_time_controls():
        """Create standard time controls used in professional chess"""
        defaults = [
            # Bullet (< 3 minutes)
            {'name': 'Bullet 1+0', 'category': 'bullet', 'initial_time': 60, 'increment': 0, 
             'description': 'Ultra-fast games for quick thinking'},
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

            # Rapid (10-60 minutes)
            {'name': 'Rapid 10+0', 'category': 'rapid', 'initial_time': 600, 'increment': 0,
             'description': 'Quick rapid games'},
            {'name': 'Rapid 10+5', 'category': 'rapid', 'initial_time': 600, 'increment': 5,
             'description': 'Popular rapid format with increment'},
            {'name': 'Rapid 15+10', 'category': 'rapid', 'initial_time': 900, 'increment': 10,
             'description': 'Tournament-style rapid'},

            # Classical (> 60 minutes)
            {'name': 'Classical 30+0', 'category': 'classical', 'initial_time': 1800, 'increment': 0,
             'description': 'Classical time control'},
            {'name': 'Classical 30+30', 'category': 'classical', 'initial_time': 1800, 'increment': 30,
             'description': 'FIDE-style classical with increment'},
            {'name': 'Classical 90+30', 'category': 'classical', 'initial_time': 5400, 'increment': 30,
             'description': 'Long classical games'},
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
            {'name': 'First Victory', 'description': 'Win your first game', 
             'category': 'milestone', 'condition': 'games_won >= 1', 'points': 10, 'icon': '🎯'},
            {'name': 'Veteran Player', 'description': 'Play 100 games', 
             'category': 'milestone', 'condition': 'total_games >= 100', 'points': 50, 'icon': '🏆'},
            {'name': 'Chess Master', 'description': 'Play 1000 games', 
             'category': 'milestone', 'condition': 'total_games >= 1000', 'points': 200, 'icon': '👑'},
            
            # Rating Achievements
            {'name': 'Rising Star', 'description': 'Reach 1400 rating', 
             'category': 'rating', 'condition': 'rapid_rating >= 1400', 'points': 25, 'icon': '⭐'},
            {'name': 'Strong Player', 'description': 'Reach 1600 rating', 
             'category': 'rating', 'condition': 'rapid_rating >= 1600', 'points': 50, 'icon': '💪'},
            {'name': 'Expert Level', 'description': 'Reach 1800 rating', 
             'category': 'rating', 'condition': 'rapid_rating >= 1800', 'points': 100, 'icon': '🎓'},
            {'name': 'Master Level', 'description': 'Reach 2000 rating', 
             'category': 'rating', 'condition': 'rapid_rating >= 2000', 'points': 200, 'icon': '🥇'},
            
            # Streak Achievements
            {'name': 'Win Streak', 'description': 'Win 5 games in a row', 
             'category': 'streak', 'condition': 'current_win_streak >= 5', 'points': 30, 'icon': '🔥'},
            {'name': 'Unstoppable', 'description': 'Win 10 games in a row', 
             'category': 'streak', 'condition': 'current_win_streak >= 10', 'points': 75, 'icon': '⚡'},
            
            # Special Achievements
            {'name': 'Speed Demon', 'description': 'Win 50 blitz games', 
             'category': 'special', 'condition': 'blitz_games >= 50', 'points': 40, 'icon': '💨'},
            {'name': 'Puzzle Solver', 'description': 'Solve 100 puzzles', 
             'category': 'puzzle', 'condition': 'puzzles_solved >= 100', 'points': 35, 'icon': '🧩'},
        ]

        created_count = 0
        for ach_data in defaults:
            achievement, created = Achievement.objects.get_or_create(
                name=ach_data['name'],
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

    # ================== PROFESSIONAL TIMER INTEGRATION ==================

    def get_timer_manager(self):
        """Get professional TimerManager instance for this game"""
        if not hasattr(self, '_timer_manager'):
            # Map time control string to TimerManager format
            time_control_map = {
                'bullet': 'bullet_1',
                'blitz': 'blitz_5',
                'rapid': 'rapid_10',
                'classical': 'classical_60'
            }
            
            timer_control = time_control_map.get(self.time_control, 'rapid_10')
            self._timer_manager = TimerManager(timer_control)
            
            # Initialize with current game state
            if self.status == 'active':
                self._timer_manager.white_time = self.white_time_left
                self._timer_manager.black_time = self.black_time_left
                self._timer_manager.current_turn = self.get_current_player_color()
                self._timer_manager.game_started = True
                
                # CRITICAL FIX: Set last_move_time for existing active games
                # Use the most recent move time or current time if no moves
                if self.moves.exists():
                    latest_move = self.moves.latest('created_at')
                    self._timer_manager.last_move_time = latest_move.created_at.timestamp()
                else:
                    # No moves yet, use current time to start countdown
                    import time
                    self._timer_manager.last_move_time = time.time()
                
        return self._timer_manager

    def get_bot_time_manager(self, bot_rating=1500):
        """Get professional TimeManager for bot thinking time"""
        if not hasattr(self, '_bot_time_manager'):
            self._bot_time_manager = create_time_manager(bot_rating)
        return self._bot_time_manager

    def start_professional_timer(self):
        """Start the professional timer system"""
        timer = self.get_timer_manager()
        timer_state = timer.start_game()
        
        # Update game model with timer state
        self.white_time_left = timer_state['white_time'] or 600
        self.black_time_left = timer_state['black_time'] or 600
        self.status = 'active'
        self.last_move_at = timezone.now()
        self.save()
        
        return timer_state

    def make_timer_move(self, player_color):
        """Professional move timing with TimerManager"""
        timer = self.get_timer_manager()
        timer_state = timer.make_move(player_color)
        
        # Update model with new timer state
        self.white_time_left = timer_state['white_time'] or 0
        self.black_time_left = timer_state['black_time'] or 0
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
                    import logging
                    logger = logging.getLogger(__name__)
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
            import logging
            logger = logging.getLogger(__name__)
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
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Game {self.id} ended due to timeout: {timeout_player} player timed out, {winner.username if winner else 'None'} wins")
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
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
