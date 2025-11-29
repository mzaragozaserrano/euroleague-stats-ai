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

```bash
poetry run pytest -v
```

## Linting

```bash
poetry run ruff check .
poetry run black .
```

## Vectorización de Esquema (RAG)

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

## Model Context Protocol (MCP) - Cursor Integration

### Descripción

MCP permite que Cursor acceda directamente a la base de datos Neon para inspeccionar el esquema y ejecutar queries de verificación sin salir del editor. Útil para:
- Inspeccionar tablas y columnas en tiempo de desarrollo
- Verificar queries antes de integrarlas en el código
- Ejecutar consultas de prueba contra datos reales

### Configuración (Automática)

MCP está configurado en `.cursor/mcp.json` con:
- **Conexión**: Neon PostgreSQL database
- **Operaciones permitidas**: SELECT y EXPLAIN (solo lectura)
- **Operaciones bloqueadas**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
- **Timeout**: 5 segundos por query
- **Límite de filas**: 1000 registros máximo

### Uso en Cursor

1. Abrir **Cursor Composer** o **Chat**
2. Usar `@mcp` para acceder a la base de datos
3. Ejemplo: "Dame el esquema de la tabla `players`" → Cursor ejecutará queries verificadas automáticamente

### Queries de Verificación

Ver `tests/mcp_verification_queries.sql` para 10 queries de prueba que validan:
- Conectividad a Neon
- Acceso a tablas de datos
- Búsqueda de similitud (pgvector)
- Rendimiento de indexes

## Estructura

```
backend/
├── app/
│   ├── main.py          # Entry point
│   ├── config.py        # Configuración
│   ├── database.py      # SQLAlchemy setup
│   ├── models/          # Modelos ORM
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Lógica de negocio
│   │   └── vectorization.py  # RAG Vectorization Service
│   │   └── text_to_sql.py    # Text-to-SQL Service
│   └── routers/         # Endpoints API
├── etl/                 # Scripts ETL
├── scripts/
│   ├── init_embeddings.py    # Inicializar schema embeddings
│   └── ...
├── tests/               # Tests BDD
│   ├── features/
│   │   ├── schema_embeddings.feature
│   │   ├── chat_endpoint.feature
│   │   └── ...
│   ├── step_defs/
│   │   └── test_schema_embeddings_steps.py
│   └── mcp_verification_queries.sql  # Queries para MCP testing
└── pyproject.toml       # Poetry config
```


