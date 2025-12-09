'use client';

import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

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


