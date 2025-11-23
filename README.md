# Euroleague Stats AI

Motor de consulta de estadísticas de la Euroliga mediante lenguaje natural con inteligencia artificial.

## Descripción

Esta aplicación permite a los aficionados, analistas y jugadores de fantasy hacer consultas complejas sobre estadísticas de la Euroliga usando lenguaje natural. En lugar de navegar por filtros y menús, simplemente haz una pregunta y obtén la respuesta visualizada instantáneamente.

**Visión:** Crear el "Statmuse de la Euroliga" - una herramienta donde la barrera entre la curiosidad del aficionado y la respuesta estadística sea cero.

## Características Principales

- 🔍 **Consulta en Lenguaje Natural**: Haz preguntas como "Comparativa de puntos por partido entre Micic y Larkin"
- 📊 **Visualización Automática**: El sistema decide la mejor forma de mostrar los datos (tablas, gráficos, shot charts)
- 🎯 **Motor Text-to-SQL**: Utiliza IA para convertir preguntas en consultas SQL precisas
- 🆓 **Modelo Freemium**: Acceso gratuito a estadísticas básicas, plan Pro para estadísticas avanzadas y espaciales

## Stack Tecnológico

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui, Recharts
- **Backend**: Python 3.11+, FastAPI
- **Base de Datos**: Neon (Serverless PostgreSQL) con pgvector
- **IA/LLM**: OpenRouter (Claude 3.5 Haiku/Sonnet), RAG con embeddings
- **Infraestructura**: Render (Web Services), GitHub Actions (CI/CD + Cron)

## Documentación

La documentación completa del proyecto se encuentra en la carpeta [`docs/`](./docs/):

- [`ROADMAP.md`](./ROADMAP.md) - Plan completo de implementación del proyecto (3 semanas)
- [`BLUEPRINT.md`](./docs/BLUEPRINT.md) - Análisis de viabilidad, mercado y arquitectura estratégica
- [`TECHNICAL_PLAN.md`](./docs/TECHNICAL_PLAN.md) - Plan técnico detallado y arquitectura del sistema
- [`SPECIFICATIONS.md`](./docs/SPECIFICATIONS.md) - Especificaciones funcionales del producto
- [`SPECIFICATIONS_GHERKIN.md`](./docs/SPECIFICATIONS_GHERKIN.md) - Especificaciones en formato Gherkin para testing BDD

### Historial de Fases

Documentación histórica de fases completadas en [`docs/history/`](./docs/history/):
- [`FASE_0_COMPLETADA.md`](./docs/history/FASE_0_COMPLETADA.md) - Resumen de la Fase 0: Scaffolding & Setup
- [`SETUP_STATUS.md`](./docs/history/SETUP_STATUS.md) - Estado detallado del setup inicial

## Estado del Proyecto

🚧 **En desarrollo** - MVP en construcción (3 semanas)

### Hoja de Ruta

- **Semana 1**: Fundación (Data & Infraestructura)
- **Semana 2**: El Cerebro (Backend & IA)
- **Semana 3**: Experiencia (Frontend & Polish)

## Prerrequisitos

### Backend
- **Python 3.11+**
- **Poetry** - Gestor de dependencias Python
- **PostgreSQL** con extensión `pgvector` (recomendado: [Neon](https://neon.tech))

### Frontend
- **Node.js 18+** - Descarga desde [nodejs.org](https://nodejs.org/)
- **npm** - Incluido con Node.js
- **Opcional**: [nvm-windows](https://github.com/coreybutler/nvm-windows) para gestión de versiones de Node.js

## Instalación y Configuración

### Backend

1. **Instalar dependencias con Poetry:**
```bash
cd backend
poetry install
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales:
# DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
# IMPORTANTE: Usar postgresql+asyncpg:// (no postgresql://) para asyncpg driver
# OPENAI_API_KEY=sk-...
```

**Nota sobre Neon**: Si usas Neon (recomendado), la URL que proporcionan usa `postgresql://`. Debes cambiarla a `postgresql+asyncpg://` para que funcione con asyncpg. Ejemplo:
- URL de Neon: `postgresql://user:pass@host/db`
- URL para .env: `postgresql+asyncpg://user:pass@host/db`

3. **Ejecutar servidor de desarrollo:**
```bash
poetry run uvicorn app.main:app --reload
```

El backend estará disponible en:
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs

### Frontend

1. **Instalar dependencias:**
```bash
cd frontend
npm install
```

2. **Configurar variables de entorno:**
```bash
cp .env.local.example .env.local
# Editar .env.local con la URL del backend
```

3. **Ejecutar servidor de desarrollo:**
```bash
npm run dev
```

El frontend estará disponible en: http://localhost:3000

## Ejecución

### Backend
```powershell
cd backend

# El archivo .env ya está configurado con DATABASE_URL de Neon
# Solo falta agregar OPENAI_API_KEY cuando sea necesario para embeddings

# Probar conexión a Neon (opcional):
poetry run python scripts/test_db_connection.py

# Ejecutar servidor:
poetry run uvicorn app.main:app --reload
```
Disponible en: http://localhost:8000
Documentación: http://localhost:8000/docs

### Frontend
```powershell
cd frontend
npm run dev
```
Disponible en: http://localhost:3000

## Endpoints Disponibles

### Backend
- `GET /health` - Health check (funcionando)
- `POST /api/chat` - Chat endpoint (placeholder, se implementará en Fase 2)

### Frontend
- `/` - Página principal con mensaje de bienvenida

## Guía de Desarrollo

### Backend

```bash
# Ejecutar tests
poetry run pytest -v

# Linting
poetry run ruff check .

# Formateo
poetry run black .

# Instalar nueva dependencia
poetry add nombre-paquete
```

### Frontend

#### Instalar componentes shadcn/ui

Para añadir nuevos componentes UI de shadcn/ui:

```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add table
# ... más componentes según necesidad
```

#### Comandos útiles

```bash
# Build para producción
npm run build

# Linting
npm run lint

# Añadir componente shadcn/ui
npx shadcn@latest add nombre-componente
```

## Contribuir

Este es un proyecto personal en desarrollo. Las contribuciones serán bienvenidas una vez se complete el MVP.

## Licencia

*Por definir*

## Referencias

- [API Oficial de Euroleague](https://api-live.euroleague.net/swagger/index.html)
- [Neon Database](https://neon.tech)
- [OpenRouter](https://openrouter.ai)
- [Render](https://render.com)
