"""
Script ETL para ingestar datos de equipos desde la API de Euroleague.

Proporciona funciones para:
- Obtener datos de equipos desde la API de Euroleague
- Transformar los datos al formato de los modelos SQLAlchemy
- Persistir datos usando la lógica de upsert para evitar duplicados
- Manejar errores de red y base de datos

Uso típico:
    async def main():
        from etl.ingest_teams import ingest_teams
        await ingest_teams()

    asyncio.run(main())
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError

from app.models import Team
from app.database import async_session_maker
from etl.euroleague_client import EuroleagueClient, EuroleagueClientError

# Configurar logging
logger = logging.getLogger(__name__)


class TeamIngestError(Exception):
    """Excepción base para errores durante la ingesta de equipos."""

    pass


class TeamTransformationError(TeamIngestError):
    """Error durante la transformación de datos de equipos."""

    pass


class TeamPersistenceError(TeamIngestError):
    """Error durante la persistencia de equipos en BD."""

    pass


async def fetch_teams_from_api(client: Optional[EuroleagueClient] = None) -> Dict[str, Any]:
    """
    Obtener datos de equipos desde la API de Euroleague.

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.

    Returns:
        Respuesta JSON de la API con los datos de equipos.

    Raises:
        EuroleagueClientError: Si hay error en la solicitud a la API.
    """
    if client is None:
        client = EuroleagueClient()

    logger.info("Obteniendo datos de equipos desde la API de Euroleague...")
    try:
        response = await client.get_teams()
        logger.info(f"Se obtuvieron datos de equipos. Respuesta contiene: {response.keys()}")
        return response
    except EuroleagueClientError as e:
        logger.error(f"Error al obtener datos de equipos desde la API: {str(e)}")
        raise TeamIngestError(f"Error al obtener datos de equipos: {str(e)}") from e


def validate_team_data(team_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos del equipo contienen los campos requeridos.

    Args:
        team_data: Diccionario con datos del equipo

    Returns:
        True si los datos son válidos, False si faltan campos requeridos.
    """
    required_fields = ["id", "name", "code"]
    return all(field in team_data for field in required_fields)


def transform_team_data(api_team: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transformar datos de equipo desde el formato de API al formato del modelo SQLAlchemy.

    Args:
        api_team: Diccionario con datos del equipo desde la API

    Returns:
        Diccionario con datos transformados para el modelo Team

    Raises:
        TeamTransformationError: Si la transformación falla
    """
    try:
        # Validar datos requeridos
        if not validate_team_data(api_team):
            logger.warning(f"Equipo con datos incompletos: {api_team}. Se usarán valores por defecto.")
            # Retornar con valores por defecto para campos faltantes
            return {
                "code": api_team.get("code", "UNKNOWN"),
                "name": api_team.get("name", "Unknown Team"),
                "logo_url": api_team.get("logo_url", None),
            }

        transformed = {
            "code": str(api_team["code"]),
            "name": str(api_team["name"]),
            "logo_url": api_team.get("logo_url", None),
        }

        # Validar que el código y nombre no estén vacíos
        if not transformed["code"] or not transformed["name"]:
            raise TeamTransformationError(
                f"Código o nombre vacío en equipo: {api_team}"
            )

        logger.debug(f"Equipo transformado: {transformed}")
        return transformed

    except Exception as e:
        logger.error(f"Error transformando datos de equipo {api_team}: {str(e)}")
        raise TeamTransformationError(
            f"Error transformando datos de equipo: {str(e)}"
        ) from e


async def upsert_team(
    session: AsyncSession, team_data: Dict[str, Any]
) -> Team:
    """
    Insertar o actualizar un equipo en la base de datos.

    La lógica de upsert:
    - Si existe un equipo con el mismo código, actualizar sus campos
    - Si no existe, insertar como nuevo equipo

    Args:
        session: Sesión de base de datos asincrónica
        team_data: Diccionario con datos del equipo transformados

    Returns:
        Objeto Team insertado o actualizado

    Raises:
        TeamPersistenceError: Si hay error en la operación de BD
    """
    try:
        # Buscar equipo existente por código
        stmt = select(Team).where(Team.code == team_data["code"])
        result = await session.execute(stmt)
        existing_team = result.scalar_one_or_none()

        if existing_team:
            # Actualizar equipo existente
            logger.info(
                f"Actualizando equipo existente: {team_data['code']} - {team_data['name']}"
            )
            existing_team.name = team_data["name"]
            existing_team.logo_url = team_data.get("logo_url")
            existing_team.updated_at = datetime.utcnow()
            await session.flush()
            return existing_team
        else:
            # Crear nuevo equipo
            logger.info(
                f"Insertando nuevo equipo: {team_data['code']} - {team_data['name']}"
            )
            new_team = Team(
                code=team_data["code"],
                name=team_data["name"],
                logo_url=team_data.get("logo_url"),
            )
            session.add(new_team)
            await session.flush()
            return new_team

    except SQLAlchemyError as e:
        logger.error(f"Error de BD al procesar equipo {team_data}: {str(e)}")
        raise TeamPersistenceError(
            f"Error al persistir equipo en BD: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Error inesperado al procesar equipo {team_data}: {str(e)}")
        raise TeamPersistenceError(
            f"Error inesperado procesando equipo: {str(e)}"
        ) from e


async def ingest_teams(
    client: Optional[EuroleagueClient] = None,
) -> Dict[str, Any]:
    """
    Ejecutar el pipeline completo de ingesta de equipos.

    Flujo:
    1. Obtener datos de equipos desde la API
    2. Transformar cada equipo al formato del modelo
    3. Hacer upsert de cada equipo en la BD
    4. Confirmar la transacción

    Args:
        client: Cliente de Euroleague. Si es None, se crea uno nuevo.

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
        TeamIngestError: Si hay errores críticos que impiden la ingesta
    """
    stats = {"total_processed": 0, "inserted": 0, "updated": 0, "errors": 0}

    try:
        # Paso 1: Obtener datos de la API
        logger.info("=== Iniciando ingesta de equipos ===")
        api_response = await fetch_teams_from_api(client)

        # Extraer lista de equipos de la respuesta
        teams_list = api_response.get("Teams", [])
        if not teams_list:
            logger.warning("La API no retornó equipos. Respuesta: {api_response}")
            return {**stats, "status": "no_teams_found"}

        logger.info(f"Se obtuvieron {len(teams_list)} equipos de la API")

        # Paso 2 y 3: Transformar y persistir cada equipo
        async with async_session_maker() as session:
            for team_data in teams_list:
                stats["total_processed"] += 1

                try:
                    # Transformar datos
                    transformed = transform_team_data(team_data)

                    # Verificar si el equipo es nuevo o existente antes de persistir
                    stmt = select(Team).where(Team.code == transformed["code"])
                    result = await session.execute(stmt)
                    existing_team = result.scalar_one_or_none()

                    # Upsert
                    await upsert_team(session, transformed)

                    if existing_team:
                        stats["updated"] += 1
                        logger.debug(
                            f"Equipo actualizado: {transformed['code']}"
                        )
                    else:
                        stats["inserted"] += 1
                        logger.debug(
                            f"Equipo insertado: {transformed['code']}"
                        )

                except (TeamTransformationError, TeamPersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(
                        f"Error procesando equipo {team_data.get('code', 'UNKNOWN')}: {str(e)}"
                    )
                    # Continuar con el siguiente equipo

            # Paso 4: Confirmar la transacción
            await session.commit()
            logger.info("Transacción confirmada. Ingesta completada.")

        stats["status"] = "success"
        logger.info(
            f"=== Ingesta de equipos completada ===\n"
            f"Total procesados: {stats['total_processed']}\n"
            f"Insertados: {stats['inserted']}\n"
            f"Actualizados: {stats['updated']}\n"
            f"Errores: {stats['errors']}"
        )
        return stats

    except EuroleagueClientError as e:
        stats["status"] = "api_error"
        logger.error(f"Error de API: {str(e)}")
        raise TeamIngestError(f"Error de API: {str(e)}") from e
    except Exception as e:
        stats["status"] = "critical_error"
        logger.error(f"Error crítico en ingesta: {str(e)}")
        raise TeamIngestError(f"Error crítico en ingesta: {str(e)}") from e


async def main():
    """Punto de entrada para ejecutar el ETL de equipos."""
    import os
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        result = await ingest_teams()
        logger.info(f"Resultado final: {result}")
        sys.exit(0 if result.get("status") == "success" else 1)
    except TeamIngestError as e:
        logger.error(f"Fallo en la ingesta: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

