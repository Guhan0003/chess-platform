from rest_framework import serializers
from .models import Game, Move


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
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            'id', 'white_player', 'white_player_username',
            'black_player', 'black_player_username',
            'status', 'fen', 'winner',
            'created_at', 'updated_at', 'moves'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'moves',
            'white_player', 'black_player',
            'white_player_username', 'black_player_username'
        ]
