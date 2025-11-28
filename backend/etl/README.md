# ETL - Ingesta de Datos de Euroleague

Este directorio contiene los scripts y utilidades para la ingesta de datos desde la API oficial de Euroleague.

## Estructura

```
etl/
├── __init__.py                  # Exportaciones del módulo
├── euroleague_client.py         # Cliente HTTP para la API de Euroleague
├── README.md                    # Este archivo
```

## EuroleagueClient

Cliente HTTP robusto para consumir la API oficial de Euroleague.

### Características

- **Autenticación**: Soporte para API keys (si es requerido por la API)
- **Reintentos Automáticos**: Reintentos exponenciales en errores temporales (500, 502, 503, 504, 408, 429)
- **Manejo de Errores**: Excepciones específicas para diferentes tipos de errores
- **Rate Limiting**: Detección y manejo de límites de tasas (HTTP 429)
- **Timeouts**: Configuración de timeouts con manejo de excepciones
- **Logging**: Logging detallado para debugging

### Uso Básico

```python
import asyncio
from etl import EuroleagueClient

async def main():
    client = EuroleagueClient()
    
    # Obtener equipos
    teams = await client.get_teams()
    
    # Obtener jugadores
    players = await client.get_players()
    
    # Obtener partidos de una temporada específica
    games = await client.get_games(season=2024)
    
    # Obtener estadísticas de jugadores
    stats = await client.get_playerstats(season=2024, round_=1)

asyncio.run(main())
```

### API Disponible

#### Métodos Públicos

- `get_teams()`: Obtener lista de equipos
- `get_players(season=None)`: Obtener lista de jugadores
- `get_games(season=None, round_=None)`: Obtener lista de partidos
- `get_playerstats(season=None, round_=None)`: Obtener estadísticas de jugadores
- `get_standings(season=None)`: Obtener clasificaciones
- `get_teamstats(season=None, round_=None)`: Obtener estadísticas de equipos
- `get_endpoint_url(endpoint_name)`: Obtener URL completa de un endpoint

#### Parámetros de Constructor

```python
client = EuroleagueClient(
    api_key="tu_api_key",           # Opcional: API key si la API lo requiere
    base_url="https://...",         # Opcional: URL base personalizada
    timeout=30                       # Opcional: timeout en segundos
)
```

### Excepciones

- `EuroleagueClientError`: Excepción base para errores del cliente
- `EuroleagueAPIError`: Error en la respuesta de la API
- `EuroleagueRateLimitError`: Se excedió el límite de tasas
- `EuroleagueTimeoutError`: Timeout en la solicitud

### Ejemplo Completo

```python
import asyncio
import logging
from etl import (
    EuroleagueClient,
    EuroleagueAPIError,
    EuroleagueRateLimitError,
)

logging.basicConfig(level=logging.INFO)

async def fetch_season_data(season: int):
    client = EuroleagueClient()
    
    try:
        # Obtener datos de la temporada
        teams = await client.get_teams()
        players = await client.get_players(season=season)
        games = await client.get_games(season=season)
        stats = await client.get_playerstats(season=season)
        
        print(f"Temporada {season}:")
        print(f"  - Equipos: {len(teams.get('Teams', []))}")
        print(f"  - Jugadores: {len(players.get('Players', []))}")
        print(f"  - Partidos: {len(games.get('Games', []))}")
        print(f"  - Registros de estadísticas: {len(stats.get('PlayerStats', []))}")
        
        return {
            'teams': teams,
            'players': players,
            'games': games,
            'stats': stats
        }
        
    except EuroleagueRateLimitError:
        print("Se alcanzó el límite de tasas. Espera antes de reintentar.")
    except EuroleagueAPIError as e:
        print(f"Error en la API: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

asyncio.run(fetch_season_data(2024))
```

### Configuración

#### Variables de Entorno

Si tu API de Euroleague requiere autenticación, configura:

```bash
EUROLEAGUE_API_KEY=tu_clave_de_api
```

Uso en código:

```python
import os
from etl import EuroleagueClient

api_key = os.getenv("EUROLEAGUE_API_KEY")
client = EuroleagueClient(api_key=api_key)
```

#### Logging

El cliente utiliza el módulo `logging` estándar de Python. Para ver logs detallados:

```python
import logging

# Configurar nivel DEBUG para ver logs detallados
logging.basicConfig(level=logging.DEBUG)
```

### Detalles Técnicos

#### Reintentos

El cliente implementa reintentos exponenciales para errores temporales:

- Códigos de estado reintentables: 408, 429, 500, 502, 503, 504
- Máximo de reintentos: 3
- Factor de backoff: 0.5 segundos
- Espera máxima entre reintentos: 10 segundos

Fórmula de espera: `min(0.5 * 2^(intento-1), 10)`

#### Timeouts

Por defecto, las solicitudes tienen un timeout de 30 segundos. Se puede personalizar:

```python
client = EuroleagueClient(timeout=60)  # 60 segundos
```

#### Headers

El cliente envía los siguientes headers por defecto:

```
User-Agent: EuroleagueStatsAI/1.0
Accept: application/json
X-API-Key: <tu_api_key> (si se proporciona)
```

### Pruebas

Para probar el cliente:

```bash
# Script de prueba
python backend/scripts/test_euroleague_client.py

# Pruebas BDD (si están implementadas)
pytest -v backend/tests/features/euroleague_client.feature
```

### API Reference de Euroleague

La API oficial de Euroleague está documentada en:
https://api-live.euroleague.net/swagger/index.html

Endpoints disponibles:
- `/v3/teams` - Información de equipos
- `/v3/players` - Información de jugadores
- `/v3/games` - Información de partidos
- `/v3/playerstats` - Estadísticas de jugadores (box scores)
- `/v3/standings` - Clasificaciones
- `/v3/teamstats` - Estadísticas de equipos

### Notas Importantes

1. **Rate Limiting**: La API de Euroleague puede tener límites de tasas. El cliente los maneja automáticamente, pero se recomienda implementar caché para datos que no cambian frecuentemente.

2. **Temporadas**: El formato de temporada es `E<año>` (ej: `E2024` para la temporada 2023-2024).

3. **Jornadas**: Los números de jornada son valores numéricos (1, 2, 3, etc.).

4. **Datos Vacíos**: Algunos endpoints pueden devolver respuestas vacías en ciertas condiciones. El cliente no genera errores en estos casos.

### Roadmap

- Implementar caché local para datos estáticos
- Soporte para paginación
- Compresión de respuestas
- Batching de solicitudes
- Monitoring y métricas

---

Para más información, consulta `docs/TECHNICAL_PLAN.md` y `docs/BLUEPRINT.md`.

