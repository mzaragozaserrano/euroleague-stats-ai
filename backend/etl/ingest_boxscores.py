"""
ETL Script: Ingesta de Box Scores (PlayerGameStats) desde euroleague_api.

Obtiene estadísticas detalladas por partido y las guarda en la BD.
Se debe ejecutar DESPUÉS de ingest_games.py e ingest_players.py.
"""

import asyncio
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from euroleague_api.boxscore_data import BoxScoreData
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Player, Game, Team

logger = logging.getLogger(__name__)

async def get_db_maps(season: int):
    """
    Obtiene mapas necesarios para FKs.
    Returns:
        player_map: {player_code: player_id}
        game_map: {game_code: game_id} para la temporada dada
        team_map: {team_code: team_id}
    """
    player_map = {}
    game_map = {}
    team_map = {}
    
    async with async_session_maker() as session:
        # Players
        # Buscamos por player_code
        result = await session.execute(select(Player.id, Player.player_code))
        for p in result.fetchall():
            player_map[str(p.player_code)] = str(p.id)
            
        # Games (solo de esta temporada)
        result = await session.execute(
            select(Game.id, Game.game_code).where(Game.season == season)
        )
        for g in result.fetchall():
            game_map[int(g.game_code)] = str(g.id)
            
        # Teams
        result = await session.execute(select(Team.id, Team.code))
        for t in result.fetchall():
            team_map[str(t.code)] = str(t.id)
            
    return player_map, game_map, team_map

async def ingest_boxscores_season(season: int):
    """
    Ingesta boxscores para una temporada.
    Usa get_player_boxscore_stats_single_season para obtener todo de una vez.
    """
    logger.info(f"Ingestando boxscores para temporada {season}...")
    
    try:
        # Obtener mapas ID
        player_map, game_map, team_map = await get_db_maps(season)
        
        boxscore_api = BoxScoreData(competition="E")
        
        # Esta llamada puede tardar un poco
        logger.info("Descargando datos masivos de stats (puede tardar)...")
        df = boxscore_api.get_player_boxscore_stats_single_season(season=season)
        
        if df is None or df.empty:
            logger.warning(f"No se encontraron stats para temporada {season}")
            return 0
            
        logger.info(f"Descargados {len(df)} registros de stats.")
        logger.debug(f"Columnas: {df.columns.tolist()}")
        
        # Columnas esperadas (basado en API):
        # Gamecode, Season, Team, Player_ID (Player Code), Player, 
        # Points, Rebounds, Assists, Steals, Turnovers, Blocks, 
        # 2FG Made, 2FG Attempted, 3FG Made, 3FG Attempted, FT Made, FT Attempted
        # Offensive Rebounds, Defensive Rebounds, Fouls Commited, Fouls Drawn, PIR, Minutes
        # Is Starter (a veces)
        
        count = 0
        async with async_session_maker() as session:
            # Preparar lista de valores para batch insert (más eficiente)
            # Pero necesitamos manejar upserts uno por uno o usar ON CONFLICT con batch?
            # SQLAlchemy asyncpg soporta executemany pero el retorno de IDs es complejo.
            # Haremos bucle por ahora, optimizable luego.
            
            for _, row in df.iterrows():
                try:
                    # IDs Externos
                    game_code = int(row.get('Gamecode', 0))
                    player_code = str(row.get('Player_ID', '')).strip() # Ojo: Player_ID en API es el code (ej: 'P001')
                    team_code = str(row.get('Team', '')).strip() # A veces es código (RM) o nombre. La API suele dar CODE aqui en stats.
                    
                    # Mapear a UUIDs internos
                    game_id = game_map.get(game_code)
                    player_id = player_map.get(player_code)
                    
                    # Team Code en DF stats suele ser 3 letras (MAD, BAR). 
                    # Nuestro DB team.code suele ser igual.
                    team_id = team_map.get(team_code)
                    
                    if not game_id:
                        if count < 5:
                            logger.warning(f"SKIP: Game ID no encontrado para code {game_code} (season {season})")
                        continue
                    
                    if not player_id:
                        if count < 5:
                            logger.warning(f"SKIP: Player ID no encontrado para code {player_code}")
                        continue
                        
                    if not team_id:
                        if count < 5:
                            logger.warning(f"SKIP: Team ID no encontrado para code {team_code}")
                        continue
                        
                    # Extraer Stats
                    minutes = str(row.get('Minutes', '00:00'))
                    points = int(row.get('Points', 0))
                    rebounds = int(row.get('Total Rebounds', row.get('Rebounds', 0)))
                    assists = int(row.get('Assists', 0))
                    steals = int(row.get('Steals', 0))
                    blocks = int(row.get('Blocks Favour', row.get('Blocks', 0))) # A veces Blocks Favour
                    turnovers = int(row.get('Turnovers', 0))
                    pir = float(row.get('Valuation', row.get('PIR', 0.0)))
                    
                    # Tiros (nombres pueden variar)
                    two_made = int(row.get('2FG Made', 0))
                    two_att = int(row.get('2FG Attempted', 0))
                    three_made = int(row.get('3FG Made', 0))
                    three_att = int(row.get('3FG Attempted', 0))
                    ft_made = int(row.get('Free Throws Made', 0))
                    ft_att = int(row.get('Free Throws Attempted', 0))
                    
                    off_reb = int(row.get('Offensive Rebounds', 0))
                    def_reb = int(row.get('Defensive Rebounds', 0))
                    
                    fouls_comm = int(row.get('Fouls Commited', 0))
                    fouls_drawn = int(row.get('Fouls Drawn', 0))
                    
                    is_starter = bool(row.get('Is Starter', 0)) # 0 o 1
                    
                    # Upsert usando DELETE + INSERT o UPDATE?
                    # No tenemos unique constraint en (player_id, game_id) en DB aun, pero creamos índice.
                    # Vamos a asumir que si corremos esto, queremos actualizar.
                    # Borramos entrada previa si existe (más limpio que update de 20 campos)
                    
                    # Opción: INSERT ON CONFLICT (player_id, game_id) UPDATE...
                    # Necesitamos constraint UNIQUE en la tabla. init_db lo creo?
                    # Init_db NO creó constraint unique, solo índice.
                    # Vamos a hacer DELETE previo.
                    
                    # Mejor: Check if exists.
                    # Para rendimiento, en volumen, DELETE x game_id primero?
                    # No, porque insertamos fila a fila.
                    
                    # Vamos a usar text() con un DELETE previo específico.
                    # DELETE FROM player_stats_games WHERE game_id = :gid AND player_id = :pid
                    
                    # Esto es lento row-by-row.
                    # Optimización: Borrar todos los stats de este game_id si es la primera vez que lo tocamos en este script?
                    # No, porque el DF viene mezclado.
                    
                    # Vamos a hacer SELECT id FROM ...
                    # Si existe, UPDATE. Si no, INSERT.
                    
                    check_stmt = text("SELECT id FROM player_stats_games WHERE game_id = :gid AND player_id = :pid")
                    res = await session.execute(check_stmt, {"gid": game_id, "pid": player_id})
                    existing = res.fetchone()
                    
                    if existing:
                        # Update
                        upd_stmt = text("""
                            UPDATE player_stats_games SET
                                team_id = :team_id, minutes = :minutes, points = :points,
                                rebounds = :rebounds, assists = :assists, steals = :steals,
                                blocks = :blocks, turnovers = :turnovers,
                                "two_points_made" = :two_made, "two_points_attempted" = :two_att,
                                "three_points_made" = :three_made, "three_points_attempted" = :three_att,
                                "free_throws_made" = :ft_made, "free_throws_attempted" = :ft_att,
                                "offensive_rebounds" = :off_reb, "defensive_rebounds" = :def_reb,
                                "fouls_committed" = :fouls_comm, "fouls_drawn" = :fouls_drawn,
                                pir = :pir, is_starter = :is_starter, updated_at = NOW()::text
                            WHERE id = :id
                        """)
                        await session.execute(upd_stmt, {
                            "team_id": team_id, "minutes": minutes, "points": points,
                            "rebounds": rebounds, "assists": assists, "steals": steals,
                            "blocks": blocks, "turnovers": turnovers,
                            "two_made": two_made, "two_att": two_att,
                            "three_made": three_made, "three_att": three_att,
                            "ft_made": ft_made, "ft_att": ft_att,
                            "off_reb": off_reb, "def_reb": def_reb,
                            "fouls_comm": fouls_comm, "fouls_drawn": fouls_drawn,
                            "pir": pir, "is_starter": is_starter,
                            "id": existing.id
                        })
                    else:
                        # Insert
                        ins_stmt = text("""
                            INSERT INTO player_stats_games (
                                id, game_id, player_id, team_id, minutes, points,
                                rebounds, assists, steals, blocks, turnovers,
                                "two_points_made", "two_points_attempted",
                                "three_points_made", "three_points_attempted",
                                "free_throws_made", "free_throws_attempted",
                                "offensive_rebounds", "defensive_rebounds",
                                "fouls_committed", "fouls_drawn",
                                pir, is_starter
                            ) VALUES (
                                gen_random_uuid(), :gid, :pid, :team_id, :minutes, :points,
                                :rebounds, :assists, :steals, :blocks, :turnovers,
                                :two_made, :two_att, :three_made, :three_att,
                                :ft_made, :ft_att,
                                :off_reb, :def_reb,
                                :fouls_comm, :fouls_drawn,
                                :pir, :is_starter
                            )
                        """)
                        await session.execute(ins_stmt, {
                            "gid": game_id, "pid": player_id, "team_id": team_id, "minutes": minutes, "points": points,
                            "rebounds": rebounds, "assists": assists, "steals": steals,
                            "blocks": blocks, "turnovers": turnovers,
                            "two_made": two_made, "two_att": two_att,
                            "three_made": three_made, "three_att": three_att,
                            "ft_made": ft_made, "ft_att": ft_att,
                            "off_reb": off_reb, "def_reb": def_reb,
                            "fouls_comm": fouls_comm, "fouls_drawn": fouls_drawn,
                            "pir": pir, "is_starter": is_starter
                        })
                    
                    count += 1
                    if count % 100 == 0:
                        logger.info(f"Procesados {count} registros...")
                        
                except Exception as e:
                    logger.error(f"Error procesando stat row: {e}")
                    continue
            
            await session.commit()
            logger.info(f"Boxscores completados para season {season}: {count} registros.")
            return count

    except Exception as e:
        logger.error(f"Error ingestando boxscores season {season}: {e}")
        return 0

async def run_ingest_boxscores(seasons: List[int] = [2023, 2024, 2025]):
    """
    Ejecuta ingesta de boxscores.
    """
    logger.info("Iniciando ETL de Box Scores...")
    
    total = 0
    for season in seasons:
        total += await ingest_boxscores_season(season)
        
    logger.info(f"ETL de Box Scores completado: {total} registros procesados")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingest_boxscores())

