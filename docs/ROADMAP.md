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

## Phase 2: Backend & AI Engine (CURRENT FOCUS 🚧)
- [ ] **2.1 Vectorization:** Script to generate embeddings for Table/Column descriptions.
- [ ] **2.2 RAG Service:** Implement `retrieve_relevant_schema`.
- [ ] **2.3 Text-to-SQL Service:** Prompt engineering & LLM integration (OpenRouter).
- [ ] **2.4 Chat Endpoint:** Connect `/api/chat` to the AI engine.
- [ ] **2.5 Testing:** BDD scenarios for SQL generation accuracy.

## Phase 3: Frontend MVP (Next Up)
- [ ] Chat Interface (Zustand store, UI Components).
- [ ] Data Visualizer (Recharts implementation for Bar/Line/Table).
- [ ] Integration with Backend API.
- [ ] Deployment to Render.

## Phase 4: Post-MVP / Pro Features
- [ ] Spatial SQL (PostGIS) for Shot Charts.
- [ ] Authentication / Monetization.