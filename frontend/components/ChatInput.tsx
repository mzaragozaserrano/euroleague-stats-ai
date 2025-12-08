'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useChatStore } from '@/stores/chatStore';

export interface ChatInputProps {
  onSubmit?: (message: string) => Promise<void>;
  disabled?: boolean;
  debounceMs?: number; // Tiempo de debounce en ms (default 300)
}

export function ChatInput({ onSubmit, disabled = false, debounceMs = 300 }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout>();
  const isLoading = useChatStore((state) => state.isLoading);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  // Debounced submit handler
  const handleSubmitDebounced = useCallback(async (message: string) => {
    if (!message.trim() || isLoading || disabled || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      if (onSubmit) {
        await onSubmit(message);
      }
    } catch (error) {
      console.error('Error submitting message:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [onSubmit, isLoading, disabled, isSubmitting]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading || disabled || isSubmitting) {
      return;
    }

    const message = input.trim();
    
    // Limpiar textarea inmediatamente para UX fluido
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Usar debounce para el envío real
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(
      () => handleSubmitDebounced(message),
      debounceMs
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, but allow Shift+Enter for new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-3 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Haz una pregunta sobre estadísticas de Euroliga..."
            disabled={isLoading || disabled || isSubmitting}
            rows={1}
            className="w-full resize-none rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-3 text-base text-slate-900 dark:text-slate-100 ring-offset-background placeholder:text-slate-500 dark:placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm min-h-12 max-h-[120px] font-light shadow-sm hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
          />
        </div>
        <Button
          type="submit"
          disabled={!input.trim() || isLoading || disabled || isSubmitting}
          size="default"
          className="mb-0 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 dark:from-blue-500 dark:to-blue-600 dark:hover:from-blue-600 dark:hover:to-blue-700 text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-blue-500/30 dark:hover:shadow-blue-500/20 transition-all duration-200 disabled:shadow-none disabled:opacity-60 rounded-xl px-6 py-2.5 min-h-12"
        >
          {isLoading || isSubmitting ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Enviando</span>
            </div>
          ) : (
            'Enviar'
          )}
        </Button>
      </div>
    </form>
  );
}

