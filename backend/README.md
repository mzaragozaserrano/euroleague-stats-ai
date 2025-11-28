# Euroleague AI Backend

Backend API para el sistema Text-to-SQL de estadísticas de la Euroliga.

## Requisitos

- Python 3.11+
- Poetry
- PostgreSQL con extensión pgvector (Neon)

## Setup

1. Instalar dependencias:
```bash
poetry install
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

**Configuración de Neon (Base de Datos):**
- El archivo `.env` ya está configurado con la URL de Neon
- **IMPORTANTE**: La URL debe usar el formato `postgresql+asyncpg://` (no `postgresql://`)
- **IMPORTANTE**: Usar `ssl=require` en lugar de `sslmode=require` para asyncpg
- Si obtienes la URL directamente de Neon, cambia:
  - `postgresql://` → `postgresql+asyncpg://`
  - `sslmode=require` → `ssl=require`
- Ejemplo: `postgresql+asyncpg://user:pass@ep-xxx.aws.neon.tech/dbname?ssl=require`

**Probar conexión a Neon:**
```bash
poetry run python scripts/test_db_connection.py
```

3. Ejecutar servidor de desarrollo:
```bash
poetry run uvicorn app.main:app --reload
```

La API estará disponible en http://localhost:8000

## Documentación

Swagger UI: http://localhost:8000/docs (solo en development)

## Testing

### Todos los Tests
```bash
poetry run pytest -v
```

### Tests BDD (Phase 2.5)
```bash
# Tests de RAG SQL Generation (15 scenarios)
poetry run pytest tests/step_defs/test_rag_steps.py -v

# Tests BDD del Pipeline de ETL
poetry run pytest tests/features/ -v
```

### Unit Tests (Phase 2)
```bash
# Tests del servicio Text-to-SQL
poetry run pytest tests/test_text_to_sql_service.py -v

# Tests del servicio de Vectorización
poetry run pytest tests/test_vectorization_service.py -v
```

### Cobertura
```bash
poetry run pytest tests/ --cov=app/services --cov-report=term-missing
```

**Status:** 68+ tests pasados (15 BDD + 53 unit) ✅

## Linting

```bash
poetry run ruff check .
poetry run black .
```

## Servicios de IA (Phase 2)

### 1. Text-to-SQL Service (Phase 2.3)

Convierte consultas en lenguaje natural a SQL válido usando LLM (OpenRouter).

**Características:**
- Validación de SQL Safety contra inyecciones (DROP/DELETE/UPDATE/INSERT)
- Few-shot prompting con ejemplos de queries complejas
- Reintentos automáticos con exponential backoff
- Retorna JSON estructurado: `{sql, visualization_type, error?}`

**Uso:**
```python
from app.services.text_to_sql import TextToSQLService

service = TextToSQLService(api_key="sk-...")

sql, viz_type, error = await service.generate_sql(
    query="Top 5 jugadores con más puntos",
    schema_context="Tables: players, player_stats_games, teams",
    conversation_history=[]  # Para contexto multiturno
)
```

### 2. Vectorización de Esquema (RAG) (Phase 2.1 & 2.2)

### Descripción

El módulo de vectorización genera embeddings para metadatos de esquema (descripciones de tablas, columnas y ejemplos SQL) usando OpenAI `text-embedding-3-small`. Estos embeddings se almacenan en PostgreSQL con pgvector y se usan para recuperar esquema relevante mediante búsqueda de similitud (cosine similarity).

### Flujo

1. **Generación**: `VectorizationService.generate_embedding()` crea embeddings de 1536 dimensiones
2. **Almacenamiento**: Los embeddings se insertan en la tabla `schema_embeddings`
3. **Recuperación**: `retrieve_relevant_schema()` realiza búsqueda de similitud para encontrar esquema relevante

### Uso

**Inicializar embeddings (una vez):**
```bash
poetry run python scripts/init_embeddings.py
```

Este script:
- Limpia embeddings anteriores
- Vectoriza 15+ items de metadatos (tablas, columnas, ejemplos SQL)
- Valida que se insertaron correctamente
- Realiza búsqueda de prueba para verificar que se pueden recuperar

**En código:**
```python
from app.services.vectorization import VectorizationService
from app.database import async_session_maker

service = VectorizationService(api_key="sk-...")

async with async_session_maker() as session:
    # Generar embedding individual
    embedding = await service.generate_embedding("my text")
    
    # Vectorizar lote de metadatos
    count = await service.vectorize_schema_metadata(session, metadata_list)
    
    # Recuperar esquema relevante
    results = await service.retrieve_relevant_schema(
        session, 
        "puntos de Larkin vs Micic",
        limit=5
    )
    # Retorna: [{"id": "...", "content": "...", "similarity": 0.85}, ...]
```

### Variables de Entorno Requeridas

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?ssl=require
OPENAI_API_KEY=sk-...
```

### Tests BDD

```bash
poetry run pytest tests/features/schema_embeddings.feature -v
```

## Estructura

```
backend/
├── app/
│   ├── main.py                  # Entry point
│   ├── config.py                # Configuración
│   ├── database.py              # SQLAlchemy setup
│   ├── models/                  # Modelos ORM
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Lógica de negocio (Phase 2)
│   │   ├── text_to_sql.py       # Text-to-SQL Service (#32)
│   │   └── vectorization.py     # RAG Vectorization Service (#30)
│   └── routers/                 # Endpoints API
│       ├── health.py            # GET /health
│       └── chat.py              # POST /api/chat (#33)
├── etl/                         # Scripts ETL
├── scripts/
│   ├── init_embeddings.py       # Inicializar schema embeddings
│   └── ...
├── tests/                       # Tests BDD + Unit Tests (Phase 2.5)
│   ├── features/
│   │   ├── schema_embeddings.feature      # Scenarios
│   │   ├── rag_sql_generation.feature    # 15 Scenarios SQL Gen (#34)
│   │   └── ...
│   ├── step_defs/
│   │   ├── test_rag_steps.py            # 15 BDD scenarios (#34)
│   │   └── ...
│   ├── test_text_to_sql_service.py       # 27 Unit tests (#34)
│   ├── test_vectorization_service.py     # 11 Unit tests (#34)
│   └── conftest.py
└── pyproject.toml               # Poetry config
```

**Phase Completion:**
- ✅ Phase 1: ETL Pipeline (Completed - Enero 2025)
- ✅ Phase 2: Backend & AI Engine (Completed - Enero 2025)
  - Vectorization (#30), RAG (#31), Text-to-SQL (#32), Chat Endpoint (#33), Testing (#34)
- 🚧 Phase 3: Frontend (In Progress)


