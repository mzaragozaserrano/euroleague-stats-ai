"""
Script para agregar la columna player_code a la tabla players
"""
import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import text

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_player_code_column():
    """Agregar columna player_code a la tabla players"""
    try:
        async with engine.begin() as conn:
            logger.info("Agregando columna player_code a tabla players...")
            
            # Agregar columna
            await conn.execute(text(
                "ALTER TABLE players ADD COLUMN IF NOT EXISTS player_code VARCHAR(50)"
            ))
            logger.info("OK: Columna player_code agregada")
            
            # Crear índice único
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code)"
            ))
            logger.info("OK: Indice unico creado")
            
        logger.info("Migracion completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en migracion: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(add_player_code_column())
    exit(0 if success else 1)

