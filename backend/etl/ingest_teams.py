"""
ETL Script: Ingesta de equipos desde euroleague_api.

Obtiene lista de equipos de Euroleague y los guarda en la BD.
Se ejecuta diariamente a las 7 AM.
"""

import asyncio
import logging
from typing import List, Dict, Any
from euroleague_api.standings import Standings
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Team

logger = logging.getLogger(__name__)


async def get_teams_from_api(season: int = 2025) -> List[Dict[str, Any]]:
    """
    Obtiene lista de equipos desde euroleague_api.
    
    Args:
        season: Temporada a procesar (default: 2025).
    
    Returns:
        Lista de diccionarios con información de equipos.
    """
    try:
        logger.info(f"Obteniendo equipos desde euroleague_api para temporada {season}...")
        standings = Standings(competition="E")
        
        # Obtener standings de la última ronda (ronda 34 es típica en Euroleague)
        # Intentamos con diferentes rondas hasta encontrar una que funcione
        standings_df = None
        for round_num in [34, 30, 25, 20, 15, 10, 5, 1]:
            try:
                standings_df = standings.get_standings(season=season, round_number=round_num)
                if standings_df is not None and not standings_df.empty:
                    logger.info(f"Standings obtenidos de la ronda {round_num}")
                    break
            except Exception as e:
                logger.debug(f"Ronda {round_num} no disponible: {e}")
                continue
        
        if standings_df is None or standings_df.empty:
            # Fallback: obtener equipos desde gamecodes_season
            logger.info("Intentando obtener equipos desde gamecodes_season...")
            games_df = standings.get_gamecodes_season(season=season)
            if games_df is not None and not games_df.empty:
                logger.debug(f"Columnas disponibles en games: {list(games_df.columns)}")
                # Buscar columnas de equipos
                home_team_col = None
                home_code_col = None
                away_team_col = None
                away_code_col = None
                
                for col in games_df.columns:
                    col_lower = str(col).lower()
                    if 'home' in col_lower and 'team' in col_lower and 'code' not in col_lower:
                        home_team_col = col
                    elif 'home' in col_lower and ('code' in col_lower or 'abbreviation' in col_lower):
                        home_code_col = col
                    elif 'away' in col_lower and 'team' in col_lower and 'code' not in col_lower:
                        away_team_col = col
                    elif 'away' in col_lower and ('code' in col_lower or 'abbreviation' in col_lower):
                        away_code_col = col
                
                if home_team_col and home_code_col:
                    home_teams = games_df[[home_team_col, home_code_col]].drop_duplicates()
                    home_teams.columns = ['Team', 'TeamCode']
                    if away_team_col and away_code_col:
                        away_teams = games_df[[away_team_col, away_code_col]].drop_duplicates()
                        away_teams.columns = ['Team', 'TeamCode']
                        standings_df = home_teams.merge(away_teams, how='outer', on=['Team', 'TeamCode']).drop_duplicates()
                    else:
                        standings_df = home_teams
        
        if standings_df is None or standings_df.empty:
            logger.warning("No se obtuvieron equipos de la API")
            return []
        
        # Detectar nombres de columnas (pueden variar)
        logger.debug(f"Columnas disponibles en standings: {list(standings_df.columns)}")
        
        # Buscar columnas de equipo (variaciones posibles)
        team_name_col = None
        team_code_col = None
        
        # Primero buscar columnas con formato 'club.name' y 'club.code'
        if 'club.name' in standings_df.columns and 'club.code' in standings_df.columns:
            team_name_col = 'club.name'
            team_code_col = 'club.code'
        else:
            # Buscar otras variaciones
            for col in standings_df.columns:
                col_lower = str(col).lower()
                if 'team' in col_lower and ('name' in col_lower or col_lower == 'team'):
                    team_name_col = col
                elif 'team' in col_lower and ('code' in col_lower or 'abbreviation' in col_lower):
                    team_code_col = col
                elif 'club' in col_lower and 'name' in col_lower:
                    team_name_col = col
                elif 'club' in col_lower and 'code' in col_lower:
                    team_code_col = col
        
        if not team_name_col or not team_code_col:
            logger.error(f"No se encontraron columnas de equipo. Columnas disponibles: {list(standings_df.columns)}")
            return []
        
        # Extraer equipos únicos
        teams_df = standings_df[[team_name_col, team_code_col]].drop_duplicates()
        teams_df.columns = ['Team', 'TeamCode']
        teams = teams_df.to_dict('records')
        
        logger.info(f"Obtenidos {len(teams)} equipos de la API")
        return teams
        
    except Exception as e:
        logger.error(f"Error obteniendo equipos de API: {e}")
        raise


async def upsert_teams(teams: List[Dict[str, Any]]) -> int:
    """
    Inserta o actualiza equipos en la BD.
    
    Args:
        teams: Lista de diccionarios con equipos.
        
    Returns:
        Número de equipos procesados.
    """
    try:
        async with async_session_maker() as session:
            count = 0
            
            for team_data in teams:
                # Extraer datos
                code = str(team_data.get('TeamCode', '')).upper().strip()
                name = str(team_data.get('Team', '')).strip()
                
                if not code or not name or code == 'NAN' or name == 'NAN':
                    logger.warning(f"Saltando equipo con datos incompletos: {team_data}")
                    continue
                
                # Buscar equipo existente (usando text() para evitar caché de statements)
                # SELECT teams.id, teams.code, teams.name, teams.logo_url, teams.created_at, teams.updated_at 
                # FROM teams WHERE teams.code = :code
                stmt = text("SELECT id, code, name FROM teams WHERE code = :code")
                result = await session.execute(stmt, {"code": code})
                existing_row = result.fetchone()
                
                if existing_row:
                    # Actualizar solo si el nombre cambió
                    if existing_row.name != name:
                        # UPDATE
                        update_stmt = text("UPDATE teams SET name = :name WHERE id = :id")
                        await session.execute(update_stmt, {"name": name, "id": existing_row.id})
                        logger.debug(f"Actualizando equipo: {code}")
                else:
                    # Crear nuevo
                    # INSERT
                    insert_stmt = text("INSERT INTO teams (code, name) VALUES (:code, :name)")
                    await session.execute(insert_stmt, {"code": code, "name": name})
                    logger.debug(f"Creando equipo: {code} - {name}")
                
                count += 1
            
            # Commit final
            await session.commit()
            logger.info(f"Insertados/actualizados {count} equipos en BD")
            return count
            
    except Exception as e:
        logger.error(f"Error insertando equipos en BD: {e}")
        await session.rollback()
        raise


async def run_ingest_teams(season: int = 2025):
    """
    Ejecuta el proceso completo de ingesta de equipos.
    
    Args:
        season: Temporada a procesar (default: 2025).
    """
    try:
        logger.info(f"Iniciando ETL de equipos para temporada {season}...")
        
        # Obtener datos de API
        teams = await get_teams_from_api(season=season)
        
        if not teams:
            logger.warning("No hay equipos para procesar")
            return
        
        # Guardar en BD
        count = await upsert_teams(teams)
        
        logger.info(f"ETL de equipos completado: {count} equipos procesados")
        
    except Exception as e:
        logger.error(f"Error en ETL de equipos: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingest_teams())
