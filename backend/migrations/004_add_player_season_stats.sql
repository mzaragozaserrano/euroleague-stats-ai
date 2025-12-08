-- Migration: Crear tabla para estadísticas de jugadores por temporada
-- Purpose: Almacenar stats obtenidas de euroleague_api
-- Date: 2025-12-08

-- Crear tabla player_season_stats
CREATE TABLE IF NOT EXISTS player_season_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    season VARCHAR(10) NOT NULL,  -- "E2025", "E2024", etc
    
    -- Estadísticas básicas
    games_played INTEGER,
    points DECIMAL(5, 2),
    rebounds DECIMAL(5, 2),
    assists DECIMAL(5, 2),
    steals DECIMAL(5, 2),
    blocks DECIMAL(5, 2),
    turnovers DECIMAL(5, 2),
    
    -- Tiros
    fg2_made DECIMAL(5, 2),
    fg2_attempted DECIMAL(5, 2),
    fg3_made DECIMAL(5, 2),
    fg3_attempted DECIMAL(5, 2),
    ft_made DECIMAL(5, 2),
    ft_attempted DECIMAL(5, 2),
    
    -- Faltas
    fouls_drawn INTEGER,
    fouls_committed INTEGER,
    
    -- Eficiencia
    pir DECIMAL(5, 2),  -- Performance Index Rating
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: Un único registro por jugador y temporada
    UNIQUE(player_id, season)
);

-- Crear índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_id ON player_season_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_season ON player_season_stats(season);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_points ON player_season_stats(points DESC);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_assists ON player_season_stats(assists DESC);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_rebounds ON player_season_stats(rebounds DESC);

-- Comentarios
COMMENT ON TABLE player_season_stats IS 'Estadísticas agregadas de jugadores por temporada, poblada desde euroleague_api';
COMMENT ON COLUMN player_season_stats.season IS 'Código de temporada en formato E2025';
COMMENT ON COLUMN player_season_stats.pir IS 'Performance Index Rating (PIR) - métrica de eficiencia';

