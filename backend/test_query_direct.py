"""
Script de prueba directo para verificar el servicio de text-to-sql
"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.text_to_sql import TextToSQLService


async def test_query():
    """Probar una consulta"""
    service = TextToSQLService(api_key=settings.openrouter_api_key)
    
    query = "¿Cuál es el máximo anotador de esta temporada?"
    schema_context = """
TABLES:
- teams (id, code, name, logo_url): Equipos de Euroleague.
- players (id, team_id, name, position): Jugadores y su equipo.
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score): Partidos jugados. SEASON values are integers: 2023, 2024, 2025.
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds_total, assists, fg3_made, pir): Estadisticas de jugador por partido.

KEY RELATIONSHIPS:
- player_stats_games.player_id -> players.id
- player_stats_games.game_id -> games.id
- players.team_id -> teams.id
- games.home_team_id, away_team_id -> teams.id

IMPORTANT - Season values are always INTEGERS (2023, 2024, 2025), NEVER strings like 'current'.
"""
    
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    
    sql, viz, error = await service.generate_sql(query, schema_context)
    
    if error:
        print(f"ERROR: {error}")
    else:
        print(f"\nSQL Generado:")
        print(f"{sql}")
        print(f"\nVisualización: {viz}")
        
        # Verificar si contiene 2022
        if "2022" in sql:
            print("\n⚠️  PROBLEMA: SQL sigue conteniendo año 2022")
        else:
            print("\n✅ OK: SQL NO contiene año 2022")


if __name__ == "__main__":
    asyncio.run(test_query())

