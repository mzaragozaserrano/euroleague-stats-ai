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


def _filter_stats_columns_for_simple_query(
    data: List[Dict[str, Any]], 
    query: str
) -> List[Dict[str, Any]]:
    """
    Filtra columnas de datos para consultas simples de máximo/top N sobre una estadística específica.
    
    Para consultas como "máximo reboteador" o "top 4 anotadores", solo retorna:
    - Jugador/Nombre
    - La estadística consultada (rebotes, puntos, asistencias, etc.)
    - Partidos (si se pregunta "cuantos X lleva")
    - Ranking (si es top N con N > 1)
    
    Args:
        data: Lista de diccionarios con datos completos
        query: Consulta del usuario
        
    Returns:
        Lista de diccionarios con solo las columnas relevantes
    """
    if not data:
        return data
    
    query_lower = query.lower()
    
    # Detectar si es una consulta simple de máximo/top N sobre una estadística específica
    is_simple_maximum_query = (
        any(word in query_lower for word in [
            "maximo", "máximo", "maxima", "máxima", "mejor", "top",
            "quien es el", "quien es la", "primer", "segundo", "tercer", "cuarto",
            "quinto", "sexto", "septimo", "octavo", "noveno", "decimo"
        ]) and
        not any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación", "estadisticas", "estadísticas"])
    )
    
    if not is_simple_maximum_query:
        return data
    
    # Detectar qué estadística se está consultando
    stat_column = None
    stat_name_spanish = None
    
    if any(word in query_lower for word in ["rebote", "rebound"]):
        stat_column = "rebounds"
        stat_name_spanish = "Rebotes"
    elif any(word in query_lower for word in ["anotador", "puntos", "points", "scorer"]):
        stat_column = "points"
        stat_name_spanish = "Puntos"
    elif any(word in query_lower for word in ["asistente", "asistencias", "assists"]):
        stat_column = "assists"
        stat_name_spanish = "Asistencias"
    elif any(word in query_lower for word in ["pir", "eficiencia", "efficiency", "valoracion", "valoración"]):
        stat_column = "pir"
        stat_name_spanish = "Valoración"
    
    # Si no se detecta estadística específica, retornar todos los datos
    if not stat_column:
        return data
    
    # Detectar si se pregunta por partidos ("cuantos rebotes lleva", "cuantos puntos tiene")
    include_games = any(word in query_lower for word in ["cuantos", "cuántos", "lleva", "tiene", "partidos", "games"])
    
    # Detectar si es top N (múltiples jugadores) para incluir ranking
    is_top_n = any(word in query_lower for word in ["top", "primeros", "mejores", "maximos", "máximos"]) or \
               any(word in query_lower for word in ["segundo", "tercer", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo"])
    
    # Filtrar datos
    filtered_data = []
    for row in data:
        filtered_row = {}
        
        # Siempre incluir nombre del jugador (buscar en diferentes formatos)
        player_name = None
        if "player_name" in row:
            player_name = row["player_name"]
        elif "Nombre" in row:
            player_name = row["Nombre"]
        elif "name" in row:
            player_name = row["name"]
        elif "Jugador" in row:
            player_name = row["Jugador"]
        
        if player_name:
            filtered_row["Jugador"] = player_name
        
        # Incluir ranking si es top N (buscar en diferentes formatos)
        if is_top_n:
            rank_value = None
            if "rank" in row:
                rank_value = row["rank"]
            elif "Ranking" in row:
                rank_value = row["Ranking"]
            elif "ranking" in row:
                rank_value = row["ranking"]
            
            if rank_value is not None:
                filtered_row["Ranking"] = rank_value
        
        # Incluir la estadística consultada (buscar en inglés y español)
        stat_value = None
        if stat_column in row:
            stat_value = row[stat_column]
        elif stat_name_spanish in row:
            stat_value = row[stat_name_spanish]
        
        if stat_value is not None:
            filtered_row[stat_name_spanish] = stat_value
        
        # Incluir partidos si se pregunta por ellos
        if include_games:
            games_value = None
            if "games_played" in row:
                games_value = row["games_played"]
            elif "Partidos" in row:
                games_value = row["Partidos"]
            elif "partidos" in row:
                games_value = row["partidos"]
            
            if games_value is not None:
                filtered_row["Partidos"] = games_value
        
        filtered_data.append(filtered_row)
    
    logger.info(f"Columnas filtradas para consulta simple: {list(filtered_data[0].keys()) if filtered_data else []}")
    return filtered_data


def _filter_comparison_columns_for_facet(
    data: List[Dict[str, Any]], 
    query: str
) -> List[Dict[str, Any]]:
    """
    Filtra columnas para comparaciones donde se menciona una faceta específica.
    
    Cuando se compara un jugador con un "máximo/quinto/etc. reboteador/anotador/asistente"
    o simplemente se compara en una faceta ("compara rebotes de X e Y"),
    ambos jugadores deben mostrar SOLO la faceta mencionada y el nombre.
    
    Args:
        data: Lista de diccionarios con datos completos
        query: Consulta del usuario
        
    Returns:
        Lista de diccionarios con columnas filtradas según corresponda
    """
    if not data:
        return data
    
    query_lower = query.lower()
    
    # Detectar si es una comparación que menciona una faceta específica
    is_comparison = any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación"])
    if not is_comparison:
        return data
    
    # Detectar qué faceta se está mencionando (reboteador, anotador, asistente)
    stat_column = None
    stat_name_spanish = None
    
    if any(word in query_lower for word in ["rebote", "rebound"]):
        stat_column = "rebounds"
        stat_name_spanish = "Rebotes"
    elif any(word in query_lower for word in ["anotador", "anotadora", "puntos", "points", "scorer"]):
        stat_column = "points"
        stat_name_spanish = "Puntos"
    elif any(word in query_lower for word in ["asistente", "asistencias", "assists"]):
        stat_column = "assists"
        stat_name_spanish = "Asistencias"
    elif any(word in query_lower for word in ["pir", "eficiencia", "efficiency", "valoracion", "valoración"]):
        stat_column = "pir"
        stat_name_spanish = "Valoración"
    
    # Si no se detecta faceta específica, no filtrar
    if not stat_column:
        return data
    
    # Detectar si se pregunta explícitamente por partidos
    # Si el usuario NO pregunta por partidos, NO incluirlos para mantener la respuesta limpia
    include_games = any(word in query_lower for word in ["cuantos", "cuántos", "lleva", "tiene", "partidos", "games"])
    
    # Detectar si se pregunta explícitamente por ranking
    # Si el usuario NO pregunta por ranking, NO incluirlo
    include_ranking = any(word in query_lower for word in ["ranking", "rank", "posicion", "posición", "lugar", "puesto"])
    
    # Definir columnas permitidas
    # Siempre incluir Nombre y la Estadística
    # Ranking solo si se pregunta explícitamente
    allowed_columns = ["Jugador", "player_name", "Nombre", "name", stat_name_spanish]
    if include_ranking:
        allowed_columns.extend(["Ranking", "rank"])
    
    # Mapeo de columnas de BD a nombre español
    col_mapping = {
        stat_column: stat_name_spanish,
        "games_played": "Partidos"
    }

    logger.info(f"🔍 FILTRANDO COMPARACIÓN: {len(data)} fila(s) de entrada")
    filtered_data = []
    for idx, row in enumerate(data):
        filtered_row = {}
        
        # CRÍTICO: Siempre incluir el nombre del jugador primero (buscar en diferentes formatos)
        player_name = None
        for name_col in ["Jugador", "player_name", "Nombre", "name"]:
            if name_col in row:
                player_name = row[name_col]
                filtered_row["Jugador"] = player_name
                break
        
        # Si no hay nombre, saltar esta fila (datos inválidos)
        if not player_name:
            logger.error(f"❌ ERROR: Fila {idx} sin nombre de jugador encontrada, omitiendo: {row}")
            logger.error(f"❌ Claves disponibles en fila: {list(row.keys())}")
            continue
        
        logger.debug(f"✅ Procesando jugador: {player_name}")
        
        # Copiar columnas permitidas que ya existan con el nombre correcto
        for key, value in row.items():
            # Excluir Ranking si no se pidió explícitamente
            if key in ["Ranking", "rank"] and not include_ranking:
                continue
            if key in allowed_columns and key not in ["Jugador", "player_name", "Nombre", "name"]:  # Ya copiamos el nombre arriba
                filtered_row[key] = value
            elif key in col_mapping:
                # Renombrar si es necesario (ej: rebounds -> Rebotes)
                target_key = col_mapping[key]
                # Solo agregar si es la estadística o si es partidos y se pidieron
                if target_key == stat_name_spanish:
                    # IMPORTANTE: Incluir incluso si es 0 o None (el usuario debe ver el valor real)
                    filtered_row[target_key] = value
                elif target_key == "Partidos" and include_games:
                    filtered_row[target_key] = value

        # Si por alguna razón falta la estadística con el nombre en español pero estaba en inglés
        if stat_name_spanish not in filtered_row and stat_column in row:
             # IMPORTANTE: Incluir incluso si es 0 o None
             filtered_row[stat_name_spanish] = row[stat_column]

        # Partidos (chequeo adicional por nombres variados)
        if include_games and "Partidos" not in filtered_row:
             if "Partidos" in row: filtered_row["Partidos"] = row["Partidos"]
             elif "partidos" in row: filtered_row["Partidos"] = row["partidos"]
             elif "games_played" in row: filtered_row["Partidos"] = row["games_played"]
        
        # Asegurar que siempre tengamos al menos el nombre y la estadística (incluso si es 0 o None)
        if stat_name_spanish not in filtered_row:
            # Si no encontramos la estadística, usar 0 como fallback para que el usuario vea que el jugador existe pero no tiene datos
            filtered_row[stat_name_spanish] = 0
            logger.warning(f"Estadística '{stat_name_spanish}' no encontrada para jugador '{player_name}', usando 0 como fallback")

        filtered_data.append(filtered_row)
    
    logger.info(f"✅ FILTRADO COMPLETADO: {len(filtered_data)} fila(s) de salida (de {len(data)} entrada)")
    logger.info(f"✅ Columnas filtradas: {list(filtered_data[0].keys()) if filtered_data else []}")
    logger.info(f"✅ Jugadores en datos filtrados: {[row.get('Jugador') for row in filtered_data]}")
    
    if len(filtered_data) < len(data):
        logger.warning(f"⚠ ADVERTENCIA: Se filtraron {len(data) - len(filtered_data)} fila(s) durante el proceso")
    
    return filtered_data


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
- players (id, team_id, name, position): Players info. IMPORTANT: Names are often stored as 'LASTNAME, FIRSTNAME' (e.g. 'CAMPAZZO, FACUNDO'). Use ILIKE with partial matches (e.g. ILIKE '%Campazzo%') or split parts.
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score): Games played. SEASON values are INTEGERS: 2023, 2024, 2025.
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds, assists, three_points_made, pir): Player stats per game (Box Score). Columns are: points, rebounds, assists, three_points_made, pir.
- player_season_stats (id, player_id, season, games_played, points, rebounds, assists, "threePointsMade", pir): Aggregated stats per season. Season values are STRINGS like 'E2024', 'E2025'.

KEY RELATIONSHIPS:
- player_stats_games.player_id -> players.id
- player_stats_games.game_id -> games.id
- player_season_stats.player_id -> players.id
- players.team_id -> teams.id
- players.team_id -> teams.id

IMPORTANT:
- Use 'player_season_stats' for season totals/averages. Season format is 'E2025'.
- Use 'player_stats_games' ONLY for specific game details.
- 'threePointsMade' in player_season_stats is quoted.
- 'three_points_made' in player_stats_games is snake_case.
- When searching for players by name, ALWAYS use ILIKE '%Name%' to handle 'Lastname, Firstname' format.
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
                    # Validar que comparaciones tengan ambos jugadores
                    query_lower = request.query.lower()
                    is_comparison = any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación"])
                    if is_comparison:
                        logger.info(f"🔍 COMPARACIÓN DETECTADA: {len(raw_data)} fila(s) retornadas")
                        logger.info(f"🔍 Nombres en datos: {[row.get('Jugador') or row.get('player_name') or row.get('Nombre') or row.get('name') or 'SIN_NOMBRE' for row in raw_data]}")
                        if len(raw_data) < 2:
                            logger.error(f"❌ ERROR CRÍTICO: Comparación debería retornar 2 filas pero solo retornó {len(raw_data)}. SQL completo: {sql}")
                            logger.error(f"❌ Datos retornados: {raw_data}")
                            # Retornar error al usuario en lugar de continuar con datos incompletos
                            return ChatResponse(
                                sql=sql,
                                error=f"Error en la consulta: Solo se encontró {len(raw_data)} jugador(es) cuando se esperaban 2. El SQL generado puede no estar recuperando correctamente ambos jugadores. Por favor, intenta reformular la consulta."
                            )
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
        # PASO 3.5: Filtrar y Refinar Datos (Común para Directo y SQL)
        # ====================================================================
        if final_data and len(final_data) > 0:
            # 1. Filtrar temporada si aplica
            temp_service = ResponseGeneratorService(api_key=settings.openrouter_api_key)
            final_data = temp_service._filter_season_column_if_not_needed(final_data, request.query)
            
            # 2. Filtrar columnas según tipo de consulta
            query_lower = request.query.lower()
            is_comparison = any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación"])
            
            if is_comparison:
                 # Aplicar filtrado de comparaciones con faceta específica
                 # Esto limpiará columnas irrelevantes (Puntos, Rebotes, etc.) si se pregunta por una faceta específica
                 final_data = _filter_comparison_columns_for_facet(final_data, request.query)
            else:
                 # Filtrar columnas para consultas simples
                 final_data = _filter_stats_columns_for_simple_query(final_data, request.query)
            
        # ====================================================================
        # PASO 4: Determinar tipo de visualización final basado en resultado real
        # ====================================================================
        if not final_visualization:
            final_visualization = "table"
        
        # Si no hay datos, usar 'table' siempre
        if len(final_data) == 0:
            final_visualization = "table"
        else:
            # Ya no necesitamos filtrar temporada ni columnas aquí porque se hizo en el paso 3.5
            
            # Corregir visualization_type basado en el resultado real
            num_rows = len(final_data)
            num_columns = len(final_data[0].keys()) if final_data else 0
            
            logger.info(f"Evaluando visualización: {num_rows} fila(s), {num_columns} columna(s)")
            
            # Detectar si es una consulta simple de "máximo X" (singular, no plural)
            query_lower = request.query.lower()
            is_simple_maximum_query = (
                (num_rows == 1) and  # Solo un resultado
                any(word in query_lower for word in [
                    "quien es el maximo", "quien es el máximo", "quien es la maxima", "quien es la máxima",
                    "maximo reboteador", "máximo reboteador", "maximo anotador", "máximo anotador",
                    "maximo asistente", "máximo asistente", "maxima anotadora", "máxima anotadora",
                    "mejor reboteador", "mejor anotador", "mejor asistente"
                ]) and
                not any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación"])
            )
            
            # Detectar si es una comparación
            is_comparison_query = any(word in query_lower for word in ["compara", "comparar", "comparacion", "comparación"])
            
            # Reglas para tipo de visualización:
            # - Consultas simples de "máximo X" (1 fila) → 'text' (respuesta simple, sin tabla)
            # - 1 fila y ≤3 columnas → 'text' (respuesta simple, sin tabla)
            # - Comparaciones con 2 filas y ≤2 columnas → 'text' (comparación simple, sin tabla)
            # - Comparaciones con 1 fila y ≤2 columnas → 'text' también (aunque debería haber 2, forzar texto)
            # - Resto → 'table' o gráfico según corresponda
            
            # Para comparaciones: si tiene ≤2 columnas, siempre texto (incluso si solo hay 1 fila por error SQL)
            is_comparison_simple = is_comparison_query and num_columns <= 2
            
            is_simple_response = (
                is_simple_maximum_query or  # Consulta de máximo singular
                (num_rows == 1 and num_columns <= 3) or
                is_comparison_simple  # Comparación simple: ≤2 columnas (2 filas idealmente, pero aceptar 1 si hay error)
            )
            
            if is_simple_response:
                # Respuesta simple: usar 'text' (no mostrar tabla de datos)
                # Si es una consulta explícita de máximo con 1 resultado, FORZAR texto
                # para evitar gráficos de una sola barra o tablas innecesarias
                if is_simple_maximum_query:
                    final_visualization = "text"
                    logger.info(f"FORZADO a 'text': consulta simple de máximo ({num_rows} fila, {num_columns} columnas)")
                # Para comparaciones simples (≤2 columnas), FORZAR texto siempre
                elif is_comparison_simple:
                    final_visualization = "text"
                    if num_rows < 2:
                        logger.warning(f"⚠ ADVERTENCIA: Comparación con solo {num_rows} fila(s) pero forzando texto (debería haber 2)")
                    logger.info(f"FORZADO a 'text': comparación simple ({num_rows} fila(s), {num_columns} columna(s))")
                # Para otros casos simples, usar 'text' solo si no es un gráfico explícito
                elif final_visualization not in ['bar', 'line', 'scatter']:
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
            
            # Detectar si es el mensaje de fallback de error (nuevo o antiguo)
            is_fallback_error = "⚠️ Hubo un problema" in natural_response or "Aquí tienes los resultados encontrados en la base de datos" in natural_response

            if is_fallback_error:
                logger.warning("Mensaje de fallback detectado: Forzando visualización de tabla para mostrar datos")
                # Forzar tabla para que el usuario vea los datos crudos
                final_visualization = "table"
                # IMPORTANTE: No borrar final_data para que se muestren
                
            elif final_visualization == "text":
                logger.info("Suprimiendo datos estructurados para respuesta simple (text)")
                final_visualization = None
                # CRÍTICO: También eliminar los datos para que el frontend no muestre tabla visual
                final_data = []
                logger.info("Datos eliminados para evitar tabla visual en respuesta simple")
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
