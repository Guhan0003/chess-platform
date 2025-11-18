import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_backend.settings')
django.setup()

from games.models import Game
from django.contrib.auth import get_user_model

User = get_user_model()
aa = User.objects.get(username='aa')
aaa = User.objects.get(username='aaa')

print("=== CURRENT RATINGS ===")
print(f"aa:  Rapid={aa.rapid_rating}, Total Games={aa.total_games}")
print(f"aaa: Rapid={aaa.rapid_rating}, Total Games={aaa.total_games}")
print()

games = Game.objects.filter(
    white_player__in=[aa, aaa], 
    black_player__in=[aa, aaa]
).order_by('created_at')

print(f"=== GAMES FOUND: {games.count()} ===")
for g in games:
    # time_control might be a string or a model object
    if hasattr(g.time_control, 'category'):
        tc = g.time_control.category
    elif g.time_control:
        tc = str(g.time_control)
    else:
        tc = "None"
    
    print(f"Game {g.id}:")
    print(f"  Status: {g.status}")
    print(f"  Result: {g.result if g.result else 'None'}")
    print(f"  White: {g.white_player.username if g.white_player else 'None'}")
    print(f"  Black: {g.black_player.username if g.black_player else 'None'}")
    print(f"  Time Control: {tc}")
    print(f"  Winner: {g.winner.username if g.winner else 'None'}")
    print()
