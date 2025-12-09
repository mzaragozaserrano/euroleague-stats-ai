'use client';

import { useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { InitCheck } from './InitCheck';
import { AlertCircle, Clock } from 'lucide-react';

export interface ChatContainerProps {
  onSendMessage?: (message: string) => Promise<void>;
}

export function ChatContainer({ onSendMessage }: ChatContainerProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const error = useChatStore((state) => state.error);
  const coldStartWarning = useChatStore((state) => state.coldStartWarning);
  const rateLimitWarning = useChatStore((state) => state.rateLimitWarning);
  const sendMessage = useChatStore((state) => state.sendMessage);
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

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-950 dark:to-slate-900">
      {/* Init Check Overlay */}
      {!isInitialized && (
        <InitCheck onReady={() => setIsInitialized(true)} />
      )}

      {/* Header - Adjusted for mobile menu button */}
      <header className="border-b border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm px-4 py-4 md:px-6 md:py-5 shadow-sm">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-xl md:text-3xl font-bold bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-400 dark:to-blue-300 bg-clip-text text-transparent">
            Euroleague AI Stats
          </h1>
          <p className="text-xs md:text-base text-slate-600 dark:text-slate-400 mt-1 font-light">
            Consulta estadísticas en lenguaje natural
          </p>
        </div>
      </header>

      {/* Warnings - Refined */}
      {(coldStartWarning || rateLimitWarning) && (
        <div className="px-4 py-3 md:px-6 md:py-4 bg-amber-50/90 dark:bg-amber-950/30 border-b border-amber-200/50 dark:border-amber-800/30 backdrop-blur-sm">
          <div className="max-w-5xl mx-auto space-y-2">
            {coldStartWarning && (
              <div className="flex items-start gap-3 text-sm md:text-base text-amber-800 dark:text-amber-200 justify-between">
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 mt-0.5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                  <p className="font-medium">Despertando al agente... (primera consulta puede tardar 3+ segundos)</p>
                </div>
                <button
                  onClick={() => dismissWarnings()}
                  className="text-amber-700 dark:text-amber-300 hover:opacity-75 flex-shrink-0 text-lg"
                  aria-label="Cerrar advertencia"
                >
                  ×
                </button>
              </div>
            )}
            {rateLimitWarning && (
              <div className="flex items-start gap-3 text-sm md:text-base text-amber-800 dark:text-amber-200 justify-between">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                  <p className="font-medium">Se alcanzó límite de consultas (50/día). Vuelve mañana para más preguntas.</p>
                </div>
                <button
                  onClick={() => dismissWarnings()}
                  className="text-amber-700 dark:text-amber-300 hover:opacity-75 flex-shrink-0 text-lg"
                  aria-label="Cerrar advertencia"
                >
                  ×
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Global error - Refined */}
      {error && (
        <div className="px-4 py-4 md:px-6 md:py-5 bg-red-50/90 dark:bg-red-950/30 border-b border-red-200/50 dark:border-red-800/30 backdrop-blur-sm">
          <div className="max-w-5xl mx-auto flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-800 dark:text-red-200">Error</h3>
              <p className="text-sm text-red-700/80 dark:text-red-300/80 mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Messages area */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input area - Refined */}
      <div className="border-t border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm px-4 py-5 md:px-6 md:py-6 shadow-lg shadow-blue-500/5">
        <div className="max-w-5xl mx-auto">
          <ChatInput
            onSubmit={handleSendMessage}
            disabled={rateLimitWarning}
          />
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-3 font-light">
            Presiona <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono border border-slate-300 dark:border-slate-600">Enter</kbd> para enviar, <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono border border-slate-300 dark:border-slate-600">Shift+Enter</kbd> para nueva línea
          </p>
        </div>
      </div>
    </div>
  );
}

