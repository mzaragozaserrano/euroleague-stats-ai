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
                schema_context = await self._get_schema_context(session)

                # Generar SQL
                logger.info("Generando SQL con LLM...")
                text_to_sql_service = TextToSQLService(
                    api_key=settings.openrouter_api_key
                )

                sql, visualization, sql_error = (
                    await text_to_sql_service.generate_sql_with_fallback(
                        query=query,
                        schema_context=schema_context,
                        conversation_history=[],
                    )
                )

                if sql_error:
                    logger.warning(f"Error en generación de SQL: {sql_error}")
                    return [TextContent(type="text", text=json.dumps({"error": sql_error}, ensure_ascii=False))]

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

    async def _get_schema_context(self, session) -> str:
        """Obtiene el contexto de esquema para el LLM."""
        try:
            result = await session.execute(
                text("""
                    SELECT content 
                    FROM schema_embeddings 
                    LIMIT 20
                """)
            )
            embeddings = result.fetchall()

            if not embeddings:
                logger.warning("No hay embeddings en BD, usando esquema por defecto")
                return self._default_schema_context()

            context = "SCHEMA METADATA FROM RAG:\n"
            for row in embeddings:
                context += f"- {row[0]}\n"

            logger.info(f"Contexto de esquema construido con {len(embeddings)} embeddings")
            return context

        except Exception as e:
            logger.error(f"Error construyendo contexto de esquema: {e}")
            return self._default_schema_context()

    @staticmethod
    def _default_schema_context() -> str:
        """Retorna el esquema por defecto cuando no hay embeddings."""
        return """
TABLES:
- teams (id, code, name, logo_url): Equipos de Euroleague.
- players (id, team_id, name, position): Jugadores y su equipo.
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score): Partidos jugados. SEASON values are integers: 2023, 2024, 2025.
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds_total, assists, fg3_made, pir): Estadisticas de jugador por partido.

KEY RELATIONSHIPS:
- player_stats_games.player_id -> players.id
- player_stats_games.game_id -> games.id
- players.team_id -> teams.id
- games.home_team_id, away_team_id -> teams.id

IMPORTANT - Season values are always INTEGERS (2023, 2024, 2025), NEVER strings like 'current'."""

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
