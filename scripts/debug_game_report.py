import asyncio
import logging
from euroleague_api.game_stats import GameStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_game_report():
    game_stats = GameStats(competition="E")
    # Try getting report for a specific game (e.g. game code 1, season 2025)
    try:
        df = game_stats.get_game_report(season=2025, game_code=1)
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.head())
        else:
            print("No data")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_game_report()

