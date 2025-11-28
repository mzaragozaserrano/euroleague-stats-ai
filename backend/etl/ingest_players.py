"""
Script ETL para ingestar datos de jugadores desde la API de Euroleague.

Proporciona funciones para:
- Obtener datos de jugadores desde la API de Euroleague
- Transformar los datos al formato de los modelos SQLAlchemy
- Persistir datos usando la lógica de upsert para evitar duplicados
- Manejar errores de red y base de datos
- Validar relaciones con equipos

Uso típico:
    async def main():
        from etl.ingest_players import ingest_players
        await ingest_players()

    asyncio.run(main())
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError

from app.models import Player, Team
from app.database import async_session_maker
from etl.euroleague_client import EuroleagueClient, EuroleagueClientError

# Configurar logging
logger = logging.getLogger(__name__)


class PlayerIngestError(Exception):
    """Excepción base para errores durante la ingesta de jugadores."""

    pass


class PlayerTransformationError(PlayerIngestError):
    """Error durante la transformación de datos de jugadores."""

    pass


class PlayerPersistenceError(PlayerIngestError):
    """Error durante la persistencia de jugadores en BD."""

    pass


async def fetch_players_from_api(
    client: Optional[EuroleagueClient] = None, season: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtener datos de jugadores desde la API de Euroleague.

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar

    Returns:
        Respuesta JSON de la API con los datos de jugadores.

    Raises:
        EuroleagueClientError: Si hay error en la solicitud a la API.
    """
    if client is None:
        client = EuroleagueClient()

    logger.info(
        f"Obteniendo datos de jugadores desde la API de Euroleague (temporada: {season})..."
    )
    try:
        response = await client.get_players(season=season)
        logger.info(f"Se obtuvieron datos de jugadores. Respuesta contiene: {response.keys()}")
        return response
    except EuroleagueClientError as e:
        logger.error(f"Error al obtener datos de jugadores desde la API: {str(e)}")
        raise PlayerIngestError(f"Error al obtener datos de jugadores: {str(e)}") from e


def validate_player_data(player_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos del jugador contienen los campos requeridos.

    Args:
        player_data: Diccionario con datos del jugador

    Returns:
        True si los datos son válidos, False si faltan campos requeridos.
    """
    required_fields = ["id", "name", "team_id"]
    return all(field in player_data for field in required_fields)


def transform_player_data(api_player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transformar datos de jugador desde el formato de API al formato del modelo SQLAlchemy.

    Args:
        api_player: Diccionario con datos del jugador desde la API

    Returns:
        Diccionario con datos transformados para el modelo Player

    Raises:
        PlayerTransformationError: Si la transformación falla
    """
    try:
        # Validar datos requeridos
        if not validate_player_data(api_player):
            logger.warning(f"Jugador con datos incompletos: {api_player}. Se rechazará.")
            raise PlayerTransformationError(f"Campos requeridos faltantes en jugador: {api_player}")

        transformed = {
            "id": int(api_player["id"]),
            "name": str(api_player["name"]),
            "team_id": int(api_player["team_id"]),
            "position": api_player.get("position", None),
            "height": api_player.get("height", None),
            "birth_date": api_player.get("birth_date", None),
        }

        # Validar que el nombre no esté vacío
        if not transformed["name"]:
            raise PlayerTransformationError(f"Nombre vacío en jugador: {api_player}")

        # Validar que team_id es válido
        if transformed["team_id"] <= 0:
            raise PlayerTransformationError(f"team_id inválido en jugador: {api_player}")

        logger.debug(f"Jugador transformado: {transformed}")
        return transformed

    except (ValueError, KeyError) as e:
        logger.error(f"Error transformando datos de jugador {api_player}: {str(e)}")
        raise PlayerTransformationError(f"Error transformando datos de jugador: {str(e)}") from e
    except PlayerTransformationError:
        raise
    except Exception as e:
        logger.error(f"Error inesperado transformando jugador {api_player}: {str(e)}")
        raise PlayerTransformationError(f"Error inesperado transformando jugador: {str(e)}") from e


async def team_exists(session: AsyncSession, team_id: int) -> bool:
    """
    Verificar si un equipo existe en la base de datos.

    Args:
        session: Sesión de base de datos asincrónica
        team_id: ID del equipo a verificar

    Returns:
        True si el equipo existe, False en caso contrario
    """
    try:
        stmt = select(exists(select(Team).where(Team.id == team_id)))
        result = await session.execute(stmt)
        return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Error verificando existencia de equipo {team_id}: {str(e)}")
        return False


async def upsert_player(session: AsyncSession, player_data: Dict[str, Any]) -> Player:
    """
    Insertar o actualizar un jugador en la base de datos.

    La lógica de upsert:
    - Si existe un jugador con el mismo id, actualizar sus campos
    - Si no existe, insertar como nuevo jugador

    Args:
        session: Sesión de base de datos asincrónica
        player_data: Diccionario con datos del jugador transformados

    Returns:
        Objeto Player insertado o actualizado

    Raises:
        PlayerPersistenceError: Si hay error en la operación de BD
    """
    try:
        # Verificar que el equipo existe
        team_exists_check = await team_exists(session, player_data["team_id"])
        if not team_exists_check:
            raise PlayerPersistenceError(
                f"El equipo con id={player_data['team_id']} no existe en la base de datos"
            )

        # Buscar jugador existente por id
        stmt = select(Player).where(Player.id == player_data["id"])
        result = await session.execute(stmt)
        existing_player = result.scalar_one_or_none()

        if existing_player:
            # Actualizar jugador existente
            logger.info(
                f"Actualizando jugador existente: {player_data['id']} - {player_data['name']}"
            )
            existing_player.name = player_data["name"]
            existing_player.team_id = player_data["team_id"]
            existing_player.position = player_data.get("position")
            existing_player.height = player_data.get("height")
            existing_player.birth_date = player_data.get("birth_date")
            existing_player.updated_at = datetime.utcnow()
            await session.flush()
            return existing_player
        else:
            # Crear nuevo jugador
            logger.info(f"Insertando nuevo jugador: {player_data['id']} - {player_data['name']}")
            new_player = Player(
                id=player_data["id"],
                name=player_data["name"],
                team_id=player_data["team_id"],
                position=player_data.get("position"),
                height=player_data.get("height"),
                birth_date=player_data.get("birth_date"),
            )
            session.add(new_player)
            await session.flush()
            return new_player

    except PlayerPersistenceError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error de BD al procesar jugador {player_data}: {str(e)}")
        raise PlayerPersistenceError(f"Error al persistir jugador en BD: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error inesperado al procesar jugador {player_data}: {str(e)}")
        raise PlayerPersistenceError(f"Error inesperado procesando jugador: {str(e)}") from e


async def ingest_players(
    client: Optional[EuroleagueClient] = None,
    season: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ejecutar el pipeline completo de ingesta de jugadores.

    Flujo:
    1. Obtener datos de jugadores desde la API
    2. Transformar cada jugador al formato del modelo
    3. Validar que los equipos existan
    4. Hacer upsert de cada jugador en la BD
    5. Confirmar la transacción

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.
        season: Temporada opcional para filtrar

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
        PlayerIngestError: Si hay errores críticos que impiden la ingesta
    """
    stats = {"total_processed": 0, "inserted": 0, "updated": 0, "errors": 0}

    try:
        # Paso 1: Obtener datos de la API
        logger.info("=== Iniciando ingesta de jugadores ===")
        api_response = await fetch_players_from_api(client, season)

        # Extraer lista de jugadores de la respuesta
        players_list = api_response.get("Players", [])
        if not players_list:
            logger.warning(f"La API no retornó jugadores. Respuesta: {api_response}")
            return {**stats, "status": "no_players_found"}

        logger.info(f"Se obtuvieron {len(players_list)} jugadores de la API")

        # Paso 2, 3 y 4: Transformar, validar equipos y persistir cada jugador
        async with async_session_maker() as session:
            for player_data in players_list:
                stats["total_processed"] += 1

                try:
                    # Transformar datos
                    transformed = transform_player_data(player_data)

                    # Verificar si el jugador es nuevo o existente antes de persistir
                    stmt = select(Player).where(Player.id == transformed["id"])
                    result = await session.execute(stmt)
                    existing_player = result.scalar_one_or_none()

                    # Upsert
                    await upsert_player(session, transformed)

                    if existing_player:
                        stats["updated"] += 1
                        logger.debug(f"Jugador actualizado: {transformed['id']}")
                    else:
                        stats["inserted"] += 1
                        logger.debug(f"Jugador insertado: {transformed['id']}")

                except (PlayerTransformationError, PlayerPersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(
                        f"Error procesando jugador {player_data.get('id', 'UNKNOWN')}: {str(e)}"
                    )
                    # Continuar con el siguiente jugador

            # Paso 5: Confirmar la transacción
            await session.commit()
            logger.info("Transacción confirmada. Ingesta completada.")

        stats["status"] = "success"
        logger.info(
            f"=== Ingesta de jugadores completada ===\n"
            f"Total procesados: {stats['total_processed']}\n"
            f"Insertados: {stats['inserted']}\n"
            f"Actualizados: {stats['updated']}\n"
            f"Errores: {stats['errors']}"
        )
        return stats

    except EuroleagueClientError as e:
        stats["status"] = "api_error"
        logger.error(f"Error de API: {str(e)}")
        raise PlayerIngestError(f"Error de API: {str(e)}") from e
    except Exception as e:
        stats["status"] = "critical_error"
        logger.error(f"Error crítico en ingesta: {str(e)}")
        raise PlayerIngestError(f"Error crítico en ingesta: {str(e)}") from e


async def main():
    """Punto de entrada para ejecutar el ETL de jugadores."""
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        result = await ingest_players()
        logger.info(f"Resultado final: {result}")
        sys.exit(0 if result.get("status") == "success" else 1)
    except PlayerIngestError as e:
        logger.error(f"Fallo en la ingesta: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
