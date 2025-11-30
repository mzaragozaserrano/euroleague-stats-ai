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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar desde app
try:
    from app.config import settings
    from app.database import async_session_maker
    from app.services.text_to_sql import TextToSQLService
    from sqlalchemy import text
except ImportError as e:
    logger.error(f"Error importando módulos de app: {e}")
    sys.exit(1)

# Importar MCP SDK
try:
    import mcp.server.stdio
    from mcp.server import Server
    from mcp.types import Tool, TextContent, CallToolResult
except ImportError as e:
    logger.error(f"MCP SDK no instalado o versión incompatible: {e}")
    sys.exit(1)


# ============================================================================
# SERVIDOR MCP
# ============================================================================

class TextToSQLMCPServer:
    """Servidor MCP que expone herramientas para text-to-SQL."""

    def __init__(self):
        self.server = Server("text-to-sql")
        self._register_tools()
        logger.info("Servidor MCP inicializado")

    def _register_tools(self):
        """Registra las herramientas disponibles en MCP."""
        
        @self.server.call_tool()
        async def query_natural(
            natural_query: str,
            **kwargs: Any,
        ):
            """
            Ejecuta una consulta en lenguaje natural contra la BD.

            Argumentos:
                natural_query: La pregunta en español (ej: "Cuantos jugadores hay?")

            Retorna:
                JSON con: sql (string), data (array), visualization (string)
            """
            logger.info(f"Query recibida: {natural_query}")
            return await self._handle_query(natural_query)

        @self.server.call_tool()
        async def count_players(**kwargs: Any):
            """Retorna el número total de jugadores en la BD."""
            logger.info("Herramienta count_players invocada")
            return await self._handle_query("Cuantos jugadores hay en total?")

        @self.server.call_tool()
        async def list_tables(**kwargs: Any):
            """Lista todas las tablas disponibles en la BD."""
            logger.info("Herramienta list_tables invocada")
            async with async_session_maker() as session:
                try:
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
                    )
                    return [TextContent(type="text", text=response_text)]
                except Exception as e:
                    logger.error(f"Error listando tablas: {e}")
                    return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def _handle_query(self, query: str):
        """Maneja una consulta: RAG → SQL Gen → Execution → Response."""
        try:
            logger.info(f"Procesando query: {query}")

            # Validar configuración
            if not settings.openrouter_api_key:
                error_msg = "OPENROUTER_API_KEY no configurada"
                logger.error(error_msg)
                return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

            async with async_session_maker() as session:
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
                    return [TextContent(type="text", text=json.dumps({"error": sql_error}))]

                if not sql:
                    logger.error("No se pudo generar SQL válido")
                    return [TextContent(type="text", text=json.dumps({"error": "No se pudo generar SQL válido"}))]

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

                    response_text = json.dumps(response_data, indent=2, default=str)
                    return [TextContent(type="text", text=response_text)]

                except Exception as db_error:
                    logger.error(f"Error ejecutando SQL: {db_error}")
                    error_response = {
                        "error": f"Error ejecutando consulta: {str(db_error)[:100]}",
                        "sql": sql,
                    }
                    return [TextContent(type="text", text=json.dumps(error_response))]

        except Exception as e:
            logger.exception(f"Error no esperado en MCP: {e}")
            return [TextContent(type="text", text=json.dumps({"error": f"Error interno: {str(e)[:100]}"}))]

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
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score): Partidos jugados.
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds_total, assists, fg3_made, pir): Estadisticas de jugador por partido.

KEY RELATIONSHIPS:
- player_stats_games.player_id -> players.id
- player_stats_games.game_id -> games.id
- players.team_id -> teams.id
- games.home_team_id, away_team_id -> teams.id
"""

    async def run(self):
        """Inicia el servidor MCP."""
        logger.info("Iniciando servidor MCP Text-to-SQL...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Servidor MCP ejecutándose en stdio")
            await self.server.run(read_stream, write_stream)


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
