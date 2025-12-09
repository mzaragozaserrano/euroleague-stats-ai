/**
 * Sistema de backup automático para localStorage del chat.
 * 
 * Crea backups automáticos antes de migraciones y permite restaurar.
 */

const BACKUP_PREFIX = 'chat-storage-backup-';
const MAX_BACKUPS = 5; // Mantener solo los últimos 5 backups

export interface BackupInfo {
  timestamp: number;
  version: number;
  data: any;
}

/**
 * Crea un backup del estado actual antes de una migración.
 */
export function createBackup(currentData: any, version: number): void {
  try {
    const backup: BackupInfo = {
      timestamp: Date.now(),
      version,
      data: currentData,
    };

    const backupKey = `${BACKUP_PREFIX}${backup.timestamp}`;
    localStorage.setItem(backupKey, JSON.stringify(backup));

    // Limpiar backups antiguos (mantener solo los últimos MAX_BACKUPS)
    cleanupOldBackups();

    console.log(`[Backup] Creado backup v${version} en ${new Date(backup.timestamp).toISOString()}`);
  } catch (error) {
    console.error('[Backup] Error creando backup:', error);
  }
}

/**
 * Obtiene todos los backups disponibles ordenados por fecha (más reciente primero).
 */
export function getAvailableBackups(): BackupInfo[] {
  const backups: BackupInfo[] = [];

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(BACKUP_PREFIX)) {
        try {
          const backupData = localStorage.getItem(key);
          if (backupData) {
            const backup: BackupInfo = JSON.parse(backupData);
            backups.push(backup);
          }
        } catch (parseError) {
          console.warn(`[Backup] Error parseando backup ${key}:`, parseError);
        }
      }
    }
  } catch (error) {
    console.error('[Backup] Error obteniendo backups:', error);
  }

  // Ordenar por timestamp (más reciente primero)
  return backups.sort((a, b) => b.timestamp - a.timestamp);
}

/**
 * Restaura un backup específico.
 */
export function restoreBackup(backup: BackupInfo): boolean {
  try {
    if (!backup || !backup.data) {
      console.error('[Backup] Backup inválido');
      return false;
    }

    // Restaurar el estado completo
    localStorage.setItem('chat-storage', JSON.stringify(backup.data));

    console.log(`[Backup] Restaurado backup v${backup.version} del ${new Date(backup.timestamp).toISOString()}`);
    return true;
  } catch (error) {
    console.error('[Backup] Error restaurando backup:', error);
    return false;
  }
}

/**
 * Restaura el backup más reciente disponible.
 */
export function restoreLatestBackup(): boolean {
  const backups = getAvailableBackups();
  if (backups.length === 0) {
    console.warn('[Backup] No hay backups disponibles');
    return false;
  }

  const latestBackup = backups[0];
  return restoreBackup(latestBackup);
}

/**
 * Limpia backups antiguos, manteniendo solo los últimos MAX_BACKUPS.
 */
function cleanupOldBackups(): void {
  try {
    const backups = getAvailableBackups();

    if (backups.length > MAX_BACKUPS) {
      // Eliminar los backups más antiguos
      const backupsToDelete = backups.slice(MAX_BACKUPS);
      
      for (const backup of backupsToDelete) {
        const backupKey = `${BACKUP_PREFIX}${backup.timestamp}`;
        localStorage.removeItem(backupKey);
      }

      console.log(`[Backup] Eliminados ${backupsToDelete.length} backups antiguos`);
    }
  } catch (error) {
    console.error('[Backup] Error limpiando backups antiguos:', error);
  }
}

/**
 * Verifica si hay datos antiguos en localStorage que no sean backups.
 * Busca posibles versiones antiguas del storage.
 */
export function findLegacyData(): {
  found: boolean;
  data: any | null;
  keys: string[];
} {
  const legacyKeys: string[] = [];
  let legacyData: any = null;

  try {
    // Buscar posibles claves antiguas
    const possibleKeys = [
      'chat-storage',
      'chat-history',
      'chat-messages',
      'euroleague-chat',
    ];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && possibleKeys.some(k => key.includes(k) && !key.startsWith(BACKUP_PREFIX))) {
        legacyKeys.push(key);
        
        // Si es la clave principal, intentar parsear
        if (key === 'chat-storage') {
          try {
            const data = localStorage.getItem(key);
            if (data) {
              legacyData = JSON.parse(data);
            }
          } catch (parseError) {
            console.warn(`[Backup] Error parseando ${key}:`, parseError);
          }
        }
      }
    }
  } catch (error) {
    console.error('[Backup] Error buscando datos legacy:', error);
  }

  return {
    found: legacyKeys.length > 0,
    data: legacyData,
    keys: legacyKeys,
  };
}

/**
 * Intenta recuperar y convertir datos legacy a formato actual.
 */
export function recoverLegacyData(): {
  success: boolean;
  recoveredSessions: number;
  message: string;
} {
  const legacy = findLegacyData();
  
  if (!legacy.found || !legacy.data) {
    return {
      success: false,
      recoveredSessions: 0,
      message: 'No se encontraron datos legacy para recuperar',
    };
  }

  try {
    // Intentar convertir datos legacy a formato de sesiones
    const data = legacy.data;
    let recoveredSessions = 0;

    // Si tiene sessions, ya está en formato nuevo
    if (data.state?.sessions && Array.isArray(data.state.sessions)) {
      return {
        success: true,
        recoveredSessions: data.state.sessions.length,
        message: `Datos ya en formato actual: ${data.state.sessions.length} sesiones encontradas`,
      };
    }

    // Si tiene messages o history, convertir a sesión
    const oldMessages = data.state?.messages || data.state?.history || data.messages || data.history || [];
    
    if (oldMessages.length > 0) {
      // Crear una sesión con los mensajes antiguos
      const recoveredSession = {
        id: `recovered-${Date.now()}`,
        title: 'Conversación recuperada',
        messages: oldMessages,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        isLoading: false,
      };

      // Guardar en formato actual
      const currentData = localStorage.getItem('chat-storage');
      let currentState: any = { state: { sessions: [], currentSessionId: null } };

      if (currentData) {
        try {
          currentState = JSON.parse(currentData);
        } catch (e) {
          // Si falla, usar estado por defecto
        }
      }

      // Agregar sesión recuperada
      currentState.state = {
        ...currentState.state,
        sessions: [recoveredSession, ...(currentState.state?.sessions || [])],
        currentSessionId: recoveredSession.id,
      };

      // Actualizar versión
      currentState.version = 5;

      localStorage.setItem('chat-storage', JSON.stringify(currentState));
      recoveredSessions = 1;

      return {
        success: true,
        recoveredSessions: 1,
        message: `Recuperada 1 conversación con ${oldMessages.length} mensajes`,
      };
    }

    return {
      success: false,
      recoveredSessions: 0,
      message: 'No se encontraron mensajes para recuperar',
    };
  } catch (error) {
    console.error('[Backup] Error recuperando datos legacy:', error);
    return {
      success: false,
      recoveredSessions: 0,
      message: `Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    };
  }
}

