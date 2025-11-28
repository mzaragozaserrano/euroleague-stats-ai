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
$fileCreated = $false

if (Test-Path $projectLabelsPath) {
    Write-Host "✓ Fichero encontrado: $projectLabelsPath" -ForegroundColor Green
} else {
    Write-Host "✗ Fichero NO encontrado: $projectLabelsPath" -ForegroundColor Yellow
    Write-Host "  Intentando crear desde versión en repositorio..." -ForegroundColor Yellow
    
    # Intentar leer desde git si el archivo está versionado
    $gitContent = git show "HEAD:.github/docs/project_labels.json" 2>$null
    if ($gitContent) {
        $gitContent | Set-Content $projectLabelsPath -Encoding UTF8
        Write-Host "✓ Fichero creado desde versión en repositorio" -ForegroundColor Green
        $fileCreated = $true
    } else {
        Write-Host "✗ ERROR: El archivo no existe localmente ni en el repositorio" -ForegroundColor Red
        Write-Host "  Debes crear $projectLabelsPath manualmente basándote en labels_convention.md" -ForegroundColor Yellow
        Write-Host "  O ejecuta este script después de hacer commit del archivo project_labels.json" -ForegroundColor Yellow
        exit 1
    }
}

# SIEMPRE leer dinámicamente desde el archivo (ya sea recién creado o existente)
Write-Host "`n[Leyendo configuración desde $projectLabelsPath...]" -ForegroundColor Cyan
try {
    $labelsConfig = Get-Content $projectLabelsPath -Raw | ConvertFrom-Json
    Write-Host "✓ Configuración cargada exitosamente" -ForegroundColor Green
    
    if ($fileCreated) {
        Write-Host "  (Archivo creado por primera vez - se sincronizarán las etiquetas automáticamente)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "✗ ERROR: No se pudo parsear el JSON" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  Verifica que el archivo tenga un formato JSON válido" -ForegroundColor Yellow
    exit 1
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

