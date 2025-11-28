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
*Key Tables implemented in Phase 1:*

- **`teams`**: `id`, `code`, `name`, `logo_url`.
- **`players`**: `id`, `team_id`, `name`, `position`.
- **`games`**: `id`, `season`, `round`, `home_team_id`, `away_team_id`, `scores`.
- **`player_stats_games`** (Fact Table): Granular box scores per player per game.
    - Metrics: `points`, `rebounds`, `assists`, `fg3_made`, `pir`, etc.
    - Constraints: Unique(`game_id`, `player_id`).
- **`schema_embeddings`**:
    - `content`: Text description of tables/columns.
    - `embedding`: Vector representation (1536 dim).
    - *Purpose:* RAG retrieval to find relevant schema for SQL generation.

## 4. AI Pipeline (Text-to-SQL)
1.  **Input:** User Query ("Puntos de Larkin vs Micic").
2.  **Schema Retrieval (RAG):**
    - Vectorize Query -> Search `schema_embeddings` table.
    - *Constraint:* DO NOT vectorise row data (stats), ONLY schema metadata.
3.  **Prompt Construction:** Inject retrieved schema + few-shot SQL examples.
4.  **Generation:** LLM produces JSON `{ sql, visualization_type }`.
5.  **Execution:** Run SQL on Neon (Read-Only user).

## 5. Critical Constraints
- **Neon Serverless:** MUST use `poolclass=NullPool` in SQLAlchemy engine.
- **Embeddings:** Use API-based embeddings to save RAM on Render.
- **ETL:** Daily Cron via GitHub Actions (Cost: $0).

## 6. Testing Strategy
- **Framework:** `pytest-bdd` + `pytest-asyncio`.
- **Workflow:** `.feature` file -> Step Definitions -> Implementation.