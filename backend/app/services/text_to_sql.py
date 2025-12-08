"""
Servicio Text-to-SQL con OpenRouter.

Convierte consultas naturales en SQL válido usando LLM con validación de seguridad.
Detecta consultas de estadísticas de jugadores y usa PlayerStatsService con caché.
"""

import re
import logging
import json
from typing import Optional, List, Dict, Any, Tuple
from openai import AsyncOpenAI
import httpx

from app.services.player_stats_service import PlayerStatsService, PlayerStatsServiceError
from app.models import PlayerSeasonStats
from app.database import async_session_maker
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Configuración de OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"  # Modelo rápido y económico


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
        self.player_stats_service = PlayerStatsService()
    
    @staticmethod
    def _requires_player_stats(query: str) -> bool:
        """
        Detecta si la consulta requiere estadísticas de jugadores en tiempo real.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si requiere stats de jugadores
        """
        query_lower = query.lower()
        
        # Keywords que indican consulta de stats
        stats_keywords = [
            "anotador", "reboteador", "asistente", "máximo", "top", "mejor",
            "estadística", "puntos", "rebotes", "asistencias", "triples",
            "scorer", "rebounder", "assists", "stats", "statistics",
            "temporada", "season", "jornada", "round"
        ]
        
        return any(keyword in query_lower for keyword in stats_keywords)
    
    async def _extract_stats_params(self, query: str) -> Dict[str, Any]:
        """
        Extrae parámetros para consulta de stats usando LLM.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con parámetros: seasoncode, stat, top_n, team_code
        """
        extraction_prompt = f"""Extract parameters from this basketball stats query:
Query: "{query}"

Return ONLY a JSON object with these fields:
- seasoncode: "E2025" (default), "E2024", etc. If user says "esta temporada" or "current" use "E2025"
- stat: "points", "rebounds_total", "assists", "steals", "blocks", etc
- top_n: number of players to return (default 10)
- team_code: team code if mentioned (optional, can be null)

Examples:
"Top 10 anotadores 2025" -> {{"seasoncode": "E2025", "stat": "points", "top_n": 10, "team_code": null}}
"Mejores reboteadores del Real Madrid" -> {{"seasoncode": "E2025", "stat": "rebounds_total", "top_n": 10, "team_code": "RM"}}
"5 mejores asistentes temporada 2024" -> {{"seasoncode": "E2024", "stat": "assists", "top_n": 5, "team_code": null}}

Return ONLY the JSON, no explanation."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,
                max_tokens=200,
                timeout=15,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extraer JSON
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            params = json.loads(response_text)
            
            # Valores por defecto
            params.setdefault("seasoncode", "E2025")
            params.setdefault("stat", "points")
            params.setdefault("top_n", 10)
            params.setdefault("team_code", None)
            
            logger.info(f"Parámetros extraídos: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error extrayendo parámetros: {e}")
            # Retornar defaults
            return {
                "seasoncode": "E2025",
                "stat": "points",
                "top_n": 10,
                "team_code": None
            }

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

** CRITICAL - SEASON VALUES **
The database ONLY contains data for seasons: 2023, 2024, 2025
- NEVER use season = 2022, 2021, 2020, or any other year
- NEVER use season as a string like season = '2022'
- ALWAYS use integer season values: 2023, 2024, 2025
- When user says "esta temporada" or "this season" or "current": Use season IN (2024, 2025)
- When user says specific year 2025: Use season = 2025
- When user says all seasons: Either remove WHERE season clause OR use season IN (2023, 2024, 2025)

GENERAL RULES:
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

Query: "máximo anotador"
{{
  "sql": "SELECT p.name, SUM(ps.points) as total_points FROM players p JOIN player_stats_games ps ON p.id = ps.player_id JOIN games g ON ps.game_id = g.id GROUP BY p.id, p.name ORDER BY total_points DESC LIMIT 1;",
  "visualization_type": "table"
}}

Query: "máximo anotador de esta temporada"
{{
  "sql": "SELECT p.name, SUM(ps.points) as total_points FROM players p JOIN player_stats_games ps ON p.id = ps.player_id JOIN games g ON ps.game_id = g.id WHERE g.season IN (2024, 2025) GROUP BY p.id, p.name ORDER BY total_points DESC LIMIT 1;",
  "visualization_type": "table"
}}

Query: "puntos por equipo esta temporada"
{{
  "sql": "SELECT t.name, SUM(ps.points) as total_points FROM teams t JOIN players p ON t.id = p.team_id JOIN player_stats_games ps ON p.id = ps.player_id JOIN games g ON ps.game_id = g.id WHERE g.season IN (2024, 2025) GROUP BY t.id, t.name ORDER BY total_points DESC;",
  "visualization_type": "bar"
}}

Query: "comparaci$([char]0x00F3)n de asistencias entre Larkin y Micic"
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

    async def _extract_stats_params(self, query: str) -> Dict[str, Any]:
        """
        Extrae parámetros de una consulta de estadísticas.
        
        Retorna:
            {
                "seasoncode": "E2025",
                "stat": "points|assists|rebounds|...",
                "top_n": 10,
                "team_code": None (opcional)
            }
        """
        seasoncode = "E2025"  # Por defecto temporada actual
        top_n = 10  # Por defecto top 10
        stat = "points"  # Por defecto puntos
        team_code = None
        
        # Detectar temporada
        season_match = re.search(r"(E?202[0-9]|E?201[0-9])", query, re.IGNORECASE)
        if season_match:
            season = season_match.group(1)
            if not season.startswith("E"):
                season = "E" + season
            seasoncode = season
        
        # Detectar número de jugadores
        top_match = re.search(r"(\d+)\s*(primeros|máximos|top)", query, re.IGNORECASE)
        if top_match:
            top_n = int(top_match.group(1))
        
        # Detectar tipo de estadística
        if re.search(r"anotador|puntos|points|scoring", query, re.IGNORECASE):
            stat = "points"
        elif re.search(r"asistencias|assists", query, re.IGNORECASE):
            stat = "assists"
        elif re.search(r"rebote|rebounds", query, re.IGNORECASE):
            stat = "rebounds"
        elif re.search(r"eficiencia|pir|rating", query, re.IGNORECASE):
            stat = "pir"
        
        # Detectar equipo (si la consulta especifica uno)
        team_patterns = [
            r"del\s+(\w+\s*\w*)",  # "del Real Madrid"
            r"de\s+(\w+\s*\w*)",   # "de Barcelona"
            r"equipo\s+(\w+\s*\w*)", # "equipo Real Madrid"
        ]
        for pattern in team_patterns:
            team_match = re.search(pattern, query, re.IGNORECASE)
            if team_match:
                team_code = team_match.group(1).strip().upper()
                break
        
        return {
            "seasoncode": seasoncode,
            "stat": stat,
            "top_n": top_n,
            "team_code": team_code
        }

    async def _get_player_stats_from_db(
        self,
        seasoncode: str,
        stat: str,
        top_n: int = 10,
        team_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener estadísticas de jugadores desde la BD (poblada por ETL).
        
        Args:
            seasoncode: Código de temporada (ej: "E2025")
            stat: Tipo de estadística ("points", "assists", "rebounds", "pir")
            top_n: Número de jugadores a retornar
            team_code: Código de equipo (opcional)
        
        Returns:
            Lista de diccionarios con jugadores y sus estadísticas
        """
        try:
            async with async_session_maker() as session:
                # Construir query base
                query = select(
                    PlayerSeasonStats.id,
                    PlayerSeasonStats.player_id,
                    PlayerSeasonStats.season,
                    PlayerSeasonStats.points,
                    PlayerSeasonStats.assists,
                    PlayerSeasonStats.rebounds,
                    PlayerSeasonStats.pir,
                    PlayerSeasonStats.games_played,
                ).where(PlayerSeasonStats.season == seasoncode)
                
                # Filtrar por equipo si se especifica
                if team_code:
                    from app.models import Player, Team
                    query = query.join(Player).join(Team).where(
                        Team.code == team_code
                    )
                
                # Ordenar por estadística solicitada
                if stat == "points":
                    query = query.order_by(PlayerSeasonStats.points.desc())
                elif stat == "assists":
                    query = query.order_by(PlayerSeasonStats.assists.desc())
                elif stat == "rebounds":
                    query = query.order_by(PlayerSeasonStats.rebounds.desc())
                elif stat == "pir":
                    query = query.order_by(PlayerSeasonStats.pir.desc())
                
                # Limitar resultados
                query = query.limit(top_n)
                
                # Ejecutar query
                result = await session.execute(query)
                rows = result.fetchall()
                
                # Convertir a formato JSON
                data = []
                for idx, row in enumerate(rows, 1):
                    data.append({
                        "rank": idx,
                        "player_id": row.player_id,
                        "season": row.season,
                        "points": float(row.points) if row.points else 0,
                        "assists": float(row.assists) if row.assists else 0,
                        "rebounds": float(row.rebounds) if row.rebounds else 0,
                        "pir": float(row.pir) if row.pir else 0,
                        "games_played": row.games_played,
                    })
                
                return data
                
        except Exception as e:
            logger.error(f"Error obteniendo stats de BD: {e}")
            raise

    async def generate_sql(
        self,
        query: str,
        schema_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Genera SQL a partir de una consulta natural.
        
        Detecta si la consulta requiere stats de jugadores y usa PlayerStatsService.
        Si no, genera SQL normal.

        Args:
            query: Consulta natural del usuario.
            schema_context: Context de esquema disponible.
            conversation_history: Historial de conversacion previo.

        Returns:
            Tupla (sql, visualization_type, error_message, direct_data).
            - Si es consulta de stats: sql=None, direct_data contiene resultados
            - Si es SQL normal: direct_data=None, sql contiene query
            Si hay error, sql y direct_data serán None.
        """
        try:
            logger.info(f"Generando SQL para query: {query}")
            
            # DETECTAR SI REQUIERE STATS DE JUGADORES
            if self._requires_player_stats(query):
                logger.info("Consulta detectada como stats de jugadores.")
                
                try:
                    # Extraer parámetros
                    params = await self._extract_stats_params(query)
                    
                    # Obtener stats desde BD (poblada por ETL diario a las 7 AM)
                    results = await self._get_player_stats_from_db(
                        seasoncode=params["seasoncode"],
                        stat=params["stat"],
                        top_n=params["top_n"],
                        team_code=params.get("team_code")
                    )
                    
                    logger.info(f"Stats obtenidas de BD: {len(results)} jugadores")
                    
                    # Retornar datos directos (sin SQL)
                    return None, "bar", None, results
                    
                except Exception as e:
                    logger.error(f"Error obteniendo estadísticas: {e}")
                    return None, None, f"Error obteniendo estadísticas: {str(e)}", None
            
            # SI NO ES STATS, CONTINUAR CON SQL NORMAL
            logger.info("Consulta normal. Generando SQL...")
            
            # Construir mensajes para el LLM
            messages = []
            
            # Agregar mensaje del sistema primero
            messages.append({
                "role": "system",
                "content": self._get_system_prompt(schema_context),
            })
            
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
                temperature=0.3,  # Bajo para consistencia
                max_tokens=500,
                timeout=30,  # Timeout de 30 segundos
            )
            
            # Extraer respuesta
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Respuesta de LLM: {response_text[:100]}...")
            
            # PRE-CORRECCIÓN DEFENSIVA: Si el LLM generó temporada 2022, corregir ANTES de parsear
            # Esto es crítico porque el LLM a veces ignora el prompt
            response_text = response_text.replace("'2022'", "'2024'")  # Reemplazar string '2022' con '2024'
            response_text = response_text.replace(", 2022", ", 2024")  # Reemplazar en listas
            response_text = response_text.replace("= 2022", "IN (2024, 2025)")  # Reemplazar número puro
            response_text = response_text.replace("= '2022'", "IN (2024, 2025)")  # Reemplazar string
            
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
                return None, None, "LLM no generó SQL válido", None
            
            # POST-VALIDACIÓN DEFENSIVA: Corregir valores de temporada muy comunes
            # Si el LLM ignora nuestras instrucciones y usa 2022, reemplazarlo
            # Esto es un último recurso cuando el prompt no es suficiente
            if "season = '2022'" in sql or "season = 2022" in sql:
                logger.warning("LLM utilizó temporada 2022 prohibida, corrigiendo automáticamente...")
                sql = sql.replace("season = '2022'", "season IN (2024, 2025)")
                sql = sql.replace("season = 2022", "season IN (2024, 2025)")
                logger.info(f"SQL corregido: {sql[:80]}...")
            
            # Validar seguridad del SQL
            is_safe, error_msg = self._validate_sql_safety(sql)
            if not is_safe:
                logger.warning(f"SQL rechazado por validación de seguridad: {error_msg}")
                return None, None, f"Consulta rechazada: {error_msg}", None
            
            logger.info(f"SQL generado exitosamente: {sql[:100]}...")
            return sql, visualization_type, None, None
        
        except httpx.TimeoutException:
            logger.error("Timeout al conectar con OpenRouter")
            return None, None, "OpenRouter tardo demasiado en responder", None
        
        except Exception as e:
            logger.error(f"Error generando SQL: {type(e).__name__}: {e}")
            return None, None, f"Error en servicio de IA: {str(e)[:100]}", None

    async def generate_sql_with_fallback(
        self,
        query: str,
        schema_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 2,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Intenta generar SQL con reintentos en caso de error transitorio.

        Args:
            query: Consulta natural.
            schema_context: Context de esquema.
            conversation_history: Historial de conversacion.
            max_retries: Número máximo de reintentos.

        Returns:
            Tupla (sql, visualization_type, error_message, direct_data).
        """
        for attempt in range(max_retries):
            sql, viz_type, error, direct_data = await self.generate_sql(
                query, schema_context, conversation_history
            )
            
            if sql is not None or direct_data is not None:
                return sql, viz_type, error, direct_data
            
            if attempt < max_retries - 1:
                logger.info(f"Reintentando generación de SQL (intento {attempt + 2}/{max_retries})")
                import asyncio
                await asyncio.sleep(1)  # Esperar antes de reintentar
        
        return None, None, error, None  # Retornar último error

