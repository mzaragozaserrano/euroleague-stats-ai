# Mejoras de Persistencia y UX - Issue #45

## Resumen

Implementación completa de persistencia robusta y mejoras significativas de UX en el frontend para garantizar una experiencia de usuario fluida y sin fricción.

## Cambios Implementados

### 1. Mejoras en Zustand Store (`frontend/stores/chatStore.ts`)

#### Nuevos Campos de Estado
- `lastCleared`: Timestamp de la última limpieza de historial
- `totalQueriesCount`: Contador acumulativo de queries totales

#### Nuevas Acciones
- **`clearHistory(confirmClear: boolean): boolean`** - Limpia historial con validación
  - Retorna `true` si se limpió exitosamente
  - Retorna `false` si no hay mensajes o no fue confirmado
  - Registra timestamp en `lastCleared`

- **`dismissWarnings(): void`** - Cierra ambas advertencias (cold start + rate limit)
  - Útil para mejorar UX permitiendo cerrar advertencias

- **`getHistoryMetadata(): { messageCount, lastMessageTime }`** - Retorna metadata
  - Para debugging y análisis de uso

#### Persistencia Mejorada
- **Version 2** con migración automática desde v1
- Nuevos campos persistidos: `lastCleared`, `totalQueriesCount`
- Función de migración (`migrate`) que preserva datos antiguos
- localStorage key: `chat-storage`

### 2. ChatContainer Mejorado (`frontend/components/ChatContainer.tsx`)

#### Nuevas Características
- **Botón "Limpiar Historial"**
  - Solo visible cuando hay mensajes (`messages.length > 0`)
  - Muestra confirmación antes de ejecutar
  - Animación fade-in/out suave con `animate-in`
  - Estados: normal → confirmación → cancelable

- **Advertencias Mejoradas**
  - Botón de cierre (×) en cada advertencia
  - Cold Start: "Despertando al agente... (primera consulta puede tardar 3+ segundos)"
  - Rate Limit: "Se alcanzó límite de consultas (50/día). Vuelve mañana para más preguntas"
  - Uso de `dismissWarnings()` para cerrar ambas a la vez

- **Layout Responsivo**
  - Header con flexbox que se adapta a móvil
  - Botón "Limpiar" colapsable en móvil (solo icono)
  - Texto visible en desktop

### 3. ChatInput con Debounce (`frontend/components/ChatInput.tsx`)

#### Optimización de Rendimiento
- **Debounce de 300ms** (configurable via prop `debounceMs`)
- Previene múltiples envíos rápidos accidentales
- UX fluida: textarea se limpia inmediatamente, envío se retrasa
- Timer cleanup automático en desmontaje del componente

#### Mejoras de Estado
- `isSubmitting`: Flag adicional para bloquear doble envío
- Verificación robusta de condiciones (input trim, loading, disabled)
- Mensaje dinámico en botón: "Enviando..." ↔ "Enviar"

#### Autoexpansión de Textarea
- Expande automáticamente con el contenido del usuario
- Max-height: 120px para evitar textarea gigante
- Auto-resize al escribir o borrar

### 4. BDD Tests (`backend/tests/features/persistence_ux.feature` + step definitions)

Incluye **12 escenarios** cubriendo:

1. ✅ Persistencia de historial a través de recargas
2. ✅ Funcionalidad de limpiar historial con confirmación
3. ✅ Botón oculto cuando no hay mensajes
4. ✅ Cold start warning (>3s) con capacidad de cerrar
5. ✅ Rate limit warning que bloquea envío
6. ✅ Cierre de rate limit warning
7. ✅ Debounce previene múltiples envíos
8. ✅ Auto-resize de textarea hasta 120px
9. ✅ Contador de queries en metadata
10. ✅ Migración de persistencia v1 → v2
11. ✅ Timestamp de última limpieza (`lastCleared`)
12. ✅ Las advertencias no se persisten (transient state)

## Arquitectura de Persistencia

```
┌─────────────────────────────────────────────┐
│          localStorage (Browser)             │
│  chat-storage {                             │
│    version: 2                               │
│    state: {                                 │
│      messages: [],      // PERSISTIDO       │
│      history: [],       // PERSISTIDO       │
│      lastCleared: ts,   // PERSISTIDO       │
│      totalQueriesCount: n // PERSISTIDO     │
│    }                                        │
│  }                                          │
└─────────────────────────────────────────────┘
                    ↓
        Migration Handler (v1 → v2)
                    ↓
┌─────────────────────────────────────────────┐
│       Zustand Store (Runtime)               │
│  {                                          │
│    // Persistido al storage                 │
│    messages, history, lastCleared,          │
│    totalQueriesCount,                       │
│                                             │
│    // NO PERSISTIDO (transient)             │
│    isLoading, error,                        │
│    coldStartWarning, rateLimitWarning       │
│  }                                          │
└─────────────────────────────────────────────┘
```

### Flujo de Persistencia
1. User abre app → Zustand carga `chat-storage` de localStorage
2. User envía mensaje → Store actualiza persistencia automáticamente
3. Advertencias (cold start, rate limit) → NO persisten (reset al refrescar)
4. User limpia historial → `lastCleared` se registra, historial vacío
5. Page reload → Nuevo historial cargado desde localStorage v2

## Flow Mejorado de UX

### Envío de Mensaje
```
User Input
   ↓
Debounce (300ms) ← Evita múltiples envíos
   ↓
Validación input
   ↓
Agregar mensaje user al store
   ↓
API call con reintentos + cold start detection
   ↓
Set coldStartWarning si latencia > 3s
   ↓
Recibir respuesta
   ↓
Agregar mensaje assistant al store
   ↓
localStorage persiste automáticamente
```

### Limpiar Historial
```
Click "Limpiar" button
   ↓
Show confirmation (Confirmar / Cancelar)
   ↓
User click Confirmar
   ↓
clearHistory(true)
   ↓
messages = []
history = []
lastCleared = timestamp
   ↓
localStorage updated
```

## Indicadores Visuales

### Cold Start Warning (Yellow Banner)
- Icono: Clock ⏱️
- Texto: "Despertando al agente... (primera consulta puede tardar 3+ segundos)"
- Botón cierre: × (llama `dismissWarnings()`)
- Trigger: `latencyMs > 3000` en primer envío

### Rate Limit Warning (Yellow Banner)
- Icono: AlertCircle ⚠️
- Texto: "Se alcanzó límite de consultas (50/día). Vuelve mañana..."
- Botón cierre: ×
- Efecto: Deshabilita input + button
- Trigger: `isRateLimit: true` en respuesta API

### Clear History Button
- Ubicación: Header derecha
- Icono: Trash2 🗑️
- Texto en desktop: "Limpiar", hidden en móvil
- Estados:
  - Normal: visible si `messages.length > 0`
  - Confirmación: muestra "Confirmar" + "Cancelar"
  - Oculto: si no hay mensajes

## Testing

### Ejecutar Tests BDD
```bash
cd backend
pytest tests/features/persistence_ux.feature -v --tb=short
```

### Escenarios Cubiertos
- Persistencia a través de recargas ✅
- Limpieza de historial ✅
- Botón oculto/visible ✅
- Cold start indicators ✅
- Rate limit handling ✅
- Debounce functionality ✅
- Textarea resize ✅
- Query counting ✅
- Version migration ✅
- Transient state management ✅

## Performance Optimizations

1. **Debounce (300ms)**: Reduce API calls, mejora responsividad UI
2. **Lazy State Updates**: Solo campos necesarios se actualizan
3. **Memoized Selectors**: Zustand selectors evitan re-renders innecesarios
4. **localStorage versionado**: Fácil migración futura (v3, v4, etc.)
5. **Transient State**: Warnings no se persisten = localStorage más limpio

## Compatibilidad

- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Mobile browsers (iOS Safari, Chrome Android)
- ✅ Tab persistence (localStorage sobrevive tab discarding)
- ✅ Dark mode compatible
- ✅ RTL ready (estructura HTML flexible)

## Cambios de Archivos

```
frontend/stores/chatStore.ts
  - Interface ChatStore ampliada
  - Nuevas acciones: clearHistory, dismissWarnings, getHistoryMetadata
  - Persistencia v2 con migración

frontend/components/ChatContainer.tsx
  - Botón Clear History con confirmación
  - Mejores advertencias con botón cierre
  - Layout responsivo mejorado

frontend/components/ChatInput.tsx
  - Debounce 300ms implementado
  - isSubmitting flag
  - Autoexpansión textarea mejorada

backend/tests/features/persistence_ux.feature
  - 12 escenarios BDD completos

backend/tests/step_defs/test_persistence_ux_steps.py
  - Step definitions implementadas con mocks/fixtures
```

## Notas de Implementación

### localStorage Key
- `chat-storage` - Persiste messages, history, lastCleared, totalQueriesCount

### Debounce Default
- 300ms - Configurable via prop `debounceMs` en ChatInput

### Max Textarea Height
- 120px - Evita que textarea ocupe pantalla completa

### Rate Limit Threshold
- 50 queries/day - Detectado desde API response (`isRateLimit` flag)

### Cold Start Threshold
- 3 segundos - Configurable en API (recomendación: 3000ms)

## Próximos Pasos

1. Implementar estadísticas de uso (total queries, top queries, etc.)
2. Agregar export de chat history (JSON/CSV)
3. Soporte para múltiples chat sessions (tabs)
4. Analytics: cold starts, rate limits, error rates
5. Offline support con Service Workers

