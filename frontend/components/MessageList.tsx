'use client';

import { useEffect, useRef, useState } from 'react';
import { ChatMessage } from '@/stores/chatStore';
import { MessageBubble } from './MessageBubble';

export interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading = false }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [loadingMessage, setLoadingMessage] = useState('Pensando...');
  const loadingStartTimeRef = useRef<number | null>(null);
  const messageTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Manejar cambios en el mensaje de carga basado en el tiempo
  useEffect(() => {
    if (isLoading) {
      // Resetear mensaje cuando comienza a cargar
      setLoadingMessage('Pensando...');
      loadingStartTimeRef.current = Date.now();
      
      // Después de 2 segundos, cambiar a "Buscando información..."
      messageTimeoutRef.current = setTimeout(() => {
        setLoadingMessage('Buscando información...');
      }, 2000);
    } else {
      // Limpiar cuando deja de cargar
      loadingStartTimeRef.current = null;
      if (messageTimeoutRef.current) {
        clearTimeout(messageTimeoutRef.current);
        messageTimeoutRef.current = null;
      }
    }

    // Cleanup
    return () => {
      if (messageTimeoutRef.current) {
        clearTimeout(messageTimeoutRef.current);
      }
    };
  }, [isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="mb-4 inline-block">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-2xl font-bold">
              EA
            </div>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3">
            Euroleague AI Stats
          </h2>
          <p className="text-base text-slate-600 dark:text-slate-400 font-light mb-6">
            Consulta estadísticas de la Euroliga en lenguaje natural y obtén análisis instantáneos.
          </p>
          <div className="bg-blue-50 dark:bg-blue-950/30 rounded-xl p-4 border border-blue-200 dark:border-blue-800/30">
            <p className="text-xs md:text-sm text-slate-600 dark:text-slate-400 font-light">
              <span className="font-semibold text-slate-900 dark:text-slate-100">Ejemplos:</span><br />
              &quot;¿Cuántos puntos acumula Micic?&quot;<br />
              &quot;Compara los triples de Larkin vs Poirier&quot;
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6 space-y-6 md:space-y-8">
      <div className="max-w-5xl mx-auto w-full">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex justify-start mb-4 animate-fade-in">
            <div className="flex gap-3 items-center px-4 py-3 bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-bl-none shadow-sm">
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse" />
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
              <span className="text-sm text-slate-600 dark:text-slate-400 font-light ml-1">
                {loadingMessage}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

