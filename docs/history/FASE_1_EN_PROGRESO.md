# FASE 1: Data Pipeline MVP - EN PROGRESO

## Resumen Ejecutivo

La Fase 1 se centra en la creación del pipeline de datos que alimentará la base de datos con estadísticas de la Euroliga. Esta fase incluye el diseño del esquema, la implementación de modelos, y los scripts ETL para ingerir datos desde la API oficial de Euroleague.

**Estrategia de Implementación:** Esta fase se ha dividido en 3 sub-fases para facilitar el desarrollo incremental y seguir correctamente el flujo TDD/BDD. Cada sub-fase puede completarse de forma independiente, permitiendo validación temprana y menor carga cognitiva.

---

## Sub-fase 1.1: Cimientos del Dominio (Foundation)

**Objetivo:** Establecer la infraestructura base del dominio sin datos reales aún. Preparar el terreno para la ingesta de datos.

### Estado: Pendiente

1. **1.1.1 Diseño del Esquema de Base de Datos**
   - Crear archivo `backend/migrations/001_initial_schema.sql`
   - Tablas: teams, players, games, player_stats_games, schema_embeddings
   - Incluir extensión pgvector para búsqueda vectorial

2. **1.1.2 Implementar Modelos SQLAlchemy**
   - `backend/app/models/team.py`
   - `backend/app/models/player.py`
   - `backend/app/models/game.py`
   - `backend/app/models/player_stats.py`
   - `backend/app/models/schema_embedding.py`
   - Configurar NullPool en database.py

3. **1.1.3 Cliente Base de Euroleague API**
   - `backend/etl/euroleague_client.py`
   - Configuración básica de conexión HTTP
   - Manejo de autenticación/headers
   - Estructura base para métodos de obtención de datos

---

## Sub-fase 1.2: Datos Maestros (Static Data TDD)

**Objetivo:** Implementar la ingesta de datos estáticos (equipos y jugadores) siguiendo el flujo TDD/BDD completo. Estos datos cambian poco y son ideales para validar el pipeline completo por primera vez.

### Estado: Pendiente

1. **1.2.1 BDD Feature - Equipos**
   - Crear `backend/tests/features/teams.feature`
   - Escenarios: Given API returns teams, When I run ETL, Then DB has teams
   - Step definitions: `backend/tests/step_defs/test_teams_steps.py`

2. **1.2.2 ETL Equipos**
   - Implementar `backend/etl/ingest_teams.py`
   - Usar euroleague_client para obtener datos
   - Transformar y persistir usando modelos SQLAlchemy
   - Validar con tests BDD

3. **1.2.3 BDD Feature - Jugadores**
   - Crear `backend/tests/features/players.feature`
   - Escenarios: Given API returns players, When I run ETL, Then DB has players
   - Step definitions: `backend/tests/step_defs/test_players_steps.py`

4. **1.2.4 ETL Jugadores**
   - Implementar `backend/etl/ingest_players.py`
   - Usar euroleague_client para obtener datos
   - Transformar y persistir usando modelos SQLAlchemy
   - Validar con tests BDD

---

## Sub-fase 1.3: Datos Transaccionales (Dynamic Data TDD)

**Objetivo:** Implementar la ingesta de datos dinámicos (partidos y estadísticas). Esta es la parte más compleja del pipeline debido a la estructura anidada de estadísticas y la frecuencia de actualización.

### Estado: Pendiente

1. **1.3.1 BDD Feature - Partidos y Estadísticas**
   - Crear `backend/tests/features/games.feature`
   - Escenarios complejos: partidos jugados vs programados, estadísticas anidadas
   - Step definitions: `backend/tests/step_defs/test_games_steps.py`

2. **1.3.2 ETL Partidos y Estadísticas**
   - Implementar `backend/etl/ingest_games.py`
   - Script más complejo: manejar partidos y sus estadísticas asociadas
   - Upsert lógico para evitar duplicados
   - Validar con tests BDD

---

## Referencias

- [`ROADMAP.md`](../../ROADMAP.md) - Plan completo del proyecto
- [`TECHNICAL_PLAN.md`](../TECHNICAL_PLAN.md) - Plan técnico detallado
- [`SPECIFICATIONS.md`](../SPECIFICATIONS.md) - Especificaciones funcionales
- [`SPECIFICATIONS_GHERKIN.md`](../SPECIFICATIONS_GHERKIN.md) - Especificaciones en formato Gherkin
- [Issues de GitHub - Fase 1](https://github.com/mzaragozaserrano/euroleague-stats-ai/issues?q=is%3Aopen+label%3Afase-1.1+label%3Afase-1.2+label%3Afase-1.3) - Tareas detalladas con dependencias y labels

---

## Notas de Implementación

- **Flujo TDD/BDD:** Cada script ETL debe tener su archivo `.feature` creado ANTES de la implementación, no después.
- **Dependencias:** La Sub-fase 1.2 puede comenzar una vez completada la 1.1. La Sub-fase 1.3 requiere que 1.2 esté completa (los partidos dependen de equipos y jugadores).
- **Validación:** Cada sub-fase debe poder ejecutarse de forma independiente y validarse antes de pasar a la siguiente.

---

**Última actualización**: Diciembre 2024

