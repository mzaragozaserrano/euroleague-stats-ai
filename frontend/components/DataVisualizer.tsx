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
  return (
    Array.isArray(data) &&
    data.length > 0 &&
    typeof data[0] === 'object' &&
    data[0] !== null
  );
}

/**
 * Renderiza un BarChart
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

  if (!categoryColumn || numericColumns.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No se encontraron columnas válidas para el gráfico de barras.
          </p>
        </div>
      </div>
    );
  }

  // Usar solo la primera columna numérica para evitar cluttering
  const mainColumn = numericColumns[0];
  const colors = [
    '#3b82f6',
    '#ef4444',
    '#10b981',
    '#f59e0b',
    '#8b5cf6',
  ];

  return (
    <div className="w-full h-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={categoryColumn}
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
            tick={{ fontSize: 12 }}
          />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
            }}
          />
          <Legend />
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
 * Renderiza un LineChart
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
      <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No se encontraron columnas válidas para el gráfico de líneas.
          </p>
        </div>
      </div>
    );
  }

  const mainColumn = numericColumns[0];
  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

  return (
    <div className="w-full h-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={categoryColumn}
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
            tick={{ fontSize: 12 }}
          />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey={mainColumn}
            stroke={colors[0]}
            strokeWidth={2}
            dot={{ fill: colors[0], r: 4 }}
            activeDot={{ r: 6 }}
            name={String(mainColumn)}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Renderiza una DataTable
 */
function DataTableRenderer({
  data,
  title,
}: {
  data: Record<string, unknown>[];
  title?: string;
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No hay datos para mostrar.</p>
        </div>
      </div>
    );
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-muted border-b">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2 text-left font-semibold text-muted-foreground"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b hover:bg-muted/50 transition-colors"
              >
                {columns.map((col) => (
                  <td key={`${rowIndex}-${col}`} className="px-4 py-2">
                    {typeof row[col] === 'object'
                      ? JSON.stringify(row[col])
                      : String(row[col])}
                  </td>
                ))}
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
  // Validar datos
  const validData = useMemo(() => {
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

  return (
    <Card className="p-4 md:p-6 w-full overflow-x-auto">
      {visualization === 'bar' && (
        <BarChartRenderer data={validData} title={title} />
      )}
      {visualization === 'line' && (
        <LineChartRenderer data={validData} title={title} />
      )}
      {visualization === 'table' && (
        <DataTableRenderer data={validData} title={title} />
      )}
    </Card>
  );
}

export default DataVisualizer;

