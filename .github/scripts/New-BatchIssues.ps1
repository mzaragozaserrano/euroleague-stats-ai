<#
.SYNOPSIS
    Crea issues en GitHub en lote basándose en una lista definida.
    Este script es modificado automáticamente por el Agente de Cursor antes de su ejecución.
    
.NOTES
    Sintaxis recomendada para títulos y bodies:
    - Usa Here-String (@"..."@) para facilitar la lectura
    - Puedes escribir tildes y acentos directamente
    - Consulta .github/docs/windows_utf8_setup.md para más detalles
#>

# 1. CARGA LA CONFIGURACIÓN UTF-8
# $PSScriptRoot es la carpeta donde está este script.
# Si el fichero Enable-Utf8.ps1 no existe, ignoramos el error para no romper nada.
if (Test-Path "$PSScriptRoot/Enable-Utf8.ps1") {
    . "$PSScriptRoot/Enable-Utf8.ps1"
}

# --- ZONA EDITABLE POR EL AGENTE ---
# El agente rellenará este array basándose en el Roadmap.
# IMPORTANTE AGENTE: 
# 1. Usa Here-String (@"..."@) para títulos y bodies
# 2. Puedes escribir tildes directamente: ñ, á, é, í, ó, ú
# 3. Consulta .github/docs/labels_convention.md para asignar labels correctamente.
#    Formato: "tipo,tecnologia,fase-X" (ej: "task,backend,fase-2")
$issues = @(
    @{ 
        Title = @"
3.1 Chat Interface - Store & State Management
"@
        Body = @"
## Objetivo
Implementar Zustand store para gestionar el estado del chat (mensajes, historial, estados de carga).

## Tareas
- [ ] Instalar Zustand: `npm install zustand`
- [ ] Crear store `frontend/stores/chatStore.ts` con:
  - Estado: `messages[]`, `isLoading`, `error`
  - Acciones: `addMessage()`, `setLoading()`, `clearError()`
- [ ] Integrar con localStorage para persistencia del historial
- [ ] Manejar estados de carga (cold start, rate limits)

## Criterios de Aceptación
- Store funcional con TypeScript
- Persistencia en localStorage funcionando
- Estados de carga manejados correctamente

## Referencias
- Backend endpoint: `POST /api/chat`
- Documentación: `docs/architecture.md`
"@
        Labels = "task,frontend,fase-3" 
    },
    @{ 
        Title = @"
3.2 Chat Interface - UI Components
"@
        Body = @"
## Objetivo
Crear componentes UI del chat usando shadcn/ui siguiendo diseño mobile-first.

## Tareas
- [ ] Crear componente `ChatInput` con shadcn/ui Input
- [ ] Crear componente `MessageList` para mostrar historial
- [ ] Crear componente `MessageBubble` (usuario/assistant)
- [ ] Implementar layout vertical mobile-first
- [ ] Agregar estados visuales (loading, error, empty)
- [ ] Integrar con chatStore

## Criterios de Aceptación
- UI responsive y mobile-first
- Componentes accesibles y con buen UX
- Integración completa con store

## Referencias
- Componentes shadcn/ui disponibles en `frontend/components/ui/`
- Diseño: `docs/project_brief.md`
"@
        Labels = "task,frontend,fase-3" 
    },
    @{ 
        Title = @"
3.3 Data Visualizer - Recharts Integration
"@
        Body = @"
## Objetivo
Implementar visualizaciones dinámicas (Bar Chart, Line Chart, Table) usando Recharts según el tipo de respuesta del backend.

## Tareas
- [ ] Instalar Recharts: `npm install recharts`
- [ ] Crear componente `DataVisualizer` que reciba `{ data, visualization }`
- [ ] Implementar `BarChart` para visualización tipo 'bar'
- [ ] Implementar `LineChart` para visualización tipo 'line'
- [ ] Implementar `DataTable` para visualización tipo 'table'
- [ ] Manejar casos edge (datos vacíos, errores)

## Criterios de Aceptación
- Los 3 tipos de visualización funcionando
- Responsive y mobile-friendly
- Integración con respuesta del backend

## Referencias
- Backend response format: `{ sql, data, visualization }`
- Recharts docs: https://recharts.org/
"@
        Labels = "task,frontend,fase-3" 
    },
    @{ 
        Title = @"
3.4 Frontend - API Integration
"@
        Body = @"
## Objetivo
Conectar el frontend con el endpoint `/api/chat` del backend, manejando errores y estados de carga.

## Tareas
- [ ] Crear servicio `frontend/lib/api.ts` con función `sendChatMessage()`
- [ ] Configurar URL del backend (env variable `NEXT_PUBLIC_API_URL`)
- [ ] Integrar con chatStore para enviar mensajes
- [ ] Manejar respuestas del backend (`{ sql, data, visualization, error? }`)
- [ ] Implementar manejo de errores (timeout, rate limits, LLM errors)
- [ ] Agregar mensajes de estado ("Despertando al Agente...", etc.)

## Criterios de Aceptación
- Comunicación exitosa con backend
- Manejo robusto de errores
- Estados de carga informativos para el usuario

## Referencias
- Backend endpoint: `POST /api/chat` (ver `backend/app/routers/chat.py`)
- Error handling: Backend siempre retorna 200 con campo `error` si falla
"@
        Labels = "task,frontend,fase-3" 
    },
    @{ 
        Title = @"
3.5 Frontend - Persistence & UX Enhancements
"@
        Body = @"
## Objetivo
Mejorar la experiencia de usuario con persistencia robusta y mejoras de UX.

## Tareas
- [ ] Implementar persistencia de historial en localStorage (sobrevive tab discarding)
- [ ] Agregar funcionalidad de limpiar historial
- [ ] Manejar estados de carga con mensajes informativos
- [ ] Implementar manejo de rate limits (mostrar advertencia UI)
- [ ] Agregar indicadores visuales de estado (cold start >3s)
- [ ] Optimizar rendimiento (debounce en input, etc.)

## Criterios de Aceptación
- Historial persiste correctamente
- UX fluida y sin bloqueos
- Mensajes informativos para el usuario

## Referencias
- UX requirements: `docs/project_brief.md`
- Latencies: Cold start >3s, rate limits 50 req/day
"@
        Labels = "task,frontend,fase-3" 
    },
    @{ 
        Title = @"
3.6 Deployment - Render Setup
"@
        Body = @"
## Objetivo
Configurar deployment del frontend Next.js en Render.

## Tareas
- [ ] Crear `render.yaml` o configurar servicio en Render dashboard
- [ ] Configurar variables de entorno (`NEXT_PUBLIC_API_URL`)
- [ ] Configurar build command: `npm run build`
- [ ] Configurar start command: `npm start`
- [ ] Verificar deployment exitoso
- [ ] Documentar proceso de deployment

## Criterios de Aceptación
- Frontend desplegado y accesible
- Variables de entorno configuradas correctamente
- Documentación actualizada

## Referencias
- Render docs: https://render.com/docs
- Next.js deployment: https://nextjs.org/docs/deployment
"@
        Labels = "task,devops,fase-3" 
    }
)
# -----------------------------------

Write-Host "`n[Iniciando creación de lote de issues...]" -ForegroundColor Cyan

# Verificación de seguridad básica
if ($issues.Count -eq 0) {
    Write-Warning "La lista de issues está vacía. No hay nada que crear."
    exit
}

foreach ($issue in $issues) {
    # Mostramos en pantalla el título
    Write-Host "Creando: $($issue.Title)..." -NoNewline
    
    # Ejecutamos el comando de GitHub CLI
    $result = gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host $result -ForegroundColor Yellow
    }
    
    # Pequeña pausa de 500ms
    Start-Sleep -Milliseconds 500 
}

Write-Host "`n[Proceso finalizado.]" -ForegroundColor Cyan
