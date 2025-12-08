# Frontend - API Integration Service

Este documento describe el servicio API del frontend para comunicación con el backend.

## Descripción General

El servicio `frontend/lib/api.ts` proporciona una forma segura y robusta de comunicarse con el endpoint `/api/chat` del backend. Incluye:

- **Reintentos automáticos** (máximo 2 reintentos en caso de timeout)
- **Manejo de timeouts** (30 segundos)
- **Detección de cold starts** (latencia > 3s)
- **Manejo de rate limits** (50 solicitudes por día)
- **Validación de respuestas** (format JSON estructurado)
- **Integración con Zustand** para persistencia en localStorage

## Uso Básico

### Enviar un mensaje

```typescript
import { sendChatMessage } from '@/lib/api';

const result = await sendChatMessage(
  '¿Cuantos jugadores hay?',
  [] // historial previo
);

if (result.response.error) {
  console.error(result.response.error);
} else {
  console.log('SQL:', result.response.sql);
  console.log('Datos:', result.response.data);
  console.log('Visualización:', result.response.visualization);
  console.log('Cold Start:', result.isColdStart);
}
```

### Usar el ChatStore (Recomendado)

```typescript
import { useChatStore } from '@/stores/chatStore';

export function MyComponent() {
  const sendMessage = useChatStore((state) => state.sendMessage);
  const isLoading = useChatStore((state) => state.isLoading);

  const handleSend = async (query: string) => {
    await sendMessage(query);
  };

  return <button onClick={() => handleSend('Mi pregunta')}>Enviar</button>;
}
```

## Configuración

### Variables de Entorno

```bash
# .env.local (crear este archivo en el frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Para Producción

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.euroleague-stats.com
```

## Características

### 1. Reintentos Automáticos

En caso de timeout de red, el servicio reintentar automáticamente hasta 2 veces:

```typescript
// Ejemplo: primer intento falla, segundo intento éxito
const result = await sendChatMessage('¿Jugadores?', []);
// Si el primer intento tira timeout, reintentar después de 1s
```

### 2. Detección de Cold Starts

Si la latencia es mayor a 3 segundos, se establece la bandera `isColdStart`:

```typescript
if (result.isColdStart) {
  console.log('Backend está iniciando, latencia: ' + result.latencyMs + 'ms');
}
```

El componente `ChatContainer` mostrará un mensaje "Despertando al agente...".

### 3. Rate Limiting

Se permite máximo 50 solicitudes por día. Después de eso:

```typescript
const result = await sendChatMessage('Query', []);
// Si excede límite: result.response.error = "Rate limit alcanzado..."
```

Para obtener información sobre el límite:

```typescript
import { getRateLimitInfo } from '@/lib/api';

const info = getRateLimitInfo();
console.log(`Solicitudes restantes: ${info.remaining}/${info.total}`);
```

### 4. Formato de Respuesta

El backend siempre retorna status 200, con errores en el campo `error`:

```typescript
interface ChatResponse {
  sql?: string;                    // SQL generado
  data?: unknown;                  // Resultados de la BD
  visualization?: 'bar' | 'line' | 'table';
  error?: string;                  // Error si aplica
}
```

### 5. Historial de Conversación

El historial se mantiene en el store y se envía al backend:

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const history: ChatMessage[] = [
  { role: 'user', content: 'Primer pregunta' },
  { role: 'assistant', content: 'Primera respuesta' }
];

const result = await sendChatMessage('Segunda pregunta', history);
```

## Manejo de Errores

### Error de Conexión

Si el backend no está disponible:

```typescript
const result = await sendChatMessage('Query', []);
if (result.response.error?.includes('No se pudo conectar')) {
  console.error('Backend no disponible');
}
```

### Error del LLM

Si OpenRouter no puede generar SQL válido:

```typescript
if (result.response.error?.includes("couldn't write")) {
  console.error('LLM no pudo generar SQL');
}
```

### Error de BD

Si la consulta SQL genera error:

```typescript
if (result.response.error?.includes('Error ejecutando')) {
  console.error('Error en la BD');
}
```

## Integración con UI

### ChatContainer

El componente `ChatContainer` integra automáticamente el API service:

```typescript
<ChatContainer />
// Automáticamente:
// - Detecta cold starts
// - Detecta rate limits
// - Muestra warnings
// - Integra con ChatStore
```

### Componentes Personalizados

Para crear un componente custom:

```typescript
'use client';

import { useState } from 'react';
import { sendChatMessage } from '@/lib/api';

export function CustomChat() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSend = async () => {
    setLoading(true);
    const result = await sendChatMessage(message, []);
    
    if (result.response.error) {
      console.error(result.response.error);
    } else {
      console.log('SQL:', result.response.sql);
    }
    
    setLoading(false);
  };

  return (
    <div>
      <input value={message} onChange={(e) => setMessage(e.target.value)} />
      <button onClick={handleSend} disabled={loading}>
        {loading ? 'Enviando...' : 'Enviar'}
      </button>
    </div>
  );
}
```

## Testing

### Tests Unitarios

Ubicación: `frontend/__tests__/lib/api.test.ts`

```bash
npm test -- api.test.ts
```

### Tests del Store

Ubicación: `frontend/__tests__/stores/chatStore.test.ts`

```bash
npm test -- chatStore.test.ts
```

### Tests BDD

Ubicación: `backend/tests/features/chat_api_integration.feature`

```bash
cd backend
pytest --co -m bdd
```

## Performance

- **Timeout**: 30 segundos
- **Cold Start Threshold**: 3 segundos
- **Max Retries**: 2
- **Retry Delay**: 1 segundo
- **Rate Limit**: 50 req/día (se reinicia cada 24h)

## Debugging

Habilitar logs en la consola del navegador:

```javascript
// En Chrome DevTools Console
localStorage.setItem('DEBUG_API', 'true');

// El servicio mostrará:
// [API] Response en Xms
// [API] Error en Xms: mensaje
// [ChatStore] Respuesta recibida
// [ChatStore] Error enviando mensaje
```

## Estructura del Proyecto

```
frontend/
├── lib/
│   └── api.ts                    # Servicio API principal
├── stores/
│   └── chatStore.ts              # Store Zustand integrado
├── components/
│   ├── ChatContainer.tsx         # Componente principal
│   ├── ChatInput.tsx             # Input textarea
│   ├── MessageList.tsx           # Lista de mensajes
│   └── MessageBubble.tsx         # Burbuja individual
├── __tests__/
│   ├── lib/
│   │   └── api.test.ts           # Tests del servicio
│   └── stores/
│       └── chatStore.test.ts     # Tests del store
└── .env.example                  # Template de variables
```

## Próximos Pasos

1. **Deployment**: Configurar URLs del backend para staging/production
2. **Caché**: Implementar caché de queries frecuentes
3. **Optimización**: Implementar debouncing en ChatInput
4. **Analytics**: Registrar eventos de consultas exitosas/fallidas
5. **Testing**: Agregar e2e tests con Cypress/Playwright

