# Active Context

## Current Focus
**Issue #30: Vectorización - Script para generar embeddings de metadatos**

Implementando el primer paso de Phase 2: crear un servicio para generar y almacenar embeddings de descripciones de tablas y columnas usando OpenAI text-embedding-3-small.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.

## Active Problems / Blockers
- **None currently.** The foundation is stable.

## Next Steps (Immediate)
1. **Initialize Embeddings:** Create the script `backend/scripts/init_embeddings.py` to populate the `schema_embeddings` table.
2. **Implement RAG Service:** Create `backend/app/services/embedding_service.py` and `rag_service.py`.
3. **Prompt Engineering:** Define the System Prompt for the Text-to-SQL agent.