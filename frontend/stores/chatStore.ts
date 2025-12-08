import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  sendChatMessage,
  ChatResponse,
  getRateLimitInfo,
} from '@/lib/api';

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
  
  // Nueva acción para enviar mensaje al backend
  sendMessage: (userQuery: string) => Promise<void>;
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

      /**
       * Envía un mensaje al backend y maneja la respuesta.
       * 
       * 1. Agrega el mensaje del usuario al historial
       * 2. Llama a sendChatMessage() con el historial
       * 3. Maneja cold starts (>3s) y rate limits
       * 4. Agrega respuesta del asistente al historial
       */
      sendMessage: async (userQuery: string) => {
        const state = get();
        
        // Validar input
        if (!userQuery?.trim()) {
          set({ error: 'Por favor escribe un mensaje' });
          return;
        }

        // 1. Agregar mensaje del usuario
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          role: 'user',
          content: userQuery.trim(),
          timestamp: Date.now(),
        };
        
        set((state) => ({
          messages: [...state.messages, userMessage],
          history: [...state.history, userMessage],
          isLoading: true,
          error: null,
          coldStartWarning: false,
          rateLimitWarning: false,
        }));

        try {
          // Preparar historial para el backend (formato: {role, content})
          const backendHistory = state.history.map((msg) => ({
            role: msg.role,
            content: msg.content,
          }));

          // 2. Llamar al API
          const result = await sendChatMessage(
            userQuery.trim(),
            backendHistory
          );

          const { response, isColdStart, isRateLimit, latencyMs } = result;

          // 3. Detectar warnings
          if (isColdStart) {
            set({ coldStartWarning: true });
          }
          if (isRateLimit) {
            set({ rateLimitWarning: true });
          }

          // Log para debugging
          console.log(
            `[ChatStore] Respuesta recibida en ${latencyMs}ms`,
            response
          );

          // 4. Agregar respuesta del asistente
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.error
              ? response.error
              : 'Query ejecutada exitosamente',
            timestamp: Date.now(),
            sql: response.sql,
            data: response.data,
            visualization: response.visualization,
            error: response.error,
          };

          set((state) => ({
            messages: [...state.messages, assistantMessage],
            history: [...state.history, assistantMessage],
            isLoading: false,
            error: response.error ? response.error : null,
          }));
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : 'Error desconocido';

          console.error('[ChatStore] Error enviando mensaje:', error);

          // Agregar mensaje de error
          const errorMessage_obj: ChatMessage = {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: `Error: ${errorMessage}`,
            timestamp: Date.now(),
            error: errorMessage,
          };

          set((state) => ({
            messages: [...state.messages, errorMessage_obj],
            history: [...state.history, errorMessage_obj],
            isLoading: false,
            error: errorMessage,
          }));
        }
      },
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

