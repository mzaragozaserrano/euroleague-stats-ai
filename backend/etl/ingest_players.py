"""
Script ETL para ingestar datos de jugadores desde la API de Euroleague.

Proporciona funciones para:
- Obtener datos de jugadores desde el roster de cada equipo (v1/teams)
- Transformar los datos al formato de los modelos SQLAlchemy
- Persistir datos usando la lógica de upsert para evitar duplicados
- Manejar errores de red y base de datos
- Validar relaciones con equipos

La API retorna jugadores dentro de la estructura de cada equipo en:
    /v1/teams -> clubs -> club -> roster -> player

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


async def fetch_players_from_teams_roster(
    client: Optional[EuroleagueClient] = None,
) -> Dict[str, Any]:
    """
    Obtener datos de jugadores desde el roster de cada equipo (v1/teams).

    La API retorna:
        clubs -> club (lista) -> roster -> player (lista o dict)

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.

    Returns:
        Diccionario con estructura {"players": [lista de jugadores]}

    Raises:
        EuroleagueClientError: Si hay error en la solicitud a la API.
    """
    if client is None:
        client = EuroleagueClient()

    logger.info("Obteniendo datos de equipos (que contienen rosters de jugadores)...")
    
    try:
        # Obtener todos los equipos con sus rosters
        teams_response = await client.get_teams()
        
        # Extraer lista de equipos
        clubs_data = teams_response.get("clubs", {})
        teams_list = clubs_data.get("club", [])
        
        if not isinstance(teams_list, list):
            teams_list = [teams_list]
        
        logger.info(f"Se obtuvieron {len(teams_list)} equipos")
        
        # Extraer jugadores de los rosters de cada equipo
        all_players = []
        for team in teams_list:
            team_code = team.get("@code")
            team_name = team.get("clubname", team.get("name"))
            
            # Obtener roster del equipo
            roster = team.get("roster", {})
            if not isinstance(roster, dict):
                logger.warning(f"Roster del equipo {team_code} no es un diccionario")
                continue
            
            players_in_roster = roster.get("player", [])
            
            # Asegurar que es una lista
            if not isinstance(players_in_roster, list):
                if players_in_roster:
                    players_in_roster = [players_in_roster]
                else:
                    players_in_roster = []
            
            logger.debug(f"Equipo {team_code} ({team_name}): {len(players_in_roster)} jugadores")
            
            # Agregar información del equipo a cada jugador
            for player in players_in_roster:
                player["team_code"] = team_code
                player["team_name"] = team_name
                all_players.append(player)
        
        logger.info(f"Total de jugadores extraídos de rosters: {len(all_players)}")
        
        return {"players": all_players}
        
    except EuroleagueClientError as e:
        logger.error(f"Error al obtener datos de equipos: {str(e)}")
        raise PlayerIngestError(f"Error al obtener datos de jugadores: {str(e)}") from e


def validate_player_data(player_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos del jugador contienen los campos requeridos.

    Args:
        player_data: Diccionario con datos del jugador (formato XML parseado)

    Returns:
        True si los datos son válidos, False si faltan campos requeridos.
    """
    # Campos requeridos en formato XML (@name, @code)
    has_code = "@code" in player_data or "code" in player_data
    has_name = "@name" in player_data or "name" in player_data
    has_team_code = "team_code" in player_data  # Agregado por fetch_players_from_teams_roster
    
    return has_code and has_name and has_team_code


def transform_player_data(api_player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transformar datos de jugador desde el formato de roster XML al formato del modelo SQLAlchemy.

    Estructura XML parseada:
    {
        "@code": "006590",
        "@name": "BEAUBOIS, RODRIGUE",
        "@alias": "Beaubois",
        "@dorsal": "1",
        "@position": "Guard",
        "@countrycode": "FRA",
        "@countryname": "France",
        "team_code": "IST",  # Agregado por fetch_players_from_teams_roster
        "team_name": "Anadolu Efes Istanbul"
    }

    Args:
        api_player: Diccionario con datos del jugador desde el roster XML

    Returns:
        Diccionario con datos transformados para el modelo Player

    Raises:
        PlayerTransformationError: Si la transformación falla
    """
    try:
        # Validar datos requeridos
        if not validate_player_data(api_player):
            logger.warning(f"Jugador con datos incompletos: {api_player}. Se rechazará.")
            raise PlayerTransformationError(f"Campos requeridos faltantes en jugador")

        # Extraer datos del formato XML (@prefijo)
        player_code = api_player.get("@code") or api_player.get("code")
        player_name = api_player.get("@name") or api_player.get("name")
        position = api_player.get("@position") or api_player.get("position")
        team_code = api_player.get("team_code")
        
        transformed = {
            "player_code": str(player_code).strip(),  # Código de Euroleague API
            "name": str(player_name).strip(),
            "team_code": str(team_code).strip(),  # Retenemos el código del equipo para lookup
            "position": str(position).strip() if position else None,
            "height": None,  # No disponible en el roster XML
            "birth_date": None,  # No disponible en el roster XML
        }

        # Validar que el nombre no esté vacío
        if not transformed["name"]:
            raise PlayerTransformationError(f"Nombre de jugador vacío: {api_player}")

        logger.debug(f"Jugador transformado: {transformed['player_code']} - {transformed['name']}")
        return transformed

    except PlayerTransformationError:
        raise
    except Exception as e:
        logger.error(f"Error transformando datos de jugador {api_player}: {str(e)}")
        raise PlayerTransformationError(
            f"Error transformando datos de jugador: {str(e)}"
        ) from e


async def get_team_id_by_code(session: AsyncSession, team_code: str) -> Optional[int]:
    """
    Obtener el ID del equipo por su código.

    Args:
        session: Sesión de base de datos asincrónica
        team_code: Código del equipo (ej: 'IST', 'MAD', etc.)

    Returns:
        ID del equipo si existe, None en caso contrario
    """
    try:
        stmt = select(Team.id).where(Team.code == team_code)
        result = await session.execute(stmt)
        team_id = result.scalar_one_or_none()
        return team_id
    except SQLAlchemyError as e:
        logger.error(f"Error obteniendo ID de equipo para código '{team_code}': {str(e)}")
        return None


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
        # Obtener el ID del equipo por su código
        team_code = player_data.get("team_code")
        team_id = await get_team_id_by_code(session, team_code)
        
        if not team_id:
            raise PlayerPersistenceError(
                f"El equipo con código '{team_code}' no existe en la base de datos"
            )

        # Buscar jugador existente por player_code
        stmt = select(Player).where(Player.player_code == player_data["player_code"])
        result = await session.execute(stmt)
        existing_player = result.scalar_one_or_none()

        if existing_player:
            # Actualizar jugador existente
            logger.info(
                f"Actualizando jugador existente: {player_data['player_code']} - {player_data['name']}"
            )
            existing_player.name = player_data["name"]
            existing_player.team_id = team_id
            existing_player.position = player_data.get("position")
            existing_player.height = player_data.get("height")
            existing_player.birth_date = player_data.get("birth_date")
            existing_player.updated_at = datetime.utcnow()
            await session.flush()
            return existing_player
        else:
            # Crear nuevo jugador
            logger.info(f"Insertando nuevo jugador: {player_data['player_code']} - {player_data['name']}")
            new_player = Player(
                player_code=player_data["player_code"],
                name=player_data["name"],
                team_id=team_id,
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
        # Paso 1: Obtener datos de jugadores desde los rosters de equipos
        logger.info("=== Iniciando ingesta de jugadores ===")
        api_response = await fetch_players_from_teams_roster(client)

        # Extraer lista de jugadores de la respuesta
        players_list = api_response.get("players", [])
        if not players_list:
            logger.warning(f"No se obtuvieron jugadores. Respuesta: {api_response}")
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
                    stmt = select(Player).where(Player.player_code == transformed["player_code"])
                    result = await session.execute(stmt)
                    existing_player = result.scalar_one_or_none()

                    # Upsert
                    await upsert_player(session, transformed)

                    if existing_player:
                        stats["updated"] += 1
                        logger.debug(f"Jugador actualizado: {transformed['player_code']}")
                    else:
                        stats["inserted"] += 1
                        logger.debug(f"Jugador insertado: {transformed['player_code']}")

                except (PlayerTransformationError, PlayerPersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(
                        f"Error procesando jugador {player_data.get('@code', 'UNKNOWN')}: {str(e)}"
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
