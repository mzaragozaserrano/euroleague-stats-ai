'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '@/stores/chatStore';
import { Card } from '@/components/ui/card';
import { DataVisualizer } from '@/components/DataVisualizer';
import { AlertCircle } from 'lucide-react';

export interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Formatea el timestamp mostrando fecha si es de otro día, solo hora si es del día actual.
 */
function formatTimestamp(timestamp: number): string {
  const messageDate = new Date(timestamp);
  const today = new Date();
  
  // Comparar solo año, mes y día (ignorar hora)
  const isToday = 
    messageDate.getFullYear() === today.getFullYear() &&
    messageDate.getMonth() === today.getMonth() &&
    messageDate.getDate() === today.getDate();
  
  if (isToday) {
    // Solo mostrar hora si es hoy
    return messageDate.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } else {
    // Mostrar fecha y hora si es de otro día
    return messageDate.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [showSQL, setShowSQL] = React.useState(false);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-8 animate-slide-up`}>
      <div
        className={`max-w-[95%] ${
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
              {formatTimestamp(message.timestamp)}
            </p>
          </>
        ) : (
          <div className="space-y-3">
            {message.error && (
              <div className="mb-3 flex items-start gap-2 p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-800/30">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
                <div className="text-sm">
                  <p className="font-semibold text-red-700 dark:text-red-300">Error en la consulta</p>
                  <p className="text-red-600 dark:text-red-400 font-light mt-0.5 whitespace-pre-line">{message.error}</p>
                </div>
              </div>
            )}

            {/* Solo mostrar contenido de texto si existe y no hay error */}
            {message.content && !message.error && (
              <div className="text-sm md:text-base break-words font-light leading-relaxed prose dark:prose-invert max-w-none [&>ul]:list-disc [&>ul]:pl-5 [&>ol]:list-decimal [&>ol]:pl-5 [&>p]:mb-2 last:[&>p]:mb-0">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({node, ...props}) => (
                      <div className="my-4 w-full overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                        <table className="w-full border-collapse text-sm" {...props} />
                      </div>
                    ),
                    thead: ({node, ...props}) => (
                      <thead className="bg-slate-100 dark:bg-slate-900/50 text-slate-700 dark:text-slate-300" {...props} />
                    ),
                    tbody: ({node, ...props}) => (
                      <tbody className="bg-white/50 dark:bg-slate-900/20" {...props} />
                    ),
                    tr: ({node, ...props}) => (
                      <tr className="border-b border-slate-200 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors" {...props} />
                    ),
                    th: ({node, ...props}) => (
                      <th className="px-4 py-3 text-left font-semibold" {...props} />
                    ),
                    td: ({node, ...props}) => (
                      <td className="px-4 py-3 align-top" {...props} />
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}

            {/* Visualización de datos */}
            {message.data !== undefined && message.visualization && (
              <div className="mt-4 w-full max-w-2xl">
                <DataVisualizer
                  data={message.data}
                  visualization={message.visualization as 'bar' | 'line' | 'table'}
                />
              </div>
            )}

            {/* SQL expandible - oculto por defecto */}
            {message.sql && (
              <div className="mt-3 pt-3 border-t border-slate-300 dark:border-slate-700">
                <button
                  onClick={() => setShowSQL(!showSQL)}
                  className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors flex items-center gap-1.5 group"
                >
                  <span className={`transform transition-transform duration-200 ${showSQL ? 'rotate-90' : ''}`}>
                    ▶
                  </span>
                  {showSQL ? 'Ocultar' : 'Mostrar'} SQL generado
                </button>
                
                {showSQL && (
                  <pre className="mt-3 bg-slate-900 dark:bg-slate-950 p-3 rounded-lg overflow-auto max-h-48 text-slate-300 text-xs font-mono border border-slate-700 dark:border-slate-800 animate-slide-up">
                    {message.sql}
                  </pre>
                )}
              </div>
            )}

            <p className="text-xs opacity-60 font-light">
              {formatTimestamp(message.timestamp)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

