# Frontend Storage Architecture

## Resumen Ejecutivo

El frontend **NO contiene base de datos embebida**. Es una aplicación **stateless** que solo persiste el historial de chats en `localStorage`.

## Qué se Persiste

### ✅ Persiste en localStorage (`chat-storage`)

```typescript
{
  // Persistidos automáticamente por Zustand
  messages: ChatMessage[];      // Todos los mensajes del chat actual
  history: ChatMessage[];       // Historial completo de la conversación
  sessions: ChatSession[];      // Múltiples sesiones de chat
  currentSessionId: string;     // Sesión activa
  lastCleared: number;          // Timestamp de última limpieza
  totalQueriesCount: number;    // Contador total de queries enviadas
  
  // NO se persisten (transient state)
  isLoading: boolean;           // Se reinicia al cargar
  error: string | null;         // Se limpia al cargar
  coldStartWarning: boolean;    // No persiste
  rateLimitWarning: boolean;    // No persiste
}
```

### ❌ NO se Persiste

- Datos de jugadores, equipos, o estadísticas (queries de BD)
- Estado de UI transitorio (warnings, loading flags)
- Cualquier información de usuario (sin autenticación implementada)

## Qué NO se Persiste (A propósito)

| Elemento | Razón |
|----------|-------|
| Advertencias (cold start, rate limit) | Se deben mostrar solo en sesión actual, no al recargar |
| Estado de carga | Se reinicia con cada sesión |
| Errores transitorios | Son contexto de una sesión, no histórico |

## Arquitectura de Datos

```
┌─────────────────────────────────────────┐
│     Backend (Neon PostgreSQL)           │
│  - teams                                │
│  - players                              │
│  - player_season_stats                  │
│  - player_stats_games                   │
│  - schema_embeddings                    │
└─────────────────────────────────────────┘
         ↑ (Consultas via API)
         │
┌─────────────────────────────────────────┐
│     Frontend (Next.js + React)          │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │  localStorage (`chat-storage`)  │  │
│  │  - Chat history only            │  │
│  │  - Persistencia automática       │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Flujo de Datos

### 1. Usuario envía pregunta

```
User Input
  ↓
ChatStore.sendMessage()
  ↓
POST /api/chat (historial incluido)
  ↓
Backend procesa (RAG + LLM + SQL)
  ↓
Respuesta JSON {sql, data, visualization, error?}
  ↓
ChatStore actualiza messages + history
  ↓
Zustand persiste automáticamente a localStorage
```

### 2. Usuario recarga la página

```
React monta
  ↓
Zustand carga `chat-storage` de localStorage
  ↓
ChatStore se restaura con:
  - Mensajes anteriores ✅
  - Historial ✅
  - Sessions ✅
  - Advertencias❌ (se limpian, transient)
  ↓
UI renderiza con historial restaurado
```

### 3. Usuario limpia historial

```
User clickea "Limpiar"
  ↓
clearHistory(confirmClear: true)
  ↓
messages = []
history = []
sessions = []
currentSessionId = null
lastCleared = Date.now()
  ↓
Zustand persiste estado vacío
```

## Configuración Técnica

### localStorage Key

```typescript
name: 'chat-storage'
```

### Versionado

```typescript
version: 3  // Actual

// Migración automática de versiones antiguas
migrate: (persistedState, version) => {
  // v0 → v3: Convierte historial antiguo en primera sesión
  // v1 → v3: Idem
  // v2 → v3: Agrega soporte de sesiones
  // v3 → v3: Sin cambios
}
```

### Límites

- **localStorage limit**: ~5-10 MB (navegador dependiente)
- **Recomendación**: Limpiar historial si excede límite
- **Almacenamiento típico**: ~10 KB por 50 mensajes

## Debugging

### Ver contenido del storage

```javascript
// En Chrome DevTools Console
JSON.parse(localStorage.getItem('chat-storage'))
```

### Limpiar storage manualmente

```javascript
localStorage.removeItem('chat-storage')
// Luego recargar la página
```

### Habilitar logs

```javascript
localStorage.setItem('DEBUG_API', 'true')
// El servicio mostrará logs en consola
```

## Comparación: Frontend Stateless vs Con BD Embebida

| Aspecto | Implementado (Stateless) | Con BD Embebida |
|---------|------------------------|-----------------|
| **Sincronización** | Siempre con backend | Riesgo de inconsistencia |
| **Storage** | localStorage 5-10MB | IndexedDB 50MB+ |
| **Latencia** | Desde backend (3-5s) | Consultas locales (ms) |
| **Complejidad** | Baja ✅ | Alta ❌ |
| **Cache desincronizado** | No ✅ | Posible ❌ |
| **Offline support** | No (sin Service Worker) | Posible |
| **Tamaño bundle** | ~50KB | +200KB (SQLite/dexie) |

## Beneficios Arquitectura Actual

1. ✅ **Simplicidad**: No hay que mantener sincronización
2. ✅ **Consistencia**: Siempre datos frescos del backend
3. ✅ **Escalabilidad**: Backend manejable por múltiples clientes
4. ✅ **Seguridad**: Datos sensibles no en cliente
5. ✅ **Mantenibilidad**: Menos lógica duplicada

## Próximos Pasos (Fuera de Scope)

Si se requiere offline support o cache más robusto:

1. Implementar Service Workers para caché HTTP
2. Agregar `stale-while-revalidate` strategy
3. Considerar IndexedDB solo si offline es crítico
4. Mantener localStorage para chat history

---

**Última actualización**: Diciembre 8, 2025  
**Estado**: Completado - Sin base de datos embebida en frontend ✅

