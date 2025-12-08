# DataVisualizer Component Documentation

## Descripción General

El componente `DataVisualizer` proporciona visualizaciones dinámicas (BarChart, LineChart, DataTable) usando Recharts. Se integra perfectamente con el pipeline de chat del backend que retorna datos estructurados con información sobre el tipo de visualización recomendado.

## Props

```typescript
interface DataVisualizerProps {
  data: unknown;              // Array de objetos con datos
  visualization?: 'bar' | 'line' | 'table';  // Tipo de visualización (por defecto: 'table')
  title?: string;            // Título opcional del gráfico
}
```

## Tipos de Visualización

### 1. BarChart
- **Caso de uso**: Comparativas, distribuciones, categorías discretas
- **Ejemplo**: "Puntos por jugador", "Rebotes por equipo"
- **Requisitos de datos**:
  - Debe haber al menos una columna de texto (eje X)
  - Debe haber al menos una columna numérica (eje Y)

```typescript
<DataVisualizer
  data={[
    { player: 'Micic', points: 24 },
    { player: 'Larkin', points: 22 },
    { player: 'Teodosic', points: 20 }
  ]}
  visualization="bar"
  title="Puntos por Jugador"
/>
```

### 2. LineChart
- **Caso de uso**: Tendencias temporales, evolución de valores
- **Ejemplo**: "Puntos por jornada", "Promedio de asistencias en temporada"
- **Requisitos de datos**:
  - Debe haber al menos una columna con categorías (eje X)
  - Debe haber al menos una columna numérica (eje Y)

```typescript
<DataVisualizer
  data={[
    { round: 1, points: 20 },
    { round: 2, points: 25 },
    { round: 3, points: 22 }
  ]}
  visualization="line"
  title="Evolución de Puntos"
/>
```

### 3. DataTable
- **Caso de uso**: Datos detallados, múltiples atributos por fila
- **Ejemplo**: "Estadísticas completas del equipo", "Listado de jugadores"
- **Requisitos de datos**:
  - Array de objetos (sin restricción de tipos)

```typescript
<DataVisualizer
  data={[
    { name: 'Micic', team: 'Real Madrid', points: 24, rebounds: 5 },
    { name: 'Larkin', team: 'Barcelona', points: 22, rebounds: 6 }
  ]}
  visualization="table"
  title="Estadísticas de Jugadores"
/>
```

## Integración con MessageBubble

El componente se integra automáticamente con `MessageBubble` cuando el mensaje contiene propiedades `data` y `visualization`:

```typescript
const message: ChatMessage = {
  id: 'msg-123',
  role: 'assistant',
  content: 'Aquí están los puntos por jugador:',
  timestamp: Date.now(),
  data: [
    { player: 'Micic', points: 24 },
    { player: 'Larkin', points: 22 }
  ],
  visualization: 'bar',
  sql: 'SELECT player_name as player, points FROM player_stats...'
};
```

## Manejo de Casos Edge

### Datos Vacíos
El componente muestra un mensaje de error elegante:
```
⚠️  No hay datos para mostrar.
```

### Datos Inválidos
Cuando los datos no son un array o son null:
```
⚠️  Datos inválidos
   No se pudieron procesar los datos para visualizar.
```

### Columnas No Compatibles
Si no hay columnas numéricas para un BarChart:
```
⚠️  No se encontraron columnas válidas para el gráfico de barras.
```

## Características

### Auto-Detección de Columnas
- **BarChart/LineChart**: Detectan automáticamente la primera columna de texto (eje X) y la primera columna numérica (eje Y)
- **DataTable**: Renderiza todas las columnas disponibles

### Responsividad
- Los gráficos usan `ResponsiveContainer` para adaptarse al ancho disponible
- En móvil, las etiquetas se rotan automáticamente (ángulo -45°)
- Las tablas tienen scroll horizontal en dispositivos pequeños

### Styling
- Utiliza Tailwind CSS y `shadcn/ui` Card para consistencia visual
- Colores definidos: `#3b82f6`, `#ef4444`, `#10b981`, `#f59e0b`, `#8b5cf6`
- Tema adaptable a dark/light mode via Tailwind

### Codificación UTF-8
- Soporta caracteres especiales (ñ, á, é, etc.)
- Los datos se procesan correctamente sin corrupción de caracteres

## Ejemplo Completo en el Chat

```typescript
// Backend retorna:
{
  "sql": "SELECT player_name, SUM(points) as total_points FROM player_stats GROUP BY player_name ORDER BY total_points DESC LIMIT 5",
  "data": [
    { "player_name": "Micic", "total_points": 120 },
    { "player_name": "Larkin", "total_points": 115 },
    { "player_name": "Teodosic", "total_points": 110 },
    { "player_name": "De Colo", "total_points": 105 },
    { "player_name": "Osman", "total_points": 100 }
  ],
  "visualization": "bar"
}

// Frontend renderiza:
<MessageBubble
  message={{
    id: 'msg-xyz',
    role: 'assistant',
    content: 'Top 5 anotadores de la temporada:',
    timestamp: Date.now(),
    data: [...],
    visualization: 'bar',
    sql: '...'
  }}
/>

// Resultado: BarChart con 5 barras, etiquetas de jugadores, títulos, leyenda, tooltip
```

## Testing

### Vitest / Jest (Recomendado para Frontend)
```typescript
import { render, screen } from '@testing-library/react';
import { DataVisualizer } from '@/components/DataVisualizer';

describe('DataVisualizer', () => {
  it('renders BarChart with valid data', () => {
    const data = [
      { name: 'A', value: 40 },
      { name: 'B', value: 60 }
    ];

    render(
      <DataVisualizer data={data} visualization="bar" />
    );

    // Assertions here
  });

  it('handles empty data gracefully', () => {
    render(
      <DataVisualizer data={[]} visualization="table" />
    );

    expect(screen.getByText(/no hay datos/i)).toBeInTheDocument();
  });
});
```

### pytest-bdd (Backend/Integration)
Consulta `backend/tests/features/data_visualizer.feature` para escenarios BDD.

## Notas Importantes

1. **Recharts Installation**: Ya está incluido en `package.json` (`recharts@^2.12.0`)

2. **Performance**: 
   - Los gráficos usan `useMemo` para validación de datos
   - ResponsiveContainer optimiza renders en cambios de tamaño

3. **Accesibilidad**:
   - Recharts proporciona soporte básico de accesibilidad
   - Las tablas son navegables con teclado

4. **Límites de Datos**:
   - El backend ya limita a 1000 filas máximo
   - Recomendado < 50 puntos en charts para legibilidad

## Referencias

- [Recharts Documentation](https://recharts.org/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)

