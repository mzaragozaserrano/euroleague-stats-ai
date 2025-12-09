'use client';

import { useEffect, useState } from 'react';
import { checkInit, getInitStatus, type InitStatus } from '@/lib/api';
import { Loader2, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface InitCheckProps {
  onReady: () => void;
}

export function InitCheck({ onReady }: InitCheckProps) {
  const [status, setStatus] = useState<InitStatus | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout | null = null;
    let isMounted = true;

    const initialize = async () => {
      try {
        // PRIMERO: Verificar estado SIN ejecutar ETL (rápido)
        const initialStatus = await getInitStatus();
        
        if (!isMounted) return;
        
        // Si está listo, continuar inmediatamente sin mostrar overlay
        if (initialStatus.status === 'ready') {
          setIsChecking(false);
          onReady();
          return;
        }

        // Si NO está listo, ENTONCES ejecutar ETL y mostrar overlay
        if (initialStatus.status === 'initializing') {
          setStatus(initialStatus);
          
          // Ahora sí llamar a checkInit() para ejecutar ETL
          const initResult = await checkInit();
          
          if (!isMounted) return;
          setStatus(initResult);
          
          // Si ya está listo después de ejecutar ETL
          if (initResult.status === 'ready') {
            setIsChecking(false);
            onReady();
            return;
          }
          
          // Si sigue inicializando, hacer polling cada 2 segundos
          if (initResult.status === 'initializing') {
            pollInterval = setInterval(async () => {
              if (!isMounted) return;

              const currentStatus = await getInitStatus();
              
              if (!isMounted) return;
              
              setStatus(currentStatus);

              // Si está listo, detener polling y continuar
              if (currentStatus.status === 'ready') {
                if (pollInterval) {
                  clearInterval(pollInterval);
                  pollInterval = null;
                }
                setIsChecking(false);
                onReady();
              }
            }, 2000); // Poll cada 2 segundos
          }
        } else {
          // Error
          setStatus(initialStatus);
          setIsChecking(false);
        }
      } catch (error) {
        console.error('Error inicializando:', error);
        if (isMounted) {
          setStatus({
            status: 'error',
            has_teams: false,
            has_players: false,
            message: 'Error conectando con el servidor',
          });
          setIsChecking(false);
        }
      }
    };

    initialize();

    return () => {
      isMounted = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [onReady]);

  // No mostrar overlay si:
  // - Está listo
  // - Aún está verificando (no hay status todavía)
  if (status?.status === 'ready' || (!status && isChecking)) {
    return null;
  }

  // Solo mostrar overlay si realmente está inicializando o hay error
  if (status?.status !== 'initializing' && status?.status !== 'error') {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-6 md:p-8 bg-white dark:bg-slate-900 shadow-xl">
        <div className="flex flex-col items-center text-center space-y-6">
          {status?.status === 'initializing' ? (
            <>
              <Loader2 className="w-16 h-16 text-blue-600 dark:text-blue-400 animate-spin" />
              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3">
                  Inicializando sitio web
                </h2>
                <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 mb-2">
                  Preparando todo para ti...
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500">
                  Esto puede tardar unos minutos la primera vez
                </p>
              </div>
            </>
          ) : status?.status === 'error' ? (
            <>
              <AlertCircle className="w-12 h-12 text-red-600 dark:text-red-400" />
              <div>
                <h2 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Error de Inicialización
                </h2>
                <p className="text-sm md:text-base text-slate-600 dark:text-slate-400">
                  {status.message || 'No se pudo inicializar'}
                </p>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm md:text-base"
              >
                Reintentar
              </button>
            </>
          ) : (
            <>
              <Loader2 className="w-16 h-16 text-blue-600 dark:text-blue-400 animate-spin" />
              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3">
                  Inicializando sitio web
                </h2>
                <p className="text-sm md:text-base text-slate-600 dark:text-slate-400">
                  Conectando con el servidor...
                </p>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
