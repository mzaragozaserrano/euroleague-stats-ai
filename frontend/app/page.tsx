'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';
import { findLegacyData, recoverLegacyData } from '@/lib/localStorageBackup';

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Verificar y recuperar datos legacy al montar el componente
  useEffect(() => {
    // Ejecutar después de que el componente se monte
    const timer = setTimeout(() => {
      const legacy = findLegacyData();
      if (legacy.found && legacy.data) {
        // Verificar si ya hay sesiones en el estado actual
        const currentData = localStorage.getItem('chat-storage');
        let hasSessions = false;
        
        if (currentData) {
          try {
            const parsed = JSON.parse(currentData);
            hasSessions = parsed.state?.sessions?.length > 0;
          } catch (e) {
            // Ignorar errores de parseo
          }
        }
        
        // Solo recuperar si no hay sesiones actuales
        if (!hasSessions) {
          const recovery = recoverLegacyData();
          if (recovery.success) {
            // Recargar la página para aplicar los cambios
            window.location.reload();
          }
        }
      }
    }, 1000); // Esperar 1 segundo para que el store se inicialice

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex h-screen">
      {/* Sidebar - Oculto en móvil, visible en desktop */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Overlay en móvil */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col relative">
        {/* Toggle Sidebar Button (móvil) */}
        <div className="md:hidden absolute top-4 left-4 z-50">
          <Button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            size="sm"
            variant="outline"
            className="gap-1.5"
          >
            {sidebarOpen ? (
              <X className="w-4 h-4" />
            ) : (
              <Menu className="w-4 h-4" />
            )}
          </Button>
        </div>

        <ChatContainer />
      </div>
    </div>
  );
}


