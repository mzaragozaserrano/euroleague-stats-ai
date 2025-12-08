/**
 * Servicio de Caché para Estadísticas de Jugadores
 * 
 * Almacena stats de jugadores por temporada en localStorage.
 * Se invalida automáticamente después de las 7 AM cada día.
 * 
 * Estructura:
 * - player-stats-cache: { [seasoncode]: { data, timestamp, lastSync } }
 * - cache-metadata: { lastCleared, version }
 */

export interface PlayerStats {
  playerId: string;
  playerName: string;
  teamCode: string;
  seasonCode: string;
  points?: number;
  rebounds?: number;
  assists?: number;
  [key: string]: any; // Otras stats de la API
}

export interface SeasonCacheEntry {
  data: PlayerStats[];
  timestamp: number; // Cuándo se guardó
  lastSync: number; // Última sincronización con API
}

export interface CacheMetadata {
  lastCleared: number; // Timestamp de última limpieza (7 AM)
  version: number;
}

const CACHE_KEY = 'player-stats-cache';
const METADATA_KEY = 'cache-metadata';
const CACHE_VERSION = 1;
const SYNC_HOUR = 7; // 7 AM

export class PlayerStatsCache {
  /**
   * Obtiene la hora de la última sincronización (7 AM de hoy)
   */
  private static getLastSyncTime(): number {
    const now = new Date();
    const syncTime = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      SYNC_HOUR,
      0,
      0,
      0
    );
    
    // Si aún no son las 7 AM, usar el 7 AM de ayer
    if (now < syncTime) {
      syncTime.setDate(syncTime.getDate() - 1);
    }
    
    return syncTime.getTime();
  }

  /**
   * Verifica si el caché debe invalidarse (después de las 7 AM)
   */
  private static shouldInvalidateCache(): boolean {
    try {
      const metadata = this.getMetadata();
      const lastSyncTime = this.getLastSyncTime();
      
      // Si nunca se ha limpiado o la última limpieza fue antes de las 7 AM de hoy
      if (!metadata.lastCleared || metadata.lastCleared < lastSyncTime) {
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('[PlayerStatsCache] Error verificando invalidación:', error);
      return false;
    }
  }

  /**
   * Obtiene metadata del caché
   */
  private static getMetadata(): CacheMetadata {
    try {
      const stored = localStorage.getItem(METADATA_KEY);
      if (!stored) {
        return { lastCleared: 0, version: CACHE_VERSION };
      }
      
      const metadata = JSON.parse(stored) as CacheMetadata;
      
      // Migración de versiones si es necesario
      if (metadata.version !== CACHE_VERSION) {
        this.clearAllCache();
        return { lastCleared: Date.now(), version: CACHE_VERSION };
      }
      
      return metadata;
    } catch (error) {
      console.error('[PlayerStatsCache] Error leyendo metadata:', error);
      return { lastCleared: 0, version: CACHE_VERSION };
    }
  }

  /**
   * Actualiza metadata del caché
   */
  private static setMetadata(metadata: CacheMetadata): void {
    try {
      localStorage.setItem(METADATA_KEY, JSON.stringify(metadata));
    } catch (error) {
      console.error('[PlayerStatsCache] Error guardando metadata:', error);
    }
  }

  /**
   * Invalida el caché si es necesario (después de las 7 AM)
   */
  public static checkAndInvalidate(): boolean {
    if (this.shouldInvalidateCache()) {
      console.log('[PlayerStatsCache] Invalidando caché (después de 7 AM)');
      this.clearAllCache();
      return true;
    }
    return false;
  }

  /**
   * Limpia TODO el caché de datos (mantiene consultas SQL del chatStore)
   */
  public static clearAllCache(): void {
    try {
      localStorage.removeItem(CACHE_KEY);
      this.setMetadata({
        lastCleared: Date.now(),
        version: CACHE_VERSION,
      });
      console.log('[PlayerStatsCache] Caché limpiado completamente');
    } catch (error) {
      console.error('[PlayerStatsCache] Error limpiando caché:', error);
    }
  }

  /**
   * Obtiene stats de una temporada desde el caché
   */
  public static getSeasonStats(seasonCode: string): PlayerStats[] | null {
    try {
      // Verificar si debe invalidarse
      this.checkAndInvalidate();
      
      const stored = localStorage.getItem(CACHE_KEY);
      if (!stored) {
        return null;
      }
      
      const cache = JSON.parse(stored) as Record<string, SeasonCacheEntry>;
      const seasonEntry = cache[seasonCode];
      
      if (!seasonEntry) {
        console.log(`[PlayerStatsCache] No hay datos en caché para ${seasonCode}`);
        return null;
      }
      
      console.log(
        `[PlayerStatsCache] Datos encontrados en caché para ${seasonCode}:`,
        seasonEntry.data.length,
        'jugadores'
      );
      
      return seasonEntry.data;
    } catch (error) {
      console.error('[PlayerStatsCache] Error leyendo caché:', error);
      return null;
    }
  }

  /**
   * Guarda stats de una temporada en el caché
   */
  public static setSeasonStats(seasonCode: string, stats: PlayerStats[]): void {
    try {
      const stored = localStorage.getItem(CACHE_KEY);
      const cache: Record<string, SeasonCacheEntry> = stored
        ? JSON.parse(stored)
        : {};
      
      cache[seasonCode] = {
        data: stats,
        timestamp: Date.now(),
        lastSync: this.getLastSyncTime(),
      };
      
      localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
      
      console.log(
        `[PlayerStatsCache] Guardados ${stats.length} jugadores para ${seasonCode}`
      );
    } catch (error) {
      console.error('[PlayerStatsCache] Error guardando caché:', error);
      
      // Si hay error de espacio, limpiar caché antiguo
      if (error instanceof Error && error.name === 'QuotaExceededError') {
        console.warn('[PlayerStatsCache] Espacio insuficiente, limpiando caché...');
        this.clearAllCache();
      }
    }
  }

  /**
   * Verifica si hay datos en caché para una temporada
   */
  public static hasSeasonStats(seasonCode: string): boolean {
    return this.getSeasonStats(seasonCode) !== null;
  }

  /**
   * Obtiene información de debug del caché
   */
  public static getDebugInfo(): {
    metadata: CacheMetadata;
    seasons: string[];
    totalPlayers: number;
    shouldInvalidate: boolean;
    nextSyncTime: string;
  } {
    const metadata = this.getMetadata();
    const stored = localStorage.getItem(CACHE_KEY);
    const cache: Record<string, SeasonCacheEntry> = stored
      ? JSON.parse(stored)
      : {};
    
    const seasons = Object.keys(cache);
    const totalPlayers = seasons.reduce(
      (sum, season) => sum + cache[season].data.length,
      0
    );
    
    const nextSync = new Date(this.getLastSyncTime());
    nextSync.setDate(nextSync.getDate() + 1);
    
    return {
      metadata,
      seasons,
      totalPlayers,
      shouldInvalidate: this.shouldInvalidateCache(),
      nextSyncTime: nextSync.toLocaleString('es-ES'),
    };
  }
}

