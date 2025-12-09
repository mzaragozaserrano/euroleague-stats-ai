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

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  isLoading?: boolean; // Estado de carga por sesión
}

export interface ChatStore {
  // Estado
  messages: ChatMessage[];
  history: ChatMessage[];
  isLoading: boolean; // Getter que retorna isLoading de la sesión actual
  error: string | null;
  coldStartWarning: boolean;
  rateLimitWarning: boolean;
  lastCleared?: number; // Timestamp de última limpieza
  totalQueriesCount?: number; // Contador de queries totales
  
  // Nuevo: Gestión de múltiples chats
  sessions: ChatSession[];
  currentSessionId: string | null;
  
  // Acciones
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void; // Deprecated: usar setSessionLoading
  setError: (error: string | null) => void;
  clearError: () => void;
  clearHistory: (confirmClear?: boolean) => boolean; // Retorna true si se limpió
  setColdStartWarning: (show: boolean) => void;
  setRateLimitWarning: (show: boolean) => void;
  getMessageCount: () => number;
  getHistoryMetadata: () => { messageCount: number; lastMessageTime: number | null };
  dismissWarnings: () => void; // Cerrar ambas advertencias
  
  // Nuevas acciones para múltiples chats
  createNewChat: () => void;
  loadChat: (sessionId: string) => void;
  deleteChat: (sessionId: string) => void;
  renameChat: (sessionId: string, title: string) => void;
  getSessions: () => ChatSession[];
  setSessionLoading: (sessionId: string, loading: boolean) => void;
  
  // Nueva acción para enviar mensaje al backend
  sendMessage: (userQuery: string) => Promise<void>;
}

const generateSessionId = () => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

const generateSessionTitle = (firstMessage: string) => {
  // Tomar los primeros 50 caracteres o hasta el primer salto de línea
  const title = firstMessage
    .split('\n')[0]
    .substring(0, 50)
    .trim();
  return title || 'Nueva conversación';
};

/**
 * Calcula el estado de carga basándose en la sesión actual
 */
const calculateIsLoading = (sessions: ChatSession[], currentSessionId: string | null): boolean => {
  if (!currentSessionId) return false;
  const currentSession = sessions.find((s) => s.id === currentSessionId);
  return currentSession?.isLoading || false;
};

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => {
      return {
        // Estado inicial
        messages: [],
        history: [],
        isLoading: false, // Getter calculado
        error: null,
        coldStartWarning: false,
        rateLimitWarning: false,
        lastCleared: undefined,
        totalQueriesCount: 0,
        sessions: [],
        currentSessionId: null,

      // Acciones
      addMessage: (message: ChatMessage) =>
        set((state) => ({
          messages: [...state.messages, message],
          history: [...state.history, message],
          error: null,
        })),

      setLoading: (loading: boolean) => {
        // Mantener compatibilidad: actualizar sesión actual si existe
        const state = get();
        if (state.currentSessionId) {
          set((prevState) => {
            const updatedSessions = prevState.sessions.map((s) =>
              s.id === state.currentSessionId
                ? { ...s, isLoading: loading }
                : s
            );
            return {
              sessions: updatedSessions,
              isLoading: calculateIsLoading(updatedSessions, state.currentSessionId),
            };
          });
        } else {
          set({ isLoading: loading });
        }
      },

      setError: (error: string | null) =>
        set({
          error,
          isLoading: false,
        }),

      clearError: () =>
        set({
          error: null,
        }),

      /**
       * Limpia el historial de mensajes con validación.
       * Retorna true si la limpieza fue exitosa, false si fue rechazada.
       */
      clearHistory: (confirmClear = false) => {
        if (get().messages.length === 0) {
          return false; // No hay nada que limpiar
        }

        // En producción, podría haber una confirmación adicional
        if (confirmClear) {
          set({
            messages: [],
            history: [],
            error: null,
            isLoading: false,
            coldStartWarning: false,
            rateLimitWarning: false,
            lastCleared: Date.now(),
          });
          return true;
        }

        return false;
      },

      setColdStartWarning: (show: boolean) =>
        set({
          coldStartWarning: show,
        }),

      setRateLimitWarning: (show: boolean) =>
        set({
          rateLimitWarning: show,
        }),

      /**
       * Cierra ambas advertencias de una vez.
       */
      dismissWarnings: () =>
        set({
          coldStartWarning: false,
          rateLimitWarning: false,
        }),

      getMessageCount: () => get().messages.length,

      /**
       * Retorna metadata del historial para debugging y análisis.
       */
      getHistoryMetadata: () => {
        const state = get();
        const lastMessage = state.messages[state.messages.length - 1];
        return {
          messageCount: state.messages.length,
          lastMessageTime: lastMessage?.timestamp || null,
        };
      },

      /**
       * Crea un nuevo chat
       */
      createNewChat: () => {
        const newSessionId = generateSessionId();
        set((state) => ({
          currentSessionId: newSessionId,
          messages: [],
          history: [],
          sessions: [
            ...state.sessions,
            {
              id: newSessionId,
              title: 'Nueva conversación',
              messages: [],
              createdAt: Date.now(),
              updatedAt: Date.now(),
              isLoading: false,
            },
          ],
          error: null,
          isLoading: false,
          coldStartWarning: false,
          rateLimitWarning: false,
        }));
      },

      /**
       * Carga un chat existente
       */
      loadChat: (sessionId: string) => {
        const state = get();
        const session = state.sessions.find((s) => s.id === sessionId);
        if (session) {
          // Ordenar mensajes por timestamp (ascendente: más antiguo primero)
          const sortedMessages = [...session.messages].sort(
            (a, b) => a.timestamp - b.timestamp
          );
          
          set({
            currentSessionId: sessionId,
            messages: sortedMessages, // Sincronizar con la sesión (ordenados)
            history: sortedMessages, // Sincronizar con la sesión (ordenados)
            isLoading: calculateIsLoading(state.sessions, sessionId),
            error: null,
          });
        }
      },

      /**
       * Elimina un chat
       */
      deleteChat: (sessionId: string) => {
        set((state) => {
          const filteredSessions = state.sessions.filter((s) => s.id !== sessionId);
          const isCurrentSession = state.currentSessionId === sessionId;
          
          // Si se elimina el chat actual, crear un nuevo chat automáticamente
          if (isCurrentSession) {
            const newSessionId = generateSessionId();
            return {
              sessions: [
                ...filteredSessions,
                {
                  id: newSessionId,
                  title: 'Nueva conversación',
                  messages: [],
                  createdAt: Date.now(),
                  updatedAt: Date.now(),
                  isLoading: false,
                },
              ],
              currentSessionId: newSessionId,
              messages: [],
              history: [],
            };
          }
          
          // Si se elimina otro chat, mantener el estado actual
          return {
            sessions: filteredSessions,
            currentSessionId: state.currentSessionId,
            messages: state.messages,
            history: state.history,
          };
        });
      },

      /**
       * Renombra un chat
       */
      renameChat: (sessionId: string, title: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { ...s, title, updatedAt: Date.now() }
              : s
          ),
        }));
      },

      /**
       * Obtiene todas las sesiones
       */
      getSessions: () => get().sessions,

      /**
       * Establece el estado de carga de una sesión específica
       */
      setSessionLoading: (sessionId: string, loading: boolean) => {
        set((state) => {
          const updatedSessions = state.sessions.map((s) =>
            s.id === sessionId ? { ...s, isLoading: loading } : s
          );
          
          return {
            sessions: updatedSessions,
            isLoading: calculateIsLoading(updatedSessions, state.currentSessionId),
          };
        });
      },

      /**
       * Envía un mensaje al backend y maneja la respuesta.
       * 
       * Flujo:
       * 1. Crear nuevo chat si no hay sesión actual
       * 2. Agregar mensaje del usuario al historial
       * 3. Clasificar tipo de consulta
       * 4. Llamar al backend
       * 5. Agregar respuesta del asistente al historial
       * 6. Actualizar sesión y contador de queries
       */
      sendMessage: async (userQuery: string) => {
        const state = get();
        
        // Validar input
        if (!userQuery?.trim()) {
          set({ error: 'Por favor escribe un mensaje' });
          return;
        }

        // 1. Crear nuevo chat si no hay sesión actual
        let currentSessionId = state.currentSessionId;
        let isFirstMessage = false;
        
        if (!currentSessionId) {
          const newSessionId = generateSessionId();
          currentSessionId = newSessionId;
          
          set((prevState) => ({
            currentSessionId: newSessionId,
            sessions: [
              ...prevState.sessions,
              {
                id: newSessionId,
                title: generateSessionTitle(userQuery.trim()),
                messages: [],
                createdAt: Date.now(),
                updatedAt: Date.now(),
                isLoading: false,
              },
            ],
          }));
          isFirstMessage = true;
        } else {
          // Verificar si es la primera consulta del chat existente
          const currentSession = state.sessions.find((s) => s.id === currentSessionId);
          isFirstMessage = currentSession ? currentSession.messages.length === 0 : false;
        }

        // 2. Agregar mensaje del usuario
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          role: 'user',
          content: userQuery.trim(),
          timestamp: Date.now(),
        };
        
        // 3. Si es la primera consulta y el título es el por defecto, actualizarlo
        if (isFirstMessage) {
          const currentSession = get().sessions.find((s) => s.id === currentSessionId);
          if (currentSession && currentSession.title === 'Nueva conversación') {
            const newTitle = generateSessionTitle(userQuery.trim());
            set((state) => ({
              sessions: state.sessions.map((s) =>
                s.id === currentSessionId
                  ? { ...s, title: newTitle }
                  : s
              ),
            }));
          }
        }
        
        // Capturar sessionId antes de la llamada async para asegurar que se actualice la sesión correcta
        const targetSessionId = currentSessionId;
        
        // Obtener la sesión objetivo para usar su historial
        const targetSession = get().sessions.find((s) => s.id === targetSessionId);
        if (!targetSession) {
          console.error(`[ChatStore] Sesión ${targetSessionId} no encontrada`);
          return;
        }
        
        // Preparar historial para el backend (solo de esta sesión + el nuevo userMessage)
        // Ordenar mensajes por timestamp (ascendente: más antiguo primero)
        const sortedMessages = [...targetSession.messages, userMessage].sort(
          (a, b) => a.timestamp - b.timestamp
        );
        
        const backendHistory = sortedMessages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));
        
        // Marcar la sesión como cargando y agregar userMessage a la sesión
        set((state) => {
          const updatedSessions = state.sessions.map((s) => {
            if (s.id === targetSessionId) {
              return {
                ...s,
                messages: [...s.messages, userMessage],
                isLoading: true,
              };
            }
            return s;
          });
          
          // Solo actualizar messages/history globales si es la sesión actual
          const isCurrentSession = state.currentSessionId === targetSessionId;
          
          return {
            messages: isCurrentSession ? [...state.messages, userMessage] : state.messages,
            history: isCurrentSession ? [...state.history, userMessage] : state.history,
            sessions: updatedSessions,
            isLoading: calculateIsLoading(updatedSessions, state.currentSessionId),
            error: null,
            coldStartWarning: false,
            rateLimitWarning: false,
            totalQueriesCount: (state.totalQueriesCount || 0) + 1,
          };
        });

        try {

          const result = await sendChatMessage(
            userQuery.trim(),
            backendHistory
          );

          const response = result.response;
          const isColdStart = result.isColdStart;
          const isRateLimit = result.isRateLimit;
          
          const { latencyMs } = result;

          // Detectar warnings
          if (isColdStart) {
            set({ coldStartWarning: true });
          }
          if (isRateLimit) {
            set({ rateLimitWarning: true });
          }

          console.log(
            `[ChatStore] Respuesta procesada`,
            {
              tieneData: !!response.data,
              tieneError: !!response.error,
              visualization: response.visualization,
            }
          );

          // 5. Agregar respuesta del asistente
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.error
              ? response.error
              : (response.message || ''),
            timestamp: Date.now(),
            sql: response.sql,
            data: response.data,
            visualization: response.visualization,
            error: response.error,
          };

          // 6. Actualizar sesión (usar targetSessionId capturado al inicio)
          set((state) => {
            // Buscar la sesión objetivo y actualizar sus mensajes
            const targetSession = state.sessions.find((s) => s.id === targetSessionId);
            if (!targetSession) {
              console.warn(`[ChatStore] Sesión ${targetSessionId} no encontrada al actualizar respuesta`);
              return state;
            }

            // userMessage ya está en targetSession.messages, solo agregar assistantMessage
            const updatedMessages = [...targetSession.messages, assistantMessage];
            const updatedSessions = state.sessions.map((s) =>
              s.id === targetSessionId
                ? {
                    ...s,
                    messages: updatedMessages,
                    isLoading: false,
                    updatedAt: Date.now(),
                  }
                : s
            );

            // Si es la sesión actual, actualizar también messages e history
            const isCurrentSession = state.currentSessionId === targetSessionId;

            return {
              messages: isCurrentSession ? updatedMessages : state.messages,
              history: isCurrentSession ? [...state.history, assistantMessage] : state.history,
              sessions: updatedSessions,
              isLoading: calculateIsLoading(updatedSessions, state.currentSessionId),
              error: response.error ? response.error : null,
            };
          });
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : 'Error desconocido';

          console.error('[ChatStore] Error procesando mensaje:', error);

          // Agregar mensaje de error
          const errorMessage_obj: ChatMessage = {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: `Error: ${errorMessage}`,
            timestamp: Date.now(),
            error: errorMessage,
          };

          set((state) => {
            // Buscar la sesión objetivo y actualizar sus mensajes
            const targetSession = state.sessions.find((s) => s.id === targetSessionId);
            if (!targetSession) {
              console.warn(`[ChatStore] Sesión ${targetSessionId} no encontrada al actualizar error`);
              return state;
            }

            // userMessage ya está en targetSession.messages, solo agregar errorMessage
            const updatedMessages = [...targetSession.messages, errorMessage_obj];
            const updatedSessions = state.sessions.map((s) =>
              s.id === targetSessionId
                ? {
                    ...s,
                    messages: updatedMessages,
                    isLoading: false,
                    updatedAt: Date.now(),
                  }
                : s
            );

            // Si es la sesión actual, actualizar también messages e history
            const isCurrentSession = state.currentSessionId === targetSessionId;

            return {
              messages: isCurrentSession ? updatedMessages : state.messages,
              history: isCurrentSession ? [...state.history, errorMessage_obj] : state.history,
              sessions: updatedSessions,
              isLoading: calculateIsLoading(updatedSessions, state.currentSessionId),
              error: errorMessage,
            };
          });
        }
      },
      };
    },
    {
      name: 'chat-storage', // localStorage key
      version: 5, // Incrementado para sincronización de messages/history
      // Seleccionar qué estado persistir
      // NO persistir messages/history globales - se derivan de la sesión actual
      partialize: (state) => ({
        lastCleared: state.lastCleared,
        totalQueriesCount: state.totalQueriesCount,
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
      }),
      // Migración de versiones antiguas
      migrate: (persistedState: any, version: number) => {
        if (version === 0 || version === 1) {
          // v1 → v4: Convertir history/messages en primera sesión
          const oldMessages = persistedState.history || persistedState.messages || [];
          const newSessionId = generateSessionId();
          
          return {
            ...persistedState,
            isLoading: false,
            error: null,
            coldStartWarning: false,
            rateLimitWarning: false,
            lastCleared: undefined,
            totalQueriesCount: persistedState.totalQueriesCount || 0,
            sessions: oldMessages.length > 0
              ? [{
                  id: newSessionId,
                  title: 'Conversación anterior',
                  messages: oldMessages,
                  createdAt: Date.now(),
                  updatedAt: Date.now(),
                  isLoading: false,
                }]
              : [],
            currentSessionId: oldMessages.length > 0 ? newSessionId : null,
          };
        }
        if (version === 2) {
          // v2 → v4: Agregar soporte de sesiones
          const oldMessages = persistedState.messages || [];
          const newSessionId = generateSessionId();
          
          return {
            ...persistedState,
            sessions: oldMessages.length > 0
              ? [{
                  id: newSessionId,
                  title: 'Conversación anterior',
                  messages: oldMessages,
                  createdAt: Date.now(),
                  updatedAt: Date.now(),
                  isLoading: false,
                }]
              : [],
            currentSessionId: oldMessages.length > 0 ? newSessionId : null,
          };
        }
        if (version === 3) {
          // v3 → v5: Agregar isLoading a sesiones existentes y sincronizar messages/history
          const sessions = (persistedState.sessions || []).map((s: ChatSession) => ({
            ...s,
            isLoading: s.isLoading ?? false,
          }));
          
          // Sincronizar messages/history con la sesión actual
          const currentSession = sessions.find((s) => s.id === persistedState.currentSessionId);
          
          return {
            ...persistedState,
            messages: currentSession?.messages || [],
            history: currentSession?.messages || [],
            sessions,
            isLoading: calculateIsLoading(sessions, persistedState.currentSessionId),
          };
        }
        // v4 → v5: Sincronizar messages/history con la sesión actual
        if (version === 4) {
          const sessions = persistedState.sessions || [];
          const currentSession = sessions.find((s: ChatSession) => s.id === persistedState.currentSessionId);
          
          return {
            ...persistedState,
            messages: currentSession?.messages || [],
            history: currentSession?.messages || [],
          };
        }
        return persistedState;
      },
      // Sincronizar messages/history con la sesión actual después de cargar desde localStorage
      onRehydrateStorage: () => (state) => {
        if (state) {
          const { currentSessionId, sessions } = state;
          
          // Ordenar mensajes de todas las sesiones por timestamp
          const sortedSessions = sessions.map((session) => ({
            ...session,
            messages: [...session.messages].sort((a, b) => a.timestamp - b.timestamp),
          }));
          
          if (currentSessionId) {
            const currentSession = sortedSessions.find((s) => s.id === currentSessionId);
            if (currentSession) {
              state.sessions = sortedSessions;
              state.messages = currentSession.messages;
              state.history = currentSession.messages;
              state.isLoading = calculateIsLoading(sortedSessions, currentSessionId);
            }
          } else {
            state.sessions = sortedSessions;
            state.messages = [];
            state.history = [];
            state.isLoading = false;
          }
        }
      },
    }
  )
);

