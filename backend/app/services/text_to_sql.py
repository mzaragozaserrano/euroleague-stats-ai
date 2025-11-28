"""
Servicio Text-to-SQL con OpenRouter.

Convierte consultas naturales en SQL válido usando LLM con validación de seguridad.
"""

import re
import logging
import json
from typing import Optional, List, Dict, Any, Tuple
from openai import AsyncOpenAI
import httpx

logger = logging.getLogger(__name__)

# Configuración de OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "meta-llama/llama-2-70b-chat"  # Modelo económico


class TextToSQLService:
    """
    Convierte consultas naturales en SQL usando LLM vía OpenRouter.
    """

    def __init__(self, api_key: str):
        """
        Inicializa el servicio con clave de API de OpenRouter.

        Args:
            api_key: Clave de API de OpenRouter.
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        self.model = OPENROUTER_MODEL

    @staticmethod
    def _get_system_prompt(schema_context: str) -> str:
        """
        Construye el prompt del sistema con context de esquema.

        Args:
            schema_context: Descripción del esquema disponible.

        Returns:
            Sistema prompt con ejemplos few-shot.
        """
        return f"""You are an expert SQL analyst for a Euroleague basketball statistics database.
Your task is to convert natural language queries into accurate PostgreSQL queries.

AVAILABLE SCHEMA:
{schema_context}

RULES:
1. You MUST return ONLY a JSON object with "sql" and "visualization_type" keys.
2. The "sql" field must contain a valid PostgreSQL SELECT query.
3. The "visualization_type" must be one of: 'table', 'bar', 'line', 'scatter'.
4. NEVER include DROP, DELETE, TRUNCATE, or ALTER statements.
5. Always use table aliases for readability.
6. Include WHERE clauses for date/season filtering when relevant.
7. Order results by most relevant column descending.

FEW-SHOT EXAMPLES:
Query: "puntos de Larkin"
{{
  "sql": "SELECT p.name, ps.points FROM players p JOIN player_stats_games ps ON p.id = ps.player_id WHERE p.name ILIKE '%Larkin%' ORDER BY ps.points DESC LIMIT 10;",
  "visualization_type": "table"
}}

Query: "puntos por equipo"
{{
  "sql": "SELECT t.name, SUM(ps.points) as total_points FROM teams t JOIN players p ON t.id = p.team_id JOIN player_stats_games ps ON p.id = ps.player_id GROUP BY t.id, t.name ORDER BY total_points DESC;",
  "visualization_type": "bar"
}}

Query: "comparación de asistencias entre Larkin y Micic"
{{
  "sql": "SELECT p.name, SUM(ps.assists) as total_assists FROM players p JOIN player_stats_games ps ON p.id = ps.player_id WHERE p.name ILIKE '%Larkin%' OR p.name ILIKE '%Micic%' GROUP BY p.id, p.name ORDER BY total_assists DESC;",
  "visualization_type": "bar"
}}

RESPONSE FORMAT:
Always respond with ONLY a JSON object. No explanation, no markdown, just JSON."""

    @staticmethod
    def _validate_sql_safety(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que el SQL no contenga operaciones peligrosas.

        Args:
            sql: Consulta SQL a validar.

        Returns:
            Tupla (es_seguro, mensaje_error).
        """
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE", "GRANT", "REVOKE"]
        
        sql_upper = sql.upper()
        
        for keyword in dangerous_keywords:
            # Buscar palabra completa (no dentro de otra palabra)
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_upper):
                return False, f"SQL contiene operación prohibida: {keyword}"
        
        # Verificar que sea SELECT
        if not re.match(r"^\s*SELECT\b", sql_upper):
            return False, "Solo se permiten consultas SELECT"
        
        # Validación básica de sintaxis
        if sql.count("(") != sql.count(")"):
            return False, "Parentesis desbalanceados en SQL"
        
        return True, None

    async def generate_sql(
        self,
        query: str,
        schema_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Genera SQL a partir de una consulta natural.

        Args:
            query: Consulta natural del usuario.
            schema_context: Context de esquema disponible.
            conversation_history: Historial de conversacion previo.

        Returns:
            Tupla (sql, visualization_type, error_message).
            Si hay error, sql será None.
        """
        try:
            logger.info(f"Generando SQL para query: {query}")
            
            # Construir mensajes para el LLM
            messages = []
            
            # Agregar historial de conversacion si existe
            if conversation_history:
                messages.extend(conversation_history)
            
            # Agregar consulta actual
            messages.append({
                "role": "user",
                "content": query,
            })
            
            # Llamar a OpenRouter
            logger.debug(f"Llamando a OpenRouter con {len(messages)} mensajes")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                system=self._get_system_prompt(schema_context),
                temperature=0.3,  # Bajo para consistencia
                max_tokens=500,
                timeout=30,  # Timeout de 30 segundos
            )
            
            # Extraer respuesta
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Respuesta de LLM: {response_text[:100]}...")
            
            # Parsear JSON de respuesta
            try:
                # Intentar extraer JSON si está dentro de markdown
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
                
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de LLM: {e}")
                return None, None, "El LLM retornó un formato inválido"
            
            # Extraer SQL y tipo de visualización
            sql = result.get("sql")
            visualization_type = result.get("visualization_type", "table")
            
            if not sql:
                logger.error("LLM no retornó campo 'sql'")
                return None, None, "LLM no generó SQL válido"
            
            # Validar seguridad del SQL
            is_safe, error_msg = self._validate_sql_safety(sql)
            if not is_safe:
                logger.warning(f"SQL rechazado por validación de seguridad: {error_msg}")
                return None, None, f"Consulta rechazada: {error_msg}"
            
            logger.info(f"SQL generado exitosamente: {sql[:100]}...")
            return sql, visualization_type, None
        
        except httpx.TimeoutException:
            logger.error("Timeout al conectar con OpenRouter")
            return None, None, "OpenRouter tardo demasiado en responder"
        
        except Exception as e:
            logger.error(f"Error generando SQL: {type(e).__name__}: {e}")
            return None, None, f"Error en servicio de IA: {str(e)[:100]}"

    async def generate_sql_with_fallback(
        self,
        query: str,
        schema_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 2,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Intenta generar SQL con reintentos en caso de error transitorio.

        Args:
            query: Consulta natural.
            schema_context: Context de esquema.
            conversation_history: Historial de conversacion.
            max_retries: Número máximo de reintentos.

        Returns:
            Tupla (sql, visualization_type, error_message).
        """
        for attempt in range(max_retries):
            sql, viz_type, error = await self.generate_sql(
                query, schema_context, conversation_history
            )
            
            if sql is not None:
                return sql, viz_type, error
            
            if attempt < max_retries - 1:
                logger.info(f"Reintentando generación de SQL (intento {attempt + 2}/{max_retries})")
                import asyncio
                await asyncio.sleep(1)  # Esperar antes de reintentar
        
        return None, None, error  # Retornar último error

