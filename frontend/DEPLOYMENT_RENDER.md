# Deployment en Render - Frontend Next.js

## Descripción General

Este documento describe el proceso para deployar el frontend Next.js 14 de Euroleague AI Stats en Render (https://render.com). Render es una plataforma PaaS moderna que proporciona hosting gratuito con soporte para aplicaciones Node.js.

## Requisitos Previos

- Cuenta en Render (https://render.com)
- Repositorio GitHub conectado a Render
- Backend deployado en Render (obtener `BACKEND_API_URL`)
- Variables de entorno configuradas

## Arquitectura de Deployment

```
GitHub Repository
    ↓
Render Dashboard
    ↓
Next.js Build
    ↓
Node.js Runtime
    ↓
Production Server
```

## Paso 1: Preparación en GitHub

### 1.1 Verificar que `render.yaml` existe

El archivo `render.yaml` debe estar en la raíz del repositorio:

```yaml
services:
  - type: web
    name: euroleague-ai-frontend
    runtime: node
    plan: free
    buildCommand: npm run build
    startCommand: npm start
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: ${BACKEND_API_URL}
```

### 1.2 Confirmar que `package.json` tiene los scripts necesarios

```json
{
  "scripts": {
    "build": "next build",
    "start": "next start"
  }
}
```

## Paso 2: Conectar Repositorio a Render

1. **Ingresar a Render Dashboard:** https://dashboard.render.com
2. **Hacer clic en "New +"** en la esquina superior derecha
3. **Seleccionar "Web Service"**
4. **Conectar GitHub:**
   - Si es primera vez, autorizar Render en GitHub
   - Seleccionar el repositorio `euroleague-stats-ai`
5. **Configurar el servicio:**
   - **Name:** `euroleague-ai-frontend`
   - **Root Directory:** `frontend` (IMPORTANTE: especificar que el código está en `frontend/`)
   - **Runtime:** Node
   - **Build Command:** `npm run build`
   - **Start Command:** `npm start`

## Paso 3: Configurar Variables de Entorno

### 3.1 En el Dashboard de Render

1. En el formulario de creación del Web Service, ir a la sección **"Environment"**
2. Añadir las siguientes variables:

| Variable | Valor | Scope | Descripción |
|----------|-------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend-api.onrender.com` | Run | URL del backend deployado en Render |
| `NODE_ENV` | `production` | Run | Ambiente de ejecución |

### 3.2 NEXT_PUBLIC_API_URL

**CRÍTICO:** Esta variable debe comenzar con `NEXT_PUBLIC_` para que sea accesible desde el navegador.

Obtener el valor:
- Si el backend está en Render, acceder al dashboard del backend
- Copiar la URL del servicio (ej: `https://euroleague-ai-backend.onrender.com`)
- Asegurarse de que la API está accesible en esa URL

### 3.3 Verificación de Variables

Después de deployar, verificar en Render Dashboard → Web Service → Environment que todas las variables están configuradas.

## Paso 4: Deploy Automático

### 4.1 Rama de Deploy

Por defecto, Render deployará automáticamente cada cambio que se haga push a la rama `main`.

Para cambiar esto:
1. En el Dashboard del Web Service → Settings
2. Buscar **"Deploy on push"**
3. Cambiar rama si es necesario

### 4.2 Observar el Deploy

1. En el Dashboard del Web Service, ir a **"Deploys"**
2. Ver el progreso del build en tiempo real
3. Los logs mostrarán:
   - `npm install` (descargando dependencias)
   - `npm run build` (compilando Next.js)
   - Inicio del servidor Node

**Tiempo esperado:** 3-5 minutos para el primer deploy (including npm install).

## Paso 5: Verificación Post-Deploy

### 5.1 Acceder al Sitio

1. En el Dashboard, copiar la URL del Web Service (ej: `https://euroleague-ai-frontend.onrender.com`)
2. Abrir en navegador
3. Verificar que:
   - La interfaz de chat carga correctamente
   - No hay errores en la consola del navegador (F12)
   - El logo y estilos (Tailwind) se aplican correctamente

### 5.2 Verificar Conexión con Backend

En el navegador:
1. Abrir Developer Tools (F12)
2. Ir a la pestaña "Network"
3. Escribir una pregunta en el chat
4. Observar que la solicitud se envía a `NEXT_PUBLIC_API_URL`
5. Verificar que la respuesta regresa exitosamente (Status 200)

### 5.3 Test de Funcionalidad Completa

Realizar las siguientes pruebas:

```
1. Chat Message Submission
   - Escribir pregunta: "¿Cuántos jugadores hay?"
   - Resultado esperado: Respuesta con datos y visualización
   - Tiempo esperado: < 5 segundos

2. History Persistence
   - Hacer refresh en la página
   - Verificar que el historial de chat persiste
   
3. Visualizaciones
   - Si la respuesta incluye gráficos, verificar que se renderizan correctamente
   - Probar con distintos tipos de datos (tabla, gráfico de barras, línea)
```

## Paso 6: Solución de Problemas

### Error: "NEXT_PUBLIC_API_URL is not defined"

**Causa:** Variable de entorno no configurada correctamente.

**Solución:**
1. Verificar que la variable se llama exactamente `NEXT_PUBLIC_API_URL`
2. Re-deployar desde el Dashboard (botón "Deploy" o hacer push a main)
3. Limpiar navegador (Ctrl+Shift+Delete)

### Error: "Failed to fetch from API"

**Causa:** Backend no está accesible o URL es incorrecta.

**Solución:**
1. Verificar que `NEXT_PUBLIC_API_URL` es accesible: abrir en navegador directamente
2. Verificar que el backend está deployado y activo en Render
3. Verificar que no hay CORS issues (revisar consola del navegador)
4. Si es necesario, contactar con el equipo de backend

### Error: "Build failed: npm ERR!"

**Causa:** Problemas con dependencias o comandos de build.

**Solución:**
1. Revisar los logs del deploy en Render Dashboard → Deploys → Ver logs
2. Asegurarse de que `npm install` puede ejecutarse (verificar `package-lock.json`)
3. Si es necesario, ejecutar localmente `npm install; npm run build` para reproducir
4. Hacer commit de los cambios y hacer push

### Sitio muy lento en primer acceso (> 5 segundos)

**Causa:** Render free tier tiene "spin down" - inactividad por 15 minutos causa apagado.

**Solución:**
- Este es comportamiento esperado en free tier
- Primer acceso puede tardar 30-60 segundos (inicializando servidor)
- Accesos subsecuentes serán rápidos
- Para evitar esto, usar plan pagado

## Paso 7: Monitoreo Continuo

### 7.1 Logs

1. Dashboard → Web Service → Logs
2. Ver logs en tiempo real de:
   - Solicitudes HTTP
   - Errores de aplicación
   - Rendimiento

### 7.2 Métricas

1. Dashboard → Web Service → Metrics
2. Monitorear:
   - CPU usage
   - Memory usage
   - Response times

### 7.3 Alertas

Render permite configurar alertas para:
- Deploy failures
- High CPU/Memory usage
- Service downtime

## Paso 8: Actualizaciones y Re-deployment

### 8.1 Actualizar Frontend

1. Hacer cambios en la rama `frontend/`
2. Hacer commit:
   ```bash
   git add frontend/
   git commit -m "feat: frontend improvements"
   ```
3. Hacer push a `main`:
   ```bash
   git push origin main
   ```
4. Render automáticamente triggerá un nuevo deploy

### 8.2 Forzar Re-deployment

Si es necesario forzar un re-deployment sin cambios de código:
1. Dashboard → Web Service → Settings
2. Hacer click en "Manual Deploy" / "Re-deploy"
3. Seleccionar rama (usualmente `main`)

## Configuración Alternativa: Deploy Manual desde CLI

Para usuarios avanzados, Render también soporta deploy manual:

```bash
# Instalar Render CLI (opcional)
npm install -g @render/cli

# Hacer login
render login

# Deploy
render deploy --name euroleague-ai-frontend
```

## Paso 9: Dominio Personalizado (Opcional)

Para usar un dominio propio (ej: `ai.euroleague-stats.com`):

1. Dashboard → Web Service → Settings
2. Buscar "Custom Domain"
3. Añadir dominio
4. Seguir instrucciones de DNS en tu registrador de dominios

## Checklist de Verificación Final

- [ ] `render.yaml` configurado correctamente
- [ ] Variables de entorno configuradas en Render Dashboard
- [ ] `NEXT_PUBLIC_API_URL` apunta al backend correcto
- [ ] Build completado exitosamente (sin errores)
- [ ] Frontend accesible en URL de Render
- [ ] Chat funciona y se conecta al backend
- [ ] Historial persiste después de refresh
- [ ] Visualizaciones se renderizan correctamente
- [ ] No hay errores en DevTools Console
- [ ] Documentación actualizada en README

## Referencias

- Render Docs: https://render.com/docs
- Next.js Deployment: https://nextjs.org/docs/deployment
- Render Node.js Guide: https://render.com/docs/deploy-node-express-app
- Render Free Tier Limits: https://render.com/pricing

## Soporte y Escalabilidad

### Free Tier Limitations

- Plan free: 0.5 CPU, 512MB RAM
- Auto-scales, pero puede tener latencia
- "Spin down" después de 15 minutos de inactividad

### Escalabilidad a Producción

Para escalar a producción:
1. Cambiar plan de Free a Starter o Pro
2. Configurar más instancias
3. Añadir CDN para assets estáticos
4. Configurar backups automáticos

### Costos Estimados

- Free Tier: $0/mes (limitado)
- Starter Plan: $7/mes por servicio
- Pro Plan: $12/mes por servicio

---

**Última actualización:** 2025-12-08
**Responsable:** DevOps Team
**Estado:** Ready for Production ✓

