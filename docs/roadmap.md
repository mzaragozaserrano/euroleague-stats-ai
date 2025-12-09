# Project Roadmap

## Phase 0: Scaffolding & Setup (COMPLETED ✅)
- [x] Monorepo structure setup.
- [x] Backend: Poetry, FastAPI, SQLAlchemy configured.
- [x] Frontend: Next.js, Shadcn/ui installed.
- [x] DB: Neon project created, `pgvector` enabled.
- [x] CI: GitHub Actions for testing configured.

## Phase 1: Data Pipeline MVP (COMPLETED ✅)
- [x] DB Schema design & migration (Tables: teams, players, games, stats).
- [x] SQLAlchemy Models implemented.
- [x] Euroleague API Client implemented.
- [x] ETL Scripts (Ingest Teams, Players, Games).
- [x] Daily Cron Workflow (GitHub Actions) operational.
- [x] BDD Tests for ETL passed (15/15 scenarios).

## Phase 2: Backend & AI Engine (COMPLETE ✅)
- [x] **2.1 Vectorization (#30):** Script to generate embeddings for Table/Column descriptions.
- [x] **2.2 RAG Service (#31):** Implement `retrieve_relevant_schema`.
- [x] **2.3 Text-to-SQL Service (#32):** Prompt engineering & LLM integration (OpenRouter).
- [x] **2.4 Chat Endpoint (#33):** Connect `/api/chat` to the AI engine.
- [x] **2.5 Testing (#34):** BDD scenarios for SQL generation accuracy (15 scenarios + 53 unit tests).
- [x] **2.6 Verification - MCP (#40):** Configure Neon MCP in Cursor for query sanity-checking.

## Phase 3: Frontend MVP (COMPLETED ✅)
- [x] **3.1 Zustand Store (#42):** Chat state management with localStorage persistence.
- [x] **3.2 Chat UI Components (#43):** ChatContainer, ChatInput, MessageList, MessageBubble.
- [x] **3.3 Data Visualizer (#44):** Recharts implementation for Bar/Line/Table charts.
- [x] **3.4 API Integration (#47):** Frontend-to-Backend communication with error handling.
- [x] **3.5 Local Storage & UX (#45):** Enhanced persistence and UI improvements (Backup system implemented).

## MVP Status: COMPLETED ✅

**Fecha de finalización:** Enero 2025

**Resumen del MVP:**
- ✅ Pipeline ETL completo con ingesta diaria automática
- ✅ Backend con motor Text-to-SQL y RAG implementado
- ✅ Frontend completo con visualizaciones interactivas
- ✅ Sistema de persistencia y UX mejorado
- ✅ Documentación completa y actualizada

**Próximos pasos:** Ver Phase 4 (Post-MVP / Pro Features)

## Phase 4: Post-MVP / Pro Features (FUTURE)
- [ ] **4.1 Game-Level Data Pipeline:** Extender ETL para ingerir estadísticas detalladas por partido (box scores, shooting data, play-by-play). Implementar modelos de datos para `player_game_stats` y `games` con soporte multi-temporada.
- [ ] **4.2 Spatial Analytics & Visualizations:** Implementar visualizaciones espaciales avanzadas mediante PostGIS (shot charts, heatmaps, court positioning). Integrar análisis de zonas de tiro y eficiencia espacial.
- [ ] **4.3 Automated Game Analysis:** Sistema de generación automática de resúmenes y análisis de partidos concretos usando LLM, extrayendo insights clave de estadísticas y eventos del juego.
- [ ] **4.4 Monetization & Infrastructure:** Implementar sistema de monetización (freemium/pro tiers) para costear infraestructura, APIs externas y escalabilidad. Incluir rate limiting, autenticación y gestión de suscripciones.