# Architecture & Tech Spec

## 1. Tech Stack Details
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, Shadcn/ui, Recharts.
- **Backend:** Python 3.11+ (FastAPI), Poetry (Dependency Mgmt).
- **Database:** Neon (Serverless PostgreSQL 16) + `pgvector`.
- **ORM:** SQLAlchemy (Async) + `asyncpg`.
- **AI/LLM:**
    - **OpenAI API**: Usado para embeddings (`text-embedding-3-small`) y corrección de consultas (input).
    - **OpenRouter**: Usado para generación de SQL (output) con modelo `openai/gpt-3.5-turbo`.
    - **RAG (Retrieval Augmented Generation)**: Sistema implementado con fallback a esquema hardcodeado.
- **Data Source:** [`euroleague-api`](https://github.com/giasemidis/euroleague_api) - Python wrapper para la API oficial de Euroleague. Usado en el pipeline ETL para extraer datos de equipos, jugadores y estadísticas.

## 2. Project Structure (Monorepo)
```text
root/
├── backend/
│   ├── app/           # FastAPI Source
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Text-to-SQL, Vectorization, Response Generator
│   │   └── models/    # SQLAlchemy models
│   ├── etl/           # Scripts de Ingesta (Teams, Players, Stats)
│   ├── migrations/    # SQL migrations (incluye schema_embeddings)
│   ├── scripts/       # Utilidades (init_schema_embeddings, test_rag_usage)
│   └── tests/         # BDD (pytest-bdd)
├── frontend/          # Next.js Source
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utilidades (localStorageBackup, checkLegacyData)
│   └── stores/        # Zustand stores (chatStore)
├── data/              # Local storage (git ignored)
└── .github/           # CI/CD & ETL Workflows
```

## 3. Data Model (Schema)

### Tablas de Producción:

- **`teams`**: `id`, `code`, `name`, `logo_url`.
  - Actualización: Diaria (8 AM UTC) vía ETL automático desde API Euroleague.
  - **Datos actuales**: Solo temporada 2025.

- **`players`**: `id`, `player_code`, `team_id`, `name`, `position`, `season`.
  - Campo clave: `player_code` (código de Euroleague API).
  - Campo `season`: Código de temporada (E2025, E2024, etc.).
  - Actualización: Diaria (8 AM UTC) vía ETL automático.
  - **Datos actuales**: Solo temporada E2025.

- **`player_season_stats`**: `id`, `player_id`, `season`, `games_played`, `points`, `rebounds`, `assists`, `threePointsMade`, `pir`.
  - Estadísticas agregadas por temporada (desde API Euroleague vía ETL).
  - Actualización: Diaria (8 AM UTC).
  - **Datos actuales**: Solo temporada E2025.

- **`schema_embeddings`**: `id`, `content`, `embedding` (vector 1536 dimensiones).
  - Descripciones de tablas/columnas y ejemplos SQL para RAG retrieval.
  - Permite que el LLM genere SQL relevante usando búsqueda semántica.
  - Poblado manualmente con `backend/scripts/init_schema_embeddings.py`.

- **`games`**: `id`, `game_code`, `season`, `round`, `date`, `home_team_id`, `away_team_id`, `home_score`, `away_score`.
  - Metadatos de partidos. **NO está poblada actualmente**.

- **`player_game_stats`**: `id`, `game_id`, `player_id`, `team_id`, `minutes`, `points`, `rebounds`, `assists`, `three_points_made`, `pir`.
  - Estadísticas por partido (box score). **NO está poblada actualmente**.

### Almacenamiento Frontend (localStorage):

- **`chat-storage`**: Historial de conversaciones del usuario (persistencia del frontend).
  - Estructura: `{ state: { sessions: [], currentSessionId }, version: 5 }`
  - Versión: 5 (con migración automática desde versiones anteriores).
  - Sistema de backup automático antes de migraciones.
  - Recuperación automática de datos legacy al iniciar la app.
  - Sobrevive a cierres de tab y recargas de página.
  - **NO HAY base de datos embebida en el frontend** (sin IndexedDB, SQLite, u otros).
  - Todos los datos se consultan del backend (Neon PostgreSQL).

## 4. Fuente de Datos y ETL

### euroleague-api Wrapper

Este proyecto utiliza [`euroleague-api`](https://github.com/giasemidis/euroleague_api) (por [@giasemidis](https://github.com/giasemidis)) como wrapper de Python para acceder a la API oficial de Euroleague.

**Uso en el proyecto:**
- **Paquete:** `euroleague-api` (versión >=0.1.0)
- **Ubicación:** `backend/pyproject.toml`
- **Módulos utilizados:**
  - `euroleague_api.standings.Standings` - Para obtener equipos
  - `euroleague_api.player_stats.PlayerStats` - Para obtener jugadores y estadísticas
  - `euroleague_api.boxscore_data.BoxScoreData` - Para obtener datos de partidos (futuro)

**Scripts ETL que lo utilizan:**
- `backend/etl/ingest_teams.py` - Ingesta de equipos
- `backend/etl/ingest_players.py` - Ingesta de jugadores
- `backend/etl/ingest_player_season_stats.py` - Ingesta de estadísticas de temporada
- `backend/etl/ingest_games.py` - Ingesta de partidos (preparado para futuro)
- `backend/etl/ingest_boxscores.py` - Ingesta de box scores (preparado para futuro)

**Licencia:** El proyecto `euroleague-api` utiliza licencia MIT, compatible con nuestra licencia MIT.

## 5. Flujo de Datos

### Arquitectura Actual:

```
API Euroleague (GitHub)
        ↓ (ETL diario 8 AM UTC - Solo temporada 2025)
Backend BD (Neon PostgreSQL)
        ↑ (Text-to-SQL generado por LLM)
Frontend ChatStore
        ↓ (localStorage persistence + backup automático)
Usuario Chat History
```

### Flujo de una Consulta:

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

**Pasos detallados:**

1. **Usuario escribe query** en el chat frontend
2. **Frontend envía** `POST /api/chat` con query + historial
3. **Backend procesa:**
   - **Corrección de consulta (OpenAI via OpenRouter)**: Corrige erratas tipográficas (ej: "Campazo" → "Campazzo")
   - **RAG (Retrieval Augmented Generation)**: 
     - Genera embedding de la query usando OpenAI `text-embedding-3-small`
     - Busca esquema relevante en `schema_embeddings` usando cosine similarity
     - Si RAG falla o no está disponible, usa esquema hardcodeado como fallback
   - **Generación de SQL (OpenRouter)**: LLM genera SQL usando contexto de esquema
   - **Ejecución**: Ejecuta SQL contra BD (Neon)
   - **Generación de Respuesta (OpenRouter)**: GPT-3.5-turbo genera respuesta en lenguaje natural (Markdown) basada en los datos obtenidos
   - **Retorna**: JSON con SQL, datos, tipo de visualización y mensaje en Markdown
4. **Frontend recibe** respuesta y renderiza:
   - Mensaje en Markdown (texto formateado con negritas, tablas, etc.)
   - Visualización de datos (BarChart, LineChart, DataTable) cuando corresponde
5. **localStorage persiste** el chat para futuras sesiones (con backup automático)

### Tipos de Consultas Soportadas

#### ✅ Soportadas: Estadísticas Agregadas por Temporada

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

#### ❌ NO Soportadas: Datos a Nivel de Partido

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

#### ✅ Soportadas: Consultas Generales de Metadatos

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

### Uso de OpenAI:

- **Input (Corrección de consultas)**: 
  - Modelo: `openai/gpt-3.5-turbo` via OpenRouter
  - Propósito: Corregir erratas tipográficas y normalizar nombres de jugadores/equipos
  - Ejemplo: "Campazo" → "Campazzo", "Larkyn" → "Larkin"

- **Embeddings (RAG)**:
  - Modelo: `text-embedding-3-small` (1536 dimensiones)
  - Propósito: Generar embeddings de metadatos de esquema y queries del usuario
  - Almacenamiento: PostgreSQL con `pgvector`

- **Output (Generación de SQL)**:
  - Modelo: `openai/gpt-3.5-turbo` via OpenRouter
  - Propósito: Convertir consultas naturales a SQL válido
  - Contexto: Esquema relevante recuperado por RAG

### Ejemplos de Flujo Real

**Ejemplo 1: Top 10 Anotadores (FUNCIONA)**
```
Usuario: "Top 10 anotadores"
  ↓
Backend: Detecta consulta de stats
Backend: Extrae params: {seasoncode: "E2025", stat: "points", top_n: 10}
Backend: SELECT * FROM player_season_stats WHERE season='E2025' ORDER BY points DESC LIMIT 10
Backend: Retorna 10 jugadores con stats
Frontend: Renderiza BarChart
```

**Ejemplo 2: Partidos de Larkin (NO FUNCIONA)**
```
Usuario: "Partidos de Larkin con más de 10 puntos"
  ↓
Backend: Detecta keyword "partidos de"
Backend: Retorna error: "Esta consulta requiere datos detallados por partido..."
Frontend: Muestra mensaje de error
```

**Ejemplo 3: Equipos (FUNCIONA)**
```
Usuario: "¿Cuántos equipos hay?"
  ↓
Backend: Detecta consulta de metadatos
Backend: LLM genera: "SELECT COUNT(*) FROM teams"
Backend: Ejecuta SQL
Backend: Retorna: {count: 18}
Frontend: Muestra resultado en tabla
```

### Limitaciones Actuales:

- ❌ **Base de datos solo contiene datos de temporada 2025** (jugadores, equipos, estadísticas)
- ❌ No se pueden consultar datos a nivel de partido individual (`player_game_stats` no está poblada)
- ❌ Las queries que requieren "partidos específicos" retornan error explicativo
- ❌ No se pueden hacer box scores
- ❌ No se pueden filtrar stats por rango de fechas (solo por temporada E2025)
- ✅ Sí se pueden consultar estadísticas agregadas por temporada (`player_season_stats` para E2025)
- ✅ Sí se pueden consultar metadatos (equipos, jugadores, posiciones de temporada 2025)
- ✅ RAG funciona con fallback seguro si OpenAI API key no está configurada
- ✅ Sistema de corrección de consultas mejora precisión de nombres

## 5. Critical Constraints
- **Neon Serverless:** MUST use `poolclass=NullPool` in SQLAlchemy engine.
- **Embeddings:** Use API-based embeddings (OpenAI `text-embedding-3-small`) to save RAM on Render.
- **ETL:** Daily Cron via GitHub Actions at 8 AM UTC (Cost: $0). Solo ingiere temporada 2025 por defecto.
- **Base de Datos:** Solo contiene datos de temporada 2025. Otras temporadas no están disponibles.
- **OpenAI API Key:** Requerida para RAG y corrección de consultas. Si no está configurada, el sistema usa fallback (esquema hardcodeado).
- **OpenRouter API Key:** Requerida para generación de SQL. Sin ella, el sistema no puede funcionar.
- **localStorage Limit:** 5-10 MB. Sistema de backup automático antes de migraciones.
- **API Euroleague:** Fuente única de verdad para estadísticas de jugadores (vía ETL diario).

## 6. Testing Strategy
- **Framework:** `pytest-bdd` + `pytest-asyncio`.
- **Workflow:** `.feature` file -> Step Definitions -> Implementation.
- **Cobertura:** Tests para ETL, Text-to-SQL, Chat endpoint, y RAG.

## 7. Sistema de Backup y Recuperación

### Backup Automático (Frontend)
- **Ubicación:** `frontend/lib/localStorageBackup.ts`
- **Funcionalidad:** 
  - Crea backup automático antes de migraciones de `chat-storage`
  - Mantiene últimos 5 backups
  - Permite restaurar backups manualmente desde consola del navegador
- **Funciones disponibles en consola:**
  - `checkLegacyData()`: Verificar y recuperar datos legacy
  - `getBackups()`: Listar backups disponibles
  - `restoreLatestBackup()`: Restaurar backup más reciente

### Recuperación de Datos Legacy
- **Ubicación:** `frontend/lib/checkLegacyData.ts`
- **Funcionalidad:**
  - Detecta automáticamente datos legacy al iniciar la app
  - Convierte formatos antiguos a estructura actual de sesiones
  - Se ejecuta automáticamente en `BackupSystemInit` component

## 8. RAG (Retrieval Augmented Generation)

### Implementación
- **Servicio:** `backend/app/services/vectorization.py`
- **Tabla:** `schema_embeddings` (PostgreSQL con `pgvector`)
- **Modelo de embeddings:** OpenAI `text-embedding-3-small` (1536 dimensiones)
- **Búsqueda:** Cosine similarity usando operador `<=>` de pgvector

### Flujo RAG
1. Usuario envía query natural
2. Se genera embedding de la query usando OpenAI
3. Se busca en `schema_embeddings` los metadatos más relevantes (top 10)
4. Se filtra por similitud mínima (>= 0.3)
5. Se construye contexto de esquema con resultados relevantes
6. Si RAG falla o no hay resultados, se usa esquema hardcodeado como fallback

### Inicialización
- **Script:** `backend/scripts/init_schema_embeddings.py`
- **Contenido:** Metadatos de tablas, columnas, relaciones y ejemplos SQL
- **Ejecución:** Manual (requiere `OPENAI_API_KEY` configurada)

### Fallback
- Si `OPENAI_API_KEY` no está configurada → usa esquema hardcodeado
- Si la tabla `schema_embeddings` está vacía → usa esquema hardcodeado
- Si hay error en la búsqueda → usa esquema hardcodeado
- El sistema siempre funciona, incluso sin RAG configurado

## 9. Persistencia Frontend

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

**Ciclo de vida:**
1. Usuario escribe mensaje
2. Frontend agrega a sesión actual
3. localStorage se actualiza automáticamente (Zustand persist)
4. Backup automático antes de migraciones
5. Usuario cierra tab/navegador
6. Usuario vuelve → localStorage restaura chat automáticamente
7. Sistema detecta y recupera datos legacy si existen

**NO hay caché de stats** en el frontend. Todos los datos vienen del backend.

## 10. Testing

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