import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  sendChatMessage,
  ChatResponse,
  getRateLimitInfo,
} from '@/lib/api';
import { PlayerStatsCache } from '@/lib/playerStatsCache';
import { EuroleagueApi } from '@/lib/euroleagueApi';
import {
  classifyQuery,
  extractParams,
  extractPlayerName,
  extractPlayerNamesForComparison,
} from '@/lib/queryClassifier';

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
  lastCleared?: number; // Timestamp de última limpieza
  totalQueriesCount?: number; // Contador de queries totales

  // Acciones
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  clearHistory: (confirmClear?: boolean) => boolean; // Retorna true si se limpió
  setColdStartWarning: (show: boolean) => void;
  setRateLimitWarning: (show: boolean) => void;
  getMessageCount: () => number;
  getHistoryMetadata: () => { messageCount: number; lastMessageTime: number | null };
  dismissWarnings: () => void; // Cerrar ambas advertencias
  
  // Nueva acción para enviar mensaje al backend
  sendMessage: (userQuery: string) => Promise<void>;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => {
      // Verificar invalidación de caché al inicializar
      if (typeof window !== 'undefined') {
        const wasInvalidated = PlayerStatsCache.checkAndInvalidate();
        if (wasInvalidated) {
          console.log('[ChatStore] Caché de stats invalidado (después de 7 AM)');
        }
      }

      return {
        // Estado inicial
        messages: [],
        history: [],
        isLoading: false,
        error: null,
        coldStartWarning: false,
        rateLimitWarning: false,
        lastCleared: undefined,
        totalQueriesCount: 0,

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
       * Envía un mensaje al backend y maneja la respuesta.
       * 
       * Flujo:
       * 1. Agregar mensaje del usuario al historial
       * 2. Clasificar tipo de consulta
       * 3. Si es de stats → manejar en frontend (caché + API)
       * 4. Si es general → llamar al backend
       * 5. Agregar respuesta del asistente al historial
       * 6. Incrementar contador de queries
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
          totalQueriesCount: (state.totalQueriesCount || 0) + 1,
        }));

        try {
          // 2. Clasificar consulta
          const queryType = classifyQuery(userQuery.trim());
          console.log(`[ChatStore] Tipo de consulta detectado: ${queryType}`);
          
          let response: any;
          let isColdStart = false;
          let isRateLimit = false;

          // 3. Manejar según tipo
          if (queryType === "top_players") {
            console.log('[ChatStore] Manejando consulta de top players en frontend');
            
            const params = extractParams(userQuery.trim());
            const startTime = Date.now();
            
            try {
              const stats = await EuroleagueApi.getTopPlayers(
                params.seasonCode,
                params.stat,
                params.topN,
                params.teamCode
              );
              
              const latencyMs = Date.now() - startTime;
              if (latencyMs > 3000) {
                isColdStart = true;
              }
              
              response = {
                data: stats,
                visualization: "bar",
                sql: null,
                error: null,
              };
            } catch (error) {
              throw error;
            }
          } else if (queryType === "player_lookup") {
            console.log('[ChatStore] Manejando consulta de búsqueda de jugador en frontend');
            
            const playerName = extractPlayerName(userQuery.trim());
            const startTime = Date.now();
            
            if (!playerName) {
              throw new Error('No se pudo extraer el nombre del jugador');
            }
            
            try {
              const player = await EuroleagueApi.searchPlayer("E2025", playerName);
              
              const latencyMs = Date.now() - startTime;
              if (latencyMs > 3000) {
                isColdStart = true;
              }
              
              if (!player) {
                throw new Error(`No se encontró el jugador: ${playerName}`);
              }
              
              response = {
                data: [player],
                visualization: "table",
                sql: null,
                error: null,
              };
            } catch (error) {
              throw error;
            }
          } else if (queryType === "comparison") {
            console.log('[ChatStore] Manejando consulta de comparación en frontend');
            
            const players = extractPlayerNamesForComparison(userQuery.trim());
            const startTime = Date.now();
            
            if (!players) {
              throw new Error('No se pudieron extraer los nombres de los jugadores para comparación');
            }
            
            try {
              const [player1, player2] = await EuroleagueApi.comparePlayers(
                "E2025",
                players[0],
                players[1]
              );
              
              const latencyMs = Date.now() - startTime;
              if (latencyMs > 3000) {
                isColdStart = true;
              }
              
              const comparisonData = [];
              if (player1) comparisonData.push(player1);
              if (player2) comparisonData.push(player2);
              
              if (comparisonData.length === 0) {
                throw new Error(`No se encontraron los jugadores: ${players.join(' vs ')}`);
              }
              
              response = {
                data: comparisonData,
                visualization: "bar",
                sql: null,
                error: null,
              };
            } catch (error) {
              throw error;
            }
          } else {
            // Consulta general → usar backend
            console.log('[ChatStore] Manejando consulta general en backend');
            
            const backendHistory = state.history.map((msg) => ({
              role: msg.role,
              content: msg.content,
            }));

            const result = await sendChatMessage(
              userQuery.trim(),
              backendHistory
            );

            response = result.response;
            isColdStart = result.isColdStart;
            isRateLimit = result.isRateLimit;
          }

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
              tipo: queryType,
              tieneData: !!response.data,
              tieneError: !!response.error,
              visualization: response.visualization,
            }
          );

          // 4. Agregar respuesta del asistente
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.error
              ? response.error
              : '', // Sin mensaje genérico - los datos hablan por sí solos
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

          console.error('[ChatStore] Error procesando mensaje:', error);

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
      };
    },
    {
      name: 'chat-storage', // localStorage key
      version: 2, // Incrementado para mejor versionado
      // Seleccionar qué estado persistir
      partialize: (state) => ({
        history: state.history,
        messages: state.messages,
        lastCleared: state.lastCleared,
        totalQueriesCount: state.totalQueriesCount,
      }),
      // Migración de versiones antiguas (v1 -> v2)
      migrate: (persistedState: any, version: number) => {
        if (version === 0 || version === 1) {
          // v1 solo tiene history y messages, los otros campos se inicializan a defaults
          return {
            ...persistedState,
            isLoading: false,
            error: null,
            coldStartWarning: false,
            rateLimitWarning: false,
            lastCleared: undefined,
            totalQueriesCount: persistedState.totalQueriesCount || 0,
          };
        }
        return persistedState;
      },
    }
  )
);

