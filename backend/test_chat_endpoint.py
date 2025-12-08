#!/usr/bin/env python3
"""
Script para probar el endpoint /chat directamente
"""
import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import async_session_maker
from app.routers.chat import _get_schema_context, _execute_sql
from app.services.text_to_sql import TextToSQLService
from sqlalchemy import text

async def main():
    async with async_session_maker() as session:
        # Obtener contexto de esquema
        print("1. Obteniendo contexto de esquema...")
        schema_context = await _get_schema_context(session)
        print(f"Contexto: {schema_context[:100]}...")
        
        # Generar SQL
        print("\n2. Generando SQL...")
        query = "Cual es el maximo anotador de esta temporada?"
        service = TextToSQLService(api_key=settings.openrouter_api_key)
        
        sql, viz_type, error = await service.generate_sql_with_fallback(
            query=query,
            schema_context=schema_context,
            conversation_history=None
        )
        
        if error:
            print(f"ERROR: {error}")
            return
        
        print(f"SQL generado:\n{sql}")
        
        if "2022" in sql:
            print("\n❌ PROBLEMA: SQL contiene 2022")
        else:
            print("\n✅ OK: SQL no contiene 2022")
        
        # Ejecutar SQL
        print("\n3. Ejecutando SQL...")
        data = await _execute_sql(session, sql)
        print(f"Resultado: {json.dumps(data, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())

