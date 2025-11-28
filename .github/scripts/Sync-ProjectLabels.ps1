<#
.SYNOPSIS
    Sincroniza y valida todas las etiquetas definidas en project_labels.json con GitHub.
    Se ejecuta automáticamente cuando se crea project_labels.json por primera vez, o manualmente cuando se solicita.
    
.DESCRIPTION
    Este script:
    1. Lee .github/docs/project_labels.json (o lo crea si no existe)
    2. Valida que todas las etiquetas necesarias estén definidas
    3. Crea o actualiza etiquetas en GitHub (usando "gh label create --force")
    4. Reporta el estado
    
.NOTES
    Dependencias: GitHub CLI (gh) debe estar instalado y autenticado
#>

param(
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
$projectLabelsPath = ".github/docs/project_labels.json"
$repoRoot = git rev-parse --show-toplevel 2>$null || Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "`n[Sincronizando Etiquetas de Proyecto]" -ForegroundColor Cyan

# ============================================================================
# PASO 1: VALIDAR/CREAR project_labels.json
# ============================================================================
if (Test-Path $projectLabelsPath) {
    Write-Host "✓ Fichero encontrado: $projectLabelsPath" -ForegroundColor Green
    $labelsConfig = Get-Content $projectLabelsPath | ConvertFrom-Json
} else {
    Write-Host "✗ Fichero NO encontrado: $projectLabelsPath" -ForegroundColor Yellow
    Write-Host "  Creando fichero con configuración por defecto..." -ForegroundColor Yellow
    
    # Crear estructura por defecto basada en labels_convention.md
    $defaultConfig = @{
        version = "1.0"
        generated = (Get-Date -Format "yyyy-MM-dd")
        description = "Configuración centralizada de todas las etiquetas del proyecto. Basado en .github/docs/labels_convention.md"
        source_of_truth = ".github/docs/labels_convention.md"
        categories = @{
            "1_task_type" = @{
                section = "Tipo de Tarea"
                description = "Define la naturaleza del trabajo. Cada issue/PR debe tener máximo una."
                max_per_issue = 1
                labels = @(
                    @{ name = "task"; color = "0366d6"; description = "Tarea de desarrollo estándar" }
                    @{ name = "bug"; color = "d73a49"; description = "Error o defecto a corregir" }
                    @{ name = "documentation"; color = "0075ca"; description = "Documentación o actualización de docs" }
                    @{ name = "question"; color = "d876e3"; description = "Pregunta o investigación" }
                    @{ name = "enhancement"; color = "a2eeef"; description = "Mejora o feature solicitada" }
                )
            }
            "2_technology" = @{
                section = "Tecnología / Componente"
                description = "Especifica el área del proyecto. Cada issue/PR debe tener máximo una."
                max_per_issue = 1
                labels = @(
                    @{ name = "backend"; color = "f9826c"; description = "Backend, API, servicios" }
                    @{ name = "frontend"; color = "a2eeef"; description = "Frontend, UI, cliente" }
                    @{ name = "database"; color = "ffc274"; description = "Base de datos, esquema, queries" }
                    @{ name = "devops"; color = "cccccc"; description = "CI/CD, infraestructura, scripts" }
                    @{ name = "testing"; color = "c5def5"; description = "Tests, QA, validación" }
                )
            }
            "3_priority_status" = @{
                section = "Estado / Prioridad"
                description = "Clasifica urgencia o estado del trabajo."
                max_per_issue = $null
                labels = @(
                    @{ name = "priority-high"; color = "d73a49"; description = "Alta prioridad" }
                    @{ name = "priority-medium"; color = "ffc274"; description = "Prioridad media" }
                    @{ name = "priority-low"; color = "c5def5"; description = "Baja prioridad" }
                    @{ name = "blocked"; color = "cccccc"; description = "Bloqueado por otra tarea" }
                    @{ name = "in-progress"; color = "f9826c"; description = "Trabajo en curso" }
                    @{ name = "review"; color = "0075ca"; description = "En revisión" }
                )
            }
            "4_github_standard" = @{
                section = "Otras Etiquetas Estándar de GitHub"
                description = "Etiquetas convencionales que GitHub sugiere."
                max_per_issue = $null
                labels = @(
                    @{ name = "good first issue"; color = "7057ff"; description = "Buena para nuevos contributores" }
                    @{ name = "help wanted"; color = "008672"; description = "Se busca ayuda" }
                    @{ name = "duplicate"; color = "cfd3d7"; description = "Duplicado de otro issue" }
                    @{ name = "wontfix"; color = "ffffff"; description = "No será solucionado" }
                    @{ name = "invalid"; color = "e4e669"; description = "No válido o incompleto" }
                )
            }
            "5_project_phases" = @{
                section = "Fases del Proyecto"
                description = "Categorizar issues por fase del roadmap (generado automáticamente desde docs/roadmap.md)"
                max_per_issue = 1
                labels = @(
                    @{ name = "fase-1"; color = "7057ff"; description = "Fase 1: Data & ETL" }
                    @{ name = "fase-2"; color = "7057ff"; description = "Fase 2: Backend & AI Engine" }
                    @{ name = "fase-3"; color = "7057ff"; description = "Fase 3: Frontend & Integration" }
                    @{ name = "fase-4"; color = "7057ff"; description = "Fase 4: Optimization & Deployment" }
                )
            }
        }
        pautas = @{
            para_issues = @(
                "Cada issue debe tener al menos una etiqueta de 'Tipo de Tarea'",
                "Cada issue debe tener opcionalmente una etiqueta de 'Tecnología'",
                "Permitir máximo una por categoría"
            )
            para_pull_requests = @(
                "Si el PR cierra un issue, heredar sus labels",
                "Si no hay issue, asignar labels siguiendo la misma estructura",
                "Agregar estado: usar 'in-progress', 'review' según sea necesario"
            )
            naming_convention = "kebab-case (minúsculas con guiones)"
            color_consistency = "Los mismos tipos siempre usan el mismo color"
        }
        validacion = @{
            automatica = $true
            script = ".github/scripts/Sync-ProjectLabels.ps1"
            frecuencia = "Ejecutar cuando se crea project_labels.json por primera vez o cuando el usuario lo solicite"
        }
    }
    
    # Guardar el fichero
    $defaultConfig | ConvertTo-Json -Depth 10 | Set-Content $projectLabelsPath -Encoding UTF8
    Write-Host "✓ Fichero creado en: $projectLabelsPath" -ForegroundColor Green
    $labelsConfig = $defaultConfig
}

# ============================================================================
# PASO 2: VERIFICAR QUE gh CLI ESTÉ DISPONIBLE
# ============================================================================
Write-Host "`n[Verificando dependencias...]" -ForegroundColor Cyan
$ghAvailable = gh --version 2>$null
if (-not $ghAvailable) {
    Write-Host "✗ GitHub CLI (gh) no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "  Descárgalo desde: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ GitHub CLI disponible" -ForegroundColor Green

# ============================================================================
# PASO 3: RECOLECTAR TODAS LAS ETIQUETAS
# ============================================================================
Write-Host "`n[Recolectando etiquetas definidas...]" -ForegroundColor Cyan

$allLabels = @()
$categoryCount = 0
$labelCount = 0

foreach ($categoryName in $labelsConfig.categories.PSObject.Properties.Name) {
    $category = $labelsConfig.categories.$categoryName
    $categoryCount++
    
    foreach ($label in $category.labels) {
        $allLabels += $label
        $labelCount++
        
        if ($Verbose) {
            Write-Host "  - $($label.name) ($($label.color))" -ForegroundColor Gray
        }
    }
}

Write-Host "✓ Total: $categoryCount categorías, $labelCount etiquetas" -ForegroundColor Green

# ============================================================================
# PASO 4: SINCRONIZAR CON GITHUB (o mostrar en DryRun)
# ============================================================================
Write-Host "`n[Sincronizando etiquetas con GitHub...]" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "(Modo DRY-RUN: No se crearán etiquetas)" -ForegroundColor Yellow
}

$successCount = 0
$errorCount = 0

foreach ($label in $allLabels) {
    $displayName = $label.name
    
    if ($DryRun) {
        Write-Host "  [DRY] Crear/actualizar: $displayName" -ForegroundColor Gray
    } else {
        $result = gh label create $label.name `
            --color $label.color `
            --description $label.description `
            --force 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $displayName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✗ $displayName - ERROR: $result" -ForegroundColor Red
            $errorCount++
        }
    }
    
    Start-Sleep -Milliseconds 100
}

# ============================================================================
# REPORTE FINAL
# ============================================================================
Write-Host "`n[Resumen de Sincronización]" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "  Modo: DRY-RUN (sin cambios)" -ForegroundColor Yellow
    Write-Host "  Etiquetas a crear/actualizar: $labelCount" -ForegroundColor Cyan
} else {
    Write-Host "  Etiquetas sincronizadas: $successCount" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "  Errores: $errorCount" -ForegroundColor Red
    }
}

Write-Host "  Archivo de configuración: $projectLabelsPath" -ForegroundColor Gray

Write-Host "`n[Sincronización completada]" -ForegroundColor Cyan

if (-not $DryRun -and $errorCount -gt 0) {
    exit 1
}

