/**
 * Script de prueba para el sistema de backup.
 * 
 * Ejecutar en la consola del navegador para probar todas las funcionalidades.
 */

import {
  createBackup,
  getAvailableBackups,
  restoreBackup,
  restoreLatestBackup,
  findLegacyData,
  recoverLegacyData,
} from './localStorageBackup';

/**
 * Ejecuta todas las pruebas del sistema de backup.
 */
export function testBackupSystem(): {
  tests: Array<{ name: string; passed: boolean; message: string }>;
  summary: { total: number; passed: number; failed: number };
} {
  const tests: Array<{ name: string; passed: boolean; message: string }> = [];

  console.log('=== Iniciando pruebas del sistema de backup ===\n');

  // Test 1: Verificar que se pueden crear backups
  try {
    const testData = {
      state: {
        sessions: [{ id: 'test-1', title: 'Test', messages: [] }],
        currentSessionId: 'test-1',
      },
      version: 5,
    };
    createBackup(testData, 5);
    const backups = getAvailableBackups();
    const hasBackup = backups.length > 0;
    tests.push({
      name: 'Crear backup',
      passed: hasBackup,
      message: hasBackup
        ? `✓ Backup creado correctamente (${backups.length} backups disponibles)`
        : '✗ No se pudo crear backup',
    });
  } catch (error) {
    tests.push({
      name: 'Crear backup',
      passed: false,
      message: `✗ Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    });
  }

  // Test 2: Verificar que se pueden listar backups
  try {
    const backups = getAvailableBackups();
    tests.push({
      name: 'Listar backups',
      passed: true,
      message: `✓ Se encontraron ${backups.length} backups`,
    });
  } catch (error) {
    tests.push({
      name: 'Listar backups',
      passed: false,
      message: `✗ Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    });
  }

  // Test 3: Verificar búsqueda de datos legacy
  try {
    const legacy = findLegacyData();
    tests.push({
      name: 'Buscar datos legacy',
      passed: true,
      message: legacy.found
        ? `✓ Datos legacy encontrados en: ${legacy.keys.join(', ')}`
        : '✓ No hay datos legacy (esto es normal si no hay datos antiguos)',
    });
  } catch (error) {
    tests.push({
      name: 'Buscar datos legacy',
      passed: false,
      message: `✗ Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    });
  }

  // Test 4: Verificar que se puede restaurar un backup (si existe)
  try {
    const backups = getAvailableBackups();
    if (backups.length > 0) {
      const restored = restoreBackup(backups[0]);
      tests.push({
        name: 'Restaurar backup',
        passed: restored,
        message: restored
          ? `✓ Backup restaurado correctamente`
          : '✗ No se pudo restaurar backup',
      });
    } else {
      tests.push({
        name: 'Restaurar backup',
        passed: true,
        message: '⚠ No hay backups para restaurar (esto es normal)',
      });
    }
  } catch (error) {
    tests.push({
      name: 'Restaurar backup',
      passed: false,
      message: `✗ Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    });
  }

  // Test 5: Verificar recuperación de datos legacy
  try {
    const recovery = recoverLegacyData();
    tests.push({
      name: 'Recuperar datos legacy',
      passed: recovery.success || !recovery.message.includes('Error'),
      message: recovery.success
        ? `✓ ${recovery.message}`
        : `⚠ ${recovery.message}`,
    });
  } catch (error) {
    tests.push({
      name: 'Recuperar datos legacy',
      passed: false,
      message: `✗ Error: ${error instanceof Error ? error.message : 'Error desconocido'}`,
    });
  }

  // Resumen
  const passed = tests.filter((t) => t.passed).length;
  const failed = tests.filter((t) => !t.passed).length;

  console.log('\n=== Resultados ===');
  tests.forEach((test) => {
    console.log(`${test.passed ? '✓' : '✗'} ${test.name}: ${test.message}`);
  });

  console.log(`\n=== Resumen ===`);
  console.log(`Total: ${tests.length}`);
  console.log(`Pasados: ${passed}`);
  console.log(`Fallidos: ${failed}`);

  return {
    tests,
    summary: {
      total: tests.length,
      passed,
      failed,
    },
  };
}

// Exportar para uso en consola del navegador
if (typeof window !== 'undefined') {
  (window as any).testBackupSystem = testBackupSystem;
}

