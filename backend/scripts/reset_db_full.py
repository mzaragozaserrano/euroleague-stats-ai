import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def reset_db():
    print("Iniciando reset de BD...")
    async with async_session_maker() as s:
        # 1. Eliminar tablas existentes
        await s.execute(text('DROP TABLE IF EXISTS player_season_stats CASCADE'))
        await s.execute(text('DROP TABLE IF EXISTS players CASCADE'))
        await s.execute(text('DROP TABLE IF EXISTS teams CASCADE'))
        await s.commit()
        print("Tablas eliminadas.")
        
        # 2. Recrear tablas
        # Teams
        await s.execute(text("""
            CREATE TABLE teams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                logo_url TEXT,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )
        """))
        await s.execute(text('CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code)'))
        
        # Players
        await s.execute(text("""
            CREATE TABLE players (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                player_code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                position VARCHAR(50),
                season VARCHAR(10) NOT NULL,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )
        """))
        await s.execute(text('CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)'))
        await s.execute(text('CREATE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code)'))
        
        # Stats
        await s.execute(text("""
            CREATE TABLE player_season_stats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                season VARCHAR(10) NOT NULL,
                games_played INTEGER DEFAULT 0,
                points FLOAT DEFAULT 0.0,
                rebounds FLOAT DEFAULT 0.0,
                assists FLOAT DEFAULT 0.0,
                steals FLOAT DEFAULT 0.0,
                blocks FLOAT DEFAULT 0.0,
                turnovers FLOAT DEFAULT 0.0,
                "threePointsMade" FLOAT DEFAULT 0.0,
                pir FLOAT DEFAULT 0.0,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )
        """))
        await s.execute(text('CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_id ON player_season_stats(player_id)'))
        
        await s.commit()
        print("Tablas recreadas correctamente.")

if __name__ == "__main__":
    asyncio.run(reset_db())

