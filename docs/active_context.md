# Active Context

## Current Focus
**#44: 3.3 Data Visualizer - Recharts Integration** (EN PROGRESO)

Implementar visualizaciones dinámicas (Bar Chart, Line Chart, Table) usando Recharts según el tipo de respuesta del backend.

## Recent Decisions & Achievements
- **ETL Completed:** We have a robust, tested ETL pipeline running daily on GitHub Actions.
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
   - ORDER BY/LIMIT/GROUP BY en queries
   - SQL injection prevention (DROP/DELETE/UPDATE/INSERT)
   - RAG retrieval con/sin historial
   - NULL handling, caracteres especiales, performance
2. **Unit Tests:** 27 tests para TextToSQLService + 11 para VectorizationService.
3. **SQL Safety:** Validación robusta de queries peligrosas.
4. **Total Tests:** 68+ tests pasados (15 BDD + 53 unit tests).

## Completed in Issue #40
1. **MCP Configuration:** `.cursor/mcp.json` configurado con Neon connection settings.
2. **Security Features:** Validación de SQL safety, timeout de 5s, límite de 1000 filas.
3. **Verification Queries:** 10 queries de prueba en `backend/tests/mcp_verification_queries.sql`.
4. **Documentation:** Guía completa de setup, uso y troubleshooting en README.md.
5. **Features:** Solo operaciones SELECT/EXPLAIN permitidas, bloqueo de DROP/DELETE/UPDATE/INSERT/ALTER/CREATE.

## Completed in Issue #42
1. **Zustand Store:** `frontend/stores/chatStore.ts` con estado completo e interface TypeScript.
   - Estado: messages[], history[], isLoading, error, coldStartWarning, rateLimitWarning
   - Acciones: addMessage(), setLoading(), setError(), clearError(), clearHistory()
2. **Persistencia:** localStorage usando middleware `persist` de Zustand.
   - Historial sobrevive a cierres de tab y página refresca
   - Selective persistence (solo history y messages)
3. **BDD Tests:** 10 escenarios en `chat_store.feature` con step definitions completas.
   - Validación de inicialización, agregación de mensajes, persistencia
   - Estados de carga y errores funcionando correctamente
4. **Test Results:** 10/10 tests pasados exitosamente

## Completed in Issue #43
1. **Chat UI Components:** Componentes funcionales con shadcn/ui.
   - `ChatInput`: Input textarea con Enter para enviar, Shift+Enter para nueva línea
   - `MessageBubble`: Renderiza mensajes con estilos diferenciados (user/assistant)
   - `MessageList`: Scroll automático, indicador de carga
   - `ChatContainer`: Layout principal con header, warnings, y area de input
2. **Mobile-First Design:** Todos los componentes responsivos usando Tailwind CSS.
3. **Zustand Integration:** Gestión de estado centralizada desde los componentes.

## In Progress - Issue #44
1. **DataVisualizer Component:** Componente principal que renderiza visualizaciones dinámicas.
   - Soporta 3 tipos: BarChart, LineChart, DataTable
   - Auto-detección de columnas numéricas y categóricas
   - Manejo robusto de casos edge (datos vacíos, inválidos)
   - Responsivo en móvil con labels rotados, scroll horizontal en tablas
2. **MessageBubble Integration:** Actualizado para renderizar visualizaciones cuando existen.
   - Mantiene estructura de SQL details y timestamps
   - Renderiza DataVisualizer si data y visualization existen
3. **BDD Tests:** 10 escenarios en `data_visualizer.feature` con step definitions.
   - Cobertura completa: BarChart, LineChart, DataTable, edge cases
   - Responsive, special characters, múltiples columnas
4. **Documentation:** README completo con ejemplos de uso, props, casos edge.

## Next Steps (Immediate)
1. **Phase 3 Frontend (En Progreso):** 
   - **#42:** Implementar Zustand store para gestión de estado del chat
   - **#43:** Crear componentes UI del chat con shadcn/ui (mobile-first)
   - **#44:** Implementar visualizaciones dinámicas con Recharts (Bar/Line/Table)
   - **#47:** Conectar frontend con backend `/api/chat` y manejo de errores
   - **#45:** Persistencia en localStorage y mejoras de UX
   - **#46:** Configurar deployment en Render
2. **Performance Tuning:** Caché de queries frecuentes, optimización de prompts (futuro).