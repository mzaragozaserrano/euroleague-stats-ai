"""
Script de inicialización de BD: Ejecuta las migraciones SQL.

Este script debe ejecutarse una sola vez al desplegarse la aplicación.
Crea las tablas necesarias si no existen (migraciones idempotentes).
"""

import asyncio
import logging
import sys
import os
import socket
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Importar con manejo de errores para configuración faltante
try:
    from app.database import async_session_maker, engine
    from app.config import settings
except ValidationError as e:
    logging.basicConfig(level=logging.ERROR)
    logger.error("❌ ERROR: Configuración de base de datos faltante o inválida")
    logger.error("   Verifica que DATABASE_URL esté configurado correctamente")
    logger.error(f"   Detalles: {e}")
    sys.exit(1)
except Exception as e:
    logging.basicConfig(level=logging.ERROR)
    logger.error(f"❌ ERROR al importar módulos de base de datos: {e}")
    logger.error(f"   Tipo de error: {type(e).__name__}")
    sys.exit(1)


async def test_connection():
    """
    Prueba la conexión a la base de datos antes de ejecutar migraciones.
    """
    try:
        logger.info("Probando conexión a la base de datos...")
        
        # Verificar que DATABASE_URL esté configurado
        db_url = os.getenv("DATABASE_URL") or settings.database_url
        if not db_url:
            logger.error("❌ ERROR: DATABASE_URL no está configurado")
            logger.error("   Configura la variable de entorno DATABASE_URL")
            sys.exit(1)
        
        # Verificar formato básico de la URL
        if not db_url.startswith("postgresql+asyncpg://"):
            logger.warning("⚠️  ADVERTENCIA: DATABASE_URL no usa el formato correcto para asyncpg")
            logger.warning("   Formato esperado: postgresql+asyncpg://user:pass@host/db?ssl=require")
            logger.warning(f"   URL actual (oculta): {db_url[:30]}...")
        
        # Intentar conectar usando el engine
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        
        logger.info("✓ Conexión a la base de datos exitosa")
        return True
        
    except (OperationalError, socket.gaierror) as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ ERROR de conexión a la base de datos: {error_msg}")
        logger.error(f"   Tipo de error: {error_type}")
        
        # Detectar errores de resolución DNS/hostname
        if (error_type == "gaierror" or 
            "Temporary failure in name resolution" in error_msg or 
            "[Errno -3]" in error_msg or
            "Name or service not known" in error_msg):
            logger.error("\n🔍 DIAGNÓSTICO:")
            logger.error("   El sistema no puede resolver el hostname de la base de datos.")
            logger.error("   Posibles causas:")
            logger.error("   1. El hostname en DATABASE_URL es incorrecto o está mal formateado")
            logger.error("   2. Problemas de red/DNS en el entorno de ejecución (GitHub Actions)")
            logger.error("   3. La base de datos Neon no es accesible desde este entorno")
            logger.error("   4. El hostname contiene caracteres especiales o espacios")
            logger.error("\n💡 SOLUCIONES:")
            logger.error("   1. Verifica que DATABASE_URL esté configurado correctamente en GitHub Secrets")
            logger.error("   2. Verifica que la URL use el formato: postgresql+asyncpg://user:pass@host/db?ssl=require")
            logger.error("   3. Extrae el hostname de la URL y verifica que sea correcto:")
            try:
                db_url = os.getenv("DATABASE_URL") or settings.database_url
                if db_url:
                    # Intentar extraer hostname para diagnóstico
                    if "@" in db_url and "/" in db_url:
                        host_part = db_url.split("@")[1].split("/")[0]
                        if "?" in host_part:
                            hostname = host_part.split("?")[0]
                        else:
                            hostname = host_part
                        logger.error(f"      Hostname detectado: {hostname}")
                        logger.error(f"      Verifica que '{hostname}' sea un hostname válido de Neon")
            except Exception:
                pass
            logger.error("   4. Verifica que el hostname de Neon sea accesible desde GitHub Actions")
            logger.error("   5. Si usas Neon, verifica que no haya restricciones de firewall/IP")
        elif "password authentication failed" in error_msg.lower():
            logger.error("\n🔍 DIAGNÓSTICO:")
            logger.error("   Las credenciales de la base de datos son incorrectas.")
            logger.error("   Verifica que DATABASE_URL contenga usuario y contraseña correctos.")
        elif "does not exist" in error_msg.lower():
            logger.error("\n🔍 DIAGNÓSTICO:")
            logger.error("   La base de datos especificada no existe.")
            logger.error("   Verifica que el nombre de la base de datos en DATABASE_URL sea correcto.")
        else:
            logger.error(f"\n🔍 ERROR: {error_msg}")
        
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ ERROR inesperado al probar conexión: {error_msg}")
        logger.error(f"   Tipo de error: {error_type}")
        
        # Si es un error de DNS pero no fue capturado antes
        if "name resolution" in error_msg.lower() or "[Errno -3]" in error_msg:
            logger.error("\n🔍 DIAGNÓSTICO:")
            logger.error("   Error de resolución DNS detectado.")
            logger.error("   Verifica que DATABASE_URL contenga un hostname válido.")
        
        sys.exit(1)


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
                    error_msg = str(e)
                    # Solo mostrar warning si es un error esperado (tabla ya existe, etc.)
                    if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                        logger.debug(f"Comando {i} omitido (ya existe): {error_msg[:50]}...")
                    else:
                        logger.warning(f"Comando {i} falló: {error_msg}")
            await session.commit()
        
        logger.info("✓ Migraciones completadas exitosamente")
        
    except (OperationalError, socket.gaierror) as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ ERROR de conexión durante migraciones: {error_msg}")
        logger.error(f"   Tipo de error: {error_type}")
        if (error_type == "gaierror" or 
            "Temporary failure in name resolution" in error_msg or 
            "[Errno -3]" in error_msg):
            logger.error("   La conexión se perdió durante la ejecución de migraciones.")
            logger.error("   Verifica la conectividad de red y la configuración de DATABASE_URL.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ERROR en migraciones: {e}")
        logger.error(f"   Tipo de error: {type(e).__name__}")
        sys.exit(1)


async def verify_schema():
    """
    Verifica que las tablas existan en la BD.
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
        
    except (OperationalError, socket.gaierror) as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ ERROR de conexión al verificar esquema: {error_msg}")
        logger.error(f"   Tipo de error: {error_type}")
        if (error_type == "gaierror" or 
            "Temporary failure in name resolution" in error_msg or 
            "[Errno -3]" in error_msg):
            logger.error("   La conexión se perdió durante la verificación del esquema.")
            logger.error("   Verifica la conectividad de red y la configuración de DATABASE_URL.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ERROR verificando esquema: {e}")
        logger.error(f"   Tipo de error: {type(e).__name__}")
        sys.exit(1)


async def main():
    """
    Ejecuta migraciones y verifica el esquema.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("=" * 80)
    logger.info("INICIALIZACIÓN DE BASE DE DATOS")
    logger.info("=" * 80)
    
    # Paso 1: Probar conexión antes de ejecutar migraciones
    await test_connection()
    
    # Paso 2: Ejecutar migraciones
    await run_migrations()
    
    # Paso 3: Verificar esquema
    await verify_schema()
    
    logger.info("\n" + "=" * 80)
    logger.info("BASE DE DATOS LISTA PARA USAR")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

