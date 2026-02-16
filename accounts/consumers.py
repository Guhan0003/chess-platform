"""
WebSocket consumers for accounts/friends functionality.
Handles real-time friend status updates and notifications.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class FriendsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for friends system.
    Handles:
    - Online status updates
    - Friend request notifications
    - Real-time friend activity
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get('user')
        
        # Allow connection even for anonymous users (they just won't get personalized updates)
        if self.user and self.user.is_authenticated:
            self.user_group = f'friends_{self.user.id}'
            self.global_group = 'friends_global'
            
            # Join user-specific group
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )
            
            # Join global presence group
            await self.channel_layer.group_add(
                self.global_group,
                self.channel_name
            )
            
            # Update user's online status
            await self.update_user_status(True)
            
            # Notify friends that user is online
            await self.broadcast_status_change('online')
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user') and self.user and self.user.is_authenticated:
            # Update user's online status
            await self.update_user_status(False)
            
            # Notify friends that user is offline
            await self.broadcast_status_change('offline')
            
            # Leave groups
            if hasattr(self, 'user_group'):
                await self.channel_layer.group_discard(
                    self.user_group,
                    self.channel_name
                )
            
            if hasattr(self, 'global_group'):
                await self.channel_layer.group_discard(
                    self.global_group,
                    self.channel_name
                )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Keep-alive ping
                await self.send(text_data=json.dumps({'type': 'pong'}))
            
            elif message_type == 'status_update':
                # User manually updating their status
                status = data.get('status', 'online')
                await self.broadcast_status_change(status)
            
            elif message_type == 'get_online_friends':
                # Request list of online friends
                online_friends = await self.get_online_friends()
                await self.send(text_data=json.dumps({
                    'type': 'online_friends',
                    'friends': online_friends
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def friend_status_update(self, event):
        """Handle friend status update broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'friend_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status']
        }))
    
    async def friend_request_notification(self, event):
        """Handle friend request notification"""
        await self.send(text_data=json.dumps({
            'type': 'friend_request',
            'action': event['action'],
            'from_user': event.get('from_user'),
            'to_user': event.get('to_user'),
            'request_id': event.get('request_id')
        }))
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        """Update user's online status in database"""
        from accounts.models import CustomUser
        try:
            user = CustomUser.objects.get(id=self.user.id)
            user.is_online = is_online
            user.last_seen = timezone.now()
            user.save(update_fields=['is_online', 'last_seen'])
        except CustomUser.DoesNotExist:
            pass
    
    async def broadcast_status_change(self, status):
        """Broadcast status change to all friends"""
        if not hasattr(self, 'user') or not self.user or not self.user.is_authenticated:
            return
            
        # Broadcast to global group
        await self.channel_layer.group_send(
            self.global_group,
            {
                'type': 'friend_status_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': status
            }
        )
    
    @database_sync_to_async
    def get_online_friends(self):
        """Get list of online friends"""
        from accounts.models import Friendship
        
        if not self.user or not self.user.is_authenticated:
            return []
        
        # Get friendships where user is involved
        friendships = Friendship.objects.filter(
            user=self.user
        ).select_related('friend')
        
        online_friends = []
        for friendship in friendships:
            friend = friendship.friend
            if friend.is_online:
                online_friends.append({
                    'id': friend.id,
                    'username': friend.username,
                    'avatar': friend.avatar.url if friend.avatar else None,
                    'status': 'online'
                })
        
        return online_friends
