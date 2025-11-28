# Active Context

## Current Focus
**Issue #34: 2.5 Testing - BDD para precisión SQL**

Escribir tests BDD (pytest-bdd) para validar la calidad del SQL generado. Crear escenarios para TOP/ORDER BY, validar SQL safety contra inyecciones, y recuperar schema relevante del historial de chat. Target: 10+ scenarios con cobertura >= 85% en services/.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.
- **Issue #32 (In Progress):** Text-to-SQL service with OpenRouter integration and prompt engineering.

## Active Problems / Blockers
- None currently

## Completed in Issue #34
1. **BDD Tests (15 scenarios):** Validación de SQL generation con pytest-bdd.
   - ORDER BY/LIMIT/GROUP BY en queries
   - SQL injection prevention (DROP/DELETE/UPDATE/INSERT)
   - RAG retrieval con/sin historial
   - NULL handling, caracteres especiales, performance
2. **Unit Tests:** 27 tests para TextToSQLService + 11 para VectorizationService.
3. **SQL Safety:** Validación robusta de queries peligrosas.
4. **Total Tests:** 68+ tests pasados (15 BDD + 53 unit tests).

## Completed in Issue #33
1. **BDD Tests:** 12 scenarios en `chat_endpoint.feature` con step definitions.
2. **Text-to-SQL Service:** Implementado con OpenRouter, validación de SQL safety, reintentos.
3. **Chat Endpoint:** Orquestación completa (RAG → SQL Gen → Execution).
4. **Error Handling:** Status 200 siempre, errores en campo error. Timeout/LLM/BD sin crashes.
5. **Response Format:** {sql, data, visualization, error?} garantizado < 5s.
6. **Logging:** Logs de RAG retrieval, SQL generation, execution en stdout.
7. **Documentation:** Setup guide con troubleshooting y arquitectura.

## Next Steps (Immediate)
1. **Issue #34 (Testing):** Ampliar BDD tests con casos de edge cases e integracion.
2. **Frontend Integration:** Implementar chat UI en Next.js que consuma /api/chat.
3. **Schema Embeddings:** Generar embeddings iniciales de metadatos para RAG.
4. **Performance Tuning:** Caché de queries frecuentes, optimización de prompts.