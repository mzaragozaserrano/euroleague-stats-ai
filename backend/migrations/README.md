# Database Migrations

Este directorio contiene todos los scripts de migración SQL para la base de datos PostgreSQL de Euroleague Statistics AI.

## Estructura de Migraciones

Las migraciones se nombran con un prefijo numérico para garantizar el orden de ejecución:
- `001_initial_schema.sql` - Esquema inicial con todas las tablas base

## Cómo Ejecutar las Migraciones

### Opción 1: Usando psql (Recomendado para desarrollo local)

```bash
# Conectarte a tu instancia de PostgreSQL
psql -h localhost -U postgres -d euroleague_stats

# Ejecutar la migración
\i backend/migrations/001_initial_schema.sql
```

### Opción 2: Usando comando SQL directo

```bash
psql -h your_host -U your_user -d your_database < backend/migrations/001_initial_schema.sql
```

### Opción 3: Para Neon (Serverless)

```bash
# Reemplaza la URL con tu DATABASE_URL de Neon
psql "postgresql://user:password@your-neon-host/dbname" < backend/migrations/001_initial_schema.sql
```

### Opción 4: Desde Python (ETL/Scripts)

```python
import psycopg2

def execute_migration(connection_string, migration_file):
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Migración ejecutada: {migration_file}")

# Uso
execute_migration(
    os.getenv("DATABASE_URL"),
    "backend/migrations/001_initial_schema.sql"
)
```

## Qué Crea Esta Migración (001_initial_schema.sql)

### Tablas Creadas:

1. **teams** - Información de equipos de Euroleague
   - `id` (PK)
   - `code` (Ej: 'RMB' para Real Madrid)
   - `name` (Nombre completo del equipo)
   - `logo_url` (URL del logo)

2. **players** - Información de jugadores
   - `id` (PK)
   - `team_id` (FK a teams)
   - `name` (Nombre del jugador)
   - `position` (G=Guard, F=Forward, C=Center)
   - `height` (En metros)
   - `birth_date` (Fecha de nacimiento)

3. **games** - Información de partidos
   - `id` (PK)
   - `season` (Año, ej: 2023 para 2023-2024)
   - `round` (Número de ronda)
   - `home_team_id` (FK a teams)
   - `away_team_id` (FK a teams)
   - `date` (Fecha del partido)
   - `home_score` (Puntos equipo local)
   - `away_score` (Puntos equipo visitante)

4. **player_stats_games** - Estadísticas por jugador por partido (Box Score)
   - Estadísticas básicas: `minutes`, `points`, `rebounds_total`, `assists`, `steals`, `blocks`, `turnovers`
   - Estadísticas de tiro: `fg2_made/attempted`, `fg3_made/attempted`, `ft_made/attempted`
   - Faltas: `fouls_drawn`, `fouls_committed`
   - PIR (Performance Index Rating)

5. **schema_embeddings** - Vector store para RAG (Recuperación Augmentada por Generación)
   - `id` (UUID, PK)
   - `content` (Descripción de tabla/columna o ejemplos SQL)
   - `embedding` (Vector de 1536 dimensiones - OpenAI text-embedding-3-small)

### Índices Creados:

Se crean múltiples índices para optimizar:
- Búsquedas por código y nombre de equipo
- Búsquedas por jugador (nombre, equipo, posición)
- Búsquedas por temporada, ronda, equipo y fecha en games
- Búsqueda por combinación player_id + game_id
- Búsqueda vectorial HNSW para similitud en embeddings

## Restricciones de Diseño

- **Tamaño optimizado**: Diseño para < 0.5GB (límite free tier de Neon)
- **Extensión pgvector**: Requerida para buscar esquema via embeddings
- **Relaciones en cascada**: Al eliminar un equipo/jugador, se eliminan sus registros relacionados
- **Timestamps**: Todas las tablas incluyen `created_at` y `updated_at` para auditoría

## Verificación

Para verificar que la migración se ejecutó correctamente:

```sql
-- Ver todas las tablas creadas
\dt

-- Ver estructura de una tabla específica
\d teams

-- Ver índices
\di

-- Ver extensiones
\dx
```

## Notas Importantes

- Las migraciones están diseñadas para ser idempotentes (usar `CREATE TABLE IF NOT EXISTS`)
- Se incluyen datos semilla para la tabla `schema_embeddings` para inicializar el RAG
- La columna `embedding` en `schema_embeddings` usa vector de 1536 dimensiones (tamaño OpenAI text-embedding-3-small)

## Troubleshooting

### Error: "pgvector extension not found"
- Asegúrate de que PostgreSQL tiene la extensión pgvector instalada
- En Neon, pgvector viene pre-instalada

### Error: "Foreign key constraint failed"
- Las tablas deben crearse en orden (teams → players → games → player_stats_games)
- La migración respeta este orden automáticamente

### Tabla ya existe
- Las migraciones usan `CREATE TABLE IF NOT EXISTS` para ser seguras
- Puedes ejecutarlas múltiples veces sin problemas

