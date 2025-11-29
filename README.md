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
* ✅ **Fase 2:** Backend & AI Engine (Completado - Issue #40)
* 🚧 **Fase 3:** Frontend MVP (En Progreso)

---

## Características Principales

- 🔍 **Consulta en Lenguaje Natural**: Haz preguntas como "Comparativa de puntos por partido entre Micic y Larkin".
- 📊 **Visualización Automática**: El sistema decide la mejor forma de mostrar los datos (tablas, gráficos, shot charts).
- 🎯 **Motor Text-to-SQL**: Utiliza IA para convertir preguntas en consultas SQL precisas.
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

   Crea el archivo `backend/.env` con las siguientes variables (la carpeta backend ya tiene archivo de referencia):

   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@ep-xxxxx.neon.tech/dbname?ssl=require
   OPENROUTER_API_KEY=tu_clave_openrouter
   OPENAI_API_KEY=tu_clave_openai
   ```

   **Notas sobre DATABASE_URL:**
   - Obtén tu URL desde el dashboard de Neon
   - Debe usar `postgresql+asyncpg://` (no `postgresql://`)
   - Incluye `?ssl=require` al final
   - Reemplaza `sslmode=require` con `ssl=require` si vienes de Neon

3. **Ejecutar servidor de desarrollo:**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   La API estará disponible en `http://localhost:8000`

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

   La aplicación estará disponible en `http://localhost:3000`

---

## 🛠️ MCP Setup (Model Context Protocol)

### Descripción

El protocolo MCP permite usar el Agent de Cursor para ejecutar consultas SQL en lenguaje natural directamente contra Neon. Con MCP configurado, puedes hacer preguntas como **"Puntos por partido de Shane Larkin"** y Cursor ejecutará automáticamente la consulta SQL necesaria.

### Requisitos Previos

- Cursor Editor (versión 0.40+)
- Node.js 16+ instalado
- `backend/.env` configurado con `DATABASE_URL`

### Configuración Rápida

1. **Asegúrate de que `backend/.env` está configurado:**

   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@ep-xxxxx.neon.tech/dbname?ssl=require
   OPENROUTER_API_KEY=tu_clave_aqui
   OPENAI_API_KEY=tu_clave_aqui
   ```

2. **El archivo `.cursor/mcp.json` ya está configurado.**
   - Cursor lo detectará automáticamente al reiniciar

3. **Reinicia Cursor completamente** (cierra y abre de nuevo)

### Cómo Usar MCP con Cursor Agent

Una vez configurado, abre el chat de Cursor (Ctrl+K) y haz preguntas en lenguaje natural:

**Ejemplo 1: Puntos por partido**
```
Puntos por partido de Shane Larkin
```

**Ejemplo 2: Estadísticas agregadas**
```
Dame el promedio de puntos de todos los jugadores
```

**Ejemplo 3: Comparativas**
```
Compara los puntos y asistencias de Micic vs Larkin
```

Cursor automáticamente:
1. Interpreta tu pregunta
2. Usa MCP para acceder a la base de datos
3. Ejecuta la consulta SQL correspondiente
4. Muestra los resultados en el chat

### Verificación Manual de Conexión

Si necesitas verificar que MCP funciona correctamente, revisa `backend/tests/mcp_verification_queries.sql`:

```sql
-- Health check
SELECT current_database(), NOW();

-- Contar jugadores
SELECT COUNT(*) as total_players FROM players;

-- Verificar embeddings
SELECT COUNT(*) as total_embeddings FROM schema_embeddings;
```

### Medidas de Seguridad

- **Solo lectura:** MCP solo permite `SELECT` y `EXPLAIN`
- **Timeout:** Máximo 5 segundos por consulta
- **Bloqueadas:** DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
- **Límite:** Máximo 1,000 filas por consulta

### Troubleshooting

| Problema | Solución |
|----------|----------|
| MCP no funciona | Reinicia Cursor; verifica que `DATABASE_URL` existe en `backend/.env` |
| "Database connection failed" | Valida que `DATABASE_URL` usa `postgresql+asyncpg://` y termina con `?ssl=require` |
| Cursor no ejecuta la consulta | Asegúrate de reiniciar Cursor después de configurar `.env` |
| "Query blocked" | Solo se permiten SELECT; no puedes hacer modificaciones |

### Recursos

- [Documentación oficial de MCP](https://modelcontextprotocol.io/)
- [Neon Documentation](https://neon.tech/docs)
- [Cursor Documentation](https://docs.cursor.sh/)

---

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Copyright (c) 2025 Euroleague Stats AI
