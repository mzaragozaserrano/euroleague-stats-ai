<#
.SYNOPSIS
    Crea todos los labels estándar en un repositorio de GitHub.
    Este script es agnóstico del proyecto y usa la convención de labels_convention.md
    
.DESCRIPTION
    Crea los labels estándar de GitHub basándose en:
    - Tipos de tarea: task, bug, documentation, question, enhancement
    - Tecnologías: backend, frontend, database, devops, testing
    - Estado/Prioridad: priority-high, priority-medium, priority-low, blocked, in-progress, review
    - Estándares GitHub: good first issue, help wanted, duplicate, wontfix, invalid
    
.NOTES
    Requiere gh CLI autenticado: gh auth login
    
.EXAMPLE
    powershell -File .github/scripts/Setup-StandardLabels.ps1
#>

# 1. CARGA LA CONFIGURACIÓN UTF-8
if (Test-Path "$PSScriptRoot/Enable-Utf8.ps1") {
    . "$PSScriptRoot/Enable-Utf8.ps1"
}

Write-Host "`n[Creando labels estándar...]" -ForegroundColor Cyan

# Definir todos los labels estándar
$standardLabels = @(
    # === TIPO DE TAREA ===
    @{ 
        name = "task"
        color = "0366d6"
        description = "Tarea de desarrollo estándar"
    }
    @{ 
        name = "bug"
        color = "d73a49"
        description = "Error o defecto a corregir"
    }
    @{ 
        name = "documentation"
        color = "0075ca"
        description = "Documentación o actualización de docs"
    }
    @{ 
        name = "question"
        color = "d876e3"
        description = "Pregunta o investigación"
    }
    @{ 
        name = "enhancement"
        color = "a2eeef"
        description = "Mejora o feature solicitada"
    }
    
    # === TECNOLOGÍA / COMPONENTE ===
    @{ 
        name = "backend"
        color = "f9826c"
        description = "Backend, API, servicios"
    }
    @{ 
        name = "frontend"
        color = "a2eeef"
        description = "Frontend, UI, cliente"
    }
    @{ 
        name = "database"
        color = "ffc274"
        description = "Base de datos, esquema, queries"
    }
    @{ 
        name = "devops"
        color = "cccccc"
        description = "CI/CD, infraestructura, scripts"
    }
    @{ 
        name = "testing"
        color = "c5def5"
        description = "Tests, QA, validación"
    }
    
    # === ESTADO / PRIORIDAD ===
    @{ 
        name = "priority-high"
        color = "d73a49"
        description = "Alta prioridad"
    }
    @{ 
        name = "priority-medium"
        color = "ffc274"
        description = "Prioridad media"
    }
    @{ 
        name = "priority-low"
        color = "c5def5"
        description = "Baja prioridad"
    }
    @{ 
        name = "blocked"
        color = "cccccc"
        description = "Bloqueado por otra tarea"
    }
    @{ 
        name = "in-progress"
        color = "f9826c"
        description = "Trabajo en curso"
    }
    @{ 
        name = "review"
        color = "0075ca"
        description = "En revisión"
    }
    
    # === ESTÁNDAR GITHUB ===
    @{ 
        name = "good first issue"
        color = "7057ff"
        description = "Bueno para nuevos contributores"
    }
    @{ 
        name = "help wanted"
        color = "008672"
        description = "Se busca ayuda"
    }
    @{ 
        name = "duplicate"
        color = "cfd3d7"
        description = "Duplicado de otro issue"
    }
    @{ 
        name = "wontfix"
        color = "ffffff"
        description = "No será solucionado"
    }
    @{ 
        name = "invalid"
        color = "e4e669"
        description = "No válido o incompleto"
    }
)

# Crear cada label
$successCount = 0
$errorCount = 0

foreach ($label in $standardLabels) {
    Write-Host "Creando label: $($label.name)..." -NoNewline
    
    $result = gh label create $label.name `
        --color $label.color `
        --description $label.description `
        --force 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host "  $result" -ForegroundColor Yellow
        $errorCount++
    }
    
    Start-Sleep -Milliseconds 200
}

Write-Host "`n[Resumen]" -ForegroundColor Cyan
Write-Host "Exitosos: $successCount" -ForegroundColor Green
Write-Host "Errores: $errorCount" -ForegroundColor Yellow

if ($errorCount -eq 0) {
    Write-Host "`nTodos los labels estándar fueron creados correctamente." -ForegroundColor Green
} else {
    Write-Host "`nAlgunos labels ya existían o hubo errores. Esto es normal." -ForegroundColor Yellow
}

Write-Host "`nSiguientes pasos:" -ForegroundColor Cyan
Write-Host "1. Revisar .github/docs/labels_convention.md para entender los labels"
Write-Host "2. Si tu proyecto tiene labels específicos, revisar .github/docs/PROJECT_LABELS.md"
Write-Host "3. Asignar labels a tus issues/PRs según la convención"

