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

* **[Visión del Proyecto](docs/project-brief.md):** Alcance, métricas de éxito y reglas de negocio UI.
* **[Arquitectura Técnica](docs/architecture.md):** Esquema de base de datos, algoritmos RAG y estrategia Text-to-SQL.
* **[Roadmap](docs/roadmap.md):** Historial de fases completadas y planes futuros.
* **[Contexto Activo](docs/active-context.md):** Estado actual del desarrollo y decisiones recientes.

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

El protocolo MCP permite usar el Agent de Cursor para ejecutar consultas en lenguaje natural contra la base de datos de Euroleague. Con MCP configurado, puedes hacer preguntas como **"Cuantos jugadores hay?"** o **"Puntos por partido de Shane Larkin"** y Cursor ejecutará automáticamente la conversión a SQL y recuperará los datos.

**Arquitectura del Servidor MCP:**
```
Query Natural (español)
     ↓
Obtener Contexto de Esquema (RAG)
     ↓
Generar SQL con LLM (OpenRouter)
     ↓
Validar SQL (seguridad)
     ↓
Ejecutar contra PostgreSQL (Neon)
     ↓
Retornar JSON { sql, data, visualization }
```

### Requisitos Previos

- Cursor Editor (versión 0.40+)
- Python 3.11+ instalado
- Poetry instalado
- `backend/.env` configurado con `DATABASE_URL` y `OPENROUTER_API_KEY`

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

**Ejemplo 3: Estadísticas agregadas**
```
@text-to-sql query_natural "Puntos por equipo ordenados descendente"
```

**Ejemplo 4: Comparativas**
```
@text-to-sql query_natural "Compara asistencias entre Micic y Larkin"
```

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

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

Copyright (c) 2025 Euroleague Stats AI
