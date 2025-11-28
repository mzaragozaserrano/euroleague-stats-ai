param([string]$IssueNumber)

if (-not $IssueNumber) {
    Write-Error "Debes proporcionar un número de Issue."
    exit 1
}

# 1. Configurar UTF-8
$utf8NoBom = . "$PSScriptRoot\Enable-Utf8.ps1"

# 2. Obtener datos de GitHub
Write-Host "Descargando contexto de Issue #$IssueNumber..." -ForegroundColor Cyan
try {
    $issueJson = gh issue view $IssueNumber --json number,title,body | ConvertFrom-Json
} catch {
    Write-Error "No se pudo obtener la issue #$IssueNumber. Verifica que existe."
    exit 1
}

# 3. Crear contenido para la IA (Prompt Engineering dentro del archivo)
$content = @"
# 🎯 TAREA ACTIVA: ISSUE #$($issueJson.number)

## Título
$($issueJson.title)

## Descripción y Requisitos
$($issueJson.body)

---
## INSTRUCCIONES PARA EL AGENTE
1. Este archivo es tu FUENTE DE VERDAD para esta sesión.
2. Implementa EXACTAMENTE lo que se pide arriba.
3. Si la issue menciona documentos, búscalos en 'docs/' (o usa el resumen).
"@

# 4. Guardar archivo de contexto (Sobrescribir si existe)
$contextFile = ".cursor/active_task.md"
# Asegurar que el directorio existe
$parentDir = Split-Path $contextFile
if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir | Out-Null }

[System.IO.File]::WriteAllText($contextFile, $content, $utf8NoBom)

Write-Host "✅ Contexto guardado en $contextFile" -ForegroundColor Green
Write-Host "⚠️ AGENTE: AHORA LEE EL ARCHIVO .cursor/active_task.md" -ForegroundColor Yellow