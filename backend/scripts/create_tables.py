"""
Script para crear las tablas usando SQLAlchemy models.

Uso:
    poetry run python scripts/create_tables.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import Team, Player, Game, PlayerStats
from app.models.schema_embedding import SchemaEmbedding

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def create_tables():
    """Crear todas las tablas usando SQLAlchemy."""
    
    try:
        logger.info("Creando tablas en la base de datos...")
        
        async with engine.begin() as conn:
            # Primero crear la extensión pgvector
            logger.info("Creando extensión pgvector...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Crear todas las tablas
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Tablas creadas exitosamente")
        
    except Exception as e:
        logger.error(f"Error creando tablas: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(create_tables())

