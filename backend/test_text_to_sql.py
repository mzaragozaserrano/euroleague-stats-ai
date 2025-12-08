#!/usr/bin/env python3
"""
Script para probar el servicio TextToSQLService directamente
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.text_to_sql import TextToSQLService

async def main():
    # Crear servicio
    service = TextToSQLService(api_key=settings.openrouter_api_key)
    
    # Obtener el prompt
    schema_context = """
    TABLES:
    - games (id, season, round, ...): Partidos jugados. SEASON values are integers: 2023, 2024, 2025.
    """
    
    # Probar consulta
    query = "Cual es el maximo anotador de esta temporada?"
    
    print(f"Query: {query}")
    print("-" * 80)
    
    sql, viz_type, error = await service.generate_sql(
        query=query,
        schema_context=schema_context,
        conversation_history=None
    )
    
    if error:
        print(f"ERROR: {error}")
    else:
        print(f"SQL GENERADO:\n{sql}")
        print(f"\nVisualization Type: {viz_type}")
        
        # Verificar si contiene 2022
        if "2022" in sql:
            print("\n❌ PROBLEMA: SQL contiene 2022 (temporada inválida)")
        else:
            print("\n✅ OK: SQL no contiene 2022")

if __name__ == "__main__":
    asyncio.run(main())

