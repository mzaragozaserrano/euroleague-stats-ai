-- Migration: Agregar campo player_code a tabla players
-- Purpose: Almacenar código de Euroleague API para cada jugador
-- Date: 2025-12-08

-- Agregar columna player_code
ALTER TABLE players ADD COLUMN IF NOT EXISTS player_code VARCHAR(50);

-- Crear índice único en player_code
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code);

-- Poblar player_code con valores temporales basados en ID (se actualizará con ETL)
UPDATE players SET player_code = 'P' || LPAD(id::TEXT, 6, '0') WHERE player_code IS NULL;

-- Hacer player_code NOT NULL después de poblar
ALTER TABLE players ALTER COLUMN player_code SET NOT NULL;

-- Comentarios
COMMENT ON COLUMN players.player_code IS 'Código único del jugador en la API de Euroleague';

