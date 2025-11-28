-- ============================================================================
-- INITIAL SCHEMA MIGRATION FOR EUROLEAGUE STATISTICS AI
-- Version: 1.0
-- Description: Creates the base schema for storing Euroleague data with
--              pgvector extension for RAG-based schema retrieval
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS pgvector;

-- ============================================================================
-- TABLE: teams
-- Purpose: Store Euroleague team information
-- ============================================================================
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,  -- e.g., 'RMB' for Real Madrid
    name VARCHAR(255) NOT NULL,
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on code for fast lookups
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);

-- ============================================================================
-- TABLE: players
-- Purpose: Store player information linked to teams
-- ============================================================================
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50),  -- e.g., 'G' (Guard), 'F' (Forward), 'C' (Center)
    height DECIMAL(3, 2),  -- in meters (e.g., 1.98)
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

-- ============================================================================
-- TABLE: games
-- Purpose: Store game information for each match
-- ============================================================================
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,  -- e.g., 2023 for 2023-2024 season
    round INTEGER NOT NULL,   -- Round number in the season
    home_team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_round ON games(round);
CREATE INDEX IF NOT EXISTS idx_games_home_team_id ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team_id ON games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
CREATE INDEX IF NOT EXISTS idx_games_season_round ON games(season, round);

-- ============================================================================
-- TABLE: player_stats_games
-- Purpose: Store granular box score statistics for each player per game
-- ============================================================================
CREATE TABLE IF NOT EXISTS player_stats_games (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Basic stats
    minutes INTEGER,
    points INTEGER,
    rebounds_total INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    
    -- Shooting stats
    fg2_made INTEGER,           -- 2-pointers made
    fg2_attempted INTEGER,      -- 2-pointers attempted
    fg3_made INTEGER,           -- 3-pointers made
    fg3_attempted INTEGER,      -- 3-pointers attempted
    ft_made INTEGER,            -- Free throws made
    ft_attempted INTEGER,       -- Free throws attempted
    
    -- Fouls
    fouls_drawn INTEGER,
    fouls_committed INTEGER,
    
    -- Computed field (can be calculated or stored)
    pir DECIMAL(5, 2),          -- Performance Index Rating
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_player_stats_games_game_id ON player_stats_games(game_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_games_player_id ON player_stats_games(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_games_team_id ON player_stats_games(team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_games_player_game ON player_stats_games(player_id, game_id);

-- ============================================================================
-- TABLE: schema_embeddings
-- Purpose: Vector store for RAG-based schema retrieval
--          Stores embeddings of table/column descriptions and SQL examples
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,      -- Description of table/column or SQL example
    embedding vector(1536),     -- OpenAI text-embedding-3-small produces 1536-dim vectors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW index for efficient vector similarity search
CREATE INDEX IF NOT EXISTS idx_schema_embeddings_vector ON schema_embeddings
    USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- SEED DATA: Initial schema embeddings for RAG
-- ============================================================================
INSERT INTO schema_embeddings (content) VALUES
('Table: teams - Stores information about Euroleague basketball teams. Columns: id (primary key), code (team code like RMB), name (full team name), logo_url (URL to team logo)'),
('Table: players - Stores player information linked to teams. Columns: id (primary key), team_id (foreign key to teams), name (player full name), position (G=Guard, F=Forward, C=Center), height (in meters), birth_date'),
('Table: games - Stores game/match information. Columns: id (primary key), season (year), round (round number), home_team_id (FK), away_team_id (FK), date, home_score, away_score'),
('Table: player_stats_games - Box score statistics for each player per game. Columns: id, game_id (FK), player_id (FK), team_id (FK), minutes, points, rebounds_total, assists, steals, blocks, turnovers, fg2_made, fg2_attempted, fg3_made, fg3_attempted, ft_made, ft_attempted, fouls_drawn, fouls_committed, pir (Performance Index Rating)'),
('Example: To get all players from a specific team: SELECT name, position, height FROM players WHERE team_id = (SELECT id FROM teams WHERE code = ''RMB'')'),
('Example: To get player scoring statistics: SELECT p.name, SUM(psg.points) as total_points, AVG(psg.points) as avg_points FROM player_stats_games psg JOIN players p ON psg.player_id = p.id GROUP BY p.name'),
('Example: To compare two players: SELECT p1.name, p2.name, AVG(psg1.points) as p1_avg_points, AVG(psg2.points) as p2_avg_points FROM player_stats_games psg1 JOIN player_stats_games psg2 ON psg1.game_id = psg2.game_id JOIN players p1 ON psg1.player_id = p1.id JOIN players p2 ON psg2.player_id = p2.id WHERE p1.id = ? AND p2.id = ? GROUP BY p1.name, p2.name'),
('Example: To get free throw percentage: SELECT p.name, CAST(SUM(psg.ft_made) AS FLOAT) / NULLIF(SUM(psg.ft_attempted), 0) * 100 as ft_percentage FROM player_stats_games psg JOIN players p ON psg.player_id = p.id WHERE psg.team_id = ? GROUP BY p.name'),
('Column: points - Total points scored by a player in a game'),
('Column: assists - Number of assists made by a player in a game'),
('Column: rebounds_total - Total rebounds (offensive + defensive) in a game'),
('Column: fg3_made, fg3_attempted - Three-pointer statistics for a game'),
('Column: ft_made, ft_attempted - Free throw statistics for a game'),
('RAG Usage: This table is used to retrieve relevant schema information when processing natural language queries to SQL');

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total tables created: 5
-- - teams: Core team data
-- - players: Player roster information
-- - games: Match information
-- - player_stats_games: Box score granular statistics
-- - schema_embeddings: Vector store for RAG schema retrieval
--
-- Indexes created:
-- - Teams: idx_teams_code, idx_teams_name
-- - Players: idx_players_team_id, idx_players_name, idx_players_position
-- - Games: Multiple indexes for season, round, team_ids, date, and composites
-- - PlayerStatsGames: Indexes on game_id, player_id, team_id, and composite player_game
-- - SchemaEmbeddings: HNSW vector index for similarity search
-- ============================================================================

