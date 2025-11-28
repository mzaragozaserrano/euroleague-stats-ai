# Active Context

## Current Focus
**Issue #31: 2.2 RAG Service - Implementar retrieve_relevant_schema()**

Implementando el servicio RAG que recupera metadatos relevantes del esquema basándose en la consulta del usuario usando búsqueda de similaridad vectorial con pgvector.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.

## Active Problems / Blockers
- **None currently.** The foundation is stable.

## Next Steps (Immediate)
1. **Implement RAG Service:** Create `backend/app/services/rag.py` with `retrieve_relevant_schema(query: str)` function.
2. **Integrate pgvector:** Use vector similarity search to find K most relevant schema embeddings (K=3-5).
3. **Return Schema Metadata:** Return table names, columns, and SQL examples for the LLM prompt.
4. **Test & Document:** Ensure latency < 500ms and document in architecture.md.