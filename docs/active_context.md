# Active Context

## Current Focus
We have successfully completed Phase 1 (Data/ETL).
**We are now starting Phase 2: Backend & AI Engine.**

The immediate goal is to build the "Brain" of the application: enabling the system to understand natural language and translate it into SQL queries using RAG.

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