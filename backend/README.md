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
│   └── routers/         # Endpoints API
├── etl/                 # Scripts ETL
├── tests/               # Tests BDD
└── pyproject.toml       # Poetry config
```


