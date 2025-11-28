# Active Context

## Current Focus
**Issue #32: 2.3 Text-to-SQL Service - Ingeniería de prompts e integración con LLM**

Implementando el servicio que convierte consultas en SQL usando LLM (OpenRouter). Incluye diseño de prompts con System + Few-Shot examples, validación de SQL generado y manejo de errores estructurado.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
- **DB Populated:** The Neon database has tables populated with teams, players, and basic stats.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.

## Active Problems / Blockers
- **None currently.** The foundation is stable.

## Next Steps (Immediate)
1. **Implement Text-to-SQL Service:** Create `backend/app/services/text_to_sql.py` with `generate_sql(query: str, schema_context: str)` function.
2. **Design Prompt Engineering:** System prompt + Few-Shot SQL examples for common query patterns.
3. **Integrate OpenRouter API:** Call LLM with low-cost model, handle rate limits and errors.
4. **SQL Validation:** Reject DROP/DELETE statements and malicious queries.
5. **Structured Response:** Return JSON with `{sql, data, visualization, latency}` format.