'use client';

import { ChatMessage } from '@/stores/chatStore';
import { Card } from '@/components/ui/card';
import { DataVisualizer } from '@/components/DataVisualizer';
import { AlertCircle } from 'lucide-react';

export interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg ${
          isUser ? 'px-4 py-2 rounded-lg bg-primary text-primary-foreground rounded-br-none' : ''
        }`}
      >
        {/* User message (simple bubble) */}
        {isUser ? (
          <>
            <p className="text-sm md:text-base break-words">{message.content}</p>
            <p className="text-xs mt-1 opacity-70">
              {new Date(message.timestamp).toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </>
        ) : (
          /* Assistant message (with visualization and metadata) */
          <div className="space-y-3">
            {/* Error state */}
            {message.error && (
              <div className="mb-2 flex items-start gap-2 p-3 bg-destructive/10 rounded-lg border border-destructive/20">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-destructive" />
                <div className="text-sm">
                  <p className="font-semibold text-destructive">Error</p>
                  <p className="text-destructive/80">{message.error}</p>
                </div>
              </div>
            )}

            {/* Main content */}
            <p className="text-sm md:text-base break-words">{message.content}</p>

            {/* Data Visualization */}
            {message.data && message.visualization && (
              <div className="mt-4 w-full max-w-2xl">
                <DataVisualizer
                  data={message.data}
                  visualization={message.visualization as 'bar' | 'line' | 'table'}
                />
              </div>
            )}

            {/* SQL query (collapsible) */}
            {message.sql && (
              <details className="mt-2 text-xs">
                <summary className="cursor-pointer font-semibold hover:underline">
                  SQL generado
                </summary>
                <pre className="mt-1 bg-background/50 p-2 rounded overflow-auto max-h-40 text-foreground/70">
                  {message.sql}
                </pre>
              </details>
            )}

            {/* Timestamp */}
            <p className="text-xs opacity-70">
              {new Date(message.timestamp).toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

