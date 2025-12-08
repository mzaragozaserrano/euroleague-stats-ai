/**
 * API Service para comunicación con el backend.
 * 
 * Maneja:
 * - Conexión con endpoint /api/chat
 * - Reintentos automáticos
 * - Timeouts
 * - Detección de cold starts (>3s)
 * - Detección de rate limits (50 req/día)
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequestPayload {
  query: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  sql?: string;
  data?: unknown;
  visualization?: 'bar' | 'line' | 'table';
  error?: string;
}

export interface ApiCallResult {
  response: ChatResponse;
  isColdStart: boolean;
  isRateLimit: boolean;
  latencyMs: number;
}

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const ENDPOINT = `${API_BASE_URL}/api/chat`;

const TIMEOUT_MS = 30000; // 30 segundos
const COLD_START_THRESHOLD_MS = 3000; // 3 segundos
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

// Rate limit tracking
let requestCount = 0;
let requestCountResetTime = Date.now();
const RATE_LIMIT_WINDOW_MS = 24 * 60 * 60 * 1000; // 24 horas
const RATE_LIMIT_MAX = 50; // 50 req/día

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Reinicia el contador de rate limit si han pasado 24 horas.
 */
function checkAndResetRateLimit(): void {
  const now = Date.now();
  if (now - requestCountResetTime > RATE_LIMIT_WINDOW_MS) {
    requestCount = 0;
    requestCountResetTime = now;
  }
}

/**
 * Verifica si estamos en rate limit.
 */
function isRateLimited(): boolean {
  checkAndResetRateLimit();
  return requestCount >= RATE_LIMIT_MAX;
}

/**
 * Incrementa el contador de rate limit.
 */
function incrementRequestCount(): void {
  requestCount++;
}

/**
 * Valida la respuesta del backend.
 */
function validateResponse(data: unknown): ChatResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('Respuesta invalida del servidor');
  }

  const response = data as Record<string, unknown>;

  // La respuesta debe ser un objeto con propiedades opcionales
  const validated: ChatResponse = {};

  if (response.sql !== undefined) {
    if (typeof response.sql !== 'string') {
      throw new Error('Campo sql debe ser string');
    }
    validated.sql = response.sql;
  }

  if (response.data !== undefined) {
    validated.data = response.data;
  }

  if (response.visualization !== undefined) {
    if (
      typeof response.visualization !== 'string' ||
      !['bar', 'line', 'table'].includes(response.visualization)
    ) {
      throw new Error(
        'visualization debe ser: bar, line o table'
      );
    }
    validated.visualization = response.visualization as
      | 'bar'
      | 'line'
      | 'table';
  }

  if (response.error !== undefined) {
    if (typeof response.error !== 'string') {
      throw new Error('Campo error debe ser string');
    }
    validated.error = response.error;
  }

  return validated;
}

/**
 * Realiza una llamada a la API con reintentos.
 */
async function fetchWithRetry(
  payload: ChatRequestPayload,
  attempt: number = 0
): Promise<Response> {
  try {
    const controller = new AbortController();
    const timeoutHandle = setTimeout(
      () => controller.abort(),
      TIMEOUT_MS
    );

    const response = await fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutHandle);
    return response;
  } catch (error) {
    // Si es timeout o error de red, reintentar
    if (
      error instanceof Error &&
      (error.name === 'AbortError' ||
        error.message.includes('fetch')) &&
      attempt < MAX_RETRIES
    ) {
      console.warn(
        `Intento ${attempt + 1} fallido, reintentando en ${RETRY_DELAY_MS}ms...`
      );
      await new Promise((resolve) =>
        setTimeout(resolve, RETRY_DELAY_MS)
      );
      return fetchWithRetry(payload, attempt + 1);
    }
    throw error;
  }
}

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * Envía un mensaje de chat al backend y retorna la respuesta.
 * 
 * @param query - Consulta natural del usuario
 * @param history - Historial de conversación (pares role/content)
 * @returns Resultado de la llamada API con latencia y flags de warning
 * @throws Error si la solicitud falla completamente
 */
export async function sendChatMessage(
  query: string,
  history: ChatMessage[] = []
): Promise<ApiCallResult> {
  // Validar input
  if (!query || typeof query !== 'string') {
    throw new Error('Query debe ser un string no vacío');
  }

  // Verificar rate limit
  const isRateLimit = isRateLimited();
  if (isRateLimit) {
    throw new Error(
      'Rate limit alcanzado (50 solicitudes por día). Intente mañana.'
    );
  }

  const payload: ChatRequestPayload = {
    query: query.trim(),
    history: history || [],
  };

  const startTime = Date.now();

  try {
    // Incrementar contador
    incrementRequestCount();

    // Realizar llamada
    const response = await fetchWithRetry(payload);

    // El backend siempre retorna 200, incluso con errores
    if (!response.ok) {
      throw new Error(
        `Error HTTP ${response.status}: ${response.statusText}`
      );
    }

    // Parsear respuesta
    const jsonData = await response.json();
    const chatResponse = validateResponse(jsonData);

    const latencyMs = Date.now() - startTime;
    const isColdStart = latencyMs > COLD_START_THRESHOLD_MS;

    console.log(
      `[API] Response en ${latencyMs}ms${
        isColdStart ? ' (COLD START)' : ''
      }`
    );

    return {
      response: chatResponse,
      isColdStart,
      isRateLimit: false,
      latencyMs,
    };
  } catch (error) {
    const latencyMs = Date.now() - startTime;
    const errorMessage =
      error instanceof Error
        ? error.message
        : 'Error desconocido';

    console.error(
      `[API] Error en ${latencyMs}ms: ${errorMessage}`
    );

    // Retornar como error en la respuesta
    return {
      response: {
        error: `No se pudo conectar con el servidor: ${errorMessage}. Verifica que el backend esté corriendo en ${API_BASE_URL}`,
      },
      isColdStart: false,
      isRateLimit: false,
      latencyMs,
    };
  }
}

/**
 * Obtiene información sobre el límite de rate limit.
 */
export function getRateLimitInfo(): {
  remaining: number;
  total: number;
  resetTime: number;
} {
  checkAndResetRateLimit();
  const remaining = Math.max(0, RATE_LIMIT_MAX - requestCount);
  const resetTime = requestCountResetTime + RATE_LIMIT_WINDOW_MS;

  return {
    remaining,
    total: RATE_LIMIT_MAX,
    resetTime,
  };
}

/**
 * Reinicia el contador de rate limit (útil para testing).
 */
export function resetRateLimitForTesting(): void {
  requestCount = 0;
  requestCountResetTime = Date.now();
}

