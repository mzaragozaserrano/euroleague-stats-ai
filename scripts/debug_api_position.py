import asyncio
import logging
from euroleague_api.player_stats import PlayerStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_api_response():
    player_stats = PlayerStats(competition="E")
    df = player_stats.get_player_stats_single_season(
        endpoint='traditional',
        season=2025,
        statistic_mode='Accumulated'
    )
    
    if df is not None and not df.empty:
        print("Columns:", df.columns.tolist())
        print("\nFirst 5 records (Position related columns):")
        # Print columns that might contain position info
        cols = [c for c in df.columns if 'os' in c.lower() or 'pos' in c.lower()]
        print(df[cols].head())
        print("\nFirst 5 records (Full):")
        print(df.head())
    else:
        print("No data returned")

if __name__ == "__main__":
    debug_api_response()

