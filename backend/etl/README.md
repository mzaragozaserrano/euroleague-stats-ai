# Scripts ETL - Guía de Uso

Este directorio contiene los scripts ETL para ingerir datos desde la API de Euroleague a la base de datos Neon.

## Scripts Disponibles

1. **`ingest_teams.py`** - Ingesta de equipos
2. **`ingest_players.py`** - Ingesta de jugadores
3. **`ingest_games.py`** - Ingesta de partidos y estadísticas de jugadores

## Prerrequisitos

1. **Variables de entorno configuradas:**
   ```bash
   # En backend/.env
   DATABASE_URL=postgresql+asyncpg://user:password@host/dbname?ssl=require
   ```

2. **Base de datos preparada:**
   - Ejecutar migraciones: `backend/migrations/001_initial_schema.sql`
   - Verificar que la extensión `pgvector` esté habilitada

## Ejecución Manual

### Opción 1: Ejecutar scripts individuales

```bash
cd backend

# 1. Ingestar equipos (debe ejecutarse primero)
poetry run python -m etl.ingest_teams

# 2. Ingestar jugadores (requiere equipos)
poetry run python -m etl.ingest_players

# 3. Ingestar partidos (requiere equipos y jugadores)
poetry run python -m etl.ingest_games
```

### Opción 2: Ejecutar todos los ETLs en secuencia

```bash
cd backend

# Script completo (equipos → jugadores → partidos → estadísticas)
poetry run python -m etl.ingest_teams && \
poetry run python -m etl.ingest_players && \
poetry run python -m etl.ingest_games
```

### Opción 3: Usar Python interactivo

```python
import asyncio
from etl.ingest_teams import ingest_teams
from etl.ingest_players import ingest_players
from etl.ingest_games import ingest_games, ingest_player_stats

async def run_all_etl():
    # 1. Equipos
    print("Ingestando equipos...")
    teams_result = await ingest_teams()
    print(f"Equipos: {teams_result}")
    
    # 2. Jugadores
    print("Ingestando jugadores...")
    players_result = await ingest_players()
    print(f"Jugadores: {players_result}")
    
    # 3. Partidos
    print("Ingestando partidos...")
    games_result = await ingest_games()
    print(f"Partidos: {games_result}")
    
    # 4. Estadísticas de jugadores
    print("Ingestando estadísticas...")
    stats_result = await ingest_player_stats()
    print(f"Estadísticas: {stats_result}")

# Ejecutar
asyncio.run(run_all_etl())
```

## Orden de Ejecución

**IMPORTANTE:** Los ETLs deben ejecutarse en este orden debido a las dependencias de claves foráneas:

1. ✅ **Equipos** (sin dependencias)
2. ✅ **Jugadores** (requiere equipos)
3. ✅ **Partidos** (requiere equipos)
4. ✅ **Estadísticas de Jugadores** (requiere partidos, jugadores y equipos)

## Parámetros Opcionales

Los scripts aceptan parámetros opcionales para filtrar por temporada o jornada:

```python
# Filtrar por temporada
await ingest_players(season=2023)
await ingest_games(season=2023)

# Filtrar por temporada y jornada
await ingest_games(season=2023, round_=1)
await ingest_player_stats(season=2023, round_=1)
```

## Verificación

Después de ejecutar los ETLs, puedes verificar los datos:

```sql
-- Verificar equipos
SELECT COUNT(*) FROM teams;

-- Verificar jugadores
SELECT COUNT(*) FROM players;

-- Verificar partidos
SELECT COUNT(*) FROM games;

-- Verificar estadísticas
SELECT COUNT(*) FROM player_stats_games;
```

## Troubleshooting

### Error: "Team does not exist"
- **Causa:** Se intentó ingestar jugadores o partidos antes de equipos
- **Solución:** Ejecutar `ingest_teams.py` primero

### Error: "Player does not exist"
- **Causa:** Se intentó ingestar estadísticas antes de jugadores
- **Solución:** Ejecutar `ingest_players.py` antes de `ingest_player_stats()`

### Error: "Connection timeout"
- **Causa:** Problemas de conexión con Neon o la API
- **Solución:** Verificar `DATABASE_URL` y conexión a internet

### Error: "Rate limit exceeded"
- **Causa:** Demasiadas solicitudes a la API de Euroleague
- **Solución:** Esperar unos minutos y reintentar

## Automatización

Los ETLs también se ejecutan automáticamente mediante GitHub Actions:

- **Workflow:** `.github/workflows/etl_daily.yml`
- **Frecuencia:** Diario a las 8 AM UTC
- **Ejecución manual:** Disponible desde GitHub Actions UI

## Logs

Los scripts generan logs detallados con información sobre:
- Número de registros procesados
- Registros insertados vs actualizados
- Errores encontrados
- Estadísticas finales
