'use client';

/**
 * Componente que inicializa las funciones de backup en window para uso en consola.
 * Se ejecuta solo en el cliente.
 */
import { useEffect } from 'react';
import { checkAndRecoverData } from '@/lib/checkLegacyData';
import { testBackupSystem } from '@/lib/testBackupSystem';
import {
  findLegacyData,
  recoverLegacyData,
  getAvailableBackups,
  restoreLatestBackup,
} from '@/lib/localStorageBackup';

export function BackupSystemInit() {
  useEffect(() => {
    // Exportar funciones a window para uso en consola del navegador
    if (typeof window !== 'undefined') {
      (window as any).checkLegacyData = checkAndRecoverData;
      (window as any).recoverLegacyData = recoverLegacyData;
      (window as any).getBackups = getAvailableBackups;
      (window as any).findLegacyData = findLegacyData;
      (window as any).restoreLatestBackup = restoreLatestBackup;
      (window as any).testBackupSystem = testBackupSystem;

      console.log('[BackupSystem] Funciones disponibles en consola:');
      console.log('  - checkLegacyData() - Verificar y recuperar datos legacy');
      console.log('  - recoverLegacyData() - Recuperar datos legacy manualmente');
      console.log('  - getBackups() - Listar backups disponibles');
      console.log('  - findLegacyData() - Buscar datos legacy');
      console.log('  - restoreLatestBackup() - Restaurar backup más reciente');
      console.log('  - testBackupSystem() - Ejecutar pruebas del sistema');
    }
  }, []);

  // Este componente no renderiza nada
  return null;
}

