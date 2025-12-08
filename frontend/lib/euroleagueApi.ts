/**
 * Cliente para API de Euroleague
 * 
 * Obtiene estadísticas de jugadores directamente desde la API oficial.
 * Integra con PlayerStatsCache para optimizar llamadas.
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
   * Obtiene estadísticas de jugadores para una temporada.
   * Prioriza caché local antes de llamar a la API.
   * 
   * @param seasonCode Código de temporada (E2024, E2025)
   * @param forceRefresh Forzar llamada a API ignorando caché
   */
  public static async getPlayerStats(
    seasonCode: string,
    forceRefresh = false
  ): Promise<PlayerStats[]> {
    try {
      // 1. Verificar invalidación automática (7 AM)
      PlayerStatsCache.checkAndInvalidate();

      // 2. Intentar obtener desde caché (si no se fuerza refresh)
      if (!forceRefresh) {
        const cached = PlayerStatsCache.getSeasonStats(seasonCode);
        if (cached) {
          console.log(`[EuroleagueApi] Usando datos de caché para ${seasonCode}`);
          return cached;
        }
      }

      // 3. Llamar a la API de Euroleague
      console.log(`[EuroleagueApi] Obteniendo datos de API para ${seasonCode}`);
      const stats = await this.fetchFromApi(seasonCode);

      // 4. Guardar en caché
      PlayerStatsCache.setSeasonStats(seasonCode, stats);

      return stats;
    } catch (error) {
      console.error('[EuroleagueApi] Error obteniendo stats:', error);

      // Si hay error de API, intentar usar caché como fallback
      const cached = PlayerStatsCache.getSeasonStats(seasonCode);
      if (cached) {
        console.warn('[EuroleagueApi] Usando caché como fallback después de error de API');
        return cached;
      }

      throw error;
    }
  }

  /**
   * Llama a la API de Euroleague para obtener estadísticas
   */
  private static async fetchFromApi(seasonCode: string): Promise<PlayerStats[]> {
    try {
      // Endpoint real de Euroleague (ajustar según documentación oficial)
      const url = `${EUROLEAGUE_API_BASE}/statistics/players?seasonCode=${seasonCode}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        // Timeout de 10 segundos
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        throw new EuroleagueApiError(
          `API retornó status ${response.status}`,
          response.status
        );
      }

      const data = await response.json();

      // Transformar respuesta de API al formato interno
      return this.transformApiResponse(data, seasonCode);
    } catch (error) {
      if (error instanceof EuroleagueApiError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new EuroleagueApiError('Timeout al conectar con Euroleague API');
        }
        throw new EuroleagueApiError(`Error de red: ${error.message}`);
      }

      throw new EuroleagueApiError('Error desconocido al llamar a la API');
    }
  }

  /**
   * Transforma la respuesta de la API al formato interno
   */
  private static transformApiResponse(
    apiData: any,
    seasonCode: string
  ): PlayerStats[] {
    try {
      // Ajustar según estructura real de la API de Euroleague
      // Este es un ejemplo genérico
      const players = apiData.data || apiData.players || [];

      return players.map((player: any) => ({
        playerId: player.playerId || player.id,
        playerName: player.playerName || player.name,
        teamCode: player.teamCode || player.team,
        seasonCode,
        points: player.points || 0,
        rebounds: player.rebounds || player.reboundsTotal || 0,
        assists: player.assists || 0,
        steals: player.steals || 0,
        blocks: player.blocks || 0,
        turnovers: player.turnovers || 0,
        fouls: player.fouls || 0,
        games: player.games || player.gamesPlayed || 0,
        // Incluir otros campos relevantes
        ...player,
      }));
    } catch (error) {
      console.error('[EuroleagueApi] Error transformando respuesta:', error);
      throw new EuroleagueApiError('Error procesando respuesta de la API');
    }
  }

  /**
   * Filtra jugadores por estadística y retorna top N
   */
  public static async getTopPlayers(
    seasonCode: string,
    stat: keyof PlayerStats,
    topN = 10,
    teamCode?: string
  ): Promise<PlayerStats[]> {
    const allStats = await this.getPlayerStats(seasonCode);

    // Filtrar por equipo si se especifica
    let filtered = allStats;
    if (teamCode) {
      filtered = allStats.filter(
        (player) => player.teamCode?.toUpperCase() === teamCode.toUpperCase()
      );
    }

    // Ordenar por estadística y tomar top N
    return filtered
      .filter((player) => typeof player[stat] === 'number')
      .sort((a, b) => {
        const aVal = a[stat] as number;
        const bVal = b[stat] as number;
        return bVal - aVal;
      })
      .slice(0, topN);
  }

  /**
   * Busca un jugador específico por nombre
   */
  public static async searchPlayer(
    seasonCode: string,
    playerName: string
  ): Promise<PlayerStats | null> {
    const allStats = await this.getPlayerStats(seasonCode);

    const found = allStats.find((player) =>
      player.playerName.toLowerCase().includes(playerName.toLowerCase())
    );

    return found || null;
  }

  /**
   * Compara dos jugadores
   */
  public static async comparePlayers(
    seasonCode: string,
    player1Name: string,
    player2Name: string
  ): Promise<[PlayerStats | null, PlayerStats | null]> {
    const allStats = await this.getPlayerStats(seasonCode);

    const player1 = allStats.find((p) =>
      p.playerName.toLowerCase().includes(player1Name.toLowerCase())
    );

    const player2 = allStats.find((p) =>
      p.playerName.toLowerCase().includes(player2Name.toLowerCase())
    );

    return [player1 || null, player2 || null];
  }
}

