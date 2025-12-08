/**
 * Clasificador de Consultas
 * 
 * Detecta el tipo de consulta del usuario y extrae parámetros relevantes.
 * Permite manejar consultas de estadísticas en el frontend (sin backend).
 */

export type QueryType = 
  | "top_players"      // Top N jugadores por estadística
  | "player_lookup"    // Buscar jugador específico
  | "team_roster"      // Roster de un equipo
  | "comparison"       // Comparar jugadores
  | "general";         // Consulta general (usar backend)

export interface QueryParams {
  seasonCode: string;
  stat: keyof typeof STAT_MAP;
  topN: number;
  teamCode?: string;
  playerName?: string;
  playerNames?: string[]; // Para comparaciones
}

/**
 * Mapeo de palabras en español a campos de estadísticas
 */
export const STAT_MAP = {
  points: ["puntos", "anotador", "scorer", "scoring"],
  rebounds: ["rebotes", "reboteador", "rebounder", "rebounds"],
  assists: ["asistencias", "asistente", "asista", "assists"],
  steals: ["robos", "robo", "steals", "steal"],
  blocks: ["tapones", "tapón", "blocks", "block"],
  threePointsMade: ["triples", "triple", "three", "3puntos"],
  turnovers: ["pérdidas", "pérdida", "turnovers"],
  fouls: ["faltas", "falta", "fouls"],
} as const;

/**
 * Mapeo de nombres de equipos a códigos de Euroleague
 */
export const TEAM_CODE_MAP: Record<string, string> = {
  // España
  "real madrid": "RM",
  "madrid": "RM",
  "barcelona": "BAR",
  "barça": "BAR",
  "valencia": "VAL",
  "baskonia": "BAS",
  "bilbao": "BAS",
  "asvel": "ASV",
  "lyon": "ASV",
  
  // Turquía
  "efes": "IST",
  "anadolu efes": "IST",
  "fenerbahce": "FEN",
  "fenerbahçe": "FEN",
  
  // Grecia
  "olympiacos": "OLY",
  "panathinaikos": "PAN",
  "atenas": "PAN",
  
  // Italia
  "virtus": "VIR",
  "bologna": "VIR",
  "milano": "MIL",
  "armani": "MIL",
  
  // Alemania
  "bayern": "BAY",
  "múnich": "BAY",
  "alba": "ALB",
  "berlín": "ALB",
  
  // Francia
  "monaco": "MON",
  "paris": "PSG",
  
  // Israel
  "maccabi": "MAC",
  "tel aviv": "MAC",
  
  // Otros
  "partizan": "PAR",
  "belgrado": "PAR",
  "zalgiris": "ZAL",
  "lituania": "ZAL",
  "estrella roja": "EST",
};

/**
 * Clasifica el tipo de consulta del usuario
 */
export function classifyQuery(query: string): QueryType {
  const lowerQuery = query.toLowerCase();
  
  // Top players
  if (/\b(top|mejor|máximo|máximos|primeros|anotador|reboteador|asistente|líder|líderes)\b/i.test(lowerQuery)) {
    return "top_players";
  }
  
  // Player lookup
  if (/\b(puntos de|stats de|estadísticas de|información de|datos de|comparar)\b/i.test(lowerQuery)) {
    if (/\s+vs\s+|versus|contra/i.test(lowerQuery)) {
      return "comparison";
    }
    return "player_lookup";
  }
  
  // Team roster
  if (/\b(jugadores del|jugadores de|roster|plantilla|alineación)\b/i.test(lowerQuery)) {
    return "team_roster";
  }
  
  // Comparison
  if (/\s+vs\s+|versus|contra/i.test(lowerQuery)) {
    return "comparison";
  }
  
  return "general";
}

/**
 * Extrae parámetros de una consulta
 */
export function extractParams(query: string): QueryParams {
  const params: QueryParams = {
    seasonCode: "E2025", // Default actual
    stat: "points",
    topN: 10,
  };
  
  // Extraer número (top N)
  const numberMatch = query.match(/\d+/);
  if (numberMatch) {
    const num = parseInt(numberMatch[0]);
    if (num > 0 && num <= 100) {
      params.topN = num;
    }
  }
  
  // Extraer estadística
  for (const [stat, keywords] of Object.entries(STAT_MAP)) {
    for (const keyword of keywords) {
      if (new RegExp(`\\b${keyword}\\b`, "i").test(query)) {
        params.stat = stat as keyof typeof STAT_MAP;
        break;
      }
    }
  }
  
  // Extraer temporada
  if (/2024|2024-2025|temporada 2024|season 2024/i.test(query)) {
    params.seasonCode = "E2024";
  } else if (/2025|2025-2026|temporada 2025|season 2025|esta temporada|this season|current/i.test(query)) {
    params.seasonCode = "E2025";
  }
  
  // Extraer equipo
  for (const [teamName, teamCode] of Object.entries(TEAM_CODE_MAP)) {
    if (new RegExp(`\\b${teamName}\\b`, "i").test(query)) {
      params.teamCode = teamCode;
      break;
    }
  }
  
  // Extraer nombre de jugador (para lookups)
  const playerMatch = query.match(
    /(?:de|del|jugador|player)\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+vs\s+|versus|contra|\s+del|\s+de|\s*$)/i
  );
  if (playerMatch) {
    params.playerName = playerMatch[1].trim();
  }
  
  return params;
}

/**
 * Extrae un nombre de jugador de la consulta
 */
export function extractPlayerName(query: string): string {
  // Buscar patrón: "de/del NOMBRE" o "NOMBRE"
  const patterns = [
    /(?:de|del)\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+vs\s+|versus|contra|\s+del|\s+de|$)/i,
    /(?:del)\s+([A-Za-zÀ-ÿ]+)/i,
    /(?:de)\s+([A-Za-zÀ-ÿ]+)/i,
  ];
  
  for (const pattern of patterns) {
    const match = query.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  return "";
}

/**
 * Extrae dos nombres de jugadores para comparación
 */
export function extractPlayerNamesForComparison(query: string): [string, string] | null {
  const match = query.match(
    /(?:de|del)?\s+([A-Za-zÀ-ÿ]+)\s+(?:vs|versus|contra|y)\s+([A-Za-zÀ-ÿ]+)/i
  );
  
  if (match && match[1] && match[2]) {
    return [match[1].trim(), match[2].trim()];
  }
  
  return null;
}

/**
 * Obtiene información de debug sobre la clasificación
 */
export function getQueryDebugInfo(query: string) {
  return {
    originalQuery: query,
    type: classifyQuery(query),
    params: extractParams(query),
    timestamp: new Date().toISOString(),
  };
}

