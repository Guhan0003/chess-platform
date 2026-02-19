# accounts/friends_views.py
"""
API views for the Friends system.
Handles friend requests, friend list, and real-time status updates.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Friendship, FriendRequest

User = get_user_model()
   

# =================================
# Helper Functions
# =================================

def generate_unique_id_for_user(user):
    """Generate and save a unique ID for a user if they don't have one"""
    if user.unique_id:
        return user.unique_id
    
    import string
    import random
    
    chars = string.ascii_uppercase + string.digits
    # Remove easily confused characters
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '').replace('L', '')
    
    max_attempts = 100
    for _ in range(max_attempts):
        code = ''.join(random.choices(chars, k=8))
        formatted_code = f"{code[:4]}-{code[4:]}"
        if not User.objects.filter(unique_id=formatted_code).exists():
            user.unique_id = formatted_code
            user.save(update_fields=['unique_id'])
            return formatted_code
    
    # Fallback: use user ID
    fallback_code = f"USER-{user.id:04d}"
    user.unique_id = fallback_code
    user.save(update_fields=['unique_id'])
    return fallback_code


def serialize_user_basic(user, include_status=True):
    """Serialize a user for friend-related responses"""
    data = {
        'id': user.id,
        'username': user.username,
        'avatar_url': user.avatar.url if user.avatar else None,
        'unique_id': generate_unique_id_for_user(user),
        'rapid_rating': user.rapid_rating,
        'rating': user.rapid_rating,  # Alias for convenience
    }
    
    if include_status:
        data['is_online'] = user.is_online
        data['status'] = get_user_status(user)
        data['last_seen'] = user.last_activity.isoformat() if user.last_activity else None
    
    return data


def get_user_status(user):
    """Get the current status of a user (online, playing, offline)"""
    if not user.is_online:
        return 'offline'
    
    # Check if user is in an active game
    try:
        from games.models import Game
        active_game = Game.objects.filter(
            Q(white_player=user) | Q(black_player=user),
            status='in_progress'
        ).first()
        
        if active_game:
            return 'playing'
    except:
        pass
    
    return 'online'


def get_user_active_game(user):
    """Get the user's active game if any"""
    try:
        from games.models import Game
        active_game = Game.objects.filter(
            Q(white_player=user) | Q(black_player=user),
            status='in_progress'
        ).first()
        
        if active_game:
            return {
                'game_id': active_game.id,
                'game_public': True  # You can add privacy settings later
            }
    except:
        pass
    
    return {'game_id': None, 'game_public': False}


# =================================
# Friends List API
# =================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends_list(request):
    """
    Get the authenticated user's friends list with status information.
    
    Returns:
        List of friends with username, avatar, rating, and online status
    """
    user = request.user
    friends = Friendship.get_friends(user)
    
    friends_data = []
    for friend in friends:
        friend_data = serialize_user_basic(friend, include_status=True)
        
        # Add active game info if playing
        if friend_data['status'] == 'playing':
            game_info = get_user_active_game(friend)
            friend_data.update(game_info)
        
        friends_data.append(friend_data)
    
    # Sort: online first, then playing, then offline
    status_order = {'online': 0, 'playing': 1, 'offline': 2}
    friends_data.sort(key=lambda x: status_order.get(x.get('status', 'offline'), 2))
    
    return Response(friends_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends_status(request):
    """
    Get status updates for all friends (for polling fallback).
    
    Returns:
        List of friend statuses
    """
    user = request.user
    friends = Friendship.get_friends(user)
    
    statuses = []
    for friend in friends:
        status_data = {
            'user_id': friend.id,
            'status': get_user_status(friend),
        }
        
        if status_data['status'] == 'playing':
            game_info = get_user_active_game(friend)
            status_data.update(game_info)
        
        statuses.append(status_data)
    
    return Response(statuses)


# =================================
# Friend Request API
# =================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    """
    Send a friend request to another user.
    
    Body:
        to_user_id: ID of the user to send request to
        message: Optional message (max 200 chars)
    
    Returns:
        The created friend request
    """
    user = request.user
    to_user_id = request.data.get('to_user_id')
    message = request.data.get('message', '')
    
    if not to_user_id:
        return Response(
            {'error': 'to_user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get target user
    try:
        to_user = User.objects.get(id=to_user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validation
    if to_user.id == user.id:
        return Response(
            {'error': 'Cannot send friend request to yourself'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if Friendship.are_friends(user, to_user):
        return Response(
            {'error': 'Already friends with this user'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if FriendRequest.has_pending_request(user, to_user):
        return Response(
            {'error': 'A pending friend request already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create request
    friend_request = FriendRequest.objects.create(
        from_user=user,
        to_user=to_user,
        message=message[:200] if message else None
    )
    
    return Response({
        'id': friend_request.id,
        'to_user': serialize_user_basic(to_user, include_status=False),
        'message': friend_request.message,
        'created_at': friend_request.created_at.isoformat(),
        'status': friend_request.status
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_requests(request):
    """
    Get all pending friend requests received by the authenticated user.
    """
    user = request.user
    pending = FriendRequest.get_pending_for_user(user).select_related('from_user')
    
    requests_data = []
    for req in pending:
        requests_data.append({
            'id': req.id,
            'from_user': serialize_user_basic(req.from_user, include_status=False),
            'message': req.message,
            'created_at': req.created_at.isoformat()
        })
    
    return Response(requests_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sent_requests(request):
    """
    Get all pending friend requests sent by the authenticated user.
    """
    user = request.user
    sent = FriendRequest.get_sent_by_user(user).select_related('to_user')
    
    requests_data = []
    for req in sent:
        requests_data.append({
            'id': req.id,
            'to_user': serialize_user_basic(req.to_user, include_status=False),
            'message': req.message,
            'created_at': req.created_at.isoformat()
        })
    
    return Response(requests_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_friend_request(request, request_id):
    """
    Accept a friend request.
    """
    user = request.user
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=user,
            status='pending'
        )
    except FriendRequest.DoesNotExist:
        return Response(
            {'error': 'Friend request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        friend_request.accept()
        return Response({
            'message': 'Friend request accepted',
            'friend': serialize_user_basic(friend_request.from_user)
        })
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_friend_request(request, request_id):
    """
    Reject a friend request.
    """
    user = request.user
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=user,
            status='pending'
        )
    except FriendRequest.DoesNotExist:
        return Response(
            {'error': 'Friend request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        friend_request.reject()
        return Response({'message': 'Friend request rejected'})
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_friend_request(request, request_id):
    """
    Cancel a sent friend request.
    """
    user = request.user
    
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            from_user=user,
            status='pending'
        )
    except FriendRequest.DoesNotExist:
        return Response(
            {'error': 'Friend request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        friend_request.cancel()
        return Response({'message': 'Friend request cancelled'})
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# =================================
# Friend Management API
# =================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_friend(request, friend_id):
    """
    Remove a friend.
    """
    user = request.user
    
    try:
        friend = User.objects.get(id=friend_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not Friendship.are_friends(user, friend):
        return Response(
            {'error': 'Not friends with this user'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    Friendship.remove_friendship(user, friend)
    
    return Response({'message': 'Friend removed successfully'})


# =================================
# Find by Unique ID API
# =================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def find_user_by_unique_id(request):
    """
    Find a user by their unique friend ID.
    
    Query params:
        unique_id: The unique ID to search for
    """
    unique_id = request.query_params.get('unique_id', '').upper().strip()
    
    if not unique_id:
        return Response(
            {'error': 'unique_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Support both formats: XXXX-XXXX and XXXXXXXX
    if len(unique_id) == 8 and '-' not in unique_id:
        unique_id = f"{unique_id[:4]}-{unique_id[4:]}"
    
    try:
        user = User.objects.get(unique_id=unique_id)
        return Response(serialize_user_basic(user))
    except User.DoesNotExist:
        return Response(
            {'error': 'No user found with this ID'},
            status=status.HTTP_404_NOT_FOUND
        )


# =================================
# Online Players API
# =================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_online_players(request):
    """
    Get list of online players (excluding current user).
    Used for the Online Players section in lobby.
    
    Query params:
        limit: Max number of players to return (default: 20)
    """
    user = request.user
    limit = min(int(request.query_params.get('limit', 20)), 100)
    
    online_users = User.objects.filter(
        is_online=True
    ).exclude(
        id=user.id
    ).order_by('-last_activity')[:limit]
    
    players_data = []
    for player in online_users:
        player_data = {
            'id': player.id,
            'username': player.username,
            'avatar_url': player.avatar.url if player.avatar else None,
            'rating': player.rapid_rating,
            'status': get_user_status(player),
        }
        
        # Check if they're friends
        player_data['is_friend'] = Friendship.are_friends(user, player)
        
        players_data.append(player_data)
    
    return Response(players_data)
