"""
Script helper para ejecutar todos los ETLs en secuencia.

Uso:
    poetry run python scripts/run_all_etl.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.ingest_teams import ingest_teams
from etl.ingest_players import ingest_players
from etl.ingest_games import ingest_games, ingest_player_stats

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def run_all_etl():
    """Ejecutar todos los ETLs en el orden correcto."""
    
    results = {}
    
    try:
        # 1. Equipos
        logger.info("=" * 60)
        logger.info("PASO 1: Ingestando equipos...")
        logger.info("=" * 60)
        teams_result = await ingest_teams()
        results["teams"] = teams_result
        
        if teams_result.get("status") != "success":
            logger.error("Fallo en ingesta de equipos. Abortando.")
            return results
        
        # 2. Jugadores
        logger.info("=" * 60)
        logger.info("PASO 2: Ingestando jugadores...")
        logger.info("=" * 60)
        players_result = await ingest_players()
        results["players"] = players_result
        
        if players_result.get("status") != "success":
            logger.warning("Fallo en ingesta de jugadores. Continuando con partidos...")
        
        # 3. Partidos
        logger.info("=" * 60)
        logger.info("PASO 3: Ingestando partidos...")
        logger.info("=" * 60)
        games_result = await ingest_games()
        results["games"] = games_result
        
        if games_result.get("status") != "success":
            logger.warning("Fallo en ingesta de partidos. Continuando con estadísticas...")
        
        # 4. Estadísticas de jugadores
        logger.info("=" * 60)
        logger.info("PASO 4: Ingestando estadísticas de jugadores...")
        logger.info("=" * 60)
        stats_result = await ingest_player_stats()
        results["player_stats"] = stats_result
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("RESUMEN FINAL DE INGESTA")
        logger.info("=" * 60)
        
        for name, result in results.items():
            logger.info(f"{name.upper()}:")
            logger.info(f"  - Total procesados: {result.get('total_processed', 0)}")
            logger.info(f"  - Insertados: {result.get('inserted', 0)}")
            logger.info(f"  - Actualizados: {result.get('updated', 0)}")
            logger.info(f"  - Errores: {result.get('errors', 0)}")
            logger.info(f"  - Estado: {result.get('status', 'unknown')}")
            logger.info("")
        
        # Determinar éxito general
        all_success = all(
            r.get("status") == "success" for r in results.values()
        )
        
        if all_success:
            logger.info("✅ Todos los ETLs se ejecutaron exitosamente")
            return results
        else:
            logger.warning("⚠️ Algunos ETLs tuvieron problemas. Revisa los logs.")
            return results
            
    except Exception as e:
        logger.error(f"Error crítico ejecutando ETLs: {str(e)}", exc_info=True)
        return results


if __name__ == "__main__":
    results = asyncio.run(run_all_etl())
    
    # Exit code basado en resultados
    all_success = all(
        r.get("status") == "success" for r in results.values()
    )
    sys.exit(0 if all_success else 1)

