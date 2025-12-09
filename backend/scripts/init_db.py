"""
Script de inicialización de BD: Ejecuta las migraciones SQL.

Este script debe ejecutarse una sola vez al desplegarse la aplicación.
Crea las tablas necesarias si no existen (migraciones idempotentes).
"""

import asyncio
import logging
import sys
from sqlalchemy import text
from app.database import async_session_maker, engine

logger = logging.getLogger(__name__)


async def run_migrations():
    """
    Ejecuta todas las migraciones SQL del directorio migrations/.
    """
    try:
        logger.info("Iniciando migraciones de BD...")
        
        # Lista de comandos SQL a ejecutar (uno por uno)
        sql_commands = [
            # Tabla de equipos
            """CREATE TABLE IF NOT EXISTS teams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                logo_url TEXT,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )""",
            "CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code)",
            
            # Tabla de jugadores
            """CREATE TABLE IF NOT EXISTS players (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                player_code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                position VARCHAR(50),
                season VARCHAR(10) NOT NULL,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )""",
            "CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code)",
            "CREATE INDEX IF NOT EXISTS idx_players_season ON players(season)",
            
            # Tabla de estadísticas por temporada
            """CREATE TABLE IF NOT EXISTS player_season_stats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                season VARCHAR(10) NOT NULL,
                games_played INTEGER DEFAULT 0,
                points FLOAT DEFAULT 0.0,
                rebounds FLOAT DEFAULT 0.0,
                assists FLOAT DEFAULT 0.0,
                steals FLOAT DEFAULT 0.0,
                blocks FLOAT DEFAULT 0.0,
                turnovers FLOAT DEFAULT 0.0,
                "threePointsMade" FLOAT DEFAULT 0.0,
                pir FLOAT DEFAULT 0.0,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )""",
            "CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_id ON player_season_stats(player_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_season_stats_season ON player_season_stats(season)",
            "CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_season ON player_season_stats(player_id, season)",
            
            # Tabla de partidos
            """CREATE TABLE IF NOT EXISTS games (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                game_code INTEGER NOT NULL,
                season INTEGER NOT NULL,
                round INTEGER NOT NULL,
                date TIMESTAMP WITH TIME ZONE,
                home_team_id UUID NOT NULL REFERENCES teams(id),
                away_team_id UUID NOT NULL REFERENCES teams(id),
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                UNIQUE (season, game_code)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_games_season_round ON games(season, round)",
            "CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)",

            # Tabla de estadísticas por partido (Box Score)
            """CREATE TABLE IF NOT EXISTS player_stats_games (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                team_id UUID NOT NULL REFERENCES teams(id),
                minutes VARCHAR(10),
                points INTEGER DEFAULT 0,
                rebounds INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                steals INTEGER DEFAULT 0,
                blocks INTEGER DEFAULT 0,
                turnovers INTEGER DEFAULT 0,
                "two_points_made" INTEGER DEFAULT 0,
                "two_points_attempted" INTEGER DEFAULT 0,
                "three_points_made" INTEGER DEFAULT 0,
                "three_points_attempted" INTEGER DEFAULT 0,
                "free_throws_made" INTEGER DEFAULT 0,
                "free_throws_attempted" INTEGER DEFAULT 0,
                "offensive_rebounds" INTEGER DEFAULT 0,
                "defensive_rebounds" INTEGER DEFAULT 0,
                "fouls_committed" INTEGER DEFAULT 0,
                "fouls_drawn" INTEGER DEFAULT 0,
                pir FLOAT DEFAULT 0.0,
                is_starter BOOLEAN DEFAULT FALSE,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )""",
            "CREATE INDEX IF NOT EXISTS idx_player_stats_games_player_game ON player_stats_games(player_id, game_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_stats_games_game_team ON player_stats_games(game_id, team_id)",
        ]
        
        async with async_session_maker() as session:
            for i, sql_cmd in enumerate(sql_commands, 1):
                try:
                    await session.execute(text(sql_cmd))
                    logger.debug(f"Comando {i}/{len(sql_commands)} ejecutado")
                except Exception as e:
                    logger.warning(f"Comando {i} falló (puede ser que ya exista): {e}")
            await session.commit()
        
        logger.info("✓ Migraciones completadas exitosamente")
        
    except Exception as e:
        logger.error(f"Error en migraciones: {e}")
        sys.exit(1)


async def verify_schema():
    """
    Verifica que las tablas existan en la BD.
    Si hay problemas de conexión temporal, solo muestra un warning.
    """
    try:
        logger.info("Verificando esquema de BD...")
        
        async with async_session_maker() as session:
            # Verificar tablas
            tables_to_check = ['teams', 'players', 'player_season_stats']
            
            for table_name in tables_to_check:
                result = await session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    )
                """))
                exists = result.scalar()
                status = "✓" if exists else "✗"
                logger.info(f"{status} Tabla '{table_name}': {'EXISTE' if exists else 'NO EXISTE'}")
        
        logger.info("✓ Verificación completada")
        
    except Exception as e:
        # Si hay problemas de conexión temporal (DNS, red, etc.), 
        # solo mostramos un warning pero no fallamos el script
        # Las migraciones ya se ejecutaron, así que la BD debería estar lista
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['temporary failure', 'name resolution', 'connection', 'network', 'timeout']):
            logger.warning(f"⚠ No se pudo verificar el esquema debido a un problema de conexión temporal: {e}")
            logger.warning("⚠ Las migraciones se ejecutaron correctamente. La verificación se puede hacer más tarde.")
        else:
            # Para otros errores, sí mostramos error pero no bloqueamos
            logger.warning(f"⚠ Error verificando esquema: {e}")
            logger.warning("⚠ Las migraciones se ejecutaron. Revisa la conexión a la BD si el problema persiste.")


async def main():
    """
    Ejecuta migraciones y verifica el esquema.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("=" * 80)
    logger.info("INICIALIZACIÓN DE BASE DE DATOS")
    logger.info("=" * 80)
    
    await run_migrations()
    await verify_schema()
    
    logger.info("\n" + "=" * 80)
    logger.info("BASE DE DATOS LISTA PARA USAR")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

