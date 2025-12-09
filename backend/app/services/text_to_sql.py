"""
Servicio Text-to-SQL con OpenRouter.

Convierte consultas naturales en SQL válido usando LLM con validación de seguridad.
Detecta consultas de estadísticas de jugadores y retorna datos desde BD poblada por ETL.
"""

import re
import logging
import json
import unicodedata
from typing import Optional, List, Dict, Any, Tuple
from openai import AsyncOpenAI
import httpx

from app.models import PlayerSeasonStats
from app.database import async_session_maker
from sqlalchemy import select, func, text
from etl.ingest_player_season_stats import run_ingest_player_season_stats

logger = logging.getLogger(__name__)

# Configuración de OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"  # Modelo rápido y económico


def normalize_text_for_matching(text: str) -> str:
    """
    Normaliza texto removiendo acentos y tildes para búsquedas insensibles.
    
    Ejemplo:
        "Llúll" -> "llull"
        "José María" -> "jose maria"
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado (minúsculas, sin acentos)
    """
    # Descomponer en caracteres base + diacríticos
    nfd = unicodedata.normalize('NFD', text)
    # Filtrar solo caracteres no-diacríticos
    without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return without_accents.lower()


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
    
    async def _correct_and_normalize_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Corrige erratas tipográficas y normaliza la consulta del usuario usando IA.
        
        Se ejecuta ANTES de generar SQL para corregir nombres de jugadores/equipos
        y mejorar la precisión del SQL generado.
        
        Args:
            query: Consulta original del usuario
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Consulta corregida y normalizada
        """
        try:
            # Si la consulta es muy corta, saltar corrección
            if len(query.strip()) < 10:
                return query
            
            correction_prompt = """Eres un asistente experto en consultas sobre estadísticas de baloncesto de la Euroleague.
Tu tarea es corregir erratas tipográficas y normalizar la consulta del usuario, manteniendo su intención original.

INSTRUCCIONES:
1. Corrige errores de ortografía y tipografía comunes
2. Normaliza nombres de jugadores y equipos a sus formas más comunes:
   - "Larkin" (no "Larkyn", "Larkin", etc.)
   - "Llull" (no "Llul", "Lull", etc.)
   - "Campazzo" (no "Campazo", "Campazo", etc.)
   - "Real Madrid" (no "real madrid", "RealMadrid", etc.)
   - "Barcelona" (no "Barsa", "Barça", etc.)
   - "Micic" (no "Micic", "Micić", etc.)
   - "Tavares" (no "Tavares", "Tavares", etc.)
   - "Vesely" (no "Vesely", "Vesely", etc.)
3. Mantén la intención original de la consulta
4. NO cambies el significado de la consulta
5. Si la consulta ya está correcta, devuélvela tal cual

EJEMPLOS:
- "puntos de Larkyn" -> "puntos de Larkin"
- "estadisticas de Campazo" -> "estadísticas de Campazzo"
- "maximo anotador del real madrid" -> "máximo anotador del Real Madrid"
- "estadisticas de Llul" -> "estadísticas de Llull"
- "top 5 anotadores" -> "top 5 anotadores" (sin cambios)

Responde SOLO con la consulta corregida, sin explicaciones adicionales."""

            messages = [
                {"role": "system", "content": correction_prompt},
            ]
            
            # Agregar historial si existe (últimos 2 mensajes para contexto)
            if conversation_history:
                messages.extend(conversation_history[-2:])
            
            messages.append({
                "role": "user",
                "content": f"Consulta original: {query}\n\nConsulta corregida:"
            })
            
            # Llamar a OpenRouter con modelo rápido y económico
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Muy bajo para consistencia
                max_tokens=200,   # Respuestas cortas
                timeout=10,       # Timeout corto
            )
            
            corrected_query = response.choices[0].message.content.strip()
            
            # Limpiar la respuesta (puede incluir prefijos como "Consulta corregida:")
            # Eliminar prefijos comunes que OpenAI puede agregar
            prefixes_to_remove = [
                "Consulta corregida:",
                "Consulta original:",
                "Consulta:",
                "Corrección:",
                "Corregida:",
                "Respuesta:",
            ]
            for prefix in prefixes_to_remove:
                if corrected_query.lower().startswith(prefix.lower()):
                    corrected_query = corrected_query[len(prefix):].strip()
            
            # También limpiar si aparece en cualquier parte del texto
            for prefix in prefixes_to_remove:
                corrected_query = corrected_query.replace(prefix, "").strip()
            
            # Si la respuesta está vacía o es muy corta, usar la original
            if not corrected_query or len(corrected_query.strip()) < 3:
                logger.warning(f"Corrección retornó respuesta vacía o muy corta ('{corrected_query}'), usando consulta original")
                return query
            
            # Si la corrección es muy diferente (más del 50% de cambio), usar la original
            # para evitar cambios no deseados
            original_words = set(query.lower().split())
            corrected_words = set(corrected_query.lower().split())
            if original_words and corrected_words:
                similarity = len(original_words & corrected_words) / max(len(original_words), len(corrected_words))
                
                if similarity < 0.5:
                    logger.warning(f"Corrección muy diferente de la original, usando original. Similaridad: {similarity:.2f}")
                    return query
            
            if corrected_query != query:
                logger.info(f"Consulta corregida: '{query}' -> '{corrected_query}'")
            
            return corrected_query
            
        except Exception as e:
            logger.warning(f"⚠ Error en corrección de consulta: {type(e).__name__}: {str(e)[:100]}. Usando consulta original.")
            return query  # Fallback a la consulta original
    
    @staticmethod
    def _requires_player_stats(query: str) -> bool:
        """
        Detecta si la consulta requiere estadísticas de jugadores en tiempo real.
        Insensible a tildes/acentos.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si requiere stats de jugadores
        """
        query_lower = query.lower()
        query_normalized = normalize_text_for_matching(query)
        
        # Keywords que indican consulta de RANKING/LEADERBOARD (sin tildes para mejor matching)
        # IMPORTANTE: No incluir palabras genéricas como "puntos", "estadisticas" o "dame" 
        # para evitar capturar consultas sobre jugadores específicos (ej: "Puntos de Llull").
        stats_keywords = [
            # Explicit leaderboard terms
            "maximo", "maxima", "top", "mejor", "mejores", "ranking", "lider", "lideres",
            "primeros", "leaders", "highest", "most", "best",
            # Plural nouns indicating lists (implying leaderboard)
            "anotadores", "reboteadores", "asistentes", "taponeadores", "recuperadores",
            "scorers", "rebounders", "assists leaders", "blockers", "stealers",
            # Specific phrases
            "quien anoto mas", "quien tiene mas", "quien hizo mas"
        ]
        
        return any(keyword in query_normalized for keyword in stats_keywords)
    
    @staticmethod
    def _is_games_query_unavailable(query: str) -> bool:
        """
        Detecta si la consulta pregunta por partidos específicos (datos no disponibles actualmente).
        Insensible a tildes/acentos.
        
        Retorna True si la consulta necesita datos de player_stats_games que aún no están poblados.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si pregunta por datos a nivel de partido que no disponemos
        """
        query_lower = query.lower()
        query_normalized = normalize_text_for_matching(query)
        
        # Keywords que indican que necesita datos a nivel de partido
        games_keywords = [
            # Partidos específicos
            "partidos donde", "partidos en", "en que partid", "en que partida",
            "cuando jug", "jugo en", "jugo contra",
            "enfrentamiento", "duelo", "partido entre", "en cada partid",
            "box score", "stats por partid", "estadisticas de ese partid",
            # Variaciones de "partidos de X con Y puntos"
            "partidos de", "partidos que", "partidos con",
            # Datos a nivel de partido
            "en el partido", "en ese partido", "por partido", "por cada partido"
        ]
        
        return any(keyword in query_normalized for keyword in games_keywords)
    
    
    @staticmethod
    def _detect_team_mentioned(query: str) -> bool:
        """
        Detecta si hay un nombre de equipo mencionado en la consulta, incluso si no está en el mapeo.
        
        Busca patrones comunes como "del [equipo]", "de [equipo]", "[equipo]" después de palabras clave.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si parece haber un nombre de equipo mencionado
        """
        query_lower = query.lower()
        query_normalized = normalize_text_for_matching(query)
        
        # Palabras comunes que NO son equipos
        non_team_words = {
            "temporada", "competicion", "euroliga", "liga", "season", "league",
            "maximo", "maxima", "maximos", "maximas", "mejor", "mejores",
            "anotador", "anotadores", "reboteador", "reboteadores",
            "asistente", "asistentes", "puntos", "rebotes", "asistencias",
            "dame", "muestra", "lista", "top", "primeros", "cuantos", "cuantas",
            "la", "el", "los", "las", "un", "una", "del", "de"
        }
        
        # Patrones mejorados que capturan nombres de equipos (pueden tener múltiples palabras)
        # Patrón 1: "del [equipo]" o "de [equipo]" - captura hasta 3 palabras
        del_de_pattern = r"(?:del|de)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})"
        matches = re.finditer(del_de_pattern, query)
        for match in matches:
            potential_team = match.group(1).lower().strip()
            # Verificar que no sea una palabra común
            words = potential_team.split()
            if words and all(word not in non_team_words for word in words):
                # Si tiene al menos una palabra significativa, probablemente es un equipo
                if any(len(word) > 2 for word in words):
                    return True
        
        # Patrón 2: Buscar en texto normalizado también (para capturar sin mayúsculas)
        del_de_normalized = r"(?:del|de)\s+(\w+(?:\s+\w+){0,2})"
        matches = re.finditer(del_de_normalized, query_normalized, re.IGNORECASE)
        for match in matches:
            potential_team = match.group(1).lower().strip()
            words = potential_team.split()
            if words and all(word not in non_team_words for word in words):
                if any(len(word) > 2 for word in words):
                    return True
        
        # Patrón 3: "equipo [nombre]" o "del equipo [nombre]"
        equipo_pattern = r"equipo\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})"
        matches = re.finditer(equipo_pattern, query)
        for match in matches:
            potential_team = match.group(1).lower().strip()
            words = potential_team.split()
            if words and all(word not in non_team_words for word in words):
                if any(len(word) > 2 for word in words):
                    return True
        
        return False
    
    @staticmethod
    async def _extract_stats_params(query: str) -> Dict[str, Any]:
        """
        Extrae parámetros para consulta de stats SIN usar LLM (rápido y confiable).
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Diccionario con parámetros: seasoncode, stat, top_n, team_code
        """
        try:
            query_lower = query.lower()
            
            # Valor por defecto para temporada
            seasoncode = "E2025"
            if "2024" in query:
                seasoncode = "E2024"
            elif "2023" in query:
                seasoncode = "E2023"
            elif "pasada" in query_lower or "anterior" in query_lower or "last season" in query_lower:
                seasoncode = "E2024"
            
            # Detectar tipo de estadística
            stat = "points"  # Default
            if any(word in query_lower for word in ["rebote", "rebound"]):
                stat = "rebounds"
            elif any(word in query_lower for word in ["asist", "assist"]):
                stat = "assists"
            elif any(word in query_lower for word in ["triple", "3pt", "3p"]):
                stat = "threePointsMade"
            elif any(word in query_lower for word in ["robo", "steal"]):
                stat = "steals"
            elif any(word in query_lower for word in ["bloque", "block"]):
                stat = "blocks"
            elif any(word in query_lower for word in ["pir", "eficiencia", "efficiency"]):
                stat = "pir"
            
            # Extraer número (top N)
            top_n = 10  # Default
            number_match = re.search(r"\d+", query)
            if number_match:
                top_n = int(number_match.group(0))
            
            # Detectar código de equipo
            team_code = None
            team_mapping = {
                "real madrid": "RM",
                "madrid": "RM",
                "barcelona": "BAR",
                "barca": "BAR",
                "milano": "OLM",
                "olympiacos": "OLY",
                "atenas": "OLY",
                "panathinaikos": "PAO",
                "fenerbahce": "FEN",
                "estambul": "FEN",
                "maccabi": "MTA",
                "tel aviv": "MTA",
                "paris": "PAR",
            }
            
            for team_name, code in team_mapping.items():
                if team_name in query_lower:
                    team_code = code
                    break
            
            params = {
                "seasoncode": seasoncode,
                "stat": stat,
                "top_n": top_n,
                "team_code": team_code
            }
            
            logger.info(f"Parámetros extraídos (local): {params}")
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
- Available seasons in database: 2022, 2023, 2024, 2025 (may vary by table).
- For `players` table, season is a STRING: 'E2022', 'E2023', 'E2024', 'E2025'. Use `p.season` for roster queries.
- For `player_season_stats`, season is a STRING: 'E2022', 'E2023', 'E2024', 'E2025'. Use `ps.season` when querying stats.
- For `games`, season is an INTEGER: 2022, 2023, 2024, 2025.
- **SEASON CONVERSION RULES:**
  - **ABSOLUTELY CRITICAL - DEFAULT SEASON:** If the user does NOT mention any season/year/temporada in their query, you MUST ALWAYS filter by the CURRENT season: 'E2025' (for players/player_season_stats) or 2025 (for games).
    * Example: "Compara Vesely y Tavares" → MUST include `ps.season = 'E2025'` in WHERE clause.
    * Example: "puntos de Larkin" → MUST include `ps.season = 'E2025'` in WHERE clause.
    * **NEVER return data from multiple seasons unless the user explicitly asks for multiple seasons or comparisons between specific seasons.**
  - When user mentions a year (e.g., "2022", "2025"), convert to season code format:
    * "2022" → 'E2022' (for players/player_season_stats) or 2022 (for games)
    * "2023" → 'E2023' (for players/player_season_stats) or 2023 (for games)
    * "2024" → 'E2024' (for players/player_season_stats) or 2024 (for games)
    * "2025" → 'E2025' (for players/player_season_stats) or 2025 (for games)
  - When user says "esta temporada" / "la temporada" / "current season":
    * STRICTLY use season = 'E2025' (or season = 2025 for games).
  - When user says "temporada pasada" / "last season" / "anterior":
    * STRICTLY use season = 'E2024' (or season = 2024 for games).
  - **ONLY when user explicitly asks to compare seasons** (e.g., "Compara la temporada 2022 y 2025", "temporadas 2022 y 2023"):
    * You may return multiple seasons using OR conditions: `(ps.season = 'E2022' OR ps.season = 'E2025')`
- **IMPORTANT:** For roster queries (listing players of a team), use `p.season` from `players` table, NOT `ps.season` from `player_season_stats`.

GENERAL RULES:
1. You MUST return ONLY a JSON object with "sql" and "visualization_type" keys.
2. The "sql" field must contain a valid PostgreSQL SELECT query.
3. The "visualization_type" must be one of: 'table', 'bar', 'line', 'scatter', 'text'.
   - Use 'text' ONLY for queries that return a SINGLE value (1 row AND 1 column). Examples: "en qué equipo juega X", "cuántos partidos jugó X".
   - Use 'table' for:
     * Multi-row results (2+ rows) - ALWAYS use 'table' for comparisons between seasons, players, etc.
     * Single row with 2+ columns - ALWAYS use 'table' when there are multiple columns.
     * Any structured list or comparison.
   - Use 'bar', 'line', 'scatter' for comparative data or trends (only when explicitly requested for charts).
4. NEVER include DROP, DELETE, TRUNCATE, or ALTER statements.
5. Always use table aliases for readability (p, ps, t, g).
6. Prioritize `player_season_stats` for season totals/averages queries.
7. Use `player_stats_games` only when specific game details are needed.
8. Column names in `player_stats_games`: three_points_made, rebounds (NOT rebounds_total, NOT fg3_made).
9. Column names in `player_season_stats`: "threePointsMade" (quoted), rebounds.
10. ALWAYS alias columns with Spanish, human-readable names (e.g. AS Puntos, AS Rebotes, AS Triples).
    - p.name -> AS Jugador / AS Nombre
    - ps.points -> AS Puntos
    - ps.assists -> AS Asistencias
    - ps.rebounds -> AS Rebotes
    - ps."threePointsMade" -> AS Triples
    - ps.pir -> AS Valoracion
    - ps.games_played -> AS Partidos
    - t.name -> AS Equipo
    - **DO NOT SELECT p.position** - Position data is not available in the database.
11. AMBIGUOUS COLUMNS: When joining tables (e.g. players & teams), ALWAYS prefix 'name' (p.name, t.name) to avoid ambiguity error.
12. **ROSTER QUERIES (CRITICAL):** When user asks for "jugadores de [team]", "lista de jugadores", "plantilla", or similar roster queries:
    - **DO NOT use LIMIT** - Return ALL players for that team.
    - Only select p.name AS Jugador (no position, no other columns unless explicitly requested).
    - Always ORDER BY p.name for consistency.
    - **MANDATORY:** Use `p.season` from the `players` table, NOT `ps.season` from `player_season_stats`.
    - **DO NOT JOIN with `player_season_stats` for roster queries** - Only JOIN with `teams` table.
    - For team name matching, use `t.name ILIKE '%team_name%'` for flexible matching (case-insensitive, partial match).
    - Team names in database may have variations (e.g., "Hapoel Tel Aviv BC" vs "Hapoel Tel Aviv"), so use partial matching with ILIKE.
    - **CRITICAL for multi-word team names:** If the team name has 2+ words, use AND conditions (not OR) to ensure ALL key words are present.
      Example: For "Hapoel Tel Aviv", use: `(t.name ILIKE '%Hapoel%' AND t.name ILIKE '%Tel Aviv%')`
      This ensures matches even if the database has "Hapoel Tel Aviv BC" while avoiding matches with other teams that share common words (e.g., "Maccabi Tel Aviv").
      NEVER use OR for team name matching as it will mix different teams.

FEW-SHOT EXAMPLES:

Query: "puntos de Larkin"
{{
  "sql": "SELECT p.name AS Jugador, ps.points AS Puntos, ps.season AS Temporada FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE p.name ILIKE '%Larkin%' AND ps.season = 'E2025';",
  "visualization_type": "text"
}}

Query: "en qué equipo juega Oturu"
{{
  "sql": "SELECT p.name AS Jugador, t.name AS Equipo FROM players p JOIN teams t ON p.team_id = t.id WHERE p.name ILIKE '%Oturu%' AND p.season = 'E2025';",
  "visualization_type": "text"
}}

Query: "máximo anotador"
{{
  "sql": "SELECT p.name AS Jugador, ps.points AS Puntos, ps.season AS Temporada FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE ps.season = 'E2025' ORDER BY ps.points DESC LIMIT 1;",
  "visualization_type": "text"
}}

Query: "puntos por equipo esta temporada"
{{
  "sql": "SELECT t.name AS Equipo, SUM(ps.points) AS Puntos_Totales FROM teams t JOIN players p ON t.id = p.team_id JOIN player_season_stats ps ON p.id = ps.player_id WHERE ps.season = 'E2025' GROUP BY t.id, t.name ORDER BY Puntos_Totales DESC;",
  "visualization_type": "bar"
}}

Query: "comparaci$([char]0x00F3)n de asistencias entre Larkin y Micic"
{{
  "sql": "SELECT p.name AS Jugador, ps.assists AS Asistencias, ps.season AS Temporada FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE (p.name ILIKE '%Larkin%' OR p.name ILIKE '%Micic%') AND ps.season = 'E2025' ORDER BY Asistencias DESC;",
  "visualization_type": "bar"
}}

Query: "Compara la temporada de Vesely y Tavares"
{{
  "sql": "SELECT ps.season AS Temporada, p.name AS Jugador, ps.points AS Puntos, ps.assists AS Asistencias, ps.rebounds AS Rebotes, ps.\"threePointsMade\" AS Triples, ps.pir AS Valoracion, ps.games_played AS Partidos FROM player_season_stats ps JOIN players p ON p.id = ps.player_id WHERE (p.name ILIKE '%Vesely%' OR p.name ILIKE '%Tavares%') AND ps.season = 'E2025' ORDER BY p.name;",
  "visualization_type": "table"
}}
NOTE: Even though the user says "la temporada" (singular), since they did NOT specify which season, we use the CURRENT season 'E2025'. We do NOT return all seasons.

Query: "Estadisticas de Llull"
{{
  "sql": "SELECT p.name AS Jugador, ps.points AS Puntos, ps.assists AS Asistencias, ps.rebounds AS Rebotes, ps.\"threePointsMade\" AS Triples, ps.pir AS Valoracion, ps.games_played AS Partidos FROM players p JOIN player_season_stats ps ON p.id = ps.player_id WHERE p.name ILIKE '%Llull%' AND ps.season = 'E2025';",
  "visualization_type": "table"
}}

Query: "Cuales son los jugadores del Real Madrid"
{{
  "sql": "SELECT p.name AS Jugador FROM players p JOIN teams t ON p.team_id = t.id WHERE t.name ILIKE '%Real Madrid%' AND p.season = 'E2025' ORDER BY p.name;",
  "visualization_type": "table"
}}

Query: "Dame la lista de los jugadores de Panathinaikos"
{{
  "sql": "SELECT p.name AS Jugador FROM players p JOIN teams t ON p.team_id = t.id WHERE (t.name ILIKE '%Panathinaikos%' OR t.code = 'PAO') AND p.season = 'E2025' ORDER BY p.name;",
  "visualization_type": "table"
}}

Query: "Jugadores del Hapoel Tel Aviv"
{{
  "sql": "SELECT p.name AS Jugador FROM players p JOIN teams t ON p.team_id = t.id WHERE (t.name ILIKE '%Hapoel%' AND t.name ILIKE '%Tel Aviv%') AND p.season = 'E2025' ORDER BY p.name;",
  "visualization_type": "table"
}}

Query: "Compara la temporada 2022 y la actual de Llull"
{{
  "sql": "SELECT ps.season AS Temporada, ps.points AS Puntos, ps.assists AS Asistencias, ps.rebounds AS Rebotes, ps.\"threePointsMade\" AS Triples, ps.pir AS Valoracion, ps.games_played AS Partidos FROM player_season_stats ps JOIN players p ON p.id = ps.player_id WHERE p.name ILIKE '%Llull%' AND (ps.season = 'E2022' OR ps.season = 'E2025') ORDER BY ps.season;",
  "visualization_type": "table"
}}
NOTE: This query returns 2 rows (one per season) with multiple columns. ALWAYS use 'table' for season comparisons or any query returning 2+ rows.

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

    async def _ensure_season_data(self, season_code: str):
        """
        Verifica si existen datos para la temporada solicitada.
        Si no existen, ejecuta la ingesta (ETL) bajo demanda.
        
        Args:
            season_code: Código de temporada (ej: 'E2024').
        """
        try:
            # Extraer año (E2024 -> 2024)
            year = int(season_code.replace("E", ""))
            
            # Verificar si ya existen datos en la BD
            async with async_session_maker() as session:
                # Consulta ligera para verificar existencia
                stmt = text("SELECT 1 FROM player_season_stats WHERE season = :season LIMIT 1")
                result = await session.execute(stmt, {"season": season_code})
                exists = result.scalar() is not None
                
            if exists:
                logger.debug(f"Datos encontrados para temporada {season_code}")
                return

            logger.info(f"Datos NO encontrados para temporada {season_code}. Iniciando ingesta bajo demanda...")
            
            # Ejecutar ETL
            # Nota: Esto puede tardar unos segundos
            await run_ingest_player_season_stats(season=year)
            
            logger.info(f"Ingesta bajo demanda completada para {season_code}")
            
        except Exception as e:
            logger.error(f"Error en ingesta bajo demanda para {season_code}: {e}")
            # No lanzamos excepción para permitir que el flujo continúe (aunque probablemente devolverá 0 resultados)

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
        query_lower = query.lower()
        query_normalized = normalize_text_for_matching(query)
        
        # Detectar si la consulta es singular (máximo/mejor/quien) o plural (lista/top)
        singular_keywords = [
            "quién", "quien", "cual", "máximo", "maximo", "mejor", 
            "máxima anotadora", "maximo anotador", "máxima", "maximo",
            "quien es el", "quien es la"
        ]
        plural_keywords = [
            "lista", "top", "dame", "dame la lista", "primeros", "máximos", 
            "dame los", "dame las", "son los", "son las", "cuáles", "cuales"
        ]
        
        # Detectar si es singular (top_n = 1) o plural (default 10)
        is_singular = any(normalize_text_for_matching(keyword) in query_normalized for keyword in singular_keywords)
        is_plural = any(keyword in query_lower for keyword in plural_keywords)
        
        if is_singular and not is_plural:
            top_n = 1  # Usuario pregunta por UNO
        
        # Detectar temporada
        season_match = re.search(r"(E?202[0-9]|E?201[0-9])", query, re.IGNORECASE)
        if season_match:
            season = season_match.group(1)
            if not season.startswith("E"):
                season = "E" + season
            seasoncode = season
        
        # Detectar número de jugadores (override explícito)
        # Buscar patrones como "Top 5", "5 máximos", "primeros 3"
        top_match = re.search(r"(?:top|primeros|máximos)\s+(\d+)|(\d+)\s+(?:primeros|máximos|top)", query, re.IGNORECASE)
        if top_match:
            # Extraer el número (puede estar en grupo 1 o grupo 2)
            num_str = top_match.group(1) or top_match.group(2)
            if num_str:
                top_n = int(num_str)
        
        # Detectar tipo de estadística (buscar más variaciones)
        if re.search(r"anotador|puntos|points|scoring|anotad", query, re.IGNORECASE):
            stat = "points"
        elif re.search(r"asistencia|asistente|assists|asist", query, re.IGNORECASE):
            stat = "assists"
        elif re.search(r"rebote|rebounds|rebotead", query, re.IGNORECASE):
            stat = "rebounds"
        elif re.search(r"eficiencia|pir|rating", query, re.IGNORECASE):
            stat = "pir"
        
        # Detectar equipo (si la consulta especifica uno)
        # Mapeo de nombres de equipos -> códigos
        team_keywords = {
            "real madrid": "RM",
            "madrid": "RM",
            "barcelona": "BAR",
            "barca": "BAR",
            "milano": "OLM",
            "olympiacos": "OLY",
            "atenas": "OLY",
            "panathinaikos": "PAO",
            "fenerbahce": "FEN",
            "estambul": "FEN",
            "maccabi": "MTA",
            "tel aviv": "MTA",
            "paris": "PAR",
        }
        
        # Solo detectar equipo si aparece explícitamente en la consulta
        for team_name, code in team_keywords.items():
            if team_name in query_lower:
                # Verificar que no sea parte de otra palabra
                # Por ejemplo, no queremos "madrid" de "temporada"
                if re.search(r'\b' + re.escape(team_name) + r'\b', query_lower):
                    team_code = code
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
                from app.models import Player, Team
                
                # Construir query con JOIN a Player para obtener el nombre
                query = select(
                    PlayerSeasonStats.id,
                    PlayerSeasonStats.player_id,
                    PlayerSeasonStats.season,
                    PlayerSeasonStats.points,
                    PlayerSeasonStats.assists,
                    PlayerSeasonStats.rebounds,
                    PlayerSeasonStats.pir,
                    PlayerSeasonStats.games_played,
                    Player.name.label("player_name"),  # Agregar nombre del jugador
                ).join(Player, PlayerSeasonStats.player_id == Player.id).where(
                    PlayerSeasonStats.season == seasoncode
                )
                
                # Filtrar por equipo si se especifica
                if team_code:
                    query = query.join(Team, Player.team_id == Team.id).where(
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
                        "player_name": row.player_name,  # Incluir nombre
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
        
        Detecta si la consulta requiere stats de jugadores y retorna datos desde BD.
        Si no, genera SQL normal.

        Args:
            query: Consulta natural del usuario.
            schema_context: Context de esquema disponible.
            conversation_history: Historial de conversacion previo.

        Returns:
            Tupla (sql, visualization_type, error_message, direct_data).
            - Si es consulta de stats: sql=None, direct_data contiene resultados desde BD
            - Si es SQL normal: direct_data=None, sql contiene query
            Si hay error, sql y direct_data serán None.
        """
        try:
            logger.info(f"Generando SQL para query original: '{query}'")
            
            # CORRECCIÓN PREVIA DE LA CONSULTA (antes de cualquier otra lógica)
            logger.debug("Iniciando corrección de consulta con OpenAI...")
            corrected_query = await self._correct_and_normalize_query(query, conversation_history)
            if corrected_query != query:
                logger.info(f"✓ Consulta corregida aplicada: '{query}' -> '{corrected_query}'")
                query = corrected_query  # Usar la consulta corregida para el resto del flujo
            else:
                logger.debug("Consulta no requirió corrección (ya está correcta)")
            
            # DETECTAR SI REQUIERE STATS DE JUGADORES
            requires_stats = self._requires_player_stats(query)
            logger.info(f"Requiere stats de jugadores: {requires_stats}")
            
            # DETECTAR SI PREGUNTA POR PARTIDOS ESPECÍFICOS (datos no disponibles aún)
            is_games_unavailable = self._is_games_query_unavailable(query)
            if is_games_unavailable:
                logger.info("Consulta detectada como búsqueda de partidos específicos (datos no disponibles).")
                error_msg = (
                    "\n\n⚠️ Esta consulta requiere datos detallados por partido que aún no están disponibles.\n\n"
                    "❌ No podemos: Mostrar estadísticas de partidos individuales, box scores, o datos jugador-por-jugador en cada partido.\n\n"
                    "✅ Podemos: Mostrar estadísticas agregadas de temporada (máximo anotador, mejores reboteadores, comparativas entre jugadores, rosters de equipos).\n\n"
                    "Próximamente: Análisis detallado de partidos individuales."
                )
                return None, None, error_msg, None
            
            if requires_stats:
                logger.info("Consulta detectada como stats de jugadores.")
                
                try:
                    # Extraer parámetros (local, sin LLM)
                    params = await self._extract_stats_params(query)
                    
                    # CRÍTICO: Si hay un equipo mencionado pero no está en el mapeo (team_code es None),
                    # usar el flujo de SQL para que el LLM pueda generar el filtro correcto con t.name ILIKE
                    team_mentioned = self._detect_team_mentioned(query)
                    if team_mentioned and params.get("team_code") is None:
                        logger.info("Equipo mencionado pero no en mapeo. Usando flujo SQL para filtro correcto.")
                        # Continuar con el flujo de SQL normal (más abajo)
                    else:
                        # VERIFICACIÓN DE INGESTA BAJO DEMANDA
                        await self._ensure_season_data(params["seasoncode"])
                        
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
            
            # DETECCION PROACTIVA DE TEMPORADA PARA INGESTA BAJO DEMANDA
            # Incluso si va a LLM, necesitamos asegurar que los datos existan
            try:
                # Usamos la misma lógica de extracción para encontrar la temporada
                # Si el usuario menciona una temporada específica (ej: "2024"), esto asegurará que esté cargada
                temp_params = await self._extract_stats_params(query)
                await self._ensure_season_data(temp_params["seasoncode"])
            except Exception as e:
                logger.warning(f"Fallo en chequeo proactivo de temporada: {e}")
            
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
            
            # PRE-CORRECCIÓN: Convertir años mencionados a formato de temporada correcto
            # Si el usuario mencionó "2022", debe convertirse a 'E2022' (no reemplazarse)
            # Solo corregir si aparece como número puro sin el prefijo 'E'
            # No reemplazar 'E2022' ya que es válido
            
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
            
            # POST-VALIDACIÓN: Corregir formato de temporada si es necesario
            # Convertir años sin prefijo 'E' a formato correcto para player_season_stats
            # Ejemplo: ps.season = '2022' → ps.season = 'E2022'
            # Pero solo si es para player_season_stats o players, no para games
            if "ps.season = '2022'" in sql:
                logger.info("Corrigiendo formato de temporada: '2022' → 'E2022' para player_season_stats")
                sql = sql.replace("ps.season = '2022'", "ps.season = 'E2022'")
            if "p.season = '2022'" in sql:
                logger.info("Corrigiendo formato de temporada: '2022' → 'E2022' para players")
                sql = sql.replace("p.season = '2022'", "p.season = 'E2022'")
            # Similar para otros años si aparecen sin prefijo
            for year in ['2023', '2024', '2025']:
                if f"ps.season = '{year}'" in sql:
                    logger.info(f"Corrigiendo formato de temporada: '{year}' → 'E{year}' para player_season_stats")
                    sql = sql.replace(f"ps.season = '{year}'", f"ps.season = 'E{year}'")
                if f"p.season = '{year}'" in sql:
                    logger.info(f"Corrigiendo formato de temporada: '{year}' → 'E{year}' para players")
                    sql = sql.replace(f"p.season = '{year}'", f"p.season = 'E{year}'")
            
            # Validar seguridad del SQL
            is_safe, error_msg = self._validate_sql_safety(sql)
            if not is_safe:
                logger.warning(f"SQL rechazado por validación de seguridad: {error_msg}")
                return None, None, f"Consulta rechazada: {error_msg}", None
            
            # CORRECCIÓN DE PRECEDENCIA DE OPERADORES EN WHERE:
            # Detectar patrones problemáticos: "OR ... AND" sin paréntesis alrededor del OR
            # Ejemplo problemático: WHERE name ILIKE '%A%' OR name ILIKE '%B%' AND season = 'E2025'
            # Debe ser: WHERE (name ILIKE '%A%' OR name ILIKE '%B%') AND season = 'E2025'
            # Buscar patrón específico: condiciones ILIKE con OR seguidas de AND (sin paréntesis)
            where_pattern = r"WHERE\s+(.+?)(?=\s*(?:ORDER\s+BY|LIMIT|GROUP\s+BY|$))"
            where_match = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)
            if where_match:
                where_clause = where_match.group(1).strip()
                
                # Detectar si hay un patrón: condiciones OR seguidas de AND (sin paréntesis)
                # Buscar cualquier secuencia de: condición OR condición ... AND
                # Patrón para encontrar al menos una condición OR seguida de AND
                or_and_pattern = r"(\w+(?:\.\w+)?\s+ILIKE\s+(?:'[^']*'|\"[^\"]*\"))\s+OR\s+(\w+(?:\.\w+)?\s+ILIKE\s+(?:'[^']*'|\"[^\"]*\"))\s+AND\s+"
                match = re.search(or_and_pattern, where_clause, re.IGNORECASE)
                
                if match:
                    # Verificar que no haya paréntesis justo antes de la primera condición
                    before_match = where_clause[:match.start()]
                    
                    # Si no hay paréntesis de apertura antes, corregir
                    if not re.search(r"\(\s*$", before_match.rstrip()):
                        # Encontrar el inicio de la primera condición ILIKE en la secuencia OR
                        # Puede haber múltiples OR, así que buscar desde el inicio del match hacia atrás
                        # para encontrar el inicio de la secuencia OR
                        start_pos = match.start(1)  # Inicio de la primera condición ILIKE capturada
                        
                        # Buscar si hay más condiciones OR antes (patrón más complejo)
                        # Retroceder para encontrar todas las condiciones OR consecutivas
                        # Buscar desde start_pos hacia atrás para ver si hay más OR
                        before_start = where_clause[:start_pos].rstrip()
                        
                        # Si hay algo antes, verificar si termina con OR (entonces hay más condiciones)
                        if before_start and re.search(r"\s+OR\s+$", before_start, re.IGNORECASE):
                            # Hay más condiciones OR antes, buscar el inicio real
                            # Buscar hacia atrás desde start_pos para encontrar el inicio de la secuencia
                            # Buscar el último patrón ILIKE antes del match actual
                            ilike_before = list(re.finditer(r"\w+(?:\.\w+)?\s+ILIKE\s+(?:'[^']*'|\"[^\"]*\")", where_clause[:start_pos], re.IGNORECASE))
                            if ilike_before:
                                # Verificar si la última condición ILIKE antes está conectada con OR
                                last_ilike = ilike_before[-1]
                                between = where_clause[last_ilike.end():start_pos]
                                if re.search(r"\s+OR\s+", between, re.IGNORECASE):
                                    start_pos = last_ilike.start()  # Comenzar desde la primera condición de la secuencia
                        
                        # Buscar dónde está el AND que sigue a la secuencia OR
                        and_pos = where_clause.find(" AND ", match.end(2), len(where_clause))
                        if and_pos == -1:
                            and_pos = where_clause.find(" and ", match.end(2), len(where_clause))
                        
                        if and_pos > 0:
                            # Extraer la parte OR que necesita paréntesis
                            or_conditions = where_clause[start_pos:and_pos].strip()
                            after_and = where_clause[and_pos + 5:].strip()  # +5 para " AND "
                            before_or = where_clause[:start_pos].rstrip()
                            
                            # Reconstruir con paréntesis
                            if before_or:
                                new_where_clause = f"{before_or} ({or_conditions}) AND {after_and}"
                            else:
                                new_where_clause = f"({or_conditions}) AND {after_and}"
                            
                            # Reemplazar en el SQL
                            sql = sql[:where_match.start()] + "WHERE " + new_where_clause + sql[where_match.end():]
                            logger.warning("Corregida precedencia de operadores: agrupadas condiciones OR con paréntesis")
            
            # CORRECCIÓN DE AMBIGÜEDAD DE COLUMNAS:
            # Si el SQL selecciona 'name' sin prefijo en un JOIN de players y teams, corregirlo a 'p.name'
            if "SELECT name" in sql or "select name" in sql.lower():
                if "JOIN teams" in sql or "join teams" in sql.lower():
                    logger.warning("Detectada columna 'name' ambigua en JOIN, corrigiendo a 'p.name'...")
                    sql = re.sub(r"SELECT\s+name\b", "SELECT p.name", sql, flags=re.IGNORECASE)
                    sql = re.sub(r"select\s+name\b", "SELECT p.name", sql, flags=re.IGNORECASE)
            
            # CORRECCIÓN DE ROSTER QUERIES:
            # Si la consulta es de tipo roster (solo selecciona p.name) y usa ps.season sin JOIN, corregir a p.season
            # Patrón: SELECT p.name ... JOIN teams ... WHERE ... ps.season (sin JOIN con player_season_stats)
            is_roster_query = (
                re.search(r"SELECT\s+p\.name\s+AS\s+Jugador", sql, re.IGNORECASE) or
                (re.search(r"SELECT\s+p\.name", sql, re.IGNORECASE) and "JOIN teams" in sql)
            )
            if is_roster_query:
                # Corregir ps.season a p.season si no hay JOIN con player_season_stats
                if "ps.season" in sql.lower() and "player_season_stats" not in sql.lower():
                    logger.warning("Detectado uso incorrecto de ps.season en roster query, corrigiendo a p.season...")
                    sql = re.sub(r"\bps\.season\b", "p.season", sql, flags=re.IGNORECASE)
                # Remover cualquier referencia a ps.* si no hay JOIN con player_season_stats
                if "ps\." in sql.lower() and "player_season_stats" not in sql.lower():
                    logger.warning("Removiendo referencias a ps.* sin JOIN correspondiente...")
                    sql = re.sub(r"\bps\.\w+\b", "", sql, flags=re.IGNORECASE)
                    # Limpiar WHERE/AND duplicados que puedan quedar
                    sql = re.sub(r"\s+AND\s+AND", " AND", sql, flags=re.IGNORECASE)
                    sql = re.sub(r"\s+WHERE\s+AND", " WHERE", sql, flags=re.IGNORECASE)
                
                # MEJORAR BÚSQUEDA DE EQUIPOS CON MÚLTIPLES PALABRAS
                # Si la búsqueda usa un nombre completo con múltiples palabras, hacerla más flexible
                # Ejemplo: '%Hapoel Tel Aviv%' -> ('%Hapoel%' OR '%Tel Aviv%')
                # Buscar patrones: t.name ILIKE '%texto%' o t.name ILIKE '%texto texto%'
                team_name_patterns = [
                    r"t\.name\s+ILIKE\s+'%([^%]+)%'",  # Patrón estándar
                    r"t\.name\s+ILIKE\s+\"%([^\"]+)\"",  # Con comillas dobles
                    r"t\.name\s+ILIKE\s+'([^']+)'",  # Sin % (menos común)
                ]
                
                for pattern in team_name_patterns:
                    team_name_match = re.search(pattern, sql, re.IGNORECASE)
                    if team_name_match:
                        team_name = team_name_match.group(1)
                        # Si el nombre tiene 2+ palabras, crear búsqueda OR con palabras clave
                        words = team_name.strip().split()
                        if len(words) >= 2:
                            # Extraer palabras significativas (más de 2 caracteres, excluir artículos comunes)
                            articles = {'el', 'la', 'de', 'del', 'los', 'las', 'the', 'of'}
                            significant_words = [w for w in words if len(w) > 2 and w.lower() not in articles]
                            
                            if len(significant_words) >= 2:
                                # CRÍTICO: Usar AND en lugar de OR para evitar mezclar equipos
                                # Ejemplo: "Hapoel Tel Aviv" -> (t.name ILIKE '%Hapoel%' AND t.name ILIKE '%Tel Aviv%')
                                # Esto evita que "Tel Aviv" coincida con "Maccabi Tel Aviv"
                                # Pero si solo hay una palabra muy común (como "Tel Aviv"), usar solo la palabra única más específica
                                
                                # Identificar la palabra más específica (generalmente la primera, como "Hapoel" o "Maccabi")
                                first_word = significant_words[0]
                                other_words = significant_words[1:]
                                
                                # Si la primera palabra es muy específica (más de 4 caracteres o es un nombre propio conocido)
                                # y hay otras palabras, usar AND para que todas deban estar presentes
                                if len(first_word) > 4 or first_word.lower() in ['hapoel', 'maccabi', 'panathinaikos', 'olympiacos', 'fenerbahce']:
                                    # Usar AND: todas las palabras deben estar presentes
                                    and_conditions = " AND ".join([f"t.name ILIKE '%{word}%'" for word in significant_words])
                                    original_match = team_name_match.group(0)
                                    sql = sql.replace(original_match, f"({and_conditions})")
                                    logger.info(f"Mejorada búsqueda de equipo (AND): '{team_name}' -> todas las palabras: {significant_words}")
                                else:
                                    # Si la primera palabra no es muy específica, usar solo la primera palabra (más específica)
                                    # para evitar matches incorrectos
                                    original_match = team_name_match.group(0)
                                    sql = sql.replace(original_match, f"t.name ILIKE '%{first_word}%'")
                                    logger.info(f"Simplificada búsqueda de equipo: '{team_name}' -> solo '{first_word}' (evitar matches incorrectos)")
                                break  # Solo aplicar una vez
                            elif len(significant_words) == 1:
                                # Si solo hay una palabra significativa, usar solo esa
                                word = significant_words[0]
                                original_match = team_name_match.group(0)
                                sql = sql.replace(original_match, f"t.name ILIKE '%{word}%'")
                                logger.info(f"Simplificada búsqueda de equipo: '{team_name}' -> '{word}'")
                                break

            logger.info(f"SQL generado exitosamente: {sql}")
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

