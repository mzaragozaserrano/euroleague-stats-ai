# Active Context

## Current Focus
**Fase 3 DevOps COMPLETADA - Listos para Phase 4 Post MVP**

Todas las tareas de deployment y frontend completadas. Sistema listo para producción en Render.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **Lazy Ingestion:** Implementado sistema de ingesta bajo demanda para datos históricos (e.g., 2024). Si el usuario pide datos que no están en BD, se descargan automáticamente de la API.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.
- **Issue #32 Completed:** Text-to-SQL service with OpenRouter integration and prompt engineering.
- **Issue #33 Completed:** Chat endpoint with full AI pipeline orchestration (RAG → SQL Gen → Execution).
- **Issue #34 Completed:** BDD tests with 15 scenarios for SQL generation accuracy and validation.
- **Issue #40 Completed:** MCP configuration for Neon in Cursor with verification queries and documentation.

## Active Problems / Blockers
- **None currently.** Phase 2 (Backend & AI Engine) 100% complete. Phase 3 Frontend development iniciada.

## Completed in Issue #33
1. **BDD Tests:** 12 scenarios en `chat_endpoint.feature` con step definitions.
2. **Text-to-SQL Service:** Implementado con OpenRouter, validación de SQL safety, reintentos.
3. **Chat Endpoint:** Orquestación completa (RAG → SQL Gen → Execution).
4. **Error Handling:** Status 200 siempre, errores en campo error. Timeout/LLM/BD sin crashes.
5. **Response Format:** {sql, data, visualization, error?} garantizado < 5s.
6. **Logging:** Logs de RAG retrieval, SQL generation, execution en stdout.
7. **Documentation:** Setup guide con troubleshooting y arquitectura.

## Completed in Issue #34
1. **BDD Tests (15 scenarios):** Validación de SQL generation con pytest-bdd.
   
