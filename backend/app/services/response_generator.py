import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI  # type: ignore

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"  # Fast and cost-effective

class ResponseGeneratorService:
    """
    Service to generate natural language responses based on data retrieved from the database.
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        self.model = OPENROUTER_MODEL

    def _filter_season_column_if_not_needed(
        self, 
        data: List[Dict[str, Any]], 
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra la columna de temporada si solo hay una temporada y la consulta no la menciona.
        
        Args:
            data: Lista de diccionarios con datos
            query: Consulta del usuario
            
        Returns:
            Lista de diccionarios con columna de temporada filtrada si aplica
        """
        if not data:
            return data
        
        # Buscar columnas relacionadas con temporada
        headers = list(data[0].keys())
        season_columns = [
            h for h in headers 
            if 'season' in h.lower() or 'temporada' in h.lower()
        ]
        
        if not season_columns:
            return data
        
        # Verificar si hay múltiples temporadas
        season_col = season_columns[0]
        unique_seasons = set()
        for row in data:
            season_value = row.get(season_col)
            if season_value is not None:
                unique_seasons.add(str(season_value).strip())
        
        # Si hay múltiples temporadas, mantener la columna
        if len(unique_seasons) > 1:
            return data
        
        # Si la consulta menciona temporada, mantener la columna
        if self._query_mentions_season(query):
            return data
        
        # Si solo hay una temporada y la consulta no la menciona, filtrar la columna
        filtered_data = []
        for row in data:
            filtered_row = {k: v for k, v in row.items() if k not in season_columns}
            filtered_data.append(filtered_row)
        
        logger.info(f"Columna de temporada '{season_col}' filtrada (una sola temporada, consulta no la menciona)")
        return filtered_data

    def _format_data_for_prompt(self, data: List[Dict[str, Any]]) -> str:
        """
        Formats data list into a compact CSV-like string to save tokens and improve clarity.
        """
        if not data:
            return "No data found."
        
        # Get headers from first item
        headers = list(data[0].keys())
        
        # Create CSV header
        csv_lines = [", ".join(headers)]
        
        # Add rows
        for item in data:
            values = [str(item.get(h, "")) for h in headers]
            csv_lines.append(", ".join(values))
            
        return "\n".join(csv_lines)
    
    def _generate_markdown_table(self, data: List[Dict[str, Any]]) -> str:
        """
        Genera una tabla markdown a partir de una lista de diccionarios.
        
        Args:
            data: Lista de diccionarios con datos
            
        Returns:
            String con tabla markdown formateada
        """
        if not data:
            return ""
        
        headers = list(data[0].keys())
        
        # Crear header de tabla
        table_lines = []
        table_lines.append("| " + " | ".join(headers) + " |")
        table_lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Agregar filas
        for item in data:
            values = [str(item.get(h, "")) for h in headers]
            table_lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(table_lines)

    def _detect_redundant_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Detecta columnas que tienen el mismo valor en todas las filas.
        
        Args:
            data: Lista de diccionarios con datos
            
        Returns:
            Lista de nombres de columnas redundantes
        """
        if not data or len(data) < 2:
            return []
        
        redundant_columns = []
        headers = list(data[0].keys())
        
        for header in headers:
            # Obtener el primer valor como referencia
            first_value = data[0].get(header)
            
            # Verificar si todos los valores son iguales
            all_same = all(
                item.get(header) == first_value 
                for item in data[1:]
            )
            
            if all_same:
                redundant_columns.append(header)
        
        return redundant_columns

    @staticmethod
    def _is_numeric_value(value: Any) -> bool:
        """Devuelve True si el valor puede convertirse a float."""
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    def _detect_player_column(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Intenta encontrar la columna que contiene el nombre del jugador.
        """
        if not data:
            return None
        
        headers = list(data[0].keys())
        player_hints = ["player", "jugador", "name", "nombre"]
        for header in headers:
            lowered = header.lower()
            if any(hint in lowered for hint in player_hints):
                return header
        
        # Fallback a la primera columna si no hay coincidencias claras
        return headers[0] if headers else None

    def _detect_stat_column(self, query: str, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Deduce la columna de estadística relevante a partir de la consulta y las columnas disponibles.
        """
        if not data:
            return None
        
        headers = list(data[0].keys())
        query_lower = query.lower()
        
        stat_mappings = {
            "asistencias": ["assist", "asist"],
            "asistencia": ["assist", "asist"],
            "asistente": ["assist", "asist"],
            "puntos": ["point", "punto", "pts"],
            "rebotes": ["rebound", "rebote"],
            "rebote": ["rebound", "rebote"],
            "triples": ["three", "triple"],
            "valoracion": ["pir", "valora"],
            "valoración": ["pir", "valora"],
            "partidos": ["games", "game", "partido"],
        }
        
        for keyword, candidates in stat_mappings.items():
            if keyword in query_lower:
                for candidate in candidates:
                    for header in headers:
                        if candidate in header.lower():
                            return header
        
        # Fallback: primera columna numérica que no sea identificador ni nombre
        for header in headers:
            lowered = header.lower()
            if any(skip in lowered for skip in ["id", "player", "jugador", "name", "nombre"]):
                continue
            values = [row.get(header) for row in data if row.get(header) is not None]
            if values and all(self._is_numeric_value(v) for v in values):
                return header
        
        return None

    def _build_maximum_disambiguation(
        self,
        query: str,
        data: List[Dict[str, Any]],
        stat_column: Optional[str],
        player_column: Optional[str],
    ) -> str:
        """
        Genera instrucciones para no intercambiar valores cuando el usuario pide comparar con el máximo/top.
        """
        if not data or not stat_column or not player_column:
            return ""
        
        query_lower = query.lower()
        if "compara" not in query_lower:
            return ""
        
        if not any(keyword in query_lower for keyword in ["maximo", "máximo", "mejor", "top"]):
            return ""
        
        def safe_number(row: Dict[str, Any]) -> float:
            try:
                return float(row.get(stat_column, float("-inf")) or float("-inf"))
            except (TypeError, ValueError):
                return float("-inf")
        
        sorted_rows = sorted(data, key=safe_number, reverse=True)
        leader_row = sorted_rows[0]
        leader_name = leader_row.get(player_column, "el lider")
        leader_value = leader_row.get(stat_column, "N/A")
        
        pairings = []
        for row in data:
            player_name = row.get(player_column, "Jugador")
            stat_value = row.get(stat_column, "N/A")
            pairings.append(f"{player_name}: {stat_value}")
        
        return f"""
- **CRITICAL - VALIDA QUIEN ES EL LIDER EN {stat_column}:**
  - Segun los datos, el lider es {leader_name} con {leader_value}.
  - Usa exactamente estos pares jugador->valor: {", ".join(pairings)}.
  - DEBES mencionar explícitamente los valores de cada jugador según esos pares (incluye al jugador mencionado y al líder).
  - Si el jugador mencionado no es el lider, aclara que el maximo es {leader_name} y compara sus numeros sin intercambiarlos.
  - No asignes {leader_value} a otro jugador ni supongas que el mencionado es el maximo si los datos dicen lo contrario.
"""

    @staticmethod
    def _friendly_stat_name(stat_column: str) -> str:
        """Devuelve un nombre legible para la estadística."""
        lc = stat_column.lower()
        if "assist" in lc or "asist" in lc:
            return "asistencias"
        if "rebound" in lc or "rebote" in lc:
            return "rebotes"
        if "point" in lc or "punto" in lc:
            return "puntos"
        if "three" in lc or "triple" in lc:
            return "triples"
        if "pir" in lc or "valor" in lc:
            return "valoración"
        return stat_column

    def _is_current_season(self, season: Optional[str]) -> bool:
        """
        Detecta si la temporada es la actual (2025/2026 o E2025).
        
        Args:
            season: Valor de temporada (formato YYYY/YYYY+1 o EYYYY)
            
        Returns:
            True si es la temporada actual, False en caso contrario
        """
        if not season:
            return False
        
        season_str = str(season).strip()
        # Formato YYYY/YYYY+1 (ej: "2025/2026")
        if '/' in season_str:
            try:
                year = int(season_str.split('/')[0])
                return year == 2025
            except ValueError:
                return False
        # Formato EYYYY (ej: "E2025")
        elif season_str.upper().startswith('E'):
            try:
                year = int(season_str[1:])
                return year == 2025
            except ValueError:
                return False
        # Formato YYYY (ej: "2025")
        else:
            try:
                year = int(season_str)
                return year == 2025
            except ValueError:
                return False
    
    def _query_mentions_season(self, query: str) -> bool:
        """
        Detecta si la consulta menciona algo sobre temporada.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si la consulta menciona temporada, False en caso contrario
        """
        query_lower = query.lower()
        season_keywords = [
            'temporada', 'season', 'año', 'year', 
            '2022', '2023', '2024', '2025', '2026',
            'e2022', 'e2023', 'e2024', 'e2025', 'e2026',
            'esta temporada', 'la temporada', 'temporada pasada',
            'current season', 'last season'
        ]
        
        return any(keyword in query_lower for keyword in season_keywords)

    def _extract_season_from_data(self, data: List[Dict[str, Any]], query: Optional[str] = None) -> Optional[str]:
        """
        Extrae el valor de temporada de los datos si existe una columna de temporada.
        
        Si hay múltiples temporadas:
        - Si el usuario menciona una temporada específica, retorna todas las temporadas presentes
        - Si el usuario NO menciona temporada, retorna solo la más reciente (actual)
        
        Args:
            data: Lista de diccionarios con datos
            query: Consulta del usuario (opcional, para detectar si menciona temporada)
            
        Returns:
            Valor de temporada encontrado (ya formateado como YYYY/YYYY+1) o None.
            Si hay múltiples temporadas y el usuario no especifica, retorna solo la más reciente.
        """
        if not data:
            return None
        
        # Buscar columnas relacionadas con temporada
        headers = list(data[0].keys())
        season_columns = [h for h in headers 
                         if 'season' in h.lower() or 'temporada' in h.lower()]
        
        if not season_columns:
            return None
        
        # Obtener la primera columna de temporada encontrada
        season_col = season_columns[0]
        
        # Extraer TODAS las temporadas únicas de los datos
        unique_seasons = set()
        for row in data:
            season_value = row.get(season_col)
            if season_value is not None:
                season_str = str(season_value).strip()
                # Si ya está en formato YYYY/YYYY+1, agregarlo
                if '/' in season_str:
                    unique_seasons.add(season_str)
                else:
                    # Intentar formatearlo si no está formateado
                    unique_seasons.add(season_str)
        
        if not unique_seasons:
            return None
        
        # Si hay una sola temporada, retornarla
        if len(unique_seasons) == 1:
            return list(unique_seasons)[0]
        
        # Si hay múltiples temporadas, verificar si el usuario mencionó una temporada específica
        user_mentioned_season = self._query_mentions_season(query) if query else False
        
        if user_mentioned_season:
            # Usuario mencionó temporada: retornar todas las temporadas presentes
            sorted_seasons = sorted(unique_seasons)
            return ", ".join(sorted_seasons)
        else:
            # Usuario NO mencionó temporada: retornar solo la más reciente (actual)
            # Asumir que la temporada más reciente es la que tiene el año más alto
            # Formato esperado: "2025/2026", "2024/2025", etc.
            def extract_year(season_str: str) -> int:
                """Extrae el año inicial de una temporada (ej: '2025/2026' -> 2025)"""
                if '/' in season_str:
                    try:
                        return int(season_str.split('/')[0])
                    except ValueError:
                        return 0
                return 0
            
            # Encontrar la temporada con el año más alto
            latest_season = max(unique_seasons, key=extract_year)
            logger.info(f"Múltiples temporadas encontradas ({len(unique_seasons)}), usuario no especificó. Usando temporada actual: {latest_season}")
            return latest_season

    @staticmethod
    def _extract_season_from_sql(sql: Optional[str]) -> Optional[str]:
        """
        Intenta extraer la temporada del SQL si está en un WHERE clause.
        
        Busca patrones como: ps.season = 'E2025' o season = 'E2025'
        
        Args:
            sql: Query SQL (puede ser None)
            
        Returns:
            Temporada formateada como YYYY/YYYY+1 o None
        """
        if not sql:
            return None
        
        import re
        
        # Buscar patrones como: season = 'E2025' o ps.season = 'E2025'
        # Case insensitive
        patterns = [
            r"season\s*=\s*['\"]?E?(\d{4})['\"]?",
            r"season\s*=\s*['\"]?(\d{4})['\"]?",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql, re.IGNORECASE)
            for match in matches:
                year_str = match.group(1)
                try:
                    year = int(year_str)
                    if 1900 <= year <= 2100:
                        return f"{year}/{year + 1}"
                except ValueError:
                    continue
        
        return None

    async def generate_response(
        self,
        query: str,
        data: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        sql: Optional[str] = None,
    ) -> str:
        """
        Generates a natural language response based on the query and the data retrieved.
        
        Args:
            query: User's natural language query.
            data: List of dictionaries containing the retrieved data.
            conversation_history: Previous conversation history.
            
        Returns:
            A string containing the natural language response in Markdown format.
        """
        try:
            # We assume up to 60 records is manageable for the prompt
            limited_data = data[:60]
            record_count = len(data)
            
            # Filtrar columna de temporada si solo hay una y la consulta no la menciona
            limited_data = self._filter_season_column_if_not_needed(limited_data, query)
            
            # Convert to CSV format string
            data_str = self._format_data_for_prompt(limited_data)
            
            # Construir system prompt basado en si hay datos o no
            if record_count == 0:
                system_prompt = """You are an expert Euroleague basketball analyst and assistant.
                Your task is to respond in Spanish when NO DATA is found.
                
                **CRITICAL RULES WHEN NO DATA:**
                - You MUST respond that NO DATA was found for the requested query.
                - DO NOT invent or mention data from other seasons or years.
                - DO NOT reference previous conversation history when stating there's no data.
                - Simply state: "No se encontraron datos para la consulta solicitada."
                - Be brief and direct. Do NOT add explanations about other seasons or speculate.
                """
            else:
                # Detectar columnas redundantes (mismo valor en todas las filas) después del filtrado
                redundant_columns = self._detect_redundant_columns(limited_data)
                
                # Detectar si la consulta menciona temporada
                query_mentions_season = self._query_mentions_season(query)
                
                # Extraer temporada de los datos (si existe)
                # Pasar la query para que la función pueda decidir si usar todas las temporadas o solo la actual
                season_from_data = self._extract_season_from_data(limited_data, query)
                
                # Detectar columnas clave para desambiguar líderes
                player_column = self._detect_player_column(limited_data)
                stat_column = self._detect_stat_column(query, limited_data)
                maximum_context = self._build_maximum_disambiguation(query, limited_data, stat_column, player_column)
                
                # Si no hay temporada en los datos, intentar extraerla del SQL
                if not season_from_data and sql:
                    season_from_sql = self._extract_season_from_sql(sql)
                    if season_from_sql:
                        season_from_data = season_from_sql
                        logger.info(f"Temporada extraída del SQL: {season_from_data}")
                
                # Detectar si es una respuesta simple basada en número de filas y columnas
                # Reglas:
                # - 1 fila y ≤3 columnas → texto
                # - 2 filas y ≤2 columnas → texto
                # - Resto → tabla
                # IMPORTANTE: Usar limited_data (ya filtrado) para contar columnas correctamente
                num_columns = len(limited_data[0].keys()) if limited_data else 0
                
                # Detectar si parece ser sobre jugadores (tiene columna de nombre de jugador)
                has_player_column = any(
                    col.lower() in ['jugador', 'player', 'name', 'nombre'] 
                    for col in (data[0].keys() if data else [])
                )
                
                # Determinar si es respuesta simple (texto)
                is_simple_response = (
                    (record_count == 1 and num_columns <= 3) or
                    (record_count == 2 and num_columns <= 2)
                )
                query_lower_for_max = query.lower()
                is_maximum_request = ("compara" in query_lower_for_max) and any(
                    keyword in query_lower_for_max for keyword in ["máximo", "maximo", "mejor", "top"]
                )
                
                if is_simple_response:
                    # Respuesta determinista para una sola fila con jugador y stat
                    if record_count == 1 and player_column and stat_column:
                        row = limited_data[0]
                        player_name = row.get(player_column, "Jugador")
                        stat_value = row.get(stat_column, "N/A")
                        stat_label = self._friendly_stat_name(stat_column)
                        season_snippet = ""
                        if season_from_data:
                            season_snippet = f" en la temporada {season_from_data}"
                        return (
                            f"**{player_name}** registra **{stat_value} {stat_label}**{season_snippet}. "
                            f"Es el valor solicitado para {stat_label}."
                        )
                    
                    # Respuesta determinista para comparaciones máximo/top con 2 filas y 1-2 columnas
                    if (
                        record_count == 2
                        and stat_column
                        and player_column
                        and is_maximum_request
                    ):
                        # Ordenar por la estadística para identificar líder y retador
                        def safe_stat(row: Dict[str, Any]) -> float:
                            try:
                                return float(row.get(stat_column, float("-inf")) or float("-inf"))
                            except (TypeError, ValueError):
                                return float("-inf")
                        
                        ordered = sorted(limited_data, key=safe_stat, reverse=True)
                        leader = ordered[0]
                        challenger = ordered[1] if len(ordered) > 1 else ordered[0]
                        leader_name = leader.get(player_column, "Líder")
                        leader_value = leader.get(stat_column, "N/A")
                        challenger_name = challenger.get(player_column, "Jugador")
                        challenger_value = challenger.get(stat_column, "N/A")
                        stat_label = self._friendly_stat_name(stat_column)
                        
                        season_snippet = ""
                        if season_from_data:
                            season_snippet = f" en la temporada {season_from_data}"
                        
                        return (
                            f"**{leader_name}** lidera la liga con **{leader_value} {stat_label}**{season_snippet}, "
                            f"mientras que **{challenger_name}** registra **{challenger_value} {stat_label}**. "
                            f"Ambos muestran solidez en {stat_label}, pero el liderato es de {leader_name}."
                        )
                    
                    # Construir instrucción de temporada explícita
                    season_instruction = ""
                    if season_from_data:
                        # Detectar si hay múltiples temporadas (separadas por comas)
                        if "," in season_from_data:
                            # Usuario mencionó temporada específica: mostrar todas
                            seasons_list = [s.strip() for s in season_from_data.split(",")]
                            season_instruction = f"""
                    - **CRITICAL - MULTIPLE SEASONS IN DATA:** The data contains MULTIPLE seasons: {season_from_data}.
                      You MUST mention ALL seasons present in the data when describing the results.
                      DO NOT invent or use any other season (like "2022/2023" or any other year not in the data).
                      The seasons in the data are: {', '.join(seasons_list)}.
                      If you mention seasons, you MUST use ONLY these exact season formats from the data.
                    """
                        else:
                            # Una sola temporada (puede ser la actual si había múltiples pero usuario no especificó)
                            is_current = self._is_current_season(season_from_data)
                            if is_current:
                                season_instruction = f"""
                    - **ABSOLUTELY CRITICAL - CURRENT SEASON (2025/2026):** The data corresponds to the CURRENT/ONGOING season **{season_from_data}**.
                      
                      **MANDATORY VERB TENSE RULES - NO EXCEPTIONS:**
                      - You MUST use PRESENT TENSE verbs: "acumula", "lleva", "tiene", "muestra", "demuestra", "es", "está".
                      - You MUST use PRESENT CONTINUOUS when describing ongoing actions: "está teniendo", "está demostrando", "está siendo".
                      - **FORBIDDEN - DO NOT USE:** "ha tenido", "ha sido", "ha demostrado", "tuvo", "anotó", "consiguió", "fue", "demostró".
                      - **FORBIDDEN - DO NOT USE:** Past perfect ("ha tenido un desempeño") - Use present instead ("tiene un desempeño" or "está teniendo un desempeño").
                      
                      **CORRECT EXAMPLES (CURRENT SEASON):**
                      - "**Okeke** acumula 10.0 asistencias" (NOT "ha tenido" or "tuvo")
                      - "**Hezonja** acumula 23.0 asistencias" (NOT "ha tenido" or "tuvo")
                      - "**Campazzo** está teniendo un desempeño impresionante" (NOT "ha tenido")
                      - "**demuestra** ser un excelente organizador" (NOT "ha demostrado")
                      
                      **WRONG EXAMPLES (DO NOT USE THESE):**
                      - ❌ "ha tenido un desempeño impresionante" → ✅ "está teniendo un desempeño impresionante"
                      - ❌ "ha demostrado ser" → ✅ "demuestra ser"
                      - ❌ "ha sido una amenaza" → ✅ "es una amenaza"
                      
                      You MUST use this exact season format in your response: **{season_from_data}**.
                      DO NOT invent or use any other season (like "2022/2023" or any other year).
                      If you mention the season, you MUST write: "{season_from_data}".
                    """
                            else:
                                season_instruction = f"""
                    - **CRITICAL - SEASON INFORMATION:** The data corresponds to season **{season_from_data}** (PAST season).
                      **VERB TENSE RULE:** Since this is a PAST season, you can use PAST TENSE.
                      - Use verbs like: "tuvo", "anotó", "consiguió", "jugó" (appropriate for past seasons).
                      You MUST use this exact season format in your response: **{season_from_data}**.
                      DO NOT invent or use any other season (like "2022/2023" or any other year).
                      If you mention the season, you MUST write: "{season_from_data}".
                    """
                    else:
                        season_instruction = """
                    - **CRITICAL - NO SEASON IN DATA:** The data provided does NOT contain season information.
                      DO NOT invent or mention any specific season (like "2022/2023", "2025/2026", etc.) unless it is explicitly mentioned in the user's query.
                      If the user's query does not mention a season, you can simply omit season references or use generic terms like "esta temporada" if appropriate.
                      NEVER make up season years.
                    """
                    
                    # Respuesta simple: usar formato destacado (negrita)
                    system_prompt = f"""You are an expert Euroleague basketball analyst and assistant.
                    Your task is to provide a natural, conversational answer in Spanish to the user's question, based STRICTLY on the provided data.
                    
                    DATA CONTEXT (CSV format):
                    - Records found: {record_count}
                    - Data content:
                    {data_str}
                    
                    GUIDELINES FOR SIMPLE RESPONSES:
                    - Respond in Spanish, naturally and conversationally (like a friendly sports commentator).
                    
                    **🚨🚨🚨 ABSOLUTELY MANDATORY - VERB VARIATION RULE (CHECK THIS FIRST BEFORE WRITING):**
                    When mentioning MULTIPLE players/stats in the SAME sentence, you MUST ALWAYS use DIFFERENT verbs. This is NON-NEGOTIABLE and MUST be checked before every response.
                    
                    ❌ **WRONG (FORBIDDEN - NEVER DO THIS):**
                    - "Okeke acumula 10.0 asistencias y Hezonja acumula 23.0 asistencias" ← SAME verb "acumula" twice - THIS IS WRONG
                    - "Larkin acumula 150 puntos y Micic acumula 140 puntos" ← SAME verb "acumula" twice - THIS IS WRONG
                    
                    ✅ **CORRECT (MANDATORY - ALWAYS DO THIS):**
                    - "Okeke acumula 10.0 asistencias mientras que Hezonja lleva 23.0 asistencias" ← DIFFERENT verbs
                    - "Okeke registra 10.0 asistencias y Hezonja acumula 23.0 asistencias" ← DIFFERENT verbs
                    - "Okeke tiene 10.0 asistencias y Hezonja lleva 23.0 asistencias" ← DIFFERENT verbs
                    - "Larkin acumula 150 puntos mientras que Micic registra 140 puntos" ← DIFFERENT verbs
                    - "Larkin lleva 150 puntos y Micic acumula 140 puntos" ← DIFFERENT verbs
                    
                    **Available verbs to vary:** "acumula", "lleva", "registra", "tiene", "muestra", "presenta"
                    **CRITICAL:** Before writing your response, CHECK that you are using DIFFERENT verbs for each player. If you see the same verb twice, CHANGE IT IMMEDIATELY.
                    **NEVER repeat the same verb twice in the same sentence when comparing players. ALWAYS vary them.**
                    - **CRITICAL:** Be conversational and engaging, not robotic or dry. Add a brief, natural comment or context when appropriate.
                      - For single player queries: Add a brief comment about the stat (e.g., "una buena cifra", "un rendimiento sólido", etc.) if it makes sense.
                      - For comparisons: Add a brief comparison or observation.
                      - Keep it natural - don't force comments if they don't fit naturally.
                    - **CRITICAL:** Present the answer in a clear, conversational format using **bold** to highlight key information.{season_instruction}
                    {maximum_context}
                    - **ABSOLUTELY FORBIDDEN - NO TABLES:** This is a SIMPLE response ({record_count} row(s), {num_columns} column(s)). 
                      You MUST respond ONLY in plain text format (no tables). 
                      DO NOT create Markdown tables (no | characters, no table headers, no table rows).
                      DO NOT use table formatting of any kind.
                      DO NOT include any table structure in your response.
                      Write 2-4 sentences in natural, conversational language (not just one dry sentence).
                    - Example formats (CORRECT - for CURRENT season 2025/2026):
                      * Single player, single stat:
                        "**Alberto Abalde** acumula **54.0 puntos** en la temporada **2025/2026**. Es una cifra que muestra su contribución ofensiva en esta campaña."
                        "**Larkin** lleva **150 puntos** anotados en la temporada **2025/2026**, lo que refleja su capacidad anotadora."
                      * Single player, multiple stats:
                        "**Tavares** ha anotado **118 puntos** y ha jugado **14 partidos** en la temporada **2025/2026**. Un rendimiento sólido para el pívot."
                      * Two players comparison (CRITICAL - VARY VERBS to avoid repetition):
                        "**Okeke** acumula **10.0 asistencias** mientras que **Hezonja** lleva **23.0 asistencias** en la temporada **2025/2026**. Hezonja tiene una ventaja considerable en esta faceta del juego."
                        "**Okeke** registra **10.0 asistencias** y **Hezonja** acumula **23.0 asistencias** en la temporada **2025/2026**. Hezonja muestra una ventaja considerable en esta faceta del juego."
                        "**Larkin** acumula **150 puntos** mientras que **Micic** registra **140 puntos** en la temporada **2025/2026**. Ambos están teniendo una gran temporada ofensiva."
                        "**Larkin** lleva **150 puntos** y **Micic** acumula **140 puntos** en la temporada **2025/2026**. Ambos están teniendo una gran temporada ofensiva."
                      * Team/position queries:
                        "**Oturu** juega en **Real Madrid** esta temporada."
                      **IMPORTANT - VERB VARIATION:** When comparing multiple players, use different verbs to avoid repetition:
                        - Use: "acumula", "lleva", "registra", "tiene", "muestra" (vary them naturally)
                        - Avoid: Repeating the same verb twice in the same sentence (e.g., "acumula... y acumula" → use "acumula... y lleva" or "registra... y acumula")
                    - Use **bold** for player names, team names, numbers/statistics, and season information.
                    - Do NOT mention "SQL", "database", "query", or "JSON". Act naturally like a sports commentator.
                    - **IMPORTANT:** Don't be overly verbose, but also don't be too dry. Find a natural balance (2-4 sentences is ideal).
                    """
                else:
                    # Extraer temporada ANTES de construir instrucciones para usarla en ejemplos
                    # Construir instrucción de temporada explícita
                    season_instruction = ""
                    if season_from_data:
                        # Detectar si hay múltiples temporadas (separadas por comas)
                        if "," in season_from_data:
                            # Usuario mencionó temporada específica: mostrar todas
                            seasons_list = [s.strip() for s in season_from_data.split(",")]
                            season_instruction = f"""
                    - **CRITICAL - MULTIPLE SEASONS IN DATA:** The data contains MULTIPLE seasons: {season_from_data}.
                      You MUST mention ALL seasons present in the data when describing the results.
                      DO NOT invent or use any other season (like "2022/2023" or any other year not in the data).
                      The seasons in the data are: {', '.join(seasons_list)}.
                      If you mention seasons, you MUST use ONLY these exact season formats from the data.
                    """
                        else:
                            # Una sola temporada (puede ser la actual si había múltiples pero usuario no especificó)
                            is_current = self._is_current_season(season_from_data)
                            if is_current:
                                season_instruction = f"""
                    - **ABSOLUTELY CRITICAL - CURRENT SEASON (2025/2026):** The data corresponds to the CURRENT/ONGOING season **{season_from_data}**.
                      
                      **MANDATORY VERB TENSE RULES - NO EXCEPTIONS:**
                      - You MUST use PRESENT TENSE verbs: "acumula", "lleva", "tiene", "muestra", "demuestra", "es", "está".
                      - You MUST use PRESENT CONTINUOUS when describing ongoing actions: "está teniendo", "está demostrando", "está siendo".
                      - **FORBIDDEN - DO NOT USE:** "ha tenido", "ha sido", "ha demostrado", "ha sido", "tuvo", "anotó", "consiguió", "fue", "demostró".
                      - **FORBIDDEN - DO NOT USE:** Past perfect ("ha tenido un desempeño") - Use present instead ("tiene un desempeño" or "está teniendo un desempeño").
                      
                      **CORRECT EXAMPLES (CURRENT SEASON):**
                      - "Campazzo **acumula** 132.0 puntos" (NOT "ha tenido" or "tuvo")
                      - "**está teniendo** un desempeño impresionante" (NOT "ha tenido")
                      - "**demuestra** ser un excelente organizador" (NOT "ha demostrado")
                      - "**es** una amenaza constante" (NOT "ha sido")
                      - "**lleva** 28.0 rebotes" (NOT "ha conseguido" or "tuvo")
                      - "**muestra** consistencia" (NOT "ha mostrado")
                      
                      **WRONG EXAMPLES (DO NOT USE THESE):**
                      - ❌ "Campazzo ha tenido un desempeño impresionante" → ✅ "Campazzo está teniendo un desempeño impresionante"
                      - ❌ "ha demostrado ser un excelente organizador" → ✅ "demuestra ser un excelente organizador"
                      - ❌ "ha sido una amenaza constante" → ✅ "es una amenaza constante"
                      - ❌ "ha sido una pieza fundamental" → ✅ "es una pieza fundamental"
                      - ❌ "ha tenido una temporada sobresaliente" → ✅ "está teniendo una temporada sobresaliente"
                      
                      You MUST use this exact season format in your response: **{season_from_data}**.
                      DO NOT invent or use any other season (like "2022/2023" or any other year).
                      If you mention the season, you MUST write: "{season_from_data}".
                    """
                            else:
                                season_instruction = f"""
                    - **CRITICAL - SEASON INFORMATION:** The data corresponds to season **{season_from_data}** (PAST season).
                      **VERB TENSE RULE:** Since this is a PAST season, you can use PAST TENSE.
                      - Use verbs like: "tuvo", "anotó", "consiguió", "jugó" (appropriate for past seasons).
                      You MUST use this exact season format in your response: **{season_from_data}**.
                      DO NOT invent or use any other season (like "2022/2023" or any other year).
                      If you mention the season, you MUST write: "{season_from_data}".
                      Example: "En la Euroleague {season_from_data}, los tres máximos anotadores fueron..."
                    """
                    else:
                        season_instruction = """
                    - **CRITICAL - NO SEASON IN DATA:** The data provided does NOT contain season information.
                      DO NOT invent or mention any specific season (like "2022/2023", "2025/2026", etc.) unless it is explicitly mentioned in the user's query.
                      If the user's query does not mention a season, you can simply omit season references or use generic terms like "esta temporada" if appropriate.
                      NEVER make up season years.
                    """
                    
                    # Construir instrucciones sobre columnas redundantes (después de tener season_from_data)
                    redundant_instructions = ""
                    if redundant_columns:
                        # Filtrar columnas de temporada si la consulta no las menciona
                        season_columns = [col for col in redundant_columns 
                                        if 'season' in col.lower() or 'temporada' in col.lower()]
                        
                        if season_columns and not query_mentions_season:
                            # Usar la temporada extraída en el ejemplo si está disponible
                            season_example = season_from_data if season_from_data else "2025/2026"
                            redundant_instructions = f"""
                    - **CRITICAL - REDUNDANT COLUMNS:** The following columns have the SAME value in ALL rows and are NOT mentioned in the user's query:
                      {', '.join(season_columns)}
                      - You MUST mention this information in your narrative text (e.g., "A lo largo de la temporada {season_example}...")
                      - You MUST EXCLUDE these columns from the Markdown table - they add no value since all rows are identical.
                      - Only include columns that provide DIFFERENTIATING information between rows.
                    """
                        elif redundant_columns:
                            # Otras columnas redundantes (no temporada)
                            redundant_instructions = f"""
                    - **REDUNDANT COLUMNS:** The following columns have the SAME value in ALL rows:
                      {', '.join(redundant_columns)}
                      - If these columns are NOT mentioned in the user's query, you may EXCLUDE them from the table.
                      - If you mention this information in your narrative text, you MUST exclude it from the table.
                    """
                    
                    # Detectar si es una comparación (2 filas típicamente) o tiene múltiples columnas
                    # También detectar si la consulta menciona "compara" o "comparación"
                    query_lower = query.lower()
                    mentions_comparison = any(word in query_lower for word in ["compara", "comparacion", "comparación", "comparar", "compare"])
                    is_comparison = (record_count == 2 and num_columns >= 2) or mentions_comparison
                    
                    # Determinar si necesita tabla según las reglas:
                    # - 1 fila y ≤3 columnas → NO tabla (texto)
                    # - 2 filas y ≤2 columnas → NO tabla (texto)
                    # - Resto → SÍ tabla
                    needs_table = not (
                        (record_count == 1 and num_columns <= 3) or
                        (record_count == 2 and num_columns <= 2)
                    )
                    
                    # Detectar si es una comparación con "máximo/top" para reforzar el pareo correcto de valores
                    query_lower_for_max = query.lower()
                    is_maximum_request = ("compara" in query_lower_for_max) and any(
                        keyword in query_lower_for_max for keyword in ["máximo", "maximo", "mejor", "top"]
                    )
                    maximum_explanation = maximum_context if is_maximum_request else ""
                    is_maximum_comparison = bool(maximum_explanation)
                    
                    comparison_instruction = ""
                    if is_comparison:
                        # Detectar si es temporada actual para ajustar ejemplos de verbos
                        is_current_for_comparison = season_from_data and self._is_current_season(season_from_data)
                        
                        if is_current_for_comparison:
                            verb_examples = """
                      **CRITICAL - VERB TENSE FOR CURRENT SEASON COMPARISONS:**
                      - ✅ CORRECT: "Ambos jugadores **están teniendo** un buen rendimiento" (NOT "han tenido")
                      - ✅ CORRECT: "Larkin **destaca** por su capacidad anotadora" (present tense)
                      - ✅ CORRECT: "Satoransky **demuestra** ser un excelente pasador" (NOT "ha demostrado")
                      - ✅ CORRECT: "Satoransky **lleva** más rebotes" or "**acumula** más rebotes" (NOT "ha logrado")
                      - ✅ CORRECT: "Satoransky **ha jugado** más partidos" (acceptable for "games played")
                      - ❌ WRONG: "han tenido un buen rendimiento" → ✅ "están teniendo un buen rendimiento"
                      - ❌ WRONG: "ha demostrado ser" → ✅ "demuestra ser"
                      - ❌ WRONG: "ha logrado más rebotes" → ✅ "lleva más rebotes" or "acumula más rebotes"
                      """
                        else:
                            verb_examples = """
                      **VERB TENSE FOR PAST SEASON COMPARISONS:**
                      - You can use past tense: "tuvieron", "demostraron", "lograron", etc.
                      """
                        
                        comparison_instruction = f"""
                    - **ABSOLUTELY CRITICAL - COMPARISON QUERY DETECTED:**
                      The user asked to COMPARE data ({record_count} rows with {num_columns} columns).
                      {maximum_explanation}
                      
                      **YOU MUST FOLLOW THIS EXACT FORMAT:**
                      1. Start with a brief 1-2 sentence introduction{(" (see MAXIMUM EXPLANATION above)" if is_maximum_comparison else "")}
                      2. **IMMEDIATELY** show a Markdown Table with ALL rows
                      3. Then provide analysis/comparison text
                      
                      **THE TABLE IS MANDATORY - DO NOT SKIP IT.**{verb_examples}
                      
                      Example of CORRECT format for CURRENT season comparison:
                      "¡Claro! Vamos a comparar el desempeño de Larkin y Satoransky en la temporada 2025/2026:
                      
                      | Jugador | Puntos | Asistencias | Rebotes | Triples | Valoración | Partidos |
                      |---------|--------|-------------|---------|---------|------------|----------|
                      | LARKIN  | 174.0  | 49.0        | 27.0    | 26.0    | 172.0      | 11       |
                      | SATORANSKY | 102.0 | 62.0    | 42.0    | 21.0    | 146.0      | 14       |
                      
                      Ambos jugadores **están teniendo** un buen rendimiento en la temporada actual. Shane Larkin **destaca** por su capacidad anotadora con 174.0 puntos, mientras que Tomas Satoransky **demuestra** ser un excelente pasador con 62.0 asistencias. En cuanto a la valoración, Larkin **lidera** con 172.0 frente a los 146.0 de Satoransky. A pesar de **llevar** menos partidos disputados, Satoransky **acumula** más rebotes con 42.0, superando los 27.0 de Larkin."
                      
                      **WRONG:** Just describing numbers in paragraphs without a table.
                      **WRONG:** Using past tense for current season: "han tenido", "ha demostrado", "ha logrado"
                      **RIGHT:** Showing the table FIRST, then analysis with PRESENT TENSE for current season.
                      
                      If you do NOT include the table, your response is INCORRECT.
                    """
                    elif needs_table and not is_comparison:
                        comparison_instruction = f"""
                    - **MANDATORY TABLE:** This query returns {record_count} row(s) with {num_columns} column(s).
                      You **MUST** generate a Markdown Table containing ALL the data.
                      Do NOT just describe the data in text - show it in a structured table format.
                    """
                    
                    # Respuesta compleja: formato completo con tablas si es necesario
                    system_prompt = f"""You are an expert Euroleague basketball analyst and assistant.
                    Your task is to provide a comprehensive, engaging, and detailed answer in Spanish to the user's question, based STRICTLY on the provided data.
                    
                    DATA CONTEXT (CSV format):
                    - Total records found: {record_count}
                    - Data content:
                    {data_str}
                    
                    GUIDELINES:
                    - Respond in Spanish.
                    - **CRITICAL: DO NOT OMIT DATA.** You MUST present ALL records provided in the data above.
                    - **NEVER SUMMARIZE A LIST.** Do NOT say "Here are some highlights" or "Others include...". You must list every single player/team/stat found in the data.
                    {season_instruction}
                    {comparison_instruction}
                    - **MANDATORY TABLE RULES (NON-NEGOTIABLE):**
                      * This query returns {record_count} row(s) with {num_columns} column(s).
                      * You **MUST** generate a Markdown Table containing ALL the data rows.
                      * The table is REQUIRED - do NOT respond with only text description.
                      * Comparisons between seasons, players, or teams ALWAYS require a table - do NOT just describe in text.
                      * **FOR COMPARISONS:** The table MUST appear in your response. Text-only responses are INCORRECT.
                      
                      Example Table (for rosters):
                      | Jugador |
                      |---------|
                      | ...     |
                      | ...     |
                      (List ALL rows - NO position column, NO other columns unless explicitly in the data)

                    - **DO NOT mention or include "position" or "Posición" columns** - This data is not available.{redundant_instructions}
                    - Be narrative and detailed ("enróllate un poco") in the introduction and conclusion, analyzing the stats/squad context.
                    - **CRITICAL - CONVERSATIONAL STYLE:** Write in a natural, conversational chat style. DO NOT use formal section headers like "### Principales Anotadores..." that repeat information already in the narrative text. Instead, start directly with a conversational sentence that introduces the data naturally.
                    - **NO REDUNDANT TITLES:** If you're going to show a table or list, do NOT create a formal title that repeats what you're about to say. Just introduce it conversationally in the text.
                    - Use **bold** for key names and stats.
                    - Use > Blockquotes for key takeaways.
                    - Do NOT mention "SQL", "database", "query", or "JSON". Act like a sports commentator.
                    """

            messages = []
            messages.append({"role": "system", "content": system_prompt})
            
            if conversation_history:
                 # Filter history to keep context manageable (last 4 messages)
                messages.extend(conversation_history[-4:])

            messages.append({"role": "user", "content": query})

            logger.info(f"Generating natural response for query: '{query}' with {record_count} records")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3, # Low temperature to ensure strict adherence to "list all" instruction
                max_tokens=1500, # Increased to allow for full tables of rosters
            )
            
            content = response.choices[0].message.content.strip()
            logger.info("Natural response generated successfully")
            
            # POST-PROCESAMIENTO: Validar y corregir respuesta según tipo esperado
            # Usar datos filtrados para contar columnas correctamente (sin temporada si aplica)
            filtered_data_for_post = self._filter_season_column_if_not_needed(data[:60], query)
            query_lower = query.lower()
            mentions_comparison = any(word in query_lower for word in ["compara", "comparacion", "comparación", "comparar", "compare"])
            has_table = "|" in content and "--" in content
            num_rows = len(filtered_data_for_post)
            num_columns = len(filtered_data_for_post[0].keys()) if filtered_data_for_post else 0
            is_comparison_data = num_rows == 2 and num_columns >= 2
            
            # Detectar si es respuesta simple según las reglas actualizadas
            # Usar datos filtrados para contar correctamente (sin temporada si aplica)
            is_simple_response_post = (
                (num_rows == 1 and num_columns <= 3) or
                (num_rows == 2 and num_columns <= 2)
            )
            
            # Si es respuesta simple pero tiene tabla, removerla
            if is_simple_response_post and has_table:
                logger.warning(f"Respuesta simple ({num_rows} fila(s), {num_columns} columna(s)) contiene tabla. Removiendo tabla...")
                # Remover tabla markdown (líneas que contienen | y --)
                lines = content.split('\n')
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
                content = '\n'.join(cleaned_lines).strip()
                logger.info("Tabla removida de respuesta simple")
                
                # Verificar que se eliminó correctamente
                still_has_table = "|" in content and "--" in content
                if still_has_table:
                    logger.warning("ADVERTENCIA: La tabla no se eliminó completamente. Intentando eliminación más agresiva...")
                    # Eliminación más agresiva: remover todas las líneas con |
                    lines = content.split('\n')
                    cleaned_lines = [line for line in lines if '|' not in line]
                    content = '\n'.join(cleaned_lines).strip()
                    logger.info("Tabla eliminada con método agresivo")
            
            # POST-PROCESAMIENTO: Si es una comparación o tiene 2+ filas con múltiples columnas y no hay tabla, agregarla
            if (mentions_comparison or is_comparison_data) and not has_table and num_rows >= 2:
                logger.warning(f"Comparación detectada ({num_rows} filas, {num_columns} columnas) sin tabla en respuesta. Generando tabla automáticamente...")
                table_markdown = self._generate_markdown_table(data)
                # Insertar la tabla después de la primera oración o párrafo
                if "\n\n" in content:
                    # Si hay párrafos, insertar después del primer párrafo
                    parts = content.split("\n\n", 1)
                    content = parts[0] + "\n\n" + table_markdown + "\n\n" + parts[1] if len(parts) > 1 else parts[0] + "\n\n" + table_markdown
                else:
                    # Si no hay párrafos, insertar después de la primera oración
                    sentences = content.split(". ", 1)
                    if len(sentences) > 1:
                        content = sentences[0] + ".\n\n" + table_markdown + "\n\n" + sentences[1]
                    else:
                        content = content + "\n\n" + table_markdown
            
            return content

        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            # Fallback message
            return "⚠️ Hubo un problema generando el resumen narrativo. Aquí tienes los datos exactos obtenidos de la base de datos:"
