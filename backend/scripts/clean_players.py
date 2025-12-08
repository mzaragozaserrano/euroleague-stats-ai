"""
Script para limpiar la tabla players (eliminar datos existentes)
y prepararse para el nuevo ETL con player_code
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

async def clean_players_table():
    """Limpiar la tabla players"""
    try:
        async with engine.begin() as conn:
            logger.info("Limpiando tabla players...")
            
            # Eliminar todos los jugadores
            await conn.execute(text("DELETE FROM players"))
            logger.info("OK: Tabla players limpiada")
            
        logger.info("Limpieza completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en limpieza: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(clean_players_table())
    exit(0 if success else 1)

