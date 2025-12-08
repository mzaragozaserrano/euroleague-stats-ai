import logging
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/init")
async def init_check() -> Dict[str, Any]:
    """
    Verifica si la BD está inicializada y ejecuta ETL si es necesario.
    
    Returns:
        {
            "status": "ready" | "initializing" | "error",
            "has_teams": bool,
            "has_players": bool,
            "message": str
        }
    """
    try:
        async with async_session_maker() as session:
            # Verificar si hay equipos
            teams_result = await session.execute(
                text("SELECT COUNT(*) FROM teams")
            )
            teams_count = teams_result.scalar() or 0
            
            # Verificar si hay jugadores
            players_result = await session.execute(
                text("SELECT COUNT(*) FROM players WHERE player_code IS NOT NULL")
            )
            players_count = players_result.scalar() or 0
            
            logger.info(
                f"Estado BD: {teams_count} equipos, {players_count} jugadores"
            )
            
            # Si hay datos suficientes, está listo
            if teams_count > 0 and players_count > 0:
                return {
                    "status": "ready",
                    "has_teams": True,
                    "has_players": True,
                    "message": "Base de datos inicializada correctamente",
                }
            
            # Si no hay datos, ejecutar ETL en background
            logger.info("BD no inicializada. Ejecutando ETL automáticamente...")
            
            # Ejecutar ETL en background (no bloquear la respuesta)
            asyncio.create_task(_run_etl_async())
            
            return {
                "status": "initializing",
                "has_teams": teams_count > 0,
                "has_players": players_count > 0,
                "message": "Inicializando base de datos. Esto puede tardar unos minutos...",
            }
            
    except Exception as e:
        logger.error(f"Error verificando inicialización: {e}", exc_info=True)
        return {
            "status": "error",
            "has_teams": False,
            "has_players": False,
            "message": f"Error verificando BD: {str(e)[:100]}",
        }


async def _run_etl_async():
    """
    Ejecuta el ETL en background.
    No bloquea la respuesta HTTP.
    """
    try:
        logger.info("=== Iniciando ETL automático ===")
        
        # Importar aquí para evitar circular imports
        from etl.ingest_teams import ingest_teams
        from etl.ingest_players import ingest_players
        
        # Ejecutar ETLs
        teams_result = await ingest_teams()
        logger.info(f"ETL equipos: {teams_result.get('status')}")
        
        if teams_result.get("status") == "success":
            players_result = await ingest_players()
            logger.info(f"ETL jugadores: {players_result.get('status')}")
        
        logger.info("=== ETL automático completado ===")
        
    except Exception as e:
        logger.error(f"Error ejecutando ETL automático: {e}", exc_info=True)


@router.get("/init/status")
async def init_status() -> Dict[str, Any]:
    """
    Obtiene el estado actual de inicialización sin ejecutar ETL.
    
    Returns:
        Estado actual de la BD
    """
    try:
        async with async_session_maker() as session:
            teams_result = await session.execute(
                text("SELECT COUNT(*) FROM teams")
            )
            teams_count = teams_result.scalar() or 0
            
            players_result = await session.execute(
                text("SELECT COUNT(*) FROM players WHERE player_code IS NOT NULL")
            )
            players_count = players_result.scalar() or 0
            
            is_ready = teams_count > 0 and players_count > 0
            
            return {
                "status": "ready" if is_ready else "initializing",
                "has_teams": teams_count > 0,
                "has_players": players_count > 0,
                "message": "Inicializando..." if not is_ready else "Listo",
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return {
            "status": "error",
            "has_teams": False,
            "has_players": False,
            "message": str(e)[:100],
        }
