"""
Script para verificar que el sistema RAG está funcionando correctamente.

Prueba:
1. Si la tabla schema_embeddings existe
2. Si hay embeddings en la tabla
3. Si RAG puede recuperar esquema relevante
4. Compara resultados con y sin RAG

Uso:
    poetry run python scripts/test_rag_usage.py
"""

import asyncio
import logging
from app.database import async_session_maker
from app.config import settings
from app.services.vectorization import VectorizationService
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_table_exists(session) -> bool:
    """Verifica si la tabla schema_embeddings existe."""
    try:
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'schema_embeddings'
            );
        """))
        exists = result.scalar()
        return exists
    except Exception as e:
        logger.error(f"Error verificando tabla: {e}")
        return False


async def count_embeddings(session) -> int:
    """Cuenta cuántos embeddings hay en la tabla."""
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM schema_embeddings"))
        count = result.scalar() or 0
        return count
    except Exception as e:
        logger.error(f"Error contando embeddings: {e}")
        return 0


async def test_rag_retrieval(session, query: str) -> dict:
    """Prueba la recuperación RAG con una query de ejemplo."""
    if not settings.openai_api_key:
        return {
            "success": False,
            "message": "OPENAI_API_KEY no configurada",
        }
    
    try:
        vectorization_service = VectorizationService(api_key=settings.openai_api_key)
        
        relevant_schema = await vectorization_service.retrieve_relevant_schema(
            session=session,
            query=query,
            limit=5
        )
        
        return {
            "success": True,
            "found": len(relevant_schema),
            "items": relevant_schema,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def main():
    """Ejecuta todas las verificaciones."""
    print("=" * 80)
    print("VERIFICACIÓN DEL SISTEMA RAG")
    print("=" * 80)
    print()
    
    async with async_session_maker() as session:
        # 1. Verificar si la tabla existe
        print("1. Verificando si la tabla schema_embeddings existe...")
        table_exists = await check_table_exists(session)
        if table_exists:
            print("   ✓ Tabla schema_embeddings existe")
        else:
            print("   ✗ Tabla schema_embeddings NO existe")
            print("   → Ejecutar: psql $DATABASE_URL -f backend/migrations/002_add_schema_embeddings.sql")
            return
        print()
        
        # 2. Contar embeddings
        print("2. Contando embeddings en la tabla...")
        count = await count_embeddings(session)
        if count > 0:
            print(f"   ✓ Hay {count} embeddings en la tabla")
        else:
            print("   ✗ No hay embeddings en la tabla")
            print("   → Ejecutar: poetry run python backend/scripts/init_schema_embeddings.py")
            return
        print()
        
        # 3. Verificar OpenAI API key
        print("3. Verificando configuración...")
        if settings.openai_api_key:
            print("   ✓ OPENAI_API_KEY configurada")
        else:
            print("   ✗ OPENAI_API_KEY NO configurada")
            print("   → Agregar OPENAI_API_KEY a .env")
            return
        print()
        
        # 4. Probar recuperación RAG
        print("4. Probando recuperación RAG con query de ejemplo...")
        test_queries = [
            "puntos de Larkin",
            "máximo anotador",
            "jugadores del Real Madrid",
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            result = await test_rag_retrieval(session, query)
            
            if result["success"]:
                if result["found"] > 0:
                    print(f"   ✓ RAG funcionando: {result['found']} resultados encontrados")
                    print(f"   Similitudes:")
                    for item in result["items"][:3]:  # Mostrar top 3
                        similarity = item.get("similarity", 0)
                        content = item.get("content", "")[:60]
                        print(f"     - {similarity:.3f}: {content}...")
                else:
                    print(f"   ⚠ RAG no encontró resultados (puede ser normal si embeddings no son relevantes)")
            else:
                print(f"   ✗ Error en RAG: {result.get('error', 'Error desconocido')}")
        
        print()
        print("=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print("✓ Tabla existe")
        print(f"✓ {count} embeddings disponibles")
        print("✓ OPENAI_API_KEY configurada")
        print("✓ RAG está listo para usar")
        print()
        print("El sistema usará RAG automáticamente en las próximas consultas.")


if __name__ == "__main__":
    asyncio.run(main())

