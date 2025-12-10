-- Migración 001: Crear tablas base (teams, players, player_season_stats)
-- Idempotente: Usa CREATE TABLE IF NOT EXISTS

-- Tabla de equipos
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    logo_url TEXT,
    created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
    updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
);

CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);

-- Tabla de jugadores
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50),
    season VARCHAR(10) NOT NULL,
    created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
    updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_player_code ON players(player_code);
CREATE INDEX IF NOT EXISTS idx_players_season ON players(season);

-- Tabla de estadísticas por temporada
CREATE TABLE IF NOT EXISTS player_season_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    season VARCHAR(10) NOT NULL,
    games_played INTEGER DEFAULT 0,
    points FLOAT DEFAULT 0.0,
    rebounds FLOAT DEFAULT 0.0,
    assists FLOAT DEFAULT 0.0,
    steals FLOAT DEFAULT 0.0,
    blocks FLOAT DEFAULT 0.0,
    turnovers FLOAT DEFAULT 0.0,
    "threePointsMade" FLOAT DEFAULT 0.0,
    pir FLOAT DEFAULT 0.0,
    created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
    updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
);

CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_id ON player_season_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_season ON player_season_stats(season);
CREATE INDEX IF NOT EXISTS idx_player_season_stats_player_season ON player_season_stats(player_id, season);



