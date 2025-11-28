# Euroleague Stats AI

![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-IN_PROGRESS-yellow)

Motor de consulta de estadísticas de la Euroliga mediante lenguaje natural con inteligencia artificial.

## Descripción

Esta aplicación permite a los aficionados, analistas y jugadores de fantasy hacer consultas complejas sobre estadísticas de la Euroliga usando lenguaje natural. En lugar de navegar por filtros y menús, simplemente haz una pregunta y obtén la respuesta visualizada instantáneamente.

**Visión:** Crear el "Statmuse de la Euroliga" - una herramienta donde la barrera entre la curiosidad del aficionado y la respuesta estadística sea cero.

---

## ✅ Estado del Proyecto

* ✅ **Fase 0:** Scaffolding & Setup (Completado)
* ✅ **Fase 1:** Data Pipeline MVP (Completado - Enero 2025)
* ✅ **Fase 2:** Backend & AI Engine (Completado - Enero 2025)
  - Vectorización de metadatos (#30)
  - Servicio RAG (#31)
  - Text-to-SQL con OpenRouter (#32)
  - Chat Endpoint (#33)
  - BDD Testing con pytest (15 scenarios, 53+ unit tests) (#34)
* 🚧 **Fase 3:** Frontend MVP (En Progreso)

---

## Características Principales

- 🔍 **Consulta en Lenguaje Natural**: Haz preguntas como "Comparativa de puntos por partido entre Micic y Larkin".
- 📊 **Visualización Automática**: El sistema decide la mejor forma de mostrar los datos (tablas, gráficos, shot charts).
- 🎯 **Motor Text-to-SQL**: Utiliza IA para convertir preguntas en consultas SQL precisas y seguras.
- 🛡️ **SQL Safety First**: Validación robusta contra inyecciones SQL y operaciones peligrosas (DROP/DELETE/UPDATE).
- 🧠 **RAG + Schema Embeddings**: Recuperación inteligente de metadatos para generar SQL sin alucinaciones.
- ✅ **BDD Tested**: 15+ scenarios de prueba con cobertura de edge cases y rendimiento.
- 🆓 **Modelo Freemium**: Acceso gratuito a estadísticas básicas (MVP), arquitectura lista para plan Pro.

---

## 📚 Documentación (SDD)

Este proyecto sigue una arquitectura dirigida por documentación. Para detalles técnicos profundos, consulta la carpeta [`docs/`](./docs/):

* **[Visión del Proyecto](docs/project_brief.md):** Alcance, métricas de éxito y reglas de negocio UI.
* **[Arquitectura Técnica](docs/architecture.md):** Esquema de base de datos, algoritmos RAG y estrategia Text-to-SQL.
* **[Roadmap](docs/roadmap.md):** Historial de fases completadas y planes futuros.
* **[Contexto Activo](docs/active_context.md):** Estado actual del desarrollo y decisiones recientes.

> *Nota: Documentación histórica y especificaciones originales archivadas en `docs/archive/`.*

---

## Stack Tecnológico

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui, Recharts.
- **Backend**: Python 3.11+, FastAPI, Poetry.
- **Base de Datos**: Neon (Serverless PostgreSQL) con `pgvector`.
- **IA/LLM**: OpenRouter (Claude 3.5), RAG con OpenAI Embeddings.
- **Infraestructura**: Render (Web Services), GitHub Actions (CI/CD + Cron).

---

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
   # Configurar DATABASE_URL (usar postgresql+asyncpg://) y OPENAI_API_KEY
   ```

3. **Ejecutar servidor de desarrollo:**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

### Frontend

1. **Instalar dependencias:**

   ```bash
   cd frontend
   npm install
   ```

2. **Ejecutar servidor de desarrollo:**

   ```bash
   npm run dev
   ```

---

## 🧪 Testing

### Ejecutar Tests BDD

```bash
cd backend
poetry run pytest tests/step_defs/test_rag_steps.py -v
```

**Cobertura:**
- 15 scenarios BDD para SQL generation
- Validación de SQL safety (inyecciones, operaciones peligrosas)
- RAG retrieval con/sin historial
- Manejo de NULL, caracteres especiales, performance

### Ejecutar Unit Tests

```bash
poetry run pytest tests/test_text_to_sql_service.py tests/test_vectorization_service.py -v
```

**Cobertura:**
- 27 tests de TextToSQLService (validación SQL, prompts, seguridad)
- 11 tests de VectorizationService (embeddings, métodos, constantes)

### Reporte de Cobertura

```bash
poetry run pytest tests/ --cov=app/services --cov-report=term-missing
```

---

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Copyright (c) 2025 Euroleague Stats AI