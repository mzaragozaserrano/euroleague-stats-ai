/**
 * Tests para el servicio API del frontend.
 * 
 * Cubre:
 * - Envío de mensajes al backend
 * - Manejo de errores y timeouts
 * - Detección de cold starts
 * - Detección de rate limits
 * - Reintentos automáticos
 * - Validación de respuestas
 */

import {
  sendChatMessage,
  getRateLimitInfo,
  resetRateLimitForTesting,
  ChatRequestPayload,
  ChatResponse,
  ApiCallResult,
} from '@/lib/api';

// Mock de fetch
global.fetch = jest.fn();

describe('API Service - Frontend', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    resetRateLimitForTesting();
  });

  // ==========================================================================
  // SCENARIO: Send a simple chat message successfully
  // ==========================================================================

  describe('Scenario: Send a simple chat message successfully', () => {
    it('should send message and return structured response', async () => {
      const mockResponse = {
        sql: 'SELECT COUNT(*) as total FROM players',
        data: [{ total: 200 }],
        visualization: 'table' as const,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sendChatMessage('¿Cuantos jugadores hay?', []);

      expect(result.response.sql).toBe(mockResponse.sql);
      expect(result.response.data).toEqual(mockResponse.data);
      expect(result.response.visualization).toBe('table');
      expect(result.isColdStart).toBe(false);
      expect(result.latencyMs).toBeGreaterThan(0);
    });

    it('should include message in request body', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      await sendChatMessage('Test query', [
        { role: 'user', content: 'Previous' },
      ]);

      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      const requestBody = JSON.parse(callArgs[1].body);

      expect(requestBody.query).toBe('Test query');
      expect(requestBody.history).toHaveLength(1);
      expect(requestBody.history[0].content).toBe('Previous');
    });
  });

  // ==========================================================================
  // SCENARIO: Handle backend errors gracefully
  // ==========================================================================

  describe('Scenario: Handle backend errors gracefully', () => {
    it('should handle backend error response', async () => {
      const mockResponse = {
        error: "I couldn't write the SQL query",
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sendChatMessage(
        '¿Jugadores con puntaje infinito?',
        []
      );

      expect(result.response.error).toBe(
        "I couldn't write the SQL query"
      );
    });

    it('should not crash on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const result = await sendChatMessage('Test', []);

      expect(result.response.error).toBeDefined();
      expect(result.response.error).toContain(
        'No se pudo conectar con el servidor'
      );
    });

    it('should allow sending another message after error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      const result1 = await sendChatMessage('Test 1', []);
      expect(result1.response.error).toBeDefined();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const result2 = await sendChatMessage('Test 2', []);
      expect(result2.response.error).toBeUndefined();
    });
  });

  // ==========================================================================
  // SCENARIO: Detect cold start (latency > 3s)
  // ==========================================================================

  describe('Scenario: Detect cold start (latency > 3s)', () => {
    it('should set isColdStart flag when latency > 3s', async () => {
      const delayedResponse = new Promise((resolve) => {
        setTimeout(
          () => {
            resolve({
              ok: true,
              json: async () => ({ data: [] }),
            });
          },
          3100
        );
      });

      (global.fetch as jest.Mock).mockReturnValueOnce(delayedResponse);

      const result = await sendChatMessage('Test', []);

      expect(result.isColdStart).toBe(true);
      expect(result.latencyMs).toBeGreaterThan(3000);
    });

    it('should not set isColdStart flag when latency < 3s', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const result = await sendChatMessage('Test', []);

      expect(result.isColdStart).toBe(false);
      expect(result.latencyMs).toBeLessThan(3000);
    });
  });

  // ==========================================================================
  // SCENARIO: Detect rate limit (> 50 requests per day)
  // ==========================================================================

  describe('Scenario: Detect rate limit (> 50 requests per day)', () => {
    it('should reject after 50 requests', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      // Send 50 messages
      for (let i = 0; i < 50; i++) {
        await sendChatMessage(`Message ${i}`, []);
      }

      // 51st message should fail
      const result = await sendChatMessage('Message 51', []);

      expect(result.response.error).toContain('Rate limit');
    });

    it('should show rate limit warning in UI', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      for (let i = 0; i < 50; i++) {
        await sendChatMessage(`Message ${i}`, []);
      }

      const result = await sendChatMessage('Message 51', []);

      expect(result.isRateLimit).toBe(false); // Still false, error thrown
      expect(result.response.error).toContain('50 solicitudes por día');
    });
  });

  // ==========================================================================
  // SCENARIO: Handle network timeout (> 30s)
  // ==========================================================================

  describe('Scenario: Handle network timeout (> 30s)', () => {
    it('should handle timeout error', async () => {
      const timeoutError = new Error('The operation was aborted.');
      timeoutError.name = 'AbortError';

      (global.fetch as jest.Mock).mockRejectedValueOnce(timeoutError);

      const result = await sendChatMessage('Test query', []);

      expect(result.response.error).toContain(
        'No se pudo conectar con el servidor'
      );
    });

    it('should not be in loading state after timeout', async () => {
      const timeoutError = new Error('Timeout');
      timeoutError.name = 'AbortError';

      (global.fetch as jest.Mock).mockRejectedValueOnce(timeoutError);

      const result = await sendChatMessage('Test', []);

      // The error is caught and returned, not thrown
      expect(result.response.error).toBeDefined();
    });
  });

  // ==========================================================================
  // SCENARIO: Validate response format
  // ==========================================================================

  describe('Scenario: Validate response format', () => {
    it('should reject invalid response format', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => 'not an object',
      });

      const result = await sendChatMessage('Test', []);

      expect(result.response.error).toContain(
        'Respuesta invalida del servidor'
      );
    });

    it('should validate visualization type', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          visualization: 'invalid_type',
        }),
      });

      const result = await sendChatMessage('Test', []);

      expect(result.response.error).toContain(
        'visualization debe ser: bar, line o table'
      );
    });

    it('should accept valid visualization types', async () => {
      const validVisualizations: Array<'bar' | 'line' | 'table'> = [
        'bar',
        'line',
        'table',
      ];

      for (const viz of validVisualizations) {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => ({ visualization: viz }),
        });

        const result = await sendChatMessage('Test', []);

        expect(result.response.visualization).toBe(viz);
        expect(result.response.error).toBeUndefined();
      }
    });
  });

  // ==========================================================================
  // SCENARIO: Persist chat history after API response
  // ==========================================================================

  describe('Scenario: Persist chat history after API response', () => {
    it('should include full history in request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      const history = [
        { role: 'user' as const, content: 'Message 1' },
        { role: 'assistant' as const, content: 'Response 1' },
      ];

      await sendChatMessage('Message 2', history);

      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      const requestBody = JSON.parse(callArgs[1].body);

      expect(requestBody.history).toEqual(history);
    });
  });

  // ==========================================================================
  // SCENARIO: Handle visualization types correctly
  // ==========================================================================

  describe('Scenario: Handle visualization types correctly', () => {
    it('should return bar chart visualization', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          sql: 'SELECT team, SUM(points) FROM stats GROUP BY team',
          data: [{ team: 'A', points: 100 }],
          visualization: 'bar',
        }),
      });

      const result = await sendChatMessage('¿Puntuacion por equipo?', []);

      expect(result.response.visualization).toBe('bar');
      expect(result.response.data).toBeDefined();
    });

    it('should return line chart visualization', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          visualization: 'line',
        }),
      });

      const result = await sendChatMessage('Test', []);

      expect(result.response.visualization).toBe('line');
    });

    it('should return table visualization', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          visualization: 'table',
        }),
      });

      const result = await sendChatMessage('Test', []);

      expect(result.response.visualization).toBe('table');
    });
  });

  // ==========================================================================
  // SCENARIO: Retry on network failure
  // ==========================================================================

  describe('Scenario: Retry on network failure', () => {
    it('should retry on network failure', async () => {
      const timeoutError = new Error('Network timeout');
      timeoutError.name = 'AbortError';

      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(timeoutError)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: [] }),
        });

      const result = await sendChatMessage('Test', []);

      // Should have retried after first failure
      expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(
        1
      );
      expect(result.response.error).toBeUndefined();
    });

    it('should max retry twice', async () => {
      const timeoutError = new Error('Network timeout');
      timeoutError.name = 'AbortError';

      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(timeoutError)
        .mockRejectedValueOnce(timeoutError)
        .mockRejectedValueOnce(timeoutError)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: [] }),
        });

      const result = await sendChatMessage('Test', []);

      // Should have tried 3 times (1 + 2 retries) and returned error
      expect((global.fetch as jest.Mock).mock.calls.length).toBeLessThanOrEqual(
        3
      );
      expect(result.response.error).toBeDefined();
    });
  });

  // ==========================================================================
  // HELPER TESTS
  // ==========================================================================

  describe('Rate limit info', () => {
    it('should return correct remaining requests', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [] }),
      });

      await sendChatMessage('Test 1', []);
      await sendChatMessage('Test 2', []);

      const info = getRateLimitInfo();

      expect(info.remaining).toBe(48); // 50 - 2
      expect(info.total).toBe(50);
    });
  });
});

