'use client';

import { useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { Card } from '@/components/ui/card';
import { AlertCircle, Clock } from 'lucide-react';

export interface ChatContainerProps {
  onSendMessage?: (message: string) => Promise<void>;
}

export function ChatContainer({ onSendMessage }: ChatContainerProps) {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const error = useChatStore((state) => state.error);
  const coldStartWarning = useChatStore((state) => state.coldStartWarning);
  const rateLimitWarning = useChatStore((state) => state.rateLimitWarning);
  const sendMessage = useChatStore((state) => state.sendMessage);

  const handleSendMessage = async (content: string) => {
    // Si hay un callback externo, usar ese (para testing o customización)
    if (onSendMessage) {
      await onSendMessage(content);
    } else {
      // De lo contrario, usar el método sendMessage del store (integración API)
      await sendMessage(content);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card px-4 py-3 md:px-6 md:py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl md:text-2xl font-bold">Euroleague AI Stats</h1>
          <p className="text-xs md:text-sm text-muted-foreground">
            Consulta estadísticas de la Euroliga en lenguaje natural
          </p>
        </div>
      </header>

      {/* Warnings */}
      {(coldStartWarning || rateLimitWarning) && (
        <div className="px-4 py-2 md:px-6 md:py-3 bg-yellow-50 dark:bg-yellow-950 border-b">
          <div className="max-w-4xl mx-auto space-y-2">
            {coldStartWarning && (
              <div className="flex items-start gap-2 text-sm md:text-base text-yellow-800 dark:text-yellow-200">
                <Clock className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>Despertando al agente... (primera consulta puede tardar 3+ segundos)</p>
              </div>
            )}
            {rateLimitWarning && (
              <div className="flex items-start gap-2 text-sm md:text-base text-yellow-800 dark:text-yellow-200">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>Se alcanzó límite de consultas (50/día). Vuelve mañana para más preguntas.</p>
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

