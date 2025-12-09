'use client';

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';

export interface DataVisualizerProps {
  data: unknown;
  visualization?: 'bar' | 'line' | 'table';
  title?: string;
}

/**
 * Extrae las columnas numéricas de un conjunto de datos
 * para usarlas como series en gráficos
 */
function getNumericColumns(data: Record<string, unknown>[]): string[] {
  if (!data || data.length === 0) return [];

  const firstRow = data[0];
  return Object.keys(firstRow).filter((key) => {
    const value = firstRow[key];
    return typeof value === 'number';
  });
}

/**
 * Extrae la primera columna de texto para usarla como eje X
 */
function getCategoryColumn(data: Record<string, unknown>[]): string | null {
  if (!data || data.length === 0) return null;

  const firstRow = data[0];
  const textColumn = Object.keys(firstRow).find((key) => {
    const value = firstRow[key];
    return typeof value === 'string';
  });

  return textColumn || null;
}

/**
 * Valida que los datos sean un array de objetos
 */
function isValidData(data: unknown): data is Record<string, unknown>[] {
  // Si es string, intentar parsearlo como JSON
  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data);
      if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object' && parsed[0] !== null) {
        return true;
      }
    } catch {
      // No es JSON válido o no es un array
    }
    return false;
  }

  return (
    Array.isArray(data) &&
    data.length > 0 &&
    typeof data[0] === 'object' &&
    data[0] !== null
  );
}

/**
 * Renderiza un BarChart con diseño moderno
 */
function BarChartRenderer({
  data,
  title,
}: {
  data: Record<string, unknown>[];
  title?: string;
}) {
  const categoryColumn = getCategoryColumn(data);
  const numericColumns = getNumericColumns(data);

  console.log('[BarChartRenderer] categoryColumn:', categoryColumn);
  console.log('[BarChartRenderer] numericColumns:', numericColumns);
  console.log('[BarChartRenderer] data:', data);

  if (!categoryColumn || numericColumns.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-400 dark:text-slate-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No se encontraron columnas válidas para el gráfico de barras.
          </p>
        </div>
      </div>
    );
  }

  // Priorizar columnas más útiles: points, assists, rebounds, pir
  // En lugar de usar la primera columna numérica (que podría ser 'rank' o 'player_id')
  const priorityColumns = ['points', 'assists', 'rebounds', 'pir'];
  const mainColumn = priorityColumns.find(col => numericColumns.includes(col)) || numericColumns[0];
  const colors = [
    '#3b82f6',
    '#ef4444',
    '#10b981',
    '#f59e0b',
    '#8b5cf6',
    '#ec4899',
    '#14b8a6',
  ];

  console.log('[BarChartRenderer] mainColumn:', mainColumn);
  console.log('[BarChartRenderer] Dibujando gráfico con', data.length, 'items');

  return (
    <div className="w-full h-full">
      {title && <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={categoryColumn}
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
            tick={{ fontSize: 12, fill: '#64748b' }}
          />
          <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#f1f5f9',
            }}
            cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar
            dataKey={mainColumn}
            fill={colors[0]}
            radius={[8, 8, 0, 0]}
            name={String(mainColumn)}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Renderiza un LineChart con diseño moderno
 */
function LineChartRenderer({
  data,
  title,
}: {
  data: Record<string, unknown>[];
  title?: string;
}) {
  const categoryColumn = getCategoryColumn(data);
  const numericColumns = getNumericColumns(data);

  if (!categoryColumn || numericColumns.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-400 dark:text-slate-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No se encontraron columnas válidas para el gráfico de líneas.
          </p>
        </div>
      </div>
    );
  }

  const mainColumn = numericColumns[0];
  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6'];

  return (
    <div className="w-full h-full">
      {title && <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={categoryColumn}
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
            tick={{ fontSize: 12, fill: '#64748b' }}
          />
          <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#f1f5f9',
            }}
            cursor={{ stroke: 'rgba(59, 130, 246, 0.2)', strokeWidth: 2 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey={mainColumn}
            stroke={colors[0]}
            strokeWidth={3}
            dot={{ fill: colors[0], r: 5, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 7 }}
            name={String(mainColumn)}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Renderiza una DataTable con diseño moderno y profesional
 */
/**
 * Mapeo de nombres de columnas a nombres legibles
 */
const columnLabels: Record<string, string> = {
  rank: 'Ranking',
  player_id: 'ID',
  player_name: 'Nombre',
  season: 'Temporada',
  points: 'Puntos',
  assists: 'Asistencias',
  rebounds: 'Rebotes',
  pir: 'PIR',
  games_played: 'Partidos',
  steals: 'Robos',
  blocks: 'Tapones',
  turnovers: 'Pérdidas',
  fouls_committed: 'Faltas Cometidas',
  fouls_drawn: 'Faltas a Favor',
};

/**
 * Columnas que se deben ocultar por defecto en contexto de stats de jugadores
 */
const hiddenColumns = new Set(['player_id', 'season']);

function DataTableRenderer({
  data,
  title,
}: {
  data: Record<string, unknown>[];
  title?: string;
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-400 dark:text-slate-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">No hay datos para mostrar.</p>
        </div>
      </div>
    );
  }

  // Filtrar columnas: mostrar solo las que no están en hiddenColumns
  const allColumns = Object.keys(data[0]);
  const columns = allColumns.filter(col => !hiddenColumns.has(col));
  
  // Detectar si hay columnas numéricas para formateo especial
  const numericColumns = columns.filter(col => 
    typeof data[0][col] === 'number'
  );

  const formatValue = (value: unknown, columnName: string): string => {
    if (value === null || value === undefined) return '-';
    
    if (typeof value === 'number') {
      // Formatear números: si es decimal, máximo 2 decimales
      if (Number.isInteger(value)) {
        return value.toLocaleString('es-ES');
      }
      return Number(value).toLocaleString('es-ES', { 
        minimumFractionDigits: 1,
        maximumFractionDigits: 2 
      });
    }
    
    if (typeof value === 'string') return value;
    
    return JSON.stringify(value);
  };

  const getColumnLabel = (colName: string): string => {
    return columnLabels[colName] || colName;
  };

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">{title}</h3>}
      
      {/* Contenedor responsivo */}
      <div className="overflow-x-auto rounded-xl shadow-sm">
        <table className="w-full">
          {/* Header */}
          <thead>
            <tr className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border-b border-slate-200 dark:border-slate-700">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-5 py-3 text-left font-semibold text-slate-700 dark:text-slate-300 text-sm tracking-wide"
                >
                  {getColumnLabel(col)}
                </th>
              ))}
            </tr>
          </thead>
          
          {/* Body */}
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`border-b border-slate-200 dark:border-slate-700 transition-colors ${
                  rowIndex % 2 === 0
                    ? 'bg-white dark:bg-slate-950'
                    : 'bg-slate-50 dark:bg-slate-900'
                } hover:bg-blue-50/50 dark:hover:bg-blue-950/30`}
              >
                {columns.map((col) => {
                  const isNumeric = numericColumns.includes(col);
                  const value = row[col];
                  const formattedValue = formatValue(value, col);
                  
                  return (
                    <td
                      key={`${rowIndex}-${col}`}
                      className={`px-5 py-3 text-sm font-medium text-slate-900 dark:text-slate-100 ${
                        isNumeric ? 'text-right font-semibold text-blue-700 dark:text-blue-300' : ''
                      }`}
                    >
                      <span>{formattedValue}</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Componente principal DataVisualizer
 * Renderiza visualizaciones dinámicas según el tipo especificado
 */
export function DataVisualizer({
  data,
  visualization = 'table',
  title,
}: DataVisualizerProps) {
  // Validar y parsear datos si es necesario
  const validData = useMemo(() => {
    if (!data) return null;
    
    // Si es string JSON, intentar parsearlo
    if (typeof data === 'string') {
      try {
        const parsed = JSON.parse(data);
        return isValidData(parsed) ? parsed : null;
      } catch {
        return null;
      }
    }
    
    return isValidData(data) ? data : null;
  }, [data]);

  if (!validData) {
    return (
      <Card className="p-4 md:p-6 bg-muted/50">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <div>
            <p className="font-semibold text-sm">Datos inválidos</p>
            <p className="text-xs text-muted-foreground">
              No se pudieron procesar los datos para visualizar.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Forzar tabla siempre por ahora para debug
  console.log('[DataVisualizer] Visualización solicitada:', visualization);
  console.log('[DataVisualizer] Usando tabla para debug');

  return (
    <div className="w-full overflow-x-auto">
      <DataTableRenderer data={validData} title={title} />
    </div>
  );
}

export default DataVisualizer;

