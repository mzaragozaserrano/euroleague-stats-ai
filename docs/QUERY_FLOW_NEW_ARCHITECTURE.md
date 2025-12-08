# Flujo de Consultas - Nueva Arquitectura

## Resumen

Con la nueva arquitectura, el flujo de consultas cambia significativamente:

**ANTES:**
```
Usuario → Backend (Text-to-SQL) → BD (stats) → Frontend (visualización)
```

**AHORA:**
```
Usuario → Frontend (caché check) → API Euroleague → Frontend (visualización)
         ↓ (solo para obtener códigos)
         Backend (Text-to-SQL) → BD (códigos)
```

## Tipos de Consultas

### 1. Consultas de Estadísticas Directas

**Ejemplos:**
- "Top 10 anotadores de esta temporada"
- "Mejores reboteadores del Real Madrid"
- "5 jugadores con más asistencias"

**Flujo:**
1. Frontend detecta que es una consulta de stats
2. Verifica caché local (`PlayerStatsCache.getSeasonStats('E2025')`)
3. Si no existe en caché:
   - Llama a `EuroleagueApi.getPlayerStats('E2025')`
   - API Euroleague retorna stats reales
   - Se guardan en caché
4. Frontend filtra/ordena datos según la consulta
5. Renderiza visualización (BarChart, LineChart, Table)

**Implementación Frontend:**

```typescript
// En ChatContainer.tsx o nuevo componente QueryHandler.tsx
async function handleStatsQuery(query: string) {
  // 1. Detectar tipo de consulta
  const queryType = detectQueryType(query); // "top_scorers", "rebounds", etc.
  
  // 2. Extraer parámetros
  const params = extractParams(query); // { seasonCode: "E2025", stat: "points", topN: 10 }
  
  // 3. Obtener datos (caché → API)
  const stats = await EuroleagueApi.getTopPlayers(
    params.seasonCode,
    params.stat,
    params.topN,
    params.teamCode
  );
  
  // 4. Renderizar
  return {
    data: stats,
    visualization: "bar",
    sql: null, // No hay SQL en este flujo
  };
}
```

### 2. Consultas de Búsqueda de Jugadores

**Ejemplos:**
- "Puntos de Larkin"
- "Estadísticas de Shane Larkin"
- "Comparar Larkin vs Micic"

**Flujo:**
1. Frontend necesita identificar al jugador
2. **Opción A (Recomendada):** Buscar directamente en caché
   ```typescript
   const stats = await EuroleagueApi.getPlayerStats('E2025');
   const larkin = stats.find(p => p.playerName.includes('Larkin'));
   ```
3. **Opción B:** Llamar al backend para obtener `player_code`
   ```typescript
   const response = await sendChatMessage("Código de Larkin", []);
   // Backend retorna: { player_code: "006590", name: "Shane Larkin" }
   const stats = await EuroleagueApi.searchPlayer('E2025', 'Larkin');
   ```
4. Renderizar stats del jugador

**Implementación Backend (si se usa Opción B):**

```python
# En text_to_sql.py
def _is_player_lookup_query(query: str) -> bool:
    """Detecta si la consulta busca información de un jugador específico."""
    keywords = ["puntos de", "estadísticas de", "stats de", "información de"]
    return any(keyword in query.lower() for keyword in keywords)

async def generate_sql(self, query: str, schema_context: str, history: List):
    if self._is_player_lookup_query(query):
        # Extraer nombre del jugador
        player_name = extract_player_name(query)  # "Larkin"
        
        # Generar SQL para obtener player_code
        sql = f"""
        SELECT player_code, name, position, team_id
        FROM players
        WHERE name ILIKE '%{player_name}%'
        LIMIT 5
        """
        
        return sql, "table", None, None
```

### 3. Consultas de Equipos

**Ejemplos:**
- "Jugadores del Real Madrid"
- "Roster del Barcelona"

**Flujo:**
1. Frontend llama al backend para obtener `team_code`
2. Backend genera SQL:
   ```sql
   SELECT code FROM teams WHERE name ILIKE '%Real Madrid%'
   ```
3. Backend retorna: `{ code: "RM" }`
4. Frontend llama a API Euroleague con filtro:
   ```typescript
   const stats = await EuroleagueApi.getTopPlayers('E2025', 'points', 20, 'RM');
   ```
5. Renderiza roster completo

## Detección de Tipo de Consulta

### Frontend: Query Classifier

```typescript
// frontend/lib/queryClassifier.ts

export type QueryType = 
  | "top_players"      // Top N jugadores por estadística
  | "player_lookup"    // Buscar jugador específico
  | "team_roster"      // Roster de un equipo
  | "comparison"       // Comparar jugadores
  | "general";         // Consulta general (usar backend)

export function classifyQuery(query: string): QueryType {
  const lowerQuery = query.toLowerCase();
  
  // Top players
  if (/top|mejor|máximo|anotador|reboteador|asistente/.test(lowerQuery)) {
    return "top_players";
  }
  
  // Player lookup
  if (/puntos de|stats de|estadísticas de|información de/.test(lowerQuery)) {
    return "player_lookup";
  }
  
  // Team roster
  if (/jugadores del|roster|plantilla/.test(lowerQuery)) {
    return "team_roster";
  }
  
  // Comparison
  if (/comparar|vs|versus|contra/.test(lowerQuery)) {
    return "comparison";
  }
  
  return "general";
}

export function extractParams(query: string, type: QueryType): QueryParams {
  // Extraer parámetros según el tipo de consulta
  // Ejemplo: "Top 10 anotadores 2025" → { topN: 10, stat: "points", seasonCode: "E2025" }
  
  const params: QueryParams = {
    seasonCode: "E2025", // Default
    stat: "points",
    topN: 10,
  };
  
  // Extraer número (top N)
  const numberMatch = query.match(/\d+/);
  if (numberMatch) {
    params.topN = parseInt(numberMatch[0]);
  }
  
  // Extraer estadística
  if (/rebot/i.test(query)) params.stat = "rebounds";
  if (/asist/i.test(query)) params.stat = "assists";
  if (/triple/i.test(query)) params.stat = "threePointsMade";
  
  // Extraer temporada
  if (/2024/i.test(query)) params.seasonCode = "E2024";
  if (/2025/i.test(query)) params.seasonCode = "E2025";
  
  return params;
}
```

## Integración en ChatStore

```typescript
// frontend/stores/chatStore.ts

sendMessage: async (userQuery: string) => {
  // ... código existente ...
  
  try {
    // 1. Clasificar consulta
    const queryType = classifyQuery(userQuery);
    
    // 2. Manejar según tipo
    let response: ChatResponse;
    
    if (queryType === "top_players") {
      // Manejar en frontend
      const params = extractParams(userQuery, queryType);
      const stats = await EuroleagueApi.getTopPlayers(
        params.seasonCode,
        params.stat,
        params.topN,
        params.teamCode
      );
      
      response = {
        data: stats,
        visualization: "bar",
        sql: null,
        error: null,
      };
    } else if (queryType === "player_lookup") {
      // Buscar en caché
      const playerName = extractPlayerName(userQuery);
      const player = await EuroleagueApi.searchPlayer("E2025", playerName);
      
      if (!player) {
        throw new Error(`No se encontró el jugador: ${playerName}`);
      }
      
      response = {
        data: [player],
        visualization: "table",
        sql: null,
        error: null,
      };
    } else {
      // Consulta general → usar backend
      response = await sendChatMessage(userQuery, backendHistory);
    }
    
    // 3. Agregar respuesta al historial
    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.error || '',
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
    }));
  } catch (error) {
    // ... manejo de errores ...
  }
},
```

## Ventajas de este Flujo

1. **Menor Latencia:** Datos en caché local (0 ms)
2. **Menos Carga en Backend:** Solo se usa para obtener códigos
3. **Offline-First:** Funciona sin conexión si hay caché
4. **Escalabilidad:** No saturamos la BD con queries de stats
5. **Simplicidad:** Frontend maneja lógica de filtrado/ordenamiento

## Desventajas y Mitigaciones

1. **Lógica Duplicada:** Filtrado en frontend y backend
   - Mitigación: Centralizar lógica en `queryClassifier.ts`

2. **Caché Puede Estar Desactualizado:**
   - Mitigación: Invalidación automática a las 7 AM

3. **Sin Historial de Conversación para Stats:**
   - Mitigación: Mantener contexto en `chatStore` para queries complejas

## Próximos Pasos

1. ✅ Implementar `queryClassifier.ts`
2. ✅ Integrar en `chatStore.sendMessage()`
3. ⏳ Actualizar `text_to_sql.py` para retornar solo códigos
4. ⏳ Testing end-to-end con queries reales
5. ⏳ Documentar ejemplos de queries soportadas

## Ejemplos de Queries Soportadas

### Frontend (sin backend)
- "Top 10 anotadores"
- "Mejores reboteadores del Real Madrid"
- "5 jugadores con más asistencias de esta temporada"
- "Puntos de Larkin"
- "Comparar Larkin vs Micic"

### Backend (con SQL)
- "¿Cuántos equipos hay?"
- "Lista de todos los equipos"
- "Jugadores del Real Madrid" (obtener códigos)
- "¿Qué posición juega Larkin?" (obtener metadatos)

### Híbrido (frontend + backend)
- "Puntos de los jugadores del Real Madrid esta temporada"
  1. Backend: Obtener `team_code` de "Real Madrid" → "RM"
  2. Frontend: `EuroleagueApi.getTopPlayers('E2025', 'points', 20, 'RM')`

