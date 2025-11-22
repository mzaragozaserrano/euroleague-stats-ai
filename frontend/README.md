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
- Zustand


