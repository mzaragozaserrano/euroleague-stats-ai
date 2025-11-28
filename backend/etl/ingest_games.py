"""
Script ETL para ingestar datos de partidos y estadísticas de jugadores desde la API de Euroleague.

Proporciona funciones para:
- Obtener datos de partidos desde la API de Euroleague
- Obtener estadísticas de jugadores (box scores) para cada partido
- Transformar los datos anidados al formato de los modelos SQLAlchemy
- Persistir partidos y estadísticas asociadas usando la lógica de upsert
- Validar relaciones de clave foránea
- Manejar errores de red y base de datos

Uso típico:
    async def main():
        from etl.ingest_games import ingest_games, ingest_player_stats
        await ingest_games()
        await ingest_player_stats()

    asyncio.run(main())
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, date
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError

from app.models import Game, Player, Team, PlayerStats
from app.database import async_session_maker
from etl.euroleague_client import EuroleagueClient, EuroleagueClientError

# Configurar logging
logger = logging.getLogger(__name__)


class GameIngestError(Exception):
    """Excepción base para errores durante la ingesta de partidos."""

    pass


class GameTransformationError(GameIngestError):
    """Error durante la transformación de datos de partidos."""

    pass


class GamePersistenceError(GameIngestError):
    """Error durante la persistencia de partidos en BD."""

    pass


class PlayerStatsIngestError(Exception):
    """Excepción base para errores durante la ingesta de estadísticas de jugadores."""

    pass


class PlayerStatsTransformationError(PlayerStatsIngestError):
    """Error durante la transformación de datos de estadísticas."""

    pass


class PlayerStatsPersistenceError(PlayerStatsIngestError):
    """Error durante la persistencia de estadísticas en BD."""

    pass


async def fetch_games_from_api(
    client: Optional[EuroleagueClient] = None,
    season: Optional[int] = None,
    round_: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Obtener datos de partidos desde la API de Euroleague.

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar
        round_: Jornada opcional para filtrar

    Returns:
        Respuesta JSON de la API con los datos de partidos.

    Raises:
        EuroleagueClientError: Si hay error en la solicitud a la API.
    """
    if client is None:
        client = EuroleagueClient()

    logger.info(
        f"Obteniendo datos de partidos desde la API de Euroleague "
        f"(temporada: {season}, jornada: {round_})..."
    )
    try:
        response = await client.get_games(season=season, round_=round_)
        logger.info(f"Se obtuvieron datos de partidos. Respuesta contiene: {response.keys()}")
        return response
    except EuroleagueClientError as e:
        logger.error(f"Error al obtener datos de partidos desde la API: {str(e)}")
        raise GameIngestError(f"Error al obtener datos de partidos: {str(e)}") from e


async def fetch_player_stats_from_api(
    client: Optional[EuroleagueClient] = None,
    season: Optional[int] = None,
    round_: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Obtener estadísticas de jugadores (box scores) desde la API de Euroleague.

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar
        round_: Jornada opcional para filtrar

    Returns:
        Respuesta JSON de la API con los datos de estadísticas.

    Raises:
        EuroleagueClientError: Si hay error en la solicitud a la API.
    """
    if client is None:
        client = EuroleagueClient()

    logger.info(
        f"Obteniendo estadísticas de jugadores desde la API de Euroleague "
        f"(temporada: {season}, jornada: {round_})..."
    )
    try:
        response = await client.get_playerstats(season=season, round_=round_)
        logger.info(
            f"Se obtuvieron estadísticas de jugadores. Respuesta contiene: {response.keys()}"
        )
        return response
    except EuroleagueClientError as e:
        logger.error(f"Error al obtener estadísticas de jugadores desde la API: {str(e)}")
        raise PlayerStatsIngestError(f"Error al obtener estadísticas de jugadores: {str(e)}") from e


def validate_game_data(game_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos del partido contienen los campos requeridos.

    Args:
        game_data: Diccionario con datos del partido

    Returns:
        True si los datos son válidos, False si faltan campos requeridos.
    """
    required_fields = ["id", "season", "round", "home_team_id", "away_team_id", "date"]
    return all(field in game_data for field in required_fields)


def validate_player_stats_data(stats_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos de estadísticas contienen los campos requeridos.

    Args:
        stats_data: Diccionario con datos de estadísticas

    Returns:
        True si los datos son válidos, False si faltan campos requeridos.
    """
    required_fields = ["game_id", "player_id", "team_id"]
    return all(field in stats_data for field in required_fields)


def parse_date(date_value: Any) -> Optional[date]:
    """
    Parsear un valor de fecha desde la API al formato date.

    Args:
        date_value: Valor de fecha (str, date, o None)

    Returns:
        Objeto date o None
    """
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, str):
        try:
            # Intentar parsear en formato ISO (YYYY-MM-DD)
            return datetime.fromisoformat(date_value).date()
        except (ValueError, TypeError):
            logger.warning(f"No se pudo parsear fecha: {date_value}")
            return None
    return None


def calculate_pir(stats: Dict[str, Any]) -> Optional[float]:
    """
    Calcular el PIR (Performance Index Rating) de un jugador.

    PIR = (puntos + rebotes + asistencias + robos + bloqueos) - (tiros_fallidos + pases_perdidos + faltas)

    Args:
        stats: Diccionario con estadísticas del jugador

    Returns:
        Valor del PIR o None si no hay datos suficientes
    """
    try:
        points = stats.get("points", 0) or 0
        rebounds = stats.get("rebounds_total", 0) or 0
        assists = stats.get("assists", 0) or 0
        steals = stats.get("steals", 0) or 0
        blocks = stats.get("blocks", 0) or 0

        # Calcular tiros fallidos
        fg2_attempted = stats.get("fg2_attempted", 0) or 0
        fg2_made = stats.get("fg2_made", 0) or 0
        fg3_attempted = stats.get("fg3_attempted", 0) or 0
        fg3_made = stats.get("fg3_made", 0) or 0
        ft_attempted = stats.get("ft_attempted", 0) or 0
        ft_made = stats.get("ft_made", 0) or 0

        missed_shots = (
            (fg2_attempted - fg2_made) + (fg3_attempted - fg3_made) + (ft_attempted - ft_made)
        )
        turnovers = stats.get("turnovers", 0) or 0
        fouls_committed = stats.get("fouls_committed", 0) or 0

        pir = (points + rebounds + assists + steals + blocks) - (
            missed_shots + turnovers + fouls_committed
        )
        return float(pir)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error calculando PIR: {str(e)}")
        return None


def transform_game_data(api_game: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transformar datos de partido desde el formato de API al formato del modelo SQLAlchemy.

    Args:
        api_game: Diccionario con datos del partido desde la API

    Returns:
        Diccionario con datos transformados para el modelo Game

    Raises:
        GameTransformationError: Si la transformación falla
    """
    try:
        # Validar datos requeridos
        if not validate_game_data(api_game):
            logger.warning(f"Partido con datos incompletos: {api_game}. Se rechazará.")
            raise GameTransformationError(f"Campos requeridos faltantes en partido: {api_game}")

        # Parsear fecha
        parsed_date = parse_date(api_game.get("date"))
        if parsed_date is None:
            raise GameTransformationError(f"Fecha inválida en partido: {api_game}")

        transformed = {
            "id": int(api_game["id"]),
            "season": int(api_game["season"]),
            "round": int(api_game["round"]),
            "home_team_id": int(api_game["home_team_id"]),
            "away_team_id": int(api_game["away_team_id"]),
            "date": parsed_date,
            "home_score": api_game.get("home_score"),
            "away_score": api_game.get("away_score"),
        }

        # Convertir puntuaciones a int si están presentes
        if transformed["home_score"] is not None:
            transformed["home_score"] = int(transformed["home_score"])
        if transformed["away_score"] is not None:
            transformed["away_score"] = int(transformed["away_score"])

        # Validar IDs de equipos
        if transformed["home_team_id"] <= 0 or transformed["away_team_id"] <= 0:
            raise GameTransformationError(f"IDs de equipo inválidos en partido: {api_game}")

        # Validar que no sean el mismo equipo
        if transformed["home_team_id"] == transformed["away_team_id"]:
            raise GameTransformationError(f"Un equipo no puede jugar contra sí mismo: {api_game}")

        logger.debug(f"Partido transformado: {transformed}")
        return transformed

    except GameTransformationError:
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Error transformando datos de partido {api_game}: {str(e)}")
        raise GameTransformationError(f"Error transformando datos de partido: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error inesperado transformando partido {api_game}: {str(e)}")
        raise GameTransformationError(f"Error inesperado transformando partido: {str(e)}") from e


def transform_player_stats_data(api_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transformar datos de estadísticas desde el formato de API al formato del modelo SQLAlchemy.

    Args:
        api_stats: Diccionario con datos de estadísticas desde la API

    Returns:
        Diccionario con datos transformados para el modelo PlayerStats

    Raises:
        PlayerStatsTransformationError: Si la transformación falla
    """
    try:
        # Validar datos requeridos
        if not validate_player_stats_data(api_stats):
            logger.warning(f"Estadísticas con datos incompletos: {api_stats}. Se rechazará.")
            raise PlayerStatsTransformationError(
                f"Campos requeridos faltantes en estadísticas: {api_stats}"
            )

        transformed = {
            "game_id": int(api_stats["game_id"]),
            "player_id": int(api_stats["player_id"]),
            "team_id": int(api_stats["team_id"]),
            "minutes": api_stats.get("minutes"),
            "points": api_stats.get("points"),
            "rebounds_total": api_stats.get("rebounds_total"),
            "assists": api_stats.get("assists"),
            "steals": api_stats.get("steals"),
            "blocks": api_stats.get("blocks"),
            "turnovers": api_stats.get("turnovers"),
            "fg2_made": api_stats.get("fg2_made"),
            "fg2_attempted": api_stats.get("fg2_attempted"),
            "fg3_made": api_stats.get("fg3_made"),
            "fg3_attempted": api_stats.get("fg3_attempted"),
            "ft_made": api_stats.get("ft_made"),
            "ft_attempted": api_stats.get("ft_attempted"),
            "fouls_drawn": api_stats.get("fouls_drawn"),
            "fouls_committed": api_stats.get("fouls_committed"),
        }

        # Convertir valores numéricos a int donde corresponda
        for field in [
            "minutes",
            "points",
            "rebounds_total",
            "assists",
            "steals",
            "blocks",
            "turnovers",
            "fg2_made",
            "fg2_attempted",
            "fg3_made",
            "fg3_attempted",
            "ft_made",
            "ft_attempted",
            "fouls_drawn",
            "fouls_committed",
        ]:
            if transformed[field] is not None:
                transformed[field] = int(transformed[field])

        # Calcular PIR
        transformed["pir"] = calculate_pir(transformed)

        logger.debug(f"Estadísticas transformadas: {transformed}")
        return transformed

    except PlayerStatsTransformationError:
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Error transformando datos de estadísticas {api_stats}: {str(e)}")
        raise PlayerStatsTransformationError(
            f"Error transformando datos de estadísticas: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Error inesperado transformando estadísticas {api_stats}: {str(e)}")
        raise PlayerStatsTransformationError(
            f"Error inesperado transformando estadísticas: {str(e)}"
        ) from e


async def teams_exist(session: AsyncSession, home_team_id: int, away_team_id: int) -> bool:
    """
    Verificar si ambos equipos existen en la base de datos.

    Args:
        session: Sesión de base de datos asincrónica
        home_team_id: ID del equipo local
        away_team_id: ID del equipo visitante

    Returns:
        True si ambos equipos existen, False en caso contrario
    """
    try:
        stmt = select(
            exists(select(Team).where(Team.id == home_team_id))
            & exists(select(Team).where(Team.id == away_team_id))
        )
        result = await session.execute(stmt)
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(
            f"Error verificando existencia de equipos {home_team_id}, {away_team_id}: {str(e)}"
        )
        return False


async def player_exists(session: AsyncSession, player_id: int) -> bool:
    """
    Verificar si un jugador existe en la base de datos.

    Args:
        session: Sesión de base de datos asincrónica
        player_id: ID del jugador a verificar

    Returns:
        True si el jugador existe, False en caso contrario
    """
    try:
        stmt = select(exists(select(Player).where(Player.id == player_id)))
        result = await session.execute(stmt)
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Error verificando existencia de jugador {player_id}: {str(e)}")
        return False


async def upsert_game(session: AsyncSession, game_data: Dict[str, Any]) -> Game:
    """
    Insertar o actualizar un partido en la base de datos.

    La lógica de upsert:
    - Si existe un partido con el mismo id, actualizar sus campos
    - Si no existe, insertar como nuevo partido

    Args:
        session: Sesión de base de datos asincrónica
        game_data: Diccionario con datos del partido transformados

    Returns:
        Objeto Game insertado o actualizado

    Raises:
        GamePersistenceError: Si hay error en la operación de BD
    """
    try:
        # Verificar que los equipos existen
        teams_exist_check = await teams_exist(
            session, game_data["home_team_id"], game_data["away_team_id"]
        )
        if not teams_exist_check:
            raise GamePersistenceError(
                f"Uno o ambos equipos (id={game_data['home_team_id']}, "
                f"id={game_data['away_team_id']}) no existen en la base de datos"
            )

        # Buscar partido existente por id
        stmt = select(Game).where(Game.id == game_data["id"])
        result = await session.execute(stmt)
        existing_game = result.scalar_one_or_none()

        if existing_game:
            # Actualizar partido existente
            logger.info(
                f"Actualizando partido existente: {game_data['id']} "
                f"({game_data['home_team_id']} vs {game_data['away_team_id']})"
            )
            existing_game.season = game_data["season"]
            existing_game.round = game_data["round"]
            existing_game.home_team_id = game_data["home_team_id"]
            existing_game.away_team_id = game_data["away_team_id"]
            existing_game.date = game_data["date"]
            existing_game.home_score = game_data.get("home_score")
            existing_game.away_score = game_data.get("away_score")
            existing_game.updated_at = datetime.utcnow()
            await session.flush()
            return existing_game
        else:
            # Crear nuevo partido
            logger.info(
                f"Insertando nuevo partido: {game_data['id']} "
                f"({game_data['home_team_id']} vs {game_data['away_team_id']})"
            )
            new_game = Game(
                id=game_data["id"],
                season=game_data["season"],
                round=game_data["round"],
                home_team_id=game_data["home_team_id"],
                away_team_id=game_data["away_team_id"],
                date=game_data["date"],
                home_score=game_data.get("home_score"),
                away_score=game_data.get("away_score"),
            )
            session.add(new_game)
            await session.flush()
            return new_game

    except GamePersistenceError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error de BD al procesar partido {game_data}: {str(e)}")
        raise GamePersistenceError(f"Error al persistir partido en BD: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error inesperado al procesar partido {game_data}: {str(e)}")
        raise GamePersistenceError(f"Error inesperado procesando partido: {str(e)}") from e


async def upsert_player_stats(session: AsyncSession, stats_data: Dict[str, Any]) -> PlayerStats:
    """
    Insertar o actualizar estadísticas de jugador en la base de datos.

    La lógica de upsert:
    - Si existe un registro con el mismo game_id, player_id y team_id, actualizar sus campos
    - Si no existe, insertar como nuevo registro

    Args:
        session: Sesión de base de datos asincrónica
        stats_data: Diccionario con datos de estadísticas transformados

    Returns:
        Objeto PlayerStats insertado o actualizado

    Raises:
        PlayerStatsPersistenceError: Si hay error en la operación de BD
    """
    try:
        # Verificar que el jugador existe
        player_exists_check = await player_exists(session, stats_data["player_id"])
        if not player_exists_check:
            raise PlayerStatsPersistenceError(
                f"El jugador con id={stats_data['player_id']} no existe en la base de datos"
            )

        # Buscar estadísticas existentes por game_id, player_id, team_id
        stmt = select(PlayerStats).where(
            (PlayerStats.game_id == stats_data["game_id"])
            & (PlayerStats.player_id == stats_data["player_id"])
            & (PlayerStats.team_id == stats_data["team_id"])
        )
        result = await session.execute(stmt)
        existing_stats = result.scalar_one_or_none()

        if existing_stats:
            # Actualizar estadísticas existentes
            logger.debug(
                f"Actualizando estadísticas existentes: "
                f"game_id={stats_data['game_id']}, player_id={stats_data['player_id']}"
            )
            existing_stats.minutes = stats_data.get("minutes")
            existing_stats.points = stats_data.get("points")
            existing_stats.rebounds_total = stats_data.get("rebounds_total")
            existing_stats.assists = stats_data.get("assists")
            existing_stats.steals = stats_data.get("steals")
            existing_stats.blocks = stats_data.get("blocks")
            existing_stats.turnovers = stats_data.get("turnovers")
            existing_stats.fg2_made = stats_data.get("fg2_made")
            existing_stats.fg2_attempted = stats_data.get("fg2_attempted")
            existing_stats.fg3_made = stats_data.get("fg3_made")
            existing_stats.fg3_attempted = stats_data.get("fg3_attempted")
            existing_stats.ft_made = stats_data.get("ft_made")
            existing_stats.ft_attempted = stats_data.get("ft_attempted")
            existing_stats.fouls_drawn = stats_data.get("fouls_drawn")
            existing_stats.fouls_committed = stats_data.get("fouls_committed")
            existing_stats.pir = stats_data.get("pir")
            existing_stats.updated_at = datetime.utcnow()
            await session.flush()
            return existing_stats
        else:
            # Crear nuevas estadísticas
            logger.debug(
                f"Insertando nuevas estadísticas: "
                f"game_id={stats_data['game_id']}, player_id={stats_data['player_id']}"
            )
            new_stats = PlayerStats(
                game_id=stats_data["game_id"],
                player_id=stats_data["player_id"],
                team_id=stats_data["team_id"],
                minutes=stats_data.get("minutes"),
                points=stats_data.get("points"),
                rebounds_total=stats_data.get("rebounds_total"),
                assists=stats_data.get("assists"),
                steals=stats_data.get("steals"),
                blocks=stats_data.get("blocks"),
                turnovers=stats_data.get("turnovers"),
                fg2_made=stats_data.get("fg2_made"),
                fg2_attempted=stats_data.get("fg2_attempted"),
                fg3_made=stats_data.get("fg3_made"),
                fg3_attempted=stats_data.get("fg3_attempted"),
                ft_made=stats_data.get("ft_made"),
                ft_attempted=stats_data.get("ft_attempted"),
                fouls_drawn=stats_data.get("fouls_drawn"),
                fouls_committed=stats_data.get("fouls_committed"),
                pir=stats_data.get("pir"),
            )
            session.add(new_stats)
            await session.flush()
            return new_stats

    except PlayerStatsPersistenceError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error de BD al procesar estadísticas {stats_data}: {str(e)}")
        raise PlayerStatsPersistenceError(f"Error al persistir estadísticas en BD: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error inesperado al procesar estadísticas {stats_data}: {str(e)}")
        raise PlayerStatsPersistenceError(
            f"Error inesperado procesando estadísticas: {str(e)}"
        ) from e


async def ingest_games(
    client: Optional[EuroleagueClient] = None,
    season: Optional[int] = None,
    round_: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ejecutar el pipeline completo de ingesta de partidos.

    Flujo:
    1. Obtener datos de partidos desde la API
    2. Transformar cada partido al formato del modelo
    3. Validar que los equipos existan
    4. Hacer upsert de cada partido en la BD
    5. Confirmar la transacción

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar
        round_: Jornada opcional para filtrar

    Returns:
        Diccionario con estadísticas de la ingesta:
        {
            "total_processed": int,
            "inserted": int,
            "updated": int,
            "errors": int,
            "status": str
        }

    Raises:
        GameIngestError: Si hay errores críticos que impiden la ingesta
    """
    stats = {"total_processed": 0, "inserted": 0, "updated": 0, "errors": 0}

    try:
        # Paso 1: Obtener datos de la API
        logger.info("=== Iniciando ingesta de partidos ===")
        api_response = await fetch_games_from_api(client, season, round_)

        # Extraer lista de partidos de la respuesta
        games_list = api_response.get("Games", [])
        if not games_list:
            logger.warning(f"La API no retornó partidos. Respuesta: {api_response}")
            return {**stats, "status": "no_games_found"}

        logger.info(f"Se obtuvieron {len(games_list)} partidos de la API")

        # Paso 2, 3 y 4: Transformar, validar equipos y persistir cada partido
        async with async_session_maker() as session:
            for game_data in games_list:
                stats["total_processed"] += 1

                try:
                    # Transformar datos
                    transformed = transform_game_data(game_data)

                    # Verificar si el partido es nuevo o existente antes de persistir
                    stmt = select(Game).where(Game.id == transformed["id"])
                    result = await session.execute(stmt)
                    existing_game = result.scalar_one_or_none()

                    # Upsert
                    await upsert_game(session, transformed)

                    if existing_game:
                        stats["updated"] += 1
                        logger.debug(f"Partido actualizado: {transformed['id']}")
                    else:
                        stats["inserted"] += 1
                        logger.debug(f"Partido insertado: {transformed['id']}")

                except (GameTransformationError, GamePersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(
                        f"Error procesando partido {game_data.get('id', 'UNKNOWN')}: {str(e)}"
                    )
                    # Continuar con el siguiente partido

            # Paso 5: Confirmar la transacción
            await session.commit()
            logger.info("Transacción confirmada. Ingesta de partidos completada.")

        stats["status"] = "success"
        logger.info(
            f"=== Ingesta de partidos completada ===\n"
            f"Total procesados: {stats['total_processed']}\n"
            f"Insertados: {stats['inserted']}\n"
            f"Actualizados: {stats['updated']}\n"
            f"Errores: {stats['errors']}"
        )
        return stats

    except EuroleagueClientError as e:
        stats["status"] = "api_error"
        logger.error(f"Error de API: {str(e)}")
        raise GameIngestError(f"Error de API: {str(e)}") from e
    except Exception as e:
        stats["status"] = "critical_error"
        logger.error(f"Error crítico en ingesta: {str(e)}")
        raise GameIngestError(f"Error crítico en ingesta: {str(e)}") from e


async def ingest_player_stats(
    client: Optional[EuroleagueClient] = None,
    season: Optional[int] = None,
    round_: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ejecutar el pipeline completo de ingesta de estadísticas de jugadores.

    Flujo:
    1. Obtener datos de estadísticas desde la API
    2. Transformar cada estadística al formato del modelo
    3. Validar que los jugadores y partidos existan
    4. Hacer upsert de cada estadística en la BD
    5. Confirmar la transacción

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar
        round_: Jornada opcional para filtrar

    Returns:
        Diccionario con estadísticas de la ingesta:
        {
            "total_processed": int,
            "inserted": int,
            "updated": int,
            "errors": int,
            "status": str
        }

    Raises:
        PlayerStatsIngestError: Si hay errores críticos que impiden la ingesta
    """
    stats = {"total_processed": 0, "inserted": 0, "updated": 0, "errors": 0}

    try:
        # Paso 1: Obtener datos de la API
        logger.info("=== Iniciando ingesta de estadísticas de jugadores ===")
        api_response = await fetch_player_stats_from_api(client, season, round_)

        # Extraer lista de estadísticas de la respuesta
        stats_list = api_response.get("PlayerStats", [])
        if not stats_list:
            logger.warning(f"La API no retornó estadísticas. Respuesta: {api_response}")
            return {**stats, "status": "no_stats_found"}

        logger.info(f"Se obtuvieron {len(stats_list)} estadísticas de jugadores de la API")

        # Paso 2, 3 y 4: Transformar, validar y persistir cada estadística
        async with async_session_maker() as session:
            for stat_data in stats_list:
                stats["total_processed"] += 1

                try:
                    # Transformar datos
                    transformed = transform_player_stats_data(stat_data)

                    # Verificar si la estadística es nueva o existente antes de persistir
                    stmt = select(PlayerStats).where(
                        (PlayerStats.game_id == transformed["game_id"])
                        & (PlayerStats.player_id == transformed["player_id"])
                        & (PlayerStats.team_id == transformed["team_id"])
                    )
                    result = await session.execute(stmt)
                    existing_stats = result.scalar_one_or_none()

                    # Upsert
                    await upsert_player_stats(session, transformed)

                    if existing_stats:
                        stats["updated"] += 1
                        logger.debug(
                            f"Estadística actualizada: "
                            f"game_id={transformed['game_id']}, "
                            f"player_id={transformed['player_id']}"
                        )
                    else:
                        stats["inserted"] += 1
                        logger.debug(
                            f"Estadística insertada: "
                            f"game_id={transformed['game_id']}, "
                            f"player_id={transformed['player_id']}"
                        )

                except (PlayerStatsTransformationError, PlayerStatsPersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(
                        f"Error procesando estadística "
                        f"(game_id={stat_data.get('game_id', 'UNKNOWN')}, "
                        f"player_id={stat_data.get('player_id', 'UNKNOWN')}): {str(e)}"
                    )
                    # Continuar con la siguiente estadística

            # Paso 5: Confirmar la transacción
            await session.commit()
            logger.info("Transacción confirmada. Ingesta de estadísticas completada.")

        stats["status"] = "success"
        logger.info(
            f"=== Ingesta de estadísticas de jugadores completada ===\n"
            f"Total procesados: {stats['total_processed']}\n"
            f"Insertados: {stats['inserted']}\n"
            f"Actualizados: {stats['updated']}\n"
            f"Errores: {stats['errors']}"
        )
        return stats

    except EuroleagueClientError as e:
        stats["status"] = "api_error"
        logger.error(f"Error de API: {str(e)}")
        raise PlayerStatsIngestError(f"Error de API: {str(e)}") from e
    except Exception as e:
        stats["status"] = "critical_error"
        logger.error(f"Error crítico en ingesta: {str(e)}")
        raise PlayerStatsIngestError(f"Error crítico en ingesta: {str(e)}") from e


async def main():
    """Punto de entrada para ejecutar los ETLs de partidos y estadísticas."""
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Ejecutar ingesta de partidos
        games_result = await ingest_games()
        logger.info(f"Resultado ingesta de partidos: {games_result}")

        # Ejecutar ingesta de estadísticas de jugadores
        stats_result = await ingest_player_stats()
        logger.info(f"Resultado ingesta de estadísticas: {stats_result}")

        success = (
            games_result.get("status") == "success" and stats_result.get("status") == "success"
        )
        sys.exit(0 if success else 1)
    except (GameIngestError, PlayerStatsIngestError) as e:
        logger.error(f"Fallo en la ingesta: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
