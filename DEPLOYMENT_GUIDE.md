# Guía de Deployment Completo en Render - Backend + Frontend

## Descripción General

Esta es la guía maestro para deployar completamente Euroleague AI Stats en Render con:
- Backend FastAPI + PostgreSQL (Neon)
- Frontend Next.js

## Flujo General

```
1. Preparar Base de Datos (Neon)
    ↓
2. Deploy Backend (Render)
    ↓
3. Deploy Frontend (Render)
    ↓
4. Integración y Verificación
```

## Fase 1: Base de Datos (Neon)

Ver: [backend/DEPLOYMENT_RENDER.md](./backend/DEPLOYMENT_RENDER.md) - Paso 1

**Tareas:**
1. Crear proyecto en Neon
2. Obtener connection string (DATABASE_URL)
3. Inicializar schema (optional)

**Duración:** 5-10 minutos

## Fase 2: Deploy Backend

Ver: [backend/DEPLOYMENT_RENDER.md](./backend/DEPLOYMENT_RENDER.md)

**Tareas:**
1. Conectar repositorio GitHub a Render
2. Crear Web Service para backend
3. Configurar variables de entorno
4. Verificar que funciona

**Variables de Entorno Necesarias:**
```
DATABASE_URL              # Desde Neon
OPENAI_API_KEY           # Desde OpenAI
OPENROUTER_API_KEY       # Desde OpenRouter
ENVIRONMENT              # production
LOG_LEVEL               # INFO
```

**Verificación:**
```bash
curl https://euroleague-ai-backend.onrender.com/health
# Esperado: 200 OK
```

**Duración:** 10-15 minutos (incluyendo deploy)

## Fase 3: Deploy Frontend

Ver: [frontend/DEPLOYMENT_RENDER.md](./frontend/DEPLOYMENT_RENDER.md)

**Tareas:**
1. Crear Web Service para frontend
2. Configurar variable de entorno
3. Verificar que funciona

**Variables de Entorno Necesarias:**
```
NEXT_PUBLIC_API_URL      # https://euroleague-ai-backend.onrender.com
NODE_ENV                 # production
```

**Verificación:**
1. Abrir https://euroleague-ai-frontend.onrender.com
2. Verificar que UI carga
3. Verificar que no hay errores de consola

**Duración:** 5-10 minutos (incluyendo build)

## Fase 4: Integración Completa

### 4.1 Verificar CORS

El backend debe permitir solicitudes del frontend:

**Archivo:** `backend/app/main.py`
```python
allow_origins=[
    "https://euroleague-ai-frontend.onrender.com",
]
```

### 4.2 Test End-to-End

1. Abrir frontend en navegador
2. Escribir pregunta: "¿Cuántos jugadores hay?"
3. Esperar respuesta
4. Verificar que datos se renderizan

**Logs para debugging:**
- Frontend: Abrir DevTools (F12) → Network tab
- Backend: Render Dashboard → Web Service → Logs

## Paso a Paso: Guía Rápida

### 1. Preparar Neon (5 min)

```bash
# Ir a https://console.neon.tech
# 1. Create Project: euroleague-ai
# 2. Copy Connection String
# Guardar para usarlo en Backend
```

### 2. Deploy Backend (10 min)

```bash
# Render Dashboard:
# 1. New Web Service
# 2. GitHub: euroleague-stats-ai
# 3. Root Directory: backend
# 4. Build: pip install -r requirements.txt
# 5. Start: uvicorn app.main:app --host 0.0.0.0 --port 8000
# 6. Environment:
#    - DATABASE_URL: <desde Neon>
#    - OPENAI_API_KEY: <tu key>
#    - OPENROUTER_API_KEY: <tu key>
# 7. Create Web Service
```

### 3. Deploy Frontend (5 min)

```bash
# Render Dashboard:
# 1. New Web Service
# 2. GitHub: euroleague-stats-ai
# 3. Root Directory: frontend
# 4. Build: npm run build
# 5. Start: npm start
# 6. Environment:
#    - NEXT_PUBLIC_API_URL: https://euroleague-ai-backend.onrender.com
# 7. Create Web Service
```

### 4. Actualizar CORS (1 min)

```bash
# Actualizar backend/app/main.py:
# Cambiar allow_origins con URL del frontend
# Hacer commit y push
# Render automáticamente re-deployará
```

### 5. Verificación Final (5 min)

```bash
# Abrir frontend en navegador
# Hacer pregunta
# Verificar que funciona end-to-end
```

**Tiempo Total:** ~40 minutos

## URLs Finales

Después del deployment, tendrás:

```
Frontend:   https://euroleague-ai-frontend.onrender.com
Backend:    https://euroleague-ai-backend.onrender.com
Docs:       https://euroleague-ai-backend.onrender.com/docs
Database:   Neon Console (https://console.neon.tech)
```

## Troubleshooting Común

### Frontend no se conecta a Backend

**Síntoma:** Error "Failed to fetch" en DevTools

**Solución:**
1. Verificar `NEXT_PUBLIC_API_URL` en frontend
2. Verificar que backend está activo
3. Verificar CORS en `backend/app/main.py`
4. Limpiar cache del navegador (Ctrl+Shift+Del)

### Backend no inicia

**Síntoma:** "Service can't find module" o crash

**Solución:**
1. Revisar logs en Render Dashboard
2. Verificar `pyproject.toml` o `requirements.txt`
3. Ejecutar localmente: `poetry install && poetry run uvicorn ...`
4. Hacer commit de fixes y hacer push

### Base de datos no accesible

**Síntoma:** "Database connection failed"

**Solución:**
1. Verificar `DATABASE_URL` exacto en Neon
2. Copiar completo (incluyendo password)
3. Verificar que Neon proyecto está activo
4. Ejecutar localmente: `psql $DATABASE_URL`

### Datos no persisten

**Síntoma:** Escribir preguntas pero no aparecen en historial

**Solución:**
1. Verificar localStorage en navegador (DevTools → Application)
2. Verificar que API regresa respuestas correctas
3. Verificar Zustand store (DevTools → Redux/Zustand extension)

## Monitoreo Después del Deploy

### Daily Checks

- ✓ Health endpoint responde
- ✓ Frontend carga sin errores
- ✓ Chat funciona end-to-end
- ✓ No hay errores en logs

### Weekly Checks

- ✓ Rendimiento de queries (< 5 segundos)
- ✓ Uso de CPU/Memory en Render
- ✓ Errores recurrentes en logs
- ✓ Rate limits de APIs externas

### Monthly Checks

- ✓ Actualizar documentación
- ✓ Revisar costos en Render + Neon
- ✓ Backup de base de datos en Neon
- ✓ Actualizar dependencias si es necesario

## Escalabilidad Futura

### Si tienes tráfico creciente:

1. **Backend:** Cambiar a plan Starter/Pro en Render
2. **Database:** Cambiar a Neon paid plan
3. **Caching:** Añadir Redis
4. **CDN:** Cloudflare o Render CDN

## Documentos Relacionados

- [frontend/DEPLOYMENT_RENDER.md](./frontend/DEPLOYMENT_RENDER.md) - Guía detallada frontend
- [backend/DEPLOYMENT_RENDER.md](./backend/DEPLOYMENT_RENDER.md) - Guía detallada backend
- [RENDER_QUICKSTART.md](./RENDER_QUICKSTART.md) - Guía rápida para iniciados
- [frontend/README.md](./frontend/README.md) - Setup local frontend
- [backend/README.md](./backend/README.md) - Setup local backend

## Contacto y Soporte

Para dudas específicas:
- Render Support: https://render.com/support
- Neon Support: https://neon.tech/support
- FastAPI Docs: https://fastapi.tiangolo.com
- Next.js Docs: https://nextjs.org/docs

---

**Última actualización:** 2025-12-08
**Guía versión:** 1.0
**Estado:** Production Ready ✓

**Requisitos:**
- [ ] Cuenta Render activa
- [ ] Cuenta Neon activa
- [ ] Repositorio GitHub conectado
- [ ] API keys (OpenAI, OpenRouter)
- [ ] 40 minutos de tiempo

**¡Listo para deployar!**

