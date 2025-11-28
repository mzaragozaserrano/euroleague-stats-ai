# Active Context

## Current Focus
**Issue #33: 2.4 Chat Endpoint - Conectar /api/chat al motor de IA**

Orquestación completa del pipeline de IA: vectorización → RAG retrieval → generación SQL → ejecución. Implementar POST /api/chat que retorna {sql, data, visualization, error?} con manejo robusto de errores.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.
- **Issue #32 (In Progress):** Text-to-SQL service with OpenRouter integration and prompt engineering.

## Active Problems / Blockers
- **None currently.** The foundation is stable.

## Next Steps (Immediate)
1. **Write BDD Tests:** Scenarios para chat endpoint (query exitosa, errores, visualización).
2. **Implement Chat Endpoint:** Orquestar VectorizationService → RAG → SQL Generation → Execution.
3. **Error Handling:** Todos los errores retornan status 200 con campo error en JSON.
4. **Response Format:** {sql, data, visualization, error?} con latencia < 5s.
5. **Logging:** stdout logs de RAG retrieval para debugging.