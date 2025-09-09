from django.contrib import admin
from .models import Game, Move


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'white_player', 'black_player', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('white_player__username', 'black_player__username')


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'move_number', 'player', 'notation', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('notation', 'player__username')
