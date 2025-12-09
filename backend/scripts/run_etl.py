"""
Script orquestador ETL: Ejecuta todos los ETLs en orden correcto.

Orden de ejecución:
1. ingest_teams.py - Crear/actualizar equipos
2. ingest_players.py - Crear/actualizar jugadores
3. ingest_player_season_stats.py - Crear/actualizar estadísticas

Se ejecuta diariamente a las 7 AM UTC via GitHub Actions.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Importar scripts ETL
from etl.ingest_teams import run_ingest_teams
from etl.ingest_players import run_ingest_players
from etl.ingest_player_season_stats import run_ingest_player_season_stats
from etl.ingest_games import run_ingest_games
from etl.ingest_boxscores import run_ingest_boxscores

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_all_etl(season: int = 2025):
    """
    Ejecuta todo el pipeline ETL en orden correcto.
    
    Args:
        season: Temporada a procesar (default: 2025).
    """
    try:
        logger.info("=" * 80)
        logger.info(f"INICIANDO ETL PIPELINE - {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)
        
        # Paso 1: Ingerir equipos
        logger.info("\n[1/5] Ingestando equipos...")
        await run_ingest_teams(season=season)
        logger.info("✓ Equipos completados")
        
        # Paso 2: Ingerir jugadores
        logger.info("\n[2/5] Ingestando jugadores...")
        await run_ingest_players(season=season)
        logger.info("✓ Jugadores completados")
        
        # Paso 3: Ingerir partidos
        logger.info("\n[3/5] Ingestando partidos (Games)...")
        await run_ingest_games(seasons=[season])
        logger.info("✓ Partidos completados")

        # Paso 4: Ingerir estadísticas de temporada
        logger.info("\n[4/5] Ingestando estadísticas de temporada...")
        await run_ingest_player_season_stats(season=season)
        logger.info("✓ Estadísticas temporada completadas")

        # Paso 5: Ingerir boxscores
        logger.info("\n[5/5] Ingestando Box Scores...")
        await run_ingest_boxscores(seasons=[season])
        logger.info("✓ Box Scores completados")
        
        logger.info("\n" + "=" * 80)
        logger.info(f"ETL PIPELINE COMPLETADO EXITOSAMENTE - {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error(f"ERROR EN ETL PIPELINE: {e}")
        logger.error("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    # Opcionalmente aceptar season como argumento
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    asyncio.run(run_all_etl(season=season))

