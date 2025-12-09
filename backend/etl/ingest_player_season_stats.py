"""
ETL Script: Ingesta de estadísticas de jugadores por temporada.

Obtiene estadísticas agregadas de jugadores y las guarda en la BD.
Se ejecuta diariamente a las 7 AM.
"""

import asyncio
import logging
from typing import List, Dict, Any
from euroleague_api.player_stats import PlayerStats
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Player, PlayerSeasonStats

logger = logging.getLogger(__name__)


async def get_player_season_stats_from_api(season: int = 2025) -> List[Dict[str, Any]]:
    """
    Obtiene estadísticas de temporada de jugadores desde euroleague_api.
    
    Args:
        season: Temporada a procesar (default: 2025).
        
    Returns:
        Lista de diccionarios con estadísticas.
    """
    try:
        logger.info(f"Obteniendo estadísticas de temporada {season} desde euroleague_api...")
        
        player_stats = PlayerStats(competition="E")
        
        # Obtener stats tradicionales acumuladas
        stats_df = player_stats.get_player_stats_single_season(
            endpoint='traditional',
            season=season,
            statistic_mode='Accumulated'  # Estadísticas totales acumuladas
        )
        
        if stats_df is None or stats_df.empty:
            logger.warning(f"No se obtuvieron stats para temporada {season}")
            return []
        
        stats_list = []
        for _, row in stats_df.iterrows():
            player_id = row.get('player.code') or row.get('PlayerID') or row.get('PlayerId')
            
            if not player_id:
                logger.debug(f"Saltando stat sin player_id: {row.to_dict()}")
                continue
            
            stat_entry = {
                'player_code': str(player_id),
                'season': f"E{season}",
                'games_played': int(row.get('gamesPlayed', 0)) if row.get('gamesPlayed') is not None else 0,
                'points': float(row.get('pointsScored', 0.0)) if row.get('pointsScored') is not None else 0.0,
                'rebounds': float(row.get('totalRebounds', 0.0)) if row.get('totalRebounds') is not None else 0.0,
                'assists': float(row.get('assists', 0.0)) if row.get('assists') is not None else 0.0,
                'steals': float(row.get('steals', 0.0)) if row.get('steals') is not None else 0.0,
                'blocks': float(row.get('blocks', 0.0)) if row.get('blocks') is not None else 0.0,
                'turnovers': float(row.get('turnovers', 0.0)) if row.get('turnovers') is not None else 0.0,
                'threePointsMade': float(row.get('threePointersMade', 0.0)) if row.get('threePointersMade') is not None else 0.0,
                'pir': float(row.get('pir', 0.0)) if row.get('pir') is not None else 0.0,
            }
            stats_list.append(stat_entry)
        
        logger.info(f"Obtenidas estadísticas de {len(stats_list)} jugadores de la API")
        return stats_list
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de API: {e}")
        raise


async def upsert_player_season_stats(stats: List[Dict[str, Any]]) -> int:
    """
    Inserta o actualiza estadísticas de temporada en la BD.
    
    Args:
        stats: Lista de diccionarios con estadísticas.
        
    Returns:
        Número de registros procesados.
    """
    try:
        async with async_session_maker() as session:
            count = 0
            
            for stat_data in stats:
                player_code = stat_data.get('player_code', '').strip()
                season = stat_data.get('season', '')
                
                if not player_code or not season:
                    logger.warning(f"Saltando stat con datos incompletos: {stat_data}")
                    continue
                
                # Buscar jugador (usando text())
                stmt = text("SELECT id, name FROM players WHERE player_code = :player_code")
                result = await session.execute(stmt, {"player_code": player_code})
                player = result.fetchone()
                
                if not player:
                    logger.debug(f"Jugador no encontrado: {player_code}")
                    continue
                
                # Buscar stats existentes
                stmt = text("SELECT id FROM player_season_stats WHERE player_id = :player_id AND season = :season")
                result = await session.execute(stmt, {"player_id": player.id, "season": season})
                existing_stats = result.fetchone()
                
                if existing_stats:
                    # Actualizar
                    update_stmt = text("""
                        UPDATE player_season_stats 
                        SET games_played = :games_played, points = :points, rebounds = :rebounds, 
                            assists = :assists, steals = :steals, blocks = :blocks, 
                            turnovers = :turnovers, "threePointsMade" = :threePointsMade, pir = :pir,
                            updated_at = NOW()::text
                        WHERE id = :id
                    """)
                    await session.execute(update_stmt, {
                        "games_played": stat_data.get('games_played', 0),
                        "points": stat_data.get('points', 0.0),
                        "rebounds": stat_data.get('rebounds', 0.0),
                        "assists": stat_data.get('assists', 0.0),
                        "steals": stat_data.get('steals', 0.0),
                        "blocks": stat_data.get('blocks', 0.0),
                        "turnovers": stat_data.get('turnovers', 0.0),
                        "threePointsMade": stat_data.get('threePointsMade', 0.0),
                        "pir": stat_data.get('pir', 0.0),
                        "id": existing_stats.id
                    })
                    logger.debug(f"Actualizando stats: {player.name}")
                else:
                    # Crear nuevo
                    insert_stmt = text("""
                        INSERT INTO player_season_stats (
                            player_id, season, games_played, points, rebounds, assists, 
                            steals, blocks, turnovers, "threePointsMade", pir
                        ) VALUES (
                            :player_id, :season, :games_played, :points, :rebounds, :assists, 
                            :steals, :blocks, :turnovers, :threePointsMade, :pir
                        )
                    """)
                    await session.execute(insert_stmt, {
                        "player_id": player.id,
                        "season": season,
                        "games_played": stat_data.get('games_played', 0),
                        "points": stat_data.get('points', 0.0),
                        "rebounds": stat_data.get('rebounds', 0.0),
                        "assists": stat_data.get('assists', 0.0),
                        "steals": stat_data.get('steals', 0.0),
                        "blocks": stat_data.get('blocks', 0.0),
                        "turnovers": stat_data.get('turnovers', 0.0),
                        "threePointsMade": stat_data.get('threePointsMade', 0.0),
                        "pir": stat_data.get('pir', 0.0)
                    })
                    logger.debug(f"Creando stats: {player.name}")
                
                count += 1
            
            # Commit final
            await session.commit()
            logger.info(f"Insertadas/actualizadas estadísticas de {count} jugadores")
            return count
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error insertando estadísticas en BD: {e}")
        
        # Detectar errores de conexión específicos y proporcionar contexto útil
        if 'temporary failure in name resolution' in error_msg or 'name resolution' in error_msg:
            logger.error("❌ Error de resolución DNS: No se puede resolver el hostname de la base de datos")
            logger.error("   Verifica que DATABASE_URL esté configurado correctamente en GitHub Secrets")
            logger.error("   Formato esperado: postgresql+asyncpg://user:pass@ep-xxx.neon.tech/dbname?ssl=require")
        elif 'connection' in error_msg or 'timeout' in error_msg or 'network' in error_msg:
            logger.error("❌ Error de conexión a la base de datos")
            logger.error("   Verifica que el hostname de Neon sea accesible desde GitHub Actions")
            logger.error("   Verifica que DATABASE_URL tenga el formato correcto")
        elif 'authentication' in error_msg or 'password' in error_msg:
            logger.error("❌ Error de autenticación con la base de datos")
            logger.error("   Verifica que las credenciales en DATABASE_URL sean correctas")
        
        try:
            await session.rollback()
        except Exception:
            pass  # Si ya falló la conexión, rollback puede fallar también
        raise


async def run_ingest_player_season_stats(season: int = 2025):
    """
    Ejecuta el proceso completo de ingesta de estadísticas.
    
    Args:
        season: Temporada a procesar (default: 2025).
    """
    try:
        logger.info(f"Iniciando ETL de estadísticas para temporada {season}...")
        
        # Obtener datos de API
        stats = await get_player_season_stats_from_api(season=season)
        
        if not stats:
            logger.warning("No hay estadísticas para procesar")
            return
        
        # Guardar en BD
        count = await upsert_player_season_stats(stats)
        
        logger.info(f"ETL de estadísticas completado: {count} registros procesados")
        
    except Exception as e:
        logger.error(f"Error en ETL de estadísticas: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingest_player_season_stats())
