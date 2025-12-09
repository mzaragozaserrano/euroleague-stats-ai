import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

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
                # Detectar columnas redundantes (mismo valor en todas las filas)
                redundant_columns = self._detect_redundant_columns(limited_data)
                
                # Detectar si la consulta menciona temporada
                query_mentions_season = self._query_mentions_season(query)
                
                # Extraer temporada de los datos (si existe)
                # Pasar la query para que la función pueda decidir si usar todas las temporadas o solo la actual
                season_from_data = self._extract_season_from_data(limited_data, query)
                
                # Si no hay temporada en los datos, intentar extraerla del SQL
                if not season_from_data and sql:
                    season_from_sql = self._extract_season_from_sql(sql)
                    if season_from_sql:
                        season_from_data = season_from_sql
                        logger.info(f"Temporada extraída del SQL: {season_from_data}")
                
                # Detectar si es una respuesta simple: 1 fila y 3 columnas (o menos) -> texto
                # Todo lo demás -> tabla
                num_columns = len(data[0].keys()) if data else 0
                is_simple_response = record_count == 1 and num_columns <= 3
                
                if is_simple_response:
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
                            season_instruction = f"""
                    - **CRITICAL - SEASON INFORMATION:** The data corresponds to season **{season_from_data}**. 
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
                    Your task is to provide a brief, direct answer in Spanish to the user's simple question, based STRICTLY on the provided data.
                    
                    DATA CONTEXT (CSV format):
                    - Records found: {record_count}
                    - Data content:
                    {data_str}
                    
                    GUIDELINES FOR SIMPLE RESPONSES:
                    - Respond in Spanish, naturally and concisely.
                    - **CRITICAL:** Present the answer in a clear, conversational format using **bold** to highlight key information.{season_instruction}
                    - Example formats:
                      * "**Oturu** juega en **Real Madrid**."
                      * "**Larkin** tiene **150 puntos** en la temporada **2025/2026**."
                      * "**Micic** ha jugado **14 partidos** esta temporada."
                    - Use **bold** for player names, team names, numbers/statistics, and season information.
                    - Do NOT create tables or complex structures - just a simple, highlighted sentence or two.
                    - Do NOT mention "SQL", "database", "query", or "JSON". Act naturally.
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
                            season_instruction = f"""
                    - **CRITICAL - SEASON INFORMATION:** The data corresponds to season **{season_from_data}**. 
                      You MUST use this exact season format in your response: **{season_from_data}**.
                      DO NOT invent or use any other season (like "2022/2023" or any other year).
                      If you mention the season, you MUST write: "{season_from_data}".
                      Example: "En la Euroleague {season_from_data}, los tres máximos anotadores..."
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
                    needs_table = record_count >= 2 or (record_count == 1 and num_columns >= 2)
                    
                    comparison_instruction = ""
                    if is_comparison:
                        comparison_instruction = f"""
                    - **ABSOLUTELY CRITICAL - COMPARISON QUERY DETECTED:**
                      The user asked to COMPARE data ({record_count} rows with {num_columns} columns).
                      
                      **YOU MUST FOLLOW THIS EXACT FORMAT:**
                      1. Start with a brief 1-2 sentence introduction
                      2. **IMMEDIATELY** show a Markdown Table with ALL rows
                      3. Then provide analysis/comparison text
                      
                      **THE TABLE IS MANDATORY - DO NOT SKIP IT.**
                      
                      Example of CORRECT format:
                      "Aquí está la comparación de las temporadas de Llull:
                      
                      | Temporada | Puntos | Asistencias | Rebotes | Triples | Valoracion | Partidos |
                      |-----------|--------|-------------|---------|---------|------------|----------|
                      | 2022/2023 | 178.0  | 69.0        | 35.0    | 32.0    | 147.0      | 29       |
                      | 2025/2026 | 39.0   | 12.0        | 11.0    | 6.0     | 21.0       | 13       |
                      
                      [Then your analysis text...]"
                      
                      **WRONG:** Just describing numbers in paragraphs without a table.
                      **RIGHT:** Showing the table FIRST, then analysis.
                      
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
                    - **NEVER SUMMARIZE A LIST.** Do NOT say "Here are some highlights" or "Others include...". You must list every single player/team/stat found in the data.{season_instruction}{comparison_instruction}
                    - **MANDATORY TABLE RULES (NON-NEGOTIABLE):**
                      * If the data contains 2+ rows with 2+ columns, you **MUST** generate a Markdown Table containing ALL the rows.
                      * If the data contains 3+ records (any number of columns), you **MUST** generate a Markdown Table.
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
            
            # POST-PROCESAMIENTO: Si es una comparación o tiene 2+ filas con múltiples columnas y no hay tabla, agregarla
            query_lower = query.lower()
            mentions_comparison = any(word in query_lower for word in ["compara", "comparacion", "comparación", "comparar", "compare"])
            has_table = "|" in content and "--" in content
            num_rows = len(data)
            num_columns = len(data[0].keys()) if data else 0
            is_comparison_data = num_rows == 2 and num_columns >= 2
            
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
            return "Aquí tienes los resultados encontrados en la base de datos:"
