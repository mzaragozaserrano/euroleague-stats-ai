import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  sql?: string;
  data?: unknown;
  visualization?: 'bar' | 'line' | 'table';
  error?: string;
}

export interface ChatStore {
  // Estado
  messages: ChatMessage[];
  history: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  coldStartWarning: boolean;
  rateLimitWarning: boolean;

  // Acciones
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  clearHistory: () => void;
  setColdStartWarning: (show: boolean) => void;
  setRateLimitWarning: (show: boolean) => void;
  getMessageCount: () => number;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Estado inicial
      messages: [],
      history: [],
      isLoading: false,
      error: null,
      coldStartWarning: false,
      rateLimitWarning: false,

      // Acciones
      addMessage: (message: ChatMessage) =>
        set((state) => ({
          messages: [...state.messages, message],
          history: [...state.history, message],
          error: null,
        })),

      setLoading: (loading: boolean) =>
        set({
          isLoading: loading,
          error: null,
        }),

      setError: (error: string | null) =>
        set({
          error,
          isLoading: false,
        }),

      clearError: () =>
        set({
          error: null,
        }),

      clearHistory: () =>
        set({
          messages: [],
          history: [],
          error: null,
          isLoading: false,
        }),

      setColdStartWarning: (show: boolean) =>
        set({
          coldStartWarning: show,
        }),

      setRateLimitWarning: (show: boolean) =>
        set({
          rateLimitWarning: show,
        }),

      getMessageCount: () => get().messages.length,
    }),
    {
      name: 'chat-storage', // localStorage key
      version: 1,
      // Seleccionar qué estado persistir
      partialize: (state) => ({
        history: state.history,
        messages: state.messages,
      }),
    }
  )
);

