# Flujo de Consultas - Arquitectura Actual

## Resumen

El sistema usa una arquitectura **ETL + Backend-Centric con RAG**:

```
API Euroleague (GitHub) --[ETL 8 AM UTC - Solo 2025]--> Backend BD (Neon)
                                                                    ↑
Frontend (User Chat) --[POST /api/chat]--> Backend API
    ↓                                              ↓
localStorage (con backup)             1. Corrección (OpenAI via OpenRouter)
                                      2. RAG (OpenAI embeddings)
                                      3. SQL Gen (OpenRouter)
                                      4. Ejecución SQL
                                      5. Retorno JSON
```

## Tipos de Consultas Soportadas

### ✅ Soportadas: Estadísticas Agregadas por Temporada

**Ejemplos:**
- "Top 10 anotadores de esta temporada"
- "Mejores reboteadores del Real Madrid"
- "Máximo asistente"

**Flujo:**
1. Frontend envía query al backend: `POST /api/chat`
2. **Corrección de consulta (OpenAI)**: Corrige erratas tipográficas (ej: "Campazo" → "Campazzo")
3. **RAG (Retrieval)**: Genera embedding de query, busca esquema relevante en `schema_embeddings`
4. Backend detecta que es consulta de stats
5. Backend extrae parámetros (temporada, estadística, top N, equipo)
6. Backend ejecuta: `SELECT ... FROM player_season_stats WHERE season = 'E2025' ORDER BY points DESC LIMIT 10`
7. Retorna datos + visualización (bar/line/table)

**Implementación Backend:**
```python
# En text_to_sql.py
if self._requires_player_stats(query):
    params = await self._extract_stats_params(query)
    results = await self._get_player_stats_from_db(
        seasoncode=params["seasoncode"],
        stat=params["stat"],
        top_n=params["top_n"],
        team_code=params.get("team_code")
    )
    return None, "bar", None, results  # Retornar datos directos
```

### ❌ NO Soportadas: Datos a Nivel de Partido

**Ejemplos (retornan error):**
- "Partidos de Larkin con más de 10 puntos"
- "Box score del partido Real Madrid vs Barcelona"
- "Estadísticas de Larkin en cada partido"
- "¿Cuántos puntos anotó Larkin contra el Milan?"

**Razón:** La tabla `player_game_stats` aún no está poblada en la BD. Solo tenemos datos de temporada 2025 agregados por temporada.

**Comportamiento:**
1. Backend detecta keyword: "partidos de", "en el partido", "por cada partido"
2. Backend retorna error informativo:
   ```json
   {
     "error": "⚠️ Esta consulta requiere datos detallados por partido que aún no están disponibles...",
     "data": null,
     "sql": null
   }
   ```
3. Frontend muestra el error al usuario

**Implementación Backend:**
```python
# En text_to_sql.py
def _is_games_query_unavailable(query: str) -> bool:
    query_lower = query.lower()
    games_keywords = [
        "partidos de", "partidos en", "en que partid", 
        "en el partido", "por partido", "por cada partido",
        # ... más keywords
    ]
    return any(keyword in query_lower for keyword in games_keywords)

if self._is_games_query_unavailable(query):
    error_msg = "⚠️ Esta consulta requiere datos detallados por partido..."
    return None, None, error_msg, None
```

### ✅ Soportadas: Consultas Generales de Metadatos

**Ejemplos:**
- "¿Cuántos equipos hay?"
- "Jugadores del Real Madrid"
- "¿Qué posición juega Larkin?"
- "Lista de todos los equipos"

**Flujo:**
1. Frontend envía query
2. **Corrección de consulta (OpenAI)**: Normaliza nombres y corrige erratas
3. **RAG (Retrieval)**: Recupera esquema relevante usando embeddings
4. Backend detecta que NO es de stats
5. Backend usa LLM (OpenRouter) para generar SQL con contexto de esquema
6. Backend ejecuta SQL contra BD
7. Retorna resultados

## Persistencia Frontend

### Chat History (localStorage)

**Clave:** `chat-storage`

**Estructura:**
```typescript
{
  state: {
    sessions: Session[],              // Múltiples sesiones de chat
    currentSessionId: string | null   // ID de sesión activa
  },
  version: 5                          // Versión actual del schema
}
```

**Sistema de Backup:**
- Backup automático antes de cada migración
- Últimos 5 backups almacenados en localStorage
- Recuperación automática de datos legacy al iniciar
- Funciones disponibles en consola: `checkLegacyData()`, `getBackups()`, `restoreLatestBackup()`

**Ciclo de vida:**
1. Usuario escribe mensaje
2. Frontend agrega a sesión actual
3. localStorage se actualiza automáticamente (Zustand persist)
4. Backup automático antes de migraciones
5. Usuario cierra tab/navegador
6. Usuario vuelve → localStorage restaura chat automáticamente
7. Sistema detecta y recupera datos legacy si existen

**NO hay caché de stats** en el frontend. Todos los datos vienen del backend.

## Limitaciones y Próximos Pasos

### Limitaciones Actuales:
- ❌ **Base de datos solo contiene temporada 2025** (jugadores, equipos, estadísticas)
- ❌ No se pueden consultar estadísticas por partido individual (`player_game_stats` no está poblada)
- ❌ No se pueden hacer box scores
- ❌ No se pueden filtrar stats por rango de fechas (solo por temporada E2025)
- ✅ RAG funciona con fallback seguro si OpenAI API key no está configurada
- ✅ Sistema de corrección de consultas mejora precisión de nombres

### Próximos Pasos (Future):
1. Extender ETL para ingerir múltiples temporadas (2023, 2024, 2025)
2. Poblar tabla `player_game_stats` con ETL
3. Implementar queries a nivel de partido
4. Agregar análisis temporal (por jornada, por fecha)
5. Soportar visualizaciones avanzadas (shot charts, heatmaps)
6. Mejorar RAG con más ejemplos SQL y metadatos de esquema

## Ejemplos de Flujo Real

### Ejemplo 1: Top 10 Anotadores (FUNCIONA)

```
Usuario: "Top 10 anotadores"
  ↓
Backend: _requires_player_stats("Top 10 anotadores") = True
Backend: _is_games_query_unavailable("Top 10 anotadores") = False
Backend: Extrae params: {seasoncode: "E2025", stat: "points", top_n: 10}
Backend: SELECT * FROM player_season_stats WHERE season='E2025' ORDER BY points DESC LIMIT 10
Backend: Retorna 10 jugadores con stats
Frontend: Renderiza BarChart
```

### Ejemplo 2: Partidos de Larkin (NO FUNCIONA)

```
Usuario: "Partidos de Larkin con más de 10 puntos"
  ↓
Backend: _requires_player_stats("Partidos de Larkin...") = True
Backend: _is_games_query_unavailable("Partidos de Larkin...") = True
Backend: Retorna error: "Esta consulta requiere datos detallados por partido..."
Frontend: Muestra mensaje de error
```

### Ejemplo 3: Equipos (FUNCIONA)

```
Usuario: "¿Cuántos equipos hay?"
  ↓
Backend: _requires_player_stats("¿Cuántos equipos hay?") = False
Backend: _is_games_query_unavailable("¿Cuántos equipos hay?") = False
Backend: LLM genera: "SELECT COUNT(*) FROM teams"
Backend: Ejecuta SQL
Backend: Retorna: {count: 18}
Frontend: Muestra resultado en tabla
```

## Testing

Para probar que el backend detecta correctamente los tipos de queries:

```bash
cd backend
python -m pytest tests/features/chat_endpoint.feature -v
```

Para probar la detección de queries de partidos:

```bash
python -c "
from app.services.text_to_sql import TextToSQLService
service = TextToSQLService(api_key='test')

queries = [
    'Top 10 anotadores',
    'Partidos de Larkin con más de 10 puntos',
    'Mejores reboteadores del Real Madrid'
]

for q in queries:
    requires_stats = service._requires_player_stats(q)
    is_games = service._is_games_query_unavailable(q)
    print(f'{q}: stats={requires_stats}, games={is_games}')
"
```
