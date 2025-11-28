"""
Script para poblar la base de datos con datos de prueba.

Este script crea datos de ejemplo para completar el entregable de "Base de datos poblada"
mientras se resuelve el acceso a la API real de Euroleague.

Uso:
    poetry run python scripts/populate_test_data.py
"""

import asyncio
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models import Team, Player, Game, PlayerStats

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def populate_test_data():
    """Poblar la base de datos con datos de prueba."""
    
    async with async_session_maker() as session:
        try:
            # 1. Crear equipos de prueba
            logger.info("Creando equipos de prueba...")
            teams_data = [
                {"code": "RMB", "name": "Real Madrid", "logo_url": None},
                {"code": "BAR", "name": "FC Barcelona", "logo_url": None},
                {"code": "OLY", "name": "Olympiacos", "logo_url": None},
                {"code": "PAN", "name": "Panathinaikos", "logo_url": None},
                {"code": "CSK", "name": "CSKA Moscow", "logo_url": None},
            ]
            
            teams = []
            for team_data in teams_data:
                # Verificar si existe
                from sqlalchemy import select
                stmt = select(Team).where(Team.code == team_data["code"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    team = Team(**team_data)
                    session.add(team)
                    teams.append(team)
                    logger.info(f"  - Creado equipo: {team_data['name']}")
                else:
                    teams.append(existing)
                    logger.info(f"  - Equipo ya existe: {team_data['name']}")
            
            await session.flush()
            
            # 2. Crear jugadores de prueba
            logger.info("Creando jugadores de prueba...")
            players_data = [
                {"id": 1, "name": "Sergio Llull", "team_id": teams[0].id, "position": "PG"},
                {"id": 2, "name": "Walter Tavares", "team_id": teams[0].id, "position": "C"},
                {"id": 3, "name": "Nikola Mirotic", "team_id": teams[1].id, "position": "PF"},
                {"id": 4, "name": "Tomas Satoransky", "team_id": teams[1].id, "position": "PG"},
                {"id": 5, "name": "Kostas Sloukas", "team_id": teams[2].id, "position": "PG"},
                {"id": 6, "name": "Georgios Printezis", "team_id": teams[2].id, "position": "PF"},
            ]
            
            players = []
            for player_data in players_data:
                stmt = select(Player).where(Player.id == player_data["id"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    player = Player(**player_data)
                    session.add(player)
                    players.append(player)
                    logger.info(f"  - Creado jugador: {player_data['name']}")
                else:
                    players.append(existing)
                    logger.info(f"  - Jugador ya existe: {player_data['name']}")
            
            await session.flush()
            
            # 3. Crear partidos de prueba
            logger.info("Creando partidos de prueba...")
            games_data = [
                {
                    "id": 1,
                    "season": 2023,
                    "round": 1,
                    "home_team_id": teams[0].id,
                    "away_team_id": teams[1].id,
                    "date": date(2023, 10, 10),
                    "home_score": 85,
                    "away_score": 80,
                },
                {
                    "id": 2,
                    "season": 2023,
                    "round": 1,
                    "home_team_id": teams[2].id,
                    "away_team_id": teams[3].id,
                    "date": date(2023, 10, 11),
                    "home_score": 92,
                    "away_score": 88,
                },
                {
                    "id": 3,
                    "season": 2023,
                    "round": 2,
                    "home_team_id": teams[0].id,
                    "away_team_id": teams[2].id,
                    "date": date(2023, 10, 17),
                    "home_score": None,  # Partido programado
                    "away_score": None,
                },
            ]
            
            games = []
            for game_data in games_data:
                stmt = select(Game).where(Game.id == game_data["id"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    game = Game(**game_data)
                    session.add(game)
                    games.append(game)
                    logger.info(f"  - Creado partido: {game_data['id']}")
                else:
                    games.append(existing)
                    logger.info(f"  - Partido ya existe: {game_data['id']}")
            
            await session.flush()
            
            # 4. Crear estadísticas de jugadores de prueba
            logger.info("Creando estadísticas de jugadores de prueba...")
            stats_data = [
                # Partido 1 - Real Madrid vs Barcelona
                {
                    "game_id": games[0].id,
                    "player_id": players[0].id,  # Llull
                    "team_id": teams[0].id,
                    "minutes": 35,
                    "points": 20,
                    "rebounds_total": 5,
                    "assists": 8,
                    "steals": 2,
                    "blocks": 0,
                    "turnovers": 2,
                    "fg2_made": 6,
                    "fg2_attempted": 12,
                    "fg3_made": 2,
                    "fg3_attempted": 5,
                    "ft_made": 4,
                    "ft_attempted": 5,
                    "fouls_drawn": 3,
                    "fouls_committed": 2,
                    "pir": 25.0,
                },
                {
                    "game_id": games[0].id,
                    "player_id": players[2].id,  # Mirotic
                    "team_id": teams[1].id,
                    "minutes": 32,
                    "points": 18,
                    "rebounds_total": 8,
                    "assists": 3,
                    "steals": 1,
                    "blocks": 1,
                    "turnovers": 1,
                    "fg2_made": 5,
                    "fg2_attempted": 10,
                    "fg3_made": 2,
                    "fg3_attempted": 4,
                    "ft_made": 4,
                    "ft_attempted": 6,
                    "fouls_drawn": 2,
                    "fouls_committed": 3,
                    "pir": 20.0,
                },
                # Partido 2 - Olympiacos vs Panathinaikos
                {
                    "game_id": games[1].id,
                    "player_id": players[4].id,  # Sloukas
                    "team_id": teams[2].id,
                    "minutes": 38,
                    "points": 22,
                    "rebounds_total": 4,
                    "assists": 10,
                    "steals": 3,
                    "blocks": 0,
                    "turnovers": 1,
                    "fg2_made": 7,
                    "fg2_attempted": 14,
                    "fg3_made": 2,
                    "fg3_attempted": 6,
                    "ft_made": 4,
                    "ft_attempted": 4,
                    "fouls_drawn": 4,
                    "fouls_committed": 1,
                    "pir": 28.0,
                },
            ]
            
            for stat_data in stats_data:
                from sqlalchemy import and_
                stmt = select(PlayerStats).where(
                    and_(
                        PlayerStats.game_id == stat_data["game_id"],
                        PlayerStats.player_id == stat_data["player_id"],
                        PlayerStats.team_id == stat_data["team_id"],
                    )
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    stat = PlayerStats(**stat_data)
                    session.add(stat)
                    logger.info(
                        f"  - Creada estadística: Game {stat_data['game_id']}, "
                        f"Player {stat_data['player_id']}"
                    )
                else:
                    logger.info(
                        f"  - Estadística ya existe: Game {stat_data['game_id']}, "
                        f"Player {stat_data['player_id']}"
                    )
            
            # Confirmar transacción
            await session.commit()
            
            logger.info("=" * 60)
            logger.info("✅ Datos de prueba creados exitosamente")
            logger.info("=" * 60)
            logger.info(f"Equipos: {len(teams)}")
            logger.info(f"Jugadores: {len(players)}")
            logger.info(f"Partidos: {len(games)}")
            logger.info(f"Estadísticas: {len(stats_data)}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creando datos de prueba: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(populate_test_data())

