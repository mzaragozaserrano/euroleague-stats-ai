/**
 * Clasificador de Consultas
 * 
 * Detecta el tipo de consulta para optimizar la generación de SQL:
 * - STATS: Consultas de estadísticas agregadas (top scorers, averages, etc.)
 * - GAMES: Consultas sobre juegos individuales
 * - TEAMS: Consultas sobre equipos
 * - GENERAL: Otras consultas
 */

export type QueryType = 'STATS' | 'GAMES' | 'TEAMS' | 'GENERAL';

interface ClassificationResult {
  type: QueryType;
  confidence: number;
  keywords: string[];
}

// Palabras clave para cada tipo de consulta
const STATS_KEYWORDS = [
  'top scorer',
  'mejor anotador',
  'máximo anotador',
  'promedio',
  'average',
  'temporada',
  'season',
  'stats',
  'estadísticas',
  'ranking',
  'líder',
  'más puntos',
  'máximos',
  'mínimos',
  'total',
  'sum',
  'cuenta',
  'count',
  'porcentaje',
  'percentage',
];

const GAMES_KEYWORDS = [
  'partido',
  'game',
  'games',
  'partidos',
  'match',
  'score',
  'resultado',
  'fecha',
  'date',
  'round',
  'ronda',
  'cuarto',
  'quarter',
  'minuto',
  'minute',
  'jugó',
  'played',
  'alineación',
  'lineup',
  'box score',
];

const TEAMS_KEYWORDS = [
  'equipo',
  'team',
  'equipos',
  'teams',
  'club',
  'barcelona',
  'madrid',
  'real',
  'alba',
  'fenerbahe',
  'turk',
  'anadolu',
  'panathinaikos',
  'olimpiakos',
];

/**
 * Clasifica una consulta natural en tipos predefinidos.
 * 
 * @param query - Consulta natural del usuario
 * @returns Tipo de consulta detectado y confianza
 */
export function classifyQuery(query: string): ClassificationResult {
  const lowerQuery = query.toLowerCase();
  
  // Contar coincidencias por tipo
  const statsMatches = STATS_KEYWORDS.filter((kw) =>
    lowerQuery.includes(kw)
  ).length;
  
  const gamesMatches = GAMES_KEYWORDS.filter((kw) =>
    lowerQuery.includes(kw)
  ).length;
  
  const teamsMatches = TEAMS_KEYWORDS.filter((kw) =>
    lowerQuery.includes(kw)
  ).length;

  // Determinar tipo basado en máximas coincidencias
  let type: QueryType = 'GENERAL';
  let confidence = 0;
  let matchedKeywords: string[] = [];

  if (statsMatches > 0 && statsMatches >= gamesMatches && statsMatches >= teamsMatches) {
    type = 'STATS';
    confidence = Math.min(statsMatches / STATS_KEYWORDS.length, 1);
    matchedKeywords = STATS_KEYWORDS.filter((kw) => lowerQuery.includes(kw));
  } else if (gamesMatches > 0 && gamesMatches > statsMatches && gamesMatches >= teamsMatches) {
    type = 'GAMES';
    confidence = Math.min(gamesMatches / GAMES_KEYWORDS.length, 1);
    matchedKeywords = GAMES_KEYWORDS.filter((kw) => lowerQuery.includes(kw));
  } else if (teamsMatches > 0) {
    type = 'TEAMS';
    confidence = Math.min(teamsMatches / TEAMS_KEYWORDS.length, 1);
    matchedKeywords = TEAMS_KEYWORDS.filter((kw) => lowerQuery.includes(kw));
  } else {
    confidence = 0;
  }

  return {
    type,
    confidence,
    keywords: matchedKeywords,
  };
}

/**
 * Obtiene el contexto optimizado para el tipo de consulta.
 * 
 * Retorna información específica que ayuda al LLM a generar
 * el SQL correcto según el tipo de consulta.
 */
export function getQueryContext(type: QueryType): string {
  switch (type) {
    case 'STATS':
      return `
        Use the player_season_stats table for season-level statistics.
        This table is optimized for aggregated stats queries.
        Columns: id, player_id, season, games_played, points, rebounds, assists, pir
      `;
    
    case 'GAMES':
      return `
        Use the player_stats_games table for game-by-game statistics.
        Include the games table for match details (date, home/away, scores).
        Columns: id, game_id, player_id, team_id, minutes, points, rebounds_total, assists, fg3_made, pir
      `;
    
    case 'TEAMS':
      return `
        Use the teams table for team information.
        Join with players or games as needed for team-related stats.
        Columns: id, code, name, logo_url
      `;
    
    default:
      return `
        Determine the most appropriate table based on the query.
        Available tables: teams, players, games, player_stats_games, player_season_stats
      `;
  }
}

