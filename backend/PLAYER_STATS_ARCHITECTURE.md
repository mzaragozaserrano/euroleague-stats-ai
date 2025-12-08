# Arquitectura de Estadísticas de Jugadores

## Visión General

Las estadísticas de jugadores se obtienen **en tiempo real** desde la API de Euroleague usando un sistema híbrido con caché inteligente.

## Componentes

### 1. Base de Datos (Permanente)
```
┌─────────────────────────────────┐
│   PostgreSQL (Neon Serverless)  │
├─────────────────────────────────┤
│ - teams (18 equipos)            │
│ - players (350 jugadores)       │
│   └─ player.code (DECK, PAU...) │
│ - schema_embeddings (RAG)       │
└─────────────────────────────────┘
```

**Propósito:** Almacenar roster de equipos y jugadores para obtener los códigos necesarios para llamar a la API.

### 2. Redis Cache (TTL 24h)
```
┌─────────────────────────────────────┐
│         Redis Cache                 │
├─────────────────────────────────────┤
│ Key: "playerstats:E2025"            │
│ Value: {                            │
│   "DECK": {                         │
│     points: 15.2,                   │
│     assists: 3.1,                   │
│     rebounds: 4.5,                  │
│     ...                             │
│   },                                │
│   "PAU": {...},                     │
│   ... (350 jugadores)               │
│ }                                   │
│ TTL: 86400s (24 horas)              │
└─────────────────────────────────────┘
```

**Propósito:** Cachear stats completas de una temporada para evitar llamadas repetidas a la API.

### 3. Euroleague API (Tiempo Real)
```
GET /v1/playerstats?SeasonCode=E2025&PlayerCode=DECK
GET /v1/playerstats?SeasonCode=E2025&PlayerCode=PAU
...
(~350 llamadas por temporada)
```

**Propósito:** Fuente de verdad para estadísticas actualizadas.

## Flujo de Usuario

### Primera Consulta del Día (Cache Miss)

```
Usuario: "Dame los 10 máximos anotadores de la Euroliga 2025"
   ↓
[10:00 AM] Día 1
   ├─ Chat API detecta: consulta de stats
   ├─ PlayerStatsService: ¿Cache hit "playerstats:E2025"? NO
   ├─ Obtener player.codes de BD (DECK, PAU, LLULL, ...)
   ├─ Llamar API Euroleague 350 veces:
   │  GET /v1/playerstats?SeasonCode=E2025&PlayerCode=DECK
   │  GET /v1/playerstats?SeasonCode=E2025&PlayerCode=PAU
   │  ... (progreso cada 50 jugadores)
   ├─ Guardar TODO en Redis: "playerstats:E2025" (TTL 24h)
   ├─ Filtrar top 10 por "points"
   └─ Retornar: [
        {name: "Gabriel Deck", code: "DECK", points: 15.2, ...},
        {name: "Nikola Mirotic", code: "MIROTIC", points: 14.1, ...},
        ...
      ]

Latencia: ~30-60 segundos (350 llamadas API)
```

### Consultas Subsecuentes (Cache Hit)

```
Usuario: "Ahora dame los 10 máximos reboteadores de esta temporada"
   ↓
[10:05 AM] Mismo día
   ├─ Chat API detecta: consulta de stats
   ├─ PlayerStatsService: ¿Cache hit "playerstats:E2025"? SÍ ✓
   ├─ Cargar desde Redis (instantáneo)
   ├─ Filtrar top 10 por "rebounds_total"
   └─ Retornar: [
        {name: "Sasha Vezenkov", code: "VEZENKOV", rebounds_total: 7.2, ...},
        ...
      ]

Latencia: <1 segundo (desde caché)
```

### Distinta Temporada

```
Usuario: "¿Y en la temporada 2024?"
   ↓
[10:10 AM]
   ├─ Chat API detecta: consulta de stats
   ├─ PlayerStatsService: ¿Cache hit "playerstats:E2024"? NO
   ├─ Llamar API Euroleague 350 veces para E2024
   ├─ Guardar en Redis: "playerstats:E2024" (TTL 24h)
   └─ Retornar resultado

Latencia: ~30-60 segundos (nueva temporada)
```

### Día Siguiente (Cache Expirado)

```
[DÍA 2, 10:00 AM]
   ├─ Cache "playerstats:E2025" expiró ✗ (24h pasadas)
   ├─ Usuario: "Top scorers 2025"
   ├─ PlayerStatsService: Cache miss
   ├─ Vuelve a llamar API 350 veces
   ├─ Llena caché nuevamente
   └─ Retornar resultado

Latencia: ~30-60 segundos (caché expirado)
```

## Implementación

### PlayerStatsService

**Ubicación:** `backend/app/services/player_stats_service.py`

**Métodos principales:**

```python
class PlayerStatsService:
    async def get_all_player_stats(seasoncode: str) -> Dict[str, Any]:
        """
        Obtiene stats de TODOS los jugadores para una temporada.
        Usa caché si disponible, sino llama API.
        """
    
    async def search_top_players(
        seasoncode: str,
        stat: str,
        top_n: int,
        team_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca top N jugadores por estadística.
        Usa get_all_player_stats() internamente.
        """
    
    async def clear_cache(seasoncode: Optional[str] = None):
        """Limpiar caché manualmente."""
    
    async def get_cache_info(seasoncode: str) -> Dict[str, Any]:
        """Info sobre estado del caché."""
```

### TextToSQLService (Actualizado)

**Ubicación:** `backend/app/services/text_to_sql.py`

**Flujo de detección:**

```python
async def generate_sql(...):
    # 1. Detectar si requiere stats
    if self._requires_player_stats(query):
        # 2. Extraer parámetros con LLM
        params = await self._extract_stats_params(query)
        # {seasoncode: "E2025", stat: "points", top_n: 10}
        
        # 3. Obtener stats
        results = await self.player_stats_service.search_top_players(**params)
        
        # 4. Retornar datos directos (sin SQL)
        return None, "table", None, results
    
    # Si no es stats, generar SQL normal
    ...
```

### Chat Router (Actualizado)

**Ubicación:** `backend/app/routers/chat.py`

**Manejo de respuestas:**

```python
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Generar SQL o stats
    sql, viz, error, direct_data = await text_to_sql_service.generate_sql(...)
    
    # Si hay datos directos (stats)
    if direct_data is not None:
        return ChatResponse(
            sql=None,  # No hay SQL
            data=direct_data,
            visualization="table"
        )
    
    # Si hay SQL, ejecutar contra BD
    if sql:
        data = await _execute_sql(session, sql)
        return ChatResponse(sql=sql, data=data, visualization=viz)
```

## Configuración

### Variables de Entorno

```bash
# backend/.env

# Redis (requerido para caché)
REDIS_URL=redis://localhost:6379
REDIS_CACHE_TTL=86400  # 24 horas en segundos

# Euroleague API (sin API key, es pública)
# No requiere configuración adicional
```

### Dependencias

```toml
# backend/pyproject.toml

[tool.poetry.dependencies]
redis = {extras = ["hiredis"], version = ">=5.0.0,<6.0.0"}
```

### Instalación

```bash
cd backend

# Instalar dependencias
poetry install

# Iniciar Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# O instalar Redis localmente
# Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# Linux: sudo apt install redis-server
# macOS: brew install redis
```

## Ventajas de esta Arquitectura

✅ **BD pequeña:** Solo roster (~350 jugadores, <1MB)
✅ **Datos frescos:** Stats actualizadas cada 24h
✅ **Rápido después del primer call:** Caché Redis
✅ **Sin duplicación:** No almacenamos millones de registros históricos
✅ **Escalable:** Agregar temporadas sin inflar BD
✅ **Control total:** Lógica propia, sin dependencias de wrappers externos
✅ **Flexible:** Fácil ajustar TTL o estrategia de caché

## Desventajas y Mitigaciones

❌ **Primera consulta lenta (~30-60s)**
   ✅ Mitigación: Mostrar mensaje "Obteniendo estadísticas..." en frontend
   ✅ Mitigación: Pre-calentar caché con cron job diario

❌ **Requiere Redis**
   ✅ Mitigación: Fallback a llamadas API sin caché si Redis falla
   ✅ Mitigación: Redis es ligero y fácil de deployar

❌ **350 llamadas API por temporada**
   ✅ Mitigación: Solo se hace 1 vez cada 24h por temporada
   ✅ Mitigación: API de Euroleague es pública y sin rate limits estrictos

## Monitoreo

### Logs

```python
# Ver progreso de llamadas API
logger.info(f"Progreso: 50/350 jugadores procesados")
logger.info(f"Progreso: 100/350 jugadores procesados")
...

# Ver cache hits/misses
logger.info("Cache HIT para E2025")
logger.info("Cache MISS para E2025. Llamando API...")
```

### Métricas

```python
# Obtener info de caché
service = PlayerStatsService()
info = await service.get_cache_info("E2025")
# {
#   "exists": True,
#   "ttl": 82341,  # segundos restantes
#   "size_bytes": 1245678,
#   "seasoncode": "E2025"
# }
```

## Testing

### Test Manual

```bash
# Terminal 1: Iniciar Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Iniciar backend
cd backend
poetry run uvicorn app.main:app --reload

# Terminal 3: Test con curl
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Dame los 10 máximos anotadores de la Euroliga 2025",
    "history": []
  }'
```

### Test de Caché

```python
# backend/test_player_stats_cache.py

import asyncio
from app.services.player_stats_service import PlayerStatsService

async def test_cache():
    service = PlayerStatsService()
    
    # Primera llamada (cache miss)
    print("Primera llamada (debería tardar ~30-60s)...")
    result1 = await service.search_top_players("E2025", "points", 10)
    print(f"Resultado: {len(result1)} jugadores")
    
    # Segunda llamada (cache hit)
    print("\nSegunda llamada (debería ser instantánea)...")
    result2 = await service.search_top_players("E2025", "rebounds_total", 10)
    print(f"Resultado: {len(result2)} jugadores")
    
    # Info de caché
    info = await service.get_cache_info("E2025")
    print(f"\nInfo caché: {info}")
    
    await service.close()

asyncio.run(test_cache())
```

## Próximos Pasos (Post-MVP)

1. **Pre-calentamiento de caché:** Cron job que llena caché a las 6 AM
2. **Caché incremental:** Solo actualizar jugadores modificados
3. **Compresión:** Comprimir datos en Redis para ahorrar memoria
4. **Múltiples temporadas:** Pre-cachear E2024, E2025 automáticamente
5. **Métricas:** Dashboard de cache hit rate, latencias, etc.
6. **Fallback inteligente:** Si API falla, usar última versión cacheada aunque esté expirada

## Referencias

- **PlayerStatsService:** `backend/app/services/player_stats_service.py`
- **TextToSQLService:** `backend/app/services/text_to_sql.py`
- **Chat Router:** `backend/app/routers/chat.py`
- **EuroleagueClient:** `backend/etl/euroleague_client.py`
- **Config:** `backend/app/config.py`

