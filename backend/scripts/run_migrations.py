"""
Script para ejecutar las migraciones SQL en la base de datos.

Uso:
    poetry run python scripts/run_migrations.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def run_migrations():
    """Ejecutar migraciones SQL desde el archivo de migración."""
    
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    
    if not migration_file.exists():
        logger.error(f"Archivo de migración no encontrado: {migration_file}")
        return
    
    logger.info(f"Leyendo migración: {migration_file}")
    sql_content = migration_file.read_text(encoding="utf-8")
    
    # Dividir en statements individuales
    statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]
    
    async with engine.begin() as conn:
        try:
            for i, statement in enumerate(statements, 1):
                if statement:
                    logger.info(f"Ejecutando statement {i}/{len(statements)}...")
                    await conn.execute(text(statement))
            
            logger.info("✅ Migraciones ejecutadas exitosamente")
        except Exception as e:
            logger.error(f"Error ejecutando migraciones: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(run_migrations())

