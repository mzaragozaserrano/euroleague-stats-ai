/**
 * Script para verificar y recuperar datos legacy del localStorage.
 * 
 * Ejecutar en la consola del navegador para verificar si hay datos antiguos.
 */

import { findLegacyData, recoverLegacyData, getAvailableBackups } from './localStorageBackup';

/**
 * Verifica y muestra información sobre datos legacy y backups disponibles.
 */
export function checkAndRecoverData(): {
  legacyFound: boolean;
  backupsAvailable: number;
  recoveryAttempted: boolean;
  recoveryResult: any;
} {
  console.log('=== Verificación de Datos Legacy ===');
  
  // 1. Buscar datos legacy
  const legacy = findLegacyData();
  console.log('Datos legacy encontrados:', legacy);
  
  // 2. Buscar backups
  const backups = getAvailableBackups();
  console.log(`Backups disponibles: ${backups.length}`);
  if (backups.length > 0) {
    console.log('Backups:', backups.map(b => ({
      version: b.version,
      fecha: new Date(b.timestamp).toISOString(),
      sesiones: b.data?.state?.sessions?.length || 0,
    })));
  }
  
  // 3. Intentar recuperar si hay datos legacy
  let recoveryResult = null;
  if (legacy.found) {
    console.log('Intentando recuperar datos legacy...');
    recoveryResult = recoverLegacyData();
    console.log('Resultado de recuperación:', recoveryResult);
  }
  
  return {
    legacyFound: legacy.found,
    backupsAvailable: backups.length,
    recoveryAttempted: legacy.found,
    recoveryResult,
  };
}

// Exportar para uso en consola del navegador
if (typeof window !== 'undefined') {
  (window as any).checkLegacyData = checkAndRecoverData;
  (window as any).recoverLegacyData = recoverLegacyData;
  (window as any).getBackups = getAvailableBackups;
  (window as any).findLegacyData = findLegacyData;
  (window as any).restoreLatestBackup = restoreLatestBackup;
}

