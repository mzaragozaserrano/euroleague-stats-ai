#!/usr/bin/env python3
"""
Script wrapper para ejecutar el servidor MCP desde cualquier directorio.
Se debe ejecutar con: poetry run python run_mcp.py
"""
import sys
import os
import asyncio
from pathlib import Path

# Agregar el directorio backend al path para las importaciones relativas
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Cargar variables de entorno desde .env si existe
env_file = backend_dir / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Ahora importar y ejecutar
from app.mcp_server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)
