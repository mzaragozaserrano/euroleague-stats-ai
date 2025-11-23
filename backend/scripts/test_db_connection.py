#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos Neon
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text


async def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        print("Probando conexión a Neon...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar_one()
            print(f"[OK] Conexión exitosa!")
            print(f"Versión de PostgreSQL: {version}")
            
            # Probar que pgvector está disponible
            try:
                result = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
                ext = result.scalar_one_or_none()
                if ext:
                    print(f"[OK] Extensión pgvector instalada")
                else:
                    print("[INFO] Extensión pgvector no instalada (se instalará más adelante)")
            except Exception as e:
                print(f"[INFO] No se pudo verificar pgvector: {e}")
                
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        print("\nVerifica:")
        print("1. Que el archivo .env existe en backend/")
        print("2. Que DATABASE_URL está configurado correctamente")
        print("3. Que la URL usa el formato: postgresql+asyncpg://...")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)

