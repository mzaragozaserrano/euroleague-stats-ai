/**
 * Cliente para API de Euroleague
 * 
 * NOTA: El frontend NO llama directamente a la API de Euroleague.
 * En su lugar, delega al backend que es quien tiene acceso a la API real.
 * 
 * El backend ya tiene un cliente funcional (euroleague_client.py) que:
 * - Maneja XML parsing
 * - Retry logic
 * - CORS y autenticación
 * 
 * Este cliente fue reemplazado por una estrategia más simple:
 * Si la consulta necesita stats de jugadores, simplemente se delega al backend
 * usando el servicio text_to_sql que luego usa PlayerStatsService.
 */

import { PlayerStats, PlayerStatsCache } from './playerStatsCache';

const EUROLEAGUE_API_BASE = 'https://api-live.euroleague.net/v1';

export interface EuroleaguePlayerStats {
  playerId: string;
  playerName: string;
  teamCode: string;
  games: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fouls: number;
  [key: string]: any;
}

export class EuroleagueApiError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'EuroleagueApiError';
  }
}

export class EuroleagueApi {
  /**
   * DEPRECATED: El frontend ya no llama directamente a la API de Euroleague.
   * En su lugar, las consultas de stats se procesan a través del backend.
   * 
   * Mantener esta clase para compatibilidad hacia atrás, pero las llamadas
   * reales se hacen a través del backend (vía sendChatMessage en lib/api.ts)
   */
  
  public static async getPlayerStats(
    seasonCode: string,
    forceRefresh = false
  ): Promise<PlayerStats[]> {
    // Esta función ya no es necesaria porque las stats vienen del backend
    console.warn(
      '[EuroleagueApi] getPlayerStats está deprecated. '
      'Las stats se obtienen a través del backend vía sendChatMessage()'
    );
    return [];
  }

  public static async getTopPlayers(
    seasonCode: string,
    stat: keyof typeof STAT_MAP,
    topN = 10,
    teamCode?: string
  ): Promise<PlayerStats[]> {
    console.warn(
      '[EuroleagueApi] getTopPlayers está deprecated. '
      'Use sendChatMessage() del backend en su lugar'
    );
    return [];
  }

  public static async searchPlayer(
    seasonCode: string,
    playerName: string
  ): Promise<PlayerStats | null> {
    console.warn(
      '[EuroleagueApi] searchPlayer está deprecated. '
      'Use sendChatMessage() del backend en su lugar'
    );
    return null;
  }

  public static async comparePlayers(
    seasonCode: string,
    player1Name: string,
    player2Name: string
  ): Promise<[PlayerStats | null, PlayerStats | null]> {
    console.warn(
      '[EuroleagueApi] comparePlayers está deprecated. '
      'Use sendChatMessage() del backend en su lugar'
    );
    return [null, null];
  }
}

// Mapeo de palabras en español a campos de estadísticas
const STAT_MAP = {
  points: ["puntos", "anotador", "scorer", "scoring"],
  rebounds: ["rebotes", "reboteador", "rebounder", "rebounds"],
  assists: ["asistencias", "asistente", "asista", "assists"],
  steals: ["robos", "robo", "steals", "steal"],
  blocks: ["tapones", "tapón", "blocks", "block"],
  threePointsMade: ["triples", "triple", "three", "3puntos"],
  turnovers: ["pérdidas", "pérdida", "turnovers"],
  fouls: ["faltas", "falta", "fouls"],
} as const;


