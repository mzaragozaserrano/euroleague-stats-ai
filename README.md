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

- [`BLUEPRINT.md`](./docs/BLUEPRINT.md) - Análisis de viabilidad, mercado y arquitectura estratégica
- [`TECHNICAL_PLAN.md`](./docs/TECHNICAL_PLAN.md) - Plan técnico detallado y arquitectura del sistema
- [`SPECIFICATIONS.md`](./docs/SPECIFICATIONS.md) - Especificaciones funcionales del producto
- [`SPECIFICATIONS_GHERKIN.md`](./docs/SPECIFICATIONS_GHERKIN.md) - Especificaciones en formato Gherkin para testing BDD

## Estado del Proyecto

🚧 **En desarrollo** - MVP en construcción (3 semanas)

### Hoja de Ruta

- **Semana 1**: Fundación (Data & Infraestructura)
- **Semana 2**: El Cerebro (Backend & IA)
- **Semana 3**: Experiencia (Frontend & Polish)

## Instalación y Configuración

*Próximamente: instrucciones de instalación y configuración*

## Contribuir

Este es un proyecto personal en desarrollo. Las contribuciones serán bienvenidas una vez se complete el MVP.

## Licencia

*Por definir*

## Referencias

- [API Oficial de Euroleague](https://api-live.euroleague.net/swagger/index.html)
- [Neon Database](https://neon.tech)
- [OpenRouter](https://openrouter.ai)
- [Render](https://render.com)

