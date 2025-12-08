/**
 * Ejemplos de uso del componente DataVisualizer
 * 
 * Este archivo muestra cómo el backend integra con el frontend
 * para visualizar datos automáticamente.
 */

// ============================================================================
// EJEMPLO 1: BarChart - Top 5 Anotadores
// ============================================================================

// Backend Response
const example1Response = {
  sql: "SELECT player_name, CAST(SUM(points) as INTEGER) as total_points FROM player_stats_games GROUP BY player_name ORDER BY total_points DESC LIMIT 5",
  data: [
    { player_name: "Micic", total_points: 245 },
    { player_name: "Larkin", total_points: 238 },
    { player_name: "Teodosic", total_points: 225 },
    { player_name: "De Colo", total_points: 210 },
    { player_name: "Osman", total_points: 198 }
  ],
  visualization: "bar"
};

// Frontend Render
/*
<MessageBubble
  message={{
    id: 'msg-1',
    role: 'assistant',
    content: 'Aquí están los 5 máximos anotadores de la temporada:',
    timestamp: Date.now(),
    data: example1Response.data,
    visualization: example1Response.visualization as 'bar',
    sql: example1Response.sql
  }}
/>
*/

// ============================================================================
// EJEMPLO 2: LineChart - Evolución de Puntos en Temporada
// ============================================================================

const example2Response = {
  sql: "SELECT round, AVG(points) as avg_points FROM player_stats_games WHERE player_id = 123 GROUP BY round ORDER BY round",
  data: [
    { round: 1, avg_points: 18.5 },
    { round: 2, avg_points: 21.3 },
    { round: 3, avg_points: 19.8 },
    { round: 4, avg_points: 23.1 },
    { round: 5, avg_points: 20.7 },
    { round: 6, avg_points: 24.2 }
  ],
  visualization: "line"
};

// ============================================================================
// EJEMPLO 3: DataTable - Estadísticas Completas de Jugador
// ============================================================================

const example3Response = {
  sql: "SELECT player_name, team_id, CAST(AVG(points) as NUMERIC(5,2)) as avg_points, CAST(AVG(rebounds_total) as NUMERIC(5,2)) as avg_rebounds, CAST(AVG(assists) as NUMERIC(5,2)) as avg_assists, CAST(AVG(fg3_made) as NUMERIC(5,2)) as avg_3pm FROM player_stats_games GROUP BY player_name, team_id ORDER BY avg_points DESC LIMIT 10",
  data: [
    {
      player_name: "Micic",
      team_id: 1,
      avg_points: 19.4,
      avg_rebounds: 4.2,
      avg_assists: 5.8,
      avg_3pm: 1.2
    },
    {
      player_name: "Larkin",
      team_id: 2,
      avg_points: 18.8,
      avg_rebounds: 3.9,
      avg_assists: 6.1,
      avg_3pm: 1.5
    },
    {
      player_name: "Teodosic",
      team_id: 3,
      avg_points: 17.9,
      avg_rebounds: 3.5,
      avg_assists: 7.2,
      avg_3pm: 1.1
    }
  ],
  visualization: "table"
};

// ============================================================================
// EJEMPLO 4: Error Case - Datos Vacíos
// ============================================================================

const example4Response = {
  sql: "SELECT * FROM player_stats_games WHERE player_id = 999999",
  data: [],
  visualization: "table",
  error: undefined
};

/*
Resultado: Se muestra el componente de tabla vacía con:
"No hay datos para mostrar."
*/

// ============================================================================
// EJEMPLO 5: Comparativa de Equipos (BarChart)
// ============================================================================

const example5Response = {
  sql: "SELECT t.name, COUNT(g.id) as games_played, CAST(AVG(g.home_score) as NUMERIC(5,1)) as avg_points_for FROM teams t JOIN games g ON t.id = g.home_team_id GROUP BY t.id, t.name ORDER BY avg_points_for DESC",
  data: [
    { name: "Real Madrid", games_played: 34, avg_points_for: 86.5 },
    { name: "Barcelona", games_played: 34, avg_points_for: 84.2 },
    { name: "Efes", games_played: 34, avg_points_for: 82.8 },
    { name: "Panathinaikos", games_played: 34, avg_points_for: 81.5 }
  ],
  visualization: "bar"
};

// ============================================================================
// EJEMPLO 6: Tendencia de Rebotes (LineChart)
// ============================================================================

const example6Response = {
  sql: "SELECT round, CAST(AVG(rebounds_total) as NUMERIC(5,2)) as avg_rebounds FROM player_stats_games WHERE player_id = 50 GROUP BY round ORDER BY round",
  data: [
    { round: 1, avg_rebounds: 6.2 },
    { round: 2, avg_rebounds: 7.1 },
    { round: 3, avg_rebounds: 6.8 },
    { round: 4, avg_rebounds: 7.9 },
    { round: 5, avg_rebounds: 8.3 },
    { round: 6, avg_rebounds: 7.5 }
  ],
  visualization: "line"
};

// ============================================================================
// USO EN CHAT CONTAINER
// ============================================================================

/*
El flujo completo en ChatContainer sería:

1. Usuario escribe: "¿Quiénes son los top 5 anotadores?"
2. ChatContainer envía a /api/chat
3. Backend retorna ejemplo1Response
4. Frontend agrega mensaje assistant con data + visualization
5. MessageBubble renderiza DataVisualizer automáticamente
6. Usuario ve BarChart interactivo

Pseudocódigo (ver ChatContainer.tsx para implementación real):

async function handleSendMessage(content: string) {
  // 1. Agregar mensaje del usuario
  addMessage({
    id: `msg-${Date.now()}-user`,
    role: 'user',
    content,
    timestamp: Date.now()
  });

  setLoading(true);

  try {
    // 2. Llamar backend
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: content,
        history: history.map(m => ({
          role: m.role,
          content: m.content
        }))
      })
    });

    const result = await response.json(); // { sql, data, visualization, error? }

    // 3. Agregar mensaje assistant
    addMessage({
      id: `msg-${Date.now()}-assistant`,
      role: 'assistant',
      content: generateResponseText(result), // Texto descriptivo
      timestamp: Date.now(),
      sql: result.sql,
      data: result.data,
      visualization: result.visualization,
      error: result.error
    });
  } catch (error) {
    setError('No se pudo conectar con el servidor');
  } finally {
    setLoading(false);
  }
}
*/

export {
  example1Response,
  example2Response,
  example3Response,
  example4Response,
  example5Response,
  example6Response,
};

