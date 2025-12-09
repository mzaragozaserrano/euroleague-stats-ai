# Backend Deployment en Render - FastAPI + PostgreSQL

## Descripción General

Este documento describe el proceso para deployar el backend FastAPI de Euroleague AI Stats en Render. El backend se ejecutará en un Web Service de Render y se conectará a Neon (PostgreSQL serverless).

## Requisitos Previos

- Cuenta en Render (https://render.com)
- Cuenta en Neon (https://neon.tech) - para la base de datos PostgreSQL
- Repositorio GitHub conectado a Render
- Variables de entorno necesarias

## Arquitectura de Deployment

```
GitHub Repository
    ↓
Render (CI/CD)
    ↓
Render Web Service (Python 3.11+)
    ↓
Neon PostgreSQL (Serverless)
    ↓
OpenAI API (Embeddings)
    ↓
OpenRouter (LLM)
```

## Paso 1: Configurar Base de Datos en Neon

### 1.1 Crear Proyecto en Neon

1. Ir a https://console.neon.tech
2. Crear cuenta si no la tienes
3. Hacer clic en "New Project"
4. Configurar:
   - **Project Name:** `euroleague-ai`
   - **Database Name:** `euroleague_db`
   - **Region:** Seleccionar región más cercana
5. Obtener connection string:
   - Ir a "Connection String"
   - Copiar la URL (ej: `postgresql://user:password@...`)
   - Guardar para usarla en Render

### 1.2 Inicializar Schema en Neon

1. Conectarse a Neon usando psql:
   ```bash
   psql postgresql://user:password@host.neon.tech/euroleague_db
   ```

2. Ejecutar migraciones (opcional - Render puede hacer esto automáticamente):
   ```bash
   # Desde la carpeta backend
   python scripts/run_migrations.py
   ```

## Paso 2: Preparar Backend para Render

### 2.1 Verificar Configuración de CORS

El archivo `backend/app/main.py` debe permitir el frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://euroleague-ai-frontend.onrender.com"],  # URL de Render frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Importante:** Actualizar `allow_origins` con la URL exacta de tu frontend en Render.

### 2.2 Verificar pyproject.toml

Asegurarse de que todos los dependencias están especificadas:

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.0"
asyncpg = "^0.29.0"
pydantic-settings = "^2.0.0"
# ... otros dependencias
```

## Paso 3: Conectar Backend a Render

### 3.1 Crear Web Service en Render

1. Ir a https://dashboard.render.com
2. Hacer clic en "New +" → "Web Service"
3. Seleccionar repositorio: `euroleague-stats-ai`
4. Configurar:
   - **Name:** `euroleague-ai-backend`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3 (Render detectará automáticamente)
   - **Build Command:** `pip install -r requirements.txt` (o Poetry si es detectado)
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 3.2 Configuración de Python en Render

Render automáticamente detectará:
- `pyproject.toml` (Poetry) - preferido
- `requirements.txt` (pip) - alternativa

Si necesitas Poetry:
1. En "Build Command", usar:
   ```
   pip install poetry; poetry install
   ```
2. En "Start Command", usar:
   ```
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Paso 4: Configurar Variables de Entorno

### 4.1 Variables Requeridas

En el Dashboard de Render, ir a Web Service → Environment y configurar:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql://user:password@host.neon.tech/euroleague_db` | Connection string de Neon |
| `OPENAI_API_KEY` | tu_api_key_aqui | API key para embeddings |
| `OPENROUTER_API_KEY` | tu_api_key_aqui | API key para LLM |
| `ENVIRONMENT` | `production` | Ambiente de ejecución |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

### 4.2 Obtener API Keys

**OpenAI API Key:**
1. Ir a https://platform.openai.com/account/api-keys
2. Crear nueva API key
3. Copiar y guardar en variables de entorno Render

**OpenRouter API Key:**
1. Ir a https://openrouter.ai/settings/api
2. Crear nueva API key
3. Copiar y guardar en variables de entorno Render

## Paso 5: Deploy Automático

### 5.1 Rama de Deploy

Por defecto, Render deployará automáticamente cada push a `main`.

Para cambiar:
1. Dashboard → Web Service → Settings
2. Buscar "Deploy on push"
3. Cambiar rama si es necesario

### 5.2 Monitorear Deploy

1. Dashboard → Web Service → Deploys
2. Ver logs en tiempo real
3. Verificar que:
   - Python se instala correctamente
   - Dependencias se descargan
   - Servidor uvicorn inicia exitosamente

**Tiempo esperado:** 5-10 minutos para el primer deploy.

## Paso 6: Verificación Post-Deploy

### 6.1 Acceder al Backend

1. Dashboard → Web Service → obtener URL (ej: `https://euroleague-ai-backend.onrender.com`)
2. Probar endpoints:
   - Health Check: `GET https://euroleague-ai-backend.onrender.com/health`
   - Documentación: `GET https://euroleague-ai-backend.onrender.com/docs`

### 6.2 Test de Conectividad

```bash
# Health check
curl https://euroleague-ai-backend.onrender.com/health

# Ejemplo de query (adaptado a tu estructura)
curl -X POST https://euroleague-ai-backend.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cuántos jugadores hay?"}'
```

### 6.3 Verificar Base de Datos

En el servidor Render:
1. Dashboard → Web Service → Shell
2. Conectarse a Neon:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM players;"
   ```

## Paso 7: Solución de Problemas

### Error: "ModuleNotFoundError"

**Causa:** Dependencias no están instaladas correctamente.

**Solución:**
1. Verificar `pyproject.toml` o `requirements.txt`
2. Revisar logs de deploy
3. Ejecutar localmente: `poetry install` o `pip install -r requirements.txt`
4. Hacer commit de cambios y hacer push

### Error: "Database connection failed"

**Causa:** `DATABASE_URL` no es correcta o Neon no está accesible.

**Solución:**
1. Verificar variable `DATABASE_URL` en Render
2. Probar connection string localmente:
   ```bash
   psql your_connection_string
   ```
3. Verificar que Neon está activo
4. Re-deployar desde Dashboard

### Error: "CORS error" en Frontend

**Causa:** CORS no está configurado correctamente.

**Solución:**
1. Actualizar `backend/app/main.py`:
   ```python
   allow_origins=[
       "http://localhost:3000",  # desarrollo
       "https://euroleague-ai-frontend.onrender.com",  # producción
   ]
   ```
2. Hacer commit y push a main
3. Render automáticamente re-deployará

### "Service crash" después de deploy

**Causa:** Variasposibles (API keys inválidas, DB no accesible, etc).

**Solución:**
1. Ir a Dashboard → Web Service → Logs
2. Ver mensaje de error exacto
3. Buscar líneas con "ERROR" o "Exception"
4. Verificar variables de entorno
5. Re-deployar

## Paso 8: Monitoreo Continuo

### 8.1 Logs en Tiempo Real

Dashboard → Web Service → Logs:
- Ver solicitudes HTTP
- Errors de aplicación
- Performance metrics

### 8.2 Métricas

Dashboard → Web Service → Metrics:
- CPU usage
- Memory usage
- Response times
- Request count

### 8.3 Configurar Alertas (Opcional)

Render permite configurar alertas para:
- Deploy failures
- High CPU usage
- Service downtime
- Error rate alta

## Paso 9: Actualizaciones y Re-deployment

### 9.1 Actualizar Backend

1. Hacer cambios en `backend/`
2. Hacer commit:
   ```bash
   git add backend/
   git commit -m "feat: backend improvements"
   ```
3. Hacer push a `main`:
   ```bash
   git push origin main
   ```
4. Render automáticamente triggerá nuevo deploy

### 9.2 Ejecutar Migraciones en Neon

Si necesitas ejecutar migraciones en la base de datos remota:

**Opción 1: Shell de Render**
1. Dashboard → Web Service → Shell
2. Ejecutar:
   ```bash
   python scripts/run_migrations.py
   ```

**Opción 2: Local (si tienes acceso a DATABASE_URL)**
1. Obtener DATABASE_URL del Dashboard
2. Localmente:
   ```bash
   DATABASE_URL=postgresql://... python scripts/run_migrations.py
   ```

## Paso 10: Escalabilidad y Costos

### Free Tier Limitations

- Plan free: 0.5 CPU, 1GB RAM
- Request timeout: 30 segundos
- Auto-scales basado en demanda
- "Spin down" después de 15 minutos de inactividad

### Escalabilidad a Producción

Para producción:
1. Cambiar plan de Free a Starter ($7/mes) o Pro ($12/mes)
2. Aumentar resources (CPU, RAM)
3. Configurar multiple replicas
4. Añadir Redis para caching (opcional)
5. Configurar backups en Neon

### Costos Estimados

- Render Backend: Free tier o $7+/mes
- Neon Database: Free tier o $15+/mes (pagado)
- OpenAI API: Pago por uso (~$0.02 por 1K queries)
- OpenRouter: Pago por uso (~$0.001 por query)

**Total estimado MVP:** $22+/mes (backend + database)

## Paso 11: Configuración Recomendada para Producción

```python
# backend/app/main.py - Producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://euroleague-ai-frontend.onrender.com",
        "https://api.tudominio.com",  # si tienes dominio propio
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Logging mejorado
logging.basicConfig(level=logging.INFO)
```

## Integración Frontend-Backend

### Paso Final: Actualizar Frontend

En `frontend`, actualizar la variable de entorno:

```
NEXT_PUBLIC_API_URL=https://euroleague-ai-backend.onrender.com
```

El frontend automáticamente enviará requests a esta URL.

## Checklist de Verificación Final

- [ ] Base de datos Neon creada y accesible
- [ ] Variables de entorno configuradas en Render
- [ ] Backend build exitosamente sin errores
- [ ] Health check funciona (`GET /health`)
- [ ] Documentación accesible (`GET /docs`)
- [ ] Conexión a base de datos confirmada
- [ ] API keys configuradas (OpenAI, OpenRouter)
- [ ] CORS configurado correctamente
- [ ] Frontend puede conectarse y enviar queries
- [ ] Respuestas JSON correctas
- [ ] Documentación actualizada

## Referencias

- Render Docs: https://render.com/docs
- Neon Docs: https://neon.tech/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Poetry Guide: https://python-poetry.org/docs/
- Uvicorn Guide: https://www.uvicorn.org/deployment/

## Soporte

Para problemas específicos:
1. Revisar logs en Render Dashboard
2. Revisar docs de Neon para issues de DB
3. Consultar FastAPI + SQLAlchemy documentation
4. Contactar con equipo DevOps

---

**Última actualización:** 2025-12-08
**Responsable:** DevOps Team
**Estado:** Production Ready ✓

