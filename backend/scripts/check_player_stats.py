"""Script rápido para verificar stats de un jugador."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import async_session_maker
from sqlalchemy import text

async def check():
    async with async_session_maker() as session:
        # Buscar el jugador encontrado
        result = await session.execute(text("""
            SELECT p.name, ps.points, ps.season, ps.games_played
            FROM players p
            JOIN player_season_stats ps ON p.id = ps.player_id
            WHERE p.name ILIKE '%FRANCISCO%SYLVAIN%' AND ps.season = 'E2025'
        """))
        rows = result.fetchall()
        print(f"Jugador encontrado: {rows}")
        
        # También probar con el nombre exacto
        result2 = await session.execute(text("""
            SELECT p.name, ps.points, ps.season
            FROM players p
            JOIN player_season_stats ps ON p.id = ps.player_id
            WHERE p.name = 'FRANCISCO, SYLVAIN' AND ps.season = 'E2025'
        """))
        rows2 = result2.fetchall()
        print(f"Con nombre exacto: {rows2}")

asyncio.run(check())

