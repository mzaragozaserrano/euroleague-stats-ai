# Active Context

## Current Focus
**Issue #40: 2.6 Verification (MCP) - Configure Neon MCP in Cursor**

Configurar Model Context Protocol (MCP) para Neon en Cursor a fin de validar queries antes de integrarlas en el Frontend. Establecer conexión MCP entre Cursor y Neon, permitir ejecución y validación de queries directamente desde el editor.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.
- **Issue #32 Completed:** Text-to-SQL service with OpenRouter integration and prompt engineering.
- **Issue #33 Completed:** Chat endpoint with full AI pipeline orchestration (RAG → SQL Gen → Execution).
- **Issue #34 Completed:** BDD tests with 15 scenarios for SQL generation accuracy and validation.

## Active Problems / Blockers
- **None currently.** Backend Phase 2 complete, moving to MCP verification and Frontend Phase 3.

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
   - ORDER BY/LIMIT/GROUP BY en queries
   - SQL injection prevention (DROP/DELETE/UPDATE/INSERT)
   - RAG retrieval con/sin historial
   - NULL handling, caracteres especiales, performance
2. **Unit Tests:** 27 tests para TextToSQLService + 11 para VectorizationService.
3. **SQL Safety:** Validación robusta de queries peligrosas.
4. **Total Tests:** 68+ tests pasados (15 BDD + 53 unit tests).

## Next Steps (Immediate)
1. **Issue #40 (MCP Verification):** Configurar Model Context Protocol para Neon en Cursor.
2. **Phase 3 Frontend:** Implementar chat UI en Next.js que consuma /api/chat.
3. **Schema Embeddings:** Generar embeddings iniciales de metadatos para RAG.
4. **Performance Tuning:** Caché de queries frecuentes, optimización de prompts.