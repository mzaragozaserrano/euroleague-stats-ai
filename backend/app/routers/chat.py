"""
Router del Chat Endpoint.

Orquesta: Vectorización → RAG → SQL Generation → Execution → Response.
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.services.vectorization import VectorizationService
from app.services.text_to_sql import TextToSQLService
from app.services.response_generator import ResponseGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Request al endpoint /api/chat."""
    query: str = Field(..., min_length=1, description="Consulta natural del usuario")
    history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Historial de conversacion (role/content pairs)"
    )


class ChatResponse(BaseModel):
    """Respuesta del endpoint /api/chat."""
    sql: Optional[str] = Field(None, description="SQL generado")
    data: Optional[Any] = Field(None, description="Datos retornados por la BD")
    visualization: Optional[str] = Field(None, description="Tipo de visualizacion")
    message: Optional[str] = Field(None, description="Respuesta en lenguaje natural (Markdown)")
    error: Optional[str] = Field(None, description="Mensaje de error si aplica")

    class Config:
        # Excluir campos None del JSON de respuesta
        exclude_none = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_season_for_display(season_value: Any) -> str:
    """
    Convierte formato de temporada de BD (E2025, 2025, 2022) a formato de visualización (2025/2026, 2022/2023).
    
    Regla: Siempre mostrar temporada como YYYY/YYYY+1
    - E2025 -> 2025/2026
    - 2025 -> 2025/2026
    - 2022 -> 2022/2023
    - E2022 -> 2022/2023
    
    Args:
        season_value: Valor de temporada (str "E2025", "E2022" o int 2025, 2022)
        
    Returns:
        String formateado como "YYYY/YYYY+1" o el valor original si no se puede convertir
    """
    if season_value is None:
        return ""
    
    # Convertir a string si es necesario
    season_str = str(season_value).strip()
    
    # Si tiene formato "E2025" o "E2022", extraer el año
    if season_str.startswith("E"):
        try:
            year = int(season_str[1:])
            # Validar que sea un año razonable (1900-2100)
            if 1900 <= year <= 2100:
                return f"{year}/{year + 1}"
        except ValueError:
            pass
    
    # Si es un número puro (2025, 2022, etc.)
    try:
        year = int(season_str)
        # Validar que sea un año razonable (1900-2100)
        if 1900 <= year <= 2100:
            return f"{year}/{year + 1}"
    except ValueError:
        pass
    
    # Si no se puede convertir, retornar original
    return season_str


def _format_seasons_in_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formatea campos de temporada en los datos para mostrar en formato YYYY/YYYY+1.
    
    Busca columnas que contengan 'season' o 'temporada' (case insensitive) y las convierte.
    Aplica a todas las columnas relacionadas con temporada, independientemente del alias usado.
    
    Args:
        data: Lista de diccionarios con datos
        
    Returns:
        Lista de diccionarios con temporadas formateadas (siempre en formato YYYY/YYYY+1)
    """
    if not data:
        return data
    
    formatted_data = []
    for row in data:
        formatted_row = {}
        for key, value in row.items():
            # Buscar columnas relacionadas con temporada (case insensitive)
            key_lower = key.lower()
            if 'season' in key_lower or 'temporada' in key_lower:
                # Aplicar formateo: siempre mostrar como YYYY/YYYY+1
                formatted_row[key] = _format_season_for_display(value)
            else:
                formatted_row[key] = value
        formatted_data.append(formatted_row)
    
    return formatted_data


def _get_default_schema_context() -> str:
    """
    Retorna esquema hardcodeado como fallback cuando RAG no está disponible.
    """
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
- 'three_points_made' in player_stats_games is snake_case.
"""


async def _get_schema_context(session: AsyncSession, query: str) -> tuple[str, bool]:
    """
    Construye el contexto de esquema para el LLM usando RAG (Retrieval Augmented Generation).
    
    Usa búsqueda semántica por similitud para recuperar solo el esquema relevante a la consulta.
    Si RAG falla o no está disponible, usa esquema hardcodeado como fallback.
    
    Args:
        session: Sesión de base de datos.
        query: Consulta natural del usuario (para búsqueda semántica).
    
    Returns:
        Tupla (contexto, usado_rag): Contexto de esquema y booleano indicando si se usó RAG.
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
                    return context, True
                else:
                    logger.warning(f"⚠ RAG encontró {len(relevant_schema)} resultados pero ninguno con similitud >= 0.3, usando esquema por defecto")
                    return _get_default_schema_context(), False
            else:
                logger.warning("⚠ RAG no retornó resultados (tabla vacía o no existe), usando esquema por defecto")
                return _get_default_schema_context(), False
                
        except Exception as e:
            # Capturar cualquier error (tabla no existe, error de conexión, etc.)
            logger.warning(f"⚠ Error usando RAG (tabla puede no existir o no tener embeddings), fallback a esquema por defecto: {type(e).__name__}: {str(e)[:100]}")
            # Fallback seguro: usar esquema hardcodeado
            return _get_default_schema_context(), False
    else:
        # Si no hay OpenAI API key, usar esquema hardcodeado
        logger.info("ℹ OPENAI_API_KEY no configurada, usando esquema por defecto (RAG desactivado)")
        return _get_default_schema_context(), False


async def _execute_sql(session: AsyncSession, sql: str) -> List[Dict[str, Any]]:
    """
    Ejecuta SQL contra la BD y retorna resultados.
    
    Args:
        session: Sesion de BD.
        sql: Query SQL a ejecutar.
        
    Returns:
        Lista de diccionarios con resultados.
        
    Raises:
        Exception: Si la BD falla.
    """
    # Asegurar que la sesión esté en un estado limpio antes de ejecutar
    # Hacer rollback preventivo para limpiar cualquier transacción inválida previa
    try:
        await session.rollback()
    except Exception:
        pass  # Ignorar errores de rollback (puede que no haya transacción activa)
    
    try:
        logger.info(f"Ejecutando SQL: {sql[:100]}...")
        result = await session.execute(text(sql))
        
        # Obtener nombre de columnas
        columns = result.keys()
        
        # Convertir filas a diccionarios
        rows = result.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        logger.info(f"SQL executado exitosamente, {len(data)} filas retornadas")
        return data
    
    except Exception as e:
        logger.error(f"Error ejecutando SQL: {type(e).__name__}: {e}")
        # Hacer rollback para limpiar la transacción inválida
        try:
            await session.rollback()
        except Exception as rollback_error:
            logger.warning(f"Error haciendo rollback: {rollback_error}")
        raise


# ============================================================================
# ENDPOINT
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Endpoint de chat que orquesta el pipeline de IA.
    
    Flujo:
    1. Validar request
    2. Obtener contexto de esquema (RAG)
    3. Generar SQL usando LLM
    4. Ejecutar SQL contra BD
    5. Generar respuesta natural (Resumen)
    6. Retornar resultados
    
    IMPORTANTE: Status siempre 200, errores en campo 'error'.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Chat request recibido: '{request.query}' con {len(request.history)} mensajes de historial")
        
        # Validar que OpenRouter esté disponible
        if not settings.openrouter_api_key:
            logger.error("OPENROUTER_API_KEY no está configurada")
            return ChatResponse(
                error="Servicio de IA no está disponible. Contacte al administrador."
            )
        
        # ====================================================================
        # PASO 1: Obtener contexto de esquema (RAG)
        # ====================================================================
        logger.info("Paso 1: Recuperando contexto de esquema con RAG...")
        schema_context, rag_used = await _get_schema_context(session, request.query)
        if rag_used:
            logger.info(f"✓ RAG ACTIVO: Contexto de esquema obtenido con búsqueda semántica ({len(schema_context)} chars)")
        else:
            logger.info(f"ℹ RAG NO USADO: Contexto de esquema obtenido desde fallback hardcodeado ({len(schema_context)} chars)")
        
        # ====================================================================
        # PASO 2: Generar SQL o obtener stats directamente
        # ====================================================================
        logger.info("Paso 2: Procesando consulta...")
        text_to_sql_service = TextToSQLService(api_key=settings.openrouter_api_key)
        
        sql, visualization, sql_error, direct_data = await text_to_sql_service.generate_sql_with_fallback(
            query=request.query,
            schema_context=schema_context,
            conversation_history=request.history,
        )
        
        if sql_error:
            logger.warning(f"Error en procesamiento: {sql_error}")
            return ChatResponse(error=sql_error)
        
        # Variables finales
        final_data = []
        final_visualization = visualization or "table"
        final_sql = sql
        
        # ====================================================================
        # PASO 3: Obtener datos (Directos o SQL)
        # ====================================================================
        
        if direct_data is not None:
            # Caso A: Datos directos (stats)
            logger.info(f"Datos directos obtenidos (stats): {len(direct_data)} registros")
            # Formatear temporadas antes de usar
            final_data = _format_seasons_in_data(direct_data)
            final_sql = None  # No hay SQL visible para el usuario en este caso
        
        elif sql:
            # Caso B: Ejecutar SQL
            logger.info(f"SQL generado: {sql[:200]}...")
            logger.info("Paso 3: Ejecutando SQL contra la BD...")
            try:
                raw_data = await _execute_sql(session, sql)
                logger.info(f"Ejecución exitosa: {len(raw_data)} registros")
                if len(raw_data) == 0:
                    logger.warning(f"SQL ejecutado correctamente pero retornó 0 registros. SQL: {sql}")
                else:
                    logger.debug(f"Primera fila de datos: {raw_data[0] if raw_data else 'None'}")
                # Formatear temporadas antes de usar
                final_data = _format_seasons_in_data(raw_data)
            except Exception as db_error:
                logger.error(f"Error ejecutando SQL: {db_error}")
                # Asegurar rollback adicional por si acaso
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.warning(f"Error haciendo rollback adicional: {rollback_error}")
                return ChatResponse(
                    sql=sql,
                    error=f"Error ejecutando consulta: {str(db_error)[:100]}"
                )
        else:
            logger.error("No se pudo generar SQL ni obtener datos directos")
            return ChatResponse(error="No se pudo procesar tu consulta. Intenta ser más específico.")
            
        # ====================================================================
        # PASO 4: Determinar tipo de visualización final basado en resultado real
        # ====================================================================
        if not final_visualization:
            final_visualization = "table"
        
        # Si no hay datos, usar 'table' siempre
        if len(final_data) == 0:
            final_visualization = "table"
        else:
            # ====================================================================
            # PASO 4.1: Filtrar columna de temporada ANTES de determinar visualización
            # ====================================================================
            # Filtrar temporada de final_data si solo hay una y la consulta no la menciona
            temp_service = ResponseGeneratorService(api_key=settings.openrouter_api_key)
            final_data_filtered = temp_service._filter_season_column_if_not_needed(final_data, request.query)
            
            # Si se filtró alguna columna, usar los datos filtrados para todo
            if len(final_data) > 0 and len(final_data_filtered) > 0:
                original_cols = len(final_data[0].keys())
                filtered_cols = len(final_data_filtered[0].keys())
                if filtered_cols < original_cols:
                    logger.info(f"Columna de temporada filtrada ({original_cols} → {filtered_cols} columnas)")
                    final_data = final_data_filtered
            
            # Corregir visualization_type basado en el resultado real (usando datos filtrados)
            num_rows = len(final_data)
            num_columns = len(final_data[0].keys()) if final_data else 0
            
            # Reglas para tipo de visualización:
            # - 1 fila y ≤3 columnas → 'text' (respuesta simple)
            # - 2 filas y ≤2 columnas → 'text' (comparación simple)
            # - Resto → 'table' o gráfico según corresponda
            
            is_simple_response = (
                (num_rows == 1 and num_columns <= 3) or
                (num_rows == 2 and num_columns <= 2)
            )
            
            if is_simple_response:
                # Respuesta simple: usar 'text' (no mostrar tabla de datos)
                if final_visualization not in ['bar', 'line', 'scatter']:
                    final_visualization = "text"
                    logger.info(f"Corregido a 'text': {num_rows} fila(s), {num_columns} columna(s) (respuesta simple)")
            elif num_rows >= 3:
                # Tres o más filas → tabla (listas, rankings, etc.)
                if final_visualization == "text":
                    final_visualization = "table"
                    logger.info(f"Corregido a 'table': {num_rows} filas (siempre tabla para 3+ filas)")
            elif num_rows == 2 and num_columns > 2:
                # Dos filas con más de 2 columnas → tabla
                if final_visualization == "text":
                    final_visualization = "table"
                    logger.info(f"Corregido a 'table': 2 filas con {num_columns} columnas")
            elif num_rows == 1 and num_columns > 3:
                # Una fila con más de 3 columnas → tabla
                if final_visualization == "text":
                    final_visualization = "table"
                    logger.info(f"Corregido a 'table': 1 fila con {num_columns} columnas")
        
        logger.info(f"Visualización final: {final_visualization}")

        # ====================================================================
        # PASO 5: Generar respuesta en lenguaje natural
        # ====================================================================
        logger.info("Paso 5: Generando respuesta natural...")
        
        # Si no hay datos, generar mensaje simple sin historial para evitar confusión
        if len(final_data) == 0:
            logger.warning("No se encontraron datos para la consulta. Generando respuesta sin historial.")
            response_service = ResponseGeneratorService(api_key=settings.openrouter_api_key)
            natural_response = await response_service.generate_response(
                query=request.query,
                data=final_data,
                conversation_history=None,  # No pasar historial cuando no hay datos
                sql=final_sql
            )
        else:
            response_service = ResponseGeneratorService(api_key=settings.openrouter_api_key)
            natural_response = await response_service.generate_response(
                query=request.query,
                data=final_data,
                conversation_history=request.history,
                sql=final_sql
            )

        # Si hay respuesta natural, verificar si contiene tabla antes de suprimir visualización
        # La respuesta natural ya incluye tablas/formato cuando es necesario
        if natural_response:
            # Verificar si la respuesta natural contiene una tabla (marcador: "|" en markdown)
            has_table_in_response = "|" in natural_response and "--" in natural_response
            
            if final_visualization == "text":
                logger.info("Suprimiendo datos estructurados para respuesta simple (text)")
                final_visualization = None
                # CAPA ADICIONAL DE SEGURIDAD: Eliminar cualquier tabla del markdown si es respuesta simple
                if has_table_in_response:
                    logger.warning("Respuesta simple contiene tabla en markdown. Eliminando tabla...")
                    lines = natural_response.split('\n')
                    cleaned_lines = []
                    skip_table = False
                    for line in lines:
                        # Detectar inicio de tabla (línea con | y --)
                        if '|' in line and '--' in line:
                            skip_table = True
                            continue
                        # Detectar líneas de tabla (contienen |)
                        if skip_table and '|' in line:
                            continue
                        # Detectar fin de tabla (línea sin |)
                        if skip_table and '|' not in line:
                            skip_table = False
                            # Si la línea no está vacía después de la tabla, incluirla
                            if line.strip():
                                cleaned_lines.append(line)
                            continue
                        # Línea normal (no es parte de tabla)
                        cleaned_lines.append(line)
                    natural_response = '\n'.join(cleaned_lines).strip()
                    # Si aún tiene tabla, eliminación más agresiva
                    if "|" in natural_response:
                        lines = natural_response.split('\n')
                        cleaned_lines = [line for line in lines if '|' not in line]
                        natural_response = '\n'.join(cleaned_lines).strip()
                    logger.info("Tabla eliminada de respuesta simple (capa adicional)")
            elif final_visualization == "table":
                if has_table_in_response:
                    logger.info("Suprimiendo tabla visualización a favor de tabla en respuesta natural")
                    final_visualization = None
                else:
                    logger.warning("Respuesta natural no contiene tabla, manteniendo visualización 'table'")
                    # Mantener la visualización si la respuesta natural no tiene tabla
            elif final_visualization == "bar":
                if has_table_in_response:
                    logger.info("Suprimiendo visualización bar a favor de tabla en respuesta natural")
                    final_visualization = None
        
        # ====================================================================
        # PASO 7: Retornar
        # ====================================================================
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"Chat endpoint completado en {latency_ms:.2f}ms")
        
        if latency_ms > 5000:
            logger.warning(f"Latencia alta: {latency_ms:.2f}ms")
        
        return ChatResponse(
            sql=final_sql,
            data=final_data,
            visualization=final_visualization,
            message=natural_response,
        )
    
    except Exception as e:
        # Capturar cualquier error no esperado
        logger.exception(f"Error no esperado en chat endpoint: {e}")
        # Asegurar rollback en caso de error inesperado
        try:
            await session.rollback()
        except Exception as rollback_error:
            logger.warning(f"Error haciendo rollback en error inesperado: {rollback_error}")
        return ChatResponse(
            error=f"Error interno del servidor: {str(e)[:100]}"
        )
