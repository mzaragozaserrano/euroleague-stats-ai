-- Migration: Recrear tabla players con player_code como identificador único
-- Purpose: Cambiar de id autoincrementante a player_code como identificador único
-- Date: 2025-12-08

-- PASO 1: Crear tabla players_new con la estructura correcta
CREATE TABLE IF NOT EXISTS players_new (
    id SERIAL PRIMARY KEY,
    player_code VARCHAR(50) NOT NULL UNIQUE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50),
    height DECIMAL(3, 2),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PASO 2: Copiar datos de la tabla antigua (si existen)
INSERT INTO players_new (id, player_code, team_id, name, position, height, birth_date, created_at, updated_at)
SELECT id, COALESCE(player_code, 'P' || LPAD(id::TEXT, 6, '0')), team_id, name, position, height, birth_date, created_at, updated_at
FROM players
ON CONFLICT (player_code) DO NOTHING;

-- PASO 3: Eliminar foreign keys que apunten a players
DROP TABLE IF EXISTS player_stats_games CASCADE;

-- PASO 4: Eliminar índices de la tabla antigua
DROP INDEX IF EXISTS idx_players_team_id;
DROP INDEX IF EXISTS idx_players_name;
DROP INDEX IF EXISTS idx_players_position;

-- PASO 5: Renombrar tablas
ALTER TABLE players RENAME TO players_old;
ALTER TABLE players_new RENAME TO players;

-- PASO 6: Recrear índices en la tabla nueva
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code);

-- PASO 7: Eliminar tabla antigua
DROP TABLE IF EXISTS players_old CASCADE;

-- Comentarios
COMMENT ON COLUMN players.player_code IS 'Código único del jugador en la API de Euroleague';

