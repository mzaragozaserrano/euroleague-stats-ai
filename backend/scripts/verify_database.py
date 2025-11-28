"""
Script para verificar el estado de la base de datos y mostrar qué datos están cargados.

Uso:
    poetry run python scripts/verify_database.py
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.database import async_session_maker
from app.models import Team, Player, Game, PlayerStats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def verify_database():
    """Verifica el estado de la base de datos y muestra estadísticas."""
    logger.info("=" * 60)
    logger.info("VERIFICACIÓN DE BASE DE DATOS")
    logger.info("=" * 60)

    async with async_session_maker() as session:
        # Contar equipos
        result = await session.execute(select(func.count(Team.id)))
        teams_count = result.scalar()
        logger.info(f"📊 Equipos en la BD: {teams_count}")

        if teams_count > 0:
            result = await session.execute(select(Team))
            teams = result.scalars().all()
            logger.info("   Equipos:")
            for team in teams:
                logger.info(f"   - {team.name} (ID: {team.id}, Code: {team.code})")

        # Contar jugadores
        result = await session.execute(select(func.count(Player.id)))
        players_count = result.scalar()
        logger.info(f"\n📊 Jugadores en la BD: {players_count}")

        if players_count > 0:
            result = await session.execute(select(Player))
            players = result.scalars().all()
            logger.info("   Jugadores:")
            for player in players:
                logger.info(
                    f"   - {player.name} "
                    f"(ID: {player.id}, Team: {player.team_id}, Position: {player.position})"
                )

        # Contar partidos
        result = await session.execute(select(func.count(Game.id)))
        games_count = result.scalar()
        logger.info(f"\n📊 Partidos en la BD: {games_count}")

        if games_count > 0:
            result = await session.execute(select(Game))
            games = result.scalars().all()
            logger.info("   Partidos:")
            for game in games:
                score_info = ""
                if game.home_score is not None and game.away_score is not None:
                    score_info = f" {game.home_score}-{game.away_score}"
                logger.info(
                    f"   - Team {game.home_team_id} vs Team {game.away_team_id}{score_info} "
                    f"(ID: {game.id}, Season: {game.season}, Round: {game.round}, "
                    f"Date: {game.date})"
                )

        # Contar estadísticas de jugadores
        result = await session.execute(select(func.count(PlayerStats.id)))
        stats_count = result.scalar()
        logger.info(f"\n📊 Estadísticas de jugadores en la BD: {stats_count}")

        if stats_count > 0:
            result = await session.execute(select(PlayerStats))
            stats = result.scalars().all()
            logger.info("   Estadísticas:")
            for stat in stats:
                logger.info(
                    f"   - Player {stat.player_id} en Game {stat.game_id}: "
                    f"{stat.points} puntos, PIR: {stat.pir}"
                )

    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN")
    logger.info("=" * 60)
    logger.info(f"✅ Equipos: {teams_count}")
    logger.info(f"✅ Jugadores: {players_count}")
    logger.info(f"✅ Partidos: {games_count}")
    logger.info(f"✅ Estadísticas: {stats_count}")

    if teams_count > 0 and players_count > 0:
        logger.info("\n✅ Base de datos poblada correctamente")
        return True
    else:
        logger.warning("\n⚠️  Base de datos vacía o incompleta")
        logger.info("   Ejecuta: poetry run python scripts/populate_test_data.py")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(verify_database())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Error verificando la base de datos: {e}", exc_info=True)
        sys.exit(1)

