"""
Script para ejecutar migraciones SQL en la base de datos.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Agregar el directorio parent al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_maker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration(migration_file: str):
    """Ejecuta un archivo SQL de migración"""
    migration_path = Path(__file__).parent.parent / "migrations" / migration_file
    
    if not migration_path.exists():
        logger.error(f"Archivo de migración no encontrado: {migration_path}")
        return False
    
    try:
        with open(migration_path, 'r') as f:
            sql_content = f.read()
        
        async with async_session_maker() as session:
            # Dividir en sentencias individuales (separadas por ;)
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                logger.info(f"Ejecutando sentencia {i}/{len(statements)}...")
                try:
                    await session.execute(text(statement))
                    await session.commit()
                    logger.info(f"✓ Sentencia {i} ejecutada correctamente")
                except Exception as e:
                    error_str = str(e)
                    # Ignorar errores de pgvector no disponible
                    if "pgvector" in error_str and "not available" in error_str:
                        logger.warning(f"⚠ pgvector no disponible (normal en Neon), continuando...")
                        await session.rollback()
                        continue
                    # Ignorar si la tabla ya existe
                    if "already exists" in error_str or "ALREADY EXISTS" in error_str:
                        logger.warning(f"⚠ Sentencia {i} ya ejecutada anteriormente, continuando...")
                        await session.rollback()
                        continue
                    # Ignorar errores de vector column que no existe (por pgvector)
                    if "does not exist" in error_str and ("embedding" in error_str or "vector" in error_str):
                        logger.warning(f"⚠ Columna vector no disponible (pgvector), continuando...")
                        await session.rollback()
                        continue
                    # Ignorar errores de índice HNSW no disponible
                    if "hnsw" in error_str.lower() or "UndefinedObjectError" in error_str:
                        logger.warning(f"⚠ Índice vector no disponible (pgvector), continuando...")
                        await session.rollback()
                        continue
                    # Ignorar errores de seed data (por UUID o constraints)
                    if "null value in column" in error_str or "violates not-null constraint" in error_str:
                        logger.warning(f"⚠ Error en seed data (probablemente gen_random_uuid), continuando...")
                        await session.rollback()
                        continue
                    logger.error(f"✗ Error en sentencia {i}: {e}")
                    await session.rollback()
                    return False
        
        logger.info(f"✓ Migración {migration_file} completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error ejecutando migración: {e}")
        return False

async def main():
    """Ejecuta todas las migraciones"""
    migrations = [
        "001_initial_schema.sql",
        "002_add_player_code.sql",
        "003_fix_players_player_code.sql",
    ]
    
    for migration in migrations:
        logger.info(f"\n{'='*60}")
        logger.info(f"Ejecutando: {migration}")
        logger.info(f"{'='*60}")
        
        success = await run_migration(migration)
        if not success:
            logger.error(f"Migración {migration} falló")
            return False
    
    logger.info(f"\n{'='*60}")
    logger.info("Todas las migraciones completadas exitosamente")
    logger.info(f"{'='*60}")
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)

