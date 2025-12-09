"""
Script para poblar embeddings iniciales del esquema en schema_embeddings.

Este script genera embeddings para metadatos del esquema (tablas, columnas, ejemplos SQL)
y los almacena en la base de datos para uso con RAG.

Uso:
    poetry run python scripts/init_schema_embeddings.py
"""

import asyncio
import logging
import os
from app.database import async_session_maker
from app.config import settings
from app.services.vectorization import VectorizationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Metadatos del esquema a vectorizar
SCHEMA_METADATA = [
    # Tablas principales
    {
        "content": "Table: teams - Stores Euroleague team information. Columns: id (UUID primary key), code (unique team code like 'RM', 'BAR'), name (full team name), logo_url (URL to team logo). Relationships: players.team_id -> teams.id"
    },
    {
        "content": "Table: players - Stores player information linked to teams. Columns: id (UUID primary key), team_id (foreign key to teams), player_code (unique code from Euroleague API), name (player full name), position (player position), season (string like 'E2025'). Relationships: player_season_stats.player_id -> players.id, players.team_id -> teams.id"
    },
    {
        "content": "Table: player_season_stats - Stores aggregated season statistics per player. Columns: id (UUID primary key), player_id (foreign key to players), season (string like 'E2025', 'E2024'), games_played (integer), points (float), rebounds (float), assists (float), steals (float), blocks (float), turnovers (float), threePointsMade (quoted column name, float), pir (Performance Index Rating, float). Use this table for season totals, averages, and leaderboards. Season values are STRINGS: 'E2022', 'E2023', 'E2024', 'E2025'."
    },
    {
        "content": "Table: games - Stores game/match information. Columns: id (UUID primary key), season (integer: 2022, 2023, 2024, 2025), round (round number), home_team_id (foreign key to teams), away_team_id (foreign key to teams), date (date), home_score (integer), away_score (integer). Relationships: games.home_team_id -> teams.id, games.away_team_id -> teams.id. Season values are INTEGERS: 2022, 2023, 2024, 2025."
    },
    {
        "content": "Table: player_game_stats - Stores box score statistics for each player per game. Columns: id, game_id (foreign key to games), player_id (foreign key to players), team_id (foreign key to teams), minutes, points, rebounds, assists, three_points_made, pir. Use this table ONLY for specific game details, not for season aggregates. Column names use snake_case: three_points_made (not threePointsMade)."
    },
    
    # Relaciones clave
    {
        "content": "Relationship: player_season_stats.player_id -> players.id - Links season statistics to players. Always JOIN player_season_stats with players to get player names."
    },
    {
        "content": "Relationship: players.team_id -> teams.id - Links players to their teams. Use this to filter players by team or get team names for players."
    },
    {
        "content": "Relationship: player_game_stats.player_id -> players.id - Links game-level statistics to players. Use this for box score queries."
    },
    {
        "content": "Relationship: player_game_stats.game_id -> games.id - Links game statistics to game metadata. Use this to filter stats by specific games or dates."
    },
    
    # Reglas importantes sobre temporadas
    {
        "content": "CRITICAL SEASON FORMAT: For players and player_season_stats tables, season is a STRING like 'E2025', 'E2024', 'E2023', 'E2022'. For games table, season is an INTEGER like 2025, 2024, 2023, 2022. Always use the correct format: p.season = 'E2025' for players, ps.season = 'E2025' for player_season_stats, g.season = 2025 for games."
    },
    {
        "content": "DEFAULT SEASON RULE: If user does NOT mention any season/year/temporada in their query, ALWAYS filter by CURRENT season: 'E2025' (for players/player_season_stats) or 2025 (for games). Example: 'puntos de Larkin' must include ps.season = 'E2025' in WHERE clause."
    },
    {
        "content": "SEASON CONVERSION: When user mentions a year like '2022' or '2025', convert to correct format: '2022' -> 'E2022' for players/player_season_stats or 2022 for games. 'temporada pasada' or 'last season' -> 'E2024' or 2024. 'esta temporada' or 'current season' -> 'E2025' or 2025."
    },
    
    # Ejemplos SQL
    {
        "content": "SQL Example: Get player points for current season - SELECT p.name AS Jugador, ps.points AS Puntos FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE p.name ILIKE '%Larkin%' AND ps.season = 'E2025';"
    },
    {
        "content": "SQL Example: Get top scorers - SELECT p.name AS Jugador, ps.points AS Puntos FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE ps.season = 'E2025' ORDER BY ps.points DESC LIMIT 10;"
    },
    {
        "content": "SQL Example: Get players from a team - SELECT p.name AS Jugador FROM players p JOIN teams t ON p.team_id = t.id WHERE t.name ILIKE '%Real Madrid%' AND p.season = 'E2025' ORDER BY p.name;"
    },
    {
        "content": "SQL Example: Compare two players - SELECT p.name AS Jugador, ps.points AS Puntos, ps.assists AS Asistencias, ps.rebounds AS Rebotes FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE (p.name ILIKE '%Larkin%' OR p.name ILIKE '%Micic%') AND ps.season = 'E2025' ORDER BY ps.points DESC;"
    },
    {
        "content": "SQL Example: Compare seasons for a player - SELECT ps.season AS Temporada, ps.points AS Puntos, ps.assists AS Asistencias FROM player_season_stats ps JOIN players p ON p.id = ps.player_id WHERE p.name ILIKE '%Llull%' AND (ps.season = 'E2022' OR ps.season = 'E2025') ORDER BY ps.season;"
    },
    
    # Reglas de columnas
    {
        "content": "Column naming: In player_season_stats, use quoted column name for three-pointers: \"threePointsMade\" (camelCase, quoted). In player_game_stats, use snake_case: three_points_made (not quoted). Always alias columns with Spanish names: AS Puntos, AS Rebotes, AS Asistencias, AS Triples, AS Valoracion, AS Partidos, AS Jugador, AS Equipo."
    },
    {
        "content": "Column ambiguity: When joining players and teams tables, ALWAYS prefix 'name' column to avoid ambiguity: p.name AS Jugador, t.name AS Equipo. Never use just 'name' without table alias."
    },
    {
        "content": "Roster queries: When user asks for 'jugadores de [team]' or 'lista de jugadores', use p.season from players table (NOT ps.season), do NOT use LIMIT (return ALL players), only JOIN with teams table (NOT player_season_stats), ORDER BY p.name."
    },
    
    # Reglas de visualización
    {
        "content": "Visualization types: Use 'text' ONLY for single value results (1 row AND 1 column). Use 'table' for multi-row results (2+ rows) or single row with 2+ columns. Use 'bar', 'line', 'scatter' for comparative data or trends when explicitly requested."
    },
]


async def init_schema_embeddings():
    """
    Pobla la tabla schema_embeddings con embeddings del esquema.
    """
    try:
        # Verificar que OpenAI API key esté configurada
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY no está configurada. No se pueden generar embeddings.")
            logger.info("Configura OPENAI_API_KEY en tu archivo .env")
            return
        
        logger.info("Iniciando población de embeddings del esquema...")
        logger.info(f"Total de metadatos a vectorizar: {len(SCHEMA_METADATA)}")
        
        # Inicializar servicio de vectorización
        vectorization_service = VectorizationService(api_key=settings.openai_api_key)
        
        # Obtener sesión de BD
        async with async_session_maker() as session:
            # Verificar si ya hay embeddings
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM schema_embeddings"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                logger.warning(f"Ya existen {existing_count} embeddings en la BD.")
                response = input("¿Deseas limpiar y regenerar todos los embeddings? (s/n): ")
                if response.lower() == 's':
                    deleted = await vectorization_service.clear_schema_embeddings(session)
                    logger.info(f"Eliminados {deleted} embeddings existentes")
                else:
                    logger.info("Manteniendo embeddings existentes. Saliendo.")
                    return
            
            # Vectorizar y almacenar metadatos
            inserted_count = await vectorization_service.vectorize_schema_metadata(
                session=session,
                metadata=SCHEMA_METADATA
            )
            
            logger.info(f"✓ Embeddings inicializados exitosamente: {inserted_count} embeddings insertados")
            
    except Exception as e:
        logger.error(f"Error inicializando embeddings: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_schema_embeddings())

