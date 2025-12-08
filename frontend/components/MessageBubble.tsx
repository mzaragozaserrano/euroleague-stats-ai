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
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-slide-up`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg ${
          isUser 
            ? 'px-4 py-3 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-none shadow-lg hover:shadow-xl transition-shadow' 
            : 'px-4 py-3 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none shadow-sm'
        }`}
      >
        {/* User message (simple bubble) */}
        {isUser ? (
          <>
            <p className="text-sm md:text-base break-words font-light">{message.content}</p>
            <p className="text-xs mt-2 opacity-75 font-light">
              {new Date(message.timestamp).toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </>
        ) : (
          <div className="space-y-3">
            {message.error && (
              <div className="mb-3 flex items-start gap-2 p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-800/30">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
                <div className="text-sm">
                  <p className="font-semibold text-red-700 dark:text-red-300">Error</p>
                  <p className="text-red-600 dark:text-red-400 font-light mt-0.5">{message.error}</p>
                </div>
              </div>
            )}

            <p className="text-sm md:text-base break-words font-light leading-relaxed">{message.content}</p>

            {message.data !== undefined && message.visualization && (
              <div className="mt-4 w-full max-w-2xl">
                <DataVisualizer
                  data={message.data}
                  visualization={message.visualization as 'bar' | 'line' | 'table'}
                />
              </div>
            )}

            {message.sql && (
              <details className="mt-3 text-xs group">
                <summary className="cursor-pointer font-semibold text-blue-600 dark:text-blue-400 hover:underline transition-colors">
                  SQL generado
                </summary>
                <pre className="mt-2 bg-slate-900 dark:bg-slate-950 p-3 rounded-lg overflow-auto max-h-40 text-slate-300 text-xs font-mono border border-slate-700 dark:border-slate-800">
                  {message.sql}
                </pre>
              </details>
            )}

            <p className="text-xs opacity-60 font-light">
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

