"""
Servidor MCP (Model Context Protocol) para Text-to-SQL.

Expone herramientas para ejecutar consultas naturales contra la BD de Euroleague
usando el servicio de Text-to-SQL con IA.

Uso:
    poetry run python -m app.mcp_server

Configuración en Cursor (.cursor/mcp.json):
    {
      "mcpServers": {
        "text-to-sql": {
          "command": "poetry",
          "args": ["run", "python", "-m", "app.mcp_server"],
          "cwd": "${workspaceFolder}/backend"
        }
      }
    }
"""

import os
import sys
import json
import logging
import asyncio
from typing import Any
from pathlib import Path

# CRITICO: Redirigir stdout/stderr ANTES de cualquier otra importación
# para evitar que logs vayan a stdio y rompan el protocolo MCP
_log_file = Path(__file__).parent.parent / "mcp_server.log"
_log_file.parent.mkdir(exist_ok=True)

# Guardar los descriptores originales por si acaso
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Configurar logging hacia archivo en lugar de stderr para no interferir con MCP stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=str(_log_file),
    filemode='a',
    force=True  # Force reconfiguration
)
logger = logging.getLogger(__name__)

# Silenciar logs de SQLAlchemy y httpx que van a stderr
# CRITICO: Si estos logs van a stderr, pueden romper el protocolo MCP stdio
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

# Importar desde app
try:
    from app.config import settings
    from app.services.text_to_sql import TextToSQLService
    from app.services.vectorization import VectorizationService
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool
except ImportError as e:
    logger.error(f"Error importando módulos de app: {e}")
    sys.exit(1)

# Importar MCP SDK
try:
    import mcp.server.stdio
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import Tool, TextContent
except ImportError as e:
    logger.error(f"MCP SDK no instalado o versión incompatible: {e}")
    sys.exit(1)

# ============================================================================
# DATABASE ENGINE PARA MCP (SIN ECHO)
# ============================================================================
# CRITICO: Crear engine sin echo para evitar que SQLAlchemy imprima a stderr
# y rompa el protocolo MCP stdio
_mcp_engine = create_async_engine(
    settings.database_url, 
    poolclass=NullPool,
    echo=False,  # NUNCA usar echo=True en MCP server
)
_mcp_session_maker = sessionmaker(_mcp_engine, class_=AsyncSession, expire_on_commit=False)


# ============================================================================
# SERVIDOR MCP
# ============================================================================

class TextToSQLMCPServer:
    """Servidor MCP que expone herramientas para text-to-SQL."""

    def __init__(self):
        self.server = Server("text-to-sql")
        self._register_handlers()
        logger.info("Servidor MCP inicializado")

    def _register_handlers(self):
        """Registra los manejadores de herramientas."""
        
        @self.server.list_tools()
        async def list_tools():
            """Lista todas las herramientas disponibles."""
            logger.info("list_tools() invocado")
            return [
                Tool(
                    name="query_natural",
                    description="Ejecuta una consulta en lenguaje natural contra la BD de Euroleague",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "natural_query": {
                                "type": "string",
                                "description": "La pregunta en español (ej: 'Cuantos jugadores hay?')"
                            }
                        },
                        "required": ["natural_query"]
                    }
                ),
                Tool(
                    name="count_players",
                    description="Retorna el número total de jugadores en la BD",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                Tool(
                    name="list_tables",
                    description="Lista todas las tablas disponibles en la BD",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Maneja las llamadas a herramientas."""
            logger.info(f"Herramienta invocada: {name} con argumentos: {arguments}")
            
            if name == "query_natural":
                natural_query = arguments.get("natural_query", "")
                return await self._handle_query(natural_query)
            
            elif name == "count_players":
                return await self._handle_query("Cuantos jugadores hay en total?")
            
            elif name == "list_tables":
                return await self._list_tables()
            
            else:
                error_msg = f"Herramienta desconocida: {name}"
                logger.error(error_msg)
                return [TextContent(type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False))]

    async def _list_tables(self):
        """Lista todas las tablas disponibles en la BD."""
        try:
            async with _mcp_session_maker() as session:
                result = await session.execute(
                    text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                )
                tables = [row[0] for row in result.fetchall()]
                response_text = json.dumps(
                    {"tables": tables, "count": len(tables)},
                    indent=2,
                    ensure_ascii=False
                )
                return [TextContent(type="text", text=response_text)]
        except Exception as e:
            logger.error(f"Error listando tablas: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

    async def _handle_query(self, query: str):
        """Maneja una consulta: RAG → SQL Gen → Execution → Response."""
        try:
            logger.info(f"Procesando query: {query}")

            # Validar configuración
            if not settings.openrouter_api_key:
                error_msg = "OPENROUTER_API_KEY no configurada"
                logger.error(error_msg)
                return [TextContent(type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False))]

            async with _mcp_session_maker() as session:
                # Obtener contexto de esquema
                logger.info("Obteniendo contexto de esquema...")
                schema_context = await self._get_schema_context(session, query)

                # Generar SQL
                logger.info("Generando SQL con LLM...")
                text_to_sql_service = TextToSQLService(
                    api_key=settings.openrouter_api_key
                )

                # CORRECCIÓN: generate_sql_with_fallback retorna 4 valores, no 3
                sql, visualization, sql_error, direct_data = (
                    await text_to_sql_service.generate_sql_with_fallback(
                        query=query,
                        schema_context=schema_context,
                        conversation_history=[],
                    )
                )

                if sql_error:
                    logger.warning(f"Error en generación de SQL: {sql_error}")
                    return [TextContent(type="text", text=json.dumps({"error": sql_error}, ensure_ascii=False))]

                # CASO 1: Datos directos (stats de jugadores sin SQL)
                if direct_data is not None:
                    logger.info(f"Datos directos obtenidos: {len(direct_data)} registros")
                    response_data = {
                        "sql": None,
                        "data": direct_data,
                        "visualization": visualization or "table",
                        "row_count": len(direct_data),
                    }
                    response_text = json.dumps(response_data, indent=2, default=str, ensure_ascii=False)
                    return [TextContent(type="text", text=response_text)]

                # CASO 2: SQL generado
                if not sql:
                    logger.error("No se pudo generar SQL válido")
                    return [TextContent(type="text", text=json.dumps({"error": "No se pudo generar SQL válido"}, ensure_ascii=False))]

                logger.info(f"SQL generado: {sql[:100]}...")

                # Ejecutar SQL
                logger.info("Ejecutando SQL...")
                try:
                    result = await session.execute(text(sql))
                    columns = result.keys()
                    rows = result.fetchall()
                    data = [dict(zip(columns, row)) for row in rows]

                    logger.info(f"Ejecución exitosa: {len(data)} filas")

                    response_data = {
                        "sql": sql,
                        "data": data,
                        "visualization": visualization or "table",
                        "row_count": len(data),
                    }

                    response_text = json.dumps(response_data, indent=2, default=str, ensure_ascii=False)
                    return [TextContent(type="text", text=response_text)]

                except Exception as db_error:
                    logger.error(f"Error ejecutando SQL: {db_error}")
                    error_response = {
                        "error": f"Error ejecutando consulta: {str(db_error)[:100]}",
                        "sql": sql,
                    }
                    return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False))]

        except Exception as e:
            logger.exception(f"Error no esperado en MCP: {e}")
            return [TextContent(type="text", text=json.dumps({"error": f"Error interno: {str(e)[:100]}"}, ensure_ascii=False))]

    async def _get_schema_context(self, session, query: str) -> str:
        """
        Obtiene el contexto de esquema para el LLM usando RAG (Retrieval Augmented Generation).
        
        Usa búsqueda semántica por similitud para recuperar solo el esquema relevante a la consulta.
        Si RAG falla o no está disponible, usa esquema hardcodeado como fallback.
        
        Args:
            session: Sesión de base de datos.
            query: Consulta natural del usuario (para búsqueda semántica).
        
        Returns:
            Contexto de esquema como string.
        """
        # Intentar usar RAG si OpenAI API key está configurada
        if settings.openai_api_key:
            try:
                vectorization_service = VectorizationService(api_key=settings.openai_api_key)
                
                # Recuperar esquema relevante usando búsqueda semántica
                relevant_schema = await vectorization_service.retrieve_relevant_schema(
                    session=session,
                    query=query,
                    limit=10  # Top 10 resultados más relevantes
                )
                
                if relevant_schema and len(relevant_schema) > 0:
                    # Filtrar por similitud y construir contexto
                    filtered_items = [
                        item for item in relevant_schema 
                        if item.get("similarity", 0) >= 0.3
                    ]
                    
                    if filtered_items and len(filtered_items) > 0:
                        # Construir contexto con los resultados más relevantes
                        context = "SCHEMA METADATA FROM RAG (Relevant to your query):\n"
                        for item in filtered_items:
                            content = item.get("content", "")
                            context += f"- {content}\n"
                        
                        logger.info(f"✓ RAG ACTIVO: Schema context construido con {len(filtered_items)} embeddings relevantes (de {len(relevant_schema)} encontrados) para query: '{query[:50]}...'")
                        return context
                    else:
                        logger.warning(f"⚠ RAG encontró {len(relevant_schema)} resultados pero ninguno con similitud >= 0.3, usando esquema por defecto")
                        return self._default_schema_context()
                else:
                    logger.warning("⚠ RAG no retornó resultados (tabla vacía o no existe), usando esquema por defecto")
                    return self._default_schema_context()
                    
            except Exception as e:
                # Capturar cualquier error (tabla no existe, error de conexión, etc.)
                logger.warning(f"⚠ Error usando RAG (tabla puede no existir o no tener embeddings), fallback a esquema por defecto: {type(e).__name__}: {str(e)[:100]}")
                # Fallback seguro: usar esquema hardcodeado
                return self._default_schema_context()
        else:
            # Si no hay OpenAI API key, usar esquema hardcodeado
            logger.info("ℹ OPENAI_API_KEY no configurada, usando esquema por defecto (RAG desactivado)")
            return self._default_schema_context()

    @staticmethod
    def _default_schema_context() -> str:
        """Retorna el esquema por defecto cuando no hay embeddings."""
        return """
TABLES:
- teams (id, code, name, logo_url): Euroleague teams.
- players (id, team_id, name, position): Players info.
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score): Games played. SEASON values are INTEGERS: 2023, 2024, 2025.
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds, assists, three_points_made, pir): Player stats per game (Box Score). Columns are: points, rebounds, assists, three_points_made, pir.
- player_season_stats (id, player_id, season, games_played, points, rebounds, assists, "threePointsMade", pir): Aggregated stats per season. Season values are STRINGS like 'E2024', 'E2025'.

KEY RELATIONSHIPS:
- player_stats_games.player_id -> players.id
- player_stats_games.game_id -> games.id
- player_season_stats.player_id -> players.id
- players.team_id -> teams.id

IMPORTANT:
- Use 'player_season_stats' for season totals/averages. Season format is 'E2025'.
- Use 'player_stats_games' ONLY for specific game details.
- 'threePointsMade' in player_season_stats is quoted.
- 'three_points_made' in player_stats_games is snake_case."""

    async def run(self):
        """Inicia el servidor MCP."""
        logger.info("Iniciando servidor MCP Text-to-SQL...")
        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                logger.info("Servidor MCP ejecutándose en stdio")
                
                # Crear opciones de inicialización con todos los campos requeridos
                init_options = InitializationOptions(
                    server_name="text-to-sql",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {}
                    }
                )
                
                try:
                    await self.server.run(
                        read_stream, 
                        write_stream, 
                        init_options
                    )
                except Exception as e:
                    logger.error(f"Error en server.run(): {e}", exc_info=True)
                    raise
        except Exception as e:
            logger.error(f"Error en stdio_server: {e}", exc_info=True)
            raise


# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Punto de entrada principal."""
    logger.info("=== Servidor MCP Text-to-SQL ===")
    
    # Validar que DATABASE_URL esté configurada
    if not settings.database_url:
        logger.error("DATABASE_URL no está configurada en .env")
        sys.exit(1)

    logger.info("DATABASE_URL configurada")
    logger.info(f"OpenRouter API Key: {'Configurada' if settings.openrouter_api_key else 'No configurada'}")

    # Iniciar servidor
    server = TextToSQLMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor MCP terminado por usuario")
    except Exception as e:
        logger.exception(f"Error fatal en servidor MCP: {e}")
        sys.exit(1)
