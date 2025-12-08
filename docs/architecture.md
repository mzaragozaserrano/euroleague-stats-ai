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

### Tablas de Producción:

- **`teams`**: `id`, `code`, `name`, `logo_url`.
  - Actualización: Diaria (7 AM UTC) vía ETL automático desde API Euroleague.

- **`players`**: `id`, `player_code`, `team_id`, `name`, `position`.
  - Campo clave: `player_code` (código de Euroleague API).
  - Actualización: Diaria (7 AM UTC) vía ETL automático.

- **`player_season_stats`**: `id`, `player_id`, `season`, `games_played`, `points`, `rebounds`, `assists`, `pir`.
  - Estadísticas agregadas por temporada (desde API Euroleague vía ETL).
  - Actualización: Diaria (7 AM UTC).

- **`schema_embeddings`**: `id`, `content`, `embedding`.
  - Descripciones de tablas/columnas para RAG retrieval.
  - Permite que el LLM genere SQL relevante.

### Almacenamiento Frontend (localStorage - SOLO CHATS):

- **`chat-storage`**: Historial de conversaciones del usuario (ÚNICA persistencia del frontend).
  - Estructura: `{ messages: [], history: [], lastCleared, totalQueriesCount, sessions, currentSessionId }`
  - Versión: 3 (con migración automática desde v1, v2)
  - Sobrevive a cierres de tab y recargas de página.
  - **NO HAY base de datos embebida en el frontend** (sin IndexedDB, SQLite, u otros).
  - Todos los datos se consultan del backend (Neon PostgreSQL).

## 4. Flujo de Datos

### Arquitectura Actual:

```
API Euroleague (GitHub)
        ↓ (ETL diario 7 AM UTC)
Backend BD (Neon PostgreSQL)
        ↑ (Text-to-SQL generado por LLM)
Frontend ChatStore
        ↓ (localStorage persistence)
Usuario Chat History
```

### Flujo de una Consulta:

1. **Usuario escribe query** en el chat frontend
2. **Frontend envía** `POST /api/chat` con query + historial
3. **Backend procesa:**
   - Obtiene esquema relevante (RAG)
   - LLM genera SQL usando OpenRouter
   - Ejecuta SQL contra BD (Neon)
   - Retorna resultados en JSON
4. **Frontend recibe** respuesta y renderiza visualización
5. **localStorage persiste** el chat para futuras sesiones

### Limitaciones Actuales:

- ❌ No se pueden consultar datos a nivel de partido individual (`player_stats_games`)
- ❌ Las queries que requieren "partidos específicos" retornan error explicativo
- ✅ Sí se pueden consultar estadísticas agregadas por temporada (`player_season_stats`)
- ✅ Sí se pueden consultar metadatos (equipos, jugadores, posiciones)

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