"""
ETL Pipeline Documentation - Euroleague Data Ingestion

Este documento describe el sistema completo de ETL (Extract, Transform, Load)
que mantiene la base de datos poblada con datos de Euroleague.
"""

# ETL Pipeline - Euroleague AI Stats System

## Overview

El ETL Pipeline automático ejecuta diariamente a las **7 AM UTC** y realiza las siguientes operaciones:

1. **Extract:** Obtiene datos de [euroleague_api](https://github.com/giasemidis/euroleague_api)
2. **Transform:** Normaliza datos y mapea códigos de equipos/jugadores
3. **Load:** Inserta/actualiza datos en PostgreSQL (Neon)

## Arquitectura

```
euroleague_api (GitHub)
    ↓ (Diariamente 7 AM UTC)
ETL Pipeline (backend/etl/)
    ├── ingest_teams.py        → teams
    ├── ingest_players.py      → players
    └── ingest_player_season_stats.py → player_season_stats
    ↓
Neon PostgreSQL (BD)
    ├── teams (18 equipos Euroleague)
    ├── players (500+ jugadores)
    └── player_season_stats (estadísticas agregadas)
```

## Componentes

### 1. Scripts ETL

#### `etl/ingest_teams.py`
- **Función:** Obtiene lista de equipos de Euroleague
- **Origen:** `EuroleagueData().get_standings()`
- **Campos:** code, name, logo_url
- **Idempotencia:** UPSERT (crea o actualiza)

```bash
# Ejecución manual
cd backend
poetry run python etl/ingest_teams.py
```

#### `etl/ingest_players.py`
- **Función:** Obtiene jugadores de la temporada actual
- **Origen:** `PlayerStats().get_season_stats()`
- **Campos:** player_code, name, position, team_id, season
- **Mapeo:** Convierte posiciones a español (Base, Escolta, Alero, Ala-Pivot, Pivot)
- **Temporada:** Parametrizable (default: 2025)

```bash
cd backend
poetry run python etl/ingest_players.py  # Temporada 2025
```

#### `etl/ingest_player_season_stats.py`
- **Función:** Obtiene estadísticas agregadas por temporada
- **Origen:** `PlayerStats().get_season_stats()`
- **Campos:** points, rebounds, assists, steals, blocks, turnovers, threePointsMade, pir
- **Temporada:** Parametrizable (default: 2025)

```bash
cd backend
poetry run python etl/ingest_player_season_stats.py  # Temporada 2025
```

### 2. Script Orquestador

#### `scripts/run_etl.py`
- **Función:** Ejecuta todos los ETLs en orden correcto
- **Orden:** teams → players → stats
- **Manejo de errores:** Falla rápido (fail-fast)
- **Logging:** Detallado con timestamps

```bash
cd backend
poetry run python scripts/run_etl.py        # Temporada 2025
poetry run python scripts/run_etl.py 2024  # Temporada 2024
```

### 3. Script de Inicialización

#### `scripts/init_db.py`
- **Función:** Crea tablas de BD (migraciones idempotentes)
- **Ejecución:** Una sola vez al desplegar
- **Verificación:** Comprueba que las tablas existen

```bash
cd backend
poetry run python scripts/init_db.py
```

### 4. Migraciones SQL

#### `migrations/001_create_tables.sql`
- **Función:** Define esquema de tablas
- **Idempotencia:** Todas usan `CREATE TABLE IF NOT EXISTS`
- **Índices:** Optimizados para queries típicas

Tablas:
- `teams` (18 equipos)
- `players` (500+ jugadores por temporada)
- `player_season_stats` (estadísticas agregadas)

## Scheduling

### GitHub Actions (Automático)

El workflow `.github/workflows/etl-sync.yml` ejecuta:

- **Cuándo:** Todos los días a las 7:00 AM UTC
- **Acciones:**
  1. Checkout del código
  2. Setup Python 3.11 + Poetry
  3. Instalación de dependencias
  4. Inicialización de BD (`init_db.py`)
  5. Ejecución de ETL (`run_etl.py`)
  6. Verificación de integridad
  7. Notificación a Slack (éxito/fallo)

**Ejecución manual:**
```
GitHub → Actions → "ETL Pipeline - Euroleague Data Sync" → Run workflow
```

### Configuración Requerida

En GitHub → Settings → Secrets:

```
DATABASE_URL        = postgresql+asyncpg://user:pass@host/db
SLACK_WEBHOOK_URL   = https://hooks.slack.com/...  (opcional)
```

## Normalización Unicode

El sistema maneja automáticamente tildes y acentos en búsquedas:

```python
# Usuario pregunta: "llull" (sin tilde)
# Jugador en BD: "Llúll" (con tilde)
# Resultado: ✓ Se encuentra al jugador

# Función: normalize_text_for_matching()
# Input: "Llúll"
# Output: "llull" (para búsqueda)
# Retorna: "Llúll" (nombre original como lo devuelve la API)
```

### Funcionalidad

La normalización Unicode ocurre en `app/services/text_to_sql.py`:

```python
from app.services.text_to_sql import normalize_text_for_matching

texto = "José María Pérez"
normalizado = normalize_text_for_matching(texto)
# Resultado: "jose maria perez"
```

## Flujo de una Consulta de Estadísticas

```
1. Usuario: "máximos anotadores del Real Madrid"
   ↓
2. Frontend envía a backend: POST /api/chat
   ↓
3. text_to_sql.generate_sql():
   - Detecta como stats query: ✓
   - Detecta como games query: ✗
   - Extrae parámetros:
     * seasoncode: "E2025"
     * stat: "points"
     * top_n: 10
     * team_code: "RM"
   ↓
4. text_to_sql._get_player_stats_from_db():
   SELECT player_season_stats.* FROM player_season_stats
   JOIN players ON ...
   JOIN teams ON ...
   WHERE season = 'E2025'
   AND teams.code = 'RM'
   ORDER BY points DESC
   LIMIT 10
   ↓
5. Retorna datos directamente (sin LLM)
   ↓
6. Frontend renderiza BarChart
```

## Caché Frontend

Para temporadas pasadas (no la actual), el frontend usa localStorage:

```javascript
// Usuario pregunta: "máximos anotadores de 2024"
// Backend: "No hay datos de 2024 en la BD"
// Frontend: Cachea en localStorage
// Futuras consultas de 2024: Usan la caché local (no se refrescan)

// localStorage key: 'euroleague-cache-2024'
```

## Validación y Testing

### BDD Specs

```bash
cd backend
poetry run pytest tests/features/etl_pipeline.feature -v
```

**Scenarios cubiertos:**
- Ingesta de equipos (18 equipos mínimo)
- Ingesta de jugadores (posiciones válidas)
- Ingesta de estadísticas (campos correctos)
- Pipeline completo en orden
- Detección de queries de stats
- Rechazo de queries de partidos
- Normalización Unicode

### Verificación Manual

```bash
cd backend

# Verificar tablas existen
poetry run python scripts/init_db.py

# Ejecutar ETL
poetry run python scripts/run_etl.py

# Consultar datos
poetry run python -c "
import asyncio
from app.database import async_session_maker
from app.models import Team, Player, PlayerSeasonStats
from sqlalchemy import select

async def check():
    async with async_session_maker() as session:
        teams = await session.execute(select(Team))
        print(f'Teams: {len(teams.scalars().all())}')
        
asyncio.run(check())
"
```

## Troubleshooting

### Error: "No se conecta a euroleague_api"

```bash
# Verificar conexión
poetry run python -c "
from euroleague_api.euroleague_data import EuroleagueData
data = EuroleagueData()
print(data.get_standings(season=2025, competition_code='E'))
"
```

### Error: "Base de datos vacía después de ETL"

```bash
# Verificar DATABASE_URL
echo $DATABASE_URL

# Verificar conexión a BD
poetry run python -c "
import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def check():
    async with async_session_maker() as session:
        result = await session.execute(text('SELECT 1'))
        print('✓ BD conectada')

asyncio.run(check())
"
```

### Error: "player_code duplicado"

El ETL intenta hacer UPSERT. Si hay conflictos:

```bash
# Limpiar datos
poetry run python -c "
import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def clean():
    async with async_session_maker() as session:
        await session.execute(text('DELETE FROM player_season_stats'))
        await session.execute(text('DELETE FROM players'))
        await session.execute(text('DELETE FROM teams'))
        await session.commit()

asyncio.run(clean())
"

# Reintentar ETL
poetry run python scripts/run_etl.py
```

## Monitoreo

### Logs

```bash
# Ver últimos logs de ETL
docker logs euroleague-backend  # Si está en contenedor
journalctl -n 100 -f            # Si está en servidor Linux
```

### Slack Notifications

El workflow envía notificaciones automáticas:

```
✓ ETL Pipeline - Success
Database: Updated
Teams: Synced
Players: Synced
Season Stats: Synced
```

## Próximos Pasos

### Fase 2 (Futuro)

1. **Consultas por partido individual**
   - Tabla: `games`, `player_stats_games`
   - ETL: Descargar box scores históricos
   - Queries: "Partidos de Larkin con >10 puntos"

2. **Análisis temporal**
   - Evolución de stats por jornada
   - Tendencias en temporada

3. **Shot charts**
   - Integración con PostGIS (`pgvector`)
   - Visualización de posiciones de tiro

## Contacto

Para issues o mejoras del ETL:
- Crear issue en GitHub
- Tag: `etl`, `database`, `euroleague-api`

