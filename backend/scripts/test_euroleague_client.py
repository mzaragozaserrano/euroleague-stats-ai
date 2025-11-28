"""
Script de prueba para validar el cliente de Euroleague API.

Este script verifica que el cliente puede conectarse exitosamente
a la API de Euroleague y obtener datos de los endpoints principales.

Uso:
    python backend/scripts/test_euroleague_client.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Añadir el directorio del backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.euroleague_client import (
    EuroleagueClient,
    EuroleagueClientError,
    EuroleagueRateLimitError,
    EuroleagueTimeoutError,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_euroleague_client():
    """Ejecutar pruebas del cliente de Euroleague."""
    client = EuroleagueClient()

    logger.info("=" * 80)
    logger.info("PRUEBAS DEL CLIENTE EUROLEAGUE API")
    logger.info("=" * 80)

    # Test 1: Obtener equipos
    logger.info("\n[TEST 1] Obteniendo lista de equipos...")
    try:
        teams = await client.get_teams()
        if teams:
            logger.info(
                f"✓ Equipos obtenidos exitosamente. "
                f"Total de equipos: {len(teams.get('Teams', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de equipos")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener equipos: {e}")

    # Test 2: Obtener jugadores
    logger.info("\n[TEST 2] Obteniendo lista de jugadores...")
    try:
        players = await client.get_players()
        if players:
            logger.info(
                f"✓ Jugadores obtenidos exitosamente. "
                f"Total de jugadores: {len(players.get('Players', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de jugadores")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener jugadores: {e}")

    # Test 3: Obtener partidos (temporada actual)
    logger.info("\n[TEST 3] Obteniendo partidos...")
    try:
        games = await client.get_games()
        if games:
            logger.info(
                f"✓ Partidos obtenidos exitosamente. "
                f"Total de partidos: {len(games.get('Games', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de partidos")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener partidos: {e}")

    # Test 4: Obtener estadísticas de jugadores
    logger.info("\n[TEST 4] Obteniendo estadísticas de jugadores...")
    try:
        playerstats = await client.get_playerstats()
        if playerstats:
            logger.info(
                f"✓ Estadísticas obtenidas exitosamente. "
                f"Total de registros: {len(playerstats.get('PlayerStats', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de estadísticas")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener estadísticas: {e}")

    # Test 5: Obtener clasificaciones
    logger.info("\n[TEST 5] Obteniendo clasificaciones...")
    try:
        standings = await client.get_standings()
        if standings:
            logger.info(
                f"✓ Clasificaciones obtenidas exitosamente. "
                f"Total de registros: {len(standings.get('Standings', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de clasificaciones")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener clasificaciones: {e}")

    # Test 6: Obtener estadísticas de equipos
    logger.info("\n[TEST 6] Obteniendo estadísticas de equipos...")
    try:
        teamstats = await client.get_teamstats()
        if teamstats:
            logger.info(
                f"✓ Estadísticas de equipos obtenidas exitosamente. "
                f"Total de registros: {len(teamstats.get('TeamStats', []))}"
            )
        else:
            logger.warning("✗ Respuesta vacía de estadísticas de equipos")
    except EuroleagueClientError as e:
        logger.error(f"✗ Error al obtener estadísticas de equipos: {e}")

    # Test 7: Verificar URLs de endpoints
    logger.info("\n[TEST 7] Verificando URLs de endpoints...")
    for endpoint_name in ["teams", "players", "games", "playerstats", "standings", "teamstats"]:
        try:
            url = client.get_endpoint_url(endpoint_name)
            logger.info(f"✓ {endpoint_name}: {url}")
        except Exception as e:
            logger.error(f"✗ Error con endpoint {endpoint_name}: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("PRUEBAS COMPLETADAS")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_euroleague_client())

