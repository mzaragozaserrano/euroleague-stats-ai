# Guía Rápida: Render Dashboard Setup

## 1. Conectar Repositorio

1. Ir a https://dashboard.render.com
2. Crear cuenta o ingresar
3. Hacer clic en "New +" → "Web Service"
4. Seleccionar "GitHub" como opción de conexión
5. Autorizar Render en GitHub si es primera vez
6. Seleccionar repositorio: `euroleague-stats-ai`

## 2. Configuración Básica del Servicio

| Campo | Valor |
|-------|-------|
| Name | `euroleague-ai-frontend` |
| Root Directory | `frontend` |
| Environment | Node |
| Region | Automático o preferencia personal |

## 3. Build & Start Commands

```
Build Command:  npm run build
Start Command:  npm start
```

## 4. Variables de Entorno

Después de ingresar las configuraciones básicas, hacer clic en "Advanced" y añadir:

```
NEXT_PUBLIC_API_URL = https://euroleague-ai-backend.onrender.com
NODE_ENV = production
```

**Nota:** Reemplazar `euroleague-ai-backend.onrender.com` con la URL real de tu servicio backend en Render.

## 5. Crear Web Service

- Hacer clic en "Create Web Service"
- Render comenzará el build automáticamente
- Esperar 3-5 minutos para que se complete

## 6. Monitoreo del Deploy

- Ver progreso en la pestaña "Deploys"
- Los logs mostrarán el progreso de npm install, build, etc.
- Cuando dice "Deployment live" el sitio está listo

## 7. Acceder al Sitio Deployado

- La URL estará disponible en el dashboard
- Formato: `https://euroleague-ai-frontend.onrender.com`
- Hacer clic en la URL para abrir

## 8. Troubleshooting Común

### Port Issues
Render automáticamente asigna puerto 3000 (Next.js default), no se requiere configuración.

### Cold Start
En free tier, el primer acceso puede tardar 30-60 segundos. Esto es normal.

### Build Failures
1. Revisar logs en "Deploys"
2. Buscar errores de npm o build
3. Ejecutar localmente `npm install && npm run build` para reproducir
4. Hacer commit de fixes y push a main

## 9. Auto-Deploy

Por defecto, cada push a `main` triggerará un nuevo deploy automáticamente. Para cambiar:
- Settings → Deploy on push → Seleccionar rama

## Referencias

- Documentación completa: [deployment-guide.md](./deployment-guide.md)
- Render Docs: https://render.com/docs
- Next.js Deployment: https://nextjs.org/docs/deployment

