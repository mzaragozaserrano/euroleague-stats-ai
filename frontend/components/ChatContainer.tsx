'use client';

import { useEffect, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, Clock, Trash2 } from 'lucide-react';

export interface ChatContainerProps {
  onSendMessage?: (message: string) => Promise<void>;
}

export function ChatContainer({ onSendMessage }: ChatContainerProps) {
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const error = useChatStore((state) => state.error);
  const coldStartWarning = useChatStore((state) => state.coldStartWarning);
  const rateLimitWarning = useChatStore((state) => state.rateLimitWarning);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const clearHistory = useChatStore((state) => state.clearHistory);
  const dismissWarnings = useChatStore((state) => state.dismissWarnings);

  const handleSendMessage = async (content: string) => {
    // Si hay un callback externo, usar ese (para testing o customización)
    if (onSendMessage) {
      await onSendMessage(content);
    } else {
      // De lo contrario, usar el método sendMessage del store (integración API)
      await sendMessage(content);
    }
  };

  const handleClearHistory = () => {
    if (clearHistory(true)) {
      setShowClearConfirm(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card px-4 py-3 md:px-6 md:py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex-1">
            <h1 className="text-xl md:text-2xl font-bold">Euroleague AI Stats</h1>
            <p className="text-xs md:text-sm text-muted-foreground">
              Consulta estadísticas de la Euroliga en lenguaje natural
            </p>
          </div>
          
          {/* Clear history button */}
          {messages.length > 0 && (
            <div className="flex items-center gap-2">
              {showClearConfirm ? (
                <div className="flex gap-2 animate-in fade-in-50 duration-200">
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleClearHistory}
                  >
                    Confirmar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowClearConfirm(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              ) : (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowClearConfirm(true)}
                  className="gap-1"
                >
                  <Trash2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Limpiar</span>
                </Button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Warnings */}
      {(coldStartWarning || rateLimitWarning) && (
        <div className="px-4 py-2 md:px-6 md:py-3 bg-yellow-50 dark:bg-yellow-950 border-b">
          <div className="max-w-4xl mx-auto space-y-2">
            {coldStartWarning && (
              <div className="flex items-start gap-2 text-sm md:text-base text-yellow-800 dark:text-yellow-200 justify-between">
                <div className="flex items-start gap-2">
                  <Clock className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <p>Despertando al agente... (primera consulta puede tardar 3+ segundos)</p>
                </div>
                <button
                  onClick={() => dismissWarnings()}
                  className="text-yellow-700 dark:text-yellow-300 hover:opacity-75 flex-shrink-0"
                  aria-label="Cerrar advertencia"
                >
                  ×
                </button>
              </div>
            )}
            {rateLimitWarning && (
              <div className="flex items-start gap-2 text-sm md:text-base text-yellow-800 dark:text-yellow-200 justify-between">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <p>Se alcanzó límite de consultas (50/día). Vuelve mañana para más preguntas.</p>
                </div>
                <button
                  onClick={() => dismissWarnings()}
                  className="text-yellow-700 dark:text-yellow-300 hover:opacity-75 flex-shrink-0"
                  aria-label="Cerrar advertencia"
                >
                  ×
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Global error */}
      {error && (
        <div className="px-4 py-3 md:px-6 md:py-4 bg-destructive/10 border-b border-destructive/20">
          <div className="max-w-4xl mx-auto flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-destructive">Error</h3>
              <p className="text-sm text-destructive/80">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Messages area */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input area */}
      <div className="border-t bg-card px-4 py-4 md:px-6 md:py-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSubmit={handleSendMessage}
            disabled={rateLimitWarning}
          />
          <p className="text-xs text-muted-foreground mt-2">
            Presiona Enter para enviar, Shift+Enter para nueva línea
          </p>
        </div>
      </div>
    </div>
  );
}

