"""
ETL Script: Ingesta de partidos (Games) desde euroleague_api.

Obtiene metadatos de los partidos y los guarda en la BD.
Se debe ejecutar DESPUÉS de ingest_teams.py.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from euroleague_api.boxscore_data import BoxScoreData
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Game, Team

logger = logging.getLogger(__name__)

async def get_team_map() -> Dict[str, str]:
    """
    Obtiene mapa de {team_code: team_id} y {team_name: team_id} desde la BD.
    """
    team_map = {}
    async with async_session_maker() as session:
        result = await session.execute(select(Team.id, Team.code, Team.name))
        teams = result.fetchall()
        for t in teams:
            team_map[t.code] = str(t.id)
            team_map[t.name] = str(t.id)
            # Normalización extra por si acaso
            team_map[t.name.upper()] = str(t.id)
            team_map[t.code.upper()] = str(t.id)
    return team_map

async def ingest_games_season(season: int, team_map: Dict[str, str]):
    """
    Ingesta partidos de una temporada específica.
    """
    logger.info(f"Ingestando partidos para temporada {season}...")
    
    try:
        boxscore_api = BoxScoreData(competition="E")
        df = boxscore_api.get_gamecodes_season(season=season)
        
        if df is None or df.empty:
            logger.warning(f"No se encontraron partidos para temporada {season}")
            return 0
            
        # Normalizar columnas
        # Esperamos: Gamecode, Season, Round, Date, Home Team, Away Team, Score, etc.
        # Las columnas suelen ser: 'Gamecode', 'Season', 'Round', 'Date', 'Home Team', 'Away Team', 'Score'
        # A veces 'Home Team' es el nombre.
        
        logger.debug(f"Columnas encontradas: {df.columns.tolist()}")
        
        count = 0
        async with async_session_maker() as session:
            for _, row in df.iterrows():
                try:
                    game_code = int(row.get('Gamecode', 0))
                    round_num = int(row.get('Round', 0))
                    date_str = str(row.get('Date', ''))
                    
                    # Parsear fecha
                    # Formato usual: "Oct 05, 2023" o similar
                    game_date = None
                    if date_str and date_str != 'nan':
                        try:
                            game_date = pd.to_datetime(date_str).to_pydatetime()
                        except:
                            logger.warning(f"No se pudo parsear fecha: {date_str}")
                    
                    # Equipos
                    home_team_name = str(row.get('Home Team', '')).strip()
                    away_team_name = str(row.get('Away Team', '')).strip()
                    
                    home_team_id = team_map.get(home_team_name) or team_map.get(home_team_name.upper())
                    away_team_id = team_map.get(away_team_name) or team_map.get(away_team_name.upper())
                    
                    if not home_team_id:
                        # Intentar buscar por código si existe columna
                        # Pero get_gamecodes_season suele dar nombres
                        logger.warning(f"No se encontró ID para equipo local: {home_team_name}")
                        continue
                        
                    if not away_team_id:
                        logger.warning(f"No se encontró ID para equipo visitante: {away_team_name}")
                        continue
                        
                    # Score (formato "80 - 75" o similar)
                    score_str = str(row.get('Score', ''))
                    home_score = 0
                    away_score = 0
                    if score_str and '-' in score_str:
                        parts = score_str.split('-')
                        try:
                            home_score = int(parts[0].strip())
                            away_score = int(parts[1].strip())
                        except:
                            pass
                    
                    # Upsert Game
                    # Usamos ON CONFLICT (season, game_code)
                    stmt = text("""
                        INSERT INTO games (id, game_code, season, round, date, home_team_id, away_team_id, home_score, away_score, updated_at)
                        VALUES (gen_random_uuid(), :game_code, :season, :round, :date, :home_team_id, :away_team_id, :home_score, :away_score, NOW()::text)
                        ON CONFLICT (season, game_code) DO UPDATE SET
                            round = EXCLUDED.round,
                            date = EXCLUDED.date,
                            home_team_id = EXCLUDED.home_team_id,
                            away_team_id = EXCLUDED.away_team_id,
                            home_score = EXCLUDED.home_score,
                            away_score = EXCLUDED.away_score,
                            updated_at = NOW()::text
                        RETURNING id
                    """)
                    
                    await session.execute(stmt, {
                        "game_code": game_code,
                        "season": season,
                        "round": round_num,
                        "date": game_date,
                        "home_team_id": home_team_id,
                        "away_team_id": away_team_id,
                        "home_score": home_score,
                        "away_score": away_score
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando partido {row.get('Gamecode')}: {e}")
                    continue
            
            await session.commit()
            logger.info(f"Procesados {count} partidos para temporada {season}")
            return count

    except Exception as e:
        logger.error(f"Error ingestando partidos season {season}: {e}")
        return 0

async def run_ingest_games(seasons: List[int] = [2023, 2024, 2025]):
    """
    Ejecuta la ingesta de partidos para múltiples temporadas.
    """
    logger.info("Iniciando ETL de Partidos (Games)...")
    
    # Obtener mapa de equipos
    team_map = await get_team_map()
    if not team_map:
        logger.error("No se encontraron equipos en BD. Ejecuta ingest_teams.py primero.")
        return
        
    total_games = 0
    for season in seasons:
        total_games += await ingest_games_season(season, team_map)
        
    logger.info(f"ETL de Partidos completado: {total_games} partidos procesados")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingest_games())

