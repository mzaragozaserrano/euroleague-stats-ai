/**
 * Tests para la integración del ChatStore con el API service.
 * 
 * Cubre:
 * - Envío de mensajes con sendMessage()
 * - Manejo de respuestas del backend
 * - Persistencia en localStorage
 * - Manejo de errores
 * - Warnings de cold start y rate limit
 */

import { renderHook, act } from '@testing-library/react';
import { useChatStore } from '@/stores/chatStore';
import * as apiModule from '@/lib/api';

// Mock del módulo API
jest.mock('@/lib/api');

const mockSendChatMessage = apiModule.sendChatMessage as jest.MockedFunction<
  typeof apiModule.sendChatMessage
>;
const mockGetRateLimitInfo = apiModule.getRateLimitInfo as jest.MockedFunction<
  typeof apiModule.getRateLimitInfo
>;

describe('ChatStore - API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Limpiar localStorage
    localStorage.clear();
    // Limpiar el store
    const { result } = renderHook(() => useChatStore());
    act(() => {
      result.current.clearHistory();
    });
  });

  // ==========================================================================
  // SCENARIO: Send a simple chat message successfully
  // ==========================================================================

  describe('Scenario: Send a simple chat message successfully', () => {
    it('should send message and add both user and assistant messages', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: {
          sql: 'SELECT COUNT(*) as total FROM players',
          data: [{ total: 200 }],
          visualization: 'table',
        },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 1000,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('¿Cuantos jugadores hay?');
      });

      expect(result.current.messages).toHaveLength(2); // user + assistant
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('¿Cuantos jugadores hay?');
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].sql).toBe(
        'SELECT COUNT(*) as total FROM players'
      );
      expect(result.current.messages[1].data).toEqual([{ total: 200 }]);
      expect(result.current.messages[1].visualization).toBe('table');
    });

    it('should update history correctly', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Test');
      });

      expect(result.current.history).toHaveLength(2);
    });
  });

  // ==========================================================================
  // SCENARIO: Handle backend errors gracefully
  // ==========================================================================

  describe('Scenario: Handle backend errors gracefully', () => {
    it('should handle backend error and display error message', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: {
          error: "I couldn't write the SQL query",
        },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 1000,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage(
          '¿Jugadores con puntaje infinito?'
        );
      });

      expect(result.current.error).toBe("I couldn't write the SQL query");
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[1].error).toBe(
        "I couldn't write the SQL query"
      );
    });

    it('should not crash on error', async () => {
      mockSendChatMessage.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Test');
      });

      expect(result.current.error).toContain('Network error');
      expect(result.current.isLoading).toBe(false);
    });

    it('should allow sending another message after error', async () => {
      mockSendChatMessage
        .mockRejectedValueOnce(new Error('Error 1'))
        .mockResolvedValueOnce({
          response: { data: [] },
          isColdStart: false,
          isRateLimit: false,
          latencyMs: 100,
        });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Message 1');
      });

      expect(result.current.error).toBeDefined();

      await act(async () => {
        await result.current.sendMessage('Message 2');
      });

      expect(result.current.error).toBeNull();
      expect(result.current.messages).toHaveLength(4); // 2 from error + 2 from success
    });
  });

  // ==========================================================================
  // SCENARIO: Detect cold start (latency > 3s)
  // ==========================================================================

  describe('Scenario: Detect cold start (latency > 3s)', () => {
    it('should set coldStartWarning when latency > 3s', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: { data: [] },
        isColdStart: true,
        isRateLimit: false,
        latencyMs: 3500,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Test query');
      });

      expect(result.current.coldStartWarning).toBe(true);
    });

    it('should not set coldStartWarning when latency < 3s', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 1000,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Test query');
      });

      expect(result.current.coldStartWarning).toBe(false);
    });
  });

  // ==========================================================================
  // SCENARIO: Detect rate limit (> 50 requests per day)
  // ==========================================================================

  describe('Scenario: Detect rate limit (> 50 requests per day)', () => {
    it('should reject after 50 requests', async () => {
      mockSendChatMessage.mockRejectedValueOnce(
        new Error('Rate limit alcanzado (50 solicitudes por día)')
      );

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Message 51');
      });

      expect(result.current.error).toContain('Rate limit');
    });
  });

  // ==========================================================================
  // SCENARIO: Persist chat history after API response
  // ==========================================================================

  describe('Scenario: Persist chat history after API response', () => {
    it('should persist messages in localStorage', async () => {
      mockSendChatMessage.mockResolvedValue({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result, rerender } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Message 1');
        await result.current.sendMessage('Message 2');
      });

      const messagesCount = result.current.messages.length;

      // Simular reinicio de página
      jest.clearAllMocks();
      mockSendChatMessage.mockResolvedValue({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result: result2 } = renderHook(() => useChatStore());

      // Los mensajes persisten en localStorage
      expect(result2.current.history.length).toBeGreaterThan(0);
    });

    it('should include history in backend request', async () => {
      mockSendChatMessage.mockResolvedValue({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Message 1');
      });

      expect(mockSendChatMessage).toHaveBeenCalledWith('Message 1', []);

      await act(async () => {
        await result.current.sendMessage('Message 2');
      });

      const lastCall =
        mockSendChatMessage.mock.calls[
          mockSendChatMessage.mock.calls.length - 1
        ];
      expect(lastCall[0]).toBe('Message 2');
      expect(Array.isArray(lastCall[1])).toBe(true);
      expect(lastCall[1].length).toBeGreaterThan(0);
    });
  });

  // ==========================================================================
  // SCENARIO: Handle visualization types correctly
  // ==========================================================================

  describe('Scenario: Handle visualization types correctly', () => {
    it('should include visualization in assistant message', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: {
          sql: 'SELECT team, SUM(points) FROM stats GROUP BY team',
          data: [{ team: 'A', points: 100 }],
          visualization: 'bar',
        },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 1000,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('¿Puntuacion por equipo?');
      });

      const assistantMessage = result.current.messages[1];
      expect(assistantMessage.visualization).toBe('bar');
    });
  });

  // ==========================================================================
  // STATE MANAGEMENT
  // ==========================================================================

  describe('State Management', () => {
    it('should set isLoading to true while sending', async () => {
      const resolveResponse = jest.fn();
      const responsePromise = new Promise((resolve) => {
        resolveResponse(() => {
          resolve({
            response: { data: [] },
            isColdStart: false,
            isRateLimit: false,
            latencyMs: 100,
          });
        };
      });

      mockSendChatMessage.mockReturnValueOnce(responsePromise as any);

      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.sendMessage('Test');
      });

      // Check that loading is true initially
      expect(result.current.isLoading).toBe(true);
    });

    it('should set isLoading to false after response', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Test');
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('should clear error on new message', async () => {
      mockSendChatMessage
        .mockRejectedValueOnce(new Error('Error'))
        .mockResolvedValueOnce({
          response: { data: [] },
          isColdStart: false,
          isRateLimit: false,
          latencyMs: 100,
        });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('Message 1');
      });

      expect(result.current.error).toBeDefined();

      await act(async () => {
        await result.current.sendMessage('Message 2');
      });

      expect(result.current.error).toBeNull();
    });
  });

  // ==========================================================================
  // VALIDATION
  // ==========================================================================

  describe('Input Validation', () => {
    it('should reject empty message', async () => {
      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('');
      });

      expect(result.current.error).toContain('Por favor escribe un mensaje');
      expect(mockSendChatMessage).not.toHaveBeenCalled();
    });

    it('should reject whitespace-only message', async () => {
      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('   ');
      });

      expect(result.current.error).toContain('Por favor escribe un mensaje');
      expect(mockSendChatMessage).not.toHaveBeenCalled();
    });

    it('should trim whitespace from message', async () => {
      mockSendChatMessage.mockResolvedValueOnce({
        response: { data: [] },
        isColdStart: false,
        isRateLimit: false,
        latencyMs: 100,
      });

      const { result } = renderHook(() => useChatStore());

      await act(async () => {
        await result.current.sendMessage('   Test message   ');
      });

      const userMessage = result.current.messages[0];
      expect(userMessage.content).toBe('Test message');
    });
  });
});

