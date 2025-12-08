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
    error: Optional[str] = Field(None, description="Mensaje de error si aplica")

    class Config:
        # Excluir campos None del JSON de respuesta
        exclude_none = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _get_schema_context(session: AsyncSession) -> str:
    """
    Construye el contexto de esquema para el LLM.
    
    Recupera descripciones de tablas y columnas de schema_embeddings.
    """
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
            # Retornar esquema hardcodeado si no hay embeddings
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

IMPORTANT - Season values are always INTEGERS (2023, 2024, 2025), NEVER strings like 'current'.
"""
        
        context = "SCHEMA METADATA FROM RAG:\n"
        for row in embeddings:
            context += f"- {row[0]}\n"
        
        logger.info(f"Schema context construido con {len(embeddings)} embeddings")
        return context
    
    except Exception as e:
        logger.error(f"Error construyendo schema context: {e}")
        # Retornar esquema por defecto
        return """
TABLES:
- teams (id, code, name, logo_url)
- players (id, team_id, name, position)
- games (id, season, round, home_team_id, away_team_id, date, home_score, away_score) - Season is INTEGER: 2023, 2024, 2025
- player_stats_games (id, game_id, player_id, team_id, minutes, points, rebounds_total, assists, fg3_made, pir)

CRITICAL: Season values are always INTEGERS, NEVER strings like 'current'."""


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
    5. Retornar resultados
    
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
        logger.info("Paso 1: Recuperando contexto de esquema...")
        schema_context = await _get_schema_context(session)
        logger.info(f"Contexto de esquema obtenido ({len(schema_context)} chars)")
        
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
        
        # ====================================================================
        # PASO 3A: Si hay datos directos (stats), retornarlos sin SQL
        # ====================================================================
        if direct_data is not None:
            logger.info(f"Datos directos obtenidos (stats): {len(direct_data)} registros")
            return ChatResponse(
                sql=None,  # No hay SQL, se obtuvo de API
                data=direct_data,
                visualization=visualization or "table",
            )
        
        # ====================================================================
        # PASO 3B: Si hay SQL, ejecutarlo contra BD
        # ====================================================================
        if not sql:
            logger.error("No se pudo generar SQL ni obtener datos directos")
            return ChatResponse(error="No se pudo procesar tu consulta. Intenta ser más específico.")
        
        logger.info(f"SQL generado: {sql[:80]}...")
        logger.info("Paso 3: Ejecutando SQL contra la BD...")
        try:
            data = await _execute_sql(session, sql)
            logger.info(f"Ejecución exitosa: {len(data)} registros")
        except Exception as db_error:
            logger.error(f"Error ejecutando SQL: {db_error}")
            return ChatResponse(
                sql=sql,
                error=f"Error ejecutando consulta: {str(db_error)[:100]}"
            )
        
        # ====================================================================
        # PASO 4: Determinar tipo de visualización
        # ====================================================================
        if not visualization:
            visualization = "table"
        
        # Si no hay datos, usar 'table' siempre
        if len(data) == 0:
            visualization = "table"
        
        logger.info(f"Visualización: {visualization}")
        
        # ====================================================================
        # PASO 5: Calcular latencia y retornar
        # ====================================================================
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"Chat endpoint completado en {latency_ms:.2f}ms")
        
        if latency_ms > 5000:
            logger.warning(f"Latencia alta: {latency_ms:.2f}ms")
        
        return ChatResponse(
            sql=sql,
            data=data,
            visualization=visualization,
        )
    
    except Exception as e:
        # Capturar cualquier error no esperado
        logger.exception(f"Error no esperado en chat endpoint: {e}")
        return ChatResponse(
            error=f"Error interno del servidor: {str(e)[:100]}"
        )


