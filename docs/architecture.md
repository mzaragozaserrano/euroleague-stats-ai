# Architecture & Tech Spec

## 1. Tech Stack Details
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, Shadcn/ui, Recharts.
- **Backend:** Python 3.11+ (FastAPI), Poetry (Dependency Mgmt).
- **Database:** Neon (Serverless PostgreSQL 16) + `pgvector`.
- **ORM:** SQLAlchemy (Async) + `asyncpg`.
- **AI/LLM:**
    - **OpenAI API**: Usado para embeddings (`text-embedding-3-small`) y corrección de consultas (input).
    - **OpenRouter**: Usado para generación de SQL (output) con modelo `openai/gpt-3.5-turbo`.
    - **RAG (Retrieval Augmented Generation)**: Sistema implementado con fallback a esquema hardcodeado.

## 2. Project Structure (Monorepo)
```text
root/
├── backend/
│   ├── app/           # FastAPI Source
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Text-to-SQL, Vectorization, Response Generator
│   │   └── models/    # SQLAlchemy models
│   ├── etl/           # Scripts de Ingesta (Teams, Players, Stats)
│   ├── migrations/    # SQL migrations (incluye schema_embeddings)
│   ├── scripts/       # Utilidades (init_schema_embeddings, test_rag_usage)
│   └── tests/         # BDD (pytest-bdd)
├── frontend/          # Next.js Source
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utilidades (localStorageBackup, checkLegacyData)
│   └── stores/        # Zustand stores (chatStore)
├── data/              # Local storage (git ignored)
└── .github/           # CI/CD & ETL Workflows
```

## 3. Data Model (Schema)

### Tablas de Producción:

- **`teams`**: `id`, `code`, `name`, `logo_url`.
  - Actualización: Diaria (8 AM UTC) vía ETL automático desde API Euroleague.
  - **Datos actuales**: Solo temporada 2025.

- **`players`**: `id`, `player_code`, `team_id`, `name`, `position`, `season`.
  - Campo clave: `player_code` (código de Euroleague API).
  - Campo `season`: Código de temporada (E2025, E2024, etc.).
  - Actualización: Diaria (8 AM UTC) vía ETL automático.
  - **Datos actuales**: Solo temporada E2025.

- **`player_season_stats`**: `id`, `player_id`, `season`, `games_played`, `points`, `rebounds`, `assists`, `threePointsMade`, `pir`.
  - Estadísticas agregadas por temporada (desde API Euroleague vía ETL).
  - Actualización: Diaria (8 AM UTC).
  - **Datos actuales**: Solo temporada E2025.

- **`schema_embeddings`**: `id`, `content`, `embedding` (vector 1536 dimensiones).
  - Descripciones de tablas/columnas y ejemplos SQL para RAG retrieval.
  - Permite que el LLM genere SQL relevante usando búsqueda semántica.
  - Poblado manualmente con `backend/scripts/init_schema_embeddings.py`.

- **`games`**: `id`, `game_code`, `season`, `round`, `date`, `home_team_id`, `away_team_id`, `home_score`, `away_score`.
  - Metadatos de partidos. **NO está poblada actualmente**.

- **`player_game_stats`**: `id`, `game_id`, `player_id`, `team_id`, `minutes`, `points`, `rebounds`, `assists`, `three_points_made`, `pir`.
  - Estadísticas por partido (box score). **NO está poblada actualmente**.

### Almacenamiento Frontend (localStorage):

- **`chat-storage`**: Historial de conversaciones del usuario (persistencia del frontend).
  - Estructura: `{ state: { sessions: [], currentSessionId }, version: 5 }`
  - Versión: 5 (con migración automática desde versiones anteriores).
  - Sistema de backup automático antes de migraciones.
  - Recuperación automática de datos legacy al iniciar la app.
  - Sobrevive a cierres de tab y recargas de página.
  - **NO HAY base de datos embebida en el frontend** (sin IndexedDB, SQLite, u otros).
  - Todos los datos se consultan del backend (Neon PostgreSQL).

## 4. Flujo de Datos

### Arquitectura Actual:

```
API Euroleague (GitHub)
        ↓ (ETL diario 8 AM UTC - Solo temporada 2025)
Backend BD (Neon PostgreSQL)
        ↑ (Text-to-SQL generado por LLM)
Frontend ChatStore
        ↓ (localStorage persistence + backup automático)
Usuario Chat History
```

### Flujo de una Consulta:

1. **Usuario escribe query** en el chat frontend
2. **Frontend envía** `POST /api/chat` con query + historial
3. **Backend procesa:**
   - **Corrección de consulta (OpenAI via OpenRouter)**: Corrige erratas tipográficas (ej: "Campazo" → "Campazzo")
   - **RAG (Retrieval Augmented Generation)**: 
     - Genera embedding de la query usando OpenAI `text-embedding-3-small`
     - Busca esquema relevante en `schema_embeddings` usando cosine similarity
     - Si RAG falla o no está disponible, usa esquema hardcodeado como fallback
   - **Generación de SQL (OpenRouter)**: LLM genera SQL usando contexto de esquema
   - **Ejecución**: Ejecuta SQL contra BD (Neon)
   - **Retorna**: Resultados en JSON con tipo de visualización
4. **Frontend recibe** respuesta y renderiza visualización (BarChart, LineChart, DataTable)
5. **localStorage persiste** el chat para futuras sesiones (con backup automático)

### Uso de OpenAI:

- **Input (Corrección de consultas)**: 
  - Modelo: `openai/gpt-3.5-turbo` via OpenRouter
  - Propósito: Corregir erratas tipográficas y normalizar nombres de jugadores/equipos
  - Ejemplo: "Campazo" → "Campazzo", "Larkyn" → "Larkin"

- **Embeddings (RAG)**:
  - Modelo: `text-embedding-3-small` (1536 dimensiones)
  - Propósito: Generar embeddings de metadatos de esquema y queries del usuario
  - Almacenamiento: PostgreSQL con `pgvector`

- **Output (Generación de SQL)**:
  - Modelo: `openai/gpt-3.5-turbo` via OpenRouter
  - Propósito: Convertir consultas naturales a SQL válido
  - Contexto: Esquema relevante recuperado por RAG

### Limitaciones Actuales:

- ❌ **Base de datos solo contiene datos de temporada 2025** (jugadores, equipos, estadísticas)
- ❌ No se pueden consultar datos a nivel de partido individual (`player_game_stats` no está poblada)
- ❌ Las queries que requieren "partidos específicos" retornan error explicativo
- ✅ Sí se pueden consultar estadísticas agregadas por temporada (`player_season_stats` para E2025)
- ✅ Sí se pueden consultar metadatos (equipos, jugadores, posiciones de temporada 2025)
- ✅ RAG funciona con fallback seguro si OpenAI API key no está configurada

## 5. Critical Constraints
- **Neon Serverless:** MUST use `poolclass=NullPool` in SQLAlchemy engine.
- **Embeddings:** Use API-based embeddings (OpenAI `text-embedding-3-small`) to save RAM on Render.
- **ETL:** Daily Cron via GitHub Actions at 8 AM UTC (Cost: $0). Solo ingiere temporada 2025 por defecto.
- **Base de Datos:** Solo contiene datos de temporada 2025. Otras temporadas no están disponibles.
- **OpenAI API Key:** Requerida para RAG y corrección de consultas. Si no está configurada, el sistema usa fallback (esquema hardcodeado).
- **OpenRouter API Key:** Requerida para generación de SQL. Sin ella, el sistema no puede funcionar.
- **localStorage Limit:** 5-10 MB. Sistema de backup automático antes de migraciones.
- **API Euroleague:** Fuente única de verdad para estadísticas de jugadores (vía ETL diario).

## 6. Testing Strategy
- **Framework:** `pytest-bdd` + `pytest-asyncio`.
- **Workflow:** `.feature` file -> Step Definitions -> Implementation.
- **Cobertura:** Tests para ETL, Text-to-SQL, Chat endpoint, y RAG.

## 7. Sistema de Backup y Recuperación

### Backup Automático (Frontend)
- **Ubicación:** `frontend/lib/localStorageBackup.ts`
- **Funcionalidad:** 
  - Crea backup automático antes de migraciones de `chat-storage`
  - Mantiene últimos 5 backups
  - Permite restaurar backups manualmente desde consola del navegador
- **Funciones disponibles en consola:**
  - `checkLegacyData()`: Verificar y recuperar datos legacy
  - `getBackups()`: Listar backups disponibles
  - `restoreLatestBackup()`: Restaurar backup más reciente

### Recuperación de Datos Legacy
- **Ubicación:** `frontend/lib/checkLegacyData.ts`
- **Funcionalidad:**
  - Detecta automáticamente datos legacy al iniciar la app
  - Convierte formatos antiguos a estructura actual de sesiones
  - Se ejecuta automáticamente en `BackupSystemInit` component

## 8. RAG (Retrieval Augmented Generation)

### Implementación
- **Servicio:** `backend/app/services/vectorization.py`
- **Tabla:** `schema_embeddings` (PostgreSQL con `pgvector`)
- **Modelo de embeddings:** OpenAI `text-embedding-3-small` (1536 dimensiones)
- **Búsqueda:** Cosine similarity usando operador `<=>` de pgvector

### Flujo RAG
1. Usuario envía query natural
2. Se genera embedding de la query usando OpenAI
3. Se busca en `schema_embeddings` los metadatos más relevantes (top 10)
4. Se filtra por similitud mínima (>= 0.3)
5. Se construye contexto de esquema con resultados relevantes
6. Si RAG falla o no hay resultados, se usa esquema hardcodeado como fallback

### Inicialización
- **Script:** `backend/scripts/init_schema_embeddings.py`
- **Contenido:** Metadatos de tablas, columnas, relaciones y ejemplos SQL
- **Ejecución:** Manual (requiere `OPENAI_API_KEY` configurada)

### Fallback
- Si `OPENAI_API_KEY` no está configurada → usa esquema hardcodeado
- Si la tabla `schema_embeddings` está vacía → usa esquema hardcodeado
- Si hay error en la búsqueda → usa esquema hardcodeado
- El sistema siempre funciona, incluso sin RAG configurado