# ROADMAP: Agente de Estadísticas IA de la Euroliga

## Visión General
Este roadmap detalla la implementación técnica del sistema Text-to-SQL para consultas de estadísticas de la Euroliga mediante lenguaje natural. El proyecto está diseñado para operar dentro de los niveles gratuitos de Render y Neon, con un plazo de implementación de 3 semanas.

---

## FASE 0: Scaffolding & Setup
**Objetivo:** Configurar la estructura del monorepo, herramientas de desarrollo y entornos de despliegue.

**Duración Estimada:** 1-2 días

### 0.1 Inicialización del Repositorio y Estructura Base

#### Estructura de Carpetas
```
proyecto/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── config.py            # Configuración (env vars)
│   │   ├── database.py          # SQLAlchemy engine con NullPool
│   │   ├── models/              # Modelos SQLAlchemy
│   │   │   └── __init__.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   └── __init__.py
│   │   ├── services/            # Lógica de negocio
│   │   │   ├── __init__.py
│   │   │   ├── rag_service.py   # Schema retrieval
│   │   │   └── sql_service.py   # Text-to-SQL generation
│   │   └── routers/             # API endpoints
│   │       ├── __init__.py
│   │       ├── health.py
│   │       └── chat.py
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── euroleague_client.py # API client
│   │   ├── ingest_teams.py
│   │   ├── ingest_players.py
│   │   └── ingest_games.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── features/            # Gherkin .feature files
│   │   │   └── .gitkeep
│   │   ├── step_defs/           # pytest-bdd step definitions
│   │   │   └── __init__.py
│   │   └── conftest.py          # pytest fixtures
│   ├── pyproject.toml           # Poetry config
│   ├── poetry.lock
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── api/                 # API routes (proxy opcional)
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── ChatInterface.tsx
│   │   └── DataVisualizer.tsx
│   ├── lib/
│   │   └── utils.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── .env.local.example
├── data/                        # Local data storage (git ignored)
│   └── .gitkeep
├── .github/
│   └── workflows/
│       ├── etl_daily.yml        # Cron job para ETL
│       └── ci.yml               # Tests y linting
├── docs/
│   ├── SPECIFICATIONS.md
│   ├── TECHNICAL_PLAN.md
│   └── ROADMAP.md
├── .gitignore
├── .cursorrules
└── README.md
```

#### Pasos de Ejecución

**1. Configurar Backend con Poetry**
```bash
# Navegar a backend
cd backend

# Inicializar Poetry (Python 3.11+)
poetry init --name euroleague-ai-backend --python "^3.11" --no-interaction

# Añadir dependencias principales
poetry add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg python-dotenv pydantic-settings

# Añadir dependencias de IA
poetry add openai langchain langchain-openai pgvector

# Añadir dependencias de desarrollo y testing
poetry add --group dev pytest pytest-asyncio pytest-bdd httpx ruff black

# Instalar dependencias
poetry install
```

**2. Crear Archivos de Configuración Backend**

`backend/.env.example`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
ENVIRONMENT=development
LOG_LEVEL=INFO
```

`backend/pyproject.toml` (añadir configuración de herramientas):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

**3. Configurar Frontend con Next.js 14**
```bash
# Desde la raíz del proyecto
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# Navegar a frontend
cd frontend

# Instalar shadcn/ui
npx shadcn-ui@latest init --yes

# Instalar dependencias adicionales
npm install recharts zustand
npm install --save-dev @types/node

# Instalar componentes shadcn necesarios
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add table
```

`frontend/.env.local.example`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**4. Configurar Git y .gitignore**

`.gitignore` (raíz):
```
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env
*.log

# Node
node_modules/
.next/
out/
.env.local
.env.production.local

# Data
data/*
!data/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets
*.pem
*.key

# Ignorar archivo específico
docs/MY_ROUTE.md
```

**5. Configurar Base de Datos Neon**
- Crear cuenta en [Neon](https://neon.tech)
- Crear nuevo proyecto "euroleague-ai"
- Habilitar extensión `pgvector`:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
- Copiar connection string a `backend/.env`

**6. Crear Archivos Base de la Aplicación**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, chat
from app.config import settings

app = FastAPI(
    title="Euroleague AI Stats API",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(chat.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

`backend/app/database.py`:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# CRÍTICO: NullPool para Neon Serverless
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.environment == "development"
)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session
```

`backend/app/routers/health.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}
```

`backend/app/routers/chat.py`:
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    sql: str
    data: Any
    visualization: str  # 'bar', 'line', 'table'

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Placeholder - se implementará en Fase 2
    return ChatResponse(
        sql="SELECT 1",
        data=[],
        visualization="table"
    )
```

`frontend/app/page.tsx`:
```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">
        Euroleague AI Stats
      </h1>
      <p className="text-muted-foreground">
        Chat interface coming soon...
      </p>
    </main>
  );
}
```

**7. Configurar GitHub Actions (Estructura Base)**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run linting
        run: poetry run ruff check .
      - name: Run tests
        run: poetry run pytest
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  frontend-build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
```

**8. Verificación del Setup**
```bash
# Backend
cd backend
poetry run uvicorn app.main:app --reload
# Verificar http://localhost:8000/health

# Frontend (en otra terminal)
cd frontend
npm run dev
# Verificar http://localhost:3000
```

### 0.2 Configuración de Render

**Backend (Web Service)**
1. Conectar repositorio GitHub a Render
2. Crear Web Service:
   - Build Command: `cd backend && pip install poetry && poetry install`
   - Start Command: `cd backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.11
3. Añadir variables de entorno desde Render Dashboard

**Frontend (Static Site o Web Service)**
1. Crear Static Site en Render:
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/out`
2. Configurar variable `NEXT_PUBLIC_API_URL` apuntando al backend

### Entregables de Fase 0
- [ ] Estructura de monorepo completa
- [ ] Backend FastAPI ejecutándose localmente con endpoint `/health`
- [ ] Frontend Next.js ejecutándose localmente
- [ ] Poetry configurado con todas las dependencias
- [ ] Base de datos Neon creada con extensión pgvector
- [ ] GitHub Actions configurado (CI básico)
- [ ] Render configurado (sin desplegar aún)

---

## FASE 1: Data Pipeline MVP
**Objetivo:** Implementar ETL básico para ingestar datos de la Euroleague API a Neon DB.

**Duración Estimada:** 4-5 días

### 1.1 Diseño del Esquema de Base de Datos

**Crear migraciones SQL** (`backend/migrations/001_initial_schema.sql`):
```sql
-- Teams
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Players
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    name VARCHAR(100) NOT NULL,
    position VARCHAR(20),
    height INTEGER,
    birth_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Games
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    season VARCHAR(20) NOT NULL,
    round INTEGER NOT NULL,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    date TIMESTAMP NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(season, round, home_team_id, away_team_id)
);

-- Player Stats per Game
CREATE TABLE player_stats_games (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    minutes INTEGER,
    points INTEGER,
    rebounds_total INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    fg2_made INTEGER,
    fg2_attempted INTEGER,
    fg3_made INTEGER,
    fg3_attempted INTEGER,
    ft_made INTEGER,
    ft_attempted INTEGER,
    fouls_drawn INTEGER,
    fouls_committed INTEGER,
    pir DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, player_id)
);

-- Vector Store for RAG (Schema Embeddings)
CREATE TABLE schema_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indices para optimización
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_stats_game ON player_stats_games(game_id);
CREATE INDEX idx_stats_player ON player_stats_games(player_id);
CREATE INDEX idx_embeddings_vector ON schema_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### 1.2 Implementar Modelos SQLAlchemy

**Crear modelos** en `backend/app/models/`:
- `team.py`
- `player.py`
- `game.py`
- `player_stats.py`
- `schema_embedding.py`

### 1.3 Cliente de Euroleague API

**Implementar** `backend/etl/euroleague_client.py`:
- Métodos para obtener teams, players, games, box scores
- Manejo de rate limiting y errores
- Caché opcional para desarrollo

### 1.4 Scripts ETL

**Crear scripts individuales**:
- `backend/etl/ingest_teams.py`: Cargar equipos
- `backend/etl/ingest_players.py`: Cargar jugadores
- `backend/etl/ingest_games.py`: Cargar partidos y estadísticas

**Lógica de Upsert**: Prevenir duplicados usando `ON CONFLICT DO UPDATE`

### 1.5 GitHub Action para ETL Automatizado

**Crear** `.github/workflows/etl_daily.yml`:
```yaml
name: Daily ETL

on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC diario
  workflow_dispatch:  # Permitir ejecución manual

jobs:
  etl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        working-directory: ./backend
        run: poetry install
      - name: Run ETL
        working-directory: ./backend
        run: |
          poetry run python etl/ingest_teams.py
          poetry run python etl/ingest_players.py
          poetry run python etl/ingest_games.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          EUROLEAGUE_API_KEY: ${{ secrets.EUROLEAGUE_API_KEY }}
```

### 1.6 Testing BDD para ETL

**Crear feature** `backend/tests/features/etl.feature`:
```gherkin
Feature: ETL Data Ingestion
  As a system
  I want to ingest Euroleague data
  So that users can query fresh statistics

  Scenario: Ingest teams successfully
    Given the Euroleague API is available
    When I run the teams ETL script
    Then teams should be stored in the database
    And no duplicate teams should exist

  Scenario: Ingest game stats with upsert
    Given a game already exists in the database
    When I ingest the same game again
    Then the game should be updated not duplicated
```

### Entregables de Fase 1
- [ ] Esquema de base de datos completo en Neon
- [ ] Modelos SQLAlchemy para todas las entidades
- [ ] Cliente funcional de Euroleague API
- [ ] Scripts ETL ejecutables manualmente
- [ ] GitHub Action programado y testeado
- [ ] Tests BDD pasando para flujo ETL
- [ ] Base de datos poblada con datos de al menos 1 temporada

---

## FASE 2: Backend & AI Engine
**Objetivo:** Implementar el motor Text-to-SQL con RAG para recuperación de esquema.

**Duración Estimada:** 6-7 días

### 2.1 Vectorización del Esquema (Schema Embeddings)

**Crear** `backend/app/services/embedding_service.py`:
- Función para generar embeddings con OpenAI `text-embedding-3-small`
- Script para vectorizar metadata del esquema:
  - Descripciones de tablas
  - Descripciones de columnas
  - Ejemplos SQL (Few-Shot Learning)

**Ejemplo de contenido a vectorizar**:
```
Table: player_stats_games
Description: Contains box score statistics for each player in each game.
Columns: points (total points scored), assists (number of assists), rebounds_total (offensive + defensive rebounds)
Example Query: SELECT player_id, AVG(points) FROM player_stats_games GROUP BY player_id
```

**Script de inicialización**: `backend/scripts/init_embeddings.py`

### 2.2 Servicio RAG (Schema Retrieval)

**Implementar** `backend/app/services/rag_service.py`:
```python
async def retrieve_relevant_schema(query: str, top_k: int = 3) -> List[str]:
    """
    Convierte la query del usuario a embedding y recupera
    las top_k descripciones de esquema más relevantes.
    """
    # 1. Generar embedding de la query
    # 2. Búsqueda de similitud coseno en schema_embeddings
    # 3. Retornar contenido de los matches
```

### 2.3 Servicio Text-to-SQL

**Implementar** `backend/app/services/sql_service.py`:

**Componentes**:
1. **Prompt Engineering**:
   - System prompt: "Eres un experto en SQL de Postgres para datos de baloncesto de la Euroliga"
   - Context injection: Schema recuperado via RAG
   - Few-shot examples: Queries comunes
   - Output format: JSON con `sql`, `data`, `visualization`

2. **LLM Integration**:
   - Usar OpenAI SDK o LangChain
   - Modelo: GPT-4 Turbo o Claude 3.5 via OpenRouter
   - Manejo de errores y reintentos

3. **SQL Validation**:
   - Validar sintaxis antes de ejecutar
   - Prevenir queries destructivas (DROP, DELETE, UPDATE)
   - Timeout de ejecución

4. **Visualization Logic**:
   - Determinar tipo de visualización basado en la query:
     - Comparación de 2-5 entidades → 'bar'
     - Serie temporal → 'line'
     - Datos tabulares complejos → 'table'

### 2.4 Actualizar Endpoint `/api/chat`

**Modificar** `backend/app/routers/chat.py`:
```python
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Retrieve relevant schema
        schema_context = await retrieve_relevant_schema(request.query)
        
        # 2. Generate SQL with LLM
        sql_result = await generate_sql(
            query=request.query,
            schema=schema_context,
            history=request.history
        )
        
        # 3. Execute SQL
        data = await execute_query(db, sql_result["sql"])
        
        # 4. Return structured response
        return ChatResponse(
            sql=sql_result["sql"],
            data=data,
            visualization=sql_result["visualization"]
        )
    except Exception as e:
        # Manejo elegante de errores
        return ChatResponse(
            sql="",
            data={"error": "No pude procesar tu consulta. Intenta reformularla."},
            visualization="table"
        )
```

### 2.5 Testing BDD para Text-to-SQL

**Crear** `backend/tests/features/text_to_sql.feature`:
```gherkin
Feature: Natural Language to SQL
  As a user
  I want to ask questions in natural language
  So that I can get basketball statistics without knowing SQL

  Scenario: Simple player comparison
    Given the database contains player statistics
    When I ask "Compara puntos de Micic y Larkin esta temporada"
    Then the system should generate valid SQL
    And the SQL should query player_stats_games and players tables
    And the response should include visualization type "bar"
    And the data should contain stats for both players

  Scenario: Temporal trend query
    Given the database contains game history
    When I ask "Evolución de puntos de Campazzo últimos 10 partidos"
    Then the visualization type should be "line"
    And the data should be ordered by date

  Scenario: Ambiguous query handling
    When I ask "Dame estadísticas"
    Then the system should return an error message
    And the error should ask for clarification
```

### 2.6 Seguridad y Optimización

**Implementar**:
- Usuario de base de datos READ-ONLY para queries de usuarios
- Rate limiting en endpoints (FastAPI middleware)
- Caché de queries frecuentes (Redis opcional, o in-memory para MVP)
- Logging estructurado de todas las queries generadas

### Entregables de Fase 2
- [ ] Schema embeddings generados y almacenados
- [ ] Servicio RAG funcional con búsqueda vectorial
- [ ] Servicio Text-to-SQL generando queries válidas
- [ ] Endpoint `/api/chat` completamente funcional
- [ ] Tests BDD pasando para casos de uso principales
- [ ] Manejo robusto de errores y edge cases
- [ ] Documentación de API actualizada

---

## FASE 3: Frontend MVP
**Objetivo:** Construir interfaz de chat y sistema de visualización de datos.

**Duración Estimada:** 5-6 días

### 3.1 Gestión de Estado

**Implementar store con Zustand** (`frontend/lib/store.ts`):
```typescript
interface Message {
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  data?: any;
  visualization?: 'bar' | 'line' | 'table';
}

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Message) => void;
  sendQuery: (query: string) => Promise<void>;
}
```

### 3.2 Componente ChatInterface

**Crear** `frontend/components/ChatInterface.tsx`:

**Características**:
- Input de texto con autocompletado de nombres de jugadores (opcional)
- Manejo de estados: idle, loading, error
- Historial de conversación scrollable
- Mobile-first design (vertical layout)
- Indicador de "typing" mientras el LLM procesa

**UI con shadcn/ui**:
- `<Input>` para query
- `<Button>` para enviar
- `<Card>` para cada mensaje
- `<ScrollArea>` para historial

### 3.3 Componente DataVisualizer

**Crear** `frontend/components/DataVisualizer.tsx`:

**Lógica de renderizado condicional**:
```typescript
interface DataVisualizerProps {
  data: any;
  visualization: 'bar' | 'line' | 'table';
  sql?: string;
}

export function DataVisualizer({ data, visualization, sql }: DataVisualizerProps) {
  if (visualization === 'bar') {
    return <BarChartComponent data={data} />;
  }
  if (visualization === 'line') {
    return <LineChartComponent data={data} />;
  }
  return <TableComponent data={data} />;
}
```

**Subcomponentes con Recharts**:
- `BarChartComponent`: Comparaciones (ej. stats de 2+ jugadores)
- `LineChartComponent`: Tendencias temporales
- `TableComponent`: Datos tabulares (usar shadcn `<Table>`)

### 3.4 Integración con Backend

**Crear** `frontend/lib/api.ts`:
```typescript
export async function sendChatMessage(query: string, history: Message[]) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history })
  });
  
  if (!response.ok) {
    throw new Error('Failed to get response');
  }
  
  return response.json();
}
```

### 3.5 Página Principal

**Actualizar** `frontend/app/page.tsx`:
- Layout centrado con hero section
- Componente `<ChatInterface>` como elemento principal
- Ejemplos de queries sugeridas (chips clickeables)
- Footer con link a documentación

**Diseño Mobile-First**:
- Breakpoints: mobile (default), tablet (md:), desktop (lg:)
- Chat ocupa 100% del viewport en mobile
- Gráficos responsivos (ajustar dimensiones según viewport)

### 3.6 Manejo de Errores y Estados Vacíos

**Implementar**:
- Mensaje de bienvenida cuando no hay historial
- Error boundaries para fallos de renderizado
- Fallback UI cuando el backend está caído
- Mensajes de error user-friendly (no técnicos)

### 3.7 Optimizaciones UX

**Añadir**:
- Debounce en input (evitar requests mientras escribe)
- Botón para copiar SQL generado
- Botón para exportar datos (CSV/JSON)
- Modo oscuro (opcional pero recomendado)
- Animaciones suaves (Framer Motion opcional)

### 3.8 Testing E2E

**Configurar Playwright** (opcional para MVP, recomendado):
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

**Tests básicos**:
- Usuario puede enviar mensaje y recibir respuesta
- Gráficos se renderizan correctamente
- Manejo de errores muestra mensaje apropiado

### Entregables de Fase 3
- [ ] ChatInterface funcional y responsive
- [ ] DataVisualizer renderizando los 3 tipos de visualización
- [ ] Integración completa con backend
- [ ] Manejo robusto de errores
- [ ] UI pulida y mobile-first
- [ ] Queries de ejemplo funcionando end-to-end
- [ ] Aplicación desplegada en Render

---

## POST-MVP: Mejoras Futuras

### Fase 4: Optimizaciones y Analytics (Semana 4)
- Implementar caché de queries con Redis
- Analytics de uso (Posthog o similar)
- Optimización de prompts basada en feedback
- A/B testing de diferentes modelos LLM

### Fase 5: Features Avanzadas (Semana 5-6)
- Shot Charts (visualización espacial)
- Comparaciones multi-jugador (>2 jugadores)
- Filtros temporales avanzados (últimos N juegos, vs equipo X)
- Exportación de reportes en PDF

### Fase 6: Tier Pro (Semana 7-8)
- Sistema de autenticación (Clerk o Auth.js)
- Paywall para estadísticas avanzadas
- API pública con rate limiting por tier
- Dashboard de admin para monitoreo

---

## Métricas de Éxito

### Técnicas
- **Uptime:** >99% en Render free tier
- **Latencia P95:** <3s desde query hasta visualización
- **SQL Success Rate:** >85% de queries generan SQL válido
- **Test Coverage:** >80% en backend, >70% en frontend

### Producto
- **Time-to-Insight:** <5s (objetivo de SPECIFICATIONS.md)
- **Query Success Rate:** >80% de queries devuelven datos útiles
- **Retention D7:** >30% de usuarios vuelven en 7 días
- **Shareability:** Función de compartir implementada y usada

---

## Notas Finales

### Dependencias Críticas
1. **Neon DB:** Configuración correcta de `NullPool` es OBLIGATORIA
2. **OpenAI API:** Monitorear costos de embeddings y completions
3. **Euroleague API:** Verificar rate limits y disponibilidad

### Riesgos y Mitigaciones
| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Euroleague API caída | Alto | Caché local de datos, fallback a última snapshot |
| Costos OpenAI exceden presupuesto | Medio | Rate limiting agresivo, caché de queries comunes |
| SQL injection | Crítico | Validación estricta, usuario DB read-only |
| Render free tier insuficiente | Medio | Optimizar cold starts, considerar upgrade |

### Comandos Útiles

**Backend**
```bash
cd backend
poetry run uvicorn app.main:app --reload  # Dev server
poetry run pytest -v                      # Run tests
poetry run ruff check .                   # Linting
poetry run black .                        # Formatting
```

**Frontend**
```bash
cd frontend
npm run dev          # Dev server
npm run build        # Production build
npm run lint         # Linting
```

**Base de Datos**
```bash
# Conectar a Neon
psql $DATABASE_URL

# Ejecutar migraciones
psql $DATABASE_URL < backend/migrations/001_initial_schema.sql
```

---

**Última actualización:** 2025-11-21  
**Versión:** 1.0.0  
**Mantenedor:** Tech Lead


