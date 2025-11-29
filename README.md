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

## 🛠️ MCP Setup (Model Context Protocol)

### Descripción

El protocolo MCP permite integrar herramientas externas directamente en Cursor para ejecutar y validar queries SQL contra la base de datos Neon sin dejar el editor. Esto mejora significativamente la experiencia del desarrollador (DX) permitiendo verificar la integridad de datos antes de integrar cambios en el Frontend.

### Requisitos Previos

- ✅ Cursor Editor (versión 0.40+)
- ✅ Base de datos Neon configurada con `DATABASE_URL` válida
- ✅ Node.js 16+ instalado en tu máquina

### Configuración

1. **Verificar `DATABASE_URL` en variables de entorno:**

   ```bash
   # En backend/.env
   DATABASE_URL=postgresql+asyncpg://user:password@host/database
   ```

2. **Configuración automática en Cursor:**

   El archivo `.cursor/mcp.json` ya está configurado. Cursor lo detectará automáticamente al reiniciar.

   Para verificar que está activo:
   - Abre Cursor
   - Presiona `Cmd+Shift+P` (Mac) o `Ctrl+Shift+P` (Windows)
   - Busca "MCP" o "Model Context Protocol"
   - Deberías ver opciones para usar el servidor Neon

### Uso

Una vez configurado, puedes:

1. **Ejecutar queries de prueba directamente en el editor:**
   - Escribe una query SQL en un archivo temporal
   - Usa el MCP para ejecutarla contra Neon sin salir de Cursor

2. **Validar integridad de datos:**
   ```sql
   -- Ejemplo: Verificar que las estadísticas de un jugador sean coherentes
   SELECT COUNT(*) as total_stats FROM player_stats_games
   WHERE player_id = 123 AND points > 100;
   ```

3. **Verificar esquema:**
   ```sql
   -- Listar todas las tablas disponibles
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

### Medidas de Seguridad

- **Solo lectura:** El MCP solo permite operaciones `SELECT` y `EXPLAIN`
- **Timeout:** Las queries tienen un límite de 5 segundos
- **Validación:** Se valida automáticamente que no contengan keywords peligrosos (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE)
- **Límite de resultados:** Máximo 1,000 filas por query

### Troubleshooting

| Problema | Solución |
|----------|----------|
| MCP no aparece en Cursor | Reinicia Cursor y verifica que `.cursor/mcp.json` existe |
| Error de conexión a Neon | Valida que `DATABASE_URL` es correcta y la red lo permite |
| Query tarda demasiado | Reduce el rango de datos (agrega `LIMIT`) o revisa índices |
| "Query blocked" | Verifica que solo uses SELECT; no están permitidas modificaciones |

### Recursos

- [Documentación oficial de MCP](https://modelcontextprotocol.io/)
- [Neon Documentation](https://neon.tech/docs)
- [Cursor MCP Integration Guide](https://docs.cursor.sh/)

---

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Copyright (c) 2025 Euroleague Stats AI