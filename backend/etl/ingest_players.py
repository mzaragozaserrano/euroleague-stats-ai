"""
ETL Script: Ingesta de jugadores desde euroleague_api.

Obtiene lista de jugadores y los asocia con sus equipos.
Se ejecuta diariamente a las 7 AM.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from euroleague_api.player_stats import PlayerStats
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Player, Team

logger = logging.getLogger(__name__)

# Mapeo de códigos de posición desde euroleague_api a nombres en español
POSITION_MAP = {
    # Números
    "1": "Base",
    "2": "Escolta",
    "3": "Alero",
    "4": "Ala-Pivot",
    "5": "Pivot",
    # Códigos cortos
    "G": "Base",
    "PG": "Base",
    "SG": "Escolta",
    "SF": "Alero",
    "PF": "Ala-Pivot",
    "C": "Pivot",
    # Nombres en inglés (singular y plural)
    "Guard": "Base",
    "Guards": "Base",
    "Point Guard": "Base",
    "Shooting Guard": "Escolta",
    "Forward": "Alero",
    "Forwards": "Alero",
    "Small Forward": "Alero",
    "Power Forward": "Ala-Pivot",
    "Center": "Pivot",
    "Centers": "Pivot",
    # Variaciones comunes
    "G-F": "Alero",  # Guard-Forward
    "F-C": "Ala-Pivot",  # Forward-Center
    "F": "Alero",
}


async def get_players_from_api(season: int = 2025) -> List[Dict[str, Any]]:
    """
    Obtiene lista de jugadores desde euroleague_api.
    
    Args:
        season: Temporada a procesar (default: 2025).
        
    Returns:
        Lista de diccionarios con información de jugadores.
    """
    try:
        logger.info(f"Obteniendo jugadores para temporada {season} desde euroleague_api...")
        
        # Usar PlayerStats de euroleague_api
        player_stats = PlayerStats(competition="E")
        
        # Obtener stats tradicionales de temporada (incluye todos los jugadores)
        try:
            stats_df = player_stats.get_player_stats_single_season(
                endpoint='traditional',
                season=season,
                statistic_mode='Accumulated'
            )
        except Exception as e:
            logger.error(f"Error llamando a get_player_stats_single_season: {e}")
            return []
        
        if stats_df is None or stats_df.empty:
            logger.warning(f"No se obtuvieron jugadores para temporada {season}")
            return []
            
        logger.info(f"Columnas recibidas de API jugadores: {list(stats_df.columns)}")
        
        # Verificar si hay alguna columna relacionada con posición
        position_columns = [col for col in stats_df.columns if 'position' in col.lower() or 'pos' in col.lower()]
        if position_columns:
            logger.info(f"Columnas de posición encontradas: {position_columns}")
        else:
            logger.warning("No se encontraron columnas de posición en la respuesta de la API")
            # Mostrar muestra de datos para debugging
            if len(stats_df) > 0:
                logger.info(f"Primera fila de ejemplo: {dict(stats_df.iloc[0])}")
        
        # Contadores para estadísticas
        players_with_position = 0
        players_without_position = 0
        
        players = []
        for _, row in stats_df.iterrows():
            # Extraer información del jugador usando nombres de columnas correctos
            # Las columnas vienen como 'player.code', 'player.name', 'player.team.code'
            player_id = row.get('player.code') or row.get('PlayerID') or row.get('PlayerId')
            player_name = row.get('player.name') or row.get('Player') or row.get('Name')
            team_code = row.get('player.team.code') or row.get('TeamCode') or row.get('team_code')
            
            # Buscar posición en múltiples columnas posibles
            position = (
                row.get('position') or 
                row.get('Position') or 
                row.get('player.position') or 
                row.get('player.Position') or
                row.get('Pos') or
                row.get('pos') or
                row.get('POS')
            )
            
            if not player_id or not player_name or not team_code:
                # Intentar buscar en otras columnas si falla
                logger.debug(f"Saltando jugador con datos incompletos (id={player_id}, name={player_name}, team={team_code})")
                continue
            
            # Normalizar y mapear posición
            mapped_position = None
            if position:
                position_str = str(position).strip().upper()
                # Intentar mapeo directo
                mapped_position = POSITION_MAP.get(position_str)
                # Si no está, intentar sin espacios
                if not mapped_position:
                    mapped_position = POSITION_MAP.get(position_str.replace(' ', ''))
                # Si aún no está, intentar con el valor original (puede ser que ya esté en español)
                if not mapped_position and position_str in ["BASE", "ESCOLTA", "ALERO", "ALA-PIVOT", "PIVOT"]:
                    mapped_position = position_str.capitalize()
                    if mapped_position == "Ala-pivot":
                        mapped_position = "Ala-Pivot"
                
                if mapped_position:
                    players_with_position += 1
                else:
                    players_without_position += 1
                    logger.debug(f"Posición no mapeada para {player_name}: '{position}' (original: {position_str})")
            else:
                players_without_position += 1
                logger.debug(f"Sin posición para jugador: {player_name}")
            
            player = {
                'player_id': str(player_id),
                'player_code': str(player_id),
                'name': str(player_name).strip(),
                'team_code': str(team_code).upper().strip(),
                'position': mapped_position,
            }
            players.append(player)
        
        logger.info(f"Obtenidos {len(players)} jugadores de la API")
        logger.info(f"Jugadores con posición: {players_with_position}, sin posición: {players_without_position}")
        
        logger.info(f"Obtenidos {len(players)} jugadores de la API")
        return players
        
    except Exception as e:
        logger.error(f"Error obteniendo jugadores de API: {e}")
        raise


async def upsert_players(players: List[Dict[str, Any]], season: str = "E2025") -> int:
    """
    Inserta o actualiza jugadores en la BD.
    
    Args:
        players: Lista de diccionarios con jugadores.
        season: Código de temporada (default: "E2025").
        
    Returns:
        Número de jugadores procesados.
    """
    try:
        async with async_session_maker() as session:
            count = 0
            
            for player_data in players:
                player_code = player_data.get('player_code', '').strip()
                name = player_data.get('name', '').strip()
                team_code = player_data.get('team_code', '').upper().strip()
                position = player_data.get('position')
                
                if not player_code or not name or not team_code:
                    logger.warning(f"Saltando jugador con datos incompletos: {player_data}")
                    continue
                
                # Obtener equipo (usando text())
                stmt = text("SELECT id FROM teams WHERE code = :code")
                result = await session.execute(stmt, {"code": team_code})
                team_row = result.fetchone()
                
                if not team_row:
                    logger.warning(f"Equipo no encontrado: {team_code} para jugador {name}")
                    continue
                
                team_id = team_row.id
                
                # Buscar jugador existente
                stmt = text("SELECT id, name, team_id, position, season FROM players WHERE player_code = :player_code")
                result = await session.execute(stmt, {"player_code": player_code})
                existing_player = result.fetchone()
                
                if existing_player:
                    # Actualizar si es necesario (team, season, o posición cambió)
                    needs_update = (
                        existing_player.team_id != team_id or 
                        existing_player.season != season or
                        existing_player.position != position
                    )
                    
                    if needs_update:
                        update_stmt = text("""
                            UPDATE players 
                            SET name = :name, team_id = :team_id, position = :position, season = :season, updated_at = NOW()::text
                            WHERE id = :id
                        """)
                        await session.execute(update_stmt, {
                            "name": name,
                            "team_id": team_id,
                            "position": position,
                            "season": season,
                            "id": existing_player.id
                        })
                        if existing_player.position != position:
                            logger.info(f"Actualizando posición de {name}: '{existing_player.position}' -> '{position}'")
                        else:
                            logger.debug(f"Actualizando jugador: {name}")
                else:
                    # Crear nuevo
                    insert_stmt = text("""
                        INSERT INTO players (team_id, player_code, name, position, season)
                        VALUES (:team_id, :player_code, :name, :position, :season)
                    """)
                    await session.execute(insert_stmt, {
                        "team_id": team_id,
                        "player_code": player_code,
                        "name": name,
                        "position": position,
                        "season": season
                    })
                    logger.debug(f"Creando jugador: {name}")
                
                count += 1
            
            # Commit final
            await session.commit()
            logger.info(f"Insertados/actualizados {count} jugadores en BD")
            return count
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error insertando jugadores en BD: {e}")
        
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


async def run_ingest_players(season: int = 2025):
    """
    Ejecuta el proceso completo de ingesta de jugadores.
    
    Args:
        season: Temporada a procesar (default: 2025).
    """
    try:
        logger.info(f"Iniciando ETL de jugadores para temporada {season}...")
        
        # Obtener datos de API
        players = await get_players_from_api(season=season)
        
        if not players:
            logger.warning("No hay jugadores para procesar")
            return
        
        # Guardar en BD
        season_code = f"E{season}"
        count = await upsert_players(players, season=season_code)
        
        logger.info(f"ETL de jugadores completado: {count} jugadores procesados")
        
    except Exception as e:
        logger.error(f"Error en ETL de jugadores: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingest_players())
