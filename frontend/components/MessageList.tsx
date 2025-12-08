'use client';

import { useEffect, useRef } from 'react';
import { ChatMessage } from '@/stores/chatStore';
import { MessageBubble } from './MessageBubble';

export interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading = false }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg md:text-xl font-semibold mb-2">
            Bienvenido a Euroleague AI Stats
          </h2>
          <p className="text-sm md:text-base text-muted-foreground">
            Haz una pregunta sobre estadísticas de la Euroliga y obtén respuestas instantáneas.
          </p>
          <p className="text-xs md:text-sm text-muted-foreground mt-4">
            Ejemplos: "¿Cuántos puntos promedio anotó Micic?" o "Compara los triples de Larkin vs Poirier"
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="flex gap-1 px-4 py-2 bg-muted rounded-lg rounded-bl-none">
            <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

