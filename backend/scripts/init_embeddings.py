"""
Script para inicializar embeddings de metadatos de esquema.

Este script:
1. Genera embeddings para descripciones de tablas, columnas y ejemplos SQL.
2. Los almacena en la tabla schema_embeddings de PostgreSQL.
3. Valida que se hayan insertado correctamente.

Uso:
    python backend/scripts/init_embeddings.py
    
Nota: Requiere variable de entorno DATABASE_URL y OPENAI_API_KEY configuradas.
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio del backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import async_session_maker
from app.services.vectorization import VectorizationService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Metadatos de esquema a vectorizar
SCHEMA_METADATA = [
    {
        "content": "Table: teams - Stores information about Euroleague basketball teams. "
        "Columns: id (primary key), code (team code like RMB), name (full team name), "
        "logo_url (URL to team logo)"
    },
    {
        "content": "Table: players - Stores player information linked to teams. "
        "Columns: id (primary key), team_id (foreign key to teams), name (player full name), "
        "position (G=Guard, F=Forward, C=Center), height (in meters), birth_date"
    },
    {
        "content": "Table: games - Stores game/match information. "
        "Columns: id (primary key), season (year), round (round number), "
        "home_team_id (foreign key), away_team_id (foreign key), date, home_score, away_score"
    },
    {
        "content": "Table: player_stats_games - Box score statistics for each player per game. "
        "Columns: id, game_id (foreign key), player_id (foreign key), team_id (foreign key), "
        "minutes, points, rebounds_total, assists, steals, blocks, turnovers, "
        "fg2_made, fg2_attempted, fg3_made, fg3_attempted, ft_made, ft_attempted, "
        "fouls_drawn, fouls_committed, pir (Performance Index Rating)"
    },
    {
        "content": "Column: points - Total points scored by a player in a game. "
        "Used for scoring queries and player performance analysis."
    },
    {
        "content": "Column: assists - Number of assists made by a player in a game. "
        "Used for playmaking analysis and player comparison."
    },
    {
        "content": "Column: rebounds_total - Total rebounds (offensive + defensive) in a game. "
        "Used for rebounding statistics and interior player evaluation."
    },
    {
        "content": "Column: fg3_made, fg3_attempted - Three-pointer statistics for a game. "
        "Used for three-point shooting analysis and perimeter player evaluation."
    },
    {
        "content": "Column: ft_made, ft_attempted - Free throw statistics for a game. "
        "Used for free throw percentage calculations and clutch performance analysis."
    },
    {
        "content": "Example SQL: To get all players from a specific team: "
        "SELECT name, position, height FROM players "
        "WHERE team_id = (SELECT id FROM teams WHERE code = 'RMB')"
    },
    {
        "content": "Example SQL: To get player scoring statistics: "
        "SELECT p.name, SUM(psg.points) as total_points, AVG(psg.points) as avg_points "
        "FROM player_stats_games psg "
        "JOIN players p ON psg.player_id = p.id "
        "GROUP BY p.name ORDER BY total_points DESC"
    },
    {
        "content": "Example SQL: To compare two players' points in the same game: "
        "SELECT p1.name, p2.name, psg1.points as p1_points, psg2.points as p2_points "
        "FROM player_stats_games psg1 "
        "JOIN player_stats_games psg2 ON psg1.game_id = psg2.game_id "
        "JOIN players p1 ON psg1.player_id = p1.id "
        "JOIN players p2 ON psg2.player_id = p2.id "
        "WHERE p1.name ILIKE '%Larkin%' AND p2.name ILIKE '%Micic%'"
    },
    {
        "content": "Example SQL: To calculate free throw percentage: "
        "SELECT p.name, "
        "CAST(SUM(psg.ft_made) AS FLOAT) / NULLIF(SUM(psg.ft_attempted), 0) * 100 as ft_percentage "
        "FROM player_stats_games psg "
        "JOIN players p ON psg.player_id = p.id "
        "GROUP BY p.name ORDER BY ft_percentage DESC"
    },
    {
        "content": "Example SQL: To get player performance by team and season: "
        "SELECT p.name, t.name as team, g.season, "
        "COUNT(*) as games_played, SUM(psg.points) as total_points, "
        "AVG(psg.points) as avg_points, SUM(psg.assists) as total_assists "
        "FROM player_stats_games psg "
        "JOIN players p ON psg.player_id = p.id "
        "JOIN teams t ON psg.team_id = t.id "
        "JOIN games g ON psg.game_id = g.id "
        "GROUP BY p.id, p.name, t.id, t.name, g.season "
        "ORDER BY g.season DESC, avg_points DESC"
    },
    {
        "content": "Schema relationship: players belong to teams through team_id foreign key. "
        "Games reference home and away teams. Player stats are recorded per game and player."
    },
    {
        "content": "RAG Usage: This schema_embeddings table is used to retrieve relevant table "
        "and column definitions when processing natural language queries to SQL translation. "
        "The system performs cosine similarity search on embeddings."
    },
]


async def init_embeddings() -> bool:
    """
    Ejecuta la inicialización de embeddings.

    Returns:
        True si fue exitoso, False en caso contrario.
    """
    try:
        # Validar variables de entorno
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY no está configurada en variables de entorno")
            return False

        logger.info("Iniciando proceso de vectorización de metadatos de esquema...")
        logger.info(f"Base de datos: {settings.database_url}")

        # Crear servicio de vectorización
        vectorization_service = VectorizationService(api_key=settings.openai_api_key)

        # Conectar a la base de datos e insertar embeddings
        async with async_session_maker() as session:
            # Limpiar embeddings anteriores (para reinicio)
            logger.info("Limpiando embeddings anteriores...")
            await vectorization_service.clear_schema_embeddings(session)

            # Vectorizar metadatos
            logger.info(f"Vectorizando {len(SCHEMA_METADATA)} items de metadatos...")
            inserted_count = await vectorization_service.vectorize_schema_metadata(
                session, SCHEMA_METADATA
            )

            logger.info(f"Se insertaron exitosamente {inserted_count} embeddings")

            # Validar que se pueden recuperar
            logger.info("Validando recuperación de embeddings...")
            test_query = "puntos de jugadores"
            retrieved = await vectorization_service.retrieve_relevant_schema(
                session, test_query, limit=3
            )

            logger.info(f"Recuperados {len(retrieved)} resultados para query de prueba:")
            for item in retrieved:
                logger.info(f"  - Similitud: {item['similarity']:.4f} | {item['content'][:60]}...")

        logger.info("Inicialización de embeddings completada exitosamente")
        return True

    except Exception as e:
        logger.error(f"Error durante inicialización de embeddings: {e}")
        return False


async def main():
    """Punto de entrada del script."""
    success = await init_embeddings()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

