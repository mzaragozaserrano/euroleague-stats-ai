# Active Context

## Current Focus
**MVP COMPLETADO ✅ - Enero 2025**

Todas las fases del MVP (0-3) han sido completadas exitosamente:
- ✅ Fase 0: Scaffolding & Setup
- ✅ Fase 1: Data Pipeline MVP
- ✅ Fase 2: Backend & AI Engine
- ✅ Fase 3: Frontend MVP

Sistema completamente funcional con ETL automático, motor Text-to-SQL con RAG, frontend con visualizaciones y persistencia inteligente.

## Recent Decisions & Achievements
- **ETL Completed:** Pipeline robusto ejecutándose diariamente en GitHub Actions (8 AM UTC). Solo ingiere temporada 2025 por defecto.
- **Base de Datos:** Solo contiene datos de temporada 2025 (jugadores, equipos, player_season_stats). Otras temporadas no están disponibles.
- **RAG Implementado:** Sistema completo de Retrieval Augmented Generation con embeddings de OpenAI `text-embedding-3-small`. Fallback seguro a esquema hardcodeado si RAG no está disponible.
- **OpenAI Integration:** 
  - Usado para embeddings (RAG) - `text-embedding-3-small`
  - Usado para corrección de consultas (input) - `openai/gpt-3.5-turbo` via OpenRouter
  - Usado para generación de SQL (output) - `openai/gpt-3.5-turbo` via OpenRouter
- **Backup System:** Sistema automático de backup y recuperación de datos legacy para localStorage implementado.
- **Tech Choice:** Validated `pytest-bdd` + `pytest-asyncio` workflow works perfectly for our async FastAPI backend.
- **Infrastructure:** Confirmed `NullPool` configuration is working for Neon connectivity.
- **Issue #30 Completed:** Vectorization service implemented with embeddings generation and storage.
- **Issue #32 Completed:** Text-to-SQL service with OpenRouter integration and prompt engineering.
- **Issue #33 Completed:** Chat endpoint with full AI pipeline orchestration (RAG → SQL Gen → Execution).
- **Issue #34 Completed:** BDD tests with 15 scenarios for SQL generation accuracy and validation.
- **Issue #40 Completed:** MCP configuration for Neon in Cursor with verification queries and documentation.
- **Issue #44 Completed:** DataVisualizer component with Recharts (BarChart, LineChart, DataTable).
- **RAG Implementation:** Sistema completo con migración, scripts de inicialización y fallback seguro.

## Active Problems / Blockers
- **None currently.** MVP completamente funcional. Todas las fases 0-3 completadas.

## Data Source Attribution
Este proyecto utiliza [`euroleague-api`](https://github.com/giasemidis/euroleague_api) (por [@giasemidis](https://github.com/giasemidis)) como wrapper de Python para acceder a la API oficial de Euroleague. Ver `docs/architecture.md` para más detalles sobre su uso en el pipeline ETL.

## Current Architecture State
- **Base de Datos:** Solo temporada 2025 (E2025)
- **ETL:** Ejecuta diariamente a las 8 AM UTC, solo ingiere temporada 2025
- **RAG:** Funcional con fallback seguro
- **OpenAI:** Usado para embeddings, corrección de consultas y generación de SQL
- **Backup System:** Funcional con recuperación automática de datos legacy
- **Documentación:** Consolidada en 4 archivos principales: `active-context.md`, `architecture.md`, `project-brief.md`, `roadmap.md`

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

## RAG Implementation Details
1. **Migración:** `002_add_schema_embeddings.sql` crea tabla `schema_embeddings` con pgvector
2. **Script de inicialización:** `init_schema_embeddings.py` pobla embeddings de metadatos
3. **Servicio:** `VectorizationService` genera y recupera embeddings
4. **Integración:** `chat.py` usa RAG con fallback seguro
5. **Fallback:** Si RAG falla, usa esquema hardcodeado (sistema siempre funciona)

## Backup System Details
1. **Backup automático:** Se crea antes de cada migración de `chat-storage`
2. **Recuperación legacy:** Detecta y convierte formatos antiguos automáticamente
3. **Funciones de consola:** Disponibles para gestión manual de backups
4. **Componente:** `BackupSystemInit` ejecuta verificación al iniciar la app
   
