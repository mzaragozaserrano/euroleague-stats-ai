import asyncio
import logging
from euroleague_api.boxscore_data import BoxScoreData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_boxscore_response():
    boxscore = BoxScoreData(competition="E")
    # Fetch stats for 2025 season
    df = boxscore.get_player_boxscore_stats_single_season(season=2025)
    
    if df is not None and not df.empty:
        print("Columns:", df.columns.tolist())
        print("\nFirst 5 records (Position related columns):")
        cols = [c for c in df.columns if 'os' in c.lower() or 'pos' in c.lower()]
        if cols:
            print(df[cols].head())
        else:
            print("No position columns found.")
            
        print("\nSample row:")
        print(df.iloc[0])
    else:
        print("No data returned")

if __name__ == "__main__":
    debug_boxscore_response()

