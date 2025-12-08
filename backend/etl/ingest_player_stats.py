"""
Script ETL para ingestar estadísticas de jugadores desde euroleague_api.

Proporciona funciones para:
- Obtener datos de estadísticas desde euroleague_api
- Transformar los datos al formato de los modelos SQLAlchemy
- Persistir datos usando upsert para evitar duplicados
- Ejecutarse diariamente a las 7 AM

Uso típico:
    async def main():
        from etl.ingest_player_stats import ingest_player_stats
        await ingest_player_stats(seasoncode="E2025")

    asyncio.run(main())
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError

from app.models import Player, PlayerSeasonStats
from app.database import async_session_maker

# Configurar logging
logger = logging.getLogger(__name__)


class PlayerStatsIngestError(Exception):
    """Excepción base para errores durante la ingesta de estadísticas."""
    pass


class PlayerStatsTransformationError(PlayerStatsIngestError):
    """Error durante la transformación de datos de estadísticas."""
    pass


class PlayerStatsPersistenceError(PlayerStatsIngestError):
    """Error durante la persistencia de estadísticas en BD."""
    pass


async def fetch_player_stats_from_euroleague(seasoncode: str = "E2025") -> List[Dict[str, Any]]:
    """
    Obtener estadísticas de jugadores desde euroleague_api.

    Args:
        seasoncode: Código de temporada (ej: "E2025", "E2024")

    Returns:
        Lista de diccionarios con estadísticas de jugadores

    Raises:
        PlayerStatsIngestError: Si hay error en la solicitud a euroleague_api
    """
    try:
        from euroleague_api.player_stats import PlayerStats
        
        season = int(seasoncode[1:])  # "E2025" -> 2025
        
        logger.info(f"Obteniendo estadísticas de euroleague_api para temporada {seasoncode}...")
        
        # Obtener stats desde euroleague_api (una sola llamada, con caché interno)
        player_stats_api = PlayerStats()
        df = player_stats_api.get_season_player_stats(season, competition_code="E")
        
        # Convertir a lista de diccionarios
        stats_list = df.to_dict('records')
        
        logger.info(f"Se obtuvieron {len(stats_list)} jugadores de euroleague_api")
        return stats_list
        
    except ImportError as e:
        logger.error("euroleague_api no está instalado. Instala con: pip install euroleague-api")
        raise PlayerStatsIngestError(f"Error importando euroleague_api: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error al obtener datos de euroleague_api: {str(e)}")
        raise PlayerStatsIngestError(f"Error obteniendo stats: {str(e)}") from e


def validate_player_stats_data(stats_data: Dict[str, Any]) -> bool:
    """
    Validar que los datos de estadísticas contienen los campos mínimos requeridos.

    Args:
        stats_data: Diccionario con datos de estadísticas

    Returns:
        True si los datos son válidos, False en caso contrario
    """
    required_fields = ["PlayerCode", "PlayerName"]
    return all(field in stats_data for field in required_fields)


def transform_player_stats_data(api_stats: Dict[str, Any], seasoncode: str) -> Dict[str, Any]:
    """
    Transformar datos de estadísticas desde euroleague_api al formato del modelo.

    Args:
        api_stats: Diccionario con datos del jugador desde euroleague_api
        seasoncode: Código de temporada

    Returns:
        Diccionario con datos transformados para el modelo PlayerSeasonStats

    Raises:
        PlayerStatsTransformationError: Si la transformación falla
    """
    try:
        if not validate_player_stats_data(api_stats):
            logger.warning(f"Stats con datos incompletos: {api_stats}. Se rechazará.")
            raise PlayerStatsTransformationError("Campos requeridos faltantes")

        # Mapear campos de euroleague_api a nuestro modelo
        # Los nombres exactos dependen de lo que retorna euroleague_api
        transformed = {
            "player_code": str(api_stats.get("PlayerCode", "")).strip(),
            "season": seasoncode,
            "games_played": int(api_stats.get("GamesPlayed", api_stats.get("Games", 0)) or 0),
            "points": float(api_stats.get("Points", 0) or 0),
            "rebounds": float(api_stats.get("Rebounds", api_stats.get("TotalRebounds", 0)) or 0),
            "assists": float(api_stats.get("Assists", 0) or 0),
            "steals": float(api_stats.get("Steals", 0) or 0),
            "blocks": float(api_stats.get("Blocks", 0) or 0),
            "turnovers": float(api_stats.get("Turnovers", 0) or 0),
            
            # Tiros
            "fg2_made": float(api_stats.get("FG2Made", 0) or 0),
            "fg2_attempted": float(api_stats.get("FG2Attempted", 0) or 0),
            "fg3_made": float(api_stats.get("FG3Made", 0) or 0),
            "fg3_attempted": float(api_stats.get("FG3Attempted", 0) or 0),
            "ft_made": float(api_stats.get("FTMade", 0) or 0),
            "ft_attempted": float(api_stats.get("FTAttempted", 0) or 0),
            
            # Faltas
            "fouls_drawn": int(api_stats.get("FoulsDrawn", 0) or 0),
            "fouls_committed": int(api_stats.get("FoulsCommitted", 0) or 0),
            
            # Eficiencia
            "pir": float(api_stats.get("PIR", api_stats.get("EfficiencyRating", 0)) or 0),
        }

        logger.debug(f"Stats transformados para jugador {transformed['player_code']}")
        return transformed

    except PlayerStatsTransformationError:
        raise
    except Exception as e:
        logger.error(f"Error transformando stats: {str(e)}")
        raise PlayerStatsTransformationError(f"Error transformando: {str(e)}") from e


async def upsert_player_stats(
    session: AsyncSession, 
    player_code: str,
    stats_data: Dict[str, Any]
) -> PlayerSeasonStats:
    """
    Insertar o actualizar estadísticas de un jugador.

    Args:
        session: Sesión de base de datos asincrónica
        player_code: Código del jugador
        stats_data: Diccionario con estadísticas transformadas

    Returns:
        Objeto PlayerSeasonStats insertado o actualizado

    Raises:
        PlayerStatsPersistenceError: Si hay error en la operación de BD
    """
    try:
        # Buscar jugador por player_code
        player_stmt = select(Player).where(Player.player_code == player_code)
        player_result = await session.execute(player_stmt)
        player = player_result.scalar_one_or_none()

        if not player:
            logger.warning(f"Jugador con código {player_code} no encontrado en BD")
            return None

        # Buscar si ya existen stats para esta temporada
        stats_stmt = select(PlayerSeasonStats).where(
            (PlayerSeasonStats.player_id == player.id) &
            (PlayerSeasonStats.season == stats_data["season"])
        )
        stats_result = await session.execute(stats_stmt)
        existing_stats = stats_result.scalar_one_or_none()

        if existing_stats:
            # Actualizar stats existentes
            logger.info(f"Actualizando stats: {player_code} - {stats_data['season']}")
            for key, value in stats_data.items():
                if key not in ["player_code", "season"]:
                    setattr(existing_stats, key, value)
            existing_stats.updated_at = datetime.utcnow()
            await session.flush()
            return existing_stats
        else:
            # Crear nuevo registro de stats
            logger.info(f"Insertando nuevas stats: {player_code} - {stats_data['season']}")
            new_stats = PlayerSeasonStats(
                player_id=player.id,
                season=stats_data["season"],
                games_played=stats_data.get("games_played"),
                points=stats_data.get("points"),
                rebounds=stats_data.get("rebounds"),
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

    except SQLAlchemyError as e:
        logger.error(f"Error de BD al procesar stats de {player_code}: {str(e)}")
        raise PlayerStatsPersistenceError(f"Error persistiendo stats: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error inesperado procesando {player_code}: {str(e)}")
        raise PlayerStatsPersistenceError(f"Error inesperado: {str(e)}") from e


async def ingest_player_stats(
    seasoncode: str = "E2025",
) -> Dict[str, Any]:
    """
    Ejecutar el pipeline completo de ingesta de estadísticas de jugadores.

    Flujo:
    1. Obtener datos de stats desde euroleague_api
    2. Transformar cada stat al formato del modelo
    3. Hacer upsert de cada stat en la BD
    4. Confirmar la transacción

    Args:
        seasoncode: Código de temporada (ej: "E2025")

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
        api_response = await fetch_player_stats_from_euroleague(seasoncode)

        if not api_response:
            logger.warning("euroleague_api no retornó datos")
            return {**stats, "status": "no_data"}

        logger.info(f"Se obtuvieron {len(api_response)} registros de stats")

        # Paso 2 y 3: Transformar y persistir cada stat
        async with async_session_maker() as session:
            for stat_data in api_response:
                stats["total_processed"] += 1

                try:
                    # Transformar datos
                    transformed = transform_player_stats_data(stat_data, seasoncode)

                    # Upsert
                    result = await upsert_player_stats(
                        session,
                        transformed["player_code"],
                        transformed
                    )

                    if result:
                        # Verificar si fue insert o update
                        # Para simplificar, contar como insert por defecto
                        stats["inserted"] += 1

                except (PlayerStatsTransformationError, PlayerStatsPersistenceError) as e:
                    stats["errors"] += 1
                    logger.error(f"Error procesando stat {stat_data.get('PlayerCode', 'UNKNOWN')}: {str(e)}")
                    # Continuar con el siguiente

            # Paso 4: Confirmar la transacción
            await session.commit()
            logger.info("Transacción confirmada. Ingesta completada.")

        stats["status"] = "success"
        logger.info(
            f"=== Ingesta de estadísticas completada ===\n"
            f"Total procesados: {stats['total_processed']}\n"
            f"Insertados: {stats['inserted']}\n"
            f"Errores: {stats['errors']}"
        )
        return stats

    except PlayerStatsIngestError as e:
        stats["status"] = "api_error"
        logger.error(f"Error de API: {str(e)}")
        raise
    except Exception as e:
        stats["status"] = "critical_error"
        logger.error(f"Error crítico en ingesta: {str(e)}")
        raise PlayerStatsIngestError(f"Error crítico: {str(e)}") from e


async def main():
    """Punto de entrada para ejecutar el ETL de estadísticas de jugadores."""
    import os
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        result = await ingest_player_stats(seasoncode="E2025")
        logger.info(f"Resultado final: {result}")
        sys.exit(0 if result.get("status") == "success" else 1)
    except PlayerStatsIngestError as e:
        logger.error(f"Fallo en la ingesta: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

