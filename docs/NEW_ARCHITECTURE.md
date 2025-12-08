# Nueva Arquitectura: Caché Frontend + API Euroleague

## Resumen

La base de datos **solo almacena metadatos** (códigos de equipos y jugadores) necesarios para hacer llamadas a la API de Euroleague. Los **datos reales** (estadísticas) se obtienen directamente de la API y se cachean en el frontend.

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Verificar Invalidación (7 AM)                    │  │
│  │     PlayerStatsCache.checkAndInvalidate()            │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Consultar Caché Local (localStorage)             │  │
│  │     - Datos por temporada (E2024, E2025)             │  │
│  │     - Invalidación automática después de 7 AM        │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                  ¿Existe?                                   │
│                  │    │                                     │
│             SÍ ──┘    └── NO                                │
│              │              │                               │
│              │              ▼                               │
│              │    ┌────────────────────────────────┐       │
│              │    │  3. Llamar API Euroleague      │       │
│              │    │     - Obtener stats reales     │       │
│              │    │     - Guardar en caché         │       │
│              │    └────────────────────────────────┘       │
│              │              │                               │
│              └──────────────┘                               │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Renderizar Visualización                         │  │
│  │     - DataVisualizer (BarChart, LineChart, Table)    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       │ (Solo para obtener códigos)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Text-to-SQL Service                                 │  │
│  │  - Genera SQL para obtener códigos de jugadores     │  │
│  │  - Retorna: player_code, team_code                  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              BASE DE DATOS (Neon PostgreSQL)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tabla: teams                                        │  │
│  │  - id, code, name, logo_url                          │  │
│  │  - Actualizada diariamente (7 AM)                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tabla: players                                      │  │
│  │  - id, player_code, team_id, name, position         │  │
│  │  - Actualizada diariamente (7 AM)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       ▲
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   ETL AUTOMÁTICO                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Scheduler: Cada día a las 7 AM                      │  │
│  │  1. Llamar API Euroleague /teams                     │  │
│  │  2. Actualizar tabla teams                           │  │
│  │  3. Para cada equipo, obtener roster                 │  │
│  │  4. Actualizar tabla players                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Componentes Clave

### 1. Frontend: PlayerStatsCache

**Ubicación:** `frontend/lib/playerStatsCache.ts`

**Responsabilidades:**
- Almacenar estadísticas de jugadores por temporada en `localStorage`
- Invalidar caché automáticamente después de las 7 AM
- Proveer métodos para obtener/guardar stats

**Estructura de Datos:**
```typescript
{
  "player-stats-cache": {
    "E2024": {
      data: PlayerStats[],
      timestamp: 1702022400000,
      lastSync: 1702018800000
    },
    "E2025": {
      data: PlayerStats[],
      timestamp: 1702022400000,
      lastSync: 1702018800000
    }
  },
  "cache-metadata": {
    lastCleared: 1702018800000,
    version: 1
  }
}
```

**Métodos:**
- `checkAndInvalidate()`: Verifica si pasaron las 7 AM y limpia caché
- `getSeasonStats(seasonCode)`: Obtiene stats de una temporada
- `setSeasonStats(seasonCode, stats)`: Guarda stats en caché
- `clearAllCache()`: Limpia todo el caché (mantiene consultas SQL del chatStore)

### 2. Frontend: EuroleagueApi

**Ubicación:** `frontend/lib/euroleagueApi.ts`

**Responsabilidades:**
- Llamar a la API oficial de Euroleague
- Integrar con PlayerStatsCache (priorizar caché)
- Transformar respuestas de API al formato interno

**Métodos:**
- `getPlayerStats(seasonCode, forceRefresh)`: Obtiene stats (caché → API)
- `getTopPlayers(seasonCode, stat, topN, teamCode)`: Filtra top N jugadores
- `searchPlayer(seasonCode, playerName)`: Busca un jugador específico
- `comparePlayers(seasonCode, player1, player2)`: Compara dos jugadores

### 3. Backend: Base de Datos Simplificada

**Tablas:**

#### `teams`
```sql
CREATE TABLE teams (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,  -- Código de Euroleague (ej: "RM", "BAR")
  name VARCHAR(255) NOT NULL,
  logo_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `players`
```sql
CREATE TABLE players (
  id SERIAL PRIMARY KEY,
  player_code VARCHAR(50) UNIQUE NOT NULL,  -- Código de Euroleague API
  team_id INTEGER REFERENCES teams(id),
  name VARCHAR(255) NOT NULL,
  position VARCHAR(50),
  height NUMERIC(3,2),
  birth_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Nota:** Las tablas `games` y `player_stats_games` se eliminan porque los datos reales vienen de la API.

### 4. Backend: ETL Automático

**Ubicación:** `backend/etl/`

**Scheduler:** GitHub Actions (Cron: `0 7 * * *` - Cada día a las 7 AM UTC)

**Proceso:**
1. Llamar a API Euroleague: `GET /teams?seasonCode=E2025`
2. Actualizar tabla `teams` (UPSERT por `code`)
3. Para cada equipo, obtener roster: `GET /teams/{code}/roster`
4. Actualizar tabla `players` (UPSERT por `player_code`)

**Scripts:**
- `ingest_teams.py`: Actualiza equipos
- `ingest_players.py`: Actualiza jugadores (roster)
- `run_all_etl.py`: Ejecuta ambos scripts

### 5. Backend: Text-to-SQL Adaptado

**Cambios:**
- Ya no genera SQL para obtener estadísticas
- Solo genera SQL para obtener **códigos** de jugadores/equipos
- El frontend usa esos códigos para llamar a la API de Euroleague

**Ejemplo:**

**Query del usuario:** "Top 10 anotadores de esta temporada"

**Flujo:**
1. Frontend detecta que necesita stats → llama a `EuroleagueApi.getTopPlayers('E2025', 'points', 10)`
2. `EuroleagueApi` verifica caché → si no existe, llama a API Euroleague
3. API retorna stats reales → se cachean en `localStorage`
4. Frontend renderiza visualización

**Query del usuario:** "Puntos de Larkin"

**Flujo:**
1. Frontend necesita identificar al jugador → llama al backend
2. Backend genera SQL: `SELECT player_code, name FROM players WHERE name ILIKE '%Larkin%'`
3. Backend retorna: `{ player_code: "P001234", name: "Shane Larkin" }`
4. Frontend llama a `EuroleagueApi.searchPlayer('E2025', 'Larkin')`
5. API retorna stats → se cachean → se renderizan

## Invalidación de Caché

### Reglas:
1. **Hora de Sincronización:** 7 AM (configurable en `playerStatsCache.ts`)
2. **Verificación:** Al inicializar `chatStore` y en cada llamada a `getSeasonStats()`
3. **Qué se limpia:** Solo datos de stats (`player-stats-cache`)
4. **Qué se mantiene:** Historial de consultas SQL (`chat-storage`)

### Lógica:
```typescript
// Obtener 7 AM de hoy
const syncTime = new Date();
syncTime.setHours(7, 0, 0, 0);

// Si aún no son las 7 AM, usar 7 AM de ayer
if (now < syncTime) {
  syncTime.setDate(syncTime.getDate() - 1);
}

// Si última limpieza fue antes de las 7 AM de hoy → invalidar
if (lastCleared < syncTime.getTime()) {
  clearAllCache();
}
```

## Ventajas de esta Arquitectura

1. **Performance:** Datos en caché local (sin latencia de red)
2. **Escalabilidad:** No saturamos la BD con millones de filas de stats
3. **Frescura:** Datos actualizados diariamente (7 AM)
4. **Simplicidad:** BD solo almacena metadatos (códigos)
5. **Offline-First:** Caché sobrevive a recargas de página
6. **Costo:** Menos queries a Neon (solo para obtener códigos)

## Desventajas y Mitigaciones

1. **Dependencia de API Externa:**
   - Mitigación: Caché como fallback si API falla
   
2. **Límites de localStorage (5-10 MB):**
   - Mitigación: Solo cachear temporadas activas (E2024, E2025)
   - Limpieza automática de temporadas antiguas
   
3. **Datos por Dispositivo:**
   - Mitigación: Aceptable para MVP (cada usuario tiene su caché)
   - Futuro: Implementar caché en backend (Redis)

## Próximos Pasos

1. ✅ Implementar `PlayerStatsCache`
2. ✅ Implementar `EuroleagueApi`
3. ✅ Integrar invalidación en `chatStore`
4. ⏳ Simplificar modelos de BD (eliminar `games`, `player_stats_games`)
5. ⏳ Adaptar ETL para actualizar solo códigos
6. ⏳ Modificar `text_to_sql.py` para retornar códigos
7. ⏳ Configurar GitHub Actions para ETL diario (7 AM)
8. ⏳ Testing end-to-end

## Referencias

- API Euroleague: https://api-live.euroleague.net/v1
- Documentación localStorage: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- GitHub Actions Cron: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule

