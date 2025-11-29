-- MCP Verification Queries
-- Archivo de prueba para validar la conexión y funcionamiento del MCP con Neon
-- Uso: Copia y pega estas queries en Cursor usando el MCP para verificar que funciona correctamente

-- 1. HEALTH CHECK: Verificar conexión a la base de datos
SELECT 
    current_database() as database,
    current_user as user,
    NOW() as timestamp,
    'Connection OK' as status;

-- 2. SCHEMA VERIFICATION: Listar todas las tablas principales
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 3. PLAYERS TABLE: Contar jugadores y verificar integridad
SELECT 
    COUNT(*) as total_players,
    COUNT(DISTINCT team_id) as teams_represented,
    COUNT(DISTINCT position) as positions
FROM players;

-- 4. PLAYER STATS: Verificar integridad de estadísticas
SELECT 
    COUNT(*) as total_stats_records,
    COUNT(DISTINCT player_id) as unique_players,
    COUNT(DISTINCT game_id) as games_covered,
    MIN(points) as min_points,
    MAX(points) as max_points,
    ROUND(AVG(points), 2) as avg_points
FROM player_stats_games;

-- 5. GAMES TABLE: Verificar cobertura de juegos
SELECT 
    COUNT(*) as total_games,
    COUNT(DISTINCT season) as seasons,
    MAX(season) as latest_season,
    COUNT(DISTINCT home_team_id) as teams
FROM games;

-- 6. SCHEMA EMBEDDINGS: Verificar que el índice vectorial está disponible
SELECT 
    COUNT(*) as embedding_records,
    COUNT(DISTINCT embedding) as unique_embeddings
FROM schema_embeddings
LIMIT 1;

-- 7. QUERY TEST: Ejemplo de RAG - TOP 5 Scorers
SELECT 
    p.name as player_name,
    t.name as team_name,
    ROUND(AVG(psg.points), 2) as avg_points_per_game,
    COUNT(*) as games_played
FROM player_stats_games psg
JOIN players p ON psg.player_id = p.id
JOIN teams t ON p.team_id = t.id
GROUP BY p.id, p.name, t.name
ORDER BY avg_points_per_game DESC
LIMIT 5;

-- 8. ADVANCED QUERY: Comparativa de rendimiento
SELECT 
    COALESCE(p1.name, 'Unknown') as player_1,
    COALESCE(p2.name, 'Unknown') as player_2,
    ROUND(AVG(s1.points), 2) as avg_points_p1,
    ROUND(AVG(s2.points), 2) as avg_points_p2,
    ROUND(AVG(s1.rebounds), 2) as avg_rebounds_p1,
    ROUND(AVG(s2.rebounds), 2) as avg_rebounds_p2
FROM player_stats_games s1
LEFT JOIN player_stats_games s2 ON s1.game_id = s2.game_id AND s1.player_id != s2.player_id
LEFT JOIN players p1 ON s1.player_id = p1.id
LEFT JOIN players p2 ON s2.player_id = p2.id
WHERE s1.player_id = 1 AND s2.player_id = 2
GROUP BY p1.name, p2.name
LIMIT 1;

-- 9. PERFORMANCE CHECK: Verificar que los índices están activos
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 10. VECTOR SEARCH TEST: Verificar que pgvector está funcionando (si hay embeddings)
SELECT 
    id,
    content,
    embedding <-> '[0.1, 0.2, 0.3]'::vector as distance
FROM schema_embeddings
ORDER BY distance
LIMIT 3;


