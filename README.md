# Euroleague Stats AI

![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-MVP_COMPLETE-green)

Motor de consulta de estadísticas de la Euroliga mediante lenguaje natural con inteligencia artificial.

## Descripción

Una interfaz de inteligencia de datos para la Euroliga basada en lenguaje natural. Invertimos el flujo de trabajo tradicional: en lugar de que el usuario busque y filtre datos manualmente, el usuario hace una pregunta ("¿Quién tiene mejor % de triples, Micic o Larkin?") y la IA recupera la respuesta visualizada instantáneamente.

**Visión:** Crear el "Statmuse de la Euroliga" - una herramienta donde la barrera entre la curiosidad del aficionado y la respuesta estadística sea cero.

---

## ✅ Estado del Proyecto

* ✅ **Fase 0:** Scaffolding & Setup (Completado)
* ✅ **Fase 1:** Data Pipeline MVP (Completado - Enero 2025)
* ✅ **Fase 2:** Backend & AI Engine (Completado - Issue #40)
* ✅ **Fase 3:** Frontend MVP (Completado - UI completa con visualizaciones)
* 🚧 **Fase 4:** Post-MVP / Pro Features (Futuro)

---

## Características Principales (MVP Implementado ✅)

- 🔍 **Consulta en Lenguaje Natural**: Haz preguntas como "Top 10 anotadores" o "Mejores reboteadores del Real Madrid". El sistema corrige automáticamente erratas tipográficas (ej: "Campazo" → "Campazzo").
- 📊 **Visualización Automática**: El sistema decide automáticamente la mejor forma de mostrar los datos (Tabla, Bar Chart o Line Chart) usando Recharts.
- 🎯 **Motor Text-to-SQL con RAG**: Utiliza Retrieval Augmented Generation sobre el esquema de base de datos para mejorar precisión en la generación de SQL. Fallback seguro si RAG no está disponible.
- 💾 **Persistencia Inteligente**: Historial de chat almacenado en localStorage con sistema automático de backup y recuperación de datos legacy.
- 🔄 **ETL Automático**: Pipeline diario (8 AM UTC) que ingiere datos desde la API de Euroleague. Actualmente solo temporada 2025.
- 🆓 **Modelo Freemium**: MVP gratuito con estadísticas básicas de temporada 2025. Arquitectura lista para Tier Pro (stats espaciales/shot-charts).

### Limitaciones Actuales

- ⚠️ **Solo temporada 2025**: La base de datos contiene únicamente datos de la temporada E2025 (jugadores, equipos, estadísticas agregadas).
- ⚠️ **No hay datos de partidos**: Las consultas que requieren estadísticas por partido individual no están disponibles (tabla `player_game_stats` no poblada).
- ✅ **Sí disponible**: Estadísticas agregadas por temporada, metadatos de equipos y jugadores, comparativas y rankings.

---

## 📚 Documentación (SDD)

Este proyecto sigue una arquitectura dirigida por documentación. Para detalles técnicos profundos, consulta la carpeta [`docs/`](./docs/):

* **[Visión del Proyecto](docs/project-brief.md):** Alcance, métricas de éxito y reglas de negocio UI.
* **[Arquitectura Técnica](docs/architecture.md):** Esquema de base de datos, algoritmos RAG y estrategia Text-to-SQL.
* **[Roadmap](docs/roadmap.md):** Historial de fases completadas y planes futuros.
* **[Contexto Activo](docs/active-context.md):** Estado actual del desarrollo y decisiones recientes.

> *Nota: Documentación histórica y especificaciones originales archivadas en `docs/archive/`.*

---

## Stack Tecnológico

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui, Recharts, Zustand.
- **Backend**: Python 3.11+, FastAPI, Poetry, SQLAlchemy (Async) + asyncpg.
- **Base de Datos**: Neon (Serverless PostgreSQL 16) con extensión `pgvector` para embeddings.
- **IA/LLM**: 
  - **OpenAI API**: Embeddings (`text-embedding-3-small`) y corrección de consultas
  - **OpenRouter**: Generación de SQL con modelo `openai/gpt-3.5-turbo`
  - **RAG**: Sistema de Retrieval Augmented Generation sobre esquema de BD
- **Infraestructura**: Render (Web Services), GitHub Actions (CI/CD + ETL Cron diario).
- **Testing**: pytest-bdd + pytest-asyncio para BDD tests.

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

El protocolo MCP permite usar el Agent de Cursor para ejecutar consultas en lenguaje natural contra la base de datos de Euroleague. Con MCP configurado, puedes hacer preguntas como **"Cuantos jugadores hay?"** o **"Puntos por partido de Shane Larkin"** y Cursor ejecutará automáticamente la conversión a SQL y recuperará los datos.

**Arquitectura del Servidor MCP:**
```
Query Natural (español)
     ↓
Corrección de Consulta (OpenAI via OpenRouter)
     ↓
Obtener Contexto de Esquema (RAG con OpenAI embeddings)
     ↓
Generar SQL con LLM (OpenRouter - GPT-3.5-turbo)
     ↓
Validar SQL (seguridad - solo SELECT)
     ↓
Ejecutar contra PostgreSQL (Neon)
     ↓
Generar Respuesta en Markdown (OpenRouter - GPT-3.5-turbo)
     ↓
Retornar JSON { sql, data, visualization, message }
```

**Flujo Completo de una Consulta:**
1. Usuario escribe query en el chat frontend
2. Frontend envía `POST /api/chat` con query + historial
3. Backend procesa:
   - Corrección de consulta (normaliza nombres y corrige erratas) - GPT-3.5-turbo via OpenRouter
   - RAG: Genera embedding, busca esquema relevante en `schema_embeddings` - OpenAI embeddings
   - Generación de SQL usando contexto de esquema - GPT-3.5-turbo via OpenRouter
   - Ejecución contra BD (Neon)
   - Generación de respuesta en Markdown basada en los datos obtenidos - GPT-3.5-turbo via OpenRouter
   - Retorna JSON con SQL, datos, tipo de visualización y mensaje en Markdown
4. Frontend renderiza:
   - Mensaje en Markdown (texto formateado con negritas, tablas, etc.)
   - Visualización de datos (BarChart, LineChart, DataTable) cuando corresponde
5. localStorage persiste el chat para futuras sesiones (con backup automático)

### Requisitos Previos

- Cursor Editor (versión 0.40+)
- Python 3.11+ instalado
- Poetry instalado
- `backend/.env` configurado con:
  - `DATABASE_URL` (connection string de Neon)
  - `OPENROUTER_API_KEY` (para generación de SQL)
  - `OPENAI_API_KEY` (para embeddings y corrección de consultas)

### Configuración Rápida

1. **Asegúrate de que `backend/.env` está configurado:**

   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@ep-xxxxx.neon.tech/dbname?ssl=require
   OPENROUTER_API_KEY=tu_clave_aqui
   OPENAI_API_KEY=tu_clave_aqui
   ```

2. **Instala dependencias del backend:**

   ```bash
   cd backend
   poetry install
   ```

3. **El archivo `.cursor/mcp.json` ya está configurado.**
   - Cursor lo detectará automáticamente al reiniciar
   - El servidor se ejecuta mediante `run_mcp.py` que carga las variables de entorno correctamente

4. **Reinicia Cursor completamente** (cierra y abre de nuevo)

### Herramientas Disponibles

El servidor MCP expone tres herramientas principales:

#### 1. `query_natural` - Consultas en lenguaje natural
```
@text-to-sql query_natural "Cuantos jugadores hay?"
```
**Respuesta:**
```json
{
  "sql": "SELECT COUNT(*) as total FROM players;",
  "data": [{"total": 245}],
  "visualization": "table",
  "row_count": 1
}
```

#### 2. `count_players` - Contador rápido de jugadores
```
@text-to-sql count_players
```

#### 3. `list_tables` - Listar tablas disponibles
```
@text-to-sql list_tables
```

### Cómo Usar MCP con Cursor Agent

Una vez configurado, usa el símbolo `@text-to-sql` en el chat de Cursor:

**Ejemplo 1: Contar jugadores**
```
@text-to-sql query_natural "¿Cuantos jugadores hay en total?"
```

**Ejemplo 2: Estadísticas de jugador**
```
@text-to-sql query_natural "Dame los puntos de Shane Larkin"
```

**Ejemplo 3: Top rankings**
```
@text-to-sql query_natural "Top 10 anotadores de esta temporada"
```

**Ejemplo 4: Estadísticas por equipo**
```
@text-to-sql query_natural "Mejores reboteadores del Real Madrid"
```

**Ejemplo 5: Comparativas**
```
@text-to-sql query_natural "Compara asistencias entre Micic y Larkin"
```

**Nota:** Las consultas sobre partidos individuales no están disponibles actualmente (solo temporada 2025 agregada).

Cursor automáticamente:
1. Detecta la herramienta MCP invocada
2. Envía la query al servidor MCP
3. El servidor convierte a SQL usando IA
4. Ejecuta contra Neon
5. Muestra resultados en el chat

### Medidas de Seguridad

- **Solo lectura:** Solo se permiten consultas SELECT
- **Validación de SQL:** Se rechazan operaciones DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, GRANT, REVOKE
- **Timeout:** Máximo 30 segundos por consulta
- **Límite:** Máximo 1,000 filas por respuesta
- **Parentesis balanceados:** Se valida sintaxis básica del SQL

### Troubleshooting

| Problema | Solución |
|----------|----------|
| MCP no funciona | Reinicia Cursor; verifica que `backend/.env` esté configurado correctamente |
| "DATABASE_URL no configurada" | Asegúrate de tener `backend/.env` con `DATABASE_URL` |
| "OPENROUTER_API_KEY no configurada" | Configura tu clave de OpenRouter en `backend/.env` |
| Error al generar SQL | Intenta ser más específico en tu pregunta natural |
| Cursor no ejecuta | Verifica que Poetry y Python 3.11+ están instalados |

**Para verificar el servidor MCP manualmente:**

```bash
cd backend
poetry run python run_mcp.py
```

El servidor se iniciará y esperará conexiones vía stdio. Los logs se guardan en `backend/mcp_server.log`. Para detener el servidor, presiona `Ctrl+C`.

### Recursos

- [Documentación oficial de MCP](https://modelcontextprotocol.io/)
- [Neon Documentation](https://neon.tech/docs)
- [Cursor Documentation](https://docs.cursor.sh/)
- [OpenRouter API](https://openrouter.ai/)

---

## Datos y ETL

### Fuente de Datos

- **API Euroleague**: Datos oficiales de la Euroliga obtenidos vía GitHub Actions
- **ETL Diario**: Ejecuta automáticamente a las 8 AM UTC todos los días
- **Temporada Actual**: Solo temporada 2025 (E2025) está disponible
- **Datos Ingeridos**: Equipos, jugadores, estadísticas agregadas por temporada (`player_season_stats`)

### Estructura de Datos

- **`teams`**: Información de equipos (código, nombre, logo)
- **`players`**: Información de jugadores (código, nombre, posición, equipo, temporada)
- **`player_season_stats`**: Estadísticas agregadas por temporada (puntos, rebotes, asistencias, triples, PIR)
- **`schema_embeddings`**: Metadatos vectorizados para RAG (tablas, columnas, ejemplos SQL)
- **`games`**: Metadatos de partidos (NO poblada actualmente)
- **`player_game_stats`**: Estadísticas por partido (NO poblada actualmente)

Para más detalles sobre el esquema, consulta [`docs/architecture.md`](./docs/architecture.md).

---

## Próximos Pasos (Fase 4)

- **4.1 Datos de Partidos**: Extender ETL para ingerir estadísticas detalladas por partido
- **4.2 Visualizaciones Espaciales**: Shot charts, heatmaps con PostGIS
- **4.3 Análisis de Partidos**: Resúmenes automáticos de partidos concretos
- **4.4 Monetización**: Sistema para costear infraestructura y APIs

Ver [`docs/roadmap.md`](./docs/roadmap.md) para más detalles.

---

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Copyright (c) 2025 Euroleague Stats AI
