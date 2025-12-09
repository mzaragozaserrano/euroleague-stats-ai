# Euroleague AI Frontend

Frontend de Next.js 14 para el sistema Text-to-SQL de estadísticas de la Euroliga.

## Requisitos

- Node.js 18+
- npm o yarn

## Setup

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
```bash
cp .env.local.example .env.local
# Editar .env.local con la URL del backend
```

3. Ejecutar servidor de desarrollo:
```bash
npm run dev
```

La aplicación estará disponible en http://localhost:3000

## Build

```bash
npm run build
npm start
```

## Estructura

```
frontend/
├── app/
│   ├── layout.tsx       # Layout principal
│   ├── page.tsx         # Página home
│   └── globals.css      # Estilos globales
├── components/
│   ├── ui/              # Componentes shadcn/ui
│   ├── ChatInterface.tsx
│   └── DataVisualizer.tsx
├── lib/
│   └── utils.ts         # Utilidades
└── public/              # Assets estáticos
```

## Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts
- Zustand (persistencia de chat history)

## Persistencia & Storage

**IMPORTANTE:** El frontend NO contiene base de datos embebida.

- **localStorage (`chat-storage`)**: Persiste SOLO el historial de conversaciones
  - Sobrevive a recargas de página y cierre de tabs
  - Estructura: mensajes, historial, timestamps, contador de queries
  - Versión 3 con migración automática desde versiones antiguas

- **Todos los datos de negocio** (jugadores, equipos, estadísticas) se consultan del backend
  - Source of truth = Neon PostgreSQL (backend)
  - No hay sincronización local ni cache de datos

## Deployment

### Render

Ver [deployment-render.md](./deployment-render.md) para instrucciones completas de deployment en Render.

**Configuración rápida:**
1. Conectar repositorio GitHub a Render
2. Configurar variables de entorno (`NEXT_PUBLIC_API_URL`)
3. Render ejecutará automáticamente `npm run build` y `npm start`

### Variables de Entorno

- `NEXT_PUBLIC_API_URL`: URL del backend (ej: https://euroleague-ai-backend.onrender.com)


