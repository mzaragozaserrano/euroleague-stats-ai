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
- **Issue #34 (In Progress):** Testing BDD para SQL generation - validación de safety, edge cases, integración con chat history.

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