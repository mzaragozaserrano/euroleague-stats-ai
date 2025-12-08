'use client';

import { ChatMessage } from '@/stores/chatStore';
import { Card } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

export interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-none'
            : 'bg-muted text-muted-foreground rounded-bl-none'
        }`}
      >
        {/* Error state */}
        {message.error && (
          <div className="mb-2 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-semibold">Error</p>
              <p>{message.error}</p>
            </div>
          </div>
        )}

        {/* Main content */}
        <p className="text-sm md:text-base break-words">{message.content}</p>

        {/* SQL query (if available, assistant only) */}
        {!isUser && message.sql && (
          <details className="mt-2 text-xs">
            <summary className="cursor-pointer font-semibold">SQL generado</summary>
            <pre className="mt-1 bg-background/50 p-2 rounded overflow-auto max-h-40 text-foreground/70">
              {message.sql}
            </pre>
          </details>
        )}

        {/* Metadata */}
        <p className="text-xs mt-1 opacity-70">
          {new Date(message.timestamp).toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}

