from rest_framework import serializers
from .models import Game, Move, GameInvitation, TimeControl


class MoveSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)

    class Meta:
        model = Move
        fields = [
            'id', 'game', 'move_number', 'player', 'player_username',
            'from_square', 'to_square', 'notation', 'fen_after_move', 'created_at'
        ]
        # Mark all auto-filled fields as read-only so they aren't required in input
        read_only_fields = [
            'id', 'created_at', 'player_username',
            'game', 'player', 'move_number', 'notation', 'fen_after_move'
        ]


class GameSerializer(serializers.ModelSerializer):
    white_player_username = serializers.CharField(source='white_player.username', read_only=True)
    black_player_username = serializers.CharField(source='black_player.username', read_only=True)
    white_player_rating = serializers.SerializerMethodField()
    black_player_rating = serializers.SerializerMethodField()
    moves = MoveSerializer(many=True, read_only=True)
    
    def get_white_player_rating(self, obj):
        """Extract rating from white player username if it's a computer"""
        if obj.white_player and 'computer' in obj.white_player.username.lower():
            parts = obj.white_player.username.split('_')
            if len(parts) >= 3 and parts[-1].isdigit():
                return int(parts[-1])
        return None
    
    def get_black_player_rating(self, obj):
        """Extract rating from black player username if it's a computer"""
        if obj.black_player and 'computer' in obj.black_player.username.lower():
            parts = obj.black_player.username.split('_')
            if len(parts) >= 3 and parts[-1].isdigit():
                return int(parts[-1])
        return None

    class Meta:
        model = Game
        fields = [
            'id', 'white_player', 'white_player_username', 'white_player_rating',
            'black_player', 'black_player_username', 'black_player_rating',
            'status', 'fen', 'winner',
            'created_at', 'updated_at', 'moves'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'moves',
            'white_player', 'black_player',
            'white_player_username', 'black_player_username',
            'white_player_rating', 'black_player_rating'
        ]


class TimeControlSerializer(serializers.ModelSerializer):
    """Serializer for TimeControl model"""
    display_name = serializers.SerializerMethodField()
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    
    class Meta:
        model = TimeControl
        fields = ['id', 'name', 'category', 'initial_time', 'increment', 'description', 'display_name']
        read_only_fields = ['id']


class GameInvitationSerializer(serializers.ModelSerializer):
    """Serializer for GameInvitation model"""
    from_player_username = serializers.CharField(source='from_player.username', read_only=True)
    to_player_username = serializers.CharField(source='to_player.username', read_only=True)
    time_control_display = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    def get_time_control_display(self, obj):
        return obj.time_control.get_display_name() if obj.time_control else None
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    class Meta:
        model = GameInvitation
        fields = [
            'id', 'from_player', 'from_player_username', 
            'to_player', 'to_player_username',
            'time_control', 'time_control_display',
            'message', 'status', 'is_expired',
            'created_at', 'expires_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'from_player_username', 'to_player_username',
            'time_control_display', 'is_expired', 
            'created_at', 'responded_at'
        ]
