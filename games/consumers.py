"""
WebSocket consumers for real-time chess gameplay.
Handles game state synchronization, move updates, and timer management.
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .models import Game, Move
import chess
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class GameConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chess game communication.
    
    Handles:
    - Game state synchronization
    - Real-time move updates
    - Timer synchronization
    - Player connection status
    - Game events (check, checkmate, etc.)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_id = None
        self.game_group_name = None
        self.user = None
        self.player_color = None
        print(f"🔧 GameConsumer initialized")  # Debug print
        
    async def connect(self):
        """Handle WebSocket connection."""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        
        # Authenticate user
        self.user = await self.get_user_from_token()
        
        # Get game and verify access
        game = await self.get_game()
        if not game:
            print(f"❌ WebSocket connection rejected: Game {self.game_id} not found")
            await self.close(code=4004)
            return
            
        # Check if user is a player in this game (allow anonymous for testing)
        if not self.user.is_anonymous:
            if not await self.is_player_in_game(self.user, game):
                print(f"❌ WebSocket connection rejected: User {self.user.username} not in game {self.game_id}")
                await self.close(code=4003)
                return
            self.player_color = await self.get_player_color(self.user, game)
        else:
            # For testing purposes, allow anonymous connections
            print(f"⚠️ Anonymous WebSocket connection to game {self.game_id} (testing mode)")
            self.user = AnonymousUser()
            self.player_color = 'white'  # Default for testing
        
        # Join game group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_success',
            'message': 'WebSocket connected successfully!',
            'game_id': self.game_id,
            'player_color': self.player_color
        }))
        
        # Notify other players
        if not self.user.is_anonymous:
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_connected',
                    'player': self.user.username,
                    'color': self.player_color
                }
            )
        
        logger.info(f"WebSocket connected to game {self.game_id} - User: {self.user.username if not self.user.is_anonymous else 'Anonymous'}")
        print(f"🚀 WebSocket connected to game {self.game_id} - User: {self.user.username if not self.user.is_anonymous else 'Anonymous'}")  # Add console print

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.game_group_name:
            # Notify other players that this player disconnected
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_disconnected',
                    'player': self.user.username if self.user else 'Unknown',
                    'color': self.player_color
                }
            )
            
            # Leave game group
            await self.channel_layer.group_discard(
                self.game_group_name,
                self.channel_name
            )
            
        logger.info(f"Player disconnected from game {self.game_id}")

    async def receive(self, text_data):
        """Handle received WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'make_move':
                await self.handle_make_move(data)
            elif message_type == 'request_game_state':
                await self.send_game_state()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error("Internal error")

    async def handle_make_move(self, data):
        """Handle move making requests."""
        try:
            from_square = data.get('from_square')
            to_square = data.get('to_square')
            promotion = data.get('promotion')
            
            if not from_square or not to_square:
                await self.send_error("Missing move data")
                return
            
            # Get current game state
            game = await self.get_game()
            if not game:
                await self.send_error("Game not found")
                return
                
            if game.status != 'active':
                await self.send_error("Game is not active")
                return
            
            # Verify it's player's turn
            board = chess.Board(game.fen)
            current_turn = 'white' if board.turn else 'black'
            
            if current_turn != self.player_color:
                await self.send_error("Not your turn")
                return
            
            # Validate and make move
            try:
                move = chess.Move.from_uci(f"{from_square}{to_square}{promotion or ''}")
                if move not in board.legal_moves:
                    await self.send_error("Illegal move")
                    return
                    
                # Calculate SAN notation before applying move
                san = board.san(move)
                
                # Apply move to board
                board.push(move)
                
                # Update game in database
                game = await self.update_game_state(game, board, move, from_square, to_square, promotion, san)
                
                # Broadcast move to all players in game IMMEDIATELY
                move_data = {
                    'type': 'move_made',
                    'move': {
                        'from_square': from_square,
                        'to_square': to_square,
                        'promotion': promotion,
                        'notation': san,
                        'player': self.user.username if not self.user.is_anonymous else 'Player',
                        'color': self.player_color
                    },
                    'game_state': await self.get_game_state_data(game, board)
                }
                
                print(f"📡 Broadcasting move: {from_square}→{to_square} to group {self.game_group_name}")
                
                await self.channel_layer.group_send(
                    self.game_group_name,
                    move_data
                )
                
                logger.info(f"Move made in game {self.game_id}: {from_square}-{to_square}")
                print(f"✅ Move broadcast complete: {from_square}→{to_square}")
                
            except ValueError as e:
                await self.send_error(f"Invalid move: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error making move: {e}")
            await self.send_error("Error making move")

    async def send_game_state(self):
        """Send current game state to this client."""
        game = await self.get_game()
        if game:
            board = chess.Board(game.fen)
            game_state = await self.get_game_state_data(game, board)
            
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'data': game_state
            }))

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Group message handlers
    async def move_made(self, event):
        """Handle move_made group message."""
        await self.send(text_data=json.dumps(event))

    async def player_connected(self, event):
        """Handle player_connected group message."""
        await self.send(text_data=json.dumps(event))

    async def player_disconnected(self, event):
        """Handle player_disconnected group message."""
        await self.send(text_data=json.dumps(event))

    async def timer_update(self, event):
        """Handle timer_update group message."""
        await self.send(text_data=json.dumps(event))

    async def game_finished(self, event):
        """Handle game_finished group message."""
        await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def get_user_from_token(self):
        """Extract user from JWT token in query string."""
        try:
            token = None
            query_string = self.scope.get('query_string', b'').decode()
            
            if query_string:
                # Parse query parameters
                params = {}
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
                token = params.get('token')
            
            if not token:
                print(f"⚠️ No token provided in WebSocket connection")
                return AnonymousUser()
            
            # Validate JWT token
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                from rest_framework_simplejwt.tokens import AccessToken
                
                # Validate the token
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                
                # Get user from database
                user = User.objects.get(id=user_id)
                print(f"✅ WebSocket authenticated user: {user.username}")
                return user
                
            except (InvalidToken, TokenError, User.DoesNotExist) as e:
                print(f"⚠️ WebSocket token validation failed: {e}")
                return AnonymousUser()
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            print(f"❌ WebSocket authentication error: {e}")
            return AnonymousUser()

    @database_sync_to_async
    def get_game(self):
        """Get game instance from database."""
        try:
            return Game.objects.get(id=self.game_id)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def is_player_in_game(self, user, game):
        """Check if user is a player in this game."""
        return game.white_player == user or game.black_player == user

    @database_sync_to_async
    def get_player_color(self, user, game):
        """Get player's color in the game."""
        if game.white_player == user:
            return 'white'
        elif game.black_player == user:
            return 'black'
        return None

    @database_sync_to_async
    def update_game_state(self, game, board, move, from_square, to_square, promotion, san):
        """Update game state in database after move."""
        # Update game FEN
        game.fen = board.fen()
        
        # Check for game end conditions
        if board.is_checkmate():
            game.status = 'finished'
            game.result = '1-0' if board.turn == chess.BLACK else '0-1'
            game.termination = 'checkmate'
            game.winner = game.white_player if game.result == '1-0' else game.black_player
        elif board.is_stalemate():
            game.status = 'finished'
            game.result = '1/2-1/2'
            game.termination = 'stalemate'
        elif board.is_insufficient_material():
            game.status = 'finished'
            game.result = '1/2-1/2'
            game.termination = 'insufficient_material'
        elif board.is_seventyfive_moves():
            game.status = 'finished'
            game.result = '1/2-1/2'
            game.termination = 'fifty_move_rule'
        elif board.is_fivefold_repetition():
            game.status = 'finished'
            game.result = '1/2-1/2'
            game.termination = 'threefold_repetition'
        
        game.save()
        
        # Create move record
        move_number = game.moves.count() + 1
        Move.objects.create(
            game=game,
            player=self.user if not self.user.is_anonymous else None,
            move_number=move_number,
            from_square=from_square,
            to_square=to_square,
            notation=san,  # Use the pre-calculated SAN notation
            fen_after_move=board.fen(),
            promotion_piece=promotion
        )
        
        return game

    @database_sync_to_async
    def get_game_state_data(self, game, board):
        """Get complete game state data."""
        moves = list(game.moves.all().values(
            'move_number', 'notation', 'from_square', 'to_square', 
            'player__username', 'created_at'
        ))
        
        return {
            'id': game.id,
            'fen': game.fen,
            'status': game.status,
            'result': game.result,
            'white_player': game.white_player.username if game.white_player else None,
            'black_player': game.black_player.username if game.black_player else None,
            'current_turn': 'white' if board.turn else 'black',
            'is_check': board.is_check(),
            'is_checkmate': board.is_checkmate(),
            'is_stalemate': board.is_stalemate(),
            'moves': moves,
            'white_time_left': getattr(game, 'white_time_left', 600),
            'black_time_left': getattr(game, 'black_time_left', 600),
        }


class TimerConsumer(AsyncWebsocketConsumer):
    """
    Dedicated consumer for game timer synchronization.
    Handles precise timer updates and time management.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_id = None
        self.timer_group_name = None
        self.timer_task = None
        
    def get_user_from_token(self):
        """Extract user from JWT token in query string."""
        try:
            token = None
            query_string = self.scope.get('query_string', b'').decode()
            
            if query_string:
                params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
                token = params.get('token')
            
            if not token:
                return AnonymousUser()
            
            # Validate JWT token
            try:
                UntypedToken(token)
                from rest_framework_simplejwt.authentication import JWTAuthentication
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                return user
            except Exception:
                return AnonymousUser()
        except Exception:
            return AnonymousUser()
    
    @database_sync_to_async
    def get_user_from_token_async(self):
        """Async version of get_user_from_token for timer consumer."""
        return self.get_user_from_token()
    
    @database_sync_to_async
    def get_game(self):
        """Get game object from database."""
        try:
            return Game.objects.get(id=self.game_id)
        except Game.DoesNotExist:
            return None
    
    @database_sync_to_async
    def is_player_in_game(self, user, game):
        """Check if user is a player in the game."""
        return user in [game.white_player, game.black_player]
        
    async def connect(self):
        """Handle timer WebSocket connection."""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.timer_group_name = f'timer_{self.game_id}'
        
        # Authenticate user for timer access (allow anonymous for testing)
        user = await self.get_user_from_token_async()
        
        # Verify game exists
        game = await self.get_game()
        if not game:
            print(f"❌ Timer WebSocket: Game {self.game_id} not found")
            await self.close(code=4004)  # Not Found
            return
            
        # For authenticated users, verify they're in the game
        if not user.is_anonymous and not await self.is_player_in_game(user, game):
            print(f"❌ Timer WebSocket: User {user.username} not in game {self.game_id}")
            await self.close(code=4003)  # Forbidden
            return
        
        # Join timer group
        await self.channel_layer.group_add(
            self.timer_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        print(f"🕐 Timer WebSocket connected to game {self.game_id}")
        
        # Send initial timer data
        timer_data = await self.get_timer_data(game)
        await self.send(text_data=json.dumps({
            'type': 'timer_tick',
            'data': timer_data
        }))
        
        # Start timer updates
        self.timer_task = asyncio.create_task(self.timer_loop())
        
    async def disconnect(self, close_code):
        """Handle timer WebSocket disconnection."""
        if self.timer_task:
            self.timer_task.cancel()
            
        if self.timer_group_name:
            await self.channel_layer.group_discard(
                self.timer_group_name,
                self.channel_name
            )
            
    async def timer_loop(self):
        """Main timer loop for sending periodic updates."""
        try:
            while True:
                game = await self.get_game()
                if game and game.status == 'active':
                    timer_data = await self.get_timer_data(game)
                    
                    await self.channel_layer.group_send(
                        self.timer_group_name,
                        {
                            'type': 'timer_tick',
                            'data': timer_data
                        }
                    )
                
                await asyncio.sleep(1)  # Update every second
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Timer loop error: {e}")
    
    async def timer_tick(self, event):
        """Handle timer tick group message."""
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def get_game(self):
        """Get game for timer updates."""
        try:
            return Game.objects.get(id=self.game_id)
        except ObjectDoesNotExist:
            return None
    
    @database_sync_to_async 
    def get_timer_data(self, game):
        """Get current timer data."""
        return {
            'white_time': getattr(game, 'white_time_left', 600),
            'black_time': getattr(game, 'black_time_left', 600),
            'current_turn': 'white' if chess.Board(game.fen).turn else 'black'
        }