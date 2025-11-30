#!/usr/bin/env python3
"""
Script de prueba para verificar que el MCP server devuelve JSON válido.
Uso: poetry run python test_mcp_json.py
"""
import json
import asyncio
import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

# Cargar .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

from app.mcp_server import TextToSQLMCPServer
from mcp.types import TextContent


async def test_json_validity():
    """Prueba que las respuestas del MCP sean JSON válido."""
    print("Inicializando servidor MCP...")
    server = TextToSQLMCPServer()
    
    # Simular una consulta
    test_query = "Cual es el nombre de todos los jugadores?"
    print(f"\nProbando consulta: {test_query}")
    
    try:
        result = await server._handle_query(test_query)
        
        # Verificar que sea una lista de TextContent
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) > 0, "Empty result list"
        assert isinstance(result[0], TextContent), f"Expected TextContent, got {type(result[0])}"
        
        # Verificar que el texto sea JSON válido
        response_text = result[0].text
        print(f"\nRespuesta cruda (primeros 500 chars):\n{response_text[:500]}")
        
        # Intentar parsear el JSON
        parsed = json.loads(response_text)
        print(f"\nJSON parseado exitosamente!")
        print(f"Keys: {list(parsed.keys())}")
        
        if "data" in parsed:
            print(f"Número de filas: {len(parsed['data'])}")
            if parsed['data']:
                print(f"Primera fila: {parsed['data'][0]}")
        
        # Re-serializar para verificar que no hay caracteres extraños
        re_serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
        print(f"\nRe-serialización exitosa!")
        
        # Verificar que la re-serialización sea igual a la original (ignorando espacios)
        original_compact = json.dumps(json.loads(response_text), ensure_ascii=False)
        re_compact = json.dumps(parsed, ensure_ascii=False)
        
        if original_compact == re_compact:
            print("[OK] JSON consistente")
        else:
            print("[ERROR] JSON inconsistente (posible corrupcion)")
            print(f"Original: {original_compact[:200]}")
            print(f"Re-serializado: {re_compact[:200]}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSON invalido!")
        print(f"Error: {e}")
        print(f"Posicion: {e.pos}")
        print(f"Contexto: {response_text[max(0, e.pos-50):e.pos+50]}")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_json_validity())
    sys.exit(0 if success else 1)

