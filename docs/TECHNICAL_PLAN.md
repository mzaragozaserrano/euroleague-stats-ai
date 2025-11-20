# PLAN TÉCNICO: Agente de Estadísticas IA de la Euroliga

## 1. Resumen Ejecutivo
Este plan detalla la arquitectura para un motor **Lenguaje Natural a SQL (Text-to-SQL)** centrado en datos de baloncesto de la Euroliga. El sistema está diseñado como una arquitectura *serverless* y por niveles, optimizada para un lanzamiento MVP gratuito (plazo de 3 semanas) con una ruta hacia un nivel "Pro" de pago.

**Restricción Central:** El sistema debe operar dentro de los niveles gratuitos (*free tiers*) de Render (Web Services) y Neon (Postgres), lo que requiere configuraciones específicas como deshabilitar el *connection pooling* a nivel de aplicación y gestionar límites estrictos de almacenamiento (<0.5GB).

---

## 2. Arquitectura del Sistema

### Flujo de Datos de Alto Nivel
1.  **Ingesta:** GitHub Actions (Cron) -> Euroleague Official API -> ETL Script -> Neon DB.
2.  **Consulta (Query):** Usuario (Next.js) -> FastAPI Endpoint -> Búsqueda Vectorial (RAG para el Schema) -> LLM (OpenRouter) -> Generación de SQL -> Ejecución en Neon DB -> Síntesis de Respuesta -> Visualización en el Frontend.

### Stack Tecnológico
* **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui, Recharts.
* **Backend:** Python 3.11+, FastAPI.
* **Base de Datos:** Neon (Serverless PostgreSQL) con `pgvector`.
* **ORM:** SQLAlchemy (Async) con `NullPool` configurado.
* **IA/LLM:**
    * *Orquestación:* LangChain o SDK de OpenAI.
    * *Inferencia:* OpenRouter (Claude 3.5 Haiku para velocidad/costo, Sonnet para lógica compleja).
    * *Embeddings:* `w601sxs/b1ade-embed` (o modelo ligero similar) para la recuperación del esquema (schema retrieval).
* **Infraestructura:** Render (Web Service), GitHub Actions (CI/CD + Cron).

---

## 3. Diseño del Esquema de la Base de Datos (La "Semantic Layer")
El esquema debe optimizarse para la legibilidad del LLM. Los nombres de las tablas y columnas deben ser descriptivos para reducir el uso de *tokens* en los *prompts*.

### Tablas Principales (MVP)
* `teams`: `id`, `code` (ej. 'RMB'), `name`, `logo_url`.
* `players`: `id`, `team_id` (FK), `name`, `position`, `height`, `birth_date`.
* `games`: `id`, `season`, `round`, `home_team_id`, `away_team_id`, `date`, `home_score`, `away_score`.
* `player_stats_games`: (Box Scores Granulares)
    * `id`, `game_id`, `player_id`, `team_id`.
    * Métricas: `minutes`, `points`, `rebounds_total`, `assists`, `steals`, `blocks`, `turnovers`, `fg2_made`, `fg2_attempted`, `fg3_made`, `fg3_attempted`, `ft_made`, `ft_attempted`, `fouls_drawn`, `fouls_committed`.
    * *Índice Calculado:* `pir` (Performance Index Rating).

### Almacén de Vectores (Vector Store - RAG)
* `schema_embeddings`:
    * `id`: uuid.
    * `content`: text (Descripción de una tabla o ejemplo de SQL complejo).
    * `embedding`: vector (384 o 768 dimensiones).
    * *Propósito:* Permite al LLM encontrar las definiciones de tablas y columnas relevantes sin cargar todo el esquema en la ventana de contexto.

---

## 4. Detalles de Implementación de IA y Backend

### A. El Pipeline Text-to-SQL
Para prevenir alucinaciones y asegurar un SQL válido, utilizaremos un enfoque basado en RAG para la selección del esquema.

**Flujo de Trabajo (Workflow):**
1.  **User Input:** "Compara el porcentaje de triples de Micic y Larkin."
2.  **Schema Retrieval:** Convertir *input* a vector -> Consultar `schema_embeddings` -> Recuperar definiciones para `players` y `player_stats_games`.
3.  **Construcción del Prompt:**
    * *Sistema:* "Eres un experto en SQL de Postgres para datos de baloncesto de la Euroliga."
    * *Contexto:* "Aquí están las tablas relevantes: {retrieved_schema}. Usa estrictamente estas columnas."
    * *Tarea:* "Genera una única consulta SQL para responder: {user_input}. Devuelve JSON con las claves: `sql_query`, `visualization_suggestion` (bar, line, table)."
4.  **Ejecución:** Ejecutar SQL contra Neon.
5.  **Seguridad (Safety):** Usuario de base de datos de solo lectura para la API para prevenir inyección/eliminación.

### B. Gestión de Conexiones (Crítico)
Dado que Neon es *serverless* y escala a cero, el *connection pooling* estándar causa errores.
* **Configuración:** El motor de SQLAlchemy debe usar `poolclass=NullPool`.
* **Efecto:** Abre una conexión por solicitud y la cierra inmediatamente. Se basa en el PgBouncer interno de Neon.

### C. Endpoints de la API
* `POST /api/chat`: Acepta `{ "query": string, "history": list }`. Devuelve `{ "data": list, "columns": list, "chart_type": string, "sql_generated": string }`.
* `GET /health`: Un simple *ping* para las comprobaciones de salud de Render.

---

## 5. Arquitectura del Frontend (Next.js)

### Componentes
* **ChatInterface:** Maneja la entrada del usuario (*user input*), los estados de carga y muestra el flujo de conversación.
* **DataVisualizer:** Un "Componente Inteligente" que toma la respuesta del *backend* y decide qué renderizar:
    * Si `chart_type == 'line'`: Renderiza `<Recharts.LineChart />` (ej. puntos a lo largo del tiempo).
    * Si `chart_type == 'bar'`: Renderiza `<Recharts.BarChart />` (ej. comparación de jugadores).
    * Si `chart_type == 'table'`: Renderiza Shadcn `<Table />`.

### Gestión del Estado (State Management)
* Usar React Context o Zustand para gestionar la sesión de historial del *chat* localmente.

---

## 6. Pipeline ETL (GitHub Actions)
Necesitamos una forma de costo cero para mantener los datos frescos.

* **Trigger:** Programación Cron `0 8 * * *` (Diario a las 8 AM UTC).
* **Script (Python):**
    1.  Obtener `/games` de la Euroleague API para la temporada actual.
    2.  Identificar juegos nuevos/completados desde la última ejecución.
    3.  Obtener `/playerstats` (*box scores*) para esos juegos.
    4.  **Upsert** los datos en Neon (prevenir duplicados).
* **Secretos:** Almacenar `NEON_DATABASE_URL` y `EUROLEAGUE_API_KEY` (si es necesario) en GitHub Secrets.

---

## 7. Hoja de Ruta de Implementación (3 Semanas)

### Semana 1: Fundación (Data & Infraestructura)
* **Tarea 1.1:** Inicializar GitHub Repo y Neon DB.
* **Tarea 1.2:** Escribir `etl_script.py` para obtener Teams, Players y Season Stats de la Euroleague API.
* **Tarea 1.3:** Configurar GitHub Action para hidratar la DB.

### Semana 2: El Cerebro (Backend & IA)
* **Tarea 2.1:** Configurar FastAPI con `NullPool`.
* **Tarea 2.2:** Implementar la lógica de recuperación RAG (incrustar definiciones de esquema).
* **Tarea 2.3:** Construir la cadena de *prompt* Text-to-SQL con OpenRouter.

### Semana 3: Experiencia (Frontend & Polish)
* **Tarea 3.1:** Construir la interfaz de usuario de Chat de Next.js.
* **Tarea 3.2:** Implementar la lógica del componente `DataVisualizer`.
* **Tarea 3.3:** Desplegar en Render y realizar UAT (Pruebas de Aceptación del Usuario).

---

## 8. Restricciones y Estándares
* **Linting:** `ruff` para Python, `eslint` para TypeScript.
* **Formato:** `black` (Python), `prettier` (JS/TS).
* **Entorno:** Separación estricta de las variables `.env`. Nunca subir las claves al repositorio.
* **Manejo de Errores:** La interfaz de usuario debe manejar elegantemente los fallos en la generación de SQL (ej. "No pude encontrar ese dato, intenta preguntar de forma más sencilla").