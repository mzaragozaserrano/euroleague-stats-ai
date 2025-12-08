# Architecture & Tech Spec

## 1. Tech Stack Details
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, Shadcn/ui, Recharts.
- **Backend:** Python 3.11+ (FastAPI), Poetry (Dependency Mgmt).
- **Database:** Neon (Serverless PostgreSQL 16) + `pgvector`.
- **ORM:** SQLAlchemy (Async) + `asyncpg`.
- **AI/LLM:**
    - Orchestration: OpenAI SDK / LangChain.
    - Inference: OpenRouter (Claude 3.5 Haiku/Sonnet).
    - Embeddings: OpenAI `text-embedding-3-small` (via API).

## 2. Project Structure (Monorepo)
```text
root/
├── backend/
│   ├── app/           # FastAPI Source
│   ├── etl/           # Scripts de Ingesta
│   └── tests/         # BDD (pytest-bdd)
├── frontend/          # Next.js Source
├── data/              # Local storage (git ignored)
└── .github/           # CI/CD & ETL Workflows
```

## 3. Data Model (Schema)
*IMPORTANTE: La BD solo almacena METADATOS (códigos). Los datos reales vienen de la API de Euroleague.*

### Tablas Activas:

- **`teams`**: `id`, `code`, `name`, `logo_url`.
  - **Propósito:** Almacenar códigos de equipos para llamadas a API.
  - **Actualización:** Diaria (7 AM) vía ETL automático.

- **`players`**: `id`, `player_code`, `team_id`, `name`, `position`.
  - **Propósito:** Almacenar códigos de jugadores para llamadas a API.
  - **Campo clave:** `player_code` (código de Euroleague API).
  - **Actualización:** Diaria (7 AM) vía ETL automático.

- **`schema_embeddings`**:
  - `content`: Text description of tables/columns.
  - `embedding`: Vector representation (1536 dim).
  - *Purpose:* RAG retrieval to find relevant schema for SQL generation.

### Tablas Deprecadas (Nueva Arquitectura):

- ~~`games`~~ - Los datos de partidos vienen de la API
- ~~`player_stats_games`~~ - Las estadísticas vienen de la API

### Caché Frontend (localStorage):

- **`player-stats-cache`**: Estadísticas de jugadores por temporada.
  - Estructura: `{ "E2024": { data: [], timestamp, lastSync }, "E2025": {...} }`
  - Invalidación: Automática después de las 7 AM.
  - Tamaño: ~5-10 MB (solo temporadas activas).

## 4. Flujo de Datos (Nueva Arquitectura)

### Flujo Principal:
```
Usuario → Frontend (caché check) → API Euroleague → Visualización
         ↓ (solo para códigos)
         Backend (Text-to-SQL) → BD (códigos)
```

### Pasos Detallados:

1. **Input:** User Query ("Top 10 anotadores").
2. **Query Classification (Frontend):**
   - Detectar tipo: `top_players`, `player_lookup`, `team_roster`, `comparison`, `general`.
3. **Caché Check (Frontend):**
   - Verificar `PlayerStatsCache.getSeasonStats('E2025')`.
   - Si existe → usar caché (latencia: 0 ms).
4. **API Call (si no hay caché):**
   - Llamar `EuroleagueApi.getPlayerStats('E2025')`.
   - Guardar en caché para futuras consultas.
5. **Filtrado/Ordenamiento (Frontend):**
   - Aplicar lógica según la consulta (top N, filtro por equipo, etc.).
6. **Visualización:**
   - Renderizar con `DataVisualizer` (BarChart, LineChart, Table).

### Uso de Backend (Text-to-SQL):

**Solo para obtener códigos de equipos/jugadores:**
- Query: "Jugadores del Real Madrid"
- SQL: `SELECT code FROM teams WHERE name ILIKE '%Real Madrid%'`
- Retorna: `{ code: "RM" }`
- Frontend usa `RM` para filtrar stats de la API.

## 5. Critical Constraints
- **Neon Serverless:** MUST use `poolclass=NullPool` in SQLAlchemy engine.
- **Embeddings:** Use API-based embeddings to save RAM on Render.
- **ETL:** Daily Cron via GitHub Actions at 7 AM UTC (Cost: $0).
- **Caché Frontend:** Invalidación automática después de las 7 AM.
- **localStorage Limit:** 5-10 MB (solo cachear temporadas activas: E2024, E2025).
- **API Euroleague:** Fuente única de verdad para estadísticas de jugadores.

## 6. Testing Strategy
- **Framework:** `pytest-bdd` + `pytest-asyncio`.
- **Workflow:** `.feature` file -> Step Definitions -> Implementation.