from euroleague_api.player_stats import PlayerStats
from euroleague_api.team_stats import TeamStats

print("PlayerStats instance methods:")
p = PlayerStats(competition="E")
print([m for m in dir(p) if not m.startswith('_')])

print("\nTeamStats instance methods:")
t = TeamStats(competition="E")
print([m for m in dir(t) if not m.startswith('_')])
